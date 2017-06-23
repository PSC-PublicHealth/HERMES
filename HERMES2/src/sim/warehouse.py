#!/usr/bin/env python

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without #
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################


__doc__=""" warehouse.py
A kind of Store with enhancements to handle the storage requirements
of multiple types of vaccines and to detect low or high reorder thresholds.
"""

_hermes_svn_id_="$Id$"

import ipath

import weakref
import sys,os,string
import types,math
import random
import curry
from SimPy.Simulation import *
#from SimPy.SimulationTrace import *
import globals
import abstractbaseclasses
import storagetypes
import trackabletypes
import vaccinetypes
import fridgetypes
import packagingmodel
import storagemodel
from util import StatVal, AccumVal, ContinuousTimeStampAccumVal,SpanTimeStampAccumVal, PushbackIterWrapper, AccumMultiVal, HistoVal
import trucktypes
import constants as C
import eventlog as evl
from util import logDebug, logVerbose
import copy

import calculateFill
from enums import StorageTypeEnums as ST

DEBUG = False

"""
The class HDict will be an ordered dict if globals.deterministic is true
and an appropriate implementation is available; otherwise a normal dict.
"""
if globals.deterministic:
    try:
        from collections import OrderedDict as HDict
    except ImportError,e:
        try:
            from odict import OrderedDict as HDict
        except:
            raise RuntimeError('Ordered dictionary requested but no implementation is available')
else:
    HDict= dict

def allocateSomeGroups(groupList, desiredVC, sim, excludeRecycling=False):
    
    logDebug(sim,"allocateSomeGroups: getting %s from %s"%(desiredVC,[g.getUniqueName() for g in groupList]))
    result= []
    failedTupleList= []
    for v,nDesired in desiredVC.items():
        if nDesired==0: continue
        if excludeRecycling:
            l= [(g.getAge(),g.getCount(),g.history,g) for g in groupList 
                if g.getType()==v and not g.getTag(abstractbaseclasses.Shippable.RECYCLE_TAG)]
        else:
            l= [(g.getAge(),g.getCount(),g.history,g) for g in groupList 
                if g.getType()==v and not g.getTag(abstractbaseclasses.Shippable.DO_NOT_USE_TAG)]
        l.sort()
        candidates= [g for age,nVials,history,g in l]
        for g in candidates:
            if g.getAge() is None: continue # skip expired vials
            elif g.getCount()>nDesired:
                result.append(g.split(nDesired))
                nDesired = 0
                break
            elif g.getCount()==nDesired:
                result.append(g)
                groupList.remove(g)
                nDesired = 0
                break
            else:
                result.append(g)
                groupList.remove(g)
                nDesired -= g.getCount()
        if nDesired>0: failedTupleList.append((v,nDesired))
    logDebug(sim,"allocateSomeGroups: result %s, remainder %s, failed %s"%\
             ([g.getUniqueName() for g in result],[g.getUniqueName() for g in groupList],[(v.bName,n) for v,n in failedTupleList]))
    return (result,groupList,failedTupleList) # since groupList is altered

def smallOldGroupComp(t1,t2):
    a1,g1= t1
    a2,g2= t2
    if a1<a2: return 1
    elif a1>a2: return -1
    elif g1.getCount()<g2.getCount(): return -1
    elif g1.getCount()>g2.getCount(): return 1
    else: return 0

def getNVialsAndTweakBuffer(vaccineType,n,buf):
    #print "applying getNVialsAndTweakBuffer to %s, %d vials of %s"%\
    #    (buf,n,vaccineType.bName)
    if n==0: return []
    workBuf= [(g.getAge(),g) for g in buf 
              if isinstance(g,abstractbaseclasses.Shippable) and g.getType()==vaccineType]
    workBuf= [(-a,g.getCount(),g.history,g) for a,g in workBuf if a is not None]
    if len(workBuf)==0: return []
    else:
        workBuf.sort()
        outGroups= []
        #print "workBuf: %s"%\
        #      [ (-a,g.getType().bName,nVials) for a,nVials,g in workBuf ]
        nGot= 0
        for negAge,nVials,history,g in workBuf:
            if nGot==n:
                break
            elif nVials>n-nGot:
                newG= g.split(n-nGot) # g now has fewer vials
                buf.append(newG) # We haven't changed total number of vials
                nGot += newG.getCount()
                outGroups.append(newG)
            else:
                nGot += nVials
                outGroups.append(g)
        #print "outGroups: %s"%\
        #      [(g.getType().bName,g.getCount()) for g in outGroups]
        
        return outGroups

def getVaccineCollectionAndTweakBuffer(vc,buf):
    outGroups= []
    for v,n in vc.getTupleList():
        outGroups += getNVialsAndTweakBuffer(v,n,buf)
    # We might as well pass on the expired vials.
    # They have all had their age checked just now, so we can short-cut
    # the age recalculation usually done by g.getAge() by accessing
    # the current age directly
    outGroups += [ g for g in buf if isinstance(g, abstractbaseclasses.Shippable) and g.getAge() is None ]
    return outGroups

def emptyOrSpoiledGroupFilter(buf):
    #print "applying emptyOrSpoiledGroupFilter to %s"%buf 
    result= []
    for g in buf:
        if g.getCount()==0 or g.getAge() is None: result.append(g)
    return result

def firstNonEmptyGroupFilter(vaccineType,buf):
    #print "applying firstNotEmptyGroupFilter to %s"%buf
    for g in buf:
        if g.getType()==vaccineType and g.getCount()>0 \
                and not g.getAge() is None:
            return [g]
    return []

def emptiestNonEmptyGroupFilter(vaccineType,buf):
    #print "applying emptiestNotEmptyGroupFilter to %s"%buf
    bestGroup= None
    for g in buf:
        if g.getCount()>0 and g.getType()==vaccineType \
                and (bestGroup is None or g.getCount()<bestGroup.getCount())\
                and not g.getAge() is None:
            bestGroup= g
    if bestGroup is None:
        return []
    else:
        return [bestGroup]

def fillThisOrderGroupFilter(vaccineCollection,buf):
    result= []
    for v,n in vaccineCollection.items():
        result += getNVialsAndTweakBuffer(v,n,buf)
    # If we're returning some, we might as well pass on the expired vials
    if len(result)>0:
        result += [ g for g in buf if isinstance(g,abstractbaseclasses.Shippable) and g.getAge() is None ]
    return result

def fillTruckOrderByTypeFilter(truckType,buf):
    for item in buf:
        if isinstance(item, trucktypes.Truck) and item.truckType==truckType:
            return [item]
    return None

def recyclingGroupFilter(buf):
    result= [s for s in buf 
             if isinstance(s, abstractbaseclasses.Shippable) 
             and s.getTag(abstractbaseclasses.Shippable.RECYCLE_TAG)]
    return result

def getStoreByName(storeDict,storeName):
    for store in storeDict.items():
        ##print store[1].bName
        if storeName == store[1].name:
            return store[1]
    raise RuntimeError('Could not find store by Name %s'%storeName)

def calculateOwnerStorageFillRatios(canOwn,thisVC,assumeEmpty):
    if DEBUG:
        oldVal = shareCool_calculateOwnerStorageFillRatios(canOwn, thisVC, assumeEmpty)
        newVal = share3_calculateOwnerStorageFillRatiosPreferred(canOwn, thisVC, assumeEmpty)
        print "**** do they match:  ****"
        print [old==new for (t, old, new) in zip(('freeze', 'cool', 'warm'), oldVal, newVal)]
        return newVal

    return canOwn.sim.fillCalculationRoutine(canOwn, thisVC, assumeEmpty)

def allocateOwnerStorageSpace(canOwn,stockBuf):
    return canOwn.sim.allocateStorageRoutine(canOwn, stockBuf)

def shareCool_calculateOwnerStorageFillRatios(canOwn,thisVC,assumeEmpty):
    """
    This attempts to allocate space fairly between vaccines.  It's
    very similar to the ARENA 'fair share' storage calculation.
    The return value is a triple of VaccineCollections

       freezeVC, coolVC, warmVC

    where each vaccine's entry represents the fraction of the available
    vials in the input VC to be stored in each medium.  These fractions
    are truncated at 1.0.  If assumeEmpty is true, all the canOwn's resources 
    are presumed to be included in thisVC; this includes both attached fridges
    and all vaccine supplies.  If false, thisVC is assumed to be 'in addition to'
    any existing fridges and supplies.
    """

    # This method should be 'const' in the C++ sense- no modifying
    # the canOwn!

    # classify everything

    if DEBUG:
        print "**** Old version ****"
    freezeTuples= []
    coolTuples= []
    warmTuples= []
    incomingStorageBlocks= []
    roomtempStorage= canOwn.sim.storage.roomtempStorage() # cache for speed
    frozenStorage= canOwn.sim.storage.frozenStorage() # cache for speed
    coolStorageList= canOwn.sim.storage.coolStorageList() # cache for speed
    sM = canOwn.getStorageModel()
    for v,n in thisVC.getTupleList():
        if isinstance(v,abstractbaseclasses.ShippableType):
            if sM.canStoreShippableType(v, ST.STORE_WARM): warmTuples.append((v,n))
            elif sM.canStoreShippableType(v, ST.STORE_FREEZE): freezeTuples.append((v,n))
            else: coolTuples.append((v,n))
        else:
            warmTuples.append((v,n)) # Things like trucks and fridges get stored warm
        if isinstance(v,abstractbaseclasses.CanStoreType):
            assert n==int(n), "Non-integral number of fridges"
            storageCapacityInfo= v.getStorageCapacityInfo()
            for st,vol in storageCapacityInfo:
                for _ in xrange(int(n)):
                    incomingStorageBlocks.append(fridgetypes.Fridge.StorageBlock(canOwn,st,vol))
    incomingStorageBlocks= canOwn.filterStorageBlocks(incomingStorageBlocks)
    if len(freezeTuples) + len(coolTuples) == 0:
        # It's all to be stored warm.  This situation can arise when the inventory to
        # be packed is a group of fridges, for example.  
        freezeVC = canOwn.sim.shippables.getCollection()
        coolVC = canOwn.sim.shippables.getCollection()
        warmVC= canOwn.sim.shippables.getCollection([(v,1.0) for v,n in warmTuples])        
        freezeTotalVol,coolTotalVol,warmTotalVol = \
            canOwn.getPackagingModel().getStorageVolumeTriple(thisVC,canOwn.getStorageModel())
    else:
        # Count up storage in each category
        freezeTotalVol,coolTotalVol,warmTotalVol = \
            canOwn.getPackagingModel().getStorageVolumeTriple(thisVC,canOwn.getStorageModel())
        if DEBUG:
            print "total volumes:"
            print "freeze: %s"%freezeTotalVol
            print "cool: %s"%coolTotalVol
            print "warm: %s"%warmTotalVol
        warmVol= 0.0
        warmVolUsed= 0.0
        freezeVol= 0.0
        freezeVolUsed= 0.0
        coolVol= 0.0
        coolVolUsed= 0.0
        if assumeEmpty:
            for sb in incomingStorageBlocks:
                if sb.storageType in coolStorageList:
                    coolVol += sb.volAvail
                elif sb.storageType==roomtempStorage:
                    warmVol += sb.volAvail
                else:
                    assert(sb.storageType==frozenStorage)
                    freezeVol += sb.volAvail
        else:
            for sb in canOwn.getStorageBlocks()+incomingStorageBlocks:
                if sb.storageType in coolStorageList:
                    coolVol += sb.volAvail
                    coolVolUsed += sb.volUsed
                elif sb.storageType==roomtempStorage:
                    warmVol += sb.volAvail
                    warmVolUsed += sb.volUsed
                else: 
                    assert(sb.storageType==frozenStorage)
                    freezeVol += sb.volAvail
                    freezeVolUsed += sb.volUsed

        if DEBUG:
            print "volume available: %s, %s, %s"%(freezeVol, coolVol, warmVol)

        # Anything we can leave at room temperature, we leave at room temp
        if warmTotalVol>warmVol:
            print 'warmTotalVol = %s, warmVol = %s, assumeEmpty = %s'%(warmTotalVol,warmVol,assumeEmpty)
            canOwn.printInventory()
            raise RuntimeError("%s ran out of room temperature storage"%canOwn.bName)
        warmVC= canOwn.sim.shippables.getCollection([(v,1.0) for v,n in warmTuples])
    
        # ratio1 is available freezer volume / desired freezer volume
        # ratio2 is a measure of how oversubscribed the non-freezer volume is
        if freezeTotalVol>0.0:
            ratio1= freezeVol/freezeTotalVol
        else:
            ratio1= 0.0
        if ratio1>=1.0:
            ratio1= 1.0
            freezeVC= canOwn.sim.shippables.getCollection([(v,ratio1) for v,n in freezeTuples])
            if coolTotalVol>0.0:
                ratio2= min(1.0,coolVol/coolTotalVol)
            else:
                ratio2= 0.0
            coolVC= canOwn.sim.shippables.getCollection([(v,ratio2) for v,n in coolTuples])
        else:
            freezeVC= canOwn.sim.shippables.getCollection([(v,ratio1) for v,n in freezeTuples])
            if coolTotalVol+freezeTotalVol>0.0:
                ratio2= coolVol/(((1.0-ratio1)*freezeTotalVol)
                                 +coolTotalVol)
                ratio2= min(1.0,ratio2)
                if ratio2>=ratio1:
                    coolVC= canOwn.sim.shippables.getCollection([(v,ratio2)
                                                             for v,n in coolTuples]
                                                            +[(v,ratio2*(1.0-ratio1))
                                                              for v,n in freezeTuples])
                else:
                    # Cooler space is scarce compared to freezer space
                    # If we include freezable stuff in the cooler, we'll
                    # end up allocating space for ratio1+(1.0-ratio1)*ratio2
                    # of it, so it'll get an unfair advantage- don't
                    # put any freezables in the cooler
                    ratio2= min(1.0,coolVol/coolTotalVol)
                    coolVC= canOwn.sim.shippables.getCollection([(v,ratio2) for v,n in coolTuples])
            else:
                ratio2= 0.0
                coolVC= canOwn.sim.shippables.getCollection([(v,0.0) for v,n in coolTuples])
            #print 'ratio2 = %f, coolTotalVol = %f, coolVol = %f'%(ratio2,coolTotalVol,coolVol)

    if DEBUG:
        print "freezeVC: %s\n"%repr(freezeVC)
        print "coolVC: %s\n"%repr(coolVC)
        print "warmVC: %s\n"%repr(warmVC)

    return (freezeVC,coolVC,warmVC)



def shareCool_allocateOwnerStorageSpace(canOwn,stockBuf):
    "New goods have been delivered; match to limited storage"

    # Bail early if we have nothing to store
    if len(stockBuf)==0:
        return []
    
    # Collect storage in each category
    warmBlocks= []
    freezeBlocks= []
    coolBlocks= []
    for sb in canOwn.getStorageBlocks():
        sb.clear()
        if sb.storageType==canOwn.sim.storage.roomtempStorage():
            warmBlocks.append(sb)
        elif sb.storageType==canOwn.sim.storage.frozenStorage():
            freezeBlocks.append(sb)
        else:
            coolBlocks.append(sb)
    warmCollection= Warehouse.StorageBlockCollection(canOwn,warmBlocks)
    freezeCollection= Warehouse.StorageBlockCollection(canOwn,freezeBlocks)
    
    # Sort out what we've got
    supply= HDict()
    doNotUseList= []
    useTheseList= []
    for group in stockBuf:
    #for group in [g for g in stockBuf if isinstance(g, abstractbaseclasses.Shippable)]:
        group.maybeTrack("sort at %s"%canOwn.bName)
        if not isinstance(group,abstractbaseclasses.Shippable):
            useTheseList.append(group)
            vax= group.getType()
            if vax not in supply: supply[vax]= []
            supply[vax].append(group)
        elif group.getAge() is None or group.getTag(abstractbaseclasses.Shippable.DO_NOT_USE_TAG):
            doNotUseList.append(group)
        else:
            useTheseList.append(group)
            vax= group.getType()
            if vax not in supply: supply[vax]= []
            supply[vax].append(group)

    newlySplitGroups= []
    
    # First, a special rule: everything marked DoNotUse or expired gets stored warm.
    for g in doNotUseList:
        leftovers,newSplits= warmCollection.store(g)
        #print '%s : stored %s %d %s at room temp'%(canOwn.bName,g.getType().bName,g.getCount(),g.getUniqueName())
        newlySplitGroups += newSplits
        if leftovers is not None:
            raise RuntimeError("%s ran out of discard space"%canOwn.bName)
    
    # What do we have?
    allVC= canOwn.sim.shippables.getCollectionFromGroupList(useTheseList)
    if allVC.totalCount()==0:
        return []

    # We attempt to implement the 'fair' allocation system from ARENA
    freezeVC,coolVC,warmVC= canOwn.calculateStorageFillRatios(allVC, assumeEmpty=True)
    #print '%s %s freezeVC: %s'%(canOwn.bName,canOwn.sim.now(),[(v.bName,n) for v,n in freezeVC.items()])
    #print '%s %f coolVC: %s'%(canOwn.bName,canOwn.sim.now(),[(v.bName,n) for v,n in coolVC.items()])
    #print '%s %f warmVC: %s'%(canOwn.bName,canOwn.sim.now(),[(v.bName,n) for v,n in warmVC.items()])
    #print '%s %f on allVC %s'%(canOwn.bName,canOwn.sim.now(),[(v.bName,n) for v,n in allVC.items()])

    # Fill storage, one vaccine at a time.  Note that expired
    # vials will end up in badVialStorage.  This comes from
    # storage.discardStorage() and is presumably
    # StorageType("roomtemperature").  We need to track space used in that
    # storage state, even though it's never expected to fill up.
    # We store vaccines largest-first to improve packing efficiency.
    vaxInPackingOrder = canOwn.getPackagingModel().sortToPackingOrder(allVC.keys(),
                                                                      canOwn.getStorageModel())
    
    for vax in vaxInPackingOrder:
        # The storage spaces in coolCollection need to be ordered
        # according to the storage priority list of the vaccine
        if isinstance(vax, abstractbaseclasses.ShippableType):
            orderedST= [sT for sT in canOwn.getStorageModel().getShippableTypeStoragePriorityList(vax)
                        if (sT in canOwn.sim.storage.coolStorageList())]
            if len(orderedST)>0:
                d= dict([(st,ind) for ind,st in enumerate(orderedST)])
                l= [(d[block.storageType],block) for block in coolBlocks]
                l.sort()
                coolCollection= Warehouse.StorageBlockCollection(canOwn,[block for _,block in l])
            else:
                coolCollection= Warehouse.StorageBlockCollection(canOwn,[])
        else:
            coolCollection= Warehouse.StorageBlockCollection(canOwn,[])
            
        # For some reason the following block is not functionally equivalent to
        # the code which produces allGroupsThisVax below.
        #l= [(g.getAge(),g.getCount(),g.history,g) for g in supply[vax]]
        #l.sort()
        #allGroupsThisVax= [g for age,nVials,history,g in l]

        if isinstance(vax, abstractbaseclasses.ShippableType):
            # Sort these youngest first
            l= [(g.getAge(),g) for g in supply[vax]]
            l.sort()
            allGroupsThisVax = [g for _,g in l]
        else:
            # These have no age, so no sorting
            allGroupsThisVax = supply[vax]
        
        groupIter= PushbackIterWrapper(allGroupsThisVax.__iter__())
        try:
            g= groupIter.next()
            
            # Room temperature storage- we should never run out.
            nWarm= int(math.floor(warmVC[vax]*allVC[vax]))
            # Frozen storage
            nFreeze= int(math.floor(freezeVC[vax]*allVC[vax]))
            # Cool storage
            nCool= int(math.floor(coolVC[vax]*allVC[vax]))
            for n,collection in [(nWarm,warmCollection), (nFreeze,freezeCollection),
                                 (nCool,coolCollection)]:
                while n>0:
                    if isinstance(g, abstractbaseclasses.Shippable):
                        gCount = g.getCount()
                    else:
                        gCount = 1
                    if gCount > n:
                        subG= g.split(gCount-n)
                        gCount = n
                        newlySplitGroups.append(subG)
                        groupIter.pushback(subG)
                    n -= gCount
                    leftovers,newSplits= collection.store(g)
                    newlySplitGroups += newSplits
                    if leftovers is not None: 
                        g= leftovers
                        # We won't be using n, so don't correct it for leftovers
                        break
                    g= groupIter.next()
                   
            # Any others get bumped to room temperature
            # We should never run out.
            while True:
                leftovers,newSplits= warmCollection.store(g)
                #print "%s : bumped %s %d %s to room temp"%(canOwn.bName,g.getType().bName,g.getCount(),g.getUniqueName())
                newlySplitGroups += newSplits
                if leftovers is not None: 
                    warmCollection.printSummary('Warm collection summary')
                    canOwn.printInventory()
                    raise RuntimeError("%s ran out of warm space"%canOwn.bName)
                g= groupIter.next()

        except StopIteration:
            pass
    
    return newlySplitGroups

