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


__doc__=""" fridgetypes.py
This module produces object instances which implement the characteristics of
different types of refrigerators and freezers, by make and model.  These
instances provide the storage capacity used by warehouses and trucks.
"""

_hermes_svn_id_="$Id$"

import weakref
import collections
import abstractbaseclasses
import trackabletypes
import storagetypes
import constants as C
import warehouse
import copy
from csv_tools import castTypes
from enums import StorageTypeEnums as ST

#: energyTranslationDict maps the 'Energy' field of the type record to a tuple containing a short name, a longer name, a string 
#: for rate units for that energy type, a string for scalar (non-rate) units, the fuel type string for costing purposes, and
#: the charge-by pattern.
energyTranslationDict = collections.defaultdict(lambda : ('Unknown',None,None,None,None,None),
                                                {'E':('Electric','Electric Mains','KwH/day','Kilowatt Hour','electric','time'),
                                                 'K':('Kerosene','Kerosene','liters/day','Liter','kerosene','time'),
                                                 'G':('Propane','LP Gas','Kg/day','Kg','propane','time'),
                                                 'P':('Petrol','Petrol','liters/day','Liter','gasoline','time'),
                                                 'S':('Solar','Solar Power','Kw','Installed Kilowatt','solar','instance'),
                                                 'I':('Ice','Ice','liters/charge','Liter','ice','charge'),
                                                 'B':('BlueIce','Blue Ice','liters/charge','Liters','ice','charge'),
                                                 'EK':('Electric/Kerosene','Electric with option for Kerosene','KwH/day','Kilowatt Hour','electric','time'),
                                                 'KE':('Kerosene/Electric','Kerosene with option for Electric','liters/day','Liter','kerosene','time'),
                                                 'EG':('Electric/Propane','Electric with option for Propane','KwH/day','Kilowatt Hour','electric','time'),
                                                 'GE':('Propane/Electric','LP Gas with option for Electric','Kg/day','Kg','propane','time'),
                                                 })

def fridgeDisplayNameFromRec(rec):
    """
    A standard way to construct an ad-hoc display name from a FridgeTyep record
    """
    nameString = ""
    if 'Make' in rec and rec['Make'] is not None:
        nameString+=str(rec['Make']) + " "
    if 'Model' in rec and rec['Model'] is not None:
        nameString+=str(rec['Model']) + " "
    if 'Year' in rec and rec['Year'] is not None \
        and rec['Year'] != 'YearUnk':
        nameString+= "("+str(rec['Year']) + ")"
    if 'Energy' in rec and rec['Energy'] is not None \
        and rec['Energy'] != 'U':
        if energyTranslationDict.has_key(rec['Energy']):
            nameString+= ": " +  energyTranslationDict[rec['Energy']][0]
    
    return nameString
        

class FridgeType(abstractbaseclasses.CanStoreType, abstractbaseclasses.NonScalingType):
    typeName= 'refrigerators'
    def __init__(self, typeManager, recDict, instanceClassName):
        """
        name is intended to describe a type of refrigerator, e.g. 'GeneralElectric_model371'
        storageCapacityInfo is a list of (storageType,volumeInCCs) tuples
        """
        super(FridgeType,self).__init__()
        self.sim= typeManager.sim
        self.name= recDict['Name']
        self.storageCapacityInfo= self.storageTupleListFromTableRec(recDict, typeManager)
        self.instanceClassName= instanceClassName 
        self.recDict= recDict # Because some derived classes want extra columns
        self.instanceCount= 0
        self.nCreated= 0

    def storageTupleListFromTableRec(self,recDict,typeManager):
        """
        Given a dict representing a table record of the sort provided by parseCSV(), 
        return a list of tuples of the form [(storageType,volInCC),...] built from
        all record entries the names of which match storage type names (like "cooler").
        The record entries are expected to be in liters.
        """
        storage= []
        
        for stName in typeManager.getActiveTypeNamesImplementing(storagetypes.StorageType):
            if stName in recDict and recDict[stName] not in ['','NA']:
                storage.append((typeManager.getTypeByName(stName),C.ccPerLiter*float(recDict[stName])))
        return storage

    @classmethod
    def fromRec(cls,recDict,typeManager):
        assert 'Name' in recDict, 'record has no "Name" field'
        assert any([kName in recDict for kName in typeManager.getActiveTypeNamesImplementing(storagetypes.StorageType)]),\
               'record contains no storage volume information'
        if 'ClassName' in recDict and recDict['ClassName'] is not None \
                and recDict['ClassName']!='':
            className= recDict['ClassName']
        else:
            className= 'Fridge'
        fridgeInstanceClass = globals()[className]
        return fridgeInstanceClass.classPartner(typeManager, recDict, className)

    def getDisplayName(self):
        return fridgeDisplayNameFromRec(self.recDict)

    def createInstance(self,count=1,name=None,currentAge=0.0,tracked=False):
        """
        Create an instance of this FridgeType.  The instance will be a Fridge.
        """
        if count!=1:
            raise RuntimeError("Internal error: Fridge creation with non-unit count")
        self.instanceCount += 1
        self.nCreated += 1
        if name is None:
            name= "%s#%d"%(self.name,self.instanceCount)
        return globals()[self.instanceClassName](self, name=name, currentAge=currentAge, tracked=tracked )

    def __repr__(self):
        return "<FridgeType(%s)>"%self.name

    def __str__(self):
        return self.name

    def summarystring(self):
        volStr= ""
        for st,v in self.storageCapacityInfo: volStr += "%s: %f; "%(st.name,v)
        return self.name \
               + '\n   Volumes in CC: ' + volStr \
               +'\n\n'

    def statisticsstring(self):
        d= self.getSummaryDict()
        return "%s : %d instances, not shippable"%(self.name,d['NCreatedAbsolute'])

    def getSummaryDict(self):
        d= {'Type':'fridgetype','Name':self.name}
        d['NCreated']= self.nCreated
        d['NCreatedAbsolute']= self.instanceCount
        return d

    def resetCounters(self):
        self.nCreated = 0

    def getStorageCapacityInfo(self):
        return self.storageCapacityInfo
    
    def getTotalVolByName(self,storeTypeName):
        vol = 0.0
        for storageCapacity in self.storageCapacityInfo:
            if str(storageCapacity[0]) == storeTypeName:
                vol += storageCapacity[1]
        return vol
    
    @classmethod
    def getColumnTypeDict(cls):
        return {
                u'BaseCostYear':[castTypes.POSITIVE_INT, castTypes.EMPTY_IS_NONE],
                u'PowerRate':[castTypes.FLOAT, castTypes.EMPTY_IS_NONE],
                u'BaseCost':[castTypes.FLOAT, castTypes.EMPTY_IS_NONE]
                }

