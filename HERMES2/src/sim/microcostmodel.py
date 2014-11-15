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
import fridgetypes, trucktypes, vaccinetypes, stafftypes
import util
import dummycostmodel
from currencysupport import CurrencyConverter

#: priceKeyTable maps the name keys for fuels to the parameter entry holding their price
priceKeyTable = {'propane':'pricepropaneperkg', 
                 'kerosene':'pricekeroseneperl', 
                 'gasoline':'pricegasolineperl', 
                 'diesel':'pricedieselperl', 
                 'electric':'priceelectricperkwh',
                 'solar':('pricesolarperkw','solarpanellifetimeyears'),
                 'ice':'priceiceperliter',
                 'free':None
                 }

class MicroCostManager(dummycostmodel.DummyCostManager):
    @staticmethod
    def _getPendingCostEvents(costable):
        l = costable.getPendingCostEvents()
        # No danger of double-counting with this recursion because _getPendingCostEvents clears the list
        if isinstance(costable, abstractbaseclasses.CanOwn):
            l.extend( costable.applyToAll(abstractbaseclasses.Costable, MicroCostManager._getPendingCostEvents) )
        return l
    
    @staticmethod
    def _getInventory(costable):
        return [(costable.getType().name, 'inventory', costable.getCount())]
    
    def _getFullInventory(self):
        """
        Returns a dict of item counts by type name and a set containing error messages (hopefully empty)
        """
        # Traverse the network, collecting inventory information
        inventoryList = []
        errSet = set()
        for r in self.sim.warehouseWeakRefs:
            wh= r()
            if wh is not None:
                try:
                    newInventory= wh.applyToAll(abstractbaseclasses.Costable, MicroCostManager._getInventory,
                                                negFilterClass=trucktypes.Truck)
                    for t in [tt for tt in wh.ownedCostables if isinstance(tt, trucktypes.Truck)]:
                        newInventory.extend(t.applyToAll(abstractbaseclasses.Costable, MicroCostManager._getInventory))
                except Exception,e:
                    errSet.add(unicode(e))
                inventoryList.extend(newInventory)

        if len(errSet) > 0:
            util.logError("The following errors were found during inventory-taking for costing")
            for s in list(errSet):
                util.logError(s);
            raise RuntimeError("Exiting due to errors during inventory-taking")

        invDict = {}
        for l in inventoryList:
            for name,key,count in [tpl[:3] for tpl in l]:
                assert key=='inventory', 'internal error scanning inventory'
                if name in invDict: invDict[name] += count
                else: invDict[name] = count
        return invDict
        
    def _calcInventoryCost(self, pairList):
        tot = 0.0
        errList = []
        runCur = self.sim.userInput['currencybase']
        runCurYear = self.sim.userInput['currencybaseyear']
        inflation = self.sim.userInput['priceinflation'] # currency converter wants per-year inflation
        for tpName,cnt in pairList:
            try:
                tp = self.sim.typeManager.getTypeByName(tpName)
                if isinstance(tp, vaccinetypes.VaccineType):
                    baseCost = tp.recDict['Vaccine price/vial']
                    baseCostCurCode = tp.recDict['Price Units']
                    baseCostYear = tp.recDict['Price Year']
                elif isinstance(tp, fridgetypes.FridgeType) or isinstance(tp, trucktypes.TruckType):
                    baseCost = tp.recDict['BaseCost']
                    baseCostCurCode = tp.recDict['BaseCostCur']
                    baseCostYear = tp.recDict['BaseCostYear']
                else:
                    raise RuntimeError("Inventory of %s changed - what is this type?"%tpName)
                unitCost = self.currencyConverter.convertTo(baseCost, baseCostCurCode, runCur, baseCostYear, runCurYear, inflation)
                tot += cnt*unitCost
            except Exception,e:
                errList.append(unicode(e))
        return tot, errList
    
    def __init__(self, sim, model, currencyConverter):
        """
        This class knows how to calculate and output cost information, based on the current Model and
        type-specific base costs.
        """
        self.currencyConverter = currencyConverter
        self.startingInventoryDict = None
        self.inventoryChangeCost = None
        dummycostmodel.DummyCostManager.__init__(self, sim, model)
    
    def startCostingInterval(self, timeNow=None):
        dummycostmodel.DummyCostManager.startCostingInterval(self, timeNow) # Do the default stuff
        invDict = self._getFullInventory()
        self.startingInventoryDict = invDict
        
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
        
        errList= []

        if self.startingInventoryDict is None:
            raise RuntimeError("Inventory from interval start is missing")
        invDict = self._getFullInventory()
        invChanges = []
        for k in set(invDict.keys()+self.startingInventoryDict.keys()):
            startingCount = self.startingInventoryDict[k] if k in self.startingInventoryDict else 0
            endingCount =  invDict[k] if k in invDict else 0
            if startingCount != endingCount:
                invChanges.append((k,endingCount-startingCount))
        #print 'list of inventory changes: %s'%invChanges
        self.inventoryChangeCost,newErrList = self._calcInventoryCost(invChanges)
        self.startingInventoryDict = None
        errList.extend(newErrList)

        if timeNow is None: timeNow= self.sim.now()
        if self.intervalStartTime is None or self.intervalEndTime is not None:
            raise RuntimeError("Costing interval is not properly bounded")
        self.intervalEndTime = timeNow
        # We do this loop in a try/except to bundle more error messages together, since there is a
        # long annoying process of finding missing price info.
        fridgeAmortPeriod = self.sim.userInput['amortizationstorageyears']*self.model.daysPerYear
        inflation = self.sim.userInput['priceinflation'] # ultimately used by currencyConverter, so per-year
        allPendingCostEvents = []
        for r in self.sim.warehouseWeakRefs:
            wh= r()
            if wh is not None and not isinstance(wh, warehouse.AttachedClinic):
                nh= wh.getNoteHolder()
                nh.addNote(self._generateBuildingCostNotes(wh.reportingLevel, wh.conditions,
                                                           self.intervalStartTime, self.intervalEndTime))
                for costable in wh.ownedCostables:
                    if isinstance(costable,abstractbaseclasses.CanStore):
                        try: 
                            nh.addNote(self._generateFridgeCostNotes(wh.reportingLevel, wh.conditions, 
                                                                     self.intervalStartTime, self.intervalEndTime, 
                                                                     costable.getType(), fridgeAmortPeriod, inflation))
                        except Exception,e:
                            errList.append(unicode(e))
                    elif isinstance(costable,trucktypes.Truck):
                        for innerItem in costable.getCargo():
                            if isinstance(innerItem,abstractbaseclasses.CanStore):
                                try: 
                                    nh.addNote(self._generateFridgeCostNotes(wh.reportingLevel, wh.conditions, 
                                                                             self.intervalStartTime, self.intervalEndTime, 
                                                                             innerItem.getType(), fridgeAmortPeriod, inflation))
                                except Exception,e:
                                    errList.append(str(e))
                    elif isinstance(costable, stafftypes.Staff):
                        pass
                    else:
                        print 'Unexpectedly found %s on %s'%(type(costable),wh.name)
                        raise RuntimeError("Expected only Fridges, Trucks, or Staff on this list")
                # No danger of double counting because getPendingCostEvents clears the list of events
                allPendingCostEvents.extend( wh.applyToAll(abstractbaseclasses.Costable, MicroCostManager._getPendingCostEvents))
                for costable in wh.ownedCostables:
                    if isinstance(costable, abstractbaseclasses.CanOwn):
                        allPendingCostEvents.extend( costable.applyToAll(abstractbaseclasses.Costable, 
                                                                         MicroCostManager._getPendingCostEvents))
        #print 'allPendingCostEvents from scan: %s'%allPendingCostEvents
        if len(errList)>0:
            util.logError("The following errors were encountered generating costs:")
            for line in errList:
                util.logError("   %s"%line)
            raise RuntimeError("Cost calculation failed")
        
    def getOverrideTotal(self, dict, key):
        """
        This method is used to provide an override mechanism for LaborCost in the reporting hierarchy.
        """
        if key=='InventoryChangeCost':
            assert dict['ReportingLevel']=='-top-', 'ReportingHierarchy InventoryChangeCost override should have level all'
            if dict['ReportingBranch']=='all':
                return 'm1C_'+key,self.inventoryChangeCost
            else:
                return None
        elif key=='LaborCost':
            assert dict['ReportingLevel']=='all', 'ReportingHierarchy LaborCost override should have level all'
            val= dict['LaborCost']
    #         try:
    #             val = self.priceTable.get("labortotal", "PerYear", level=dict['ReportingBranch'], conditions='normal')
    #         except:
    #             pass
            val = 0.0
            return val * (self.intervalEndTime - self.intervalStartTime)/float(self.model.daysPerYear)
        else:
            return None
        
    def generateFactoryDeliveryCostNotes(self, deliveredSC, targetWH):
        """
        This routine is called once per factory delivery, and returns a Dict suitable for NoteHolder.addNote()
        containing cost information appropriate for the delivery.
        """
        errList = []
        vaxCost,newErrList = self._calcInventoryCost([(v.name,n) for v,n in deliveredSC.items() 
                                                        if isinstance(v,vaccinetypes.VaccineType)])
        errList.extend(newErrList)
        fridgeCost,newErrList = self._calcInventoryCost([(v.name,n) for v,n in deliveredSC.items() 
                                                        if isinstance(v,fridgetypes.FridgeType)])
        errList.extend(newErrList)
        truckCost,newErrList = self._calcInventoryCost([(v.name,n) for v,n in deliveredSC.items() 
                                                        if isinstance(v,trucktypes.TruckType)])
        if len(errList)!= 0:
            util.logError("The following errors were encountered generating costs:")
            for line in errList:
                util.logError("   %s"%line)
            raise RuntimeError("Cost calculation failed")            

        return {'m1C_Vaccines':vaxCost, 'm1C_Storage':fridgeCost,'m1C_Transport':truckCost}
    
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
        totKm = 0.0
        perKmCost= 0.0
        laborCost= 0.0
        ### This is to ensure that the condition on the first leg of the trip is used for 
        ### The per trip costs
        condFlag = False
        leg0Conditions = None
        allPendingCostEvents = []
        for tuple in tripJournal:
            op = tuple[0]
            if op == "move":
                legConditions = tuple[3]
                fromWH = tuple[4]
                toWH = tuple[5]
                if condFlag is False:
                    leg0Conditions = legConditions
                    condFlag = True
                conditionMultiplier = 1.0
                totKm += conditionMultiplier*fromWH.getKmTo(toWH,level,legConditions)
