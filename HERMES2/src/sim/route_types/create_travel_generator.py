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


__doc__=""" create_travel_generator.py
This is the algorithm that will create a travel generator from a set of steps
"""

_hermes_svn_id_="$Id$"

import ipath

import sys,os,string

import curry
from SimPy.Simulation import *
#from SimPy.SimulationTrace import *
import abstractbaseclasses

import vaccinetypes
import packagingmodel
import storagemodel
from util import StatVal, AccumVal, ContinuousTimeStampAccumVal,SpanTimeStampAccumVal, PushbackIterWrapper, AccumMultiVal, HistoVal
import constants as C
import eventlog as evl
from util import logDebug, logVerbose

import warehouse

def createTravelGenerator(name, stepList, truckType, delayInfo, proc, 
                          totalVC=None, truck=None, scaleVC=None, legStartTime=None, fractionGotVC=None,
                          tripJournal=None, legConditions=None, tripID=None, pendingCostEvents=None):
    """
    This function returns a generator, successive steps of which carry a shipment 
    along a programmed route.  name is a name for the generator, stepList is the
    series of successive actions (see below), truckType is the truck type to be used,
    delayInfo is the delay information (which may be None), and proc is the calling
    process.  The defaulted parameters totalVC, truck, scaleVC, legStartTime,
    fractionGotVC and tripJoural are used to continue an existing trip and should not 
    generally be used by outside callers.
    
    stepList is a list of the form [(stepname,paramTuple),(stepname,paramTuple),...]
    where the valid stepnames and the forms of their associated parameters are:
    
        'gettruck'            (truckSupplierWH,)
        'loadexistingtruck'   (supplierWH, packagingModel, storageModel, totalVC)  totalVC is sum of all requested deliveries
        'load'                (supplierWH, packagingModel, storageModel, totalVC)  this one includes acquiring the truck
        'move'                (transitTime, fromWH, toWH, conditionsString)
        'deliver'             (wh, requestVC, timeToNextShipment)  note that requestVC will be scaled automatically
        'alldeliver'          (wh, requestVC, timeToNextShipment)  requestVC ignored; delivers everything left
        'askanddeliver'       (wh, requestVC, timeToNextShipment)  requestVC ignored; checks quantity before delivery
        'markanddeliver'      (wh, requestVC, timeToNextShipment)  like 'deliver' but marks for recycling
        'allmarkanddeliver'   (wh, requestVC, timeToNextShipment)  like 'alldeliver' but marks for recycling
        'recycle'             (wh, packagingModel, storageModel) pick up recycling
        'unload'              (wh,)            drop off leftovers and recycling
        'finish'              (endingWH, costOwnerWH) 
        
    stepList must start with either gettruck or load, and end with finish.  The location should
    be the same at the start and end, as the truck will be acquired from that location at the
    start and put to that location at the end.
    
    As it is executed, the travel generator appends tuples to the tripJournal, which presumably starts the
    trip empty.  Tuples have the format (stepname, legStartTime, legEndTime, legConditions...) where the
    stepname corresponds to one of the strings above.  legConditions==None is equivalent to legConditions=='normal'.
    Depending on the stepname additional tuple entries may be present, as follows:
        
        ('gettruck',legStartTime,legEndTime,legConditions,truckSupplierW,miscCosts)
        ('loadexistingtruck',legStartTime,legEndTime,legConditions,supplierW,litersLoaded,miscCosts)
        ('load',legStartTime,legEndTime,legConditions,supplierW,litersLoaded,miscCosts)
        ("move",legStartTime,legEndTime,legConditions,fromW,toW,volCarriedOnRouteL,miscCosts)
        (op,legStartTime,legEndTime,legConditions,supplierW,leftVolumeLiter,miscCosts)
          where op is ['deliver','alldeliver','askanddeliver','markanddeliver','allmarkanddeliver']
        ('recycle',legStartTime,legEndTime,legConditions,miscCosts)
        ('unload',legStartTime,legEndTime,legConditions,thisW,totVolLiters,miscCosts)
        ("finish",legStartTime,legEndTime,legConditions,endingW,miscCosts)
        
    """
    #bName = name.encode('utf8')
    bName = name
    routeName = proc.routeName
    RECYCLE_TAG= abstractbaseclasses.Shippable.RECYCLE_TAG # for brevity
    deliveryStepNamesSet= set(['deliver','alldeliver','askanddeliver','markanddeliver','allmarkanddeliver'])
    if tripJournal is None: 
        tripJournal = []
        leftHome= False
    else:
        leftHome= True
    if tripID is None:
        tripID = proc.sim.getUniqueNum()
    finished = False
    #segmentFill = []
    if pendingCostEvents is None:
        pendingCostEvents = []
    try:
        for op,paramTuple in stepList:
            #
            #  Gettruck operation:
            #    params: ( truckSupplierW, )
            #    steps:
            #      get the truck 
            #      legStartTime = now
            #      write start-of-trip notes
            #
            #
            if op == 'gettruck':
                truckSupplierW,  = paramTuple
                assert legStartTime is None, "Internal error: gettruck is not the first step in a loop"
                legStartTime = proc.sim.now()
                logDebug(proc.sim,"%s: ----- acquiring truck at %s at %g"%(bName,truckSupplierW.bName,proc.sim.now()))
                yield get,proc,truckSupplierW.getStore(), \
                   curry.curry(warehouse.fillTruckOrderByTypeFilter,truckType), \
                   proc.shipPriority
                assert len(proc.got)==1
                truck= proc.got[0]
                truck.maybeTrack('acquired by %s'%name)
                truck.noteHolder= proc.noteHolder
                legEndTime= proc.sim.now()
                tripJournal.append(('gettruck',legStartTime,legEndTime,'normal',truckSupplierW,pendingCostEvents))
                pendingCostEvents = []
                logDebug(proc.sim,"%s: ----- truck acquired at %s at %g"%(bName,truckSupplierW.bName,proc.sim.now()))                    

            #
            #  Loadexistingtruck operation: used when a truck is loaded on other than the first stop
            #    params: ( supplierW, truckPackagingModel, truckStorageModel, totalVC )
            #    steps:
            #      calculate truck volume scaling; yields loadFac, scaleVC; scales totalVC
            #      get from the store
            #      apply breakage in storage
            #      legStartTime = now
            #      calculate fractionGot
            #      write start-of-trip notes
            #      applyBreakageInStorage 
            #
            #
            elif op == 'loadexistingtruck':
                legStartTime = proc.sim.now()
                supplierW, truckPackagingModel, truckStorageModel, totalVC = paramTuple
                totalVC = totalVC.copy() # preserve the parameter tuple
                truck.setPackagingModel(truckPackagingModel)
                truck.setStorageModel(truckStorageModel)
                # Check against space in truck
                logDebug(proc.sim,"%s: ----- ready to load %s at %s at %g"%(bName,truck.bName,supplierW.bName,proc.sim.now()))
                stats,scaleVC,totVolCC= truckType.checkStorageCapacity(totalVC, truckPackagingModel, truckStorageModel)
                logDebug(proc.sim,"%s: %s has %s"%(bName,supplierW.bName,supplierW.getSupplySummary()))
                logDebug(proc.sim,"%s: requesting %s"%(bName,totalVC))
                logDebug(proc.sim,"%s: yields scaleVC %s"%(bName,scaleVC))
                proc.sim.evL.log(proc.sim.now(),evl.EVT_REQUEST,totalVC,supplier=supplierW.bName,tripID=tripID,
                                 route=proc.bName)
                totalVC *= scaleVC
                totalVC.roundDown()
                logVerbose(proc.sim,"%s: requesting %s after truck volume scaling"%(bName,totalVC))
                proc.sim.evL.log(proc.sim.now(),evl.EVT_SCALEDREQUEST,totalVC,supplier=supplierW.bName,
                                 tripID=tripID,route=proc.bName)
                yield (get,proc,supplierW.getStore(),
                       curry.curry(warehouse.fillThisOrderGroupFilter,totalVC), 
                       proc.shipPriority),(hold,proc,proc.orderPendingLifetime)
                if proc.acquired(supplierW.getStore()):
                    gotThese= proc.got[:] # shallow copy
                    
                    for g in gotThese:
                        if isinstance(g,abstractbaseclasses.Costable): pendingCostEvents.extend(g.getPendingCostEvents())
                        g.getAge() # to force an age update for the group
                        g.detach(proc)
                    gotTheseVC= proc.sim.shippables.getCollectionFromGroupList(gotThese)
                    fractionGotVC= gotTheseVC/totalVC
    
                    if proc.noteHolder is not None:
                        nActualVaccines= sum([g.getCount() for g in gotThese if isinstance(g.getType(),vaccinetypes.VaccineType)])
                        if nActualVaccines>0: 
                            for stat,val in stats.items():
                                proc.noteHolder.addNote({stat:StatVal(val)})
                            proc.noteHolder.addNote({"Route_L_vol_used_time":AccumVal(totVolCC/C.ccPerLiter)})                        
                            if truck.truckType.origStorageCapacityInfo is not None:
                                storageSC = proc.sim.fridges.getTotalVolumeSCFromFridgeTypeList(truck.truckType.origStorageCapacityInfo)
                                truckVolL = proc.sim.storage.getTotalRefrigeratedVol(storageSC)
                                if totVolCC > truckVolL:
                                    proc.noteHolder.addNote({'gap_route_trip_over':1.0})
                                #segmentFill.append(loadFac)
                        else:
                            proc.noteHolder.addNote({"RouteFill":StatVal(0.0),
                                                     "Route_L_vol_used_time":AccumVal(0.0)})
                            #segmentFill.append(0.0)
                    logDebug(proc.sim,"%s: ----- loaded at %s at %g"%(bName,supplierW.bName,proc.sim.now()))
                    logDebug(proc.sim,"%s: got %s total at %s"%(bName,gotTheseVC,proc.sim.now()))                                                        
                    proc.sim.evL.log(proc.sim.now(),evl.EVT_PICKUP,gotTheseVC,supplier=supplierW.bName,
                                     tripID=tripID,route=proc.bName)
                    if supplierW.breakageModel is not None:
                        gotThese,bL= supplierW.breakageModel.applyBreakageInStorage(supplierW,gotThese)
                        gotTheseVC= proc.sim.shippables.getCollectionFromGroupList(gotThese)
                        fractionGotVC= gotTheseVC/totalVC
                        logDebug(proc.sim,"broken in storage at %s: %s"%(supplierW.bName,proc.sim.shippables.getCollectionFromGroupList(bL)))
                        if supplierW.getNoteHolder() is not None:
                            supplierW.getNoteHolder().addNote(dict([(g.getType().name+'_broken',g.getCount())
                                                                    for g in bL]))
                        # No need to detach broken vials, because they are currently not attached
                                                                            
                    logVerbose(proc.sim,"%s: got %s after breakage in storage (fraction %s) at %g"%(bName,gotTheseVC,fractionGotVC,proc.sim.now()))
                    if supplierW.getNoteHolder() is not None:
                        supplierW.getNoteHolder().addNote(dict([(v.name+'_outshipped',n)
                                                                for v,n in gotTheseVC.items()]))
                    for g in gotThese: 
                        g.attach(truck, proc)
                        g.maybeTrack("shipment")
                    truck.allocateStorageSpace()
                    gotThese= truck.getCargo()
                else:
                    logVerbose(proc.sim,"%s: no supply available at %f"%(bName,proc.sim.now()))
                    # Bail- drive home and unload any recycling.
                    # How can we implement this?  By creating a generator inside this generator, naturally!
                    innerOp, innerParamTuple= stepList[-1]
                    assert innerOp == 'finish', "Internal error in operator order in %s"%name
                    innerEndingW, innerCostOwnerW = innerParamTuple
                    firstMoveStep= [s for s in stepList if s[0]=='move'][0]
                    innerOp2, innerParamTuple2 = firstMoveStep
                    innerTripTime, w1, w2, innerConditions = innerParamTuple2
                    assert w1==innerEndingW and w2==supplierW, \
                        "Internal error: can't find move to get home in %s"%name
                    bailStepList= [('move', (innerTripTime,supplierW,innerEndingW,innerConditions) ),
                                   ('unload',(innerEndingW,)),
                                   ('finish',(innerEndingW,innerCostOwnerW))
                                   ]
                    bailGenerator= createTravelGenerator(bName, bailStepList, truckType, delayInfo, proc,
                                                         totalVC=totalVC, fractionGotVC=fractionGotVC,
                                                         scaleVC=scaleVC, truck=truck, legStartTime=legStartTime,
                                                         tripJournal=tripJournal, legConditions=legConditions,
                                                         tripID=tripID,pendingCostEvents=pendingCostEvents)
                    for val in bailGenerator: yield val
                    break 
                                            
                # Final bookkeeping for this stop
                legEndTime= proc.sim.now()
                litersLoaded = sum([(n*v.getSingletonStorageVolume(True)) for v,n in gotTheseVC.items()])/C.ccPerLiter
                tripJournal.append(('loadexistingtruck',legStartTime,legEndTime,legConditions,supplierW,litersLoaded,pendingCostEvents))
                pendingCostEvents = []
                legConditions = None
                #legStartTime= legEndTime
                    
            #
            #  Load operation: used to load and acquire the truck
            #    params: ( supplierW, truckPackagingModel, truckStorageModel, totalVC )
            #    steps:
            #      calculate truck volume scaling; yields loadFac, scaleVC; scales totalVC
            #      get from the store
            #      get the truck 
            #      apply breakage in storage
            #      legStartTime = now
            #      calculate fractionGot
            #      write start-of-trip notes
            #      applyBreakageInStorage 
            #
            #
            elif op == 'load':
                legStartTime = proc.sim.now()
                supplierW, truckPackagingModel, truckStorageModel, totalVC = paramTuple
                totalVC = totalVC.copy() # preserve the parameter tuple
                # Check against space in truck
                stats,scaleVC,totVolCC= truckType.checkStorageCapacity(totalVC, truckPackagingModel, truckStorageModel)
                logDebug(proc.sim,"%s: ----- ready to load at %s at %g"%(bName,supplierW.bName,proc.sim.now()))
                logDebug(proc.sim,"%s: %s has %s"%(bName,supplierW.bName,supplierW.getSupplySummary()))
                logDebug(proc.sim,"%s: requesting %s"%(bName,totalVC))                                                            
                logDebug(proc.sim,"%s: yields scaleVC %s"%(bName,scaleVC))
                proc.sim.evL.log(proc.sim.now(),evl.EVT_REQUEST,totalVC,supplier=supplierW.bName,
                                 tripID=tripID,route=proc.bName)
                totalVC *= scaleVC
                totalVC.roundDown()
                logVerbose(proc.sim,"%s: requesting %s after truck volume scaling"%(bName,totalVC))
                proc.sim.evL.log(proc.sim.now(),evl.EVT_SCALEDREQUEST,totalVC,supplier=supplierW.bName,
                                 tripID=tripID,route=proc.bName)
                yield (get,proc,supplierW.getStore(),
                       curry.curry(warehouse.fillThisOrderGroupFilter,totalVC), 
                       proc.shipPriority),(hold,proc,proc.orderPendingLifetime)
                if proc.acquired(supplierW.getStore()):
                    gotThese= proc.got[:] # shallow copy
                    
                    logDebug(proc.sim,"%s: ----- acquiring truck at %s at %g"%(bName,supplierW.bName,proc.sim.now()))
                    yield get,proc,supplierW.getStore(), \
                       curry.curry(warehouse.fillTruckOrderByTypeFilter,truckType), \
                       proc.shipPriority
                    assert len(proc.got)==1
                    truck= proc.got[0]
                    truck.maybeTrack('acquired by %s'%name)
                    truck.setPackagingModel(truckPackagingModel)
                    truck.setStorageModel(truckStorageModel)
                    truck.noteHolder= proc.noteHolder
                    legStartTime= proc.sim.now()
                    logDebug(proc.sim,"%s: ----- truck acquired at %s at %g"%(bName,supplierW.bName,proc.sim.now()))
                    
                    for g in gotThese:
                        if isinstance(g,abstractbaseclasses.Costable): pendingCostEvents.extend(g.getPendingCostEvents())
                        g.getAge() # to force a time statistics update for the group
                        g.detach(proc)
                    gotTheseVC= proc.sim.shippables.getCollectionFromGroupList(gotThese)
                    fractionGotVC= gotTheseVC/totalVC
    
                    if proc.noteHolder is not None:
                        nActualVaccines= sum([g.getCount() for g in gotThese if isinstance(g.getType(),vaccinetypes.VaccineType)])
                        if nActualVaccines>0: 
                            for stat,val in stats.items():
                                proc.noteHolder.addNote({stat:StatVal(val)})
                            proc.noteHolder.addNote({"Route_L_vol_used_time":AccumVal(totVolCC/C.ccPerLiter)})                        
                            #segmentFill.append(loadFac)
                        else:
                            proc.noteHolder.addNote({"RouteFill":StatVal(0.0),
                                                     "Route_L_vol_used_time":AccumVal(0.0)})
                            #segmentFill.append(0.0)
                    logDebug(proc.sim,"%s: ----- loaded at %s at %g"%(bName,supplierW.bName,proc.sim.now()))
                    logDebug(proc.sim,"%s: got %s total at %s"%(bName,gotTheseVC,proc.sim.now()))
                                                                            
                    proc.sim.evL.log(proc.sim.now(),evl.EVT_PICKUP,gotTheseVC,supplier=supplierW.bName,
                                     tripID=tripID,route=proc.bName)
                    if supplierW.breakageModel is not None:
                        gotThese,bL= supplierW.breakageModel.applyBreakageInStorage(supplierW,gotThese)
                        gotTheseVC= proc.sim.shippables.getCollectionFromGroupList(gotThese)
                        fractionGotVC= gotTheseVC/totalVC
                        logDebug(proc.sim,"broken in storage at %s: %s"%(supplierW.bName,proc.sim.shippables.getCollectionFromGroupList(bL)))
                                                                            
                        # No need to detach broken vials, because they are currently not attached
                        if supplierW.getNoteHolder() is not None:
                            supplierW.getNoteHolder().addNote(dict([(g.getType().name+'_broken',g.getCount())
                                                                    for g in bL]))
                    logVerbose(proc.sim,"%s: got %s after breakage in storage (fraction %s) at %g"%(bName,gotTheseVC,fractionGotVC,proc.sim.now()))
                    for g in gotThese: 
                        g.attach(truck, proc)
                        g.maybeTrack("shipment")
                    truck.allocateStorageSpace()
                    gotThese= truck.getCargo()
                    if supplierW.getNoteHolder() is not None:
                        supplierW.getNoteHolder().addNote(dict([(v.name+'_outshipped',n)
                                                                for v,n in gotTheseVC.items()]))
                    
                else:
                    logVerbose(proc.sim,"%s: no supply available at %f"%(bName,proc.sim.now()))
                    break
                legEndTime= proc.sim.now()
                ## Compute Volume loaded
                litersLoaded = sum([n*v.getSingletonStorageVolume(True) for v,n in gotTheseVC.items()])/C.ccPerLiter
                tripJournal.append(('load',legStartTime,legEndTime,legConditions,supplierW,litersLoaded,pendingCostEvents))
                pendingCostEvents = []
                legConditions = None
                    
            #
            #  Move operation:
            #    params: (triptime, fromW, toW, conditions)
            #
            #
            elif op == 'move':
                legStartTime = proc.sim.now()  
                t, fromW, toW, conditions = paramTuple
                thisTransitTime = t
                legConditions = conditions
                # see if our truck is delayed
                if delayInfo is not None:
                    delay= delayInfo.getDeliveryDelay()
                    if delay>0.0:
                        logDebug(proc.sim,"%s: shipment is delayed en route by %f days"%(bName,delay))
                        thisTransitTime += delay

                logDebug(proc.sim,"%s moving from %s to %s at %s; transit time will be %s"%(bName,fromW.bName,toW.bName,proc.sim.now(),thisTransitTime))

                # beware: vaccine can expire during this hold!
                yield hold,proc,thisTransitTime

                # We must reconstruct gotThese, since autonomous events happening in transit may
                # have split vaccines.
                gotThese= truck.getCargo()
                        
                if fromW.breakageModel is not None:
                    gotThese,bL= fromW.breakageModel.applyBreakageInTransit(fromW, toW, gotThese)
                    logDebug(proc.sim,"%s: broken in transit from %s: %s"%(bName,fromW.bName,proc.sim.shippables.getCollectionFromGroupList(bL)))
                    for g in bL: 
                        if isinstance(g,abstractbaseclasses.Costable): pendingCostEvents.extend(g.getPendingCostEvents())
                        g.detach(proc)
                gotTheseVC= proc.sim.shippables.getCollectionFromGroupList(gotThese)
                volCarriedOnRouteL = sum([n*v.getSingletonStorageVolume(False) for v,n in gotTheseVC.getTupleList() if isinstance(v,vaccinetypes.VaccineType)])/C.ccPerLiter
                #print "Carried " + str(proc.bName) + " " + str(volCarriedOnRouteL)
                for v,n in gotTheseVC.getTupleList():
                    if isinstance(v,abstractbaseclasses.ShippableType):
                        v.recordTransport(n,fromW,toW,thisTransitTime, toW.category, conditions)
                
                truckType.recordTransport(fromW,toW,thisTransitTime, toW.category, conditions)
                
                if not leftHome:
                    leftHome = True
                    if proc.noteHolder is not None:
                        proc.noteHolder.addNote({"RouteTrips":1})
                
                legEndTime = proc.sim.now()
                tripJournal.append(("move",legStartTime,legEndTime,legConditions,fromW,toW,volCarriedOnRouteL,pendingCostEvents))
                pendingCostEvents = []
            
                
            #
            #  deliver, askanddeliver, and alldeliver operation:
            #    params: (w, vc)
            #    steps:
            #      calculate groupsAllocVC
            #      record info about groupsAllocVC
            #      if groupsAllocVC > 0:
            #        get groupsToPut
            #        if w is a clinic, apply breakage in storage, since UseVials will not.
            #        put groupsToPut
            #        update gotThese and gotTheseVC
            #        make notes about delivery
            #      legEndTime=now(); add leg to tripJournal; legStartTime=legEndTime
            #
            #
            elif op in deliveryStepNamesSet:
                legStartTime = proc.sim.now()
                w, vc, timeToNextShipment= paramTuple
                vc = vc * scaleVC # effect of truck volume scaling
                gotTheseVC= proc.sim.shippables.getCollectionFromGroupList(gotThese)

                if op in ['alldeliver','allmarkanddeliver']:
                    # Last stop- if they will take it, they get everything on the truck.  Some
                    # may end up at room temperature, but that's no worse than staying on the truck.
                    tupleList= [(t,gotTheseVC[t]) for t,v in vc.items() 
                                if v!=0.0 and isinstance(t,vaccinetypes.VaccineType)]
                    tupleList += [(t,v) for t,v in vc.items() if not isinstance(t,vaccinetypes.VaccineType)]
                    groupsAllocVC= proc.sim.shippables.getCollection(tupleList)
                    groupsAllocVC.roundDown()
                elif op == 'askanddeliver':
                    groupsAllocVC = vc*fractionGotVC
                    # we use vc to access the class method here
                    groupsAllocVC = vc.min(proc.sim.model.getDeliverySize(routeName, w, groupsAllocVC, timeToNextShipment,
                                                                          proc.sim.now()),
                                           groupsAllocVC)
                    groupsAllocVC.roundDown()
                else:
                    groupsAllocVC= vc*fractionGotVC
                    groupsAllocVC.roundDown()
                logDebug(proc.sim,"%s: ----- at %s"%(bName,w.bName))
                logDebug(proc.sim,"%s: gotTheseVC is now %s"%(bName,gotTheseVC))
                logDebug(proc.sim,"%s: totalVC now %s"%(bName,totalVC))
                logDebug(proc.sim,"%s: client %s: wants %s; getting %s (frac %s)"%(bName,w.bName,vc,groupsAllocVC,fractionGotVC))     
                if groupsAllocVC.totalCount()>0:
                    groupsToPut,gotThese,failTuples= warehouse.allocateSomeGroups(gotThese,
                                                                                  groupsAllocVC,
                                                                                  proc.sim,
                                                                                  excludeRecycling=True)

                    groupsToPutVC= proc.sim.shippables.getCollectionFromGroupList(groupsToPut)
                    gotTheseVC= proc.sim.shippables.getCollectionFromGroupList(gotThese)
                    logDebug(proc.sim,"%s: about to put %s=%s to %s at %g"%(bName,groupsToPutVC,
                                                                            [g.getUniqueName() for g in groupsToPut],
                                                                            w.bName,proc.sim.now()))
                    logDebug(proc.sim,"%s: gotTheseVC is now %s"%(bName,gotTheseVC))                                                                            
                    proc.sim.evL.log(proc.sim.now(),evl.EVT_DELIVERY,groupsToPutVC,
                                     supplier=supplierW.bName,client=w.bName, tripID=tripID,
                                     route=proc.bName)

                    if w.noteHolder is None:
                        raise RuntimeError("%s unexpectedly has no NoteHolder!"%w.name)

                    if isinstance(w, warehouse.Clinic) and w.breakageModel is not None:
                        # We need to pick up in-storage breakage at the clinic
                        groupsToPut,bL= w.breakageModel.applyBreakageInStorage(w, groupsToPut)
                        logDebug(proc.sim,"%s: broken in clinic storage at %s: %s"%(bName,w.bName,proc.sim.shippables.getCollectionFromGroupList(bL)))
                        w.getNoteHolder().addNote(dict([(g.getType().name+'_broken',g.getCount())
                                                        for g in bL]))
                        for g in bL: 
                            if isinstance(g,abstractbaseclasses.Costable): pendingCostEvents.extend(g.getPendingCostEvents())
                            g.detach(proc)
                    
                    if len(groupsToPut) > 0:
                        markFlag = ( op in ['markanddeliver', 'allmarkanddeliver'])
                        for g in groupsToPut:
                            g.maybeTrack("delivery %s"%w.bName)
                            if isinstance(g,abstractbaseclasses.Costable): pendingCostEvents.extend(g.getPendingCostEvents())
                            g.detach(proc)
                            g.attach(w, proc)
                            if markFlag: g.setTag(RECYCLE_TAG)
                        yield put,proc,w.getStore(),groupsToPut
                    truck.allocateStorageSpace()
                    gotThese= truck.getCargo()
                    if len(groupsToPut) > 0:
                        logVerbose(proc.sim,"%s finished put %s to %s at %g"%(bName,groupsToPutVC,w.bName,proc.sim.now()))
                    else:
                        logVerbose(proc.sim,"%s aborted empty put to %s at %g"%(bName,w.bName,proc.sim.now()))
                    logVerbose(proc.sim,"%s: %s has %s"%(bName,w.bName,w.getSupplySummary()))
                                                
                    totVolCC= 0.0
                    for v,n in groupsToPutVC.getTupleList():
                        if isinstance(v,vaccinetypes.VaccineType):
                            totVolCC += w.getStorageVolumeWOPackagingOrDiluent(v,n)
                    w.noteHolder.addNote({"tot_delivery_vol":
                                          totVolCC/C.ccPerLiter})
                    w.noteHolder.addNote(dict([(v.name+'_delivered',n)
                                                            for v,n in groupsToPutVC.items()]))

                # Final bookkeeping for this stop
                totalVC -= vc
                ## get the volume of remaining vaccines
                leftVolumeLiter = sum([n*v.getSingletonStorageVolume(True) for v,n in totalVC.getTupleList() if isinstance(v,vaccinetypes.VaccineType)])/C.ccPerLiter
                
                legEndTime= proc.sim.now()
                tripJournal.append((op,legStartTime,legEndTime,legConditions,supplierW,leftVolumeLiter,pendingCostEvents))
                pendingCostEvents = []
                legConditions = None
                #legStartTime= legEndTime

            #
            # Recycle operation:
            #   params: (w, truckPackagingModel, truckStorageModel)
            #   steps:
            #      pick up recycling
            #      if any recycling:
            #        apply breakage in storage to recycling                    
            #
            elif op == "recycle":
                legStartTime = proc.sim.now()
                w,truckPackagingModel,truckStorageModel = paramTuple
                truck.setPackagingModel(truckPackagingModel)
                truck.setStorageModel(truckStorageModel)
                # Pick up recycling, if any
                yield (get,proc,w.getStore(),warehouse.recyclingGroupFilter,
                       proc.shipPriority),(hold,proc,warehouse.Warehouse.shortDelayTime)
                if proc.acquired(w.getStore()):
                    newRecycle= proc.got[:]

                    if w.getNoteHolder() is None:
                        raise RuntimeError("%s unexpectedly has no NoteHolder!"%w.name)

                    if w.breakageModel is not None:
                        newRecycle,bL= w.breakageModel.applyBreakageInStorage(w, newRecycle)
                        logDebug(proc.sim,"%s: recycling broken in storage at %s: %s"%(bName,w.bName,proc.sim.shippables.getCollectionFromGroupList(bL)))
                        w.getNoteHolder().addNote(dict([(g.getType().name+'_broken',g.getCount())
                                                        for g in bL]))
                        for g in bL:
                            if isinstance(g,abstractbaseclasses.Costable): pendingCostEvents.extend(g.getPendingCostEvents())
                            g.detach(proc)
                    
                    if len(newRecycle)>0:
                        for g in newRecycle:
                            if isinstance(g,abstractbaseclasses.Costable): pendingCostEvents.extend(g.getPendingCostEvents())
                            g.detach(proc)
                            g.attach(truck, proc)
                        newRecycleVC = proc.sim.shippables.getCollectionFromGroupList(newRecycle)
                        logVerbose(proc.sim,"%s: got recycling %s at %g"%(bName,newRecycleVC,proc.sim.now()))
                        w.getNoteHolder().addNote(dict([(v.name+'_recycled',n)
                                                        for v,n in newRecycleVC.items()]))
                        proc.sim.evL.log(proc.sim.now(),evl.EVT_RECYCLE,newRecycleVC,supplier=w.bName,
                                         tripID=tripID,route=proc.bName)
                        truck.allocateStorageSpace()
                        gotThese= truck.getCargo()
                        gotTheseVC= proc.sim.shippables.getCollectionFromGroupList(gotThese)
                    else:
                        logDebug(proc.sim,"%s: nothing unbroken to recycle at %f"%(bName,proc.sim.now()))
                else:
                    logDebug(proc.sim,"%s: nothing to recycle at %f"%(bName,proc.sim.now()))
                    # We must reconstruct gotThese, since autonomous events happening while
                    # we were waiting for the recycling pickup may have split vials
                    gotThese= truck.getCargo()
                
                legEndTime = proc.sim.now()
                tripJournal.append(('recycle',legStartTime,legEndTime,legConditions,pendingCostEvents))
                pendingCostEvents = []

            #
            # Unload operation:
            #   params: (w,)
            #   steps:
            #     No breakage, because it was picked up in the 'move' and 'delivery' steps
            #     No recordTransport, because 'move' did that.
            #     put the leftovers
            #     update the trip journal
            #
            elif op == 'unload':
                legStartTime = proc.sim.now()
                totVolCC = 0.0
                w, = paramTuple

                leftovers= [g for g in gotThese 
                            if isinstance(g.getType(),vaccinetypes.VaccineType) or 
                            (isinstance(g, abstractbaseclasses.Shippable) and g.getTag(RECYCLE_TAG))]

                if len(leftovers) > 0:
                    for g in leftovers:
                        g.maybeTrack("recycling delivery %s"%w.bName)
                    leftoversVC= proc.sim.shippables.getCollectionFromGroupList(leftovers)
                    logVerbose(proc.sim,"%s about to put %s to %s for recycling at %g"%(bName,leftoversVC,w.bName,proc.sim.now()))
                    proc.sim.evL.log(proc.sim.now(),evl.EVT_RECYCLEDELIVERY,leftoversVC,client=w.bName,
                                     tripID=tripID,route=proc.bName)
                    for g in leftovers:
                        if isinstance(g,abstractbaseclasses.Costable): pendingCostEvents.extend(g.getPendingCostEvents())
                        g.detach(proc)
                        g.attach(w.getStore(), proc)
                    yield put,proc,w.getStore(),leftovers
                    if w.noteHolder is None:
                        raise RuntimeError("Noteholder for %s is unexpectedly None!"%w.name)
                    else:
                        for v,n in leftoversVC.getTupleList():
                            if isinstance(v,vaccinetypes.VaccineType):
                                totVolCC += w.getStorageVolumeWOPackagingOrDiluent(v,n)
                        w.noteHolder.addNote({"tot_delivery_vol":
                                              totVolCC/C.ccPerLiter})
                        w.noteHolder.addNote(dict([(v.name+'_recyclingdelivery',n)
                                                   for v,n in leftoversVC.items()]))
                    truck.allocateStorageSpace()
                else:
                    logVerbose(proc.sim,"%s put nothing to %s for recycling at %g"%(bName,w.bName,proc.sim.now()))
                    if w.noteHolder is None:
                        raise RuntimeError("Noteholder for %s is unexpectedly None!"%w.name)
                    else:
                        w.noteHolder.addNote({"tot_delivery_vol":0.0})
                    
                legEndTime= proc.sim.now()
                tripJournal.append(('unload',legStartTime,legEndTime,legConditions,w,totVolCC/C.ccPerLiter,pendingCostEvents))
                pendingCostEvents = []
                legConditions = None
                
            #
            # Finish operation:
            #   params: (endingW, costOwnerW)
            #   steps:
            #     release the truck
            #     make the final entry in the trip journal
            #
            elif op == 'finish':
                endingW, costOwnerW = paramTuple
                tripJournal.append(("finish",legStartTime,proc.sim.now(),legConditions,endingW,pendingCostEvents))
                pendingCostEvents = []
                legConditions = None
                truck.dropTrash()
                truck.maybeTrack('released by %s'%name)
                assert len(truck.getStock())==0, "Released non-empty truck"
                # call discharge on all CanStore objects on the truck!!!
                for fridge in truck.getFridges():
                    fridge.discharge(proc)

                truck.setPackagingModel(packagingmodel.DummyPackagingModel())
                truck.setStorageModel(storagemodel.DummyStorageModel())
                delattr(truck,"noteHolder")
                yield put,proc,endingW.getStore(),[truck]
                truck= None
                if proc.noteHolder is None:
                    raise RuntimeError("This route lacks noteHolder needed for accounting!")
                else:
                    if hasattr(proc, 'getPerDiemModel'):
                        perDiemModel = proc.getPerDiemModel()
                        costMgr = proc.sim.costManager
                        tripNotes = costMgr.generateTripCostNotes(truckType,
                                                                  costOwnerW.reportingLevel,
                                                                  costOwnerW.conditions,
                                                                  tripJournal,
                                                                  endingW,
                                                                  perDiemModel)
                        proc.noteHolder.addNote(tripNotes)
                    else:
                        raise RuntimeError("proc %s has no PerDiemModel" %
                                           proc.name)
                segmentCount = 0
                for journalEntry in tripJournal:
                    if journalEntry[0] == "move":
                        #if journalEntry[6] > 1000.0:
                        #    print "Journ " + str(journalEntry[6])
                        proc.noteHolder.addNote({"triptimes_timestamp":SpanTimeStampAccumVal(journalEntry[6],(journalEntry[1],journalEntry[2]))})

                        if not hasattr(proc, 'triptimeKeys'):
                            proc.triptimeKeys = ("volumeCarried", "startTime", "endTime")
                        proc.noteHolder.addNote({"triptimes_multival":AccumMultiVal(proc.triptimeKeys, 
                                                                                    journalEntry[6],
                                                                                    journalEntry[1],
                                                                                    journalEntry[2])})
                        segmentCount += 1 
                finished = True
                    
            else:
                raise RuntimeError("Internal error in %s: Inconsistency in stepList"%name)

    except GeneratorExit:
        # The close method of the generator was called.
        if not finished:
            # Early exit- we could put clean-up code here, but it would have to not include
            # any yields.  
            pass
