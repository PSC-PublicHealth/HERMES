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


__doc__=""" statsmodel.py
This module holds classes used in calculating some stats associated with simulations.
"""

_hermes_svn_id_="$Id$"

import sys, os, StringIO, types, unittest
import abstractbaseclasses, warehouse, reportinghierarchy
import csv_tools
import util

class StatsManager:
    tagMethodList= [('_mean',util.HistoVal.mean),
                    ('_stdv',util.HistoVal.stdv),
                    ('_min',util.HistoVal.min),
                    ('_max',util.HistoVal.max),
                    ('_median',util.HistoVal.median),
                    ('_count',util.HistoVal.count),
                    ('_stdv',util.HistoVal.stdv),
                    ('_q1',util.HistoVal.q1),
                    ('_q3',util.HistoVal.q3),
                    ('_raw', util.HistoVal.raw)
                    ]

    def __init__(self, sim, model):
        """
        This class knows how to calculate and output stats information, based on the current Model.
        """
        self.sim = sim
        self.model = model
        self.intervalStartTime = self.sim.now()
        self.intervalEndTime = None
        
    def startStatsInterval(self, timeNow=None):
        """
        Set the start time for time-interval-based stats calculations to the given time.  Note that
        this does not clear statistics from the NoteHolders or ReportingHierarchies used to generate 
        actual reports.
        """
        if timeNow is None: timeNow= self.sim.now()
        self.intervalStartTime = timeNow
        self.intervalEndTime = None
        
    def endStatsInterval(self, timeNow=None):
        """
        End the stats interval and trigger the addition of stats-related notes for this interval to
        all StatProviders.  It is expected that this call will be followed by one or more calls to 
        generateStatsRecordInfo with different ReportingHierarchies, perhaps followed by clearing of
        stats data from the StatProviders, followed by a call to startStatsInterval to begin the 
        cycle again.
        """
        if timeNow is None: timeNow= self.sim.now()
        if self.intervalStartTime is None or self.intervalEndTime is not None:
            raise RuntimeError("Stats interval is not properly bounded")
        self.intervalEndTime = timeNow
        for r in self.sim.warehouseWeakRefs:
            wh= r()
            if wh is not None and not isinstance(wh, warehouse.AttachedClinic):
                nh= wh.getNoteHolder()
                nh.addNote(self.generateWarehouseInventoryStatsNotes(wh, self.intervalStartTime, self.intervalEndTime))
        
    def generateCompleteRetentionRecordInfo(self, reportingHierarchy, timeNow=None):
        """
        Returns a "melted" csv containing of all days_retention records
        """
        if timeNow is None: timeNow = self.sim.now()
        shippableTypeNames = self.sim.vaccines.getActiveTypeNames()
        wanted = ["%s_daysretention"%n for n in shippableTypeNames]
        keys = ['ReportingLevel','ReportingBranch','ReportingIntervalDays','DaysPerYear']
        recs = reportingHierarchy.report(wanted, dictFactory=lambda : util.TagAwareDict(util.HistoVal, StatsManager.tagMethodList))
        idNames = ','.join(sorted(keys))
        yield '%s,type_name,days_retention\n' % (idNames,)
        for rec in recs:
            rec['ReportingIntervalDays'] = self.intervalEndTime - self.intervalStartTime
            rec['DaysPerYear'] = float(self.model.daysPerYear)
            idVals = ','.join([str(rec[k]) for k in sorted(keys)])
            for typeName in shippableTypeNames:
                typeNameKey = typeName+'_daysretention_raw'
                if typeNameKey in rec: 
                    for val in rec[typeNameKey]:
                        yield '%s,%s,%s\n' % (idVals,typeName,str(val))

    def generateStatsRecordInfo(self, reportingHierarchy, timeNow=None):
        """
        Returns a set of statistics for the given reportingHierarchy.  The function returns
        a tuple (keys, recs) in the format used for reading and writing CSV files.
        """
        if timeNow is None: timeNow = self.sim.now()
        shippableTypeNames = self.sim.vaccines.getActiveTypeNames()
        wanted = ["%s_daysretention"%n for n in shippableTypeNames]
        keys = ['ReportingLevel','ReportingBranch','ReportingIntervalDays','DaysPerYear']
        for s1 in wanted:
            keys += ["%s_%s"%(s1,s2) for s2 in ['min', 'max', 'mean', 'median', 'stdv', 'q1', 'q3', 'count']]
        recs = reportingHierarchy.report(wanted, dictFactory=lambda : util.TagAwareDict(util.HistoVal, StatsManager.tagMethodList))
        for rec in recs:
            rec['ReportingIntervalDays'] = self.intervalEndTime - self.intervalStartTime
            rec['DaysPerYear'] = float(self.model.daysPerYear)
        return keys, recs
    
    def writeStatsRecordList(self, fileName, reportingHierarchy, timeNow=None):
        """
        This is a convenience function to generate a record list and write it to the given
        open file in .csv format.
        """
        if timeNow is None: timeNow = self.sim.now()
        #print reportingHierarchy.getAvailableFieldNames()
        keys, recs= self.generateStatsRecordInfo( reportingHierarchy, timeNow )
        with util.openOutputFile(fileName,"w") as f: csv_tools.writeCSV(f, keys, recs, sortColumn="ReportingLevel" )
