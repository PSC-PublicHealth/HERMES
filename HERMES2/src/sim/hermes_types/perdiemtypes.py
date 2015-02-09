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

""" perdiemtypes.py
This module produces object instances which implement per diem payment
patterns.
"""

_hermes_svn_id_ = "$Id$"

import math
import abstractbaseclasses
from typemanager import SubTypeManager
from csv_tools import castTypes
import perdiemmodel


class PerDiemType(abstractbaseclasses.ManagedType,
                  abstractbaseclasses.CostableType,
                  perdiemmodel.PerDiemModel):
    typeName = 'perDiem'

    def __init__(self, recDict):
        """ name is intended to describe a type of per diem

        e.g. 'Std_PerDiem_None'
        """
        super(PerDiemType, self).__init__()
        self.name = recDict['Name']
        assert all([k in recDict for k in ['DisplayName',
                                           'BaseAmount',
                                           'BaseAmountCur',
                                           'BaseAmountYear',
                                           'MustBeOvernight',
                                           'CountFirstDay',
                                           'MinKmHome']])
        self.recDict = recDict.copy()

    @classmethod
    def fromRec(cls, recDict, typeManager):
        assert 'Name' in recDict, 'Missing required Name field'
        return PerDiemType(recDict)

    def __repr__(self):
        return "<PerDiemType(%s)>" % self.name

    def __str__(self):
        return self.name

    def summarystring(self):
        infoStr = '%s, amount %g %s %d' % (self.recDict['DisplayName'],
                                           self.recDict['BaseAmount'],
                                           self.recDict['BaseAmountCur'],
                                           self.recDict['BaseAmountYear'])
        return self.name \
            + '\n  %s ' % infoStr \
            + '\n\n'

    def statisticsstring(self):
        s = "%s : no statistics" % self.name
        return s

    def getSummaryDict(self):
        return {'Type': 'perdiemtype', 'Name': self.name}

    @classmethod
    def getColumnTypeDict(cls):
        """
        This method returns a dict of the form {columnKey:[datatypes.DataType]},
        with the expectation that csv_tools.castColumn will be used with the
        given type to convert incoming record fields.
        """
        return {u'BaseAmountYear': [castTypes.POSITIVE_INT, castTypes.EMPTY_IS_NONE],
                u'BaseAmount': [castTypes.FLOAT, castTypes.EMPTY_IS_NONE],
                u'MinKmHome': [castTypes.FLOAT, castTypes.EMPTY_IS_ZERO],
                u'MustBeOvernight': [castTypes.BOOLEAN],
                u'CountFirstDay': [castTypes.BOOLEAN]
                }

    def resetCounters(self):
        pass

    def calcPerDiemDays(self, tripJournal, homeWH):
        """
        This function is called once at the end of each full round trip for any
        shipping process to calculate the number of days of per diem pay the
        driver is to receive, based on the details of the just- completed trip.

        tripJournal is a list of tuples describing the steps of the
        just-completed trip.  tripJournal entries all start with
        (stepname, legStartTime, legEndTime, legConditions...);
        see the description of warehouse.createTravelGenerator for additional
        details.

        homeWH is the warehouse which is the driver's 'home'; that is, where
        the driver might be expected to sleep for free. Typically legEndTime
        for one leg will equal legStartTime for the next.

        The return value of this function is expected to be a number.
        """
        currentWH = homeWH
        totDays = 0.0
        mustBeOvernight = self.recDict['MustBeOvernight']
        countFirstDay = self.recDict['CountFirstDay']
        minKmHome = self.recDict['MinKmHome']
        for tpl in tripJournal:
            op = tpl[0]
            legStart = tpl[1]
            legEnd = tpl[2]
            conditions = tpl[3]
            if op == 'move':
                currentWH = toWH = tpl[5]  # @UnusedVariable
            if conditions is None:
                conditions = 'normal'
            if homeWH.getKmTo(currentWH, currentWH.category, conditions) > minKmHome:
                totDays += math.floor(legEnd) - math.floor(legStart)
        if mustBeOvernight and totDays < 1.0:
            return 0
        totDays = int(totDays)
        if countFirstDay:
            totDays += 1
        return totDays

    def calcPerDiemAmountTriple(self, tripJournal, homeWH):
        """
        This function is called once at the end of each full round trip for any
        shipping process to calculate the per diem pay the driver is to
        receive, based on the details of the just- completed trip.

        tripJournal is a list of tuples describing the steps of the
        just-completed trip.  tripJournal entries all start with
        (stepname, legStartTime, legEndTime, legConditions...);
        see the description of warehouse.createTravelGenerator for additional
        details.

        homeWH is the warehouse which is the driver's 'home'; that is, where
        the driver might be expected to sleep for free. Typically legEndTime
        for one leg will equal legStartTime for the next.

        The return value of this function is expected to to be a tuple
        of the form (amount, currencyCode, baseYear).
        """
        days = self.calcPerDiemDays(tripJournal, homeWH)
        return (days * self.recDict['BaseAmount'], self.recDict['BaseAmountCur'],
                self.recDict['BaseAmountYear'])


class PerDiemTypeManager(SubTypeManager):

    subTypeKey = "perdiems"

    def __init__(self, typeManager):
        """
        Initialize the manager, which is really just a wrapper around the
        simulation-wide TypeManager, passed in here as typeManager.
        All PerDiemTypes have presumably already been defined within the
        sim-wide TypeManager.
        """
        self.tm = typeManager
        self.typeClass = PerDiemType

    def getCollection(self, tupleList=[]):
        """
        format of tupleList is [(perDiemType,n),(perDiemType,n)...]
        """
        return self.tm.getCollectionImplementing(tupleList, self.typeClass)

    def getTypeByName(self, name, activateFlag=True):
        result = self.tm.getTypeByName(name, activateFlag=activateFlag)
        assert isinstance(result, self.typeClass), \
            "%s is not the name of a PerDiemType" % name
        return result

    def validTypeName(self, name):
        return self.tm.validTypeNameImplementing(name, self.typeClass)

    def getActiveTypeNames(self):
        return self.tm.getActiveTypeNamesImplementing(self.typeClass)

    def getActiveTypes(self):
        return self.tm.getActiveTypesImplementing(self.typeClass)
