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

__doc__=""" microcostmodel.py
This module holds classes used in calculating costs associated with simulations.
"""

_hermes_svn_id_="$Id$"

import sys, os, StringIO, types, unittest
import ipath
import abstractbaseclasses, warehouse, reportinghierarchy
import csv_tools
import fridgetypes, trucktypes, vaccinetypes
import util
import dummycostmodel
from currencysupport import CurrencyConverter

#: priceKeyTable maps the name keys for fuels to the parameter entry holding their price
priceKeyTable = {'propane':'pricepropaneperkg', 
                 'kerosene':'pricekeroseneperl', 
                 'gasoline':'pricegasolineperl', 
                 'diesel':'pricedieselperl', 
                 'electric':'priceelectricperkwh',
                 'solar':'pricesolarperkw',
                 'ice':'priceiceperliter'
                 }

class MicroCostManager(dummycostmodel.DummyCostManager):
    def __init__(self, sim, model, currencyConverter):
        """
        This class knows how to calculate and output cost information, based on the current Model and
        type-specific base costs.
        """
        self.currencyConverter = currencyConverter
        dummycostmodel.DummyCostManager.__init__(self, sim, model)
        
    def endCostingInterval(self, timeNow=None):
        """
        End the costing interval and trigger the addition of cost-related notes for this interval to
        all StatProviders.  It is expected that this call will be followed by one or more calls to 
        generateCostRecordInfo with different ReportingHierarchies, perhaps followed by clearing of
        costing data from the StatProviders, followed by a call to startCostingInterval to begin the 
        cycle again.
        
        This CostManager should return the following data:
           for Fridges: fuelCost, amortizationCost
           for Trucks: fuelCost, amortizationByKmCost, driverCost, perDiemCost
           for healthposts: staffCost, vaccineCost, buildingCost
           for warehouses: staffCost, buildingCost
        How does it know the right units?
        """
        
        if timeNow is None: timeNow= self.sim.now()
        if self.intervalStartTime is None or self.intervalEndTime is not None:
            raise RuntimeError("Costing interval is not properly bounded")
        self.intervalEndTime = timeNow
        # We do this loop in a try/except to bundle more error messages together, since there is a
        # long annoying process of finding missing price info.
        errList= []
        fridgeAmortPeriod = self.sim.userInput['amortizationstorageyears']*self.model.daysPerYear
        inflation = self.sim.userInput['priceinflation']/self.model.daysPerYear  # ignore compounding to save 
        for r in self.sim.warehouseWeakRefs:
            wh= r()
            if wh is not None and not isinstance(wh, warehouse.AttachedClinic):
                nh= wh.getNoteHolder()
                nh.addNote(self._generateBuildingCostNotes(wh.reportingLevel, wh.conditions,
                                                           self.intervalStartTime, self.intervalEndTime))
                for costable in wh.ownedCostables:
                    if isinstance(costable,abstractbaseclasses.CanStore):
                        #try: 
                            nh.addNote(self._generateFridgeCostNotes(wh.reportingLevel, wh.conditions, 
                                                                     self.intervalStartTime, self.intervalEndTime, 
                                                                     costable.getType(), fridgeAmortPeriod, inflation))
                        #except Exception,e:
                        #    errList.append(str(e))
                    elif isinstance(costable,trucktypes.Truck):
                        for innerItem in costable.getCargo():
                            if isinstance(innerItem,abstractbaseclasses.CanStore):
                                try: 
                                    nh.addNote(self._generateFridgeCostNotes(wh.reportingLevel, wh.conditions, 
                                                                             self.intervalStartTime, self.intervalEndTime, 
                                                                             innerItem.getType(), fridgeAmortPeriod, inflation))
                                except Exception,e:
                                    print e
                                    errList.append(str(e))
                                    raise

                    else:
                        print 'Unexpectedly found %s on %s'%(type(costable),wh.name)
                        raise RuntimeError("Expected only Fridges and Trucks on this list")
        if len(errList)>0:
            print "The following errors were encountered generating costs:"
            for line in errList:
                print "   %s"%line
            raise RuntimeError("Cost calculation failed")
        
    def getLaborTotal(self, dict, key):
        """
        This method is used to provide an override mechanism for LaborCost in the reporting hierarchy.
        """
        val= dict['LaborCost']
        assert dict['ReportingLevel']=='all', 'ReportingHierarchy totalcost override should have level all'
