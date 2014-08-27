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

__doc__=""" costmodel.py
This module holds classes used in calculating costs associated with simulations.
"""

_hermes_svn_id_="$Id: costmodel.py 879 2012-03-08 16:47:47Z jleonard $"

import sys, os, StringIO, types, unittest
import abstractbaseclasses, warehouse, reportinghierarchy
import csv_tools
import fridgetypes, trucktypes, vaccinetypes
import util

class CurrencyConverter:
    """
    This class reads a currency conversion table and provides currency conversions.
    """
    def __init__(self, csvFile, currencyBase, currencyBaseYear):
        self.cb= currencyBase
        self.year= int(currencyBaseYear)
        keys,recs= csv_tools.parseCSV(csvFile)
        if currencyBaseYear in keys:
            self.yearKey = currencyBaseYear
        elif str(currencyBaseYear) in keys:
            self.yearKey = str(currencyBaseYear)
        else:
            raise RuntimeError("Requested currency base year %d is not in the currency conversion table"%self.year)
        if 'Currency Code' not in keys:
            raise RuntimeError('The currency table is missing a "Currency Code" column')
        
        for r in recs:
            r['Currency Code'] = r['Currency Code'].strip() # avoids problems with trailing blanks
            
        found = False
        for r in recs:
            if r['Currency Code'] == 'USD' and r[self.yearKey] != '':
                found = True
                if r[self.yearKey] != 1.0:
                    raise RuntimeError("The currency conversion table does not seem to be written in terms of USD")
                break
        if not found:
            raise RuntimeError("Cannot find an entry for USD in the currency conversion table")
        
        baseRecList = [r for r in recs if r['Currency Code']=='USD']
        if len(baseRecList) == 0:
            raise RuntimeError("The currency table record for %s is missing"%self.cb)
        baseFac = None
        for r in baseRecList:
            if type(r[self.yearKey]) == types.FloatType:
                baseFac = r[self.yearKey]
                break
        if baseFac is None:
            raise RuntimeError("Failed to find a valid base currency value for the base year")
        if baseFac <= 0.0:
            raise RuntimeError("Currency table contains a nonsense value for the base currency at base year")
        
        self.table= {}
        for r in recs:
            curCode = r['Currency Code']
            if self.yearKey in r:
                v = r[self.yearKey]
                if v is not None and v is not '' and v > 0.0:
                    self.table[curCode] = baseFac/v
                    
    def _toJSON(self):
        """
        This makes the user interface's life easier.
        """
        return { 
                'currencyBase':self.cb,
                'currencyBaseYear':self.year,
                'table':self.table
                }

        
    def convert(self, curCode, val):
        if curCode in self.table:
            return self.table[curCode] * val
        raise RuntimeError("No conversion factor to take %s to %s"%(curCode,self.cb))
    
    def convertTo(self, curCode, val, newCurCode):
        if curCode in self.table and newCurCode in self.table:
            return (self.table[curCode] * val)/self.table[newCurCode]
        raise RuntimeError("No conversion factor to take %s to %s"%(curCode,newCurCode))
    
    def getBaseCurrency(self):
        return self.cb
    
    def getBaseYear(self):
        return int(self.year)
    
    def __str__(self): 
        return "<CurrencyConverter(%s, %d)>"%(self.cb, self.year)

