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

__doc__=""" peopletypes.py
This module produces object instances which know the characteristics of
different types of people- newborns, children, pregnant women, etc..
"""

_hermes_svn_id_="$Id$"

import abstractbaseclasses
import typemanager

genericPeopleTypeName= "GenericPeople"

class PeopleType(abstractbaseclasses.ManagedType):
    typeName= 'people'
    def __init__(self, name):
        """
        name is intended to describe a type of person, e.g. 'newborn'
        """
        abstractbaseclasses.ManagedType.__init__(self)
        self.name= name
        self.patientsTreated= 0
        self.patientsApplied= 0

    @classmethod
    def fromRec(cls,recDict, typeManager):
        assert(recDict.has_key('Name'))
        return PeopleType(recDict['Name'])

    def __repr__(self):
        return "<PeopleType(%s)>"%self.name

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
        return {'Type':'peopletype','Name':self.name}

    def resetCounters(self):
        self.patientsTreated= 0
        self.patientsApplied= 0

class PeopleTypeManager:
    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the simulation-wide TypeManager,
        passed in here as typeManager.
        All PeopleTypes have presumably already been defined within the sim-wide TypeManager.
        """
        self.tm= typeManager
        self.typeClass= PeopleType
        
    def getCollection(self, tupleList=[]):
        """
        format of tupleList is [(peopleType,n),(peopleType,n)...]
        """
        return self.tm.getCollectionImplementing(tupleList, self.typeClass)

    def getTypeByName(self,name,activateFlag=True): 
        result= self.tm.getTypeByName(name,activateFlag=activateFlag)
        assert isinstance(result,self.typeClass), "%s is not the name of a PeopleType"
        return result
    
    def validTypeName(self,name): return self.tm.validTypeNameImplementing(name, self.typeClass)
    
    def getActiveTypeNames(self): return self.tm.getActiveTypeNamesImplementing(self.typeClass)

    def getActiveTypes(self): return self.tm.getActiveTypesImplementing(self.typeClass)