class ShippableFridgeType(FridgeType, abstractbaseclasses.ShippableType, abstractbaseclasses.DeliverableType):
    typeName= 'shippableRefrigerators'
    def __init__(self, typeManager, recDict, instanceClassName):
        """
        name is intended to describe a type of refrigerator, e.g. 'GeneralElectric_model371'
        storageCapacityInfo is a list of (storageType,volumeInCCs) tuples
        """
        super(ShippableFridgeType,self).__init__(typeManager, recDict, instanceClassName)
        self.storagePriorityList= None # filled in when first requested
        self.nBroken= 0 # need to handle this in case a refrigerator is 'broken in transit'
        self.absoluteNBroken= 0
        self.totalKm= 0.0
        self.totalInstanceKm= 0.0
        self.totalTravelDays= 0.0
        self.totalInstanceTravelDays= 0.0

    @classmethod
    def fromRec(cls,recDict,typeManager):
        assert 'Name' in recDict, 'record has no "Name" field'
        assert any([kName in recDict for kName in typeManager.getActiveTypeNamesImplementing(storagetypes.StorageType)]),\
               'record contains no storage volume information'
        if 'ClassName' in recDict and recDict['ClassName'] is not None \
                and recDict['ClassName']!='':
            className= recDict['ClassName']
        else:
            className= 'ShippableFridge'
        return ShippableFridgeType(typeManager, recDict, className)

    def createInstance(self,count=1,name=None,currentAge=0.0,tracked=False):
        """
        Create an instance of this ShippableFridgeType.  The instance will be a ShippableFridge.
        """
        if count!=1:
            raise RuntimeError("Internal error: Fridge creation with non-unit count")
        self.instanceCount += 1
        self.nCreated += 1
        if name is None:
            name= "%s#%d"%(self.name,self.instanceCount)
        return globals()[self.instanceClassName](self, name=name, currentAge=currentAge, tracked=tracked )

    def __repr__(self):
        return "<ShippableFridgeType(%s)>"%self.name

    def __str__(self):
        return self.name


    def getNDosesPerVial(self):
        return 1
    
    def canStore(self, storageType):
        return True

    def wantStore(self, storageType):
        return True

    def preferredStore(self):
        # would prefer warm but mostly doesn't matter.
        return ST.STORE_WARM, {ST.STORE_WARM: 1.0, ST.STORE_COOL: 1.01, ST.STORE_FREEZE: 1.02}

    def canKeepOpenVials(self,howLongOpen):
        """
        If the first dose from a vial has been used, can the rest still be used after 'howLongOpen' days?  
        Obviously this is nonsense for Shippable things that don't actually hold multipe doses.
        """
        return False

    def recordBreakage(self,nVials):
        self.nBroken += nVials

    def recordTreatment(self,nTreated,nApplied,nVialsUsedForTreatment):
        if nApplied!=0:
            print '######## Treated %d %d %d'%(nTreated,nApplied,nVialsUsedForTreatment)
        if nTreated!=0:
            raise RuntimeError('Internal error: Used a Fridge to treat a patient')
    
    def recordTransport(self, nInstances, fromWH, toWH, transitTimeDays, level, conditions):
        km= fromWH.getKmTo(toWH, level, conditions)
        self.totalKm += km
        self.totalInstanceKm += nInstances*km
        self.totalTravelDays += transitTimeDays
        self.totalInstanceTravelDays += nInstances*transitTimeDays

    def statisticsstring(self):
        d= self.getSummaryDict()
        if d['ShipTimeDays'] == 0.0:
            return "%s : none shipped"%self.name
        else:
            s= "%s \n"%self.name
            s += "   Total shipping time %g days\n"%d['ShipTimeDays']
            s += "   Total product of instance count and shipping time %g days\n"%d['ShipInstanceTimeDays']
            s += "   Total shipping distance %g km\n"%d['ShipKm']
            s += "   Total product of instance count and shipping distance %g km\n"%d['ShipInstanceKm']
            s += "   Broke %d instances in storage or transit\n"%d['NBroken']
            s += "\n"
            return s

    def getSummaryDict(self):
        d= super(ShippableFridgeType,self).getSummaryDict()
        d['Type']= 'shippablefridgetype'
        d['ShipTimeDays']= self.totalTravelDays
        d['ShipInstanceTimeDays']= self.totalInstanceTravelDays
        d['ShipKm']= self.totalKm
        d['ShipInstanceKm']= self.totalInstanceKm
        d['NBroken']= self.nBroken
        d['NBrokenAbsolute']= self.absoluteNBroken
        return d

    def resetCounters(self):
        super(ShippableFridgeType,self).resetCounters()
        self.nBroken= 0 # need to handle this in case a refrigerator is 'broken in transit'
        self.totalKm= 0.0
        self.totalInstanceKm= 0.0
        self.totalTravelDays= 0.0
        self.totalInstanceTravelDays= 0.0
    
    def getStoragePriorityList(self):
        if self.storagePriorityList is None:
            assert hasattr(self,'sim'), "This %s has not been decorated with 'sim' by TypeManager"%self.typeName
            self.storagePriorityList= [self.sim.storage.roomtempStorage()]
        return self.storagePriorityList

    def addPackageType(self, packageType):
        """
        Assert that this ShippableType may come in the given packageType.  Neither the
        ShippableType nor packageType is made active as a result of this call.
        """
        raise RuntimeError('Tried to register package type %s for the %s %s'%(packageType.name,self.typeName))

    def getLargestPackageType(self):
        """
        returns the packagetypes.PackageType value corresponding to the largest valid package for this
        ShippableType, or 'None' if no PackageTypes are defined.  The 'None' value thus corresponds to
        the implied singleton package.
        
        Fridges travel as singletons.
        """
        return None

    def getPackageTypeList(self):
        """
        Returns (a shallow copy of) the list of all valid package types for this Shippable, in order.  
        """
        raise RuntimeError("called getPackageTypeList for a %s"%self.__class__.__name__)
    
    def activate(self, **keywords): 
        """
        We must take this opportunity to make sure any required types are also activated.
        """
        retval = super(ShippableFridgeType,self).activate(**keywords)
        assert retval==self, "Internal error: there is a problem with the Deliverable inheritence hierarchy"
        for reqType in self.getRequiredToPrepSC(1).keys():
            self.manager.getTypeByName(reqType.name)
        
        return retval
    
    def getSingletonStorageVolume(self, withDiluent):
        """
        Output is in CCs.  This is total shelf space to store this Fridge, including 
        packaging- that is, the external volume of the Fridge including the box it comes in.
        
        We'll worry about returning a realistic value when we start tracking room temperature space.
        Obviously fridges don't come with 'diluent'.
        """
        return 1.0    
    