#         try:
#             val = self.priceTable.get("labortotal", "PerYear", level=dict['ReportingBranch'], conditions='normal')
#         except:
#             pass
        val = 0.0
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
#         startWh= originatingWH
#         totKm = 0.0
#         perKmCost= 0.0
#         laborCost= 0.0
#         ### This is to ensure that the condition on the first leg of the trip is used for 
#         ### The per trip costs
#         condFlag = False
#         leg0Conditions = None
#         for tuple in tripJournal:
#             op = tuple[0]
#             if op == "move":
#                 opString,startTime,endTime,legConditions,fromWH,toWH,litersCarried = tuple
#                 if condFlag is False:
#                     leg0Conditions = legConditions
#                     condFlag = True
#                 conditionMultiplier = 1.0
#                 totKm += conditionMultiplier*fromWH.getKmTo(toWH,level,legConditions)
#                 perKmCost += fromWH.getKmTo(toWH,level,legConditions) * self.priceTable.get(truckType.name,"PerKm",
#                                                                                        level=level, conditions=legConditions)
#                 startWh= fromWH
#             else:
#                 startTime = tuple[1]
#                 endTime = tuple[2]
#                 legConditions = tuple[3]
#             laborCost += (endTime-startTime) * self.priceTable.get("driver", "PerYear", level=level, conditions=legConditions)
#         perDiemDays= self.model.calcPerDiemDays(tripJournal,originatingWH)
#         perDiemCost= perDiemDays * (self.priceTable.get("driver", "PerDiem",level=level, conditions=leg0Conditions) +
#                                     self.priceTable.get(truckType.name,"PerDiem",level=level, conditions=leg0Conditions))
#         
#         laborCost /= float(self.model.daysPerYear)
#         perTripCost= self.priceTable.get("driver", "PerTrip", level=level, conditions=leg0Conditions) + \
#                      self.priceTable.get(truckType.name,"PerTrip",level=level, conditions=leg0Conditions)
#                      
#         transportCost= perTripCost + perKmCost + perDiemCost
#         return {"PerDiemDays":perDiemDays,
#                 "PerDiemCost":perDiemCost,
#                 "PerKmCost":perKmCost,
#                 "PerTripCost":perTripCost,
#                 "LaborCost":laborCost,
#                 "TransportCost":transportCost
#                 }
        return {}
        
    def generateUseVialsSessionCostNotes(self, level, conditions):
        """
        This routine is called once per UseVials session, and returns a Dict suitable for NoteHolder.addNote()
        containing cost information appropriate for the session.
        
        level and conditions are used as per their definitions in PriceTable.
        """
#         return {"CostingTreatmentDays":1,
#                 "LaborCost":self.priceTable.get("healthworker","PerTreatmentDay",
#                                                 level=level,conditions=conditions)}
        return {}
        
    def _generateFridgeCostNotes(self, level, conditions, startTime, endTime, costable, amortPeriod, inflation ):
        """
        This routine is called once per Fridge instance per reporting interval, and returns a Dict 
        suitable for NoteHoder.addNote() containing cost information for that instance over the interval.
        A simple linear amortization schedule is assumed.
        """
        assert isinstance(costable,fridgetypes.FridgeType), "expected %s to be a FridgeType"%costable
        fridge = costable
        if fridge.recDict['Name'].startswith('onthefly_'):
            return {} # This is an 'OnTheFly' fridge within a vehicle or warehouse; fridge cost assumed to be subsumed by vehicle cost
        else:
            fCur = fridge.recDict['BaseCostCur']
            fYear = fridge.recDict['BaseCostYear']
            fuel = fridgetypes.energyTranslationDict[fridge.recDict['Energy']][4]
            if fuel in ['ice','solar']:
                print 'I should be handling %s differently'%fridge.name
            fuelPrice = self.sim.userInput[priceKeyTable[fuel]] # in run currency at run base year
            assert fuelPrice is not None, u"Cost information for power type %s is missing"%fuel
            baseCost = fridge.recDict['BaseCost']
            powerRate = fridge.recDict['PowerRate']
            assert baseCost is not None and powerRate is not None, u"Cost information for %s is incomplete"%fridge.name
            runCur = self.sim.userInput['currencybase']
            runCurYear = self.sim.userInput['currencybaseyear']
            rawAmortCost = baseCost*(self.intervalEndTime - self.intervalStartTime)/amortPeriod
            print 'handling %s'%fridge.recDict['Name']
            amortCost = self.currencyConverter.convertTo(rawAmortCost, fCur, runCur, fYear, runCurYear, inflation)
            # This is wrong- fuelPrice and PowerRate are in different units.
            rawFuelCost = powerRate*fuelPrice*(self.intervalEndTime - self.intervalStartTime)
            fuelCost = self.currencyConverter.convertTo(rawFuelCost, fCur, runCur, fYear, runCurYear, inflation)
            return {"m1C_%s"%fuel:fuelCost, "m1C_FridgeAmort":amortCost}

    def _generateBuildingCostNotes(self, level, conditions, startTime, endTime ):
        """
        This routine is called once per Warehouse or Clinic instance per reporting interval, and returns a Dict 
        suitable for NoteHoder.addNote() containing cost information associated with the building or location
        for that instance over the interval.

        Note that it is probably an error to call this function for an AttachedClinic instance, as AttachedClinics
        have no associated building.
        """