def share3_calculateOwnerStorageFillRatios(canOwn,thisVC,assumeEmpty):
    """
    This attempts to allocate space fairly between vaccines.  It's
    very similar to the ARENA 'fair share' storage calculation.
    The return value is a triple of VaccineCollections

       freezeVC, coolVC, warmVC

    where each vaccine's entry represents the fraction of the available
    vials in the input VC to be stored in each medium.  These fractions
    are truncated at 1.0.  If assumeEmpty is true, all the canOwn's resources 
    are presumed to be included in thisVC; this includes both attached fridges
    and all vaccine supplies.  If false, thisVC is assumed to be 'in addition to'
    any existing fridges and supplies.
    """
    
    if DEBUG:
        print "**** new version ****"
    # This method should be 'const' in the C++ sense- no modifying
    # the canOwn!

    # classify everything
    freezeTuples= []
    freezeCoolTuples = []
    coolTuples= []
    coolWarmTuples = []
    warmTuples= []
    anyTuples = []
    ignoreTuples = []
    incomingStorageBlocks= []
    roomtempStorage= canOwn.sim.storage.roomtempStorage() # cache for speed
    frozenStorage= canOwn.sim.storage.frozenStorage() # cache for speed
    coolStorageList= canOwn.sim.storage.coolStorageList() # cache for speed
    sM = canOwn.getStorageModel()
    noShippables = True
    for v,n in thisVC.getTupleList():
        if isinstance(v,abstractbaseclasses.ShippableType):
            noShippables = False
            (warm, cool, freeze) = [sM.canStoreShippableType(v, st) for st in ST.wcfList]
            
            if warm and cool and freeze: anyTuples.append((v,n))
            elif warm and cool: coolWarmTuples.append((v,n))
            elif cool and freeze: freezeCoolTuples.append((v,n))
            elif warm: warmTuples.append((v,n))
            elif cool: coolTuples.append((v,n))
            elif freeze: freezeTuples.append((v,n))
            else: anyTuples.append((v,n))
        else:
            ignoreTuples.append((v,n)) # Things like trucks and fridges get stored outside the constraints

        if isinstance(v,abstractbaseclasses.CanStoreType):
            assert n==int(n), "Non-integral number of fridges"
            storageCapacityInfo= v.getStorageCapacityInfo()
            for st,vol in storageCapacityInfo:
                for _ in xrange(int(n)):
                    incomingStorageBlocks.append(fridgetypes.Fridge.StorageBlock(canOwn,st,vol))

    if noShippables:
        freezeVC = canOwn.sim.shippables.getCollection()
        coolVC = canOwn.sim.shippables.getCollection()
        warmVC= canOwn.sim.shippables.getCollection([(v,1.0) for v,n in ignoreTuples])        
        return (freezeVC, coolVC, warmVC)

    if DEBUG:
        print "ignoreTuples: %s"%repr(ignoreTuples)
        print "any: %s"%repr(anyTuples)
        print "freezeCool: %s"%repr(freezeCoolTuples)
        print "coolWarm: %s"%repr(coolWarmTuples)
        print "freeze: %s"%repr(freezeTuples)
        print "cool: %s"%repr(coolTuples)
        print "warm: %s"%repr(warmTuples)

    incomingStorageBlocks= canOwn.filterStorageBlocks(incomingStorageBlocks)

    # Count up storage in each category
    #freezeTotalVol,coolTotalVol,warmTotalVol = \
    #    canOwn.getPackagingModel().getStorageVolumeTriple(thisVC,canOwn.getStorageModel())

    freezeTotalVol,coolTotalVol,warmTotalVol,freezeCoolTotalVol,coolWarmTotalVol,anyTotalVol = \
        canOwn.getPackagingModel().getStorageVolumeHex(thisVC,canOwn.getStorageModel())

    if DEBUG:
        print "total volumes:"
        print "any: %s"%anyTotalVol
        print "freezeCool: %s"%freezeCoolTotalVol
        print "coolWarm: %s"%coolWarmTotalVol
        print "freeze: %s"%freezeTotalVol
        print "cool: %s"%coolTotalVol
        print "warm: %s"%warmTotalVol

    warmVol= 0.0
    warmVolUsed= 0.0
    freezeVol= 0.0
    freezeVolUsed= 0.0
    coolVol= 0.0
    coolVolUsed= 0.0
    outdoorVol = 0.0
    outdoorVolUsed = 0.0
    if assumeEmpty:
        for sb in incomingStorageBlocks:
            if sb.storageType in coolStorageList:
                coolVol += sb.volAvail
            elif sb.storageType==roomtempStorage:
                warmVol += sb.volAvail
            else:
                assert(sb.storageType==frozenStorage)
                freezeVol += sb.volAvail
    else:
        for sb in canOwn.getStorageBlocks()+incomingStorageBlocks:
            if sb.storageType in coolStorageList:
                coolVol += sb.volAvail
                coolVolUsed += sb.volUsed
            elif sb.storageType==roomtempStorage:
                if sb.volAvail == 1000000000000:
                    outdoorVol += sb.volAvail
                    outdoorVolUsed += sb.volUsed
                else:
                    warmVol += sb.volAvail
                    warmVolUsed += sb.volUsed
            else: 
                assert(sb.storageType==frozenStorage)
                freezeVol += sb.volAvail
                freezeVolUsed += sb.volUsed

    if DEBUG:
        print "volume available: %s, %s, %s"%(freezeVol, coolVol, warmVol)


    w_wR, w_wV, wc_wR, wc_wV, wcf_wR, wcf_wV, \
    c_cR, c_cV, wc_cR, wc_cV, cf_cR, cf_cV, wcf_cR, wcf_cV, \
    f_fR, f_fV, cf_fR, cf_fV, wcf_fR, wcf_fV = \
        calculateFill._share3(warmVol, coolVol, freezeVol, 
                              warmTotalVol, coolTotalVol, freezeTotalVol,
                              coolWarmTotalVol, freezeCoolTotalVol, anyTotalVol)

    spaceLeft = {ST.STORE_WARM : warmVol - w_wV - wc_wV - wcf_wV,
                 ST.STORE_COOL : coolVol - c_cV - wc_cV - cf_cV - wcf_cV,
                 ST.STORE_FREEZE : freezeVol - f_fV - cf_fV - wcf_fV}


    warmVC = canOwn.sim.shippables.getCollection()
    coolVC = canOwn.sim.shippables.getCollection()
    freezeVC = canOwn.sim.shippables.getCollection()


    for (tupleList, ratioList) in ((warmTuples, (w_wR, None, None)),
                                   (coolWarmTuples, (wc_wR, wc_cR, None)),
                                   (anyTuples, (wcf_wR, wcf_cR, wcf_fR)),
                                   (coolTuples, (None, c_cR, None)),
                                   (freezeCoolTuples, (None, cf_cR, cf_fR)),
                                   (freezeTuples, (None, None, f_fR))):


        for v,n in tupleList:
            for ratio, vc in zip(ratioList, (warmVC, coolVC, freezeVC)):
                if ratio is None:
                    continue
                if ratio == 0.0:
                    continue
                vc += canOwn.sim.shippables.getCollection([(v,ratio)])


    # currently we've put our shippables into one of the optimal configurations that satisfies their minimum
    # needs.  Now let's go through this and see which shippables would prefer to be elsewhere
    # and then see if that can swap any of them around into a different, more optimal, optimal configuration.

    # first generate two lists, a list of things that can be moved and still satisfy their "want" behavior
    # and a list of things that want to be moved because currently their want behavior is not satisfied.
    vcDict = {ST.STORE_WARM : warmVC, ST.STORE_COOL : coolVC, ST.STORE_FREEZE : freezeVC}
    wantMoveList = []
    canMoveList = []
    for (tupleList, ratioList) in ((warmTuples, (w_wR, None, None)),
                                   (coolWarmTuples, (wc_wR, wc_cR, None)),
                                   (anyTuples, (wcf_wR, wcf_cR, wcf_fR)),
                                   (coolTuples, (None, c_cR, None)),
                                   (freezeCoolTuples, (None, cf_cR, cf_fR)),
                                   (freezeTuples, (None, None, f_fR))):
        for v,n in tupleList:
            want = {}
            wantCount = 0;
            for st in ST.wcfList:
                if sM.wantStoreShippableType(v, st):
                    want[st] = True
                    wantCount += 1
                else:
                    want[st] = False
            for ratio, vc, st in zip(ratioList, (warmVC, coolVC, freezeVC), ST.wcfList):
                if ratio is None:
                    continue
                if ratio > 0.0:
                    if not want[st]:
                        wantMoveList.append([st, v, ratio, ratio * n, want, wantCount])
                    elif wantCount > 1:
                        canMoveList.append([st, v, ratio, ratio * n, want, wantCount])
        # add empty space to the canMoveList
        openWant = {ST.STORE_WARM:True, ST.STORE_COOL:True,ST.STORE_FREEZE:True}
        for st,amt in spaceLeft.items():
            if amt <= 0.0:
                continue
            canMoveList.append([st, None, None, amt, openWant, 3])

    # now let's try swapping things around!
    #arguably we should randomize the wantMoveList so that no entity is favored.  For now we're not going to bother.
    while True:
        try:
            (wantSt, wantV, wantRatio, wantVol, wantWant, wantCount) = wantMoveList.pop()
        except:
            break
        if wantVol <= 0.0:  #did we get to this one already?
            continue
        # might need to modify the list entry in place so grab list entry before expanding it
        for canMove in wantMoveList + canMoveList:
            (canSt, canV, canRatio, canVol, canWant, canCount) = canMove
            # if can and want are in the same pool there's no swap possible
            if wantSt == canSt:
                continue
            # can must be in a pool that want is ok with and vice versa
            if not canWant[wantSt] or not wantWant[canSt]:
                continue

            # if we're here, we can swap some or all of want with can
            if DEBUG:
                print "swapping some %s with %s"%(wantV, canV)
            if wantVol <= canVol:
                # split the can entry
                try: # the canMove entry might have None for its ratio
                    swapRatio = canRatio/canVol * wantVol
                    remainingRatio = canRatio - swapRatio
                except: 
                    swapRatio = remainingRatio = None
                canMove[:] = [wantSt, canV, swapRatio, wantVol, canWant, canCount]
                newCan = [canSt, canV, remainingRatio, canVol-wantVol, canWant, canCount]
                canMoveList.append(newCan)

                # we can swap all of want for part of can
                vcDict[wantSt] -= canOwn.sim.shippables.getCollection([(wantV, wantRatio)])
                vcDict[canSt] += canOwn.sim.shippables.getCollection([(wantV, wantRatio)])
                if canV is not None: # don't need to formally move empty space
                    vcDict[canSt] -= canOwn.sim.shippables.getCollection([(canV, swapRatio)])
                    vcDict[wantSt] += canOwn.sim.shippables.getCollection([(canV, swapRatio)])

                # if wantCount > 1 then this should be added to the canMoveList because
                # something else in the canMove list might still wish to swap with it.
                if wantCount > 1:
                    canMoveList.append([canSt, wantV, wantRatio, wantVol, wantWant, wantCount])

                # since we're completely done with this want entry (and it has been disposed of) we can just
                break # out of the canMove list and get a new wantMove entry.

            else: # wantVol > canVol
                # get the ratios.  The wantMove entry had better not have None for its ratio
                swapRatio = wantRatio/wantVol * canVol
                remainingRatio = wantRatio - swapRatio

                # modify the canMove Entry
                canMove[:] = [wantSt, canV, canRatio, canVol, canWant, canCount]

                # now swap part of want for all of can
                vcDict[wantSt] -= canOwn.sim.shippables.getCollection([(wantV, swapRatio)])
                vcDict[canSt] += canOwn.sim.shippables.getCollection([(wantV, swapRatio)])
                if canV is not None: # don't need to formally move empty space
                    vcDict[canSt] -= canOwn.sim.shippables.getCollection([(canV, canRatio)])
                    vcDict[wantSt] += canOwn.sim.shippables.getCollection([(canV, canRatio)])

                # if wantMove is happy to be in at least two places make a new canMove entry
                if wantCount > 1:
                    canMoveList.append([canSt, wantV, swapRatio, canVol, wantWant, wantCount])

                # modify the want values before we continue
                wantRatio = remainingRatio
                wantVol = wantVol - canVol



    # since we don't yet have a proper place to put ignoreVC, put it in warm:
    for v,n in ignoreTuples:
        warmVC += canOwn.sim.shippables.getCollection([(v,1.0)])

    if DEBUG:
        print "freezeVC: %s\n"%repr(freezeVC)
        print "coolVC: %s\n"%repr(coolVC)
        print "warmVC: %s\n"%repr(warmVC)
        #print "sum: %s\n"%repr(freezeVC + coolVC + warmVC)
        #print (freezeVC, coolVC, warmVC)
    return (freezeVC, coolVC, warmVC)


