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

__doc__=""" typemanager.py
This module provides abastract base classes for managing classes representing types
of things, for example instances of VaccineType.
"""

_hermes_svn_id_="$Id$"

import abstractbaseclasses, genericcollection, csv_tools
import util

class TypeManager(object):
    """
    A container to hold instances of a class that are intended to be constant through
    a simulation and act as 'types'- instances of class VaccineType for example. All
    the managed entities must satisfy the ManagedType abstract base class.
    """
    
    class TypeCollection(genericcollection.GenericCollection):
        """
        A supply of different managedTypes, with some convenient math operators.
        """
        def __init__(self, owner, tupleList, implementedClass):
            """
            Owner is the creating TypeManager.
            format of tupleList is [(managedType,nOfThese),(managedType,nOfThese)...]
            """
            assert issubclass(implementedClass, abstractbaseclasses.ManagedType), "Attempted to create a collection of unmanaged types"
            for t,n in tupleList: # @UnusedVariable n
                assert isinstance(t,implementedClass), "Bad %s collection element %s"%(implementedClass.typeName, t.name)
            genericcollection.GenericCollection.__init__(self,tupleList)
            self.implementedClass= implementedClass
            self.typeName = (implementedClass.typeName).capitalize()+"Collection"
            self.owner = owner
            
        def splitOut(self,subClass,newCollectionClass=None):
            """
            Select those elements of the collection the key of which satisfies isinstance(key,subClass) and
            return a new collection containing only those elements.  The corresponding elements of the current 
            collection are deleted or their values are set to 0.0.  The implementedClass of the new collection
            is newCollectionClass if that value is given, or subClass if newCollectionClass is None.
            """
            splitTuples= []
            for k,v in self.getTupleList():
                if isinstance(k,subClass):
                    splitTuples.append((k,v))
                    self[k]= 0.0
            if newCollectionClass is None:
                return self.owner.getCollectionImplementing(splitTuples,subClass)
            else:
                return self.owner.getCollectionImplementing(splitTuples,newCollectionClass)
        
        def getSimilarCollection(self, tupleList):
            """
            Produce a collection with the same implementedClass as this one
            """
            return self.owner.getCollectionImplementing(tupleList, self.implementedClass)

    def __init__(self, definitionTupleList, verbose=False, debug=False, sim=None):
        """
        Initialize the manager.  typeClass is the class that will be managed, for example
        VaccineType.  definitionTupleList is a list of tuples of the form (definitionFile, defaultClassName)
        where:
        
          definitionFile is an open file containing class definition records
                    for the type, for example the return value of open('UnifiedVaccineTypeInfo.csv','rU').
          defaultClassName is a string giving the name of a class satisfying ManagedType.  This
                    element will be ignored for any record within the definition file which contains
                    a 'ClassName' value.
        """
        self.typeDict= {}  # Dictionary of all type instances by name, active and not.
        self.activeTypes= [] # list of the type instances which are active
        self.sim= sim
        assert( sim is not None )
        
        for definitionFile, targetClass in definitionTupleList:
            self.addTypeRecordsFromFile(definitionFile, targetClass, verbose, debug)
   
    def addType(self, recDict, targetClass, verbose=False, debug=False):
        """
        recDict is a single record dictionary of the type generated by parseCSV in response to an
        input record for this type.  targetClass must implement the ManagedType ABC.
        Duplicate named types are silently discarded.
        """
        #try:
        name = recDict['Name']
        if name in self.typeDict:
            return
        for k,v in targetClass.getColumnTypeDict().items():
            csv_tools.castEntry(recDict, k, v)
        self.typeDict[name]= targetClass.fromRec(recDict, self)
        assert isinstance(self.typeDict[name],abstractbaseclasses.ManagedType), "Cannot manage an instance of %s"%name

        # NOTE: the following constitute references to the typeClass instance.
        # Since typeClass.activate() may replace the instance, these references 
        # must be cleared and recreated around the call to typeClass.activate().
        #print 'addType %s %s'%(self.typeClass,name)
        self.typeDict[name].sim= self.sim
        self.typeDict[name].manager= self
