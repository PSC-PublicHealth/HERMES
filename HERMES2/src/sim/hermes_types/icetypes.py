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

__doc__=""" icetypes.py
This module implements ice, which is a Shippable that has the property of being
able to recharge certain types of Fridge.
"""

_hermes_svn_id_="$Id$"

import math,types,random
from SimPy.Simulation  import *
#from SimPy.SimulationGUIDebug import *
import abstractbaseclasses
import warehouse
import storagetypes
import trackabletypes
import constants as C

class Ice(abstractbaseclasses.Shippable, abstractbaseclasses.Deliverable, abstractbaseclasses.Trackable):
    """
    Represents one or more packets of ice (or other cold source, like blue ice) with
    identical history.
    """
    def __init__(self, iceType, storage, name=None, tracked=False, ageBase=None):
        """This constructor is not meant to be called by the user- use IceType.createInstance() instead!"""
        if name is None:
            name= iceType.sim.getUniqueString("ice")

        abstractbaseclasses.Shippable.__init__(self)
        abstractbaseclasses.Deliverable.__init__(self)
        abstractbaseclasses.Trackable.__init__(self)
        self.name= name
        self.iceType= iceType
        self.tracked= tracked
        self.place= None # not currently owned by anything
        self.tags= set()
        self.storage= storage
        self.history= 1
        self.tracked= False
        self.debug= False
        if ageBase is None:
            self.ageBase= self.iceType.sim.now()
        else:
            self.ageBase= ageBase
        self.maybeTrack("creation")
    def maybeTrack(self,info):
        if self.tracked:
            print '\n%g, "%s", "%s"\n'%(self.iceType.sim.now(),str(self),info)
    def __repr__(self):
        return "<Ice(%s,%s,%s,%s)>"%(repr(self.iceType),
                                     repr(self.storage.name),
                                     self.name,
                                     self.tracked)
    def __str__(self):
        return self.getUniqueName()
    def getStatus(self):
        return "%d instances, storage %s"%(1,self.storage.name)
    def getAge(self):
        "This is the time since we left frozen storage"
        if self.storage==self.iceType.sim.storage.frozenStorage():
                return 0.0
        else:
            return self.iceType.sim.now() - self.ageBase
    def split(self,count):
        raise RuntimeError('Tried to split %s - ice instances cannot be split'%self.name)
    def setStorage(self,storage,withDiluent):
        """withDiluent is ignored, for obvious reasons"""
        if self.storage != storage:
            self.storage= storage
            if self.storage==self.iceType.sim.storage.frozenStorage():
                self.clearTag(abstractbaseclasses.Shippable.DO_NOT_USE_TAG)
                self.clearTag(abstractbaseclasses.Shippable.RECYCLE_TAG)
            else:
                self.setTag(abstractbaseclasses.Shippable.DO_NOT_USE_TAG)
            self.maybeTrack("stored %s"%storage.name)
    def getStorage(self):
        """Returns current storageType"""
        return self.storage
    def getStorageOtherData(self):
        """Returns 'other' storage data, in this case the value of withDiluent"""
        return False
    def getStorageVolume(self, storageType, withDiluent):
        """
        This is the total volume needed to store this Deliverable, including packages.
        Output is in CCs.
        """
        return self.iceType.getSingletonStorageVolume(withDiluent)
    def setPackageType(self,packageType):
        """
        Sets how this Shippable is packaged.  packageType==None indicates the singleton package.
        This type always travels as singletons, so this method is just a check to make sure no one
        tries to do otherwise.
        """
        assert packageType is None, "Tried to set package type for %s, which always travels as singletons"%self.getType().name
        self.packageType = packageType
    def attach(self, place, callingProc):
        assert self.place is None, "%s is already attached"%self.name
        self.place= place
        place.attachIce(self)
        self.maybeTrack("attach to %s"%self.place.name)
    def detach(self, callingProc):
        assert self.place is not None, "%s is not attached"%self.name
        self.place.detachIce(self)
        self.maybeTrack("detach from %s"%self.place.name)
        self.place= None
    def getType(self):
        return self.iceType
    def getCount(self):
        return 1
    def getUniqueName(self):    
        """
        Provides an opportunity for the class to give a more unique response when the '.name' attribute is
        not unique.
        """ 
        return "%s"%self.name
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
    def prepForDelivery(self, shippableList ):
        raise RuntimeError('Tried to prep the fridge %s for delivery'%self.name)
    