def share3_calculateOwnerStorageFillRatiosPreferred(canOwn,thisVC,assumeEmpty):
    """
    This attempts to allocate space fairly between vaccines.  It's
    very similar to the ARENA 'fair share' storage calculation.
    The return value is a triple of VaccineCollections

       freezeVC, coolVC, warmVC

    where each vaccine's entry represents the fraction of the available
    vials in the input VC to be stored in each medium.  These fractions
    are truncated at 1.0.  If assumeEmpty is true, all the canOwn's resources 
    are presumed to be included in thisVC; this includes both attached fridges
    and all vaccine supplies.  If false, thisVC is assumed to be 'in addition to'
    any existing fridges and supplies.
    """
    
    if DEBUG:
        print "**** new version ****"
    # This method should be 'const' in the C++ sense- no modifying
    # the canOwn!

    # classify everything
    freezeTuples= []
    freezeCoolTuples = []
    coolTuples= []
    coolWarmTuples = []
    warmTuples= []
    anyTuples = []
    ignoreTuples = []
    incomingStorageBlocks= []
    roomtempStorage= canOwn.sim.storage.roomtempStorage() # cache for speed
    frozenStorage= canOwn.sim.storage.frozenStorage() # cache for speed
    coolStorageList= canOwn.sim.storage.coolStorageList() # cache for speed
    sM = canOwn.getStorageModel()
    noShippables = True
    for v,n in thisVC.getTupleList():
        if isinstance(v,abstractbaseclasses.ShippableType):
            noShippables = False
            (warm, cool, freeze) = [sM.canStoreShippableType(v, st) for st in ST.wcfList]
            
            if warm and cool and freeze: anyTuples.append((v,n))
            elif warm and cool: coolWarmTuples.append((v,n))
            elif cool and freeze: freezeCoolTuples.append((v,n))
            elif warm: warmTuples.append((v,n))
            elif cool: coolTuples.append((v,n))
            elif freeze: freezeTuples.append((v,n))
            else: anyTuples.append((v,n))
        else:
            ignoreTuples.append((v,n)) # Things like trucks and fridges get stored outside the constraints

        if isinstance(v,abstractbaseclasses.CanStoreType):
            assert n==int(n), "Non-integral number of fridges"
            storageCapacityInfo= v.getStorageCapacityInfo()
            for st,vol in storageCapacityInfo:
                for _ in xrange(int(n)):
                    incomingStorageBlocks.append(fridgetypes.Fridge.StorageBlock(canOwn,st,vol))

    if noShippables:
        freezeVC = canOwn.sim.shippables.getCollection()
        coolVC = canOwn.sim.shippables.getCollection()
        warmVC= canOwn.sim.shippables.getCollection([(v,1.0) for v,n in ignoreTuples])        
        return (freezeVC, coolVC, warmVC)

    if DEBUG:
        print "ignoreTuples: %s"%repr(ignoreTuples)
        print "any: %s"%repr(anyTuples)
        print "freezeCool: %s"%repr(freezeCoolTuples)
        print "coolWarm: %s"%repr(coolWarmTuples)
        print "freeze: %s"%repr(freezeTuples)
        print "cool: %s"%repr(coolTuples)
        print "warm: %s"%repr(warmTuples)

    incomingStorageBlocks= canOwn.filterStorageBlocks(incomingStorageBlocks)

    # Count up storage in each category
    #freezeTotalVol,coolTotalVol,warmTotalVol = \
    #    canOwn.getPackagingModel().getStorageVolumeTriple(thisVC,canOwn.getStorageModel())

    freezeTotalVol,coolTotalVol,warmTotalVol,freezeCoolTotalVol,coolWarmTotalVol,anyTotalVol = \
        canOwn.getPackagingModel().getStorageVolumeHex(thisVC,canOwn.getStorageModel())

    if DEBUG:
        print "total volumes:"
        print "any: %s"%anyTotalVol
        print "freezeCool: %s"%freezeCoolTotalVol
        print "coolWarm: %s"%coolWarmTotalVol
        print "freeze: %s"%freezeTotalVol
        print "cool: %s"%coolTotalVol
        print "warm: %s"%warmTotalVol

    warmVol= 0.0
    warmVolUsed= 0.0
    freezeVol= 0.0
    freezeVolUsed= 0.0
    coolVol= 0.0
    coolVolUsed= 0.0
    outdoorVol = 0.0
    outdoorVolUsed = 0.0
    if assumeEmpty:
        for sb in incomingStorageBlocks:
            if sb.storageType in coolStorageList:
                coolVol += sb.volAvail
            elif sb.storageType==roomtempStorage:
                warmVol += sb.volAvail
            else:
                assert(sb.storageType==frozenStorage)
                freezeVol += sb.volAvail
    else:
        for sb in canOwn.getStorageBlocks()+incomingStorageBlocks:
            if sb.storageType in coolStorageList:
                coolVol += sb.volAvail
                coolVolUsed += sb.volUsed
            elif sb.storageType==roomtempStorage:
                if sb.volAvail == 1000000000000:
                    outdoorVol += sb.volAvail
                    outdoorVolUsed += sb.volUsed
                else:
                    warmVol += sb.volAvail
                    warmVolUsed += sb.volUsed
            else: 
                assert(sb.storageType==frozenStorage)
                freezeVol += sb.volAvail
                freezeVolUsed += sb.volUsed

    if DEBUG:
        print "volume available: %s, %s, %s"%(freezeVol, coolVol, warmVol)


    w_wR, w_wV, wc_wR, wc_wV, wcf_wR, wcf_wV, \
    c_cR, c_cV, wc_cR, wc_cV, cf_cR, cf_cV, wcf_cR, wcf_cV, \
    f_fR, f_fV, cf_fR, cf_fV, wcf_fR, wcf_fV = \
        calculateFill._share3(warmVol, coolVol, freezeVol, 
                              warmTotalVol, coolTotalVol, freezeTotalVol,
                              coolWarmTotalVol, freezeCoolTotalVol, anyTotalVol)

    spaceLeft = {ST.STORE_WARM : warmVol - w_wV - wc_wV - wcf_wV,
                 ST.STORE_COOL : coolVol - c_cV - wc_cV - cf_cV - wcf_cV,
                 ST.STORE_FREEZE : freezeVol - f_fV - cf_fV - wcf_fV}


    warmVC = canOwn.sim.shippables.getCollection()
    coolVC = canOwn.sim.shippables.getCollection()
    freezeVC = canOwn.sim.shippables.getCollection()


    for (tupleList, ratioList) in ((warmTuples, (w_wR, None, None)),
                                   (coolWarmTuples, (wc_wR, wc_cR, None)),
                                   (anyTuples, (wcf_wR, wcf_cR, wcf_fR)),
                                   (coolTuples, (None, c_cR, None)),
                                   (freezeCoolTuples, (None, cf_cR, cf_fR)),
                                   (freezeTuples, (None, None, f_fR))):


        for v,n in tupleList:
            for ratio, vc in zip(ratioList, (warmVC, coolVC, freezeVC)):
                if ratio is None:
                    continue
                if ratio == 0.0:
                    continue
                vc += canOwn.sim.shippables.getCollection([(v,ratio)])


    # currently we've put our shippables into one of the optimal configurations that satisfies their minimum
    # needs.  Now let's go through this and see which shippables would prefer to be elsewhere
    # and then see if that can swap any of them around into a different, more optimal, optimal configuration.

    # first generate two lists, a list of things that can be moved and still satisfy their "want" behavior
    # and a list of things that want to be moved because currently their want behavior is not satisfied.
    vcDict = {ST.STORE_WARM : warmVC, ST.STORE_COOL : coolVC, ST.STORE_FREEZE : freezeVC}
    wantMoveList = []
    canMoveList = []
    for (tupleList, ratioList) in ((warmTuples, (w_wR, None, None)),
                                   (coolWarmTuples, (wc_wR, wc_cR, None)),
                                   (anyTuples, (wcf_wR, wcf_cR, wcf_fR)),
                                   (coolTuples, (None, c_cR, None)),
                                   (freezeCoolTuples, (None, cf_cR, cf_fR)),
                                   (freezeTuples, (None, None, f_fR))):
        for v,n in tupleList:
            want = {}
            wantCount = 0;
            for st in ST.wcfList:
                if sM.wantStoreShippableType(v, st):
                    want[st] = True
                    wantCount += 1
                else:
                    want[st] = False
            for ratio, vc, st in zip(ratioList, (warmVC, coolVC, freezeVC), ST.wcfList):
                if ratio is None:
                    continue
                if ratio > 0.0:
                    if not want[st]:
                        wantMoveList.append([st, v, ratio, ratio * n, want, wantCount])
                    elif wantCount > 1:
                        canMoveList.append([st, v, ratio, ratio * n, want, wantCount])
        # add empty space to the canMoveList
        openWant = {ST.STORE_WARM:True, ST.STORE_COOL:True,ST.STORE_FREEZE:True}
        for st,amt in spaceLeft.items():
            if amt <= 0.0:
                continue
            canMoveList.append([st, None, None, amt, openWant, 3])

    # now let's try swapping things around!
    #arguably we should randomize the wantMoveList so that no entity is favored.  Or maybe sort by preference.
    #For now we're not going to bother.
    while True:
        try:
            (wantSt, wantV, wantRatio, wantVol, wantWant, wantCount) = wantMoveList.pop()
        except:
            break
        if wantVol <= 0.0:  #did we get to this one already?
            continue
        # might need to modify the list entry in place so grab list entry before expanding it
        for canMove in wantMoveList + canMoveList:
            (canSt, canV, canRatio, canVol, canWant, canCount) = canMove
            # if can and want are in the same pool there's no swap possible
            if wantSt == canSt:
                continue
            # can must be in a pool that want is ok with and vice versa
            if not canWant[wantSt] or not wantWant[canSt]:
                continue

            # if we're here, we can swap some or all of want with can
            if DEBUG:
                print "swapping some %s with %s"%(wantV, canV)
            if wantVol <= canVol:
                # split the can entry
                try: # the canMove entry might have None for its ratio
                    swapRatio = canRatio/canVol * wantVol
                    remainingRatio = canRatio - swapRatio
                except: 
                    swapRatio = remainingRatio = None
                canMove[:] = [wantSt, canV, swapRatio, wantVol, canWant, canCount]
                newCan = [canSt, canV, remainingRatio, canVol-wantVol, canWant, canCount]
                canMoveList.append(newCan)

                # we can swap all of want for part of can
                vcDict[wantSt] -= canOwn.sim.shippables.getCollection([(wantV, wantRatio)])
                vcDict[canSt] += canOwn.sim.shippables.getCollection([(wantV, wantRatio)])
                if canV is not None: # don't need to formally move empty space
                    vcDict[canSt] -= canOwn.sim.shippables.getCollection([(canV, swapRatio)])
                    vcDict[wantSt] += canOwn.sim.shippables.getCollection([(canV, swapRatio)])
                else: # but since it's convenient to keep tracking empty space to continue this thing:
                    spaceLeft[wantSt] += wantVol
                    spaceLeft[canSt] -= wantVol

                # if wantCount > 1 then this should be added to the canMoveList because
                # something else in the canMove list might still wish to swap with it.
                if wantCount > 1:
                    canMoveList.append([canSt, wantV, wantRatio, wantVol, wantWant, wantCount])

                # since we're completely done with this want entry (and it has been disposed of) we can just
                break # out of the canMove list and get a new wantMove entry.

            else: # wantVol > canVol
                # get the ratios.  The wantMove entry had better not have None for its ratio
                swapRatio = wantRatio/wantVol * canVol
                remainingRatio = wantRatio - swapRatio

                # modify the canMove Entry
                canMove[:] = [wantSt, canV, canRatio, canVol, canWant, canCount]

                # now swap part of want for all of can
                vcDict[wantSt] -= canOwn.sim.shippables.getCollection([(wantV, swapRatio)])
                vcDict[canSt] += canOwn.sim.shippables.getCollection([(wantV, swapRatio)])
                if canV is not None: # don't need to formally move empty space
                    vcDict[canSt] -= canOwn.sim.shippables.getCollection([(canV, canRatio)])
                    vcDict[wantSt] += canOwn.sim.shippables.getCollection([(canV, canRatio)])
                else: # but since it's convenient to keep tracking empty space to continue this thing:
                    spaceLeft[wantSt] += canVol
                    spaceLeft[canSt] -= canVol

                # if wantMove is happy to be in at least two places make a new canMove entry
                if wantCount > 1:
                    canMoveList.append([canSt, wantV, swapRatio, canVol, wantWant, wantCount])

                # modify the want values before we continue
                wantRatio = remainingRatio
                wantVol = wantVol - canVol


    # now let's do this again but moving things to their absolute preferred location
    wantMoveList = []
    canMoveList = []
    for tupleList, st in zip((warmVC, coolVC, freezeVC), ST.wcfList):
        #print tupleList
        for v,ratio in tupleList.items():
            preferredSt, facDict = sM.preferredStoreShippableType(v)
            if ratio == 0.0:
                continue
            if preferredSt == st:
                continue

            # if here this vaccine would prefer to move.
            wantMoveList.append([st, v, ratio, ratio*thisVC[v], preferredSt, facDict])

        # add empty space to the canMoveList
        openFac = {ST.STORE_WARM:1.0, ST.STORE_COOL:1.0,ST.STORE_FREEZE:1.0}
        for st,amt in spaceLeft.items():
            if amt <= 0.0:
                continue
            canMoveList.append([st, None, None, amt, 'any', openFac])

    # now let's try swapping things around!
    #arguably we should randomize the wantMoveList so that no entity is favored.  For now we're not going to bother.
    while True:
        try:
            (wantSt, wantV, wantRatio, wantVol, wantPreferred, facDict) = wantMoveList.pop()
        except:
            break
        if wantVol <= 0.0:  #did we get to this one already?
            continue
        # might need to modify the list entry in place so grab list entry before expanding it
        for canMove in wantMoveList + canMoveList:
            (canSt, canV, canRatio, canVol, canPreferred, canDict) = canMove
            
            # see if it's a good match for want
            if wantPreferred != canSt:
                continue
            # see if it's a good match for can
            if canPreferred != 'any':
                if canPreferred != wantSt:
                    continue

            # if we're here, we can swap some or all of want with can
            if DEBUG:
                print "swapping some %s with %s"%(wantV, canV)
            if wantVol <= canVol:
                # modify the can entry.  If it's open space, then split it
                if canV is not None:
                    swapRatio = canRatio/canVol * wantVol
                    remainingRatio = canRatio - swapRatio
                    canMove[:] = [canSt, canV, remainingRatio, canVol-wantVol, canPreferred, canDict]
                else:
                    canMove[:] = [canSt, None, None, canVol-wantVol, canPreferred, canDict]
                    newCan = [wantSt, None, None, wantVol, canPreferred, canDict]
                    canMoveList.append(newCan)

                # we can swap all of want for part of can
                vcDict[wantSt] -= canOwn.sim.shippables.getCollection([(wantV, wantRatio)])
                vcDict[canSt] += canOwn.sim.shippables.getCollection([(wantV, wantRatio)])
                if canV is not None: # don't need to formally move empty space
                    vcDict[canSt] -= canOwn.sim.shippables.getCollection([(canV, swapRatio)])
                    vcDict[wantSt] += canOwn.sim.shippables.getCollection([(canV, swapRatio)])
                else: # but since it's convenient to keep tracking empty space to continue this thing:
                    spaceLeft[wantSt] += wantVol
                    spaceLeft[canSt] -= wantVol

                # since we're completely done with this want entry (and it has been disposed of) we can just
                break # out of the canMove list and get a new wantMove entry.

            else: # wantVol > canVol
                # get the ratios.  The wantMove entry had better not have None for its ratio
                swapRatio = wantRatio/wantVol * canVol
                remainingRatio = wantRatio - swapRatio

                # modify the canMove Entry
                # for open space we wish to just make it available on a different st
                if canV is None:
                    canMove[0] = wantSt
                else: # otherwise we wish to invalidate it by setting its volume to 0.0
                    canMove[3] = 0.0

                # now swap part of want for all of can
                vcDict[wantSt] -= canOwn.sim.shippables.getCollection([(wantV, swapRatio)])
                vcDict[canSt] += canOwn.sim.shippables.getCollection([(wantV, swapRatio)])
                if canV is not None: # don't need to formally move empty space
                    vcDict[canSt] -= canOwn.sim.shippables.getCollection([(canV, canRatio)])
                    vcDict[wantSt] += canOwn.sim.shippables.getCollection([(canV, canRatio)])
                else: # but since it's convenient to keep tracking empty space to continue this thing:
                    spaceLeft[wantSt] += canVol
                    spaceLeft[canSt] -= canVol

                # modify the want values before we continue
                wantRatio = remainingRatio
                wantVol = wantVol - canVol



    # since we don't yet have a proper place to put ignoreVC, put it in warm:
    for v,n in ignoreTuples:
        warmVC += canOwn.sim.shippables.getCollection([(v,1.0)])

    if DEBUG:
        print "freezeVC: %s\n"%repr(freezeVC)
        print "coolVC: %s\n"%repr(coolVC)
        print "warmVC: %s\n"%repr(warmVC)
        #print "sum: %s\n"%repr(freezeVC + coolVC + warmVC)
        #print (freezeVC, coolVC, warmVC)
    return (freezeVC, coolVC, warmVC)


def share3_allocateOwnerStorageSpace(canOwn,stockBuf):
    "New goods have been delivered; match to limited storage"

    # Bail early if we have nothing to store
    if len(stockBuf)==0:
        return []
    
    # Collect storage in each category
    warmBlocks= []
    freezeBlocks= []
    coolBlocks= []
    outdoorBlocks = []
    for sb in canOwn.getStorageBlocks():
        sb.clear()
        if sb.storageType==canOwn.sim.storage.roomtempStorage():
            #SILLY_CHECK_FOR_OUTDOORS
            if sb.volAvail == 1000000000000:
                #print "appending Outdoors"
                outdoorBlocks.append(sb)
            else:
                #print "appending Warm Block {0}".format(sb)
                warmBlocks.append(sb)
        elif sb.storageType==canOwn.sim.storage.frozenStorage():
            freezeBlocks.append(sb)
        else:
            coolBlocks.append(sb)
    freezeCollection = Warehouse.StorageBlockCollection(canOwn, freezeBlocks)
    coolCollection = Warehouse.StorageBlockCollection(canOwn, coolBlocks)
    warmCollection = Warehouse.StorageBlockCollection(canOwn, warmBlocks)
    outdoorCollection = Warehouse.StorageBlockCollection(canOwn, outdoorBlocks)

    # Sort out what we've got
    supply= HDict()
    doNotUseList= []
    useTheseList= []
    for group in stockBuf:
    #for group in [g for g in stockBuf if isinstance(g, abstractbaseclasses.Shippable)]:
        group.maybeTrack("sort at %s"%canOwn.bName)
        if not isinstance(group,abstractbaseclasses.Shippable):
            useTheseList.append(group)
            vax= group.getType()
            if vax not in supply: supply[vax]= []
            supply[vax].append(group)
        elif group.getAge() is None or group.getTag(abstractbaseclasses.Shippable.DO_NOT_USE_TAG):
            doNotUseList.append(group)
        else:
            useTheseList.append(group)
            vax= group.getType()
            if vax not in supply: supply[vax]= []
            supply[vax].append(group)

    newlySplitGroups= []
    
    # First, a special rule: everything marked DoNotUse or expired gets stored warm.
    for g in doNotUseList:
        leftovers,newSplits= outdoorCollection.store(g)
        #print '%s : stored %s %d %s at room temp'%(canOwn.bName,g.getType().bName,g.getCount(),g.getUniqueName())
        newlySplitGroups += newSplits
        if leftovers is not None:
            raise RuntimeError("%s ran out of discard space"%canOwn.bName)
    
    # What do we have?
    allVC= canOwn.sim.shippables.getCollectionFromGroupList(useTheseList)
    if allVC.totalCount()==0:
        return []

    # We attempt to implement the 'fair' allocation system from ARENA
    freezeVC,coolVC,warmVC= canOwn.calculateStorageFillRatios(allVC, assumeEmpty=True)
    #print '%s %s freezeVC: %s'%(canOwn.bName,canOwn.sim.now(),[(v.bName,n) for v,n in freezeVC.items()])
    #print '%s %f coolVC: %s'%(canOwn.bName,canOwn.sim.now(),[(v.bName,n) for v,n in coolVC.items()])
    #print '%s %f warmVC: %s'%(canOwn.bName,canOwn.sim.now(),[(v.bName,n) for v,n in warmVC.items()])
    #print '%s %f on allVC %s'%(canOwn.bName,canOwn.sim.now(),[(v.bName,n) for v,n in allVC.items()])

    # Fill storage, one vaccine at a time.  Note that expired
    # vials will end up in badVialStorage.  This comes from
    # storage.discardStorage() and is presumably
    # StorageType("roomtemperature").  We need to track space used in that
    # storage state, even though it's never expected to fill up.
    # We store vaccines largest-first to improve packing efficiency.
    vaxInPackingOrder = canOwn.getPackagingModel().sortToPackingOrder(allVC.keys(),
                                                                      canOwn.getStorageModel())
    
    for vax in vaxInPackingOrder:
        # For some reason the following block is not functionally equivalent to
        # the code which produces allGroupsThisVax below.
        #l= [(g.getAge(),g.getCount(),g.history,g) for g in supply[vax]]
        #l.sort()
        #allGroupsThisVax= [g for age,nVials,history,g in l]

        if isinstance(vax, abstractbaseclasses.ShippableType):
            # Sort these youngest first
            l= [(g.getAge(),g) for g in supply[vax]]
            l.sort()
            allGroupsThisVax = [g for _,g in l]
        else:
            # These have no age, so no sorting
            allGroupsThisVax = supply[vax]
        
        groupIter= PushbackIterWrapper(allGroupsThisVax.__iter__())
        try:
            g= groupIter.next()
            
            # Room temperature storage- we should never run out.
            nWarm= int(math.floor(warmVC[vax]*allVC[vax]))
            # Frozen storage
            nFreeze= int(math.floor(freezeVC[vax]*allVC[vax]))
            # Cool storage
            nCool= int(math.floor(coolVC[vax]*allVC[vax]))
            for n,collection in [(nWarm,warmCollection), (nFreeze,freezeCollection),
                                 (nCool,coolCollection)]:
                while n>0:
                    if isinstance(g, abstractbaseclasses.Shippable):
                        gCount = g.getCount()
                    else:
                        gCount = 1
                    if gCount > n:
                        subG= g.split(gCount-n)
                        gCount = n
                        newlySplitGroups.append(subG)
                        groupIter.pushback(subG)
                    n -= gCount
                    leftovers,newSplits= collection.store(g)
                    newlySplitGroups += newSplits
                    if leftovers is not None: 
                        g= leftovers
                        # We won't be using n, so don't correct it for leftovers
                        break
                    g= groupIter.next()
                   
            # Any others get bumped to room temperature
            # We should never run out.
            while True:
                leftovers,newSplits= outdoorCollection.store(g)
                #print "%s : bumped %s %d %s to room temp"%(canOwn.bName,g.getType().bName,g.getCount(),g.getUniqueName())
                newlySplitGroups += newSplits
                if leftovers is not None: 
                    warmCollection.printSummary('Warm collection summary')
                    canOwn.printInventory()
                    raise RuntimeError("%s ran out of warm space"%canOwn.bName)
                g= groupIter.next()

        except StopIteration:
            pass
    
    return newlySplitGroups



