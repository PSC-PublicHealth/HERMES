#! /usr/bin/env python

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
