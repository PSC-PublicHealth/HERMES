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

class DummyCostManager:
    """
    This class presents the same API as CostManager, but does nothing.
    """
    def __init__(self):
        pass
    def startCostingInterval(self, timeNow=None):
        pass
    def endCostingInterval(self, timeNow=None):
        pass
    def generateCostRecordInfo(self, reportingHierarchy, timeNow=None):
        return ([],[])
    def generateTripCostNotes(self, truckType, level, conditions, tripJournal, originatingWH):
        return {}
    def generateUseVialsSessionCostNotes(self, level, conditions):
        return {}
    def generateSimpleFridgeCostNotes(self, level, conditions, startTime, endTime, typeName ):
        return {}
    def getLaborTotal(self, dict, key):
        return {}
    def writeCostRecordsToResultsEntry(self, shdNet, reportingHierarchy, results, timeNow=None):
        pass
    def writeCostRecordList(self, fileName, reportingHierarchy, timeNow=None):
        pass
    def realityCheck(self):
        pass
    def checkReady(self, net):
        return True

class DummyCostModelVerifier:
    def __init__(self):
        pass
    def checkReady(self,net):
        return True