#         costPerYear= self.priceTable.get("building","PerYear",level=level,conditions=conditions)
#         return {"BuildingCost":((endTime-startTime)/float(self.model.daysPerYear))*costPerYear}
        return {}
        
    def generateCostRecordInfo(self, reportingHierarchy, timeNow=None):
        """
        Returns a set of cost statistics for the given reportingHierarchy.  The function returns
        a tuple (keys, recs) in the format used for reading and writing CSV files.
        """
        if timeNow is None: timeNow = self.sim.now()
        available = reportingHierarchy.getAvailableFieldNames()
        wanted = [fld for fld in available if fld.startswith('m1C_')]
        keys = ['ReportingLevel','ReportingBranch','ReportingIntervalDays','DaysPerYear','Currency','BaseYear','Type']+wanted
        recs = reportingHierarchy.report(wanted)
        keys += ['Currency','BaseYear']
        for rec in recs:
            rec['Currency'] = self.currencyConverter.getBaseCurrency()
            rec['BaseYear'] = self.currencyConverter.getBaseYear()
            rec['ReportingIntervalDays'] = self.intervalEndTime - self.intervalStartTime
            rec['DaysPerYear'] = float(self.model.daysPerYear)
            rec['Type'] = 'micro1'
        return keys, recs
    
    def realityCheck(self):
        """
        This scans for inappropriate costs entries- but since everything is done from the type records, there is nothing
        to be checked.
        """
        pass

    def writeCostRecordsToResultsEntry(self, shdNet, reportingHierarchy, results, timeNow=None):
        if timeNow is None: timeNow = self.sim.now()
        #print reportingHierarchy.getAvailableFieldNames()
        keys, recs= self.generateCostRecordInfo( reportingHierarchy, timeNow )
        results.addCostSummaryRecs(shdNet, recs)
    

