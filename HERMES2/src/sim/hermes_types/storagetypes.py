#!/usr/bin/env python


__doc__=""" storagetypes.py
This module implements storage temperatures as a type by
emulating the TypeManager interface.
"""

_hermes_svn_id_="$Id$"

import abstractbaseclasses
import typemanager
import genericcollection
import constants as C

storageTypeNames= ["freezer","cooler","roomtemperature"]
coolerStorageTypeNames= ["cooler"]
storageTypes= "placeholder" # for backward compatibility

class StorageType(abstractbaseclasses.ManagedType):
    typeName= 'storage'
    def __init__(self, name):
        abstractbaseclasses.ManagedType.__init__(self)
        self.name= name

    @classmethod
    def fromRec(cls,recDict,typeManager):
        assert('Name' in recDict)
        return StorageType(recDict['Name'])

    def __repr__(self):
        return "<StorageType(%s)>"%self.name

    def __str__(self):
        return self.name

    def summarystring(self):
        return self.name \
               + '\n   No specific characteristics ' \
               +'\n\n'

    def statisticsstring(self):
        str= "%s \n"%self.name
        str += "      No statistics are currently gathered\n"
        str += "\n"
        return str

    def getSummaryDict(self):
        return {'Type':'storagetype','Name':self.name}

    def resetCounters(self): 
        pass

class StorageTypeManager(typemanager.SubTypeManager):

    subTypeKey = "storage"

    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All StorageTypes have presumably already been defined within the sim-wide TypeManager.
        """
        self.tm= typeManager
        self.typeClass= StorageType
        
    def getCollection(self, tupleList=[]):
        """
        format of tupleList is [(storageType,nCC),(storageType,nCC)...]
        """
        return self.tm.getCollectionImplementing(tupleList, self.typeClass)

    def getTypeByName(self, name, activateFlag=True): 
        result= self.tm.getTypeByName(name, activateFlag=activateFlag)
        assert isinstance(result,self.typeClass), "%s is not the name of a StorageType"
        return result
    
    def validTypeName(self,name): return self.tm.validTypeNameImplementing(name, self.typeClass)
    
    def getActiveTypeNames(self): return self.tm.getActiveTypeNamesImplementing(self.typeClass)

    def getActiveTypes(self): return self.tm.getActiveTypesImplementing(self.typeClass)

    def translateCapacityInfo(self, tupleList):
        """
        format of tupleList is [(storageTypeName,nCC),(storageTypeName,nCC)...]
        The return value substitutes StorageType instances for the storageTypeNames.
        """
        return [(self.getTypeByName(str),v) for str,v in tupleList]
    
    def discardStorage(self):
        return self.getTypeByName("roomtemperature")

    def frozenStorage(self):
        return self.getTypeByName("freezer")

    def roomtempStorage(self):
        return self.getTypeByName("roomtemperature")

    def outdoorDiscardStorage(self):
        # this should be harmonized with discardStorage()
        return self.getTypeByName("outdoorDiscard")
    
    def coolStorageList(self):
        return [self.getTypeByName(nm) for nm in coolerStorageTypeNames]

    def getTotalRefrigeratedVol(self, collection):
        """
        Given a Collection of StorageType information, return the total volume which is not
        at room temperature.  Values are generally in CC.
        """
        assert issubclass(collection.implementedClass, self.typeClass), \
        "collection of %s passed to getTotalRefrigeratedVol"%collection.implementedClass
        roomtempType= self.roomtempStorage()
        return sum([n for f,n in collection.items() if f!=roomtempType])
    def getTotalCoolVol(self, collection):
        """
        Given a Collection of StorageType information, return the total volume which is
        'cool'.  Values are generally in CC.
        """
        assert issubclass(collection.implementedClass, self.typeClass), \
        "collection of %s passed to getTotalCoolVol"%collection.implementedClass
        coolList= self.coolStorageList()
        return sum([v for k,v in collection.items() if k in coolList])

    def getStorageVolumes(self, collection):
        """
        Given a Collection of StorageType information, return the total volume 
        of freezer, cool, and room temperature space.
        Values are generally in CC.
        """
        assert issubclass(collection.implementedClass, self.typeClass), \
            "collection of %s passed to getTotalCoolVol"%collection.implementedClass
        f=c=w=0.0
        for k,v in collection.items():
            if k is self.getTypeByName("freezer"): f += v
            elif k is self.getTypeByName("cooler"): c += v
            elif k is self.getTypeByName("roomtemperature"): w += v
        return f,c,w