#        import gzip
#        with gzip.open(fileName + '.complete.retention.records.gz', 'wb') as f:
#            for line in self.generateCompleteRetentionRecordInfo(reportingHierarchy, timeNow):
#                f.write(line)
    
    def generateWarehouseInventoryStatsNotes(self, wh, startTime, endTime ):
        """
        This routine is called once per Warehouse or Clinic instance per reporting interval, and returns a Dict 
        suitable for NoteHoder.addNote() containing stats information associated with that instance over the interval.

        Note that it is probably an error to call this function for an AttachedClinic instance, as AttachedClinics
        have no inventory.
        """
        
        result = {}
        
        for shippableType, histo in wh.getStockIntervalHistograms().items():
            assert isinstance(shippableType, abstractbaseclasses.ShippableType), \
                "Found a stock interval histogram for %s, which is not shippable"%str(shippableType)
            assert isinstance(histo, util.HistoVal), \
                "The stock interval histogram for %s at %s is of the wrong type"%(str(shippableType), wh.name)
            result["%s_daysretention"%shippableType.name] = histo
            
        return result

class DummyStatsManager:
    """
    This class presents the same API as StatsManager, but does nothing.
    """
    def __init__(self):
        pass
    def startStatsInterval(self, timeNow=None):
        pass
    def endStatsInterval(self, timeNow=None):
        pass
    def generateStatsRecordInfo(self, reportingHierarchy, timeNow=None):
        return ([],[])
    def writeStatsRecordList(self, fileName, reportingHierarchy, timeNow=None):
        pass
    
def describeSelf():
    print \
"""
Testing options:

  There are currently no testing options.
"""

def main(myargv = None):
    "Provides a few test routines"
    
    if myargv is None: 
        myargv = sys.argv
    
    if False: # would match test name strings here
        pass
    else:
        describeSelf()

class TestStatsFuncs(unittest.TestCase):
    def getReadBackBuf(self, wordList):
        try:
            sys.stdout = myStdout = StringIO.StringIO()
            main(wordList)
        finally:
            sys.stdout = sys.__stdout__
        return StringIO.StringIO(myStdout.getvalue())
    
    def compareOutputs(self, correctStr, readBack):
        correctRecs = StringIO.StringIO(correctStr)
        for a,b in zip(readBack.readlines(), correctRecs.readlines()):
            if a.strip() != b.strip():
                print "\nExpected: <%s>"%b
                print "Got:      <%s>"%a
            self.assertTrue(a.strip() == b.strip())
    
#    def test_test1(self):
#        correctStr = """This string should contain
#correct results
#        """
#        readBack= self.getReadBackBuf(['dummy','test1'])
#        self.compareOutputs(correctStr, readBack)
        
        
############
# Main hook
############

if __name__=="__main__":
    main()

