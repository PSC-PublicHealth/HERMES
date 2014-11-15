#!/usr/bin/env python

########################################################################
# Copyright C 2009, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" trackabletypes.py
This module provides a TypeManager class with some specialization to handle
Trackables.
"""

_hermes_svn_id_="$Id$"

import types
from abstractbaseclasses import Shippable, TrackableType, DeliverableType
import util
import typemanager
import csv_tools
        
class TrackableTypeManager:
    """
    A specialization of TypeManager just for Trackables.
    """
    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All VaccineTypes have presumably already been defined within the sim-wide TypeManager.
        """
        self.tm= typeManager
        self.typeClass= TrackableType
        
    def getCollection(self, tupleList=[]):
        """
        format of tupleList is [(ShippableType,n),(ShippableType,n)...]
        """
        return self.tm.getCollectionImplementing(tupleList, self.typeClass)
    
    def getCollectionFromGroupList(self, listOfTrackableGroups):
        tupleList = []
        for g in listOfTrackableGroups:
            if isinstance(g,Shippable): 
                if g.getAge() is not None: 
                    tupleList.append((g.getType(),g.getCount()))
            else: tupleList.append((g.getType(),1))
        result= self.getCollection(tupleList)
        return result

    def getTypeByName(self,name,activateFlag=True):
        result= self.tm.getTypeByName(name,activateFlag=activateFlag)
        assert isinstance(result,self.typeClass), "%s is not the name of a %s"%(name,self.typeClass.__name__)
        return result
    
    def validTypeName(self,name): return self.tm.validTypeNameImplementing(name, self.typeClass)
    
    def getActiveTypeNames(self): return self.tm.getActiveTypeNamesImplementing(self.typeClass)

    def getActiveTypes(self): return self.tm.getActiveTypesImplementing(self.typeClass)

    def getAllValidTypeNames(self): return self.tm.getAllValidTypeNamesImplementing(self.typeClass)
    
    def addType(self, recDict, verbose=False, debug=False):
        self.tm.addType(recDict, self.typeClass, verbose, debug)
        
    def _accumRequiredPairs(self,name,allRecsDict,count=1,recurLevel=0):
        """
        This routine recurses down through shippable type records, accumulating requirements:
        if count and name are 3 and T1 respectively, and type T1 requires 4 of T2 and nothing
        else, this should return [(3,'T1'), (12,'T2')] .  Records of allRecsDict are
        presumed to be indexed by name string and to have rec[4] be a list of the form
        [(count,typeString), (count,typeString),...] of requirements.
        """
        assert recurLevel<10, "recursion is too deep- is there a dependency loop involving %s?"%name
        result = [(count,name)]
        for subCount,subName in allRecsDict[name][4]:
            subList = self._accumRequiredPairs(subName, allRecsDict, count*subCount, recurLevel+1)
            result += subList
        #print "%sreturning %s at recurLevel %d"%(recurLevel*"    ",result,recurLevel)
        return result
    
    def addPrepSupplies(self, rawSC):
        """
        This routine scans the given ShippableCollection for DeliverableTypes, and adds the quantities of
        the needed ShippableTypes necessary to successfully call prepForDelivery on those deliverables.  Note
        that it is not assuming integer inputs and does not round; fractional vials will require fractional
        amounts of supplies.  Note also that it doesn't include ShippableType quantities already in rawSC.
        Thus, if you call addPrepSupplies( addPrepSupplies ( someSC ) ) you will end up with twice the supply
        of shippables needed for prep.
        
        rawSC is not modified; the result is an entirely separate ShippableCollection.
        """
        fullSC = rawSC.copy()
        for v,n in rawSC.items():
            if isinstance(v,DeliverableType):
                fullSC += v.getRequiredToPrepSC(n)
        return fullSC
                
    def importRecords(self, tupleList, verbose=False, debug=False):
        """
        The format of tupleList is [([fileNameOrRecList,...], ShippableType, DeliverableType), ...]  where 
        fileNameOrRecList is either the name of a .csv file containing records for trackables or
        a list of dictionaries representing such records.  Those records are used to define 
        instances of the corresponding ShippableType and DeliverableType, as follows.  Either
        ShippableType or DeliverableType may be None, but an exception will be raised if an actual type
        is determined to be needed as described below.  DeliverableType may also be a TrackableType
        which is not a DeliverableType, for example a FridgeType; in this case ShippableType is expected
        to be None.
        
        Each CSV record may contain a 'Requires' column, containing an expression in a format like:
        '3*SOME_VACCINE_TYPE+SOME_ICE_TYPE' .  The presence of such a column implies that DeliverableType
        must be an actual DeliverableType (like a VaccineType) rather than a TrackableType (like a FridgeType).
        This information defines a dependency on other shippable types.  For example, if this Requires column 
        appeared in a record with the 'Name' column entry 'MY_VACCINE', MY_VACCINE would have a dependency on 
        SOME_VACCINE_TYPE and SOME_ICE_TYPE.  The required types must be ShippableTypes.
        
        Once all records have been scanned, those types which no other type lists as a dependency are
        built using the given DeliverableType value.  Those on which some other type depends are built
        using the given ShippableType value.  The 'Requires' entry above would force SOME_VACCINE_TYPE 
        and SOME_ICE_TYPE to be ShippableTypes rather than DeliverableTypes (or non-shippable TrackableTypes).
        
        Once every input record has been scanned for dependencies and classified, those which are shippables
        will be instantiated using the ShippableType entry from the same input tuple; the rest will be 
        instantiated with the corresponding DeliverableType entry.
        """
        allRecsDict = {} # indexed by name; entries are tuples like (rec, shippableType, deliverableType, dependedOnList)
        for fnameOrRecList, shippableClass, deliverableClass in tupleList:
            if fnameOrRecList is None:
                continue
            elif not isinstance(fnameOrRecList, types.ListType):
                fnameOrRecList = [fnameOrRecList] # *now* it's a list

            thisBlockDict = {}
            for fnameOrRec in fnameOrRecList:
                if fnameOrRec is None:
                    continue
                elif isinstance(fnameOrRec,types.DictType):
                    # Single record
                    r = fnameOrRec
                    assert 'Name' in r.keys(), "Record has no 'Name' field"
                    if r['Name'] in thisBlockDict:
                        util.logWarning("Definition of type %s was masked by an earlier definition"%r['Name'])
                    else:
                        thisBlockDict[r['Name']] = (r, shippableClass, deliverableClass, [], [])                       
                else:
                    assert isinstance(fnameOrRec,types.StringTypes), "Record source is neither a string nor a list"
                    if fnameOrRec not in ['', 'None']:
                        with util.openDataFullPath(fnameOrRec) as f:
                            keys,recs = csv_tools.parseCSV(f)
                            assert 'Name' in keys, "Shippable table %s has no 'Name' field"%fnameOrRec
                            for r in recs:
                                if r['Name'] in thisBlockDict:
                                    util.logWarning("Definition of type %s was masked by an earlier definition"%r['Name'])
                                else:
                                    thisBlockDict[r['Name']] = (r, shippableClass, deliverableClass, [], [])                       
            for k,v in thisBlockDict.items():
                if k in allRecsDict:
                    raise RuntimeError("Two different shippable types share the name '%s'"%k)
                else:
                    allRecsDict[k] = v
            
        for name,v in allRecsDict.items():
            rec, sClass, dClass, depList, reqList = v
            if 'Requires' in rec and rec['Requires'] is not None and rec['Requires'] != '':
                assert dClass is None or isinstance(dClass,DeliverableType), \
                    "The ManagedType %s has a Requires field but is not Shippable"%rec['Name']
                invTupleList = util.parseInventoryString(rec['Requires'])
                for count,subName in invTupleList:
                    allRecsDict[name][4].append((count,subName))
                    if subName in allRecsDict: allRecsDict[subName][3].append(name)
                    else:
                        raise RuntimeError("%s requires the unknown type %s"%(name,subName))

        for name,v in allRecsDict.items():
            rec, sClass, dClass, depList, reqPairList = v
            if len(depList):
                # This is required by something
                if debug: print "%s is required by %s"%(name,depList)
                self.tm.addType(rec, sClass, verbose, debug)
            else:
                # Not required by anything, so this must be a deliverable
                if debug: print "%s is a deliverable or trackable of class %s"%(name,dClass)
                self.tm.addType(rec, dClass, verbose, debug)
                
        for name,v in allRecsDict.items():
            rec, sClass, dClass, depList, reqPairList = v
            if len(depList) == 0: 
                # This is a deliverable
                reqPairTList = self._accumRequiredPairs(name, allRecsDict)
                reqPairTList = reqPairTList[1:] # Remove the first element, which is the deliverable itself
                tp = self.getTypeByName(name,activateFlag=False)
                if isinstance(tp, DeliverableType):
                    reqPairSC = self.getCollection([(self.getTypeByName(nm,activateFlag=False),ct)
                                                    for ct,nm in reqPairTList])
                    tp.setRequiredToPrepSC(reqPairSC)
                else: 
                    assert len(reqPairTList) == 0, "Found %s when expecting a DeliverableType"%name                
            else:
                # This shippable is required by something
                for depName in depList:
                    depT = self.getTypeByName(depName,activateFlag=False)
                    self.getTypeByName(name, activateFlag=False).requiredByList.append(depT)
                
                