#                 perKmCost += fromWH.getKmTo(toWH,level,legConditions) * self.priceTable.get(truckType.name,"PerKm",
#                                                                                        level=level, conditions=legConditions)
            else:
                startTime = tuple[1]
                endTime = tuple[2]
                legConditions = tuple[3]
            miscCosts = tuple[-1]
            allPendingCostEvents.extend(miscCosts)
            
        errList = []
        result = {}
        
        #  Costs associated with the truck
        tCur = truckType.recDict['BaseCostCur']
        tYear = truckType.recDict['BaseCostYear']
        fuel = trucktypes.fuelTranslationDict[truckType.recDict['Fuel']][4]
        costPattern = trucktypes.fuelTranslationDict[truckType.recDict['Fuel']][5]
        runCur = self.sim.userInput['currencybase']
        runCurYear = self.sim.userInput['currencybaseyear']
        inflation = self.sim.userInput['priceinflation'] # currencyConverter wants per-year inflation
        if costPattern == 'distance':
            priceKeyInfo = priceKeyTable[fuel]
            if priceKeyInfo is not None and self.sim.userInput[priceKeyInfo] != 0.0:
                assert isinstance(priceKeyInfo, types.StringTypes), u"fuel type for %s should not have amortization"%truckType.name
                fuelPrice = self.sim.userInput[priceKeyInfo] # in run currency at run base year
                assert fuelPrice is not None, u"Cost information for fuel type %s is missing"%fuel
                fuelRate = truckType.recDict['FuelRate']
                assert fuelRate is not None, u"Cost information for %s is incomplete"%truckType.name
                #
                # fuel cost is totKm/fuelRate, since fuelRate is an inverse, like Km/liter.  The price of fuel
                # is already given in the run currency at the run year, so no currency conversion is needed.
                #
                fuelCost = (totKm/fuelRate)*fuelPrice
                fare = 0.0
            else:
                # Fuel is free
                fuelCost = 0.0
                fare = 0.0
        elif costPattern == 'pertrip':
            rawFare = truckType.recDict['FuelRate']
            fare = self.currencyConverter.convertTo(rawFare, tCur, runCur, tYear, runCurYear, inflation)
            fuelCost = 0.0
        else:
            raise RuntimeError(u'Transport type %s as an unexpected costing pattern'%truckType.name)
        baseCost = truckType.recDict['BaseCost']
        assert baseCost is not None, u"Cost information for %s is incomplete"%truckType.name
        amortKm = truckType.recDict['AmortizationKm']
        if baseCost != 0.0:
            rawAmortCost = baseCost*totKm/amortKm
            amortCost = self.currencyConverter.convertTo(rawAmortCost, tCur, runCur, tYear, runCurYear, inflation)
        else:
            amortCost = 0.0
        for k,v in [("m1C_%s"%fuel, fuelCost), ("m1C_TruckAmort",amortCost),("m1C_TransitFareCost",fare)]:
            if v != 0.0:
                if k in result: result[k] += v
                else: result[k] = v
        
        #  Add in the miscellaneous costs
        miscCostDict = {}
        for tpl in allPendingCostEvents:
            tpName,evtStr,count = tpl[0:3]
            key = (tpName,evtStr)
            if key in miscCostDict:
                miscCostDict[key] += count
            else:
                miscCostDict[key] = count
        
        for innerFridge,n in truckType.getFridgeCollection().items():
            assert isinstance(innerFridge, fridgetypes.FridgeType), "Expected only Fridges in this category"
            if innerFridge.name.startswith(u'onthefly_'):
                continue
            energyInfo = fridgetypes.energyTranslationDict[innerFridge.recDict['Energy']] # a long tuple
            costPattern = energyInfo[5]
            if costPattern == 'charge':
                # We will assume all ice fridges associated with the truck are charged once per trip
                key = (innerFridge.recDict['Name'],'recharge')
                if key in miscCostDict.items():
                    miscCostDict[key] += n
                else:
                    miscCostDict[key] = n
            else:
                pass
            
        # Now generate costs for all the events identified
        for k,n in miscCostDict.items():
            tpName,evtStr = k
            tp = self.sim.typeManager.getTypeByName(tpName)
            if isinstance(tp, fridgetypes.FridgeType):
                energyInfo = fridgetypes.energyTranslationDict[tp.recDict['Energy']] # a long tuple
                costPattern = energyInfo[5]
                if evtStr=='recharge':
                    if costPattern == 'charge':
                        # We will assume all ice fridges associated with the truck are charged once per trip
                        try:
                            fuel = energyInfo[4]
                            priceKeyInfo = priceKeyTable[fuel]
                            powerRate = tp.recDict['PowerRate']
                            assert powerRate is not None, u"Cost information for %s is incomplete"%tp.name
                            runCur = self.sim.userInput['currencybase']
                            runCurYear = self.sim.userInput['currencybaseyear']
                            fuelPrice = self.sim.userInput[priceKeyInfo] # in run currency at run base year
                            assert not isinstance(fuelPrice,types.TupleType), "Ice should not have an amortization rate"
                            #
                            # fuel cost is just powerRat*fuelPrice, since this is per-trip and not time-dependent.  The price of fuel
                            # is already given in the run currency at the run year, so no currency conversion is needed.
                            #
                            fuelCost = powerRate*fuelPrice # one charge for this trip
                            valKey = "m1C_%s"%fuel
                            fuelCost *= n
                            if valKey in result: result[valKey] += fuelCost
                            else: result[valKey] = fuelCost
                        except Exception,e:
                            errList.append(unicode(e))
                else:
                    errList.append("Unhandled cost event %s for type %s (%d instances)"%(tpName,evtStr,count))
            else:
                errList.append("Unhandled cost event %s for type %s (%d instances)"%(tpName,evtStr,count))

        if len(errList)>0:
            util.logError("The following errors were encountered generating trip costs:")
            for line in errList:
                util.logError( "   %s"%line)
            raise RuntimeError("Trip Cost calculation failed")
            