abstractbaseclasses.ShippableType.register(ShippableFridgeType) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.CanStoreType.register(ShippableFridgeType) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.NonScalingType.register(ShippableFridgeType) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.DeliverableType.register(ShippableFridgeType) # @UndefinedVariable because PyDev can't see abc.register()


class Fridge(abstractbaseclasses.CanStore, abstractbaseclasses.Costable):
    """
    This is basically an instance of a FridgeType.  
    fridgeType is the creating type.
    storageCapacityInfo is a list of (storageType,volumeInCCs) tuples
    """
    classPartner = FridgeType
    class StorageBlock:
        def __init__(self, fridge, storageType, volAvail):
            """
            fridge is a Fridge instance (*not* a FridgeType)
            The others are a StorageType instance and a volume in CC.
            """
            self.fridge= weakref.proxy(fridge)
            self.storageType= storageType
            self.volAvail= volAvail
            self.volUsed= 0.0
            self.contents= []
        def store(self,vaccineGroup):
            assert self.fridge.place is not None, "Attempt to store in unattached fridge"
            withDiluent = self.fridge.place.getStorageModel().getStoreVaccinesWithDiluent(vaccineGroup.getType())
            vol = vaccineGroup.getStorageVolume(self.storageType,withDiluent) # includes packaging
            if vol+self.volUsed<=self.volAvail+C.epsilon:
                self.volUsed += vol
                self.contents.append(vaccineGroup)
                #SILLY_CHECK_FOR_OUTDOORS
                if self.volAvail == 1000000000000:
                    vaccineGroup.setStorage(storagetypes.OUTDOORS, withDiluent)
                else:
                    vaccineGroup.setStorage(self.storageType, withDiluent)
            else:
                print "%f: %f: %f"%(vol,vol+self.volUsed,self.volAvail)
                raise RuntimeError('Overfilled StorageBlock of %s for %s %s'%\
                                   (self.fridge.place.name,self.fridge.fridgeType.name,self.storageType.name))
        def freeVol(self):
            return self.volAvail - self.volUsed
        def getNVialsThatFit(self,vaccineType):
            assert self.fridge.place is not None, "Attempt to calculate for unattached fridge"
            return self.fridge.place.getNVialsThatFit(vaccineType,self.volAvail - self.volUsed)
        def clear(self):
            self.volUsed= 0.0
            self.contents= []
        def __str__(self): 
            return "StorageBlock(%s:%g)"%(self.storageType.name,self.volAvail)
        def __repr__(self):
            return "StorageBlock(%s:%g)"%(self.storageType,self.volAvail)

    def __init__(self, fridgeType, name=None, currentAge=0.0, tracked=False):
        """
        This constructor is not meant to be called by the user- use FridgeType.createInstance() instead!
        
        fridgeType is the creating type.
        """
        abstractbaseclasses.CanStore.__init__(self)
        abstractbaseclasses.Costable.__init__(self)
        self.fridgeType= fridgeType
        self.place= "Never" # must be attached before this storage can be used
        self.allStorageBlocks= []
        for st,vol in fridgeType.getStorageCapacityInfo():
            self.allStorageBlocks.append(Fridge.StorageBlock(self,st,vol))
        self.storageBlocks= [] # initialized at attach time
        self.currentExternalStorage= self.fridgeType.sim.storage.roomtempStorage()
        self.ageBase= self.fridgeType.sim.now()-currentAge
        self.tracked= tracked
        self.name= name
        self.history= 1
        self.tags= set()
        #if name[:18]=='N_LargeCarrier_U_I': self.tracked= True
        self.maybeTrack("creation")
    
    def getUniqueName(self):    
        """
        Provides an opportunity for the class to give a more unique response when the '.name' attribute is
        not unique.
        """ 
        return self.name

    def getType(self):
        """
        Return the base type, e.g. FrideType for a Fridge instance.
        """
        return self.fridgeType 
    
    def getCount(self):
        """
        Fridges always come in singletons
        """
        return 1

    def setTag(self,tag):
        """
        tag can be any hashable- set the tag to 'true'.  Tags which have never been set are false.
        """
        self.tags.add(tag)
        self.maybeTrack('set tag %s'%tag)
    def clearTag(self,tag):
        """
        tag can be any hashable- set the tag to 'false'.  Tags which have never been set are false.
        """
        self.tags.discard(tag)
        self.maybeTrack('clear tag %s'%tag)
        
    def getAge(self):
        return None
    
    def getTag(self,tag):
        """
        tag can be any hashable- return true if that tag has been set, false if it has been cleared or never was set.
        """
        return tag in self.tags
    def getTagList(self):
        """
        return a list of all true tags.
        """
        return [t for t in self.tags]
        
    def getStorageBlocks(self):
        """
        Returns the storage blocks *provided by* this instance.
        """
        return self.storageBlocks
    def recharge(self, callingProc):
        """
        This corresponds to replacing the ice, refilling the gas tank or the equivalent.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        """
        self.ageBase= self.fridgeType.sim.now()
    def discharge(self, callingProc):
        """
        This corresponds to removing the ice, emptying the gas tank or the equivalent; the
        expectation is that it will leave the Fridge in a 'failed' state.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        """
        pass
    def attach(self,place,callingProc):
        # this is something of a stupid hack
        # At startup, if a fridge is attached to a warehouse the fridge should default to on.
        # If the fridge starts as attached to a truck it should default to off.
        # deal with that here.
        if self.place is not None:
            if self.place == "Never":
                self.place = None
                if isinstance(place, abstractbaseclasses.Trackable):
                    self.discharge(callingProc)
        
        assert self.place is None, "%s:%d is already attached"%(self.name,self.history)
        self.place= weakref.proxy(place) # Avoid loop graph for easier GC
        place.attachStorage(self, callingProc)
        self.storageBlocks= self.place.filterStorageBlocks(self.allStorageBlocks)
        self.maybeTrack("attach to %s"%self.place.name)
    def detach(self,callingProc):
        assert self.place is not None, "%s:%d is not attached"%(self.name,self.history)
        self.place.detachStorage(self, callingProc)
        self.maybeTrack("detach from %s"%self.place.name)
        self.place= None
    def maybeTrack(self,info):
        if self.tracked:
            print '\n%g, "%s", "%s"\n'%(self.fridgeType.sim.now(),str(self),info)
    def __str__(self):
        return "<%s>"%(self.name)
    def __repr__(self):
        s= ""
        for bl in self.getStorageBlocks():
            s += "%s: %f CC available, %f used; "%(bl.storageType.name,bl.volAvail,bl.volUsed)
        if s!="": s= s[:-2] # drop tailing ;
        return "<%s(%s)>"%(self.fridgeType.name,s)
    def getPendingCostEvents(self):
        return []