#        except Exception,e:
#            if 'Name' in recDict:
#                print "***Warning*** Failed to load bad record for %s type %s: %s"%\
#                      (targetClass.typeName,recDict['Name'],e)
#                if debug:
#                    print recDict
#            else:
#                print "***Warning*** Failed to load bad record for nameless %s type: %s"%\
#                      (targetClass.typeName,e)
#                if debug:
#                    print recDict
                        
    def addTypeRecordsFromFile(self, definitionFile, targetClass, verbose=False, debug=False):
        """
        recDictList is a list of record dictionaries of the type generated by parseCSV.
        targetClass must implement the ManagedType ABC.
        """
        with util.openFileOrHandle(definitionFile) as f:
            keys, recDictList = csv_tools.parseCSV(f)
        self.addTypeRecordsFromRecs(recDictList, targetClass, verbose, debug)
  
    def addTypeRecordsFromRecs(self, recs, targetClass, verbose=False, debug=False):
        # no duplicate records within a single "file"
        s = set()
        for rec in recs:
            if 'Name' not in rec:
                continue  # I'll let someone else catch this error
            if rec['Name'] in s:
                raise RuntimeError("type %s is defined twice in one file"%rec['Name'])
            s.add(rec['Name'])
        for k,v in targetClass.getColumnTypeDict().items():
            csv_tools.castColumn(recs, k, v)
        for rec in recs: self.addType(rec, targetClass, verbose, debug)

    def resetAllCounters(self):
        """
        Reset the counters of all type instances, active and otherwise.  The type
        instances know what their counters are.
        """
        for t in self.typeDict.itervalues():
            t.resetCounters()
            
    def getTypeByName(self,name,activateFlag=True,**keywords):
        """
        Returns the type instance with the given name.  Unless activateFlag is
        False, the type instance is marked active as a side effect of this call.
        Any keyword arguments are passed to the ManagedType's 'activate()' method.
        """
        if name in self.typeDict:
            t= self.typeDict[name]
            if t in self.activeTypes:
                if not t.checkCompatibleDefinition(**keywords):
                    raise RuntimeError("Incompatible definition of  %s type %s: keywords %s this time"%\
                                       (t.typeName,name,keywords))
            elif activateFlag:
                #print 'activate %s %s'%(t.name,keywords)
                tNew= t.activate(**keywords) # allow activation method to substitute a replacement
                # If a replacement instance has been substituted, dereference the old version 
                # and reference the new.  See the note in __init__().
                if tNew != t:
                    tNew.sim= t.sim
                    t.sim= None
                    tNew.manager= t.manager
                    t.manager= None
                    t= tNew
                    self.typeDict[name]= t
                t.index= len(self.activeTypes) # zero-based offset into active type list
                self.activeTypes.append(t)
            return t
        else:
            raise RuntimeError("Unknown type <%s>"%name)
            
    def getActiveTypeNames(self):
        "Returns a list of the names of all active type instances"
        return [v.name for v in self.activeTypes]
    
    def getActiveTypeNamesImplementing(self, someClass):
        "Returns a list of the names of all active type instances satisfying isinstance(type, someClass)"
        return [v.name for v in self.activeTypes if isinstance(v, someClass)]
    
    def getActiveTypes(self):
        return self.activeTypes[:] # shallow copy

    def getActiveTypesImplementing(self, someClass):
        return [v for v in self.activeTypes if isinstance(v, someClass)]

    def validTypeName(self,name):
        """
        Test to see if the type name is known without activating it.
        """
        return (name in self.typeDict)

    def getAllValidTypeNames(self):
        return self.typeDict.keys()[:]

    def validTypeNameImplementing(self, name, someClass):
        """
        Test to see if the type name is known without activating it.
        """
        return (name in self.typeDict and isinstance(self.typeDict[name], someClass))

    def getAllValidTypeNamesImplementing(self, someClass):
        return [name for name in self.typeDict.keys() if isinstance(self.typeDict[name],someClass)]

    def getCollection(self, tupleList=[]):
        """
        format of tupleList is [(managedType,n),(managedType,n)...]
        """
        return self.getCollectionImplementing(tupleList, abstractbaseclasses.ManagedType)

    def getCollectionImplementing(self, tupleList, someClass):
        """
        format of tupleList is [(someType,n),(someType,n)...]
        where all managedTypes must satisfy isinstance (someType, someClass)
        and someClass must satisfy isinstance(someClass,ManagedType)
        """
        return TypeManager.TypeCollection(self, tupleList, someClass)


class SubTypeManager(object):
    """A class from which specialized type managers will be derived.
    """

    subTypeKey = None
    """A key used for indexing derived *TypeManager types
    """

def main():
    "Provides a few test routines"

    from input import UnifiedInput
    from storagetypes import StorageType, storageTypeNames
    from vaccinetypes import VaccineType
    from trucktypes import TruckType
    from peopletypes import PeopleType
    from fridgetypes import FridgeType
    from util import openDataFullPath
    
    tm= TypeManager([], verbose= True, debug= True, sim="junk")
    for rec in [{"Name":stn} for stn in storageTypeNames]: 
        tm.addType(rec, StorageType, verbose=True, debug=True)

    u= UnifiedInput()
    for fname,cl in [(u.vaccineFile,VaccineType), 
                     (u.truckFile,TruckType),
                     (u.peopleFile,PeopleType), 
                     # (u.fridgeFile,FridgeType) # exclude fridges because they need a valid 'sim' to load
                     ]:
        with openDataFullPath(fname,'rU') as f:
            tm.addTypeRecordsFromFile(f, cl, verbose=True, debug=True)
        tm.addType({"Name":"default", "CoolVolumeCC":1.0e9, "Note":"default type"}, TruckType)
    v= tm.getTypeByName('N_Tuberculosis')
    print v
    print v.typeName.capitalize()

############
# Main hook
############

if __name__=="__main__":
    main()