#             laborCost += (endTime-startTime) * self.priceTable.get("driver", "PerYear", level=level, conditions=legConditions)
#         perDiemDays= self.model.calcPerDiemDays(tripJournal,originatingWH)
#         perDiemCost= perDiemDays * (self.priceTable.get("driver", "PerDiem",level=level, conditions=leg0Conditions) +
#                                     self.priceTable.get(truckType.name,"PerDiem",level=level, conditions=leg0Conditions))
         
#         laborCost /= float(self.model.daysPerYear)
#         perTripCost= self.priceTable.get("driver", "PerTrip", level=level, conditions=leg0Conditions) + \
#                      self.priceTable.get(truckType.name,"PerTrip",level=level, conditions=leg0Conditions)
                      
        return result
        
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
            costPattern = fridgetypes.energyTranslationDict[fridge.recDict['Energy']][5]
            priceKeyInfo = priceKeyTable[fuel]
            if costPattern == 'charge':
                fuelPrice = 0.0 # handled elsewhere
            elif isinstance(priceKeyInfo, types.TupleType):
                assert costPattern == 'instance', u"Fuel type %s has amortization but is not by-instance"%fridge.name
                basePrice = self.sim.userInput[priceKeyInfo[0]]
                amortPeriod = self.sim.userInput[priceKeyInfo[1]]
                assert basePrice is not None, u"Cost information for power type %s is missing"%fuel
                assert amortPeriod is not None and amortPeriod != 0.0, u"Component lifetime for power type %s is missing"%fuel
                fuelPrice = basePrice/amortPeriod
            else:
                fuelPrice = self.sim.userInput[priceKeyInfo] # in run currency at run base year
                assert fuelPrice is not None, u"Cost information for power type %s is missing"%fuel
            baseCost = fridge.recDict['BaseCost']
            powerRate = fridge.recDict['PowerRate']
            assert baseCost is not None and powerRate is not None, u"Cost information for %s is incomplete"%fridge.name
            runCur = self.sim.userInput['currencybase']
            runCurYear = self.sim.userInput['currencybaseyear']
            rawAmortCost = baseCost*(self.intervalEndTime - self.intervalStartTime)/amortPeriod
            #print 'handling %s'%fridge.recDict['Name']
            amortCost = self.currencyConverter.convertTo(rawAmortCost, fCur, runCur, fYear, runCurYear, inflation)
            if fuelPrice == 0.0: 
                fuelCost = 0.0  # fuel handled elsewhere; save some math
            else:
                #
                #  This cost is proportional to time.  Since the fuel price is already in run currency at the run year,
                #  no inflation or currency conversion is needed.
                #
                fuelCost = powerRate*fuelPrice*(self.intervalEndTime - self.intervalStartTime)
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


