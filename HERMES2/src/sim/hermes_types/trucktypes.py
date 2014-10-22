#!/usr/bin/env python

########################################################################
# Copyright C 2010, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

__doc__=""" trucktypes.py
This module implements methods dealing with trucks, which includes anything that
carries Shippable instances between Warehouses.
"""

_hermes_svn_id_="$Id$"

import math,types,random,collections
from SimPy.Simulation  import *
#from SimPy.SimulationGUIDebug import *
import abstractbaseclasses
import warehouse
import storagetypes
import typemanager
import packagingmodel
import storagemodel
import util
import constants as C
from copy import copy

#: fuelTranslationDict maps the 'Fuel' field of the type record to a tuple containing a short name, a longer name, a string 
#: for rate units for that fuel type, a string for scalar (non-rate) units, the fuel type string for costing purposes, and
#: the charge-by pattern.
fuelTranslationDict = collections.defaultdict(lambda : ('Unknown',None,None,None,None,None),
                                              {'P':('Petrol','Petrol','km/liter','Liter','gasoline','distance'),
                                               'G':('Propane','LP Gas','km/kg','Kg','propane','distance'),
                                               'D':('Diesel','Diesel Fuel','km/liter','Liter','diesel','distance'),
                                               'F':('Free','No Fuel','','None','free','distance')
                                               })

