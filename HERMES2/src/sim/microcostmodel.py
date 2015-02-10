#!/usr/bin/env python

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


__doc__=""" microcostmodel.py
This module holds classes used in calculating costs associated
with simulations.
"""

_hermes_svn_id_ = "$Id$"

import sys
import StringIO
import types
import unittest
import ipath
import abstractbaseclasses
import warehouse
import fridgetypes
import trucktypes
import vaccinetypes
import stafftypes
import perdiemtypes
import util
import dummycostmodel
from currencysupport import CurrencyConverter

#: priceKeyTable maps the name keys for fuels to the parameter entry
#: holding their price
priceKeyTable = {'propane': 'pricepropaneperkg',
                 'kerosene': 'pricekeroseneperl',
                 'gasoline': 'pricegasolineperl',
                 'diesel': 'pricedieselperl',
                 'electric': 'priceelectricperkwh',
                 'solar': ('pricesolarperkw', 'solarpanellifetimeyears'),
                 'ice': 'priceiceperliter',
                 'free': None
                 }


class MicroCostManager(dummycostmodel.DummyCostManager):
    @staticmethod
    def _getPendingCostEvents(costable):
        l = costable.getPendingCostEvents()
        # No danger of double-counting with this recursion because _getPendingCostEvents
        # clears the list
        if isinstance(costable, abstractbaseclasses.CanOwn):
            l.extend(costable.applyToAll(abstractbaseclasses.Costable,
                                         MicroCostManager._getPendingCostEvents))
        return l

    @staticmethod
    def _getInventory(costable):
        return [(costable.getType().name, 'inventory', costable.getCount())]

    def _getFullInventory(self):
        """
        Returns a dict of item counts by type name and a set containing error messages
        (hopefully empty)
        """
        # Traverse the network, collecting inventory information
        inventoryList = []
        errSet = set()
        for r in self.sim.warehouseWeakRefs:
            wh = r()
            if wh is not None:
                try:
                    newInventory = wh.applyToAll(abstractbaseclasses.Costable,
                                                 MicroCostManager._getInventory,
                                                 negFilterClass=trucktypes.Truck)
                    for t in [tt for tt in wh.ownedCostables if isinstance(tt, trucktypes.Truck)]:
                        newInventory.extend(t.applyToAll(abstractbaseclasses.Costable,
                                                         MicroCostManager._getInventory))
                except Exception, e:
                    errSet.add(unicode(e))
                inventoryList.extend(newInventory)

        if len(errSet) > 0:
            util.logError("The following errors were found during inventory-taking for costing")
            for s in list(errSet):
                util.logError(s)
            raise RuntimeError("Exiting due to errors during inventory-taking")

        invDict = {}
        for l in inventoryList:
            for name, key, count in [tpl[:3] for tpl in l]:
                assert key == 'inventory', 'internal error scanning inventory'
                if name in invDict:
                    invDict[name] += count
                else:
                    invDict[name] = count
        return invDict

    def _calcInventoryCost(self, pairList):
        tot = 0.0
        errList = []
        runCur = self.sim.userInput['currencybase']
        runCurYear = self.sim.userInput['currencybaseyear']
        inflation = self.sim.userInput['priceinflation']  # cur converter wants per-year inflation
        for tpName, cnt in pairList:
            try:
                tp = self.sim.typeManager.getTypeByName(tpName)
                if isinstance(tp, vaccinetypes.VaccineType):
                    if self.sim.userInput['vaccinecostsincluded']:
                        baseCost = tp.recDict['Vaccine price/vial']
                        baseCostCurCode = tp.recDict['Price Units']
                        baseCostYear = tp.recDict['Price Year']
                    else:
                        continue
                elif (isinstance(tp, fridgetypes.FridgeType)
                      or isinstance(tp, trucktypes.TruckType)):
                    baseCost = tp.recDict['BaseCost']
                    baseCostCurCode = tp.recDict['BaseCostCur']
                    baseCostYear = tp.recDict['BaseCostYear']
                else:
                    raise RuntimeError("Inventory of %s changed - what is this type?" % tpName)
                unitCost = self.currencyConverter.convertTo(baseCost, baseCostCurCode, runCur,
                                                            baseCostYear, runCurYear, inflation)
                tot += cnt*unitCost
            except Exception, e:
                errList.append(unicode(e))
        return tot, errList

    def __init__(self, sim, model, currencyConverter):
        """
        This class knows how to calculate and output cost information, based on the current Model
        and type-specific base costs.
        """
        self.currencyConverter = currencyConverter
        self.startingInventoryDict = None
        self.inventoryChangeCost = None
        dummycostmodel.DummyCostManager.__init__(self, sim, model)

    def startCostingInterval(self, timeNow=None):
        dummycostmodel.DummyCostManager.startCostingInterval(self, timeNow)  # Do the default stuff
        invDict = self._getFullInventory()
        self.startingInventoryDict = invDict

    def endCostingInterval(self, timeNow=None):
        """
        End the costing interval and trigger the addition of cost-related notes for this interval
        to all StatProviders.  It is expected that this call will be followed by one or more calls
        to generateCostRecordInfo with different ReportingHierarchies, perhaps followed by
        clearing of costing data from the StatProviders, followed by a call to startCostingInterval
        to begin the cycle again.

        This CostManager should return the following data:
           for Fridges: fuelCost, amortizationCost
           for Trucks: fuelCost, amortizationByKmCost, driverCost, perDiemCost
           for healthposts: staffCost, vaccineCost, buildingCost
           for warehouses: staffCost, buildingCost
        How does it know the right units?
        """

        errList = []

        if self.startingInventoryDict is None:
            raise RuntimeError("Inventory from interval start is missing")
        invDict = self._getFullInventory()
        invChanges = []
        for k in set(invDict.keys()+self.startingInventoryDict.keys()):
            startingCount = self.startingInventoryDict[k] if k in self.startingInventoryDict else 0
            endingCount = invDict[k] if k in invDict else 0
            if startingCount != endingCount:
                invChanges.append((k, endingCount - startingCount))
        # print 'list of inventory changes: %s'%invChanges
        self.inventoryChangeCost, newErrList = self._calcInventoryCost(invChanges)
        self.startingInventoryDict = None
        errList.extend(newErrList)

        if timeNow is None:
            timeNow = self.sim.now()
        if self.intervalStartTime is None or self.intervalEndTime is not None:
            raise RuntimeError("Costing interval is not properly bounded")
        self.intervalEndTime = timeNow
        # We do this loop in a try/except to bundle more error messages together, since there is a
        # long annoying process of finding missing price info.
        inflation = self.sim.userInput['priceinflation']  # used by currencyConverter, so per-year
        allPendingCostEvents = []
        for r in self.sim.warehouseWeakRefs:
            wh = r()
            if wh is not None:
                nh = wh.getNoteHolder()
                if nh is None:
                    continue
                if not isinstance(wh, warehouse.AttachedClinic):
                    nh.addNote(self._generateBuildingCostNotes(wh,
                                                               self.intervalStartTime,
                                                               self.intervalEndTime,
                                                               inflation))
                    for costable in wh.ownedCostables:
                        if isinstance(costable, abstractbaseclasses.CanStore):
                            try:
                                nh.addNote(self._generateFridgeCostNotes(wh.reportingLevel,
                                                                         wh.conditions,
                                                                         self.intervalStartTime,
                                                                         self.intervalEndTime,
                                                                         costable.getType(),
                                                                         inflation))
                            except Exception, e:
                                errList.append(unicode(e))
                        elif isinstance(costable, trucktypes.Truck):
                            for innerItem in costable.getCargo():
                                if isinstance(innerItem, abstractbaseclasses.CanStore):
                                    try:
                                        nh.addNote(self._generateFridgeCostNotes(wh.reportingLevel,
                                                                                 wh.conditions,
                                                                                 self.intervalStartTime,
                                                                                 self.intervalEndTime,
                                                                                 innerItem.getType(),
                                                                                 inflation))
                                    except Exception, e:
                                        errList.append(str(e))
                        elif isinstance(costable, stafftypes.Staff):
                            try:
                                nh.addNote(self._generateStaffCostNotes(wh.reportingLevel,
                                                                        wh.conditions,
                                                                        self.intervalStartTime,
                                                                        self.intervalEndTime,
                                                                        costable.getType(),
                                                                        inflation))
                            except Exception, e:
                                errList.append(unicode(e))
                        else:
                            print 'Unexpectedly found %s on %s' % (type(costable),
                                                                   wh.name)
                            raise RuntimeError("Expected only Fridges, Trucks,"
                                               " or Staff on this list")
                    # No danger of double counting because getPendingCostEvents
                    # clears the list of events
                    allPendingCostEvents.extend(wh.applyToAll(abstractbaseclasses.Costable,
                                                              MicroCostManager._getPendingCostEvents))
                    for costable in wh.ownedCostables:
                        if isinstance(costable, abstractbaseclasses.CanOwn):
                            allPendingCostEvents.extend(costable.applyToAll(abstractbaseclasses.Costable,
                                                                            MicroCostManager._getPendingCostEvents))
                    # print 'allPendingCostEvents from scan: %s'%allPendingCostEvents

        if len(errList) > 0:
            util.logError("The following errors were encountered generating"
                          " costs:")
            for line in errList:
                util.logError("   %s" % line)
            raise RuntimeError("Cost calculation failed")

    def getOverrideTotal(self, dct, key):
        """
        This method is used to provide an override mechanism for LaborCost in
        the reporting hierarchy.
        """
        if key == 'InventoryChangeCost':
            assert dct['ReportingLevel'] == '-top-', \
                'ReportingHierarchy InventoryChangeCost override should have' \
                'level all'
            if dct['ReportingBranch'] == 'all':
                return 'm1C_'+key, self.inventoryChangeCost
            else:
                return None
        elif key == 'LaborCost':
            assert dct['ReportingLevel'] == 'all', \
                'ReportingHierarchy LaborCost override should have level all'
            val = dct['LaborCost']