class ChainedFridge(Fridge):
    pass

abstractbaseclasses.CanStore.register(ChainedFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.Costable.register(ChainedFridge) # @UndefinedVariable because PyDev can't see abc.register()

class ElectricFridge(Fridge):
    classPartner = FridgeType
    def __init__(self, fridgeType, name=None, currentAge=0.0, tracked=False):
        Fridge.__init__(self, fridgeType, name=name, currentAge=currentAge, tracked=tracked)
        #if fridgeType.recDict['Now']
        if fridgeType.recDict['NoPowerHoldoverDays'] == None or fridgeType.recDict['NoPowerHoldoverDays'] == 0.0 :
            self.noPowerHoldoverDays = 0.00001
        else:
            self.noPowerHoldoverDays = float(fridgeType.recDict['NoPowerHoldoverDays'])
        self.hasPower = True
        self.closed = False
        self.roomTempTimer = None# warehouse.TimerProcess(self.fridgeType.sim,"%s_RoomTempProc"%self.name,
                                                    #self.noPowerHoldoverDays,self.ifStillNoPowerSetToRoomTemp,None)
        #self.fridgeType.sim.activate(self.roomTempTimer,self.roomTempTimer.run())
        #self.roomTempTimer.cancel
        
    def powerFail(self, duration):
        #print 'powerFail; my storage is %s'%self.getStorageBlocks()
        assert self.place is not None, "powerFail on a homeless fridge"
        #self.hasPower = False
        #self.roomTempTimer = warehouse.TimerProcess(self.fridgeType.sim,"{0}_RoomTempProc_{1}".format(self.name,self.fridgeType.sim.now()),
         #                                                    self.noPowerHoldoverDays,self.ifStillNoPowerSetToRoomTemp,None)
        #self.fridgeType.sim.activate(self.roomTempTimer,self.roomTempTimer.run())
        self.closed = False
        if(duration > self.noPowerHoldoverDays):
            self.hasPower = False
            rtStorage= self.fridgeType.sim.storage.roomtempStorage()
            for sb in self.allStorageBlocks:
                if not hasattr(sb,'_realStorageType'): 
                    sb._realStorageType= sb.storageType
                sb.storageType= rtStorage
                for vg in sb.contents: vg.setStorage(rtStorage, vg.getStorageOtherData())
    
#     def ifStillNoPowerSetToRoomTemp(self,timerProc,otherArg):
#         if self.hasPower == False:
#             print "This Shit worked on {0}".format(self.fridgeType.sim.now())
#         else:
#             print "This Shit doesn't work on {0}".format(self.fridgeType.sim.now())
#         self.roomTempTimer = None

    def powerUnFail(self):
        #print 'powerUnFail; my storage is %s'%self.getStorageBlocks()
        assert self.place is not None, "powerFail on a homeless fridge"
        if self.hasPower == False:
            for sb in self.allStorageBlocks:
                if hasattr(sb,'_realStorageType'):
                    sb.storageType= sb._realStorageType
                    for vg in sb.contents: vg.setStorage(sb.storageType, vg.getStorageOtherData())
                self.hasPower = True
        self.closed = False        
abstractbaseclasses.CanStore.register(ElectricFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.Costable.register(ElectricFridge) # @UndefinedVariable because PyDev can't see abc.register()

class ShippableFridge(Fridge, abstractbaseclasses.Shippable,  abstractbaseclasses.Deliverable):
    classPartner = ShippableFridgeType
    def __init__(self, fridgeType, name=None, currentAge=0.0, tracked=False):
        """
        This constructor is not meant to be called by the user- use ShippableFridgeType.createInstance() instead!
        
        fridgeType is the creating type.
        """
        Fridge.__init__(self, fridgeType, name=name, currentAge=currentAge, tracked=tracked)
        abstractbaseclasses.Shippable.__init__(self)
        abstractbaseclasses.Deliverable.__init__(self)

        self.ageBase= self.fridgeType.sim.now()-currentAge
        self.history= 1
        self.tags= set()
    def setPackageType(self,packageType):
        """
        Sets how this Shippable is packaged.  packageType==None indicates the singleton package.
        This type always travels as singletons, so this method is just a check to make sure no one
        tries to do otherwise.
        """
        assert packageType is None, "Tried to set package type for %s, which always travels as singletons"%self.getType().name
        self.packageType = packageType
    def getStatus(self): 
        d= {}
        for bl in self.getStorageBlocks():
            if bl.storageType not in d: d[bl.storageType]= (0.0,0.0) # vol avail, vol used
            avail,used= d[bl.storageType]
            avail += bl.volAvail
            used += bl.volUsed
            d[bl.storageType]= (avail,used)
        pairs= d.items()
        pairs.sort() # for uniformity
        s= ""
        for k,v in pairs:
            avail,used= v
            s += "%s: %d/%d; "%(k.name,int(round(used)),int(round(avail)))
        if s!="": s= s[:-2] # Get rid of trailing ;
        return s
    def getAge(self): 
        """
        For Fridges, this returns time since last recharge
        """
        return self.fridgeType.sim.now()-self.ageBase
    def setStorage(self,storageType,withDiluent): 
        """
        Sets storageType to the given type.  This is the storageType in which the Fridge is
        stored, not the storageType provided to its contents.
        """
        # withDiluent is ignored, for obvious reasons.
        self.currentExternalStorage = storageType
    def getStorage(self):
        """
        Returns current storageType.  This is the storageType in which the Fridge is stored, not
        the storageType provided to its contents.
        """
        return self.currentExternalStorage
    def getStorageOtherData(self):
        """Returns 'other' storage data, in this case the value of withDiluent"""
        return False
    def getType(self):
        return self.fridgeType
    def getCount(self):
        return 1
    def setTag(self,tag):
        """
        tag can be any hashable- set the tag to 'true'.  Tags which have never been set are false.
        """
        self.tags.add(tag)
        self.maybeTrack('set tag %s'%tag)
    def clearTag(self,tag):
        """
        tag can be any hashable- set the tag to 'false'.  Tags which have never been set are false.
        """
        self.tags.discard(tag)
        self.maybeTrack('clear tag %s'%tag)
    def getTag(self,tag):
        """
        tag can be any hashable- return true if that tag has been set, false if it has been cleared or never was set.
        """
        return tag in self.tags
    def getTagList(self):
        """
        return a list of all true tags.
        """
        return [t for t in self.tags]
    def split(self,nToSplit):
        """
        Some shippables come in groups- VaccineGroups are an example.  This method decreases the current
        Shippable's 'count' by nToSplit and returns a new Shippable of the same type which 'contains' the
        nToSplit items that were split off.  This should never be called if self.getCount() returns 1.
        """
        raise RuntimeError('Tried to split %s - fridges cannot be split'%self.name)
    def prepForDelivery(self, shippableList ):
        raise RuntimeError('Tried to prep the fridge %s for delivery'%self.name)
    def getStorageVolume(self, storageType, withDiluent):
        """
        Output is in CCs.  This is total shelf space to store this Fridge, including 
        packaging- that is, the external volume of the Fridge including the box it comes in.
        
        We'll worry about returning a realistic value when we start tracking room temperature space.
        """
        return self.fridgeType.getSingletonStorageVolume(withDiluent)

abstractbaseclasses.CanStore.register(ShippableFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.Costable.register(ShippableFridge) # @UndefinedVariable because PyDev can't see abc.register()

class IceFridge(ShippableFridge):
    classPartner = ShippableFridgeType
    def __init__(self, fridgeType, name=None, currentAge=0.0, tracked=False):
        ShippableFridge.__init__(self, fridgeType, name=name, currentAge=currentAge, tracked=tracked)
        assert 'ColdLifetime' in fridgeType.recDict, \
            "IceFridge type %s requires a ColdLifetime entry"%fridgeType.name
        self.coldLifetimeDays= float(fridgeType.recDict['ColdLifetime'])
        self.pendingRechargeCostEvents = 0
        if fridgeType.sim.perfect:
            # Disable all special functionality
            self.meltTimer= None
            self.discharge= self.discharge_perfect
            self.recharge= self.recharge_perfect
        else:
            self.meltTimer= warehouse.TimerProcess(fridgeType.sim, "%s_MeltProc"%self.name,
                                                   self.coldLifetimeDays,self.iceFail,None)
            fridgeType.sim.activate(self.meltTimer,self.meltTimer.run())
            self.discharge= self.discharge_std
            self.recharge= self.recharge_std


    def iceFail(self,meltProc,otherArg):
        """
        This method is triggered by the meltTimer process when it runs out.
        """
        #print "*** ice fail occurred at %s ***"%self.place
        self.discharge(meltProc)
        if self.place is None:
            # unconnected; all the contents get warm
            rtStorage= self.fridgeType.sim.storage.roomtempStorage()
            for sb in self.allStorageBlocks:
                for vg in sb.contents: vg.setStorage(rtStorage,  vg.getStorageOtherData())
        else:
            self.place.allocateStorageSpace()
            
    def discharge_std(self, callingProc):
        """
        This corresponds to removing the ice, emptying the gas tank or the equivalent; the
        expectation is that it will leave the Fridge in a 'failed' state.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        """
        Fridge.discharge(self,callingProc)
        if self.fridgeType.sim.now()>0.0:
            # meaning that this is not initialization time
            self.maybeTrack('no ice')
            rtStorage= self.fridgeType.sim.storage.roomtempStorage()
            for sb in self.allStorageBlocks:
                if not hasattr(sb,'_realStorageType'): 
                    sb._realStorageType= sb.storageType
                sb.storageType= rtStorage
            assert callingProc is not None, "unexpected attempt to discharge an IceFridge at initialization time"
            self.meltTimer.cancel()
        else:
            #we're at startup and we want the melt timer canceled if we're starting on a truck
            self.meltTimer.cancel()

    def discharge_perfect(self, callingProc):
        """
        This corresponds to removing the ice, emptying the gas tank or the equivalent; the
        expectation is that it will leave the Fridge in a 'failed' state.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        This version is for when 'perfect' simulation mode is enabled.
        """
        Fridge.discharge(self,callingProc)

    def recharge_std(self, callingProc):
        """
        This corresponds to replacing the ice, refilling the gas tank or the equivalent.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        """
        Fridge.recharge(self,callingProc)
        self.pendingRechargeCostEvents += 1
        self.maybeTrack('fresh ice')
        self.meltTimer.cancel()
        for sb in self.allStorageBlocks:
            if hasattr(sb,'_realStorageType'):
                sb.storageType= sb._realStorageType
                for vg in sb.contents: vg.setStorage(sb.storageType, vg.getStorageOtherData())

        self.meltTimer= warehouse.TimerProcess(self.fridgeType.sim, "%s_MeltProc"%self.name,
                                               self.coldLifetimeDays,self.iceFail,None)
        self.fridgeType.sim.activate(self.meltTimer,self.meltTimer.run())

    def recharge_perfect(self, callingProc):
        """
        This corresponds to replacing the ice, refilling the gas tank or the equivalent.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        This version is for when 'perfect' simulation mode is enabled.
        """
        Fridge.recharge(self,callingProc)
        self.pendingRechargeCostEvents += 1

    def getPendingCostEvents(self):
        if self.pendingRechargeCostEvents>0:
            tpl = (self.getType().name, 'recharge', self.pendingRechargeCostEvents)
            self.pendingRechargeCostEvents = 0
            return [tpl]
        else:
            return []

abstractbaseclasses.Shippable.register(IceFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.CanStore.register(IceFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.Costable.register(IceFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.Deliverable.register(IceFridge) # @UndefinedVariable because PyDev can't see abc.register()

class AlarmedIceFridge(IceFridge):
    classPartner = ShippableFridgeType
    def __init__(self, fridgeType, name=None, currentAge=0.0, tracked=False):
        
        IceFridge.__init__(self, fridgeType, name=name, currentAge=currentAge, tracked=tracked)
        assert 'AlarmDays' in fridgeType.recDict, \
            "AlarmedIceFridge type %s requires an AlarmDays entry"%fridgeType.name
        assert 'SnoozeDays' in fridgeType.recDict, \
            "AlarmedIceFridge type %s requires an SnoozeDays entry"%fridgeType.name            
        self.alarmDays= float(fridgeType.recDict['AlarmDays'])
        self.snoozeDays= float(fridgeType.recDict['SnoozeDays'])

        if fridgeType.sim.perfect:
            # disable all special functionality
            self.alarmTimer= None
            self.discharge= self.discharge_perfect
            self.recharge= self.recharge_perfect
        else:
            self.alarmTimer= warehouse.SnoozeTimerProcess(self.fridgeType.sim,"%s_AlarmProc"%self.name,
                                                          self.alarmDays, self.snoozeDays,
                                                          self._alarm, None)
            self.fridgeType.sim.activate(self.alarmTimer,self.alarmTimer.run())
            self.discharge= self.discharge_std
            self.recharge= self.recharge_std
                
    def _alarm(self,alarmProc,otherArg):
        """
        Returning False is equivalent to hitting snooze; returning true causes the process to exit.
        """
        #print '%s: alarm! at %f; place= %s'%(self.name,self.alarmTimer.sim.now(),self.place)
        thingCount= sum([len(block.contents) for block in self.getStorageBlocks()])
        if thingCount>0:
            return self.place.attemptRestockOfSpecifiedShippable(self.fridgeType)
        else:
            return False # we want to be in snooze mode in case vaccine arrives later
            
    def discharge_std(self, callingProc):
        """
        This corresponds to removing the ice, emptying the gas tank or the equivalent; the
        expectation is that it will leave the Fridge in a 'failed' state.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        """
        IceFridge.discharge_std(self,callingProc)
        if self.fridgeType.sim.now()>0.0:
            # meaning that this is not initialization time
            self.alarmTimer.cancel()

    def discharge_perfect(self, callingProc):
        """
        This corresponds to removing the ice, emptying the gas tank or the equivalent; the
        expectation is that it will leave the Fridge in a 'failed' state.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        This version is for when 'perfect' simulation mode is enabled.
        """
        IceFridge.discharge_perfect(self,callingProc)

    def recharge_std(self, callingProc):
        """
        This corresponds to replacing the ice, refilling the gas tank or the equivalent.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        """
        self.charged = True
        IceFridge.recharge_std(self,callingProc)
        self.alarmTimer.cancel()
        self.alarmTimer= warehouse.SnoozeTimerProcess(self.fridgeType.sim,"%s_AlarmProc"%self.name,
                                                      self.alarmDays, self.snoozeDays,
                                                      self._alarm, None)
        self.fridgeType.sim.activate(self.alarmTimer,self.alarmTimer.run())

    def recharge_perfect(self, callingProc):
        """
        This corresponds to replacing the ice, refilling the gas tank or the equivalent.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        This version is for when 'perfect' simulation mode is enabled.
        """
        IceFridge.recharge_perfect(self,callingProc)

abstractbaseclasses.Shippable.register(AlarmedIceFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.CanStore.register(AlarmedIceFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.Costable.register(AlarmedIceFridge) # @UndefinedVariable because PyDev can't see abc.register()
abstractbaseclasses.Deliverable.register(AlarmedIceFridge) # @UndefinedVariable because PyDev can't see abc.register()


class FridgeTypeManager(trackabletypes.TrackableTypeManager):
    subTypeKey = 'fridges'

    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All FridgeTypes have presumably already been defined within the sim-wide TypeManager- though
        it is still possible to add FridgeTypes if it is done before the list of active FridgeTypes
        is actually used.
        """
        trackabletypes.TrackableTypeManager.__init__(self, typeManager)
        self.typeClass= FridgeType
        self.mergeFridgeYears= self.tm.sim.userInput['mergefridgeyears']
        
    def getTypeByName(self,name,activateFlag=True): 
        if self.mergeFridgeYears and name[:9]!='onthefly_':
            o1= name.rfind('_')
            if o1>5:
                o2= o1-5
                if name[o2]=='_' and name[o2+1:o1].isdigit():
                    mergedName= "%s_U%s"%(name[:o2],name[o1:])
                    proto= self.tm.getTypeByName(name, activateFlag=False)
                    if not self.validTypeName(mergedName):
                        newDict= proto.recDict.copy()
                        newDict['Name']= mergedName
                        self.addType(newDict)
                    uResult= self.tm.getTypeByName(mergedName, activateFlag=activateFlag)
                    if all([uResult.recDict[k]==v for k,v in proto.recDict.items() 
                            if not k in ['Name','Notes','Year']]):
                        #print 'Substituted %s -> %s'%(name,mergedName)
                        result= uResult
                    else:
                        result= self.tm.getTypeByName(name, activateFlag=activateFlag)
                    assert isinstance(result,self.typeClass), "%s is not the name of a FridgeType"%name
                else:
                    result= self.tm.getTypeByName(name, activateFlag=activateFlag)
            else:
                result= self.tm.getTypeByName(name, activateFlag=activateFlag)
        else:
            result= self.tm.getTypeByName(name, activateFlag=activateFlag)
        assert isinstance(result,self.typeClass), "%s is not the name of a FridgeType"%name
        return result

    def addType(self, recDict, verbose=False, debug=False):
        self.tm.addType(recDict, self.typeClass, verbose, debug)
            
    def getOnTheFlyFridgeType(self, storageTypeName, volLiters):
        roundedVolCC= round(1000*volLiters)
        fridgeTypeName= "onthefly_%s_%d"%(storageTypeName,int(roundedVolCC))
        if not self.validTypeName(fridgeTypeName):
            self.addType({'Name':fridgeTypeName, storageTypeName:(0.001*roundedVolCC)})
        return self.getTypeByName(fridgeTypeName)

    def getPartiallyUtilizedFridge(self, fridgeType, useFactor):
        """
        Take an existing fridge type and apply a storage utilization factor to it.

        This takes the original fridge, copies its recDict, applies the factor to
        the storage space, and modifies its name and creates a new fridge type.
        """
        usePercent = int(round(useFactor * 100))
        useFactor = float(usePercent) / 100.0
        if (usePercent == 100):
            return fridgeType
        name = fridgeType.recDict['Name']
        newName = "%s_%02d%%"%(name, usePercent)

        if not self.validTypeName(newName):
            recDict = copy.deepcopy(fridgeType.recDict)
            for stn in storagetypes.storageTypeNames:
                try: recDict[stn] = float(recDict[stn]) * useFactor
                except: pass
            recDict['Name'] = newName
            self.addType(recDict)
        return self.getTypeByName(newName)
    def getPerfectFridge(self, fridgeType):
        name = fridgeType.recDict['Name']
        newName = "%s_perfect"%(name)
        if not self.validTypeName(newName):
            recDict = copy.deepcopy(fridgeType.recDict)
            for stn in storagetypes.storageTypeNames: 
                if recDict[stn] > 0.0: 
                    recDict[stn] = float(C.storageLotsOfSpace)
            recDict['Name'] = newName
            self.addType(recDict)
        newFridge = self.getTypeByName(newName,False)
        newFridge.setRequiredToPrepSC(self.getCollection())
        
        return self.getTypeByName(newName)
            
    def fridgeTypeListFromTableRec(self, rec, storageUtilityFactor=1.0):
        fridgeTypeList= []

        # For the 'traditional' record fields, set things up so that the Warehouse.__init__()
        # method generates an on-the-fly fridge to match
        for str1,str2 in [('CoolVolumeCC','CoolVolumeLiters')]:
            if str1 in rec and str2 in rec:
                raise RuntimeError('Input record contains both %s and %s columns- probably an error'%
                                   (str1,str2))
        for stStr,key in [('freezer','VOL - (lit)'),('cooler','VOL + (lit)'),
                          ('freezer','Walk in -(lit)'),('cooler','Walk in +(lit)'),
                          ('cooler','CoolVolumeLiters')]:
            if key in rec:
                volLiters= storageUtilityFactor*float(rec[key])
                if volLiters>0.0:
                    fridgeTypeList.append(self.getOnTheFlyFridgeType(stStr,volLiters))
        for stStr,key in [('cooler','CoolVolumeCC')]:
            if key in rec and rec[key]!='':
                volCC= storageUtilityFactor*float(rec[key])
                if volCC>0.0:
                    fridgeTypeList.append(self.getOnTheFlyFridgeType(stStr,volCC/C.ccPerLiter))
        if 'Storage' in rec:
            storageString= rec['Storage'].strip()
            #print 'storageString for %s: %s'%(rec['NAME'],storageString)
            if storageString is not None and storageString not in  ['','None']:
                fridgeWords= storageString.split('+')
                for word in fridgeWords:
                    bits= word.split('*')
                    if len(bits)==2:
                        fac= int(bits[0])
                        fridge= self.tm.sim.fridges.getTypeByName(bits[1].strip())
                    elif len(bits)==1:
                        fac= 1
                        fridge= self.tm.sim.fridges.getTypeByName(word.strip())
                    else:
                        raise RuntimeError('Unparsable Storage description "%s"'%storageString)
                    for _ in xrange(fac): fridgeTypeList.append(fridge)
        return fridgeTypeList
    
    def perfectFridgeTypeList(self,orgFridgeTypeList):
        storageSC = self.getTotalVolumeSCFromFridgeTypeList(orgFridgeTypeList)
        perfFridgeTypeList = []
        ## Must pull out the shippables
        shippablesList = [g for g in orgFridgeTypeList \
                          if isinstance(g,abstractbaseclasses.CanStoreType) \
                          and isinstance(g,abstractbaseclasses.ShippableType)]
        perfFridgeTypeList = [self.getPerfectFridge(g) for g in shippablesList]
        if self.tm.sim.storage.getTotalCoolVol(storageSC) > 0.0:
            perfFridgeTypeList.append(self.getOnTheFlyFridgeType('cooler', C.storageLotsOfSpace))
        if self.tm.sim.storage.getTotalRefrigeratedVol(storageSC) != self.tm.sim.storage.getTotalCoolVol(storageSC):
            perfFridgeTypeList.append(self.getOnTheFlyFridgeType('freezer', C.storageLotsOfSpace))
        perfFridgeTypeList.append(self.getOnTheFlyFridgeType('roomtemperature',C.storageLotsOfSpace))
        return perfFridgeTypeList
    
    def getTotalVolumeSCFromFridgeTypeList(self,fridgeTypeList,ignoreOutdoors=False):
        """
        Returns a StorageCollection containing the total volume described in fridgeTypeList.
        """
        sDict= {}
        for entry in fridgeTypeList:
            assert(isinstance(entry,FridgeType))
            for st,vol in entry.storageCapacityInfo:
                if ignoreOutdoors:
                    if vol == 1000000000000:
                        continue
                if st in sDict:
                    sDict[st] += vol
                else:
                    sDict[st]= vol
        result= self.tm.sim.storage.getCollection(sDict.items())
        return result

    def getTotalVolumeSCFromFridgeSC(self,fridgeSC):
        """
        Returns a StorageCollection containing the total volume described in fridgeTypeList.
        """
        sDict= {}
        for f,n in fridgeSC.items():
            assert(isinstance(f,FridgeType))
            for st,vol in f.storageCapacityInfo:
                if st in sDict:
                    sDict[st] += n*vol
                else:
                    sDict[st]= n*vol
        result= self.tm.sim.storage.getCollection(sDict.items())
        return result

    