class Warehouse(Store, abstractbaseclasses.Place):
            
    class StorageBlockCollection:
        def __init__(self,owner,blockList):
            """
            blockList is a list of StorageBlock instances
            """
            self.blockList= blockList[:]
            self.blockList.sort() # just to make things more regular
            self.freeVol= sum([sb.volAvail for sb in self.blockList])
            self.iter= self.blockList.__iter__()
            self.current= None
        def printSummary(self,comment):
            print "\n------\n%s:"%comment
            for block in self.blockList:
                print "    %s (%s) %f/%f"%(block.fridge.bName,block.storageType.bName,block.volUsed,block.volAvail)
            print "------"
        def store(self,vaccineGroup):
            if self.current is None:
                # First store operation
                try:
                    self.current= self.iter.next()
                except StopIteration:   
                    # The list is empty
                    return vaccineGroup,[]
            curGroup= vaccineGroup
            if isinstance(curGroup,abstractbaseclasses.Shippable):
                nRemaining= curGroup.getCount()
            else:
                nRemaining= 1
            newlySplitGroups= []
            try:
                while nRemaining>0:
                    nThisBlock= self.current.getNVialsThatFit(vaccineGroup.getType())
                    if nThisBlock>=nRemaining:
                        self.current.store(curGroup)
                        nRemaining= 0
                        curGroup= None
                    else:
                        if nThisBlock>0:
                            subGroup= curGroup.split(nThisBlock)
                            newlySplitGroups.append(subGroup)
                            self.current.store(subGroup)
                            nRemaining -= nThisBlock
                        self.current= self.iter.next()
            except StopIteration:
                pass
            return curGroup, newlySplitGroups
        
    """
    Sometimes we want to wait 'a short time' between events, but we don't really care
    how long that time is.  shortDelayTime sets a scale for that sort of interval.  The
    value is in days.
    """
    shortDelayTime= 0.01
    
    def __init__(self,sim, placeholder1, placeholder2, 
                 capacityInfoOrInventory, 
                 popServedPC,
                 func=None, category=None, name=None, recorder=None, breakageModel=None,
                 packagingModel=None, storageModel=None, conditions=None,longitude=0.0,
                 latitude=0.0, origCapacityInfoOrInventory=None,bufferStockFraction=0.25):
        """
        sim is the HermesSim instance in which the warehouse is created.
        capacityInfoOrInventory is:
            either a list, the entries of which are FridgeType instances,
            or a list, the entries of which are Shippable instances
        recorder can be None, or a Monitor or Tally,
           or a tuple like (vaccineName,MonitorOrTally),
           or a dictionary like {vaccineName:MonitorOrTally,...}
        popServedPC is a PeopleCollection giving the population served
        func is a Stores file FUNCTION column entry, like "Administration"
        category is a Stores file CATEGORY column entry, like "District"
        """
        if not name:
            name= sim.getUniqueString("Warehouse")
        self.fridges= []
        if all([isinstance(entry,abstractbaseclasses.CanStoreType) for entry in capacityInfoOrInventory]):
            initialStock= [entry.createInstance() for entry in capacityInfoOrInventory]
        elif all([isinstance(entry,abstractbaseclasses.Trackable) for entry in capacityInfoOrInventory]):
            initialStock= capacityInfoOrInventory[:]
        else:
            raise RuntimeError('Mixed or confused initial inventory list')
        Store.__init__(self,name=name,unitName="vials",
                       getQType=PriorityQ, sim=sim,initialBuffered=initialStock)
        assert packagingModel is not None, "Packaging model was not declared at Warehouse initialization time"
        self.packagingModel = packagingModel
        assert storageModel is not None, "Storage model was not declared at Warehouse initialization time"
        self.storageModel = storageModel
        for entry in initialStock: entry.attach(self, None)

        self.ownedCostables= [ entry for entry in initialStock if isinstance(entry, abstractbaseclasses.Costable) ]
        self.fromAboveThresholdDict= HDict()
        self.fromBelowThresholdDict= HDict()
        self.lowEvent= None
        self.lowStockSet= set([])
        self.highEvent= None
        self.highStockSet= set([])
        self.pendingShipmentDict= HDict()
        self.vaccineTypes= sim.shippables.getActiveTypes()
        self.storageTypes= sim.storage.getActiveTypes()
        if popServedPC is None:
            self._popServedPC= sim.people.getCollection()
        else:
            self._popServedPC= popServedPC.copy()
        self._cumPopServedPC= None
        self.breakageModel=breakageModel
        self.recorder= recorder
        self.longitude= longitude
        self.latitude= latitude
        self._suppliers= []
        self._clients= []
        self._clientRoutes= []
        self.noteHolder= None
        self._instantaneousDemandVC= sim.shippables.getCollection()
        self._instantaneousDemandInterval= 1.0
        self.function = func
        self.category = self.reportingLevel = category
        self.conditions = conditions
        self.origCapacityInfoOrInventory= origCapacityInfoOrInventory
        self.buildFinished= False
        self.storageIntervalDict = {}
        self.bufferStockFraction = bufferStockFraction

        #Create a list of weak references to Warehouse objects
        sim.warehouseWeakRefs.append( weakref.ref(self) )
 
    def __del__(self):
        """
        On the off chance that this warehouse gets actually deleted, we want to make sure
        that any VaccineGroups in its buffer have their age information updated to deletion
        time.  This is required if the vaccines in those groups are to contribute properly
        to overall vaccine type statistics.
        """
        # Trick the warehouse into scanning through its buffer, forcing the ages to update
        junkVC= self.getSupplySummary()

    def getSim(self):
        return self.sim
    def setRecorder(self,recorder):
        self.recorder= recorder
    def setNoteHolder(self,noteHolder):
        self.noteHolder= noteHolder
    def getNoteHolder(self):
        return self.noteHolder
    def setPackagingModel(self,packagingModel):
        """
        Set the PackagingModel associated with this CanOwn
        """
        self.packagingModel = packagingModel
    def getPackagingModel(self):
        """
        Returns the PackagingModel for this CanOwn
        """
        return self.packagingModel
    def setStorageModel(self,storageModel):
        """
        Set the StorageModel associated with this CanOwn
        """
        self.storageModel = storageModel
    def getStorageModel(self):
        """
        Returns the StorageModel for this CanOwn
        """
        return self.storageModel
    def addSupplier(self,wh,routeInfoDict=None):
        if not wh in self._suppliers:
            self._suppliers.append((wh,routeInfoDict))
    def addClient(self,wh):
        if wh is self:
            eStr = "Warehouse %s attempted to add itself as its own client.  "%self.bName
            eStr += "Check the demand and routes for this warehouse."
            raise RuntimeError(eStr)

        if not wh in self._clients:
            self._clients.append(wh)
    def addClientRoute(self, name, proc, clientIds, routeType, truckType, interval, latency):
        self._clientRoutes.append({'name':name,
                                   'proc':proc,
                                   'clientIds':clientIds,
                                   'type':routeType,
                                   'truckType':truckType,
                                   'interval':interval,
                                   'latency':latency})
    def getSuppliers(self):
        return self._suppliers
    def getClients(self):
        return self._clients
    def getClientRoutes(self):
        return self._clientRoutes
    def addPendingShipment(self,client,tupleListOrVC):
        """
        Format of tupleList is [(type,nVials),...]; or just supply a 
        VaccineCollection
        """
        if isinstance(tupleListOrVC,list):
            vc= self.sim.shippables.getCollection(tupleListOrVC)
        else:
            vc= tupleListOrVC
        if client not in self.pendingShipmentDict\
                or self.pendingShipmentDict[client] is None:
            self.pendingShipmentDict[client]= vc
        else:
            self.pendingShipmentDict[client] += vc
    def getAndForgetPendingShipment(self,client):
        if client in self.pendingShipmentDict:
            result= self.pendingShipmentDict[client] 
            del self.pendingShipmentDict[client] 
            return result
        else:
            return self.sim.shippables.getCollection()
    def getSupplySummary(self):
        "Return a VaccineCollection of what's available"
        return self.sim.shippables.getCollection([(vG.getType(),vG.getCount())
                                                for vG in self.theBuffer
                                                if isinstance(vG,abstractbaseclasses.Shippable)
                                                and vG.getAge() is not None])
    def getStatus(self):
        str= "Current stock in vials: "
        for (name,count) in self.getSupplySummary().items():
            str += "%d %s,"%(name,count)
        str= str[:-1] # remove trailing ','
        return str
    def getPopServedPC(self):
        """
        Returns a PeopleCollection giving local population served.
        """
        return self._popServedPC
    def setPopServedPC(self, popServedPC):
        """
        Sets the warehouse's popServed to a copy of the given PeopleCollection.
        Note that if you do this after finishBuild has been called you should 
        call getTotalDownstreamPopServedPC(recalculate=true) on the network's
        most upstream warehouse to force cached cumulative populations to be
        recalculated.
        """
        self._popServedPC= popServedPC.copy()
    def __repr__(self):
        return u"<Warehouse({0})>".format(self.name)
    def __str__(self): return self.__repr__()
    def maybeRecordVialCount(self):
        if not self.recorder is None:
            if type(self.recorder)==types.DictType:
                recDict= self.recorder
                totVC= self.getSupplySummary()
                for k in recDict.keys():
                    if k in totVC:
                        recDict[k].observe(totVC[k])
                    elif k=="all":
                        recDict[k].observe(totVC.totalCount())
                    else:
                        recDict[k].observe(0)
                
            elif type(self.recorder)==types.TupleType:
                v,rec= self.recorder
                nTot= 0
                for group in self.theBuffer:
                    if isinstance(group, abstractbaseclasses.Shippable) and group.getAge() is not None:
                        if group.getType()==v:
                            nTot += group.getCount()
                rec.observe(nTot)
            else:
                nTot= 0
                for group in self.theBuffer:
                    if isinstance(group, abstractbaseclasses.Shippable):
                        if group.getAge() is not None:
                            nTot += group.getCount()
                self.recorder.observe(nTot)
        if self.noteHolder:
            keysList = [x for x in self.vaccineTypes if isinstance(x,abstractbaseclasses.ShippableType)]
            valueList = [0 for x in range(0,len(keysList))]
            totVC = self.getSupplySummary()
            for key in keysList:
                valueList[keysList.index(key)] = totVC[key]
            valueList.append(self.sim.now())
            names = [x.name for x in keysList]
            names.append('time')
            self.noteHolder.addNote({'storeVialCount_multival':\
                            AccumMultiVal(names,valueList)})

            
    def getStorageVolumeWOPackagingOrDiluent(self,v,nVials):
        return nVials*v.getSingletonStorageVolume(False)
    def getStorageRatio(self, onlyRatios=False):
        supply= HDict()
        totD= HDict()
        
        for sb in self.getStorageBlocks():
            if sb.storageType not in totD:
                totD[sb.storageType]= (0.0,0.0)
            hasVol,usedVol= totD[sb.storageType]
            totD[sb.storageType]= (hasVol+sb.volAvail, usedVol+sb.volUsed)
        for k in totD.keys():
            hasVol,usedVol= totD[k]
            if usedVol==0.0: ratio= 0.0
            else:
                try:
                    ratio= usedVol/hasVol
                except ZeroDivisionError:
                    str= "float division, usedVol= %g, hasVol= %g, %s"%\
                         (usedVol,hasVol,self.noteHolder)
                    raise ZeroDivisionError(str)
            supply[k.name]= StatVal(ratio)
            if not onlyRatios:
                supply[k.name + "_vol_used"] = StatVal(usedVol / C.ccPerLiter)
        return supply
    def getNVialsThatFit(self,shippableType,volCC):
        """
        What is the largest integer number of instanes of this shippableType that will
        fit in the given volCC, given this location's PackagingModel?
        """
        return self.packagingModel.getNThatFit(volCC, shippableType, self.getStorageModel())
    def getLonLat(self):
        """
        Returns a tuple (longitude, latitude) with values in decimal degrees.
        """
        return (self.longitude,self.latitude)
    def getOriginalStorageSC(self):
        """
        This is a utility function for the gap analysis as a place to store
        the original storage declaration of the storage location
        
        Returns a storageTypeCollection for the original storage
        """
        if self.origCapacityInfoOrInventory is None:
            return None
        fridgeTypeList= [g.getType() for g in self.origCapacityInfoOrInventory if isinstance(g,abstractbaseclasses.CanStore)]
        return self.sim.fridges.getTotalVolumeSCFromFridgeTypeList(fridgeTypeList)
