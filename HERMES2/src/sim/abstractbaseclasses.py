#!/usr/bin/env python

########################################################################
# Copyright C 2011, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" abstractbaseclasses.py
This module provides abstract base classes for the type system
"""

_hermes_svn_id_="$Id$"

import abc, math, types, sys
import chardet

class UnicodeSupportMetaClass(abc.ABCMeta):
    defaultEncoding = 'utf-8'
    @staticmethod
    def fake_name():
        """Return a wrapped property to always return .name as unicode"""
        def u_getName(self):
            return self._u_name
        def u_setName(self,value):
            if isinstance(value,types.UnicodeType):
                self._u_name = value
            else:
                self._u_name = value.decode(chardet.detect(value)['encoding'])
        def u_delName(self):
            del self._u_name
        return property(u_getName, u_setName, u_delName, 'name provided by UnicodeSupportMetaClass')
    @staticmethod
    def fake_bname():
        """Return a wrapped property to always return .bName as a byte string"""
        def u_getBName(self):
            if hasattr(self,'_u_name'):
                return self._u_name.encode(UnicodeSupportMetaClass.defaultEncoding)
            else:
                raise RuntimeError("Class instance has no .name and hence no .bName")
        return property(u_getBName, None, None, 'name provided by UnicodeSupportMetaClass')
    @staticmethod
    def wrap_str(innerStr):
        def outerStr(self):
            v = innerStr(self)
            if isinstance(v, types.UnicodeType):
                return v.encode(UnicodeSupportMetaClass.defaultEncoding)
            else:
                return v
        return outerStr
    def __new__(cls, name, bases, attrs):
        attrs['name'] = cls.fake_name()
        attrs['bName'] = cls.fake_bname()
        if '__str__' in attrs:
            #print 'patching str for %s'%name
            attrs['__str__'] = cls.wrap_str(attrs['__str__'])
        if '__repr__' in attrs:
            #print 'patching repr for %s'%name
            attrs['__repr__'] = cls.wrap_str(attrs['__repr__'])
        return super(UnicodeSupportMetaClass, cls).__new__(cls, name, bases, attrs)

class UnicodeSupport(object):
    __metaclass__ = UnicodeSupportMetaClass


class CanOwn(UnicodeSupport):
    """
    Classes derived from this abstract base class are instances of places where
    Shippable things can be, for example a specific warehouse or a specific truck.
    """
    
    @abc.abstractmethod
    def getSupplySummary(self):
        return None
    @abc.abstractmethod
    def getStorageVolumeWOPackagingOrDiluent(self, v, nVials):
        """
        Returns the storage volume of nCount instances of this ShippableType with no packaging.  Thus for 
        vaccine vials it is the packed storage volume of nCount of the bare vials themselves.  This method
        is used to track total delivered volume of goods, which by convention is the unpackaged volume of
        the goods.
        """
        return 0.0
    @abc.abstractmethod
    def getNVialsThatFit(self, v, volCC):
        """
        This is basically the inverse of self.getStorageVolume.  The results presumably depend on the packaging
        policy of the CanOwn instance, and perhaps other factors.
        """
        return 0
    @abc.abstractmethod
    def getStorageBlocks(self):
        return []
    @abc.abstractmethod
    def filterStorageBlocks(self, storageBlocks):
        return []
    @abc.abstractmethod
    def calculateStorageFillRatios(self, thisVC, assumeEmpty=False):
        """
        This attempts to allocate space fairly between vaccines.  It's
        very similar to the ARENA 'fair share' storage calculation.
        The return value is a triple of VaccineCollections

           freezeVC, coolVC, warmVC

        where each vaccine's entry represents the fraction of the available
        vials in the input VC to be stored in each medium.  These fractions
        are truncated at 1.0.   If assumeEmpty is true, all the canOwn's resources 
        are presumed to be included in thisVC; this includes both attached fridges
        and all vaccine supplies.  If false, thisVC is assumed to be 'in addition to'
        any existing fridges and supplies.
        """
        return None
    @abc.abstractmethod
    def allocateStorageSpace(self):
        """
        This method shifts the CanOwn instance's Shippables into optimal storage.  This may result in
        splitting of some (grouped) Shippables.  The method returns a list of any new Shippables
        created in this way, but note that those Shippables have already been added to the CanOwn's 
        internal lists.
        """
        return []
    @abc.abstractmethod    
    def attachStorage(self, thisFridge, callingProc):
        """
        thisFridge must satisfy isinstance(thisFridge,abstractbaseclasses.CanStore)
        callingProc is the SimPy Process instance which is currently active- its
        presence here is an unfortunate artifact of the SimPy API.
        """
        pass
    @abc.abstractmethod
    def detachStorage(self, thisFridge, callingProc):
        """
        thisFridge must satisfy isinstance(thisFridge,abstractbaseclasses.CanStore)
        callingProc is the SimPy Process instance which is currently active- its
        presence here is an unfortunate artifact of the SimPy API.
        """
        pass
    @abc.abstractmethod
    def attachStock(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        pass
    @abc.abstractmethod
    def detachStock(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        pass
    @abc.abstractmethod
    def attachIce(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        pass
    @abc.abstractmethod
    def detachIce(self,shippable):
        """
        shippable must not satisfy isinstance(shippable,abstractbaseclasses.CanStore)
        """
        pass
    @abc.abstractmethod
    def printInventory(self):
        """
        When this method is called the CanOwn instance will print (to sys.stdout) an inventory
        of all its currently attached Shippables.  This is intended as a debugging tool.
        """
        pass
    @abc.abstractmethod
    def getSim(self):
        """
        Returns the current simulation
        """
        return None
    @abc.abstractmethod
    def attemptRestockOfSpecifiedShippable(self,shippableType):
        """
        This method is provided so that outside classes can request a restock if a particular
        ShippableType is available.  It returns True if a restock has been signaled (because
        the ShippableType is available), False otherwise.
        """
        return False
    @abc.abstractmethod
    def setPackagingModel(self,packagingModel):
        """
        Set the PackagingModel associated with this CanOwn
        """
        pass
    @abc.abstractmethod
    def getPackagingModel(self):
        """
        Returns the PackagingModel for this CanOwn
        """
        return None
    @abc.abstractmethod
    def setStorageModel(self,storageModel):
        """
        Set the StorageModel associated with this CanOwn
        """
        pass
    @abc.abstractmethod
    def getStorageModel(self):
        """
        Returns the StorageModel for this CanOwn
        """
        return None
    
    @abc.abstractmethod
    def applyToAll(self, filterClass, func, negFilterClass=None, argList = []):
        """
        Causes the CanOwn to apply all those owned instances for which isinstance(thisInstance,filterClass) is true
        to execute func(thisInstance,*argList) and return a list containing the return values of all those
        function invocations.
        """
        return []
        
class Place(CanOwn):
    """
    Classes derived from this abstract base class represent fixed locations, for example
    warehouses and clinics.
    """
    
    @abc.abstractmethod
    def getPopServedPC(self):
        pass
    @abc.abstractmethod
    def setPopServedPC(self,popPC):
        pass
    @abc.abstractmethod
    def registerInstantaneousDemandVC(self, instantaneousDemandVC, interval):
        pass
    @abc.abstractmethod
    def getInstantaneousDemandVC(self, interval):
        pass
    @abc.abstractmethod
    def getTotalDownstreamPopServedPC(self):
        pass
    @abc.abstractmethod
    def getTotalDownstreamClientsByTier(self):
        pass
    @abc.abstractmethod
    def getStore(self):
        pass
    @abc.abstractmethod
    def getLonLat(self):
        """
        Returns a tuple (longitude, latitude) with values in decimal degrees.
        """
        pass
    @abc.abstractmethod
    def getKmTo(self,otherPlace,level,conditions):
        """
        level is typically a string like 'central'.  conditions might be None, or
        a string like 'muddy'.
        """
        pass
    @abc.abstractmethod
    def cutGridPower(self):
        pass
    @abc.abstractmethod
    def restoreGridPower(self):
        pass

class ManagedType(UnicodeSupport):
    """
    Classes derived from this abstract base class are types managed by the typeManager.
    Examples: FridgeType, VaccineType, PeopleType, TruckType, StorageType
    """
    
    # I really wish this was a 'classproperty' or 'abc.abstractclassproperty', but those are not
    # yet cleanly implemented.
    typeName= "managed"
    
    # If this were Python3 we'd use @abstractclassmethod ...
    @classmethod
    def fromRec(cls,recDict,sim=None):
        raise RuntimeError("%s.fromRec() called; derived class should have overridden this"%\
                           ManagedType.typeName)
    
    @abc.abstractmethod
    def resetCounters(self): 
        """
        The ManagedType should reset its internal statistics in response to this call, so that future
        getSummaryDict() or statisticsstring() calls ignore any events occurring before this call.
        """
        pass

    @abc.abstractmethod
    def getSummaryDict(self):
        """
        Returns a dictionary of information summarizing the statistics for this ManagedType.  This information
        will end up in the summary output spreadsheet, or be used to generate a statistics string in the
        summary output text.
        """
        return {}
    @abc.abstractmethod
    def summarystring(self):
        """
        Returns a summary string describing this ManagedType.  This string will end up in the 
        log file.
        """
        return ""
    @abc.abstractmethod
    def statisticsstring(self):
        """
        Returns a string summarizing the statistics for this ManagedType.  This string will end up in
        summary output text.
        """
        return ""

    
    def activate(self, **keywords): 
        """
        This method must return the activated object, to allow the associated TypeManager to
        substitute a replacement type if necessary.
        """
        return self
    
    def checkCompatibleDefinition(self, **keywords):
        """
        This method provides an opportunity for the ManagedType to raise an error if 
        the TypeManager fields a request which implies a different set of construction parameters.
        """
        return True
    
    @classmethod
    def getColumnTypeDict(cls):
        """
        This method returns a dict of the form {columnKey:[datatypes.DataType]}, with the expectation
        that csv_tools.castColumn will be used with the given type to convert incoming record fields.
        """
        return {}

class TangibleType(ManagedType):
    """
    Classes derived from this abstract base class represent types for which it makes sense to create an
    instance- for example, vaccines and trucks but not StorageTypes (which are just temperature labels).
    """
    
    # I really wish this was a 'classproperty' or 'abc.abstractclassproperty', but those are not
    # yet cleanly implemented.
    typeName= "tangible"

    @abc.abstractmethod
    def createInstance(self,count=1,name=None,currentAge=0.0,tracked=False):
        """Returns an instance of the type, for example a VaccineGroup or a Fridge"""
        return None

class HasOVW(TangibleType):
    """
    This class is used as a tag to exempt things which don't come in vials (like cold boxes) from
    open vial waste calculations.
    """
    
    def __init__(self):
        # This is to satisfy Eclipse syntax checking
        pass
    
class Trackable(UnicodeSupport):
    """
    Classes which can be owned by a CanOwn instance should be derived from Trackable- for example 
    vaccines, fridges and trucks.  Each of these items has an associated Type class- Fridge has 
    FridgeType, for example.  Those type classes should be derived from TrackableType.
    
    Instances which are Trackable but not Shippable do not occupy space in CanStore instances, and
    are not stored at a particular temperature.  They are not subject to packaging or storage
    restrictions.  They have no Age and no tags.  To produce something which can actually travel
    through the shipping network, Trackable must be combined with Shippable.  Trackable instances
    coexist with Shippable+Trackable instances in the inventory lists of CanOwn objects, but are
    ignored by the mechanisms which transport and store Shippable instances.
    """
    
    def __init__(self):
        # This is to satisfy Eclipse syntax checking
        pass

    @abc.abstractmethod
    def attach(self, place, callingProc):
        """
        Establish the association between a shippable and its location.  This DOES NOT include
        insertion of the shippable into Store.theBuffer; that operation is handled by SimPy in
        response to an appropriate 'yield'.  Note that after this method is called and before
        the 'place' reallocates storage space, items stored in this shippable may violate the
        storage rules for the new 'place'.  callingProc is the current SimPy Process instance; 
        its presence here is an unfortunate consequence of the SimPy API.
        """
        pass
    @abc.abstractmethod
    def detach(self, callingProc):
        """
        Break the association between a shippable and its current location.  This DOES NOT include
        removal of the shippable from Store.theBuffer; that operation is handled by SimPy in
        response to an appropriate 'yield'.  callingProc is the current SimPy Process instance; its
        presence here is an unfortunate consequence of the SimPy API.
        """
        pass
    @abc.abstractmethod
    def maybeTrack(self,info):
        pass
    @abc.abstractmethod
    def getType(self):
        """
        Return the base type, e.g. VaccineType for a VaccineGroup instance.
        """
        return None
    @abc.abstractmethod
    def getCount(self):
        """
        Return the instance count, e.g. nVials for a VaccineGroup instance.
        """
        return 1
    @abc.abstractmethod
    def getUniqueName(self):    
        """
        Provides an opportunity for the class to give a more unique response when the '.name' attribute is
        not unique.
        """ 
        return ""

class TrackableType(TangibleType):
    """
    Classes derived from this abstract base class produce instances which include the Trackable ABC
    """

class CanStore(Trackable):
    """
    Classes derived from this abstract base class provide space in which Shippable objects can be stored.
    Examples: specific refrigerator instances
    """
    
    def __init__(self):
        # This is to satisfy Eclipse syntax checking
        super(Trackable,self).__init__()
    
    @abc.abstractmethod
    def getStorageBlocks(self): return None
    
    def discharge(self, callingProc):
        """
        This corresponds to removing the ice, emptying the gas tank or the equivalent; the
        expectation is that it will leave the Fridge in a 'failed' state.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        """
        pass
    
    def recharge(self, callingProc):
        """
        This corresponds to replacing the ice, refilling the gas tank or the equivalent.
        callingProc is the process making the call; it is required so that timer processes
        can be canceled. 
        """
        pass

class CanStoreType(TrackableType):
    """
    Classes derived from this abstract base class produce instances which include the CanStore ABC.
    Examples: specific fridgeTypes
    """
    
    @abc.abstractmethod
    def getStorageCapacityInfo(self): return None



class StatProvider(UnicodeSupport):
    """
    This is a sample interface providing a method to request a value by name.  It is intended
    as a generic way to return summary statistics for aggregation.
    """
    @abc.abstractmethod
    def getStat(self, statNameString):
        """
        In response to a name, getStat should return an appropriate object giving that value.  It might
        be a simple scalar, a string, or something more complex like an AccumVal.  The caller will
        presumably use the __add__ or __iadd__ operations to merge values.  If no value is available by
        that name, getStat should return None.
        """
        return None
    @abc.abstractmethod
    def getAvailableStatNameList(self):
        """
        Return a list of all valid stat names.
        """
        return []

class CostableType(UnicodeSupport):
    """
    Types which contribute to capital or ongoing costs.  Currently all the functionality is implemented 
    in CostManager, so there are no methods here.
    """

    def __init__(self):
        """
        This is to satisfy Eclipse syntax checking
        """
        pass

class Costable(UnicodeSupport):
    """
    Classes which contribute to capital or ongoing costs.  Currently all the functionality is implemented 
    in CostManager, so there are no methods here.
    """
    
    def __init__(self):
        """
        This is to satisfy Eclipse syntax checking
        """
        pass
    
    @abc.abstractmethod
    def getPendingCostEvents(self):
        """
        This method returns a list of tuples of the form (typeName, eventName, count, ...) representing
        cost events which have happened since the last call to the method.
        """
    pass

class Shippable(UnicodeSupport):
    """
    Classes derived from this abstract base class can be transported through the shipping network.
    Examples: refrigerators, vaccines
    """
    
    RECYCLE_TAG= "recycle"
    DO_NOT_USE_TAG= "donotuse"
    IN_USE_TAG= "inuse"
    EXCLUDE_FROM_STATS_TAG= "exclude_from_stats"

    def __init__(self):
        super(Shippable,self).__init__()
        self.packageType = None
        self.arrivalTime = None
        
    def setArrivalTime(self, time):
        """
        get- and setArrivalTime are used to calculate statistics for duration of storage of shippables
        in particular CanStore instances. The normal mode of operation is to set the arrival time when 
        the shippable is attached to the CanStore.
        """
        self.arrivalTime = time
        
    def getArrivalTime(self):
        """
        get- and setArrivalTime are used to calculate statistics for duration of storage of shippables
        in particular CanStore instances. The normal mode of operation is to set the arrival time when 
        the shippable is attached to the CanStore.
        """
        return self.arrivalTime
        
    def setPackageType(self,packageType):
        """
        Sets how this Shippable is packaged.  packageType==None indicates the singleton package.
        """
        self.packageType = packageType
    
    def getPackageType(self):
        """
        What is the largest package in which this Shippable may be packaged?  Note that smaller types may also
        be present- a number of Shippable instances might have a package type indicating a carton, but leftovers
        might be packed in boxes, and leftovers from the boxes might be packed as singletons.
        Return value is a PackageType, or None.  None indicates the singleton package.
        """
        return self.packageType

    @abc.abstractmethod        
    def getStorageVolume(self,storageType,withDiluent):
        """
        Output is in CCs; this is total shelf space to store all 'things' represented by
        this Shippable, including packaging.  Thus, for a VaccineGroup stored in a partially 
        filled box, this would be the outside volume of the box.
        """
        return 0.0
    
    @abc.abstractmethod
    def getStatus(self): 
        pass
    @abc.abstractmethod
    def getAge(self): 
        pass
    @abc.abstractmethod
    def setStorage(self,storageType,withDiluent): 
        """Sets storageType to the given type"""
        pass
    @abc.abstractmethod
    def getStorage(self):
        """Returns current storageType"""
        return None
    @abc.abstractmethod
    def getStorageOtherData(self):
        """Returns 'other' storage data, in this case the value of withDiluent"""
        return False
    @abc.abstractmethod
    def setTag(self,tag):
        """
        tag can be any hashable- set the tag to 'true'.  Tags which have never been set are false.
        """
        pass
    @abc.abstractmethod
    def clearTag(self,tag):
        """
        tag can be any hashable- set the tag to 'false'.  Tags which have never been set are false.
        """
        pass
    @abc.abstractmethod
    def getTag(self,tag):
        """
        tag can be any hashable- return true if that tag has been set, false if it has been cleared or never was set.
        """
        return False
    @abc.abstractmethod
    def getTagList(self):
        """
        return a list of all true tags.
        """
        return []
    @abc.abstractmethod
    def split(self,nToSplit):
        """
        Some shippables come in groups- VaccineGroups are an example.  This method decreases the current
        Shippable's 'count' by nToSplit and returns a new Shippable of the same type which 'contains' the
        nToSplit items that were split off.  This should never be called if self.getType() returns 1.
        """
        return None

class Deliverable(UnicodeSupport):
    """
    Classes derived from this abstract base class are actually provided to the consumer.  Vaccines are
    deliverables; diluent is shippable but is only used to prepare the vaccine for delivery to the consumer.
    """

    def __init__(self):
        # This is to satisfy Eclipse syntax checking
        pass
        
    class PrepFailure(Exception):
        """
        This exception is returned when a prepForDelivery operation fails, presumably because some required
        shippable was not supplied, e.g. insufficient diluent was provided to reconstitute a vaccine vial.
        """
        pass
    
    @abc.abstractmethod
    def prepForDelivery(self, shippableList ):
        """
        Using material from shippableList, prepare this Deliverable for delivery.  The method returns a
        tuple of lists, (listOfUnusedShippables, listOfConsumedShippables).  The former list contains
        input shippables from shippableList which were not needed to prep this Deliverable; the latter
        contains shippables which were used up in the process.
        """
        return [],[]
    
class GroupedShippable(Shippable):
    """
    Classes derived from this abstract base class are Shippable instances that come in 
    groups, such that item.getCount() may return values greater than 1.
    """
        
class ShippableType(TrackableType):
    """
    These are the types of which Shippable things are the instances.
    """
    
    # I really wish this was a 'classproperty' or 'abc.abstractclassproperty', but those are not
    # yet cleanly implemented.
    typeName= "shippable"

    def __init__(self):
        self.requiredByList = []      
    
    @abc.abstractmethod
    def getNDosesPerVial(self): 
        """Returns doses per vial- since everything shippable is sometimes treated like a vaccine"""
        pass
    @abc.abstractmethod
    def canLeaveOut(self):
        """Returns true if this type can be stored at room temperature"""
        return True
    @abc.abstractmethod
    def canFreeze(self):
        """Returns true if this type can be stored at freezing temperatures"""
        return True
    @abc.abstractmethod
    def canKeepOpenVials(self,howLongOpen):
        """
        If the first dose from a vial has been used, can the rest still be used after 'howLongOpen' days?  
        Obviously this is nonsense for Shippable things that don't actually hold multipe doses.
        """
        return False
    @abc.abstractmethod
    def recordBreakage(self,nVials):
        """
        If the BreakageModel calculates that nVials of these are broken in storage or transport, this
        method is used to inform the ShippableType of that destruction.  Note that nVials is the number
        of instances broken, so if the ShippableType actually represents cold boxes, that's the number
        of boxes broken; it does not indicate that any vials stored in those boxes are broken.
        """
        pass
    @abc.abstractmethod
    def recordTreatment(self,nTreated,nApplied,nVialsUsedForTreatment):
        """
        Records the number of instances of this ShippableType consumed in a treatment event, the number
        of patients who applied for that treatment, and the number of patients for which treatment was
        actually provided.
        """
        pass
    @abc.abstractmethod
    def recordTransport(self, nInstances, fromWH, toWH, transitTimeDays, level, conditions):
        """
        Records a transport step for this shippableType.  nInstances were transported from fromWH to toWH
        with transitTimeDays spent in transit.  level is the level or category at this level of the
        shipping hierarchy, e.g. 'central'.  conditions is travel conditions, e.g. 'muddy' or None.
        """
        pass
    @abc.abstractmethod
    def getStoragePriorityList(self):
        """
        Returns an ordered list of StorageType instances indicating the desirability of storing this
        ShippableType in each StorageType, most desirable first.
        """
        return []
    @abc.abstractmethod
    def addPackageType(self, packageType):
        """
        Assert that this ShippableType may come in the given packageType.  Neither the
        ShippableType nor packageType is made active as a result of this call.
        """
        pass
    @abc.abstractmethod
    def getLargestPackageType(self):
        """
        returns the packagetypes.PackageType value corresponding to the largest valid package for this
        ShippableType, or 'None' if no PackageTypes are defined.  The 'None' value thus corresponds to
        the implied singleton package.
        """
        return None
    @abc.abstractmethod
    def getPackageTypeList(self):
        """
        Returns (a shallow copy of) the list of all valid package types for this Shippable, in order.
        """
        return None

    def getRequiredByList(self):
        """
        If this ShippableType is required to prep any DeliverableType(s), return a list of those 
        DeliverableTypes.
        """
        return self.requiredByList

    @abc.abstractmethod
    def getSingletonStorageVolume(self, withDiluentFlagOrStorageModel):
        """
        Returns the storage volume of one instance of this ShippableType with no packaging.  Thus for 
        vaccine vials it is the packed storage volume of nCount of the bare vials themselves.  This method
        is used to track total delivered volume of goods, which by convention is the unpackaged volume of
        the goods.
        """
        return 0.0
        
class DeliverableType(UnicodeSupport):
    """
    These are the types of which Deliverable things are the instances.
    """

    def __init__(self):
        self.requiredToPrepSC = None        

    def getRequiredToPrepSC(self, nInstances):
        """
        Returns a ShippableCollection containing types and counts necessary to prepare nInstances delivarables
        of this type for delivery.  For example, calling this on a VaccineType with nInstances==3 would
        return a ShippableCollection listing 3 instances of the vaccine's diluent.
        """
        assert self.requiredToPrepSC is not None, "Prep requirements for %s were not initialized"%self.name
        #print '%s: requiredToPrep is %s'%(self.name,self.requiredToPrepSC)
        result = self.requiredToPrepSC*nInstances
        return result
    
    def setRequiredToPrepSC(self, sc):
        """
        Assert that this deliverable type requires the contents of the ShippableCollection sc to prep, per
        instance of the deliverable.  No value is returned.
        """
        self.requiredToPrepSC = sc.copy() # for safety
        
    def countPrep(self, sList):
        """
        What is the maximum number of instances of this type that can be prepped for delivery with the
        given list of shippable instances?  This method returns the largest integer count for which 
        deliverableType.createInstance(count).prepForDelivery(sList) will not thrown Deliverable.PrepFailure.
        The special value None is returned if an infinite number could be prepared, as occurs when the
        type requires nothing to prep.
        """
        neededSC = self.getRequiredToPrepSC(1)
        #print "countPrep: needed: %s sList: %s"%([(v.name,n) for v,n in neededSC.items()],[(s.getType().name,s.getCount()) for s in sList])
        if neededSC.totalCount()==0:
            return None
        else:
            lim = None
            # This could be implemented via ShippableCollection.__div__(), but not as efficiently.
            for v,n in neededSC.items():
                avail = sum([s.getCount() for s in sList
                             if s.getType()==v and s.getAge() is not None and not s.getTag(Shippable.RECYCLE_TAG)])
                i = int(math.floor(avail/n))
                if lim is None:
                    lim = i
                else:
                    if i<lim: lim= i
            #print 'countPrep: got %d'%lim
            return lim
                    
class GroupedShippableType(ShippableType):
    """
    Classes derived from this abstract base class have GroupedShippable things as their instances.
    """

class NonScalingType(UnicodeSupport):
    """
    Classes the shipment size of which does not change with the shipping interval.  For example, if a shipment 
    is to deliver PVSDs or ice charges for cold boxes, presumably those things should be delivered on every
    shipment.  If the interval between shipments is 1.3 times or 0.7 times normal, the number of PVSDs and ice
    charges delivered with the shipment does not change.  If a calendar schedule is used to prevent vaccination
    on some days of a shipping interval, the application of that calendar does not change the number of PVSDs or
    ice charges shipped.
    """
    
    def __init__(self):
        # This is to satisfy Eclipse syntax checking
        pass

class ConsumesSupplies(UnicodeSupport):
    """
    Classes derived from this abstract base class consume things like vaccines or ice.
    Examples: some refrigerators; people.
    """
    
class Shopper(UnicodeSupport):
    """
    Classes derived from this abstract base class contain methods to select ordered subsets of Shippable things.
    Examples: warehouse.getVaccineCollectionAndTweakBuffer
    """
    
    @abc.abstractmethod
    def selectItems(self, someCollection, someCanSend): pass
    """
    Returns a list of Shippable instances, updating someCanSend.theBuffer as appropriate.  This method
    provides the selection function for a 'yield get'.
    """

class CanProvide(Place):
    """
    Classes derived from this abstract base class can serve as the upstream end of a shipping link.
    Examples: Warehouse
    """

    @abc.abstractmethod
    def gotAnyOfThese(self, listOfShippableTypes): pass
    """
    Returns True if somethingThatCanStore has any available instances of the listed ShippableTypes,
    or False otherwise
    """
    
    @abc.abstractmethod
    def fillThisOrderFilter(self, someShopper, someCollection): pass
    """
    This method is used to actually remove Shippable items from the CanStore's theBuffer.
    """

class CanReceive(CanStore):
    """
    Classes derived from this abstract base class can serve as the downstream end of a shipping link.
    Examples: Warehouse, Clinic
    """

    @abc.abstractmethod
    def wantAnyOfThese(self, listOfShippableTypes): pass
    """
    Returns True if somethingThatCanStore has any available instances of the listed ShippableTypes,
    or False otherwise
    """


        