class PriceTable:
    """
    This class implements a table of the prices of specific actions for specific items.  It is built from
    a CSV file.
    
    Column names in the CSV file are case sensitive.  Values for the following standard keys may be of any type:
    
        Name, Currency, Level, Conditions, Notes
        
    All other values will be cast to floats.  The float-valued standard keys are:
    
        PerKm, PerTrip, PerYear, PerVial, PerDiem, PerTreatmentDay
    """
    requiredList= ["Name", "Currency","PerKm","PerTrip","PerTreatmentDay","PerYear","PerVial","PerDiem"]
    nonFloatList= ["Name","Level", "Conditions","Currency","Notes"]  # Everything else in the table is expected to be a float
    canBeMissingList= ["Notes","Level","Conditions"]

    def __init__(self, priceTableFile, currencyConverter, required=True):
        """
        priceTableFile is an open CSV file containing at least the columns:
        'Name', 'Currency', 'PerKm', 'PerTrip', 'PerTreatmentDay', 'PerYear', 'PerVial', 'PerDiem',
        and optionally 'Notes', 'Level' and/or 'Conditions'.  
        
        The column headings are case sensitive.  If 'required' is True, the
        absence of a value for any column other than 'Notes', 'Level', or 'Conditions' 
        produces a run time error when the corresponding value is requested via the get()
        method.  If 'required' is False, missing values are treated as zero (for
        floating point values) or ''. The absence of a 'Conditions' value is
        equivalent to a conditions value of 'Normal' or 'normal'.  The absence
        of a 'Level' value is equivalent to a level value of 'Any' or 'any'.
        
        By convention, 'Level' is a level in the shipping hierarchy, as specified in the Stores file under
        the keyword CATEGORY.  'Condition' can be any string, for example 'good', 'muddy' or 'overtime'.
        
        As a special case, passing None for priceTableFile will produce an empty PriceTable.
        """
        if priceTableFile is None: 
            # Provide support for simulations for which no costing info is available
            dummyFile= StringIO.StringIO("Name,Currency,PerYear,PerTrip,PerTreatmentDay,PerKm,PerVial,PerDiem,Notes")
            dummyFile.name= fName= "NoSuchFile"
            keys,recs= csv_tools.parseCSV(dummyFile)
            dummyFile.close()
        else:
            keys,recs= csv_tools.parseCSV(priceTableFile)
            try:
                fName= priceTableFile.name
            except:
                fName = "NoFile"
        for rK in PriceTable.requiredList:
            if rK not in keys: raise RuntimeError("Required column '%s' is missing from price table %s"%(rK,fName))
        self.knownItems= {}
        for recDict in recs:
            itemDict= {}
            for k,v in recDict.items():
                if v is None or v == "": continue # blank entry
                if k in PriceTable.nonFloatList: itemDict[k] = v
                else: itemDict[k] = currencyConverter.convert(recDict['Currency'],float(v)) # will raise an error if a non-float quantity is present
            recDict['Currency'] = currencyConverter.getBaseCurrency()
            if "Conditions" not in itemDict or itemDict["Conditions"] in ["","Normal","normal"]:
                itemDict["Conditions"]= None
            if "Level" not in itemDict or itemDict["Level"] in ["","Any","any"]:
                itemDict["Level"]= None
            if "Name" in itemDict:
                lookupKey = (itemDict["Name"],itemDict["Level"],itemDict["Conditions"])
                if lookupKey in self.knownItems:
                    raise RuntimeError("Redundant record for %s with Level %s and Conditions %s"%lookupKey)
                self.knownItems[lookupKey] = itemDict
            else:
                raise RuntimeError("A record in the price table %s lacks a valid Name field"%fName)
        self.required= required
        self.currency= "%s%d"%(currencyConverter.getBaseCurrency(),currencyConverter.getBaseYear())
        
    def items(self):
        """
        This returns the items from the internal dictionary- the keys are (name,level,condition) triples;
        the values are the associated price records after conversion to the base currency.
        """
        return self.knownItems.items()

    def get(self,name,entry,level=None,conditions=None):
        """
        Returns the given entry for the given item name and conditions value.  
        
        The name and entry parameters are expected to be strings; the conditions
        and level parameters must be strings or the value None.  
        
        Item name is case-dependent. entry strings must match those of the CSV
        file used to define the PriceTable, which are subject to the constraints
        described for the __init__ method.  Conditions values of None, "Normal"
        and "normal" are interchangeable, as are level values of None, "Any" and 
        "any".  If a record with "Name", "Level", and "Conditions" exactly
        matching the specified parameters is present, it will be selected.  Failing
        that, if a similar record with "Level" equal to "any" is present, it will
        be selected.  Failing that, if the "Name" and "Level" values match a record
        with "Conditions" "normal", that record will be selected. Failing that, if
        the "Name" matches a record with "Level" "any" and "Conditions" "normal",
        that record will be selected. If the selected record has a column for the
        requested entry and that column is not empty, the value of that column will
        be returned. If no such entry is found a RuntimeError is raised, except in
        the special case where entry is "Notes".  (However, see the description of
        required=False below).
        
        If the PriceTable instance was created with required=True, any
        call for which name, entry and conditions do not match a
        record from the input CSV file will raise a RunTimeError.  If
        required=False was passed to the constructor, missing values
        are treated as zero (for floating point values) or ''.
        
        """
        if level in ["Any", "any"]: level = None
        if conditions in ["Normal", "normal"]: conditions = None
        lookupKey = (name, level, conditions)
        if lookupKey in self.knownItems:
            rec= self.knownItems[lookupKey]
            if entry in rec:
                if entry in PriceTable.nonFloatList: return rec[entry]
                else: return float(rec[entry])
            elif self.required and entry not in PriceTable.canBeMissingList:
                    raise RuntimeError("Cost info %s was requested for %s with level %s and conditions %s; that value was not in the input table"%\
                                       (entry,name,level,conditions))
            else:
                if entry in PriceTable.nonFloatList: return ""
                else: return 0.0
        elif level is not None and (name, None, conditions) in self.knownItems:
            rec= self.knownItems[(name, None, conditions)]
            if entry in rec:
                if entry in PriceTable.nonFloatList: return rec[entry]
                else: return float(rec[entry])
            elif self.required and entry not in PriceTable.canBeMissingList:
                    raise RuntimeError("Cost info %s was requested for %s with level %s and conditions %s; that value was not in the input table"%\
                                       (entry,name,level,conditions))
            else:
                if entry in PriceTable.nonFloatList: return ""
                else: return 0.0
        elif level is not None and conditions is not None and (name, level, None) in self.knownItems:
            rec= self.knownItems[(name, level, None)]
            if entry in rec:
                if entry in PriceTable.nonFloatList: return rec[entry]
                else: return float(rec[entry])
            elif self.required and entry not in PriceTable.canBeMissingList:
                    raise RuntimeError("Cost info %s was requested for %s with level %s and conditions %s; that value was not in the input table"%\
                                       (entry,name,level,conditions))
            else:
                if entry in PriceTable.nonFloatList: return ""
                else: return 0.0
        elif level is not None and conditions is not None and (name, None, None) in self.knownItems:
            rec= self.knownItems[(name, None, None)]
            if entry in rec:
                if entry in PriceTable.nonFloatList: return rec[entry]
                else: return float(rec[entry])
            elif self.required and entry not in PriceTable.canBeMissingList:
                    raise RuntimeError("Cost info %s was requested for %s with level %s and conditions %s; that value was not in the input table"%\
                                       (entry,name,level,conditions))
            else:
                if entry in PriceTable.nonFloatList: return ""
                else: return 0.0
        elif self.required and entry not in PriceTable.canBeMissingList:
            raise RuntimeError("No cost info is available for %s with level %s under conditions %s; that item was not in the input table"%\
                               (name,level,conditions))
        else:
            if entry in PriceTable.nonFloatList: return ""
            else: return 0.0
            
    def getKeys(self):
        return self.knownItems.keys()
    
    def getCurrency(self):
        return self.currency