class MicroCostModelVerifier(dummycostmodel.DummyCostModelVerifier):
    def __init__(self, currencyConverter):
        self.currencyConverter = currencyConverter
        dummycostmodel.DummyCostModelVerifier.__init__(self)

    def _verifyFridge(self, invTp):
        try:
            return (invTp.Energy is not None \
                    and (isinstance(invTp.BaseCost,types.FloatType) and invTp.BaseCost>=0.0) \
                    and invTp.BaseCostCurCode is not None \
                    and (isinstance(invTp.BaseCostYear,(types.IntType, types.LongType)) and invTp.BaseCostYear>=2000) \
                    and (isinstance(invTp.PowerRate,types.FloatType) and invTp.PowerRate>=0.0))
        except:
            return False

    def _verifyVaccine(self, vTp):
        try:
            return ( isinstance(vTp.pricePerVial, types.FloatType) and vTp.pricePerVial>=0.0 
                     and vTp.priceUnits is not None
                     and (isinstance(vTp.priceBaseYear,(types.IntType, types.LongType)) and vTp.priceBaseYear>=2000) )
        except:
            return False
        
    def _verifyTruck(self, invTp):
        try:
            return (invTp.Fuel is not None \
                    and (isinstance(invTp.BaseCost,types.FloatType) and invTp.BaseCost>=0.0) \
                    and invTp.BaseCostCurCode is not None \
                    and (isinstance(invTp.BaseCostYear,(types.IntType, types.LongType)) and invTp.BaseCostYear>=2000) \
                    and (isinstance(invTp.FuelRate,types.FloatType) and invTp.FuelRate>=0.0) \
                    )
        except:
            return False
        
    def _verifyCostConversion(self, curCode, year):
        try:
            if curCode is None or year is None: return True
            else: return (0.0<=self.currencyConverter.convertTo(1.0,curCode,'USD',year))
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
        problemSet = set()
        
        print '####### beginning checks'
        # Check all the fuel price entries from parms
        for v in priceKeyTable.values()+['priceinflation', 'amortizationstorageyears'] :
            if v is None: continue  # 'free' fuel
            if isinstance(v, types.TupleType):
                for vv in v:
                    try:
                        if not isinstance(net.getParameterValue(vv), types.FloatType):
                            problemSet.add("%s is not defined or is invalid"%vv)
                    except:
                        problemSet.add("%s is not a valid parameter"%vv)
            else:
                try:
                    if not isinstance(net.getParameterValue(v), types.FloatType):
                        problemSet.add("%s is not defined or is invalid"%v)
                except:
                    problemSet.add("%s is not a valid parameter"%v)

        for v in ['currencybaseyear'] :
            try:
                if not isinstance(net.getParameterValue(v), types.IntType):
                    problemSet.add("%s is not defined or is invalid"%v)
            except:
                problemSet.add("%s is not a valid parameter"%v)
                    
        for v in ['currencybase'] :
            try:
                if not isinstance(net.getParameterValue(v), types.StringTypes):
                    problemSet.add("%s is not defined or is invalid"%v)
            except:
                problemSet.add("%s is not a valid parameter"%v)
                    
        
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
                if invTp.typeClass == 'fridges':
                    if not self._verifyFridge(invTp):
                        problemSet.add("Storage type %s has missing costing entries"%invTp.Name)
                    if not self._verifyCostConversion(invTp.BaseCostCurCode, invTp.BaseCostYear):
                        problemSet.add("No currency conversion value is available for the currency %s in %s"%\
                                           (invTp.BaseCostCurCode, invTp.BaseCostYear))
                elif invTp.typeClass == 'trucks':
                    if not self._verifyTruck(invTp):
                        problemSet.add("Truck type %s has missing costing entries"%invTp.Name)
                    if not self._verifyCostConversion(invTp.BaseCostCurCode, invTp.BaseCostYear):
                        problemSet.add("No currency conversion value is available for the currency %s in %s"%\
                                           (invTp.BaseCostCurCode, invTp.BaseCostYear))
                    truckStorageNames = [b for a,b in util.parseInventoryString(shdInv.invType.Storage)]  # @UnusedVariable
                    for fridge in [net.fridges[nm] for nm in truckStorageNames]:
                        if fridge.Name in alreadyChecked: continue
                        else: alreadyChecked.add(fridge.Name)
                        if not self._verifyFridge(fridge):
                            problemSet.add("Storage type %s has missing costing entries"%fridge.Name)
                        if not self._verifyCostConversion(fridge.BaseCostCurCode, fridge.BaseCostYear):
                            problemSet.add("No currency conversion value is available for the currency %s in %s"%\
                                               (fridge.BaseCostCurCode, fridge.BaseCostYear))

        for v in [net.vaccines[dmnd.vaccineStr] for dmnd in net.unifiedDemands+net.shippingDemands+net.consumptionDemands
                       if dmnd.vaccineStr in net.vaccines]:
            if v.Name in alreadyChecked: continue
            else: alreadyChecked.add(v.Name)
            if not self._verifyVaccine(v):
                problemSet.add("Vaccine type %s has missing costing entries"%v.Name)
            if not self._verifyCostConversion(v.priceUnits, v.priceBaseYear):
                problemSet.add("No currency conversion value is available for the currency %s in %s"%\
                               (v.priceUnits, v.priceBaseYear))
        print '##### Done checking'

        return list(problemSet)


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