class Truck(abstractbaseclasses.CanOwn, abstractbaseclasses.Trackable, abstractbaseclasses.Costable):
    def __init__(self, truckType, instanceNum):
        super(Truck,self).__init__()
        self.truckType= truckType
        self.sim= self.truckType.sim
        self.tracked= False
        self.name= "%s_#%d"%(self.truckType.name,instanceNum)
        self.fridges= []
        self.stock= []
        self.place= None  # Used for checking attach/detach process- trucks should never detach
        self.packagingModel = packagingmodel.DummyPackagingModel() # to be replaced later
        self.storageModel = storagemodel.DummyStorageModel() # to be replaced later
        for ft in truckType.storageCapacityInfo: ft.createInstance().attach(self, None)
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
    def getSupplySummary(self):
        return self.sim.shippables.getCollection([(vG.vaccineType,vG.nVials)
                                                  for vG in self.stock
                                                  if vG.getAge() is not None])
    def getStorageVolumeWOPackagingOrDiluent(self, v, nVials):
        return nVials * v.getSingletonStorageVolume(False)
    def getNVialsThatFit(self, shippableType, volCC):
        """
        What is the largest integer number of instances of this shippableType that will
        fit in the given volCC, given this location's PackagingModel?
        """
        return self.packagingModel.getNThatFit(volCC, shippableType, self.getStorageModel())
    def getStorageBlocks(self):
        result= []
        doNotUseTag= abstractbaseclasses.Shippable.DO_NOT_USE_TAG
        for sb in [f.getStorageBlocks() for f in self.fridges 
                   if (not isinstance(f,abstractbaseclasses.Shippable) or not f.getTag(doNotUseTag))]:
            result += sb
        return result
    def filterStorageBlocks(self, storageBlocks):
        return storageBlocks
    def calculateStorageFillRatios(self, thisVC, assumeEmpty=False):
        return warehouse.calculateOwnerStorageFillRatios(self,thisVC,assumeEmpty)
    def allocateStorageSpace(self):
        # The newly split groups are attached to the stock list in the background, so
        # ignore them here.  Further, they are getting attached to the stock list as
        # the algorithm proceeds, so we need to copy the list to keep it from changing
        # on the fly.
        result= warehouse.allocateOwnerStorageSpace(self,self.stock[:]+self.fridges[:])
        return result
    def getStock(self):
        return self.stock
    def getCargo(self):
        return self.stock + self.fridges
    def attachStock(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        self.getPackagingModel().repackage(shippable)
        self.stock.append(shippable)
#        shippable.setArrivalTime( self.sim.now() )
    def detachStock(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        if shippable in self.stock:
            self.stock.remove(shippable)
#            if shippable.getAge() is not None: # exclude expired shippables
#                assert hasattr(self,'noteHolder') and self.noteHolder is not None, \
#                    "Attempted to detach %s from %s, but this proc is not associated with a shipping process"%(shippable.getUniqueString(),self.name)
#                tp = shippable.getType()
#                dT = self.sim.now() - shippable.getArrivalTime()
#                key = "%s_daysretention"%tp.name
#                if key in self.noteHolder:
#                    self.noteHolder.addNote({key:dT})
#                else:
#                    self.noteHolder.addNote({key:util.HistoVal(dT)})
        else:
            raise RuntimeError("Internal error: %s not in stock of this %s"%(shippable,self.truckType.name))
    def attachStorage(self,thisFridge,callingProc):
        """
        thisFridge must satisfy isinstance(thisFridge,abstractbaseclasses.CanStore)
        callingProc is the current SimPy Process instance, or None at initialization time.  
        """
        if isinstance(thisFridge,abstractbaseclasses.Shippable):
            self.getPackagingModel().repackage(thisFridge)
        self.fridges.append(thisFridge)
    def detachStorage(self,thisFridge,callingProc):
        """
        thisFridge must satisfy isinstance(thisFridge,abstractbaseclasses.CanStore)
        """
        if thisFridge in self.fridges:
            self.fridges.remove(thisFridge)
        else:
            raise RuntimeError("Internal error: %s not in storage of this %s"%(thisFridge,self.truckType.name))
    def attachIce(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        self.getPackagingModel().repackage(shippable)
        self.stock.append(shippable)
    def detachIce(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        if shippable in self.stock:
            self.stock.remove(shippable)
        else:
            raise RuntimeError("Internal error: %s not in stock of this %s"%(shippable,self.truckType.name))
    def printInventory(self):
        """
        When this method is called the CanOwn instance will print (to sys.stdout) an inventory
        of all its currently attached Shippables.  This is intended as a debugging tool.
        """
        print "Inventory for %s %s:"%(self.__class__.__name__,self.name)
        for f in self.fridges:
            if isinstance(f,abstractbaseclasses.Shippable):
                fTagList = f.getTagList()
            else:
                fTagList = None
            print "    %s: %s: tags %s"%(f.name,f.getType().name,fTagList)
            for b in f.getStorageBlocks():
                print "        type %s: %d / %d CC; contents %s"%(b.storageType.name,
                                                                  int(round(b.volUsed)),int(round(b.volAvail)),
                                                                  [g.getUniqueName() for g in b.contents])
        for s in self.stock:
            if isinstance(s,abstractbaseclasses.Shippable):
                sTagList = s.getTagList()
                sAge = s.getAge()
            else:
                sTagList = None
                sAge = None
            print "    %s: %s count %d age %s tags %s"%\
                (s.getType().name,s.getUniqueName(),s.getCount(),sAge, sTagList)
    def dropTrash(self):
        """
        Disown things like expired vaccines
        """
        self.stock= [g for g in self.stock if g.getAge() is not None]
    def maybeTrack(self,info):
        if self.tracked:
            print '\n%g, "%s", "%s"\n'%(self.truckType.sim.now(),str(self),info)
    def __str__(self):
        return self.name
    def getSim(self):
        return self.sim
    def attemptRestockOfSpecifiedShippable(self,shippableType):
        """
        This method is provided so that outside classes can request a restock if a particular
        ShippableType is available.  It returns True if a restock has been signaled (because
        the ShippableType is available), False otherwise.
        
        This request can come to a truck if, for example, an AlarmedIceFridge instance fires its 
        alarm while the fridge is in transit.  
        """
        return False # We cannot satisfy this request; we're a truck.
    def attach(self,place,callingProc):
        assert self.place is None, "%s:%d is already attached"%(self.name,self.history)
        self.place = place
    def detach(self,callingProc):
        assert self.place is not None, "%s:%d is not attached"%(self.name,self.history)
        raise RuntimeError("Trucks should not detach; tried to detach %s from %s"%(self.name,self.place.name))
    def getType(self):
        """
        Return the base type, e.g. TruckType for a Truck instance.
        """
        return self.truckType
    def getCount(self):         
        """
        Trucks are always singletons
        """
        return 1
    def getUniqueName(self):    
        """
        Provides an opportunity for the class to give a more unique response when the '.name' attribute is
        not unique.
        """ 
        return self.name
    
    def getPendingCostEvents(self):
        return []
    
    def applyToAll(self, filterClass, func, negFilterClass=None, argList=[]):
        """
        Causes the CanOwn to apply all those owned instances for which isinstance(thisInstance,filterClass) is true
        to execute func(thisInstance,*argList) and return a list containing the return values of all those
        function invocations.
        
        In this case, an owned instance is any instance of a TrackableType found in self.stock or self.fridges .
        """
        if negFilterClass is None:
            return [func(g, *argList) for g in [gg for gg in (self.stock+self.fridges) if isinstance(gg, filterClass)]]
        else:
            return [func(g, *argList) for g in [gg for gg in (self.stock+self.fridges) 
                                                if isinstance(gg, filterClass) and not isinstance(gg, negFilterClass)]]

class TruckTypeSkeleton(abstractbaseclasses.ManagedType):
    typeName= 'uninitializedTruck'
    def __init__(self, name, displayName, recDict ):
        """
        In the uninitialized state, storageCapacityInfo is a list of FridgeType instances.  These are
        translated to actual StorageTypes at activation time.
        """
        self.name= name
        if displayName == "":
            self.displayName = name
        else:
            self.displayName = displayName
        self.recDict= recDict
    @classmethod
    def fromRec(cls,recDict,typeManager):
        raise RuntimeError('Internal error- TruckTypeSkeleton.fromRec() should never be called')
    def resetCounters(self): pass
    def summarystring(self):
        str= "Truck type %s: (skeleton)\n"%self.name
        return str
    def statisticsstring(self):
        str= "%s (skeleton)\n"%self.name
        return str
    def getSummaryDict(self):
        return {'Type':'trucktypeskeleton','Name':self.name}
    def activate(self, **keywords): 
        """
        Return a full TruckType instance, which will replace this TruckTypeSkeleton instance.
        """
        assert(keywords.has_key('sim'))
        sim= keywords['sim']
        capacityInfo= self.sim.fridges.fridgeTypeListFromTableRec(self.recDict)
        origStorageCapacityInfo= None  
        if self.sim.perfect is True:
            origStorageCapacityInfo = copy(capacityInfo)
            capacityInfo= self.sim.fridges.perfectFridgeTypeList(origStorageCapacityInfo)
        # All trucks get to store things at room temperature
        capacityInfo.append(self.sim.fridges.getTypeByName('OUTDOORS'))
        truckType= TruckType(sim, self.name, self.displayName, capacityInfo,
                             origStorageCapacityInfo=origStorageCapacityInfo,
                             recDict=self.recDict)
        return truckType
    
class TruckType(abstractbaseclasses.TrackableType):
    typeName= 'truck'
    def __init__(self, sim, name, displayName, storageCapacityInfo, number=1, origStorageCapacityInfo=None,
                 recDict = None):
        """
        storageCapacityInfo is a list of CanStoreType instances
        number is the number of such trucks in the pool
        """
        self.name= name
        self.displayName = displayName
        self.number= int(number)
        self.storageCapacityInfo= storageCapacityInfo[:]
        self.origStorageCapacityInfo = origStorageCapacityInfo
        self.totalTrips= 0
        self.totalKm= 0.0
        self.totalTravelDays= 0.0
        self.instanceCount= 0
        self.recDict = recDict
        
    @classmethod
    def fromRec(cls, rec, typeManager):
        assert(rec.has_key('Name'))
        displayName=rec['Name']
        if rec.has_key('DisplayName'):
            displayName = rec['DisplayName']
        if rec.has_key('Number'):
            return TruckTypeSkeleton(rec['Name'], displayName, rec, int(rec['Number']))
        else:
            return TruckTypeSkeleton(rec['Name'], displayName, rec)
                    
    def createInstance(self):
        """
        This call creates a Truck of this TruckType.
        """
        self.instanceCount += 1
        return Truck(self,self.instanceCount)

    def checkCompatibleDefinition(self,**keywords):
        if keywords.has_key('number') and keywords['number'] != self.number:
            return False
        else:
            return abstractbaseclasses.ManagedType.checkCompatibleDefinition(self, **keywords)
    
    def getNetStorageCapacity(self):
        """
        This call will return the maximum net storage capacity for this truck type
        by running through the storage capacity info and totalling is all up
        """
        myStorageSC = self.sim.fridges.getTotalVolumeSCFromFridgeTypeList(self.storageCapacityInfo)
        myStorageDict = {}
        myStorageDict['cooler'] = self.sim.storage.getTotalCoolVol(myStorageSC)
        myStorageDict['feezer'] = self.sim.storage.getTotalRefrigeratedVol(myStorageSC) - myStorageDict['cooler']
        return myStorageDict

    def getFridgeCollection(self):
        return self.sim.fridges.getCollection([(tp,1) for tp in self.storageCapacityInfo])
    
    def checkStorageCapacity(self, proposedVC, packagingModel, storageModel):
        myStorageSC= self.sim.fridges.getTotalVolumeSCFromFridgeTypeList(self.storageCapacityInfo)
        incomingFridgeSC= proposedVC.copy().splitOut(abstractbaseclasses.CanStoreType) # Don't change proposedVC!!
        myStorageSC += self.sim.fridges.getTotalVolumeSCFromFridgeSC(incomingFridgeSC)
        coldVolAvail= self.sim.storage.getTotalRefrigeratedVol(myStorageSC)
        fSC,cSC,wSC = packagingModel.getStorageVolumeSCTriple(proposedVC, storageModel)
        totVolCC = fSC.totalCount() + cSC.totalCount()
        if totVolCC==0.0:
            r= 1.0
        else:
            r= coldVolAvail/totVolCC
            r= min(1.0,r)
        resultVC= self.sim.shippables.getCollection([(v,r) for v,n in (fSC.items() + cSC.items()) if n>0]
                                                    + [(v,1.0) for v,n in wSC.items() if n>0])
        fridgeVC= self.sim.shippables.getCollection([(v,1.0) for v,n in incomingFridgeSC.items() if n>0.0])
        
        resultVC.replace(fridgeVC)
        return (totVolCC/coldVolAvail, resultVC, totVolCC)               

    def __repr__(self):
        return "<TruckType(%s)>"%(self.name)
    def __str__(self):
        return self.name
    def summarystring(self):
        s= "Truck type %s: %d instances:\n"%\
            (self.name,self.number)
        d= {}
        for fridgeType in self.storageCapacityInfo:
            if fridgeType in d:
                d[fridgeType] += 1
            else:
                d[fridgeType]= 1
        keys= d.keys()
        #keys.sort()
        fStr= ""
        for k in keys:
            if d[k]==1: fStr += "%s + "%k.name
            else: fStr += "%d*%s + "%(d[k],k.name)
        fStr= fStr[:-2] # drop trailing '+'
        s += "   %s\n\n"%fStr
        return s
    def statisticsstring(self):
        str= "%s \n"%self.name
        str += "   Display Name %s\n"%self.displayName
        str += "   Total trips %d\n"%self.totalTrips
        str += "   Total km traveled %g\n"%self.totalKm
        str += "   Total days in transit %g\n"%self.totalTravelDays
        return str
    def getSummaryDict(self):
        return {'Type':'trucktype','Name':self.name, "TotalTrips":self.totalTrips, "TotalKm":self.totalKm,
                "TotalTravelDays":self.totalTravelDays}
    def resetCounters(self):
        self.totalTrips= 0
        self.totalKm= 0.0
        self.totalTravelDays= 0.0
    def recordTransport(self, fromWH, toWH, transitTimeDays, level, conditions):
        self.totalTrips += 1
        self.totalTravelDays += transitTimeDays
        self.totalKm += fromWH.getKmTo(toWH, level, conditions)
        
class TruckTypeManager:
    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All TruckTypes have presumably already been defined within the sim-wide TypeManager.
        """
        self.tm= typeManager
        self.typeClass= TruckType
        
    def getCollection(self, tupleList=[]):
        """
        format of tupleList is [(truckType,n),(truckType,n)...]
        """
        return self.tm.getCollectionImplementing(tupleList, self.typeClass)

    def getTypeByName(self,name,sim=None): 
        if sim is None:
            raise RuntimeError("Internal error: getTypeByName called with no sim set")
        truckType= self.tm.getTypeByName(name, activateFlag=True, sim=sim)
        assert isinstance(truckType,self.typeClass), "%s is not the name of a TruckType"
        return truckType
    
    def validTypeName(self,name): return self.tm.validTypeNameImplementing(name, self.typeClass)
    
    def getActiveTypeNames(self): return self.tm.getActiveTypeNamesImplementing(self.typeClass)

    def getActiveTypes(self): return self.tm.getActiveTypesImplementing(self.typeClass)
    

