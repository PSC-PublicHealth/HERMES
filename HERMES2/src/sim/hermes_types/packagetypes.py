#!/usr/bin/env python

###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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

__doc__=""" packagetypes.py
This module produces object instances which know the characteristics of
different types of packaging- individual vials, boxes, pallets, etc..
"""

_hermes_svn_id_="$Id$"

import abstractbaseclasses
import typemanager
import packagingmodel

class PackageType(abstractbaseclasses.ManagedType):
    typeName= 'package'
    def __init__(self, name, containsStr, count, categoryStr, volumeCC, sortOrder):
        """
        name is intended to describe a type of packaging, e.g. 'N_Tuberculosis_box'
        containsStr is the name of the ShippableType contained by this package, e.g. 'N_Tuberculosis'
        count is the integer number of Shippable instances of that type contained by the package
        categoryStr is a general category of package, e.g. 'box'
        volumeCC is the outside volume of the package in CC
        sortOrder is used for output; packages will be listed in increasing sortOrder
        """
        abstractbaseclasses.ManagedType.__init__(self)
        self.name = name
        self.containsStr = containsStr
        self.count = int(count)
        self.category = packagingmodel.pkgCategories[categoryStr]
        self.volumeCC = volumeCC
        self.nextSmaller = None
        self.sortOrder = sortOrder

    @classmethod
    def fromRec(cls,recDict, typeManager):
        assert(recDict.has_key('Name'))
        return PackageType(recDict['Name'], recDict['Contains'], recDict['Count'], recDict['Category'],
                           recDict['Volume(CC)'],recDict['SortOrder'])
    def __repr__(self):
        return "<PackageType(%s,%f)>"%(self.name, self.count)

    def __str__(self):
        return self.name

    def summarystring(self):
        return "%s: contains %d of %s, volume %f"%(self.name, self.count, self.containsStr, self.volumeCC)

    def statisticsstring(self):
        str= "%s \n"%self.name
        str += "      No statistics are currently gathered\n"
        str += "\n"
        return str

    def getSummaryDict(self):
        return {'Type':'packagetype','Name':self.name}

    def resetCounters(self):
        self.patientsTreated= 0
        self.patientsApplied= 0
        
    def setNextSmaller(self,nextSmaller):
        """
        Tell this PackageType that the next smaller PackageType containing the same ShippableType is
        nextSmaller.  A value of None for nextSmaller refers to the singleton package.
        """
        self.nextSmaller = nextSmaller
        
    def getNextSmaller(self):
        """
        What is the next smaller package type?
        """
        return self.nextSmaller


class PackageTypeManager(typemanager.SubTypeManager):

    subTypeKey = "packaging"

    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All PeopleTypes have presumably already been defined within the sim-wide TypeManager.
        """
        self.tm= typeManager
        self.typeClass= PackageType
        
    def getCollection(self, tupleList=[]):
        """
        format of tupleList is [(packageType,n),(packageType,n)...]
        """
        return self.tm.getCollectionImplementing(tupleList, self.typeClass)

    def getTypeByName(self,name,activateFlag=True): 
        result= self.tm.getTypeByName(name,activateFlag=activateFlag)
        assert isinstance(result,self.typeClass), "%s is not the name of a PackageType"
        return result
    
    def validTypeName(self,name): return self.tm.validTypeNameImplementing(name, self.typeClass)
    
    def getActiveTypeNames(self): return self.tm.getActiveTypeNamesImplementing(self.typeClass)

    def getActiveTypes(self): return self.tm.getActiveTypesImplementing(self.typeClass)
        
    def getAllValidTypeNames(self): return self.tm.getAllValidTypeNamesImplementing(self.typeClass)