class MicroCostModelVerifier(dummycostmodel.DummyCostModelVerifier):
    def __init__(self, currencyConverter):
        self.currencyConverter = currencyConverter
        dummycostmodel.DummyCostModelVerifier.__init__(self)

    def _verifyFridge(self, invTp):
        try:
            return (invTp.Energy is not None \
                    and (isinstance(invTp.BaseCost,types.FloatType) and invTp.BaseCost>=0.0) \
                    and invTp.BaseCostCurCode is not None \
                    and (isinstance(invTp.BaseCostYear,types.IntType) and invTp.BaseCostYear>=2000) \
                    and (isinstance(invTp.PowerRate,types.FloatType) and invTp.PowerRate>=0.0)) \
                    and (0.0<=self.currencyConverter.convertTo(1.0,invTp.BaseCostCurCode,'USD',invTp.BaseCostYear))
        except:
            return False

    def checkReady(self, net):
        problemList = self.getProblemList(net)
        return (len(problemList)==0)

    def getProblemList(self, net):
        """
        This scans the given ShdNetwork, making sure that all data needed to compute costs for the model
        are defined.
        """
        problemList = []
        
        print '####### beginning checks'
        # Check all the fuel price entries from parms
        for v in priceKeyTable.values()+['priceinflation', 'amortizationstorageyears'] :
            try:
                if not isinstance(net.getParameterValue(v), types.FloatType):
                    problemList.append("%s is not defined or is invalid"%v)
            except:
                problemList.append("%s is not a valid parameter"%v)

        for v in ['currencybaseyear'] :
            try:
                if not isinstance(net.getParameterValue(v), types.IntType):
                    problemList.append("%s is not defined or is invalid"%v)
            except:
                problemList.append("%s is not a valid parameter"%v)
                    
        for v in ['currencybase'] :
            try:
                if not isinstance(net.getParameterValue(v), types.StringTypes):
                    problemList.append("%s is not defined or is invalid"%v)
            except:
                problemList.append("%s is not a valid parameter"%v)
                    
        
        # Check the fridge cost entries
        alreadyChecked = set()
        for storeId,store in net.stores.items():  # @UnusedVariable
            if hasattr(store,'conditions') and store.conditions is not None: 
                conditions = store.conditions
            else: conditions = u'normal'
            
            for shdInv in store.inventory:
                invTp = shdInv.invType
                if invTp.Name in alreadyChecked: continue
                else: alreadyChecked.add(invTp.Name)
                if invTp == 'fridges':
                    if not self._verifyFridge(invTp):
                        problemList.append("Storage type %s has missing costing entries"%invTp.Name)
                elif invTp == 'trucks':
                    truckStorageNames = [b for a,b in util.parseInventoryString(shdInv.invType.Storage)]  # @UnusedVariable
                    for fridge in [net.fridges[nm] for nm in truckStorageNames]:
                        if fridge.Name in alreadyChecked: continue
                        else: alreadyChecked.add(fridge.Name)
                        if not self._verifyFridge(fridge):
                            problemList.append("Storage type %s has missing costing entries"%fridge.Name)

        # For each fridge type, check that we can do currency conversion from costing currency to run
        # currency in the purchase year of the fridge

#         print '####### checked the following types'
#         print alreadyChecked
#         print '####### problemList follows'
#         for s in problemList: print s
#         print '####### end of problemList'
#             
#         for routeId,route in net.routes.items():
#             truckType = route.TruckType
#             if truckType != u'': # attached routes have no truck
#                 print route.RouteName
#                 print route.Type
#                 category = route.supplier().CATEGORY
#                 conditions = route.Conditions
#                 if conditions is None or conditions==u'': conditions = u'normal'
#                 print '%s %s %s'%(truckType,category,conditions)
#                 neededEntries.add((truckType,u'PerKm',category,conditions))
#                 neededEntries.add((truckType,u'PerDiem',category,conditions))
#                 neededEntries.add((truckType,u'PerTrip',category,conditions))
#                 neededEntries.add((u'driver',u'PerYear',category,conditions))
#                 neededEntries.add((u'driver',u'PerDiem',category,conditions))
#                 neededEntries.add((u'driver',u'PerTrip',category,conditions))
        return problemList


def describeSelf():
    print \
"""
Testing options:

  None so far

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
    currencyFile.name = 'notReallyACurrencyFile'
    currencyConverter = CurrencyConverter(currencyFile, 'USD', 2011, 0.0)
    if len(myargv)<2:
        describeSelf()
#     elif myargv[1]=="test1":
#         if len(myargv)==2:
#             testFile= StringIO.StringIO(
# """\
# Name,Conditions,PerDay,Notes
# hello,Hello,thisShouldFail,test1
# """    
#             )
#             testFile.name= "notReallyAFile"
#             print "This test should throw an error because the Currency field is missing."
#             try:
#                 pt= PriceTable(testFile, currencyConverter)
#             except RuntimeError,e:
#                 print "Test threw the error %s"%e
#         else:
#             print "Wrong number of arguments!"
#             describeSelf()
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
    
#     def test_test1(self):
#         correctStr = """This test should throw an error because the Currency field is missing.
# Test threw the error Required column 'Currency' is missing from price table notReallyAFile
#         """
#         readBack= self.getReadBackBuf(['dummy','test1'])
#         self.compareOutputs(correctStr, readBack)
        
        
############
# Main hook
############

if __name__=="__main__":
    main()


