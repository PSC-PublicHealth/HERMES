#! /usr/bin/env python

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

""" dummycostmodel.py
This module holds classes used in calculating costs associated with simulations
"""

_hermes_svn_id_ = "$Id$"

import sys
import util
import csv_tools
import warehouse
import abstractbaseclasses
import perdiemmodel


def _clearPendingCosts(costable):
    costable.getPendingCostEvents()
    if isinstance(costable, abstractbaseclasses.CanOwn):
        costable.applyToAll(abstractbaseclasses.Costable, _clearPendingCosts)
    return None


class DummyCostManager:
    """
    This class presents the same API as CostManager, but does nothing.
    """
    def __init__(self, sim, model):
        self.sim = sim
        self.model = model
        self.intervalStartTime = self.sim.now()
        self.intervalEndTime = None

    def startCostingInterval(self, timeNow=None):
        if timeNow is None:
            timeNow = self.sim.now()
        self.intervalStartTime = timeNow
        self.intervalEndTime = None

        # Clear any pending cost events
        for r in self.sim.warehouseWeakRefs:
            wh = r()
            if wh is not None and not isinstance(wh, warehouse.AttachedClinic):
                wh.applyToAll(abstractbaseclasses.Costable, _clearPendingCosts)

    def endCostingInterval(self, timeNow=None):
        pass

    def generateCostRecordInfo(self, reportingHierarchy, timeNow=None):
        return ([], [])

    def generateTripCostNotes(self, truckType, level, conditions,
                              tripJournal, originatingWH, perDiemModel):
        assert isinstance(perDiemModel, DummyPerDiemModel), \
            "Cost model is dummy type but per diem model is not"
        return {}

    def generateUseVialsSessionCostNotes(self, level, conditions):
        return {}

    def generateFactoryDeliveryCostNotes(self, deliveredSC, targetWH):
        return {}

    def getOverrideTotal(self, dct, key):
        return None

    def writeCostRecordsToResultsEntry(self, shdNet, reportingHierarchy,
                                       results, timeNow=None):
        if timeNow is None:
            timeNow = self.sim.now()
        # print reportingHierarchy.getAvailableFieldNames()
        keys, recs = self.generateCostRecordInfo(reportingHierarchy, timeNow)  # @UnusedVariable
        results.addCostSummaryRecs(shdNet, recs)

    def writeCostRecordList(self, fileName, reportingHierarchy, timeNow=None):
        """
        This is a convenience function to generate a record list and write it
        to the given open file in .csv format.
        """
        if timeNow is None:
            timeNow = self.sim.now()
        # print reportingHierarchy.getAvailableFieldNames()
        keys, recs = self.generateCostRecordInfo(reportingHierarchy, timeNow)
        if len(recs) > 0:
            with util.openOutputFile(fileName, "w") as f:
                csv_tools.writeCSV(f, keys, recs, sortColumn="ReportingLevel")

    def realityCheck(self):
        pass

    def getPerDiemModel(self, perDiemName):
        return DummyPerDiemModel()


class DummyCostModelVerifier:
    def __init__(self):
        pass

    def checkReady(self, net):
        return True

    def getProblemList(self, net):
        return []


class DummyPerDiemModel(perdiemmodel.PerDiemModel):
    """
    A do-nothing version of a PerDiemModel
    """
    def __init__(self):
        pass

    def __str__(self):
        return "<DummyPerDiemModel>"

    def calcPerDiemDays(self, tripJournal, homeWH):
        return 0

    def calcPerDiemAmountTriple(self, tripJournal, homeWH):
        return (0.0, u'USD', 2014)