#             try:
#                 val = self.priceTable.get("labortotal", "PerYear",
#                                           level=dct['ReportingBranch'],
#                                           conditions='normal')
#             except:
#                 pass
            val = 0.0
            return val * (self.intervalEndTime -
                          self.intervalStartTime)/float(self.model.daysPerYear)
        else:
            return None

    def generateFactoryDeliveryCostNotes(self, deliveredSC, targetWH):
        """
        This routine is called once per factory delivery, and returns a Dict suitable for
        NoteHolder.addNote() containing cost information appropriate for the delivery.
        """
        errList = []
        vaxCost, newErrList = self._calcInventoryCost([(v.name, n) for v, n in deliveredSC.items()
                                                       if isinstance(v, vaccinetypes.VaccineType)])
        errList.extend(newErrList)
        fridgeCost, newErrList = self._calcInventoryCost([(v.name, n)
                                                          for v, n in deliveredSC.items()
                                                          if isinstance(v, fridgetypes.FridgeType)])
        errList.extend(newErrList)
        truckCost, newErrList = self._calcInventoryCost([(v.name, n)
                                                         for v, n in deliveredSC.items()
                                                         if isinstance(v, trucktypes.TruckType)])
        if len(errList) != 0:
            util.logError("The following errors were encountered generating costs:")
            for line in errList:
                util.logError("   %s" % line)
            raise RuntimeError("Cost calculation failed")

        return {'m1C_Vaccines': vaxCost, 'm1C_Storage': fridgeCost, 'm1C_Transport': truckCost}

    def generateTripCostNotes(self, truckType, level, homeConditions,
                              tripJournal, originatingWH, perDiemModel):
        """
        This routine is called once per shipping trip, and returns a Dict
        suitable for NoteHolder.addNote() containing cost information
        appropriate for the trip.

        truckType is obviously the type of truck used to make the trip; level
        and homeConditions are used as per their definitions in PriceTable.

        tripJournal is a list of tuples describing the steps of the
        just-completed trip.  tripJournal entries all start with
        (stepname, legStartTime, legEndTime, legConditions...);
        see the description of warehouse.createTravelGenerator for additional
        details.  legConditions==None is equivalent to legConditions=='normal'.

        originatingWH is used both as the starting point of the trip for travel
        distance purposes and as the 'home' for the driver for per diem
        purposes.

        perDiemModel is an instance of PerDiemModel, presumably that associated
        with the trip in question.

        PerKm costs are calculated based on the legConditions for each leg
        traversed; PerDiem and PerTrip costs are based on home conditions.
        """
        totKm = 0.0
        allPendingCostEvents = []
        for tpl in tripJournal:
            op = tpl[0]
            if op == "move":
                legConditions = tpl[3]
                fromWH = tpl[4]
                toWH = tpl[5]
                conditionMultiplier = 1.0
                totKm += (conditionMultiplier *
                          fromWH.getKmTo(toWH, level, legConditions))
            else:
                legConditions = tpl[3]
            miscCosts = tpl[-1]
            allPendingCostEvents.extend(miscCosts)

        errList = []
        result = {}

        #  Costs associated with the truck
        tCur = truckType.recDict['BaseCostCur']
        tYear = truckType.recDict['BaseCostYear']
        eTpl = trucktypes.fuelTranslationDict[truckType.recDict['Fuel']]
        fuel = eTpl[4]
        costPattern = eTpl[5]
        runCur = self.sim.userInput['currencybase']
        runCurYear = self.sim.userInput['currencybaseyear']
        inflation = self.sim.userInput['priceinflation']
        maintFrac = self.sim.userInput['vehiclemaintcostfraction']
        if costPattern == 'distance':
            priceKeyInfo = priceKeyTable[fuel]
            if (priceKeyInfo is not None
                    and self.sim.userInput[priceKeyInfo] != 0.0):
                assert isinstance(priceKeyInfo, types.StringTypes), \
                    (u"fuel type for %s should not have amortization" %
                     truckType.name)
                fuelPrice = self.sim.userInput[priceKeyInfo]  # in run currency at run base year
                assert fuelPrice is not None, \
                    u"Cost information for fuel type %s is missing" % fuel
                fuelRate = truckType.recDict['FuelRate']
                assert fuelRate is not None, \
                    u"Cost information for %s is incomplete" % truckType.name
                #
                # fuel cost is totKm/fuelRate, since fuelRate is an inverse,
                # like Km/liter.  The price of fuel is already given in the
                # run currency at the run year, so no currency conversion is
                # needed.
                #
                fuelCost = (totKm/fuelRate)*fuelPrice
                fare = 0.0
                maintCost = maintFrac * fuelCost
            else:
                # Fuel is free
                fuelCost = 0.0
                fare = 0.0
                maintCost = 0.0
        elif costPattern == 'pertrip':
            rawFare = truckType.recDict['FuelRate']
            fare = self.currencyConverter.convertTo(rawFare, tCur, runCur,
                                                    tYear, runCurYear,
                                                    inflation)
            fuelCost = 0.0
            maintCost = 0.0
        else:
            raise RuntimeError(u'Transport type %s has an unexpected costing pattern' %
                               truckType.name)
        baseCost = truckType.recDict['BaseCost']
        assert baseCost is not None, \
            u"Cost information for %s is incomplete" % truckType.name
        amortKm = truckType.recDict['AmortizationKm']
        if baseCost != 0.0:
            rawAmortCost = baseCost*totKm/amortKm
            amortCost = self.currencyConverter.convertTo(rawAmortCost, tCur,
                                                         runCur, tYear,
                                                         runCurYear, inflation)
        else:
            amortCost = 0.0
        perDiemCostTuple = perDiemModel.calcPerDiemAmountTriple(tripJournal,
                                                                originatingWH)
        pdAmt, pdCur, pdYear = perDiemCostTuple
        perDiemCost = self.currencyConverter.convertTo(pdAmt, pdCur, runCur,
                                                       pdYear, runCurYear,
                                                       inflation)
        for k, v in [("m1C_%s" % fuel, fuelCost),
                     ("m1C_TruckAmort", amortCost),
                     ("m1C_TransitFareCost", fare),
                     ("m1C_PerDiem", perDiemCost),
                     ("m1C_TruckMaint", maintCost)]:
            if v != 0.0:
                if k in result:
                    result[k] += v
                else:
                    result[k] = v

        #  Add in the miscellaneous costs
        miscCostDict = {}
        for tpl in allPendingCostEvents:
            tpName, evtStr, count = tpl[0:3]
            key = (tpName, evtStr)
            if key in miscCostDict:
                miscCostDict[key] += count
            else:
                miscCostDict[key] = count

        for innerFridge, n in truckType.getFridgeCollection().items():
            assert isinstance(innerFridge, fridgetypes.FridgeType), \
                "Expected only Fridges in this category"
            if innerFridge.name.startswith(u'onthefly_'):
                continue
            eKey = innerFridge.recDict['Energy']
            energyInfo = fridgetypes.energyTranslationDict[eKey]  # long tuple
            costPattern = energyInfo[5]
            if costPattern == 'charge':
                # We will assume all ice fridges associated with the truck are
                # charged once per trip
                key = (innerFridge.recDict['Name'], 'recharge')
                if key in miscCostDict.items():
                    miscCostDict[key] += n
                else:
                    miscCostDict[key] = n
            else:
                pass

        # Now generate costs for all the events identified
        for k, n in miscCostDict.items():
            tpName, evtStr = k
            tp = self.sim.typeManager.getTypeByName(tpName)
            if isinstance(tp, fridgetypes.FridgeType):
                eKey = tp.recDict['Energy']
                energyInfo = fridgetypes.energyTranslationDict[eKey]
                costPattern = energyInfo[5]
                if evtStr == 'recharge':
                    if costPattern == 'charge':
                        # We will assume all ice fridges associated with the
                        # truck are charged once per trip
                        try:
                            fuel = energyInfo[4]
                            priceKeyInfo = priceKeyTable[fuel]
                            powerRate = tp.recDict['PowerRate']
                            assert powerRate is not None, \
                                (u"Cost information for %s is incomplete" %
                                 tp.name)
                            runCur = self.sim.userInput['currencybase']
                            runCurYear = self.sim.userInput['currencybaseyear']
                            fuelPrice = self.sim.userInput[priceKeyInfo]  # in run currency at run base year
                            assert not isinstance(fuelPrice, types.TupleType), \
                                "Ice should not have an amortization rate"
                            #
                            # fuel cost is just powerRat*fuelPrice, since this
                            # is per-trip and not time-dependent.  The price
                            # of fuel is already given in the run currency at
                            # the run year, so no currency conversion is
                            # needed.
                            #
                            fuelCost = powerRate * fuelPrice  # one charge per trip
                            valKey = "m1C_%s" % fuel
                            fuelCost *= n
                            if valKey in result:
                                result[valKey] += fuelCost
                            else:
                                result[valKey] = fuelCost
                        except Exception, e:
                            errList.append(unicode(e))
                else:
                    errList.append("Unhandled cost event %s for type %s (%d instances)" %
                                   (tpName, evtStr, count))
            else:
                errList.append("Unhandled cost event %s for type %s (%d instances)" %
                               (tpName, evtStr, count))

        if len(errList) > 0:
            util.logError("The following errors were encountered generating "
                          "trip costs:")
            for line in errList:
                util.logError("   %s" % line)
            raise RuntimeError("Trip Cost calculation failed")

        return result

    def generateUseVialsSessionCostNotes(self, level, conditions):
        """
        This routine is called once per UseVials session, and returns a Dict
        suitable for NoteHolder.addNote() containing cost information
        appropriate for the session.

        Under microcosting there are no such costs because we are only costing
        for transport infrastructure, so we return an empty dict.
        """
        return {}

    def _generateFridgeCostNotes(self, level, conditions, startTime, endTime,
                                 costable, inflation):
        """
        This routine is called once per Fridge instance per reporting interval,
        and returns a Dict suitable for NoteHoder.addNote() containing cost
        information for that instance over the interval.  A simple linear
        amortization schedule is assumed.
        """
        assert isinstance(costable, fridgetypes.FridgeType), \
            "expected %s to be a FridgeType" % costable
        fridge = costable
        if fridge.recDict['Name'].startswith('onthefly_'):
            # This is an 'OnTheFly' fridge within a vehicle or warehouse;
            # fridge cost assumed to be subsumed by vehicle cost
            return {}
        else:
            fCur = fridge.recDict['BaseCostCur']
            fYear = fridge.recDict['BaseCostYear']
            eTpl = fridgetypes.energyTranslationDict[fridge.recDict['Energy']]
            fuel = eTpl[4]
            costPattern = eTpl[5]
            priceKeyInfo = priceKeyTable[fuel]
            solarMaintPriceRaw = 0.0
            if costPattern == 'charge':
                fuelPrice = 0.0  # handled elsewhere
            elif isinstance(priceKeyInfo, types.TupleType):
                # We now handle the special case of solar power, where we have to include the
                # amortization and maintenance cost of the panels.  Remember that the needed
                # installed kilowatts are stored in the 'PowerRate' field for solar fridges.
                assert fuel == 'solar', \
                    'Per instance fuel maintenance but the fuel %s is not a solar panel' % fuel
                assert costPattern == 'instance', \
                    u"Fuel type %s has amortization but is not by-instance" % \
                    fridge.name
                # base price is (price per installed kilowatt) * (installed kilowatts needed)
                basePrice = self.sim.userInput[priceKeyInfo[0]] * fridge.recDict['PowerRate']
                solarMaintPriceRaw = self.sim.userInput['storagemaintcostfraction'] * basePrice
                fuelAmortPeriod = self.sim.userInput[priceKeyInfo[1]]
                assert basePrice is not None, \
                    u"Cost information for power type %s is missing" % fuel
                assert fuelAmortPeriod is not None and fuelAmortPeriod != 0.0, \
                    u"Component lifetime for power type %s is missing" % fuel
                fuelPrice = basePrice/fuelAmortPeriod
            else:
                fuelPrice = self.sim.userInput[priceKeyInfo]  # in run currency at run base year
                assert fuelPrice is not None, \
                    u"Cost information for power type %s is missing" % fuel
            baseCost = fridge.recDict['BaseCost']
            powerRate = fridge.recDict['PowerRate']
            amortPeriod = fridge.recDict['AmortYears']*self.model.daysPerYear
            assert (baseCost is not None and powerRate is not None
                    and fridge.recDict['AmortYears'] is not None), \
                u"Cost information for %s is incomplete" % fridge.name
            runCur = self.sim.userInput['currencybase']
            runCurYear = self.sim.userInput['currencybaseyear']
            rawAmortCost = baseCost*(self.intervalEndTime
                                     - self.intervalStartTime)/amortPeriod
            rawMaintCost = baseCost*self.sim.userInput['storagemaintcostfraction']
            # print 'handling %s'%fridge.recDict['Name']
            amortCost = self.currencyConverter.convertTo(rawAmortCost, fCur,
                                                         runCur, fYear,
                                                         runCurYear, inflation)
            maintCost = self.currencyConverter.convertTo(rawMaintCost, fCur,
                                                         runCur, fYear,
                                                         runCurYear, inflation)
            solarMaintCost = self.currencyConverter.convertTo(solarMaintPriceRaw, fCur,
                                                              runCur, fYear,
                                                              runCurYear, inflation)
            if fuelPrice == 0.0:
                fuelCost = 0.0  # fuel handled elsewhere; save some math
            else:
                #
                #  This cost is proportional to time.  Since the fuel price is
                #  already in run currency at the run year,
                #  no inflation or currency conversion is needed.
                #
                fuelCost = powerRate*fuelPrice*(self.intervalEndTime
                                                - self.intervalStartTime)
            return {"m1C_%s" % fuel: fuelCost, "m1C_FridgeAmort": amortCost,
                    "m1C_FridgeMaint": maintCost, "m1C_SolarMaint": solarMaintCost}

    def _generateStaffCostNotes(self, level, conditions, startTime, endTime,
                                costable, inflation):
        """
        This routine is called once per Staff instance per reporting interval,
        and returns a Dict suitable for NoteHoder.addNote() containing cost
        information for that instance over the interval.
        """
        assert isinstance(costable, stafftypes.StaffType), \
            "expected %s to be a StaffType" % costable
        staff = costable
        fCur = staff.recDict['BaseSalaryCur']
        fYear = staff.recDict['BaseSalaryYear']
        baseSalary = staff.recDict['BaseSalary']
        assert baseSalary is not None, \
            u"Cost information for %s is incomplete" % staff.name
        fracEPI = staff.recDict['FractionEPI']
        assert (baseSalary is not None
                and isinstance(fracEPI, types.FloatType)
                and fracEPI >= 0.0 and fracEPI <= 1.0), \
            u"Cost information for %s is incomplete" % staff.name
        runCur = self.sim.userInput['currencybase']
        runCurYear = self.sim.userInput['currencybaseyear']
        rawStaffCost = (fracEPI * baseSalary * (self.intervalEndTime
                                                - self.intervalStartTime)
                        / self.model.daysPerYear)
        # print 'handling %s'%staff.recDict['Name']
        staffCost = self.currencyConverter.convertTo(rawStaffCost,
                                                     fCur, runCur,
                                                     fYear, runCurYear,
                                                     inflation)
        return {"m1C_StaffSalary": staffCost}

    def _generateBuildingCostNotes(self, wh, startTime, endTime, inflation):
        """
        This routine is called once per Warehouse or Clinic instance per reporting interval,
        and returns a Dict suitable for NoteHoder.addNote() containing cost information
        associated with the building or location for that instance over the interval.

        Note that it is probably an error to call this function for an AttachedClinic instance,
        as AttachedClinics have no associated building.
        """
        rawCost = wh.recDict['SiteCostPerYear']*((endTime-startTime)/self.model.daysPerYear)
        fCur = wh.recDict['SiteCostCur']
        fYear = wh.recDict['SiteCostBaseYear']
        runCur = self.sim.userInput['currencybase']
        runCurYear = self.sim.userInput['currencybaseyear']
        cost = self.currencyConverter.convertTo(rawCost, fCur, runCur, fYear, runCurYear,
                                                inflation)
        return {"m1C_BuildingCost": cost}

    def generateCostRecordInfo(self, reportingHierarchy, timeNow=None):
        """
        Returns a set of cost statistics for the given reportingHierarchy.  The function returns
        a tuple (keys, recs) in the format used for reading and writing CSV files.
        """
        if timeNow is None:
            timeNow = self.sim.now()
        available = reportingHierarchy.getAvailableFieldNames()
        wanted = [fld for fld in available if fld.startswith('m1C_')]
        keys = ['ReportingLevel', 'ReportingBranch', 'ReportingIntervalDays', 'DaysPerYear',
                'Currency', 'BaseYear', 'Type'] + wanted
        recs = reportingHierarchy.report(wanted)
        keys += ['Currency', 'BaseYear']
        for rec in recs:
            rec['Currency'] = self.currencyConverter.getBaseCurrency()
            rec['BaseYear'] = self.currencyConverter.getBaseYear()
            rec['ReportingIntervalDays'] = self.intervalEndTime - self.intervalStartTime
            rec['DaysPerYear'] = float(self.model.daysPerYear)
            rec['Type'] = 'micro1'
        return keys, recs

    def realityCheck(self):
        """
        This scans for inappropriate costs entries- but since everything is
        done from the type records, there is nothing to be checked.
        """
        pass

    def getPerDiemModel(self, perDiemName):
        assert perDiemName is not None and perDiemName != '', \
            "Microcosting requires real per diem type names"
        return self.sim.perdiems.getTypeByName(perDiemName)