class IceType(abstractbaseclasses.ShippableType, abstractbaseclasses.NonScalingType,
              abstractbaseclasses.DeliverableType):
    typeName= 'ice'
    def __init__(self, recDict, instanceClassName):
        """
        volCC is the volume in CC of one instance of Ice of this IceType.
        rand_key is an integer or None.  If None, the value will
           be generated from the hash of the vaccine name.  This value
           gives the 'seed offset' of the random number generator for
           this vaccine from the base RNG, so one might want to set 
           different versions of the same vaccine (e.g. Measles and 
           Measles-unidose) to have to same offset.  If this is done AND
           the seed value for the run is kept constant, the same patient
           population will be generated for the two variants of the
           vaccine.
        """
        super(IceType,self).__init__()
        self.name= recDict['Name']
        self.volCC= recDict['VolCC']
        self.instanceClassName= instanceClassName
        self.recDict= recDict # Never know when you might need it...
        self.rndm= random.Random()
        if recDict.has_key('RandomKey') and recDict['RandomKey']!='': 
            rand_key= int(recDict['RandomKey'])
        else: rand_key= None
        if rand_key is None: self.rndm_jumpahead= hash(self.name)
        else: self.rndm_jumpahead= rand_key
        self.storagePriorityList= None
        self.totalTrips= 0
        self.totalKm= 0.0
        self.totalTravelDays= 0.0
        self.instanceCount= 0
        self.nBroken= 0
        self.nCreated= 0
        self.absoluteNBroken= 0
        # absoluteNCreated is just instanceCount!

    @classmethod
    def fromRec(cls,recDict, typeManager):
        assert 'Name' in recDict, 'record has no "Name" field'
        assert 'VolCC' in recDict, 'record has no "VolCC" field'
        if 'ClassName' in recDict and recDict['ClassName'] is not None \
                and recDict['ClassName']!='':
            className= recDict['ClassName']
        else:
            className= 'Ice'
        return IceType(recDict, className)
                    
    def createInstance(self,count=1,name=None,tracked=False):
        """
        Create and return an Ice of this IceType.
        """
        if count!=1:
            raise RuntimeError("Internal error: Ice creation with non-unit count")
        self.instanceCount += 1
        self.nCreated += 1
        if name is None:
            name= "%s#%d"%(self.name,self.instanceCount)
        return globals()[self.instanceClassName](self, storage=self.sim.storage.frozenStorage(),
                                                 name=name, tracked=tracked )

    def __repr__(self):
        return "<IceType(%s, %f)>"%(self.name,self.volCC)
    def __str__(self):
        return self.name
    
    def summarystring(self):
        str= "Ice type %s\n\n"%self.name
        return str
    def statisticsstring(self):
        if self.totalTravelDays == 0.0:
            return "%s : none shipped"%self.name
        else:
            str= "%s \n"%self.name
            str += "   Total trips %d\n"%self.totalTrips
            str += "   Total km traveled %g\n"%self.totalKm
            str += "   Total days in transit %g\n"%self.totalTravelDays
            str += "   Broke %d instances\n"%self.nBroken
            str += "\n"
            return str
    def getSummaryDict(self):
        return {'Type':'icetype','Name':self.name, "TotalTrips":self.totalTrips, "TotalKm":self.totalKm,
                "TotalTravelDays":self.totalTravelDays,"NBroken":self.nBroken,"NCreated":self.nCreated,
                "NBrokenAbsolute":self.absoluteNBroken,"NCreatedAbsolute":self.instanceCount}
    def resetCounters(self):
        self.totalTrips= 0
        self.totalKm= 0.0
        self.totalTravelDays= 0.0
        self.nCreated= 0
        self.nBroken= 0
    def recordTransport(self, nInstances, fromWH, toWH, transitTimeDays, level, conditions):
        km= fromWH.getKmTo(toWH, level, conditions)
        self.totalKm += km
        self.totalTravelDays += transitTimeDays
    def getNDosesPerVial(self): 
        """Returns doses per vial- since everything shippable is sometimes treated like a vaccine"""
        return 1
    def canLeaveOut(self):
        """Returns true if this type can be stored at room temperature"""
        return False
    def canFreeze(self):
        """Returns true if this type can be stored at freezing temperatures"""
        return True # freeze us, please
    def canKeepOpenVials(self,howLongOpen):
        """
        If the first dose from a vial has been used, can the rest still be used after 'howLongOpen' days?  
        Obviously this is nonsense for Shippable things that don't actually hold multipe doses.
        """
        return False
    
    def recordBreakage(self,nInstances):
        """
        If the BreakageModel calculates that nInstances of these are broken in storage or transport, this
        method is used to inform the ShippableType of that destruction.  Note that nInstances is the number
        of instances broken, so if the ShippableType actually represents cold boxes, that's the number
        of boxes broken; it does not indicate that any vials stored in those boxes are broken.
        """
        self.nBroken += nInstances
        self.absoluteNBroken += nInstances
        
    def randSeed(self,seed=None):
        self.rndm.seed(seed)
        self.rndm.jumpahead(self.rndm_jumpahead) 

    def recordTreatment(self,nTreated,nApplied,nInstancesUsedForTreatment):
        """
        Records the number of instances of this ShippableType consumed in a treatment event, the number
        of patients who applied for that treatment, and the number of patients for which treatment was
        actually provided.
        """
        if nApplied!=0:
            print '######## Treated %d %d %d'%(nTreated,nApplied,nInstancesUsedForTreatment)
        if nTreated!=0:
            raise RuntimeError('Internal error: Used an Ice to treat a patient')
    def getStoragePriorityList(self):
        """
        Returns an ordered list of StorageType instances indicating the desirability of storing this
        ShippableType in each StorageType, most desirable first.
        """
        if self.storagePriorityList is None:
            assert hasattr(self,'sim'), "This %s has not been decorated with 'sim' by TypeManager"%self.typeName
            self.storagePriorityList= [self.sim.storage.frozenStorage(),self.sim.storage.roomtempStorage()]
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
        
        IceType instances travel as singletons.
        """
        return None

#    def getPackageType(self, pkgCategory):
#        """
#        Returns the largest smaller than or equal to the given pkgCategory, where pkgCategory
#        is one of the enumerated values provided by the packagetypes module.  Except that we don't
#        expect this type to travel in packages.
#        """
#        assert isinstance(pkgCategory,types.IntType), "getPackageType: pkgCategory %s should be an integer"%repr(pkgCategory)
#        assert pkgCategory in packagingmodel.pkgCategorySet, "getPackageType got the invalid pkgCategory %d"%pkgCategory
#        raise RuntimeError("Tried to get packagetype %s for a %s"%(packagingmodel.pkgCategoryNames[pkgCategory],
#                                                                   self.__class__.__name__))

    def getPackageTypeList(self):
        """
        Returns (a shallow copy of) the list of all valid package types for this Shippable, in order.  
        """
        raise RuntimeError("called getPackageTypeList for a %s"%self.__class__.__name__)
    
    def getSingletonStorageVolume(self, withDiluent):
        """
        Output is in CCs.  This is total shelf space to store this Fridge, including 
        packaging- that is, the external volume of the Fridge including the box it comes in.
        
        We'll worry about returning a realistic value when we start tracking room temperature space.
        Obviously ice doesn't come with 'diluent'.
        """
        return self.volCC

class DeliverableIceType( IceType ):
    def activate(self, **keywords): 
        """
        We must take this opportunity to make sure any required types are also activated.
        """
        retval = super(DeliverableIceType,self).activate(**keywords)
        assert retval==self, "Internal error: there is a problem with the Deliverable inheritence hierarchy"
        for reqType in self.getRequiredToPrepSC(1).keys():
            self.manager.getTypeByName(reqType.name)
        
        return retval

class IceTypeManager(trackabletypes.TrackableTypeManager):

    subTypeKey = "ice"

    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All IceTypes have presumably already been defined within the sim-wide TypeManager.
        """
        trackabletypes.TrackableTypeManager.__init__(self, typeManager)
        self.typeClass= IceType
            