class CostManager:
    def __init__(self, sim, model, priceTable):
        """
        This class knows how to calculate and output cost information, based on the current Model and
        a PriceTable.
        """
        self.sim = sim
        self.model = model
        self.priceTable = priceTable
        self.intervalStartTime = self.sim.now()
        self.intervalEndTime = None
        
    def startCostingInterval(self, timeNow=None):
        """
        Set the start time for time-interval-based cost calculations to the given time.  Note that
        this does not clear statistics from the NoteHolders or ReportingHierarchies used to generate 
        actual reports.
        """
        if timeNow is None: timeNow= self.sim.now()
        self.intervalStartTime = timeNow
        self.intervalEndTime = None
        
    def endCostingInterval(self, timeNow=None):
        """
        End the costing interval and trigger the addition of cost-related notes for this interval to
        all StatProviders.  It is expected that this call will be followed by one or more calls to 
        generateCostRecordInfo with different ReportingHierarchies, perhaps followed by clearing of
        costing data from the StatProviders, followed by a call to startCostingInterval to begin the 
        cycle again.
        """
        if timeNow is None: timeNow= self.sim.now()
        if self.intervalStartTime is None or self.intervalEndTime is not None:
            raise RuntimeError("Costing interval is not properly bounded")
        self.intervalEndTime = timeNow
        # We do this loop in a try/except to bundle more error messages together, since there is a
        # long annoying process of finding missing price info.
        errList= []
        for r in self.sim.warehouseWeakRefs:
            wh= r()
            if wh is not None and not isinstance(wh, warehouse.AttachedClinic):
                nh= wh.getNoteHolder()
                nh.addNote(self.generateBuildingCostNotes(wh.reportingLevel, wh.conditions,
                                                          self.intervalStartTime, self.intervalEndTime))
                for costable in wh.ownedCostables:
                    if isinstance(costable,abstractbaseclasses.CanStore):
                        try: 
                            nh.addNote(self.generateSimpleFridgeCostNotes(wh.reportingLevel, wh.conditions, 
                                                                          self.intervalStartTime, self.intervalEndTime, 
                                                                          costable.getType().name))
                        except Exception,e:
                            errList.append(str(e))
                    elif isinstance(costable,trucktypes.Truck):
                        for innerItem in costable.getCargo():
                            if isinstance(innerItem,abstractbaseclasses.CanStore):
                                try: 
                                    nh.addNote(self.generateSimpleFridgeCostNotes(wh.reportingLevel, wh.conditions, 
                                                                                  self.intervalStartTime, self.intervalEndTime, 
                                                                                  innerItem.getType().name))
                                except Exception,e:
                                    errList.append(str(e))

                    else:
                        print 'Unexpectedly found %s on %s'%(type(costable),wh.name)
                        raise RuntimeError("Expected only Fridges and Trucks on this list")
        if len(errList)>0:
            print "The following errors were encountered looking up items in the price table:"
            for line in errList:
                print "   %s"%line
            raise RuntimeError("Missing data in price table?")
        
    def getLaborTotal(self, dict, key):
        """
        This method is used to provide an override mechanism for LaborCost in the reporting hierarchy.
        """
        val= dict['LaborCost']
        assert dict['ReportingLevel']=='all', 'ReportingHierarchy totalcost override should have level all'
        try:
            val = self.priceTable.get("labortotal", "PerYear", level=dict['ReportingBranch'], conditions='normal')
        except:
            pass
        return val * (self.intervalEndTime - self.intervalStartTime)/float(self.model.daysPerYear)
        
    def generateTripCostNotes(self, truckType, level, homeConditions, tripJournal, originatingWH):
        """
        This routine is called once per shipping trip, and returns a Dict suitable for NoteHolder.addNote() 
        containing cost information appropriate for the trip.  
        
        truckType is obviously the type of truck used to make the trip; level and homeConditions are used
        as per their definitions in PriceTable.  
        
        tripJournal is a list of tuples describing the steps of the just-completed trip.
        tripJournal entries all start with (stepname, legStartTime, legEndTime, legConditions...);
        see the description of warehouse.createTravelGenerator for additional details.
        legConditions==None is equivalent to legConditions=='normal'.

        originatingWH is used both as the starting point of the trip for travel distance purposes and as the 'home' 
        for the driver for per diem purposes.
        
        PerKm costs are calculated based on the legConditions for each leg traversed; PerDiem and PerTrip costs are 
        based on home conditions.
        """
        startWh= originatingWH
        perKmCost= 0.0
        laborCost= 0.0
        ### This is to ensure that the condition on the first leg of the trip is used for 
        ### The per trip costs
        condFlag = False
        leg0Conditions = None
        for tuple in tripJournal:
            op = tuple[0]
            if op == "move":
                opString,startTime,endTime,legConditions,fromWH,toWH,litersCarried = tuple
                if condFlag is False:
                    leg0Conditions = legConditions
                    condFlag = True
                perKmCost += fromWH.getKmTo(toWH,level,legConditions) * self.priceTable.get(truckType.name,"PerKm",
                                                                                       level=level, conditions=legConditions)
                startWh= fromWH
            else:
                startTime = tuple[1]
                endTime = tuple[2]
                legConditions = tuple[3]
            laborCost += (endTime-startTime) * self.priceTable.get("driver", "PerYear", level=level, conditions=legConditions)
        perDiemDays= self.model.calcPerDiemDays(tripJournal,originatingWH)
        perDiemCost= perDiemDays * (self.priceTable.get("driver", "PerDiem",level=level, conditions=leg0Conditions) +
                                    self.priceTable.get(truckType.name,"PerDiem",level=level, conditions=leg0Conditions))
        
        laborCost /= float(self.model.daysPerYear)
        perTripCost= self.priceTable.get("driver", "PerTrip", level=level, conditions=leg0Conditions) + \
                     self.priceTable.get(truckType.name,"PerTrip",level=level, conditions=leg0Conditions)
                     
        transportCost= perTripCost + perKmCost + perDiemCost
        return {"PerDiemDays":perDiemDays,
                "PerDiemCost":perDiemCost,
                "PerKmCost":perKmCost,
                "PerTripCost":perTripCost,
                "LaborCost":laborCost,
                "TransportCost":transportCost
                }
        
    def generateUseVialsSessionCostNotes(self, level, conditions):
        """
        This routine is called once per UseVials session, and returns a Dict suitable for NoteHolder.addNote()
        containing cost information appropriate for the session.
        
        level and conditions are used as per their definitions in PriceTable.
        """
        return {"CostingTreatmentDays":1,
                "LaborCost":self.priceTable.get("healthworker","PerTreatmentDay",
                                                level=level,conditions=conditions)}
        
    def generateSimpleFridgeCostNotes(self, level, conditions, startTime, endTime, typeName ):
        """
        This routine is called once per Fridge instance per reporting interval, and returns a Dict 
        suitable for NoteHoder.addNote() containing cost information for that instance over the interval.
        A simple linear amortization schedule is assumed.
        """
        costPerYear= self.priceTable.get(typeName,"PerYear",level=level,conditions=conditions)
        return {"StorageCost":((endTime-startTime)/float(self.model.daysPerYear))*costPerYear}

    def generateBuildingCostNotes(self, level, conditions, startTime, endTime ):
        """
        This routine is called once per Warehouse or Clinic instance per reporting interval, and returns a Dict 
        suitable for NoteHoder.addNote() containing cost information associated with the building or location
        for that instance over the interval.

        Note that it is probably an error to call this function for an AttachedClinic instance, as AttachedClinics
        have no associated building.
        """
        costPerYear= self.priceTable.get("building","PerYear",level=level,conditions=conditions)
        return {"BuildingCost":((endTime-startTime)/float(self.model.daysPerYear))*costPerYear}
        
    def generateCostRecordInfo(self, reportingHierarchy, timeNow=None):
        """
        Returns a set of cost statistics for the given reportingHierarchy.  The function returns
        a tuple (keys, recs) in the format used for reading and writing CSV files.
        """
        if timeNow is None: timeNow = self.sim.now()
        wanted= ['Currency','RouteTrips','PerDiemDays','CostingTreatmentDays','PerDiemCost','PerKmCost',
                 'PerTripCost','TransportCost','LaborCost','StorageCost','BuildingCost']
        keys = ['ReportingLevel','ReportingBranch','ReportingIntervalDays','DaysPerYear']+wanted
        recs = reportingHierarchy.report(wanted)
        keys += ['Currency']
        for rec in recs:
            rec['Currency'] = self.priceTable.getCurrency()
            rec['ReportingIntervalDays'] = self.intervalEndTime - self.intervalStartTime
            rec['DaysPerYear'] = float(self.model.daysPerYear)
            rec['Type'] = 'legacy'