class MicroCostModelVerifier(dummycostmodel.DummyCostModelVerifier):
    def __init__(self, currencyConverter):
        self.currencyConverter = currencyConverter
        dummycostmodel.DummyCostModelVerifier.__init__(self)

    def _verifyFridge(self, invTp):
        try:
            return (invTp.Energy is not None
                    and (isinstance(invTp.BaseCost, types.FloatType)
                         and invTp.BaseCost >= 0.0)
                    and invTp.BaseCostCurCode is not None
                    and (isinstance(invTp.BaseCostYear, (types.IntType,
                                                         types.LongType))
                         and invTp.BaseCostYear >= 2000)
                    and (isinstance(invTp.AmortYears, types.FloatType)
                         and invTp.AmortYears >= 0.0)
                    and (isinstance(invTp.PowerRate, types.FloatType)
                         and invTp.PowerRate >= 0.0)
                    and (invTp.Energy in fridgetypes.energyTranslationDict))
        except:
            return False

    def _verifyVaccine(self, vTp):
        try:
            return (isinstance(vTp.pricePerVial, types.FloatType)
                    and vTp.pricePerVial >= 0.0
                    and vTp.priceUnits is not None
                    and (isinstance(vTp.priceBaseYear, (types.IntType,
                                                        types.LongType))
                         and vTp.priceBaseYear >= 2000))
        except:
            return False

    def _verifyTruck(self, invTp):
        try:
            return (invTp.Fuel is not None
                    and (isinstance(invTp.BaseCost, types.FloatType)
                         and invTp.BaseCost >= 0.0)
                    and invTp.BaseCostCurCode is not None
                    and (isinstance(invTp.BaseCostYear, (types.IntType,
                                                         types.LongType))
                         and invTp.BaseCostYear >= 2000)
                    and (isinstance(invTp.FuelRate, types.FloatType)
                         and invTp.FuelRate >= 0.0)
                    )
        except:
            return False

    def _verifyStaff(self, invTp):
        try:
            return ((isinstance(invTp.BaseSalary, types.FloatType)
                     and invTp.BaseSalary >= 0.0)
                    and invTp.BaseSalaryCurCode is not None
                    and (isinstance(invTp.BaseSalaryYear, (types.IntType,
                                                           types.LongType))
                         and invTp.BaseSalaryYear >= 2000)
                    and (isinstance(invTp.FractionEPI, types.FloatType)
                         and invTp.FractionEPI >= 0.0 and invTp.FractionEPI <= 1.0)
                    )
        except:
            return False

    def _verifyCostConversion(self, curCode, year):
        try:
            if curCode is None or year is None:
                return True
            else:
                return (0.0 <= self.currencyConverter.convertTo(1.0, curCode,
                                                                'USD', year))
        except:
            return False

    def _verifyRoute(self, shdRoute, shdNet):
        try:
            return (((shdRoute.PerDiemType is not None and shdRoute.PerDiemType != '')
                     and shdRoute.PerDiemType in shdNet.perdiems)
                    or shdRoute.Type == 'attached')
        except:
            return False

    def _verifyStore(self, shdStore, shdNet):
        try:
            return ((shdStore.SiteCost is not None and shdStore.SiteCost != ''
                     and float(shdStore.SiteCost) >= 0.0)
                    and (shdStore.SiteCostCurCode is not None)
                    and (isinstance(shdStore.SiteCostYear, (types.IntType, types.LongType))
                         and shdStore.SiteCostYear >= 2000 and shdStore.SiteCostYear <= 3000)
                    )
        except:
            return False

    def _verifyPerDiem(self, perDiemType):
        try:
            return ((isinstance(perDiemType.BaseAmount, types.FloatType)
                     and perDiemType.BaseAmount >= 0.0)
                    and perDiemType.BaseAmountCurCode is not None
                    and (isinstance(perDiemType.BaseAmountYear, (types.IntType,
                                                                 types.LongType))
                         and perDiemType.BaseAmountYear >= 2000)
                    and (isinstance(perDiemType.MinKmHome, types.FloatType)
                         and perDiemType.MinKmHome >= 0.0)
                    and (isinstance(perDiemType.MustBeOvernight, types.BooleanType))
                    and (isinstance(perDiemType.CountFirstDay, types.BooleanType))
                    )

        except:
            return False

    def checkReady(self, net):
        problemList = self.getProblemList(net)
        return (len(problemList) == 0)

    def getProblemList(self, net):
        """
        This scans the given ShdNetwork, making sure that all data needed to
        compute costs for the model are defined.
        """
        probSet = set()

        print '####### beginning checks'
        # Check all the fuel price entries from parms
        for v in priceKeyTable.values() + ['priceinflation',
                                           'amortizationstorageyears',
                                           'vehiclemaintcostfraction',
                                           'storagemaintcostfraction']:
            if v is None:
                continue  # 'free' fuel
            if isinstance(v, types.TupleType):
                for vv in v:
                    try:
                        if not isinstance(net.getParameterValue(vv),
                                          types.FloatType):
                            probSet.add("%s is not defined or is invalid" % vv)
                    except:
                        probSet.add("%s is not a valid parameter" % vv)
            else:
                try:
                    if not isinstance(net.getParameterValue(v),
                                      types.FloatType):
                        probSet.add("%s is not defined or is invalid" % v)
                except:
                    probSet.add("%s is not a valid parameter" % v)

        for v in ['currencybaseyear']:
            try:
                if not isinstance(net.getParameterValue(v), types.IntType):
                    probSet.add("%s is not defined or is invalid" % v)
            except:
                probSet.add("%s is not a valid parameter" % v)

        for v in ['currencybase']:
            try:
                if not isinstance(net.getParameterValue(v), types.StringTypes):
                    probSet.add("%s is not defined or is invalid" % v)
            except:
                probSet.add("%s is not a valid parameter" % v)

        # Check the fridge cost entries
        alreadyChecked = set()
        for storeId, store in net.stores.items():  # @UnusedVariable
            if hasattr(store, 'conditions') and store.conditions is not None:
                conditions = store.conditions
            else:
                conditions = u'normal'

            if not self._verifyStore(store, net):
                probSet.add("The location %s (%d) has missing cost entries" %
                            (store.NAME, storeId))
            if not self._verifyCostConversion(store.SiteCostCurCode, store.SiteCostYear):
                probSet.add("No currency conversion value is available for the"
                            " currency %s in %s" % (store.SiteCostCurCode, store.SiteCostYear))

            for shdInv in store.inventory:
                invTp = shdInv.invType
                if invTp.Name in alreadyChecked:
                    continue
                else:
                    alreadyChecked.add(invTp.Name)
                if invTp.typeClass == 'fridges':
                    if not self._verifyFridge(invTp):
                        probSet.add("Storage type %s has missing cost entries" %
                                    invTp.Name)
                    if not self._verifyCostConversion(invTp.BaseCostCurCode,
                                                      invTp.BaseCostYear):
                        probSet.add("No currency conversion value is available for the"
                                    " currency %s in %s" % (invTp.BaseCostCurCode,
                                                            invTp.BaseCostYear))
                elif invTp.typeClass == 'trucks':
                    if not self._verifyTruck(invTp):
                        probSet.add("Truck type %s has missing costing entries" %
                                    invTp.Name)
                    if not self._verifyCostConversion(invTp.BaseCostCurCode,
                                                      invTp.BaseCostYear):
                        probSet.add("No currency conversion value is available for the"
                                    " currency %s in %s" % (invTp.BaseCostCurCode,
                                                            invTp.BaseCostYear))
                    truckStorageNames = [b for a, b  # @UnusedVariable
                                         in util.parseInventoryString(shdInv.invType.Storage)]
                    for fridge in [net.fridges[nm]
                                   for nm in truckStorageNames]:
                        if fridge.Name in alreadyChecked:
                            continue
                        else:
                            alreadyChecked.add(fridge.Name)
                        if not self._verifyFridge(fridge):
                            probSet.add("Storage type %s has missing costing entries"
                                        % fridge.Name)
                        if not self._verifyCostConversion(fridge.BaseCostCurCode,
                                                          fridge.BaseCostYear):
                            probSet.add("No currency conversion value is available for the"
                                        " currency %s in %s" % (fridge.BaseCostCurCode,
                                                                fridge.BaseCostYear))
                elif invTp.typeClass == 'staff':
                    if not self._verifyStaff(invTp):
                        probSet.add("Staff type %s has missing cost entries" %
                                    invTp.Name)
                    if not self._verifyCostConversion(invTp.BaseSalaryCurCode,
                                                      invTp.BaseSalaryYear):
                        probSet.add("No currency conversion value is available for the"
                                    " currency %s in %s" % (invTp.BaseCostCurCode,
                                                            invTp.BaseCostYear))

        for routeName, route in net.routes.items():
            if not self._verifyRoute(route, net):
                probSet.add("Route %s has missing costing entries" % routeName)
            pDTName = route.PerDiemType
            if pDTName is None or pDTName == u'':
                probSet.add("Route %s has no PerDiem policy" % routeName)
            else:
                pDT = net.perdiems[pDTName]
                if pDTName in alreadyChecked:
                    continue
                else:
                    alreadyChecked.add(pDTName)
                    if not self._verifyPerDiem(pDT):
                        probSet.add("PerDiem type %s has missing costing entries" % pDTName)
                    if not self._verifyCostConversion(pDT.BaseAmountCurCode,
                                                      pDT.BaseAmountYear):
                        probSet.add("No currency conversion value is available for the"
                                    " currency %s in %s" % (pDT.BaseAmountCurCode,
                                                            pDT.BaseAmountYear))

        if net.getParameterValue('vaccinecostsincluded'):
            for v in [net.vaccines[dmnd.vaccineStr]
                      for dmnd in (net.unifiedDemands
                                   + net.shippingDemands
                                   + net.consumptionDemands)
                      if dmnd.vaccineStr in net.vaccines]:
                if v.Name in alreadyChecked:
                    continue
                else:
                    alreadyChecked.add(v.Name)
                if not self._verifyVaccine(v):
                    probSet.add("Vaccine type %s has missing costing entries" %
                                v.Name)
                if not self._verifyCostConversion(v.priceUnits, v.priceBaseYear):
                    probSet.add("No currency conversion value is available for the"
                                " currency %s in %s" %
                                (v.priceUnits, v.priceBaseYear))
        print '##### Done checking'

        return list(probSet)


def describeSelf():
    print """
Testing options:

  None so far

"""


def main(myargv=None):
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