#    def getOriginalStorage(self):
#        storageSC = self.getOriginalStorageSC()
        
    def calculateStorageFillRatios(self, thisVC, assumeEmpty=False):
        """
        This attempts to allocate space fairly between vaccines.  It's
        very similar to the ARENA model 'fair share' storage calculation.
        The return value is a triple of VaccineCollections

           freezeVC, coolVC, warmVC

        where each vaccine's entry represents the fraction of the available
        vials in the input VC to be stored in each medium.  These fractions
        are truncated at 1.0.   If assumeEmpty is true, all the canOwn's resources 
        are presumed to be included in thisVC; this includes both attached fridges
        and all vaccine supplies.  If false, thisVC is assumed to be 'in addition to'
        any existing fridges and supplies.
        """

        # This method should be 'const' in the C++ sense- no modifying
        # the instance!
        return calculateOwnerStorageFillRatios(self,thisVC,assumeEmpty)
    
    def allocateStorageSpace(self):
        "New goods have been delivered; match to limited storage"
        newlySplitGroups= allocateOwnerStorageSpace(self,self.theBuffer)
        self.theBuffer= self.theBuffer+newlySplitGroups
        return newlySplitGroups
                
    def _put(self,arg):
        #print "put with %s getQ %s supply %s"%\
        #    (self.bName,self.getQ,self.getSupplySummary())
        #print "put with %s getQ length %d supply %s"%\
        #    (self.bName,len(self.getQ),self.getSupplySummary())
        self.maybeRecordVialCount()
        super(Warehouse,self)._put(arg)
        newVC= self.getSupplySummary()
        flag= False
        for v in self.vaccineTypes:
            n= newVC[v]
            if v in self.fromBelowThresholdDict:
                if n>=self.fromBelowThresholdDict[v]:
                    if v not in self.highStockSet:
                        self.highStockSet.add(v)
                        flag= True
            if v in self.fromAboveThresholdDict:
                if n>self.fromAboveThresholdDict[v]:
                    self.lowStockSet.discard(v)
        self.allocateStorageSpace()
        self.maybeRecordVialCount()
        if self.noteHolder is not None:
            storeRat = self.getStorageRatio()
            self.noteHolder.addNote(storeRat)
            ## NOTE: This will not accurately record the storage ratio for mobile devices
            for st in storeRat.keys():
                if 'vol_used' not in st:
                    self.noteHolder.addNote({st+"_timestamp":ContinuousTimeStampAccumVal(storeRat[st],self.sim.now())})             

            if not hasattr(self, "storeRatioNotesKeys"):
                nameList = copy.copy(storagetypes.storageTypeNames)
                nameList.append('time')
                self.storeRatioNotesKeys = tuple(nameList)

            storeRatList = []
            for st in storagetypes.storageTypeNames:
                if st in storeRat.keys():
                    storeRatList.append(float(storeRat[st]))
                else:
                    storeRatList.append(0.0)
            storeRatList.append(self.sim.now())
            self.noteHolder.addNote({'storageRatio_multival': AccumMultiVal(self.storeRatioNotesKeys, storeRatList)})

        for w in self.getClients():
            w.attemptRestock()
        if flag: self.attemptDestock()
        #print "end put with %s putQ %s supply %s"%\
        #    (self.bName,self.putQ,self.getSupplySummary())
        #print "end put with %s putQ length %d supply %s"%\
        #    (self.bName,len(self.putQ),self.getSupplySummary())
    def _get(self,arg):
        #print "get with %s putQ %s supply %s"%\
        #    (self.bName,self.putQ,self.getSupplySummary())
        #print "get with %s putQ length %d supply %s"%\
        #    (self.bName,len(self.putQ),self.getSupplySummary())
        self.maybeRecordVialCount()
        super(Warehouse,self)._get(arg)
        newVC= self.getSupplySummary()
        flag= False
        for v in self.vaccineTypes:
            n= newVC[v]
            if v in self.fromAboveThresholdDict:
                if n<=self.fromAboveThresholdDict[v]:
                    if v not in self.lowStockSet:
                        self.lowStockSet.add(v)
                        flag= True
            if v in self.fromBelowThresholdDict:
                if n<self.fromBelowThresholdDict[v]:
                    self.lowStockSet.discard(v)
        for w in self.getSuppliers():
            w[0].attemptDestock()
        if flag: self.attemptRestock()
        self.allocateStorageSpace()
        self.maybeRecordVialCount()
        if self.noteHolder is not None:
            storeRat = self.getStorageRatio()
            ## NOTE: This will not accurately record the storage ratio for mobile devices
            for st in storeRat.keys():
                if 'vol_used' not in st:
                    self.noteHolder.addNote({st+"_timestamp":ContinuousTimeStampAccumVal(storeRat[st],self.sim.now())})                
            if not hasattr(self, "storeRatioNotesKeys"):
                nameList = copy.copy(storagetypes.storageTypeNames)
                nameList.append('time')
                self.storeRatioNotesKeys = tuple(nameList)

            storeRatList = []
            for st in storagetypes.storageTypeNames:
                if st in storeRat.keys():
                    storeRatList.append(float(storeRat[st]))
                else:
                    storeRatList.append(0.0)
            storeRatList.append(self.sim.now())
            self.noteHolder.addNote({'storageRatio_multival': AccumMultiVal(self.storeRatioNotesKeys, storeRatList)})



        #print "end get with %s getQ %s supply %s"%\
        #    (self.bName,self.getQ,self.getSupplySummary())
        #print "end get with %s getQ length %d supply %s"%\
        #    (self.bName,len(self.getQ),self.getSupplySummary())
    def checkStock(self):
        currentVC= self.getSupplySummary()
        highFlag= False
        lowFlag= False
        for v in self.vaccineTypes:
            n= currentVC[v]
            if v in self.fromAboveThresholdDict:
                if n<=self.fromAboveThresholdDict[v]:
                    if v not in self.lowStockSet:
                        self.lowStockSet.add(v)
                    self.highStockSet.discard(v)
                    lowFlag= True
            if v in self.fromBelowThresholdDict:
                if n<self.fromBelowThresholdDict[v]:
                    if v not in self.highStockSet:
                        self.highStockSet.add(v)
                    self.lowStockSet.discard(v)
                    highFlag= True
        if highFlag: self.attemptDestock()
        if lowFlag: self.attemptRestock()
    def attemptRestock(self):
        """
        This happens when the supply of something is too low.  If
        it appears that an incoming shipment will be helpful, the
        signal that triggers the shipment will be emitted.
        """
        if len(self.lowStockSet)==0:
            return
        for w in self.getSuppliers():
            if w[0].gotAnyOfThese(self.lowStockSet):
                self.lowEvent.signal()
                logDebug(self.sim,"%s fired low Event at %g on %s"%(self.bName, self.sim.now(),self.lowStockSet))
                break
    def attemptRestockOfSpecifiedShippable(self,shippableType):
        """
        This method is provided so that outside classes can request a restock if a particular
        ShippableType is available.  It returns True if a restock has been signaled (because
        the ShippableType is available), False otherwise.
        """
        #self.noteHolder.addNote({'TriggerCount':1})
        if self.lowEvent is None:
            logDebug(self.sim,"%s events are not being followed; ignoring attemptRestockofSpecifiedShippable on %s at %g"%(self.bName,shippableType.bName,self.sim.now()))
        else:
            testSet= set([shippableType])
            for w in self.getSuppliers():
                if w[0].gotAnyOfThese(testSet):
                    self.lowEvent.signal()  
                    logDebug(self.sim,"%s fired lowEvent at %g on specific shippable %s"%(self.bName,self.sim.now(),shippableType.bName))
                    return True
        return False
    def attemptDestock(self):
        """
        This happens when the supply of something is too high.  If
        it appears that an outgoing shipment will be helpful, the
        signal that triggers the shipment will be emitted.
        """
        if len(self.highStockSet)==0:
            return
        for w in self.getClients():
            if w.gotAnyOfThese(self.highStockSet):
                self.highEvent.signal()
                logDebug(self.sim,"%s fired highEvent at %g"%(self.bName,self.sim.now()))
                break
    def setLowThresholdAndGetEvent(self,typeInfo,thresh):
        self.fromAboveThresholdDict[typeInfo]= thresh
        print "Thresh = {0}".format(thresh)
        if self.lowEvent is None:
            print "Setting low Event"
            self.lowEvent= SimEvent("Low event from %s"%self.name,sim=self.sim)
        return self.lowEvent
    def setHighThresholdAndGetEvent(self,typeInfo,thresh):
        self.fromBelowThresholdDict[typeInfo]= thresh
        if self.highEvent is None:
            self.highEvent= SimEvent("High event from %s"%self.name,sim=self.sim)
        return self.highEvent
    def resetLowThresholds(self, threshVC):
        """
        This routine changes the trigger thresholds for high-to-low stock transitions
        to the values given in the given VaccineCollection (assumed to be in vials).  
        """
        for v, n in threshVC.items():
            self.fromAboveThresholdDict[v] = n
    def resetHighThresholds(self, threshVC):
        """
        This routine changes the trigger thresholds for low-to-high stock transitions
        to the values given in the given VaccineCollection (assumed to be in vials).  
        """
        for v, n in threshVC:
            self.fromBelowThresholdDict[v] = n
    def gotAnyOfThese(self, vaccineList):
        for v in vaccineList:
            for thisG in self.theBuffer:
                if isinstance(thisG, abstractbaseclasses.Shippable) \
                    and thisG.getType()==v and thisG.getAge() is not None:
                    return True
        return False
    def wantAnyOfThese(self,vaccineList):
        raise RuntimeError("Not implemented")
    def getKmTo(self,otherWH,level,conditions):
        return self.sim.geo.getKmBetween(self,otherWH,level,conditions)
    def getStorageBlocks(self):
        result= []
        doNotUseTag= abstractbaseclasses.Shippable.DO_NOT_USE_TAG
        for sb in [f.getStorageBlocks() for f in self.fridges 
                   if (not isinstance(f,abstractbaseclasses.Shippable) or not f.getTag(doNotUseTag))]:
            result += sb
        return result
    
    def registerInstantaneousDemandVC(self, instantaneousDemandVC, interval):
        """
        This routine plus getInstantaneousDemand provide a (rather expensive)
        way to propagate demand figures up the distribution tree immediately,
        as if all the warehouses had called each other on the phone to total things up.
        This routine sets the warehouse's total local demand level; this level stays in
        effect until the next time the routine is called.  By convention the
        input is in vials, not doses.
        """
        # Store internally as doses to save a little computation
        self._instantaneousDemandVC= instantaneousDemandVC*self.sim.vaccines.getVialsToDosesVC()
        self._instantaneousDemandInterval= interval

    def getProjectedDemandVC(self, routeName, interval,recurLevel=0):
        """
        This routine provides a (rather expensive) way to propagate demand
        figures up the distribution tree immediately, as if all the warehouses
        had called each other on the phone to total things up. This routine
        recurses through the distribution network, totaling all the demand
        levels registered by downstream clients.  Beware diamond- shaped
        distribution graphs; demand can be double-counted!  By convention the
        result is in vials, not doses.
        
        interval should be a tuple, (timeStart, timeEnd).
        """
        tStart,tEnd= interval
        #print "%s%s %s %s:"%("    "*recurLevel,self.bName,tStart,tEnd)
        resultVC = self.sim.shippables.getCollection()
        clientDict= dict([(w.code,(w,[])) for w in self.getClients()])                
        for rDict in self.getClientRoutes():
            interval= rDict['interval']
            latency=  rDict['latency']
            rtName= rDict['name']
            for c in rDict['clientIds']:
                w,routeTupleList= clientDict[c]
                routeTupleList.append((interval, latency, rtName))
        for code,valTuple in clientDict.items():
            w, routeList= valTuple
            for interval, latency, rtName in routeList:
                if interval is None: # denoting an attached clinic
                    prevTime= tStart
                    nextTime= tEnd
                else:
                    prevCycle= max(math.ceil((tStart-latency)/interval),0)
                    nextCycle= max(math.floor((tEnd-latency)/interval)+1,1)
                    if nextCycle == prevCycle: nextCycle += 1
                    prevTime= prevCycle*interval+latency
                    nextTime= nextCycle*interval+latency
                print "    %s%s via %s: %s %s"%("   "*recurLevel, w.bName,
                                                rtName.encode('utf8'), prevTime, nextTime)
                delta= w.getProjectedDemandVC(rtName, (prevTime,nextTime), recurLevel=recurLevel+1)
                print "    %s--> %s"%("    "*recurLevel,delta)
                resultVC += delta
        print "%s%s --> %s:"%("    "*recurLevel,self.bName,resultVC)
        return resultVC

    def getProjectedDemandVCNew(self, routeName, interval, recurLevel=0):
        """
        This routine provides a (rather expensive) way to propagate demand
        figures up the distribution tree immediately, as if all the warehouses
        had called each other on the phone to total things up. This routine
        recurses through the distribution network, totaling all the demand
        levels registered by downstream clients.  Beware diamond- shaped
        distribution graphs; demand can be double-counted!  By convention the
        result is in vials, not doses.
        
        interval should be a tuple, (timeStart, timeEnd).
        """
        tStart,tEnd= interval
        #print "sh %s%s %s %s:"%("    "*recurLevel,self.bName,tStart,tEnd)
        resultVC = self.sim.shippables.getCollection()
        clientDict= dict([(w.code,(w,[])) for w in self.getClients()])      
        #print clientDict          
        for rDict in self.getClientRoutes():
            print rDict
            interval= rDict['interval']
            latency=  rDict['latency']
            for c in rDict['clientIds']:
                w,routeTupleList= clientDict[c]
                routeTupleList.append((interval,latency))
        nonMan = 0
        for code,valTuple in clientDict.items():
            w,routeList= valTuple
            bestPrev= None
            bestNext= None
            #print "RL = {0}".format(routeList)
            mdelta = self.sim.shippables.getCollection()
            for interval,latency in routeList:
                if isinstance(interval,list):
                    
                    if len(interval) > 0 and len(mdelta) == 0:
                        for v in interval[0][1].keys():
                            mdelta[v] = 0.0
                    for startI,amount in interval:
                        if startI >= tStart and startI <= tEnd:
                            for v,n in amount.items():
                                vacc = self.sim.vaccines.getTypeByName(v)
                                mdelta[vacc] += n
                else:
                    nonMan+=1
                    if interval is None: # denoting an attached clinic
                        prevTime= tStart
                        nextTime= tEnd
                    else:
                        prevCycle= max(math.ceil((tStart-latency)/interval),0)
                        nextCycle= max(math.floor((tEnd-latency)/interval)+1,1)
                        if nextCycle == prevCycle: nextCycle += 1
                        prevTime= prevCycle*interval+latency
                        nextTime= nextCycle*interval+latency
                    if bestPrev is None: bestPrev= prevTime
                    else: bestPrev= max(bestPrev,prevTime)
                    if bestNext is None: bestNext= nextTime
                    else: bestNext= min(bestNext,nextTime)
                #print "    %s%s: %s %s"%("   "*recurLevel,w.bName,bestPrev,bestNext)
                if nonMan > 0:
                    delta= w.getProjectedDemandVC(routeName, (bestPrev,bestNext), recurLevel=recurLevel+1)
                    
                    resultVC += delta
            #print "    %s--> %s"%("    "*recurLevel,delta)
            resultVC += mdelta
        #print "%s%s --> %s:"%("    "*recurLevel,self.bName,resultVC)
        return resultVC
    
    def getInstantaneousDemandVC(self, routeName, interval, recurLevel=0):
        """
        This routine plus registerInstantaneousDemand provide a (rather expensive)
        way to propagate demand figures up the distribution tree immediately,
        as if all the warehouses had called each other on the phone to total things up.
        This routine recurses through the distribution network, totaling all
        the demand levels registered by downstream clients.  Beware diamond-
        shaped distribution graphs; demand can be double-counted!  By convention
        the result is in vials, not doses.
        """
        if type(interval)==types.TupleType:
            # New protocol
            tStart,tEnd= interval
        else:
            # This is effectively what is done under the old protocol
            tStart = self.sim.now()
            tEnd = tStart + interval
        print "%s%s %s %s %s:"%("    "*recurLevel,self.bName,tStart,tEnd,self._instantaneousDemandInterval)
        doseTupleList= []
        for v,n in self._instantaneousDemandVC.items():
            if isinstance(v,vaccinetypes.VaccineType):
                doseTupleList.append((v,n*((tEnd-tStart)/self._instantaneousDemandInterval)))
            else:
                doseTupleList.append((v,n))
        resultDosesVC= self.sim.shippables.getCollection(doseTupleList)
        resultVC= resultDosesVC*self.sim.vaccines.getDosesToVialsVC()
        resultVC.roundUp()
        clientDict= dict([(w.code,(w,[])) for w in self.getClients()])                
        for rDict in self.getClientRoutes():
            interval= rDict['interval']
            latency=  rDict['latency']
            rtName= rDict['name']
            for c in rDict['clientIds']:
                w,routeTupleList= clientDict[c]
                routeTupleList.append((interval,latency,rtName))
        for code,valTuple in clientDict.items():
            w,routeList= valTuple
            for interval,latency,rtName in routeList:
                if interval is None: # denoting an attached clinic
                    prevTime= tStart
                    nextTime= tEnd
                else:
                    prevCycle= max(math.ceil((tStart-latency)/interval),0)
                    nextCycle= max(math.floor((tEnd-latency)/interval)+1,1)
                    if nextCycle == prevCycle: nextCycle += 1
                    prevTime= prevCycle*interval+latency
                    nextTime= nextCycle*interval+latency
                print "    %s%s via %s: %s %s"%("   "*recurLevel, w.bName, rtName, prevTime, nextTime)
                delta= w.getInstantaneousDemandVC(rtName, (prevTime, nextTime),recurLevel=recurLevel+1)
                print "    %s--> %s"%("    "*recurLevel, delta)
                resultVC += delta
        print "%s%s --> %s:"%("    "*recurLevel,self.bName,resultVC)
                        
        return resultVC
    
    def _calcTotalDownstreamPopServedPC(self,recalculate=False):
        """
        This routine recurses through the network, counting client
        populations for all downstream warehouses recursively.  The
        return value is a PeopleCollection.  This routine should only
        be called after the shipping network is assembled.  Beware
        diamond-shaped shipping graphs; demand can be double-counted!
        """
        if self._cumPopServedPC is None or recalculate:
            totPopPC= self.sim.people.getCollection()
            if self._popServedPC is not None:
                totPopPC+=self._popServedPC
            for c in self.getClients():
                #print "%s found child %s"%(self.bName,c.bName)
                c._calcTotalDownstreamPopServedPC(recalculate=recalculate)
                totPopPC += c._cumPopServedPC
            self._cumPopServedPC= totPopPC
            #print "%s: calculated %s"%(self.bName,self._cumPopServedPC)

    def getTotalDownstreamPopServedPC(self,recalculate=False):
        """
        This routine counts total client population recursively through
        the network below the warehouse, plus any clients associated with
        the warehouse itself.  It can only be called after finishBuild()
        has been called on the network.  Beware of diamond-shaped shipping 
        graphs; demand can be double-counted!
        """
        if not self.buildFinished:
            raise RuntimeError("finishBuild has not been called on %s"%self)
        if self._cumPopServedPC is None or recalculate:
            self._calcTotalDownstreamPopServedPC(recalculate=recalculate)
        return self._cumPopServedPC
    
    def _countClientsByTier(self,baseTier,whTierDict,popTierDict,allMarkedList):
        if hasattr(self,'_recurMark'): return
        if baseTier not in whTierDict:
            whTierDict[baseTier]= 0
        if baseTier not in popTierDict:
            popTierDict[baseTier]= self.sim.people.getCollection()
        whTierDict[baseTier]+=1
        popTierDict[baseTier]+=self._popServedPC
        self._recurMark= True
        allMarkedList.append(self)
        for c in self.getClients():
            if not hasattr(c,'_recurMark'):
                c._countClientsByTier(baseTier+1,whTierDict,popTierDict,allMarkedList)

    def getTotalDownstreamClientsByTier(self):
        """
        This routine recurses through the network, counting client
        warehouses and the populations they serve.  The return value
        is a tuple ( nTotWh, whTierDict, popTierDict ). The dictionaries are
        indexed by integers starting at 0.  whTierDict gives the number
        of warehouses at that tier; popTierDict gives the total population
        served at that tier.
        """
        
        whTierDict= HDict()
        popTierDict= HDict()
        allMarkedList= []
        self._countClientsByTier(0,whTierDict,popTierDict,allMarkedList)
        nTotWh= len(allMarkedList)
        for wh in allMarkedList: del wh._recurMark
        return (nTotWh, whTierDict, popTierDict)

    def getStore(self):
        """
        This method is used to support the functionality of AttachedClinics,
        the original mechanism of which ceased to work with SimPy 2.1.0
        """
        return self
        
    def finishBuild(self):
        """
        This method should be called after the shipping network has been assembled.
        It allows the Warehouse to precalculate quantities that depend on information
        from elsewhere in the network.
        """
        self.buildFinished= True
        self._calcTotalDownstreamPopServedPC()
        
    def filterStorageBlocks(self,storageBlocks):
        """
        Some derived classes may choose to not use particular kinds of storage- for
        example, WHO rules say that clinics do not store anything in freezers.  This
        filter provides an opportunity to modify a list of storage blocks based on
        restrictions for the clinic type.
        
        The input storageBlocks is a list of tuples of form (storageType,volInCC).
        The output is expected to be a list in the same format.
        """
        return storageBlocks
        
    def cutGridPower(self):
        if not hasattr(self, "gridPowerCut"):
            self.gridPowerCut = 0
        self.gridPowerCut += 1
        if self.gridPowerCut == 1:
            print "%s: power cut at %f."%(self.bName,self.sim.now())
            count= 0
            for f in self.fridges:
                if hasattr(f,"powerFail"): 
                    f.powerFail()
                    count += 1
            if count>0:
                self.allocateStorageSpace() 
        else:
            print "%s: power is still cut at %f."%(self.bName,self.sim.now())


    def restoreGridPower(self):
        self.gridPowerCut -= 1
        if self.gridPowerCut == 0:
            print "%s: power restored at %f."%(self.bName,self.sim.now())
            count= 0
            for f in self.fridges:
                if hasattr(f,"powerUnFail"): 
                    f.powerUnFail()
                    count += 1
            if count>0:
                self.allocateStorageSpace() 
        else:
            print "%s: power is not yet restored."%self.bName

    def attachStorage(self,thisFridge,callingProc):
        """
        thisFridge must satisfy isinstance(thisFridge,abstractbaseclasses.CanStore)
        callingProc is the current SimPy Process instance, or None at initialization time.
        """
        if isinstance(thisFridge,abstractbaseclasses.Shippable):
            self.getPackagingModel().repackage(thisFridge)
            thisFridge.clearTag(abstractbaseclasses.Shippable.RECYCLE_TAG)
            if self.sim.userInput["pvsdbugfix"]:
                thisFridge.setTag(abstractbaseclasses.Shippable.DO_NOT_USE_TAG)
                if callingProc is not None: # None means it's initialization time
                    thisFridge.discharge(callingProc) # make it warm so that it won't be used for local storage
        self.fridges.append(thisFridge)
        
    def detachStorage(self,thisFridge,callingProc):
        """
        thisFridge must satisfy isinstance(thisFridge,abstractbaseclasses.CanStore)
        """
        if thisFridge in self.fridges:
            self.fridges.remove(thisFridge)
        else:
            raise RuntimeError("Internal error: %s not in storage of this %s"%(thisFridge,self.truckType.bName))
        if isinstance(thisFridge,abstractbaseclasses.Shippable):
            thisFridge.clearTag(abstractbaseclasses.Shippable.DO_NOT_USE_TAG)
        thisFridge.recharge(callingProc)
        
    def _recordStockArrivalStats(self, shippable):
        shippable.setArrivalTime( self.sim.now() )

    def _recordStockDepartureStats(self, shippable):
        if shippable.getAge() is not None: # exclude expired shippables
            tp = shippable.getType()
            dT = self.sim.now() - shippable.getArrivalTime()
            if tp in self.storageIntervalDict:
                self.storageIntervalDict[tp] += (dT, shippable.getCount())
            else:
                self.storageIntervalDict[tp] = HistoVal( (dT,shippable.getCount()) )
                
    def getStockIntervalHistograms(self):
        return self.storageIntervalDict
    
    def clearStockIntervalHistograms(self):
        self.storageIntervalDict = {}
        
    def clearStatistics(self):
        self.clearStockIntervalHistograms()
            
    def attachStock(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        if isinstance(shippable, abstractbaseclasses.Shippable):
            shippable.clearTag(abstractbaseclasses.Shippable.RECYCLE_TAG)
            self.getPackagingModel().repackage(shippable)
            if not shippable.getTag(abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG):
                self._recordStockArrivalStats(shippable)
        
    def detachStock(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        if isinstance(shippable, abstractbaseclasses.Shippable):
            if not shippable.getTag(abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG):
                self._recordStockDepartureStats(shippable)
        
    def attachIce(self,thisIce):
        """
        thisIce must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        self.getPackagingModel().repackage(thisIce)
        thisIce.clearTag(abstractbaseclasses.Shippable.DO_NOT_USE_TAG) # because we need to store it in a freezer
        if not thisIce.getTag(abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG):
            self._recordStockArrivalStats(thisIce)

    def detachIce(self,thisIce):
        """
        thisIce must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        if not thisIce.getTag(abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG):
            self._recordStockDepartureStats(thisIce)

    def printInventory(self):
        """
        When this method is called the CanOwn instance will print (to sys.stdout) an inventory
        of all its currently attached Shippables.  This is intended as a debugging tool.
        """
        print "Inventory for %s %s:"%(self.__class__.__name__,self.bName)
        for f in [item for item in self.theBuffer if isinstance(item,abstractbaseclasses.CanStore)]:
            if isinstance(f,abstractbaseclasses.Shippable):
                tagList = f.getTagList()
            else:
                tagList = None
            if hasattr(f,'getType'):
                print "    %s: %s: tags %s"%(f.bName,f.getType().bName,tagList)
            else:
                print "    %s: %s: tags %s"%(f.bName,f.__class__.__name__,tagList)
            for b in f.getStorageBlocks():
                print "        type %s: %d / %d CC; contents %s"%(b.storageType.bName,
                                                                  int(round(b.volUsed)),int(round(b.volAvail)),
                                                                  [g.getUniqueName() for g in b.contents])
        for s in self.theBuffer:
            if isinstance(s,abstractbaseclasses.Shippable):
                print "    %s: %s count %d age %s tags %s"%\
                    (s.getType().bName,s.getUniqueName(),s.getCount(),s.getAge(), s.getTagList())
            else:
                print "    %s: %s"%(s.__class__.__name__,s.bName)

    def applyToAll(self, filterClass, func, negFilterClass=None, argList=[]):
        """
        Causes the CanOwn to apply all those owned instances for which isinstance(thisInstance,filterClass) is true
        to execute func(thisInstance,*argList) and return a list containing the return values of all those
        function invocations.
        
        For this class and its derived classes, and 'owned instance' is an instance of a TrackableType which is found
        in self.theBuffer .
        """
        if negFilterClass is None:
            return [func(g, *argList) for g in [gg for gg in self.theBuffer if isinstance(gg, filterClass)]]
        else:
            return [func(g, *argList) for g in [gg for gg in self.theBuffer 
                                                if isinstance(gg, filterClass) and not isinstance(gg,negFilterClass)]]

class Clinic(Warehouse):
    def __init__(self,sim, placeholder1, placeholder2, capacityInfo,
                 popServedPC,func=None,category=None,conditions=None,
                 name=None,recorder=None,breakageModel=None,
                 demandModel=None,packagingModel=None,storageModel=None,
                 longitude=0.0,latitude=0.0,
                 useVialsLatency=None, useVialsTickInterval=None,
                 origCapacityInfoOrInventory=None,
                 bufferStockFraction=0.25):
        """
        A Clinic is a location that treats patients.  It does not ship out, so only AttachedClinics
        can be the children of Clinics.  In addition to the parameters to the constructor of
        Warehouse, Clinic.__init__ takes the following parameters:

        demandModel  Either a DemandModel instance or a tuple of two DemandModel instances,
                     (shippingDemandModel, consumptionDemandModel) in that order.  If a single
                     DemandModel is given it plays both roles.

        useVialsLatency  Time in days before the start-up of the UseVials cycle
        useVialsTickInterval Time in days between UseVials events
        """
        if name is None:
            name= sim.getUniqueString("Clinic")
        Warehouse.__init__(self,
                           sim, placeholder1, placeholder2, 
                           capacityInfo,
                           popServedPC,
                           func=func, category=category, conditions=conditions,
                           name=name,recorder=recorder, breakageModel=breakageModel,
                           packagingModel=packagingModel, storageModel=storageModel,
                           longitude=longitude, latitude=latitude,
                           origCapacityInfoOrInventory=origCapacityInfoOrInventory,
                           bufferStockFraction=bufferStockFraction)
        self.leftoverDoses= HDict()
        self._accumulatedUsageVC= self.sim.shippables.getCollection()
        self._instantUsageVC = self.sim.shippables.getCollection()
        if isinstance(demandModel, types.TupleType):
            self.shippingDemandModel, self.consumptionDemandModel = demandModel
        else:
            self.shippingDemandModel = self.consumptionDemandModel = demandModel
        self.useVialsLatency = useVialsLatency
        self.useVialsTickInterval = useVialsTickInterval

    def getUseVialsLatency(self): return self.useVialsLatency
    def getUseVialsTickInterval(self): return self.useVialsTickInterval
    def __repr__(self):
        return "<Clinic(%s)>"%self.name
    def __str__(self): return self.__repr__()
    def addClient(self,wh):
        if wh is self:
            eStr = "Clinic %s attempted to add itself as its own client.  "%self.bName
            eStr += "Check the demand and routes for this clinic."
            raise RuntimeError(eStr)
        if isinstance(wh,AttachedClinic):
            super(Clinic,self).addClient(wh)
        else:
            raise RuntimeError("Clinic %s can have only AttachedClinics as clients"%self.name)
    def setDemandModel(self,demandModel):
        """
        demandModel can be either a single DemandModel instance or a tuple of the form
        (shippingDemandModel, consumptionDemandModel) in that order.  If only a single
        instance is given, it serves both roles.
        """
        if isinstance(demandModel, types.TupleType):
            self.shippingDemandModel, self.consumptionDemandModel = demandModel
        else:
            self.shippingDemandModel = self.consumptionDemandModel = demandModel
    def getLeftoverDoses(self,vax):
        """
        The return value is a tuple (nDoses, timeWhenOpened)
        """
        if vax in self.leftoverDoses:
            return self.leftoverDoses[vax] 
        else:
            return (0,0.0)
    def setLeftoverDoses(self,vax,count,vaxOpenTime):
        self.leftoverDoses[vax]= (count,vaxOpenTime) 
    def getAccumulatedUsageVC(self):
        """
        Returns accumulated usage in vials since the last time the accumulator was cleared.
        """
        return self._accumulatedUsageVC
    def clearAccumulatedUsage(self):
        """
        Clears the usage accumulator.
        """
        self._accumulatedUsageVC= self.sim.shippables.getCollection()
    def clearInstantUsage(self):
        """
        Clears the InstataneousUsage accumulator for daily reporting
        """
        self._instantUsageVC = self.sim.shippables.getCollection()
    def getProjectedDemandVC(self, routeName, interval, recurLevel=0):
        """
        This routine provides a (rather expensive) way to propagate shipping demand
        figures up the distribution tree immediately, as if all the warehouses
        had called each other on the phone to total things up. This routine
        recurses through the distribution network, totaling all the demand
        levels registered by downstream clients.  Beware diamond- shaped
        distribution graphs; demand can be double-counted!  By convention the
        result is in vials, not doses.
        
        interval should be a tuple, (timeStart, timeEnd).
        """
        tStart,tEnd= interval
        #print "%s%s %s %s:"%("    "*recurLevel,self.bName,tStart,tEnd)
        resultVC= self.shippingDemandModel.getDemandExpectationVials(self.getPopServedPC(),
                                                                     self.getUseVialsTickInterval(),
                                                                     tEnd-tStart,tStart)
        resultVC= self.sim.shippables.addPrepSupplies(resultVC)
        #print "%s%s --> %s:"%("    "*recurLevel,self.bName,resultVC)
        # Cover the case where someone hangs an attached clinic on a clinic
        for w in self.getClients():
            if isinstance(w,AttachedClinic):
                #print "    %s%s: %s %s"%("   "*recurLevel,w.bName,tStart,tEnd)
                delta= w.getProjectedDemandVC(routeName, (tStart, tEnd), recurLevel=recurLevel+1)
                #print "    %s--> %s"%("    "*recurLevel,delta)
                resultVC += delta
            else:
                raise RuntimeError("Clinic %s has client %s, which is not an AttachedClinic"%\
                                   self.name,w.name)
        return resultVC

    def filterStorageBlocks(self,storageBlocks):
        """
        Some derived classes may choose to not use particular kinds of storage- for
        example, WHO rules say that clinics do not store anything in freezers.  This
        filter provides an opportunity to modify a list of storage blocks based on
        restrictions for the clinic type.
        
        This implementation enforces the WHO rule about not using freezers at clinics.
        
        The input storageBlocks is a list of tuples of form (storageType,volInCC).
        The output is expected to be a list in the same format.
        """
        return [ block for block in storageBlocks if block.storageType!=self.sim.storage.frozenStorage()]

    def attachStorage(self, thisFridge, callingProc):
        """
        thisFridge must satisfy isinstance(thisFridge,abstractbaseclasses.CanStore)
        callingProc is the current SimPy Process instance, or None at initialization time.
        """
        if isinstance(thisFridge,abstractbaseclasses.Shippable):
            self.getPackagingModel().repackage(thisFridge)
        thisFridgeType= thisFridge.getType()
        # nothing gets marked for recycling during initialization, and the arrival of fridges in
        # the process of getting recycled does not mark existing fridges
        if self.sim.now()>0.0 and not thisFridge.getTag(abstractbaseclasses.Shippable.RECYCLE_TAG): 
            l= [(-f.getAge(),f) for f in self.fridges
                if f.getType()==thisFridgeType and not f.getTag(abstractbaseclasses.Shippable.RECYCLE_TAG)]
            if len(l)>0:
                l.sort()
                oldestSimilarFridge= l[0][1]
                oldestSimilarFridge.setTag(abstractbaseclasses.Shippable.RECYCLE_TAG)
                logDebug(self.sim,'%s matched %s at %s'%(oldestSimilarFridge,thisFridge,self.bName))
            else:
                logDebug(self.sim,'Nothing matching %s at %s'%(thisFridge,self.bName))
        self.fridges.append(thisFridge)
        
    def detachStorage(self,thisFridge,callingProc):
        """
        thisFridge must satisfy isinstance(thisFridge,abstractbaseclasses.CanStore)
        """
        # Superclass method would turn off the recycling flag
        if thisFridge in self.fridges:
            self.fridges.remove(thisFridge)
        else:
            raise RuntimeError("Internal error: %s not in storage of this %s"%(thisFridge,self.truckType.name))

    def attachStock(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        if isinstance(shippable, abstractbaseclasses.Shippable):
            self.getPackagingModel().repackage(shippable)
            if not shippable.getTag(abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG):
                self._recordStockArrivalStats(shippable)
    def detachStock(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        if isinstance(shippable, abstractbaseclasses.Shippable):
            if not shippable.getTag(abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG):
                self._recordStockDepartureStats(shippable)

    def attachIce(self,thisIce):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        self.getPackagingModel().repackage(thisIce)
        if self.sim.now()>0.0: # nothing gets marked for recycling during initialization
            thisIceType= thisIce.getType()
            nToFlag= thisIce.getCount()
            l= [(-g.getAge(),g) for g in self.theBuffer
                if g.getType()==thisIceType and not g.getTag(abstractbaseclasses.Shippable.RECYCLE_TAG)]
            l.sort()
            try:
                while nToFlag>0:
                    target= l.pop(0)[1]
                    if target.getCount()>nToFlag:
                        newTarget= target.split(nToFlag)
                        self.theBuffer.append(newTarget) # doesn't actually change number of instances in theBuffer
                        target= newTarget
                    target.setTag(abstractbaseclasses.Shippable.RECYCLE_TAG)
                    nToFlag -= target.getCount()
            except IndexError:
                print '%s ran out of old iceType %s to recycle'%(self.bName,thisIceType.bName)      
                
    def detachIce(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        pass

abstractbaseclasses.Place.register(Clinic) # @UndefinedVariable

class AttachedClinic(Clinic):
    def __init__(self,sim,owningWH,
                 popServedPC,name=None,recorder=None,breakageModel=None,
                 demandModel=None, useVialsLatency = None, useVialsTickInterval = None,
                 bufferStockFraction=0.25):
        """
        This is meant to represent a clinic which is closely
        associated with a warehouse, and uses that warehouse's stores
        directly.  Parameters are as for Clinic.
        """
        if name is None:
            name= sim.getUniqueString("AttachedClinic")
        function = "Attached Administration"
        category = "Attached Clinic"
        if owningWH is None: 
            conditions = None
            reportingLevel = None
            packagingModel = packagingmodel.DummyPackagingModel() # until initialization is complete
        else: 
            conditions = owningWH.conditions
            reportingLevel = owningWH.reportingLevel
            packagingModel = owningWH.getPackagingModel()
        Clinic.__init__(self,
                        sim,
                        "placeholder","placeholder",
                        [],
                        popServedPC,
                        func=function,category=category,conditions=conditions,
                        name=name,recorder=recorder,
                        breakageModel=breakageModel,
                        demandModel=demandModel,
                        packagingModel=packagingModel,
                        storageModel=storagemodel.DummyStorageModel(),
                        longitude=0.0,
                        latitude=0.0,useVialsLatency=useVialsLatency,
                        useVialsTickInterval=useVialsTickInterval,
                        bufferStockFraction=bufferStockFraction)
        if owningWH is not None:
            self.addSupplier(owningWH,{'Type':'attached'})
            owningWH.addClient(self)
        self.reportingLevl = reportingLevel
        self.leftoverDoses = HDict()
    def getOwningWH(self):
        if len(self._suppliers)>0: return self._suppliers[0][0]
        else: return None
    def addSupplier(self,wh,routeInfoDict=None):
        if len(self._suppliers)==0:
            logDebug(self.sim,"Adding supplier %s to AttachedClinic %s"%(wh.bName,self.bName))
            self.conditions = wh.conditions
            self.reportingLevel = wh.reportingLevel
            self.packagingModel = wh.packagingModel
            self._suppliers.append((wh,routeInfoDict))
        else:
            raise RuntimeError("AttachedClinic %s can have no supplier but its partner"%self.name)
    def addClient(self,wh):
        if wh is self:
            eStr = "Clinic %s attempted to add itself as its own client.  "%self.name
            eStr += "Check the demand and routes for this clinic."
            raise RuntimeError(eStr)
        raise RuntimeError("AttachedClinic %s can have no clients"%self.name)
    def addPendingShipment(self,client,tupleListOrVC):
        raise RuntimeError("AttachedClinic %s cannot ship"%self.name)
    def getAndForgetPendingShipment(self,client):
        raise RuntimeError("AttachedClinic %s does not know any shipments"%self.name)
    def getSupplySummary(self):
        "Return a VaccineCollection of what's available"
        return self.getOwningWH().getSupplySummary()
    def getStatus(self):
        s= "Current stock in vials: 0 of anything"
        return s
    def __repr__(self):
        return "<AttachedClinic(%s)>"%self.name
    def __str__(self): return self.__repr__()
    def maybeRecordVialCount(self):
        """
        I have no vials of my own, and my partner has its own
        method.  However, this method is still handy for some
        improvised diagnostics.
        """
        pass
        ## This block returns the supply at the store to which we are connected
        #if not self.recorder is None:
        #    vc= self.getOwningWH().getSupplySummary()
        #    if type(self.recorder)==types.DictType:
        #        recDict= self.recorder
        #        for k in recDict.keys():
        #            if k in vc:
        #                recDict[k].observe(vc[k])
        #    elif type(self.recorder)==types.TupleType:
        #        v,rec= self.recorder
        #        rec.observe(vc[v])
        #    else:
        #        self.recorder.observe(vc.totalCount())
        # This block returns the number of *doses* in the 'leftovers'
        #if not self.recorder is None:
        #    if type(self.recorder)==types.DictType:
        #        recDict= self.recorder
        #        for k in recDict.keys():
        #            recDict[k].observer(self.getLeftoverDoses(k))
        #    elif type(self.recorder)==types.TupleType:
        #        v,rec= self.recorder
        #        rec.observe(self.getLeftoverDoses(v))
        #    else:
        #        nTot= 0
        #        for v,n in self.leftoverDoses.items():
        #            nTot += n
        #        self.recorder.observe(nTot)
            
    def getNVialsThatFit(self,v,volCC):
        return self.getOwningWH().getNVialsThatFit(v,volCC)
    def getLonLat(self):
        return self.getOwningWH().getLonLat()
    def getStorageBlocks(self):
        return self.getOwningWH().getStorageBlocks()
    def _put(self,arg):
        raise RuntimeError("Attempt to put supplies to AttachedClinic %s"%\
                           self.name)
    def _get(self,arg):
        raise RuntimeError("Attempt to get supplies from AttachedClinic %s"%\
                           self.name)
    def setLowThresholdAndGetEvent(self,typeInfo,thresh):
        raise RuntimeError("AttachedClinic %s cannot set low threshold"%\
                           self.name)
    def setHighThresholdAndGetEvent(self,typeInfo,thresh):
        raise RuntimeError("AttachedClinic %s cannot set high threshold"%\
                           self.name)
    def gotAnyOfThese(self,vaccineList):
        raise RuntimeError("AttachedClinic %s shouldn't be asked for anything"%\
                           self.name)
    def wantAnyOfThese(self,vaccineList):
        raise RuntimeError("AttachedClinic %s shouldn't be offered anything"%\
                           self.name)
    def getStore(self):
        """
        This method is used to support the functionality of AttachedClinics,
        the original mechanism of which ceased to work with SimPy 2.1.0
        """
        return self.getOwningWH().getStore()
    def setPackagingModel(self,packagingModel):
        """
        Set the PackagingModel associated with this CanOwn
        """
        raise RuntimeError("Attempted to set the packaging model of %s which is an AttachedClinic"%self.name)
    def getPackagingModel(self):
        """
        Returns the PackagingModel for this CanOwn
        """
        return self.getOwningWH().getPackagingModel()
    def setStorageModel(self,storageModel):
        """
        Set the StorageModel associated with this CanOwn
        """
        raise RuntimeError("Attempted to set the storage model of %s which is an AttachedClinic"%self.name)
    def getStorageModel(self):
        """
        Returns the StorageModel for this CanOwn
        """
        return self.getOwningWH().getStorageModel()
    

abstractbaseclasses.Place.register(AttachedClinic) # @UndefinedVariable

class Factory(Process, abstractbaseclasses.UnicodeSupport):
    """
    A factory produces products and injects them into the supply chain.
    It's not really a kind of Warehouse, but it can appear in the supplier
    lists of actual Warehouses, so some methods have been added to allow
    a Factory to pretend to be a Warehouse.  Because python is a "quacks
    like a duck" language, this works out just fine.
    """
    def __init__(self, targetStores, batchInterval, quantityFunction, vaccineProd=None, startupLatency=0.0,
                 trackThis=None, trackingShipmentNumber=0, name=None, overstockScale=1.0,
                 wasteEstimates=None,
                 demandType='Projection'):
        """
        quantityFunction determines the amount of vaccine delivered; its
        signature is:

        vaccineCollection quantityFunction(factory, timeNow, daysSinceLastShipment,
                                           daysUntilNextShipment)

        targetStores is a list of tuples of the form (proportion,storeId)
        """
        #print str(targetStores)
        if name is None:
            name = targetStores[0][1].sim.getUniqueString("Factory")
        Process.__init__(self, name=name, sim=targetStores[0][1].sim)
        if batchInterval < 1.0:
            raise RuntimeError("Factory %s has cycle time of less than a day- probably not what you wanted" % \
                               name)
        if startupLatency < 0.0:
            raise RuntimeError("Factory %s has a negative startup latency" % startupLatency)
        self.name = name
        self.targetStores = targetStores
        self.quantityFunction = quantityFunction
        self.batchInterval = batchInterval
        self.trackThis = trackThis
        self.trackCountdown = trackingShipmentNumber
        self.startupLatency = startupLatency
        self.lastProductionTime = None
        self.overstockScale = overstockScale
        self.wasteEstimatesDict = wasteEstimates
        self.vaccinesProd = vaccineProd
        self.demandType = demandType
        for targetStore in self.targetStores:
            targetStore[1].addSupplier(self,None)
            targetStore[1].sim.processWeakRefs.append(weakref.ref(self))
    def run(self):
        if self.startupLatency > 0.0:
            yield hold, self, self.startupLatency
        self.lastProductionTime = self.startupLatency
        while True:
            productionVCDict = self.quantityFunction(self, self.sim.now() - self.lastProductionTime, self.sim.now(), self.batchInterval)
            for targetST, productionVC in productionVCDict.items():
                product = []
                for v, n in productionVC.getTupleList():
                    if n == 0: continue
                    if self.trackCountdown == 0:
                        if self.trackThis == v.name:
                            trackMe = True  # Turn on vial tracking
                            self.trackThis = None
                        else:
                            trackMe = False
                    else:
                        trackMe = False
                    pType = v.getLargestPackageType()
                    if isinstance(v, abstractbaseclasses.GroupedShippableType):
                        newGrp = v.createInstance(n, tracked=trackMe)
                        newGrp.setPackageType(pType)
                        product.append(newGrp)
                    else:
                        for i in xrange(int(round(n))):
                            newInst = v.createInstance(1, tracked=trackMe)
                            newInst.setPackageType(pType)
                            product.append(newInst)
                if len(product) > 0:
                    for p in product: p.attach(targetST.getStore(), self)
                    logVerbose(self.sim, "%s: put at %g: %s" % (self.bName, self.sim.now(), product))
                    yield put, self, targetST.getStore(), product
                else:
                    logVerbose(self.sim, "%s: nothing to put at %g" % (self.bName, self.sim.now()))
                self.trackCountdown -= 1
                self.lastProductionTime = self.sim.now()
                if targetST.noteHolder is not None:
                    targetST.noteHolder.addNote(self.sim.costManager.generateFactoryDeliveryCostNotes(productionVC, targetST))
                    totVolCC = 0.0
                    for v, n in productionVC.getTupleList():
                        if isinstance(v, vaccinetypes.VaccineType):
                            totVolCC += targetST.getStorageVolumeWOPackagingOrDiluent(v, n)
                    # print "totVolCC: " + str(totVolCC)
                    targetST.noteHolder.addNote({"tot_delivery_vol":totVolCC / C.ccPerLiter})
                    targetST.noteHolder.addNote(dict([(v.name + '_delivered', n)
                                                      for v, n in productionVC.items()]))
            yield hold, self, self.batchInterval       
    def __repr__(self):
        return "<Factory(%s)>"%self.targetStores[0][1].name
    def __str__(self): return self.__repr__()
    def addSupplier(self,wh,routeInfoDict=None):
        raise RuntimeError("Factory cannot add supplier")
    def addClient(self,wh):
        raise RuntimeError("Factory clients are defined at creation time")
    def addPendingShipment(self,client,tupleListOrVC):
        raise RuntimeError("Factory shipments are defined at creation time")
    def getAndForgetPendingShipment(self,client):
        pass # exception was raised when shipment was added
    def getSupplySummary(self):
        raise RuntimeError("Attempt to get a supply summary from a factory")
    def getStatus(self):
        return "This is a factory."
    def maybeRecordVialCount(self):
        pass
    def getNVialsThatFit(self,shippableType,volCC):
        """
        What is the largest integer number of instances of this shippableType that will
        fit in the given volCC, given this location's PackagingModel?  Since things should
        never be stored at a Factory, something is clearly amiss.
        """
        raise RuntimeError("Attempted to calculate storage space for a factory")
    def allocateStorageSpace(self):
        raise RuntimeError("Attempt to deliver to a factory!?")
    def attemptRestock(self):
        pass
    def attemptDestock(self):
        pass
    def setLowThresholdAndGetEvent(self,typeInfo,thresh):
        raise RuntimeError("Attempt to treat a Factory like a Warehouse")
    def setHighThresholdAndGetEvent(self,typeInfo,thresh):
        raise RuntimeError("Attempt to treat a Factory like a Warehouse")
    def gotAnyOfThese(self,vaccineList):
        return False
    def wantAnyOfThese(self,vaccineList):
        return False
    def getKmTo(self,otherWH,level,conditions):
        return 0.0
    def getTotalDownstreamPopServedPC(self):
        returnPop = None
        for prop, targetST in self.targetStores:
            if returnPop is None:
                returnPop = prop * targetST.getTotalDownstreamPopServedPC()
            else:
                returnPop += prop * targetST.getTotalDownstreamPopServedPC()
        returnPop
        # return self.targetStore.getTotalDownstreamPopServedPC()
    def getTotalDownstreamClientsByTier(self):
        returnPop = None
        for prop, targetST in self.targetStores:
            if returnPop is None:
                returnPop = prop * targetST.getTotalDownstreamClientsByTier()
            else:
                returnPop += prop * targetST.getTotalDownstreamClientsByTier()
        return returnPop
    def getStore(self):
        """
        This method is used to support the functionality of AttachedClinics,
        the original mechanism of which ceased to work with SimPy 2.1.0
        """
        raise RuntimeError("Attempt to get or put supplies to a Factory")
    def finishBuild(self):
        """
        This method should be called after the shipping network has been assembled.
        It allows the Warehouse to precalculate quantities that depend on information
        from elsewhere in the network.
        """
        pass
    def filterStorageBlocks(self,storageBlocks):
        """
        Some derived classes may choose to not use particular kinds of storage- for
        example, WHO rules say that clinics do not store anything in freezers.  This
        filter provides an opportunity to modify a list of storage blocks based on
        restrictions for the clinic type.
        
        The input storageBlocks is a list of tuples of form (storageType,volInCC).
        The output is expected to be a list in the same format.
        """
        return storageBlocks
    def setPackagingModel(self,packagingModel):
        """
        Set the PackagingModel associated with this CanOwn
        """
        raise RuntimeError("Attempted to set the packaging model of a Factory")
    def getPackagingModel(self):
        """
        Returns the PackagingModel for this CanOwn
        """
        raise RuntimeError("Attempted to get the packaging model of a Factory")
    def setStorageModel(self,storageModel):
        """
        Set the StorageModel associated with this CanOwn
        """
        raise RuntimeError("Attempted to set the storage model of a Factory")
    def getStorageModel(self):
        """
        Returns the StorageModel for this CanOwn
        """
        raise RuntimeError("Attempted to get the storage model of a Factory")

abstractbaseclasses.Place.register(Factory) # @UndefinedVariable


class PeriodicProcess(Process, abstractbaseclasses.UnicodeSupport):
    def __init__(self,sim,name,interval,startupLatency=0.0):
        """
        This is a process that does something every so often.
        The shipping interval and startupLatency are in days.
        """
        Process.__init__(self, name=name, sim=sim)
        if startupLatency<0.0:
            raise RuntimeError("PeriodicProcess %s has a negative startup latency"%startupLatency)
        self.interval= interval
        self.startupLatency= startupLatency
        self.nextCycleTime= startupLatency
        sim.processWeakRefs.append( weakref.ref(self) )

    def run(self):
        if self.startupLatency>0.0:
            yield hold,self,self.startupLatency
        while True:
            logDebug(self.sim,"%s awake at %g"%(self.bName,self.sim.now()))
            self.nextCycleTime += self.interval
            result= self.cycle(self.sim.now())
            if type(result)==types.GeneratorType:
                # cycle() returned a generator, meaning it includes a 'yield'.  
                # Otherwise, result should be None and cycle is a simple
                # function.
                try:
                    yield result.next()
                    while True:
                        yield result.send(self.sim.now())
                except StopIteration:
                    pass
            # Just in case the action of cycle() took a really long time...
            while self.nextCycleTime <= self.sim.now():
                self.nextCycleTime += self.interval
            yield hold,self,self.nextCycleTime-self.sim.now()
    def cycle(self,timeNow):
        """
        This can be a simple function, or can contain SimPy 'yield's.  If 
        it contains 'yield's it will be called via cycleReturnValue.send(timeNow) .
        For example,
        
            def cycle(initialTimeNow):
               ...
               timeNow= yield( hold,self,delayTime )
               ...
        """
        pass
    def __repr__(self):
        return "<PeriodicProcess(%s)>"%self.name
    def __str__(self): 
        return "<PeriodicProcess(%s)>"%self.name

class TimerProcess(Process, abstractbaseclasses.UnicodeSupport):
    counter= 0
    def __init__(self,sim,name,delayDays,alarmclockFunc,funArgs):
        """
        This is a process that does something once, unless it is canceled. 
        The signature of alarmclockFunc should be:
        
            alarmclockFunc(thisTimerProcess, funArgs)
            
        alarmclockFunc should return no value.  Some other process can prevent
        the activation of the function by calling cancel(self,thisTimerProcess).
        """
        self.id= TimerProcess.counter
        TimerProcess.counter += 1
        Process.__init__(self, name="%s#%d"%(name,self.id), sim=sim)
        self.delayDays= delayDays
        if self.delayDays <= 0.0:
            raise RuntimeError("TimerProcess needs a positive delay; %f won't do"%self.delayDays)
        self.alarmclockFunc= alarmclockFunc
        self.funArgs= funArgs
        sim.processWeakRefs.append( weakref.ref(self) )
    def cancel(self):
        self.alarmclockFunc= None
    def run(self):
        yield hold,self,self.delayDays
        if self.alarmclockFunc is not None: self.alarmclockFunc(self, self.funArgs)
        #else: print '%s at %f was canceled'%(self.bName,self.sim.now())
    def __repr__(self):
        if self.alarmclockFunc is None:
            return "<TimerProcess(%s) (canceled)>"%self.name
        else:
            return "<TimerProcess(%s)>"%self.name
    def __str__(self):
        if self.alarmclockFunc is None:
            return "<TimerProcess(%s) (canceled)>"%self.name
        else:
            return "<TimerProcess(%s)>"%self.name

class SnoozeTimerProcess(Process, abstractbaseclasses.UnicodeSupport):
    counter= 0
    def __init__(self,sim,name,delayDays,snoozeDays,snoozealarmclockFunc,funArgs):
        """
        This is a process that does something once, unless it is canceled. 
        The signature of alarmclockFunc should be:
        
            trueOrFalse= alarmclockFunc(thisSnoozeTimerProcess, funArgs)
            
        alarmclockFunc should return a boolean; returning False is equivalent to
        hitting the snooze button and will cause the function to be called again
        after snoozeDays.  Some other process can prevent the activation of the 
        function by calling cancel(self,thisTimerProcess).
        """
        self.id= SnoozeTimerProcess.counter
        SnoozeTimerProcess.counter += 1
        Process.__init__(self, name="%s#%d"%(name,self.id), sim=sim)
        self.delayDays= delayDays
        self.snoozeDays= snoozeDays
        if self.delayDays <= 0.0:
            raise RuntimeError("SnoozeTimerProcess needs a positive delay; %f won't do"%self.delayDays)
        self.alarmclockFunc= snoozealarmclockFunc
        self.funArgs= funArgs
        sim.processWeakRefs.append( weakref.ref(self) )
    def cancel(self):
        self.alarmclockFunc= None
    def run(self):
        yield hold,self,self.delayDays
        done= False
        while not done and self.alarmclockFunc is not None:
            done= self.alarmclockFunc(self, self.funArgs)
            if done: return
            yield hold,self,self.snoozeDays
    def __repr__(self):
        if self.alarmclockFunc is None:
            return "<SnoozeTimerProcess(%s) (canceled)>"%self.name
        else:
            return "<SnoozeTimerProcess(%s)>"%self.name
    def __str__(self):
        if self.alarmclockFunc is None:
            return "<SnoozeTimerProcess(%s) (canceled)>"%self.name
        else:
            return "<SnoozeTimerProcess(%s)>"%self.name

class UseVials(Process, abstractbaseclasses.UnicodeSupport):
    def __init__(self,clinic,
                 tickInterval,patientWaitInterval,useVialPriority,
                 startupLatency=0.0,openVialDenyFraction=None):
        """
        The paramters are:

        clinic (type Clinic): the Clinic to which this is attached
        tickInterval: interval between activations in days
        useVialPriority: 'get' priority for withdrawal of supplies from clinic
        startupLatency: delay before first activation in days
        """
        Process.__init__(self,name="UseVials_%s"%clinic.name, sim=clinic.sim)
        if tickInterval<1.0:
            raise RuntimeError("UseVials %s has cycle time of less than a day- probably not what you wanted"%\
                               self.name)
        if startupLatency<0.0:
            raise RuntimeError("UseVials %s has a negative startup latency"%startupLatency)
        assert(patientWaitInterval<tickInterval)
        assert(isinstance(clinic,Clinic))
        assert(hasattr(clinic,'consumptionDemandModel'))
        assert tickInterval is not None, "tickInterval must be defined for %s"%self.name
        self.clinic= clinic
        self.tickInterval= tickInterval
        self.patientWaitInterval= patientWaitInterval
        self.nextTickTime= 0.0
        self.useVialPriority= useVialPriority
        self.startupLatency= startupLatency
        self.openVialDenyFraction = openVialDenyFraction
        clinic.sim.processWeakRefs.append( weakref.ref(self) )
        
    def _buildTreatmentSummaryString(self,sim,paramTuple):
        treatmentTupleList, = paramTuple
        summaryString = ""
        for v,nVialsUsed,nPatients,nTreated in treatmentTupleList:
            summaryString += "%s: %d of %d using %d vials,"%\
                             (v.name,nTreated,nPatients,nVialsUsed)
        summaryString= summaryString[:-1] # trim trailing ','
        summaryString= "%s treated %s at %s"%(self.name,summaryString,self.sim.now())
        return summaryString

    def recordTreatment(self,treatmentTupleList, recordTreatmentStats = True):
        """
        This is called internally by the run() method; it is not intended to be called directly
        by the user.
        """
        logVerbose(self.sim, self._buildTreatmentSummaryString,treatmentTupleList)
            
        if self.clinic.noteHolder is not None:
            oneOutageIndicator = 0
            for v,nVialsUsed,nPatients,nTreated in treatmentTupleList:
                if nTreated<nPatients: 
                    outageIndicator= 1
                    oneOutageIndicator = 1
                else:
                    outageIndicator= 0
                # a '0' is registered in _expired here so that each vax will have an 
                # _expired note iff they've had any other interaction.
                # it is still possible for an _expired field to exist without
                # any of the other fields but it is highly unlikely.
                self.clinic.noteHolder.addNote({(v.name+"_vials"):nVialsUsed,
                                               (v.name+"_patients"):nPatients,
                                               (v.name+"_treated"):nTreated,
                                               (v.name+"_outages"):outageIndicator,
                                               (v.name+"_expired"):0})

            #Update the total outage indicator
            self.clinic.noteHolder.addNote({"one_vaccine_outages":oneOutageIndicator})
        # Record treatment statistics
        if recordTreatmentStats:
            for v,nVialsUsed,nPatients,nTreated in treatmentTupleList:
                v.recordTreatment(nTreated,nPatients,nVialsUsed)
            if self.clinic.noteHolder is not None:
                sessionNotes= self.sim.costManager.generateUseVialsSessionCostNotes(self.clinic.reportingLevel,
                                                                                    self.clinic.conditions)
                self.clinic.noteHolder.addNote( sessionNotes )
                
    def sortDoseRequirments(self, doseVC):
        """
        The input doseVC is the result of calling the DemandModel for this treatment interval.
        This method returns a tuple of the following lists, in order:
        
            treatmentTupleList= []  # tuple fmt (vax,nVials,nPatients,nTreated), ultimately used for reporting
            elaboratedTypeRateList= [] # tuple fmt (vax,nPatients,nVials), used for downstream usage calculations
            vcList= []              # tuple fmt (vax,nVials), list of needed Deliverables
            notUsedForTreatmentList = [] # Shippables produced by the DemandModel that are not Vaccines.

        from the demand in vcList.
        """
        treatmentTupleList= []  # tuple fmt (vax,nVials,nPatients,nTreated)
        elaboratedTypeRateList= [] # tuple fmt (vax,nPatients,nVials)
        vcList= []              # tuple fmt (vax,nVials)
        notUsedForTreatmentList = []

        # Can we handle any of them out of leftover vials?
        for v,doses in doseVC.items():
            if isinstance(v, vaccinetypes.VaccineType):
                if isinstance(v, abstractbaseclasses.DeliverableType):
                    # Deduct any part of the demand for deliverables that may be
                    # available from leftovers
                    leftoverDosesThisVax,doseOpenTime= self.clinic.getLeftoverDoses(v)
                    if (self.sim.now() - doseOpenTime) >= v.getLifetimeOpenDays():
                        leftoverDosesThisVax = 0

                    if doses<leftoverDosesThisVax:
                        treatmentTupleList.append( (v, 0, doses, doses ) )
                        self.clinic.setLeftoverDoses(v, leftoverDosesThisVax-doses, doseOpenTime)
                        doses = 0
                    else:
                        if leftoverDosesThisVax>0:
                            doses -= leftoverDosesThisVax
                            treatmentTupleList.append( (v, 0,
                                                        leftoverDosesThisVax,
                                                        leftoverDosesThisVax) )
                        self.clinic.setLeftoverDoses(v,0,doseOpenTime)
                        
                if doses > 0:
                    # Be sure to round up number of vials!
                    dosesPerVial = v.getNDosesPerVial()

                    nVials= (doses+dosesPerVial-1)/dosesPerVial
                    elaboratedTypeRateList.append((v,doses,nVials))
                    vcList.append((v,nVials))
                
            else:
                # Things like refrigerators or diluent may be in our demand list, but
                # we don't use them to treat patients 
                notUsedForTreatmentList.append((v,doses))
                continue
            
        return (treatmentTupleList, elaboratedTypeRateList, vcList, notUsedForTreatmentList)

    def getTreatmentSessionStoresRequestVC(self, expectedNeedVC):
        """
        This is provided to allow overrides by derived classes.  The input expectedNeedVC will
        include both Deliverables and the Shippables needed to prep them.
        """
        
        return expectedNeedVC
    
    def saveLeftoverDoses(self, leftoversList):
        """
        leftoversList is a list of (vaccineType, nDoses) tuples in opened-but-not-empty vials
        from a day's treatment session.  The leftovers are presumed to have been opened 'now'.
        This method returns nothing.
        
        BUG: we always discard leftover doses from one session when we save doses from the next,
        but if the new session has no doses of a particular type older leftovers will survive.
        """
        #comply = True
        #if random.random() > self.sim.openVialPolicyProb:
        #    comply = False
        for v,n in leftoversList:
            #if False:
            if v.canKeepOpenVials(self.tickInterval):
                #if comply is True:
                self.clinic.setLeftoverDoses(v,n,self.sim.now())

    def keepOrDiscardAfterTreatmentSession(self,unusedList):
        """
        unusedList is a list of Shippables (like VaccineGroups) which were fetched from the local Store
        for a treatment session but were ultimately never opened.  This function sorts them into two
        categories: goBackList, which contains items returned to the Store, and discardList, containing
        items which are discarded.
        """
        goBackList = unusedList[:]
        discardList = []
        return goBackList, discardList

    def selectDeliverablesToPrep(self, availableList, elaboratedTypeRateList):
        """
        availableList is the list of all unexpired Shippable and Deliverable instances fetched from the
        local store for a treatment session- no Deliverable has yet been prepped.  Divide these into
        to categories, the deliverables to be prepped (prepList) and everything else (otherList).
        elaboratedTypeRate list is the actual demand for new vials, in the format [(vax,nPatients,nVials),...]
        
        Since deliverables were ordered based on demand, the right thing to do is just select all
        deliverables.
        """
        prepList = []
        otherList = []
        for g in availableList:
            if isinstance(g,abstractbaseclasses.Deliverable): prepList.append(g)
            else: otherList.append(g)
        return (prepList, otherList)

    def readyToConsume(self, preppedList, usedUpList):
        """
        This method exists for the benefit of derived classes, which may want a look at the Deliverable
        and Consumable groups which are actually used in vaccination.
        """
        pass

    def endOfSessionActivities(self):
        """
        This is an opportunity for derived classes to do end-of-session clean-up
        """
        pass
    
    def run(self):
        # When will we next wake up?  We'll add a little
        # randomness to make sure wake-up order of clinics
        # gets shuffled.  If the latency is long enough, we will call
        # the checkStock() method at appropriate intervals to make sure
        # the pipeline operates smoothly while we wait.

        # Pause for a bit to get phase right
        pauseTime= self.startupLatency % self.tickInterval
        if pauseTime>0.0:
            self.nextTickTime += pauseTime
            yield hold,self,pauseTime
        # Check stock regularly while we wait the rest of the latency
        while self.sim.now()<self.startupLatency:
            self.nextTickTime += self.tickInterval
            self.clinic.checkStock()
            yield hold,self,self.nextTickTime-self.sim.now()
            
        # Start running in earnest
        while True:
            
            # When will we next wake up?  We'll add a little
            # randomness to make sure wake-up order of clinics
            # gets shuffled.
            self.nextTickTime += self.sim.rndm.normalvariate(self.tickInterval,Warehouse.shortDelayTime)

            # How many patients today?  Remember, this VaccineCollection
            # will hold doses, not vials.  It contains only deliverables, not
            # those supplies needed to prep them for delivery.
            doseVC= self.clinic.consumptionDemandModel.getDemand(self.clinic.getPopServedPC(),
                                                                 self.tickInterval,self.sim.now())
            
            treatmentTupleList, elaboratedTypeRateList, vcList, notUsedForTreatmentList = \
                self.sortDoseRequirments(doseVC)
            #print "%s: notUsedForTreatment: %s"%(self.bName,[(v.bName,n) for v,n in notUsedForTreatmentList])
                
            # Now we try to get something from the clinic stock.  
            # neededDeliverablesVC is a collection of *deliverable* vials, and does not
            # include the supplies necessary to prep them
            neededDeliverablesVC = self.sim.shippables.getCollection(vcList)
            #print "%s: neededDeliverablesVC is %s"%(self.bName, [(v.bName,n) for v,n in neededDeliverablesVC.items()])
            elaboratedVC = self.sim.shippables.addPrepSupplies(neededDeliverablesVC)
            #print "%s: elaboratedVC is %s"%(self.bName, [(v.bName,n) for v,n in elaboratedVC.items()])
            
            if self.openVialDenyFraction:
                for v,n in doseVC.items():
                    threshold = math.floor(v.getNDosesPerVial()*self.openVialDenyFraction)
                    nLeft = n % v.getNDosesPerVial()
                    #print "n = {0} nLeft = {1}".format(n,nLeft)
                    if nLeft > 0 and nLeft < threshold:
                        testVar = elaboratedVC[v]
                        elaboratedVC[v] -= 1
                        if elaboratedVC[v] < 0:
                            elaboratedVC[v] = 0
                        #print "N = {0} threshold = {1} Before = {2} After ={3}".format(nLeft,threshold,testVar,elaboratedVC[v])
            
            self.clinic._instantUsageVC += elaboratedVC
            self.clinic._accumulatedUsageVC += elaboratedVC

            storesRequestVC = self.getTreatmentSessionStoresRequestVC(elaboratedVC)
            # This may block until the end of patientWaitInterval!
            yield (get,self,self.clinic.getStore(),
                   curry.curry(getVaccineCollectionAndTweakBuffer,storesRequestVC),
                   self.useVialPriority),(hold,self,self.patientWaitInterval)

            if self.acquired(self.clinic.getStore()):
                #print "%s: got %s"%(self.bName,[(g.getType().bName,g.getCount()) for g in self.got])
                unexpiredList = []
                expiredList = []
                for g in self.got:
                    if g.getAge() is None: expiredList.append(g)
                    else: unexpiredList.append(g)
                for g in expiredList: g.detach(self)
                deliverList, consumeList = self.selectDeliverablesToPrep(unexpiredList, elaboratedTypeRateList)
                #print "%s: deliverList= %s consumeList=%s"%(self.bName, 
                #                                            [(g.getType().bName,g.getCount()) for g in deliverList],
                #                                            [(g.getType().bName,g.getCount()) for g in consumeList])
                
                usedUpList = []
                preppedList = []
                prepFailedList = []
                for g in deliverList:
                    nToPrep = min(g.getCount(), g.getType().countPrep(consumeList))
                    if nToPrep is None or nToPrep>=g.getCount():
                        consumeList, uuL = g.prepForDelivery(consumeList)
                        usedUpList.extend(uuL)
                        preppedList.append(g)
                    elif nToPrep == 0:
                        prepFailedList.append(g)
                    else:
                        subG = g.split(nToPrep)
                        consumeList, uuL = subG.prepForDelivery(consumeList)
                        usedUpList.extend(uuL)
                        preppedList.append(subG)
                        prepFailedList.append(g)
                # consumeList now contains leftovers
                self.readyToConsume(preppedList,usedUpList)
                TAG = abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG
                for g in preppedList+usedUpList:
                    g.detach(self)
                    g.maybeTrack("opened")
                    if not g.getTag(TAG):
                        g.getType().totalTransitHisto += (self.sim.now()-g.creationTime, g.getCount())
                    
                vcReady = self.sim.shippables.getCollectionFromGroupList(preppedList)
                #print "%s: prepFailedList is %s"%(self.bName,[(g.getType().bName,g.getCount()) for g in prepFailedList])
                #print "%s: preppedList is %s"%(self.bName,[(g.getType().bName,g.getCount()) for g in preppedList])
                #print "%s: elaboratedTypeRateList is %s"%(self.bName,[(v.bName,nPatients,nVials) for v,nPatients,nVials in elaboratedTypeRateList])
                        
                leftoversList = [] # format [(v,n), ...]
                for v,nPatients,nVials in elaboratedTypeRateList:
                    if v not in vcReady:
                        treatmentTupleList.append((v,0,nPatients,0))
                    elif vcReady[v]<nVials:
                        nVialsUsed= vcReady[v]
                        treatmentTupleList.append((v,nVialsUsed,
                                                   nPatients,
                                                   nVialsUsed*v.getNDosesPerVial()))
                    else:
                        treatmentTupleList.append((v,nVials,
                                                   nPatients,nPatients))
                        dosesLeftOver= nVials*v.getNDosesPerVial()-nPatients
                        leftoversList.append((v, dosesLeftOver))
                self.saveLeftoverDoses(leftoversList)
                            
                # Shortages can lead to prep failures, which can lead to some of the
                # fetched supplies not being used.  Figure out what to do with them.
                goBackList, discardList = self.keepOrDiscardAfterTreatmentSession(consumeList + prepFailedList)
                #print "%s: goBackList is %s"%(self.bName,[(g.getType().bName,g.getCount()) for g in goBackList])
                #print "%s: discardList is %s"%(self.bName,[(g.getType().bName,g.getCount()) for g in discardList])

                for g in discardList:
                    g.detach(self)
                    g.maybeTrack("discarded")
                
                if len(goBackList)>0:
                    yield put,self,self.clinic.getStore(),goBackList
            else:
                # We've got nothing.
                for v,nPatients,nVials in elaboratedTypeRateList:
                    treatmentTupleList.append((v,0,nPatients,0))

            self.endOfSessionActivities()
            self.recordTreatment(treatmentTupleList)

            # Go back to sleep
            yield hold,self,self.nextTickTime-self.sim.now()
            
    def __repr__(self):
        return "<UseVials(%s)>"%(repr(self.clinic))
    def __str__(self): 
        return "<UseVials(%s)>"%(self.clinic.name)

class UseOrDiscardVials(UseVials):
    def __init__(self,clinic,
                 tickInterval,patientWaitInterval,useVialPriority,
                 startupLatency=0.0):
        """
        This process is just like a UseVials process, except that any vaccine
        left over at the end of a treatment session is discarded.  The store 
        supplying this process is totally cleaned out.  This is the pattern 
        appropriate for vaccination programs that ship in one session's worth 
        of vaccine, use it, and then save nothing.  It's not just the open vials
        that get discarded. *All* the vaccine in the store gets discarded.
        Discarded vaccine gets treated as if it were all open vial waste.  
        
        The paramters are the same as for UseVials:

        clinic (type Clinic): the Clinic to which this is attached
        tickInterval: interval between activations in days
        useVialPriority: 'get' priority for withdrawal of supplies from clinic
        startupLatency: delay before first activation in days
        """
        UseVials.__init__(self,clinic,
                 tickInterval,patientWaitInterval,useVialPriority,
                 startupLatency)
        
    def sortDoseRequirments(self, doseVC):
        """
        The input doseVC is the result of calling the DemandModel for this treatment interval.
        This method returns a tuple of the following lists, in order:
        
            treatmentTupleList= []  # tuple fmt (vax,nVials,nPatients,nTreated), ultimately used for reporting
            elaboratedTypeRateList= [] # tuple fmt (vax,nPatients,nVials), used for downstream usage calculations
            vcList= []              # tuple fmt (vax,nVials), list of needed Deliverables
            notUsedForTreatmentList = [] # Shippables produced by the DemandModel that are not Vaccines.

        If this clinic has leftover doses from previous sessions, this is the time to subtract them
        from the demand in vcList.  UseOrDiscardVials keeps no leftovers, however, so that gets implemented
        here instead.
        """
        treatmentTupleList= []  # tuple fmt (vax,nVials,nPatients,nTreated)
        elaboratedTypeRateList= [] # tuple fmt (vax,nPatients,nVials)
        vcList= []              # tuple fmt (vax,nVials)
        notUsedForTreatmentList = []

        # Can we handle any of them out of leftover vials?
        for v,doses in doseVC.items():
            if isinstance(v, vaccinetypes.VaccineType):
                # Be sure to round up number of vials!
                dosesPerVial = v.getNDosesPerVial()
                
                nVials= (doses+dosesPerVial-1)/dosesPerVial
                elaboratedTypeRateList.append((v,doses,nVials))
                vcList.append((v,nVials))
                
            else:
                # Things like refrigerators or diluent may be in our demand list, but
                # we don't use them to treat patients 
                notUsedForTreatmentList.append((v,doses))
                continue
            
        return (treatmentTupleList, elaboratedTypeRateList, vcList, notUsedForTreatmentList)

    def getTreatmentSessionStoresRequestVC(self, expectedNeedVC):
        """
        This is provided to allow overrides by derived classes.  The input expectedNeedVC will
        include both Deliverables and the Shippables needed to prep them.

        In contrast to the UseVials process, we ask for *every* vaccine in the store's buffer.  
        Unless there is nothing there, in which case we ask for what we would have wanted for 
        actual treatment, in case something shows up during our wait interval.
        """
        wantedVC= self.sim.shippables.getCollectionFromGroupList([g for g in self.clinic.getStore().theBuffer
                                                                  if isinstance(g,vaccinetypes.VaccineGroup)])
        
        if wantedVC.totalCount()==0:
            wantedVC= expectedNeedVC.copy()

        return wantedVC
    
    def saveLeftoverDoses(self, leftoversList):
        """
        leftoversList is a list of (vaccineType, nDoses) tuples in opened-but-not-empty vials
        from a day's treatment session.  
        This method returns nothing.
        
        UseOrDiscardVials never saves leftover doses, so this is easy.
        """
        pass

    def keepOrDiscardAfterTreatmentSession(self,unusedList):
        """
        unusedList is a list of Shippables (like VaccineGroups) which were fetched from the local Store
        for a treatment session but were ultimately never opened.  This function sorts them into two
        categories: goBackList, which contains items returned to the Store, and discardList, containing
        items which are discarded.
        
        UseOrDiscardVials discards everything.
        """
        goBackList = []
        discardList = unusedList[:]
        return goBackList, discardList

class UseOrRecycleVials(UseVials):
    def __init__(self,clinic,
                 tickInterval,patientWaitInterval,useVialPriority,
                 startupLatency=0.0):
        """
        This process is just like a UseVials process, except that any unopened
        vaccine left over at the end of a treatment session is marked for recycling.
        All open vials are discarded.  This is the pattern 
        appropriate for 'outreach' vaccination programs in which there is no local
        storage, as when vaccine arrives in a cold box, treatment happens, and then
        the cold box is collected and returned.  
        
        The paramters are the same as for UseVials:

        clinic (type Clinic): the Clinic to which this is attached
        tickInterval: interval between activations in days
        useVialPriority: 'get' priority for withdrawal of supplies from clinic
        startupLatency: delay before first activation in days
        """
        UseVials.__init__(self,clinic,
                 tickInterval,patientWaitInterval,useVialPriority,
                 startupLatency)
        
    def sortDoseRequirments(self, doseVC):
        """
        The input doseVC is the result of calling the DemandModel for this treatment interval.
        This method returns a tuple of the following lists, in order:
        
            treatmentTupleList= []  # tuple fmt (vax,nVials,nPatients,nTreated), ultimately used for reporting
            elaboratedTypeRateList= [] # tuple fmt (vax,nPatients,nVials), used for downstream usage calculations
            vcList= []              # tuple fmt (vax,nVials), list of needed Deliverables
            notUsedForTreatmentList = [] # Shippables produced by the DemandModel that are not Vaccines.

        If this clinic has leftover doses from previous sessions, this is the time to subtract them
        from the demand in vcList.  UseOrRecycleVials keeps no leftovers, however, so that gets implemented
        here instead.
        """
        treatmentTupleList= []  # tuple fmt (vax,nVials,nPatients,nTreated)
        elaboratedTypeRateList= [] # tuple fmt (vax,nPatients,nVials)
        vcList= []              # tuple fmt (vax,nVials)
        notUsedForTreatmentList = []

        # Can we handle any of them out of leftover vials?
        for v,doses in doseVC.items():
            if isinstance(v, vaccinetypes.VaccineType):
                # Be sure to round up number of vials!
                dosesPerVial = v.getNDosesPerVial()
                
                nVials= (doses+dosesPerVial-1)/dosesPerVial
                elaboratedTypeRateList.append((v,doses,nVials))
                vcList.append((v,nVials))
                
            else:
                # Things like refrigerators or diluent may be in our demand list, but
                # we don't use them to treat patients 
                notUsedForTreatmentList.append((v,doses))
                continue
            
        return (treatmentTupleList, elaboratedTypeRateList, vcList, notUsedForTreatmentList)

    def getTreatmentSessionStoresRequestVC(self, expectedNeedVC):
        """
        This is provided to allow overrides by derived classes.  The input expectedNeedVC will
        include both Deliverables and the Shippables needed to prep them.

        In contrast to the UseVials process, we ask for *every* vaccine in the store's buffer.  
        Unless there is nothing there, in which case we ask for what we would have wanted for 
        actual treatment, in case something shows up during our wait interval.
        """
        wantedVC= self.sim.shippables.getCollectionFromGroupList([g for g in self.clinic.getStore().theBuffer
                                                                  if isinstance(g,vaccinetypes.VaccineGroup)])
        
        if wantedVC.totalCount()==0:
            wantedVC= expectedNeedVC.copy()

        return wantedVC
    
    def saveLeftoverDoses(self, leftoversList):
        """
        leftoversList is a list of (vaccineType, nDoses) tuples in opened-but-not-empty vials
        from a day's treatment session.  
        This method returns nothing.
        
        UseOrRecycleVials never saves leftover doses, so this is easy.
        """
        pass

    def keepOrDiscardAfterTreatmentSession(self,unusedList):
        """
        unusedList is a list of Shippables (like VaccineGroups) which were fetched from the local Store
        for a treatment session but were ultimately never opened.  This function sorts them into two
        categories: goBackList, which contains items returned to the Store, and discardList, containing
        items which are discarded.
        
        UseOrRecycleVials keeps everything, but marks it for recycling.
        """
        goBackList = unusedList[:]
        discardList = []
        return goBackList, discardList

    def selectDeliverablesToPrep(self, availableList, elaboratedTypeRateList):
        """
        availableList is the list of all unexpired Shippable and Deliverable instances fetched from the
        local store for a treatment session- no Deliverable has yet been prepped.  Divide these into
        to categories, the deliverables to be prepped (prepList) and everything else (otherList).
        elaboratedTypeRate list carries actual demand info in the format [(vax,nPatients,nVials), ...]
        
        UseOrRecycleVials gets all supplies from the local Store, but we only want to open enough to
        treat the expected clients.
        """
        prepList = []
        otherList = []
        neededCounts = {}
        for v,_,nVials in elaboratedTypeRateList:
            if nVials>0: 
                if v in neededCounts: neededCounts[v] += nVials
                else: neededCounts[v] = nVials
        for g in availableList:
            v = g.getType()
            n = g.getCount()
            if v in neededCounts and neededCounts[v]>0:
                if neededCounts[v] < n:
                    prepList.append(g.split(neededCounts[v]))
                    otherList.append(g) # which is smaller now
                    neededCounts[v] = 0
                else:
                    prepList.append(g)
                    neededCounts[v] -= n

        return (prepList, otherList)

    def endOfSessionActivities(self):
        """
        This is an opportunity for derived classes to do end-of-session clean-up.  We take this
        opportunity to mark *everything* for recycling.
        """
        for thing in [g for g in self.clinic.getStore().theBuffer if isinstance(g,abstractbaseclasses.Shippable)]:
            thing.setTag(abstractbaseclasses.Shippable.RECYCLE_TAG)
        #pass
    
class UseVialsSilently(UseVials):
    def __init__(self,clinic,
                 tickInterval,patientWaitInterval,useVialPriority,
                 startupLatency=0.0):
        """
        This process is just like a UseVials process, except that any vaccine
        consumption never gets recorded.  This is done so that surrogate clinics can
        silently swallow up vaccine without effecting the statistics for the run.
        """
        UseVials.__init__(self,clinic,tickInterval,patientWaitInterval,
                          useVialPriority,startupLatency)
    def recordTreatment(self,treatmentTupleList):
        """
        This is called internally by the run() method; it is not intended to be called directly
        by the user.
        """
        UseVials.recordTreatment(self, treatmentTupleList, False)
    def readyToConsume(self, preppedList, usedUpList):
        """
        This method exists for the benefit of derived classes, which may want a look at the Deliverable
        and Consumable groups which are actually used in vaccination.
        
        In this case, the method prevents these groups from contributing to collected statistics.
        """
        TAG = abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG
        for g in preppedList+usedUpList: g.setTag(TAG)

class UseOrDiscardVialsSilently(UseOrDiscardVials):
    def __init__(self,clinic,tickInterval,patientWaitInterval,useVialPriority,
                 startupLatency=0.0):
        """
        This process is just like a UseOrDiscardVials process, except that any vaccine
        consumption never gets recorded.  This is done so that surrogate clinics can
        silently swallow up vaccine without effecting the statistics for the run.
        """
        UseOrDiscardVials.__init__(self,clinic,tickInterval,patientWaitInterval,
                                   useVialPriority,startupLatency)
    def recordTreatment(self,treatmentTupleList):
        """
        This is called internally by the run() method; it is not intended to be called directly
        by the user.
        """
        UseOrDiscardVials.recordTreatment(self, treatmentTupleList, False)
        
    def readyToConsume(self, preppedList, usedUpList):
        """
        This method exists for the benefit of derived classes, which may want a look at the Deliverable
        and Consumable groups which are actually used in vaccination.
        
        In this case, the method prevents these groups from contributing to collected statistics.
        """
        TAG = abstractbaseclasses.Shippable.EXCLUDE_FROM_STATS_TAG
        for g in preppedList+usedUpList: g.setTag(TAG)
    

class MonitorStock(PeriodicProcess):
    def __init__ (self,interval,startupLatency,threshold,wh):
        assert(isinstance(wh,Warehouse))
        PeriodicProcess.__init__(self,wh.sim,"MonitorStockProccess_%s"%wh.name,
                                 interval,startupLatency)
        self.wh = wh
        self.threshold = threshold
        if self.wh.noteHolder is not None:
            self.wh.noteHolder.addNote({"gap_cooler_overstock_time":0.0})
            self.wh.noteHolder.addNote({"gap_freezer_overstock_time":0.0})
            self.wh.noteHolder.addNote({"overstock_time":0.0})
            self.wh.noteHolder.addNote({"stockout_time":0.0})
    def cycle(self,timeNow):
        if self.wh.noteHolder is not None:
            supply = self.wh.getStorageRatio()
            overStockFlag = False
            stockoutFlag = True
            gapOverTimeFlag = {}
            for k in supply.keys():
                if k.count("vol_used") == 0:
                    gapOverTimeFlag[k] = False
            for st in supply.keys():
                if st.count("vol_used"):
                    self.wh.noteHolder.addNote({st+"_time":AccumVal(float(supply[st]))})
                else:
                    if self.wh.origCapacityInfoOrInventory is not None:
                        orgStorageSC = self.wh.getOriginalStorageSC()
                        if st in [str(x) for x in orgStorageSC.keys()]:
                            if (supply[st].v * C.storageLotsOfSpace * 1000.0) > orgStorageSC[self.sim.typeManager.getTypeByName(st)]:
                                gapOverTimeFlag[st] = True
                    if supply[st].v > self.threshold:
                        overStockFlag = True
                    if supply[st].v > 0 and st != "roomtemperature":
                        stockoutFlag = False
            if overStockFlag == True:
                self.wh.noteHolder.addNote({"overstock_time":self.interval})  
            if stockoutFlag == True:
                self.wh.noteHolder.addNote({"stockout_time":self.interval})
            for k in gapOverTimeFlag.keys():
                if gapOverTimeFlag[k] is True:
                    self.wh.noteHolder.addNote({"gap_" + str(k) + "_overstock_time":self.interval})
                    
                