#            try:
#                val= self.priceTable.get("labortotal", "PerYear", level=rec['ReportingBranch'], conditions='normal')
#                rec['LaborCost'] = val * (self.intervalEndTime - self.intervalStartTime)/float(self.model.daysPerYear)
#            except RuntimeError:
#                pass
        return keys, recs
    
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
        with util.openOutputFile(fileName,"w") as f: csv_tools.writeCSV(f, keys, recs, sortColumn="ReportingLevel" )
        
    def _checkOneRec(self, keyStr, rec):
        disallowedKeyDict = {'driver':['PerKm', 'PerTreatmentDay', 'PerVial'],
                             'healthworker':['PerKm','PerTrip','PerDiem','PerVial'],
                             'building':['PerKm', 'PerTrip', 'PerTreatmentDay', 'PerDiem', 'PerVial'],
                             'labortotal':['PerKm', 'PerTrip', 'PerTreatmentDay', 'PerDiem', 'PerVial'],
                             'FridgeType':['PerKm', 'PerTrip', 'PerTreatmentDay', 'PerDiem', 'PerVial'],
                             'TruckType':['PerYear', 'PerTreatmentDay', 'PerVial'],
                             'VaccineType':['PerYear','PerKm', 'PerTrip', 'PerTreatmentDay', 'PerDiem'],
                             }

        if keyStr in disallowedKeyDict:
            badFields = [field for field in disallowedKeyDict[keyStr]
                         if field in rec and rec[field] not in [None, '', 0.0]]
            if len(badFields)>0:
                print "***Warning*** For %s at level %s and conditions %s, the following price fields are ignored: %s"%\
                    (rec['Name'], rec['Level'], rec['Conditions'], badFields)
            
        
    def realityCheck(self):
        """
        This scans through the price table and prints hopefully-helpful warning messages
        about inappropriate entries.
        """
        
        recDict= {}
        for k,v in self.priceTable.items():
            name, level, conditions= k
            if name not in recDict: recDict[name] = []
            recDict[name].append(v)
            
        # We can't ask the typeManager to give us the type by name, because that could
        # cause an otherwise inactive type to be activated.
        for t in self.sim.typeManager.getActiveTypes():
            if t.name in recDict:
                for rec in recDict[t.name]: 
                    if isinstance(t,fridgetypes.FridgeType): self._checkOneRec('FridgeType', rec)
                    elif isinstance(t,trucktypes.TruckType): self._checkOneRec('TruckType', rec)
                    elif isinstance(t,vaccinetypes.VaccineType): self._checkOneRec('VaccineType', rec)
                    else:
                        print '***Warning*** There is no costing support for type %s.'%t.name
        
        for specialKey in ['driver', 'healthworker', 'building', 'labortotal']:
            if specialKey in recDict:
                for rec in recDict[specialKey]: self._checkOneRec(specialKey, rec)
        
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
    
