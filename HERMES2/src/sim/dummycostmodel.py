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

__doc__=""" dummycostmodel.py
This module holds classes used in calculating costs associated with simulations.
"""

_hermes_svn_id_="$Id$"

import util,csv_tools

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
        if timeNow is None: timeNow= self.sim.now()
        self.intervalStartTime = timeNow
        self.intervalEndTime = None

    def endCostingInterval(self, timeNow=None):
        pass
    
    def generateCostRecordInfo(self, reportingHierarchy, timeNow=None):
        return ([],[])
    def generateTripCostNotes(self, truckType, level, conditions, tripJournal, originatingWH):
        return {}
    def generateUseVialsSessionCostNotes(self, level, conditions):
        return {}
    def getLaborTotal(self, dict, key):
        return {}
    def writeCostRecordsToResultsEntry(self, shdNet, reportingHierarchy, results, timeNow=None):
        if timeNow is None: timeNow = self.sim.now()
        #print reportingHierarchy.getAvailableFieldNames()
        keys, recs= self.generateCostRecordInfo( reportingHierarchy, timeNow )
        results.addCostSummaryRecs(shdNet, recs)
    
    def writeCostRecordList(self, fileName, reportingHierarchy, timeNow=None):
        """
        This is a convenience function to generate a record list and write it to the given
        open file in .csv format.
        """
        if timeNow is None: timeNow = self.sim.now()
        #print reportingHierarchy.getAvailableFieldNames()
        keys, recs= self.generateCostRecordInfo( reportingHierarchy, timeNow )
        if len(recs) > 0:
            with util.openOutputFile(fileName,"w") as f: csv_tools.writeCSV(f, keys, recs, sortColumn="ReportingLevel" )

    def realityCheck(self):
        pass
    def checkReady(self, net):
        return True

class DummyCostModelVerifier:
    def __init__(self):
        pass
    def checkReady(self,net):
        return True


