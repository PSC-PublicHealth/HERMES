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

__doc__=""" stafftypes.py
This module produces object instances which know the characteristics of
different types of staff- drivers, warehouse workers, etc..
"""

_hermes_svn_id_="$Id$"

import abstractbaseclasses
import weakref
import typemanager

class StaffType(abstractbaseclasses.TrackableType):
    typeName= 'staff'
    def __init__(self, recDict):
        """
        name is intended to describe a type of staff, e.g. 'driver'
        """
        super(StaffType,self).__init__()
        self.name= recDict['Name']
        self.instanceClassName = 'Staff'
        self.recDict = recDict.copy()
        self.instanceCount= 0
        self.nCreated= 0

    @classmethod
    def fromRec(cls,recDict, typeManager):
        assert(recDict.has_key('Name'))
        return StaffType(recDict)

    def createInstance(self,count=1,name=None,currentAge=0.0,tracked=False):
        """
        Create an instance of this StaffType.  The instance will be a Staff.
        """
        if count!=1:
            raise RuntimeError("Internal error: Staff creation with non-unit count")
        self.instanceCount += 1
        self.nCreated += 1
        if name is None:
            name= "%s#%d"%(self.name,self.instanceCount)
        return globals()[self.instanceClassName](self, name=name, currentAge=currentAge, tracked=tracked )

    def __repr__(self):
        return "<StaffType(%s)>"%self.name

    def __str__(self):
        return self.name

    def summarystring(self):
        infoStr = '%s, salary %g %s %d'%(self.recDict['DisplayName'], 
                                         self.recDict['BaseSalary'],
                                         self.recDict['BaseSalaryCur'],
                                         self.recDict['BaseSalaryYear'])
        return self.name \
               + '\n  %s '%infoStr \
               +'\n\n'

    def statisticsstring(self):
        s= "%s : %d instances"%(self.name,self.instanceCount)
        return s

    def getSummaryDict(self):
        return {'Type':'stafftype','Name':self.name}

    def resetCounters(self):
        pass

class Staff(abstractbaseclasses.Trackable, abstractbaseclasses.Costable):
    """
    This is basically an instance of a FridgeType.  
    fridgeType is the creating type.
    storageCapacityInfo is a list of (storageType,volumeInCCs) tuples
    """
    classPartner = StaffType

    def __init__(self, staffType, name=None, currentAge=0.0, tracked=False):
        """
        This constructor is not meant to be called by the user- use FridgeType.createInstance() instead!
        
        fridgeType is the creating type.
        """
        abstractbaseclasses.Trackable.__init__(self)
        abstractbaseclasses.Costable.__init__(self)
        self.staffType= staffType
        self.name= name
        self.place= None
        self.tracked= tracked
        self.maybeTrack("creation")

    def getPendingCostEvents(self):
        return []

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
        return self.staffType 
    
    def getCount(self):
        """
        Staffs always come in singletons
        """
        return 1

    def attach(self,place,callingProc):
        assert self.place is None, "%s is already attached"%self.name
        self.place= weakref.proxy(place) # Avoid loop graph for easier GC
        place.attachStock(self)
        self.maybeTrack("attach to %s"%self.place.name)
    def detach(self,callingProc):
        assert self.place is not None, "%s:%d is not attached"%(self.name,self.history)
        raise RuntimeError("Attempted to detach Staff instance %s from %s"%(self.name,self.place.name))
#         self.place.detachStock(self)
#         self.maybeTrack("detach from %s"%self.place.name)
#         self.place= None
    def maybeTrack(self,info):
        if self.tracked:
            print '\n%g, "%s", "%s"\n'%(self.fridgeType.sim.now(),str(self),info)

class StaffTypeManager(typemanager.SubTypeManager):

    subTypeKey = "staff"

    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All StaffTypes have presumably already been defined within the sim-wide TypeManager.
        """
        self.tm= typeManager
        self.typeClass= StaffType
        
    def getCollection(self, tupleList=[]):
        """
        format of tupleList is [(staffType,n),(staffType,n)...]
        """
        return self.tm.getCollectionImplementing(tupleList, self.typeClass)

    def getTypeByName(self,name,activateFlag=True): 
        result= self.tm.getTypeByName(name,activateFlag=activateFlag)
        assert isinstance(result,self.typeClass), "%s is not the name of a StaffType"
        return result
    
    def validTypeName(self,name): return self.tm.validTypeNameImplementing(name, self.typeClass)
    
    def getActiveTypeNames(self): return self.tm.getActiveTypeNamesImplementing(self.typeClass)

    def getActiveTypes(self): return self.tm.getActiveTypesImplementing(self.typeClass)