def describeSelf():
    print \
"""
Testing options:

  The following tests operate on PriceTable:

  test1
  test2
  test3
  test4
  test5
  test6
  test7
  test8
  test9

     Perform simple tests using iternal data
     
  testfile csvFileName item entry [conditions [level]]
  
     Load the named CSV file and print the value of 'entry' for item 'item'

"""

def main(myargv = None):
    "Provides a few test routines"
    
    if myargv is None: 
        myargv = sys.argv
    
    # Remember, valid CSV input must have column headers on line zero.
    # Create a small but adequate CurrencyTable
    currencyFile = StringIO.StringIO(
"""\
"Country Name","Currency Name","Currency Code","2002","2003","2004","2005","2006","2007","2008","2009","2010","2011","Notes"
"Thailand","baht","THB",42.960000000000001,41.479999999999997,40.219999999999999,40.219999999999999,37.880000000000003,34.520000000000003,33.310000000000002,34.289999999999999,31.690000000000001,30.489999999999998,""
"United States","us dollar","USD",1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,""
"""
                                     )
    currencyConverter = CurrencyConverter(currencyFile, 'USD', 2011)
    if len(myargv)<2:
        describeSelf()
    elif myargv[1]=="test1":
        if len(myargv)==2:
            testFile= StringIO.StringIO(
"""\
Name,Conditions,PerDay,Notes
hello,Hello,thisShouldFail,test1
"""    
            )
            testFile.name= "notReallyAFile"
            print "This test should throw an error because the Currency field is missing."
            try:
                pt= PriceTable(testFile, currencyConverter)
            except RuntimeError,e:
                print "Test threw the error %s"%e
    elif myargv[1]=="test2":
        if len(myargv)==2:
            testFile= StringIO.StringIO(
"""\
Name,Currency,PerYear,PerTrip,PerTreatmentDay,PerKm,PerVial,PerDiem,Notes
hello,USD,thisShouldFail,12.34,1.23,3.12,,,test2
"""    
            )
            testFile.name= "notReallyAFile"
            print "This test should throw an error because PerYear is not a float."
            try:
                pt= PriceTable(testFile, currencyConverter)
            except Exception,e:
                print "Test threw the error: %s"%e
    elif myargv[1]=="test3":
        if len(myargv)==2:
            testFile= StringIO.StringIO(
"""\
Name,Currency,PerYear,PerTrip,PerTreatmentDay,PerKm,PerVial,PerDiem,Notes
hello,USD,56.78,12.34,1.23,3.12,,4.5,test3
"""    
            )
            testFile.name= "notReallyAFile"
            print "This test should throw an error because PerVial is not available."
            try:
                pt= PriceTable(testFile, currencyConverter)
                print pt.get('hello','PerVial')
            except Exception,e:
                print "Test threw the error: %s"%e
    elif myargv[1]=="test4":
        if len(myargv)==2:
            testFile= StringIO.StringIO(
"""\
Name,Currency,PerYear,PerTrip,PerTreatmentDay,PerKm,PerVial,PerDiem,Notes
hello,USD,56.78,12.34,1.23,3.12,1.7,4.5,test2
"""    
            )
            testFile.name= "notReallyAFile"
            print "This test should throw an error because Hello (uppercase) is not a known item."
            try:
                pt= PriceTable(testFile, currencyConverter)
                print pt.get('Hello','perday')
            except Exception,e:
                print "Test threw the error: %s"%e
    elif myargv[1]=="test5":
        if len(myargv)==2:
            testFile= StringIO.StringIO(
"""\
Name,Currency,PerYear,PerTrip,PerTreatmentDay,PerKm,PerVial,PerDiem,Notes
hello,USD,56.78,12.34,1.23,3.12,,,test2
Hello,THB,117,43,3.12,,,,"Test record for Hello"
"""    
            )
            testFile.name= "notReallyAFile"
            print "This test should produce several values."
            pt= PriceTable(testFile, currencyConverter)
            print pt.get('Hello','Notes')
            print pt.get('hello','Notes')
            print pt.get('Hello','Currency')
            print pt.get('Hello','PerYear')
        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="test6":
        if len(myargv)==2:
            testFile= StringIO.StringIO(
"""\
Name,Currency,PerYear,PerTrip,PerTreatmentDay,PerKm,PerVial,PerDiem,Conditions,Notes
hello,USD,56.78,12.34,1.23,3.12,,,,"Notes for hello"
Hello,THB,117,43,1.23,3.12,,,poor,"Test record for Hello poor"
Hello,THB,117,43,1.23,3.12,,,normal,"Test record for Hello normal"
Hello,THB,117,43,1.23,3.12,,,good,"Test record for Hello good"
"""    
            )
            testFile.name= "notReallyAFile"
            print "This test should produce several values."
            pt= PriceTable(testFile, currencyConverter)
            print pt.get('Hello','Notes')
            print pt.get('hello','Notes')
            print pt.get('Hello','Notes',conditions="poor")
            print pt.get('Hello','Notes',conditions="normal")
            print pt.get('Hello','Notes',conditions="Normal")
            print "An empty string should follow because Notes is not required"
            print pt.get('Hello','Notes',conditions="muddy")
            try:
                print pt.get('Hello','PerDiem',conditions="muddy")
            except Exception,e:
                print "Tried to get 'Hello','PerDiem',conditions='muddy' and got expected error '%s'"%e
            print pt.get('Hello','Currency')
            print pt.get('Hello','PerYear')
    elif myargv[1]=="test7":
        if len(myargv)==2:
            testFile= StringIO.StringIO(
"""\
Name,Currency,PerYear,PerTrip,PerTreatmentDay,PerKm,PerVial,PerDiem,Level,Notes
hello,USD,56.78,12.34,1.23,3.12,,,,"Notes for hello"
Hello,THB,117,43,1.23,3.12,,,Central,"Test record for Hello Central"
Hello,THB,117,43,1.23,3.12,,,District,"Test record for Hello District"
Hello,THB,117,43,1.23,3.12,,,IHC,"Test record for Hello IHC"
"""    
            )
            testFile.name= "notReallyAFile"
            print "This test should produce several values."
            pt= PriceTable(testFile, currencyConverter)
            print pt.get('Hello','Notes')
            print pt.get('hello','Notes')
            print pt.get('Hello','Notes',level="Central")
            print pt.get('Hello','Notes',level="District")
            print pt.get('Hello','Notes',level="IHC")
            print "An empty string should follow because Notes is not required"
            print pt.get('Hello','Notes',level="Regional")
            try:
                print pt.get('Hello','PerDiem',level="Regional")
            except Exception,e:
                print "Tried to get 'Hello','PerDiem',level='Regional' and got expected error '%s'"%e
            print pt.get('hello','Currency')
            print pt.get('hello','PerYear')
        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="test8":
        if len(myargv)==2:
            testFile= StringIO.StringIO(
"""\
Name,Currency,PerYear,PerTrip,PerTreatmentDay,PerKm,PerVial,PerDiem,Level,Conditions,Notes
hello,USD,56.78,12.34,1.23,3.12,,,,,"Notes for hello any normal"
Hello,THB,117,43,1.23,3.12,,,Central,poor,"Test record for Hello Central poor"
Hello,THB,117,43,1.23,3.12,,,IHC,poor,"Test record for Hello IHC poor"
Hello,THB,117,43,1.23,3.12,,,Central,normal,"Test record for Hello Central normal"
Hello,THB,117,43,1.23,3.12,,,IHC,,"Test record for Hello IHC normal"
Hello,THB,117,43,1.23,3.12,,1.56,IHC,good,"Test record for Hello IHC good"
Hello,THB,117,43,1.23,3.12,,,any,good,"Test record for Hello any good"
"""    
            )
            testFile.name= "notReallyAFile"
            print "This test should produce several values."
            pt= PriceTable(testFile, currencyConverter)
            print pt.get('hello','Notes')
            print "A blank line should follow" # since Notes is not required
            print pt.get('Hello','Notes')
            print pt.get('Hello','Notes',conditions="good")
            print pt.get('Hello','Notes',level="IHC",conditions="normal")
            print "A blank line should follow" # since Notes is not required
            print pt.get('hello','Notes',level="Regional")
            try:
                print pt.get('Hello','PerDiem',level="IHC",conditions="muddy")
            except Exception,e:
                print "Tried to get 'Hello','PerDiem', 'IHC', 'muddy' and got expected error '%s'"%e
            print pt.get('Hello','PerDiem',level="IHC",conditions="good")
            print pt.get('hello','Currency',level=None,conditions=None)
        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="test9":
        if len(myargv)==2:
            print "Trying to create a default empty PriceTable"
            pt= PriceTable(None,currencyConverter)
            print "That worked"
        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="testfile":
        if len(myargv) in [5,6,7]:
            with open(myargv[2],'rU') as f:
                pt = PriceTable(f)
            if len(myargv) == 5:
                print pt.get(myargv[3],myargv[4])
            elif len(myargv) == 6:
                print pt.get(myargv[3],myargv[4],conditions=myargv[5])
            elif len(myargv) == 7:
                print pt.get(myargv[3],myargv[4],conditions=myargv[5],level=myargv[6])
        else:
            print "Wrong number of arguments!"
            describeSelf()
    else:
        describeSelf()

class TestCostFuncs(unittest.TestCase):
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
    
    def test_test1(self):
        correctStr = """This test should throw an error because the Currency field is missing.
Test threw the error Required column 'Currency' is missing from price table notReallyAFile
        """
        readBack= self.getReadBackBuf(['dummy','test1'])
        self.compareOutputs(correctStr, readBack)
        
    def test_test2(self):
        correctStr = """This test should throw an error because PerYear is not a float.
Test threw the error: could not convert string to float: thisShouldFail
        """
        readBack= self.getReadBackBuf(['dummy','test2'])
        self.compareOutputs(correctStr, readBack)
        
    def test_test3(self):
        correctStr = """This test should throw an error because PerVial is not available.
Test threw the error: Cost info PerVial was requested for hello with level None and conditions None; that value was not in the input table
        """
        readBack= self.getReadBackBuf(['dummy','test3'])
        self.compareOutputs(correctStr, readBack)
        
    def test_test4(self):
        correctStr = """This test should throw an error because Hello (uppercase) is not a known item.
Test threw the error: No cost info is available for Hello with level None under conditions None; that item was not in the input table
        """
        readBack= self.getReadBackBuf(['dummy','test4'])
        self.compareOutputs(correctStr, readBack)
        
    def test_test5(self):
        correctStr = """This test should produce several values.
"Test record for Hello"
test2
THB
3.83732371269
        """
        readBack= self.getReadBackBuf(['dummy','test5'])
        self.compareOutputs(correctStr, readBack)
        
    def test_test6(self):
        correctStr = """This test should produce several values.
"Test record for Hello normal"
"Notes for hello"
"Test record for Hello poor"
"Test record for Hello normal"
"Test record for Hello normal"
An empty string should follow because Notes is not required

Tried to get 'Hello','PerDiem',conditions='muddy' and got expected error 'No cost info is available for Hello with level None under conditions muddy; that item was not in the input table'
THB
3.83732371269
        """
        readBack= self.getReadBackBuf(['dummy','test6'])
        self.compareOutputs(correctStr, readBack)
        
    def test_test7(self):
        correctStr = """This test should produce several values.

"Notes for hello"
"Test record for Hello Central"
"Test record for Hello District"
"Test record for Hello IHC"
An empty string should follow because Notes is not required

Tried to get 'Hello','PerDiem',level='Regional' and got expected error 'No cost info is available for Hello with level Regional under conditions None; that item was not in the input table'
USD
56.78
        """
        readBack= self.getReadBackBuf(['dummy','test7'])
        self.compareOutputs(correctStr, readBack)
        
    def test_test8(self):
        correctStr = """This test should produce several values.
"Notes for hello any normal"
A blank line should follow

"Test record for Hello any good"
"Test record for Hello IHC normal"
A blank line should follow
"Notes for hello any normal"
Tried to get 'Hello','PerDiem', 'IHC', 'muddy' and got expected error 'Cost info PerDiem was requested for Hello with level IHC and conditions muddy; that value was not in the input table'
0.0511643161692
USD
        """
        readBack= self.getReadBackBuf(['dummy','test8'])
        self.compareOutputs(correctStr, readBack)
        
    def test_test9(self):
        correctStr = """Trying to create a default empty PriceTable
That worked
        """
        readBack= self.getReadBackBuf(['dummy','test9'])
        self.compareOutputs(correctStr, readBack)
        
############
# Main hook
############

if __name__=="__main__":
    main()

