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


__doc__=""" model_generic.py
This is a generic model for the vaccine distribution simulator HERMES
"""

##########################
# Notes-
#
##########################

_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math

import globals as G

import constants as C
import recorders
import storagetypes
import vaccinetypes
import trucktypes
import peopletypes as pt
from util import openDataFullPath
from noteholder import NoteHolderGroup
import warehouse
import sampler
import demandmodel
import breakagemodel
import packagingmodel
import storagemodel
import model
import csv_tools
import abstractbaseclasses
from copy import copy, deepcopy

class MonthlyOrderProcess(warehouse.PeriodicProcess):
    """
    This process type is used to keep the InstantaneousDemand for a given Clinic updated.
    That value is then read by upstream suppliers as they calculate their shipment quantities.
    """
    def __init__(self,interval, startupLatency,wh):
        warehouse.PeriodicProcess.__init__(self, wh.sim, "MonthlyOrderProcess_%s"%wh.name,
                                           interval,startupLatency)
        self.wh= wh
        assert(hasattr(self.wh,'shippingDemandModel'))
    def cycle(self,timeNow):

## The monthly order will be based on how many people you will need to have vaccinated
## rounded up to the number of vials needed to match that demand.  This implies
## OVW so there is no need to scale the demand by the OVW.

        dosesNeededVC= self.wh.shippingDemandModel.getDemandExpectation(self.wh.getPopServedPC(),
                                                                        self.interval,timeNow=timeNow)
#        if self.interval == 1:
#            vialsVC = dosesNeededVC*self.sim.vaccines.getDosesToVialsVC()
#        else:
#            vialsVC= self.sim.model._scaleDemandByType(dosesNeededVC)

        vialsVC = dosesNeededVC*self.sim.vaccines.getDosesToVialsVC()
        vialsVC.roundUp()
        vialsVC = self.sim.shippables.addPrepSupplies(vialsVC)

        self.wh.registerInstantaneousDemandVC(vialsVC,self.interval)

class MonthlyReportProcess(warehouse.PeriodicProcess):
    """
    This process is used to store reporting data by month, rather than only at the end of
    the simulation.
    """
    def __init__(self,sim,interval,startupLatency):
        warehouse.PeriodicProcess.__init__(self,sim,"MonthlyReportProcess",interval,startupLatency)
        self.counter= 0
    def cycle(self,timeNow):
        nameRoot= 'report_%03d'%self.counter
        print "\nWriting %s"%nameRoot
        self.sim.syncStatistics()
        Model.checkSummary(nameRoot,clear=True)
        self.counter += 1


def _createAndExtendList(length, baseList, defaultVal):
    ret = []
    lastVal = defaultVal
    for i in xrange(length):
        if i < len(baseList):
            lastVal = baseList[i]
        ret.append(lastVal)

    return ret


class Model(model.Model):

    class SurrogateClinic(warehouse.AttachedClinic):
        """
        This is defined to make it easier for the code to distinguish surrogates from
        regular old attached clinics.
        """
        pass

    class CentralWarehouse(warehouse.Warehouse):
        """
        This is defined to make it easier for the code to distinguish the top-level warehouse,
        which presumably gets the factory.
        """
        pass

    class OutreachClinic(warehouse.Clinic):
        """
        This is defined to make it easier for the code to distinguish outreach locations,
        which have different delivery and UseVials rules.
        """
        pass

    def __init__(self, sim):
        model.Model.__init__(self,sim)

        ##################
        # Info provided via the input file
        # Look below this block for things you may have to override in a derived model file!
        ##################
        #if self.sim.userInput['twentyeightdaymonths']: self.daysPerMonth = 28
        #else: self.daysPerMonth = 30
        self.daysPerMonth = self.sim.userInput['dayspermonth']
        self.daysPerYear= C.monthsPerYear*self.daysPerMonth
        self.runDays= self.sim.userInput['rundays']
        self.burninDays= self.sim.userInput['burnindays']
        self.updateWasteEstimateFreq= self.sim.userInput['wasteestfreq']
        self.defaultShipStartupLatency = self.sim.userInput['defaultshipstartuplatency']
        self.factoryStartupLatency= self.sim.userInput['factorystartuplatency']
        self.factoryOverstockScale= self.sim.userInput['factoryoverstockscale']
        self.discardUnusedVaccine = self.sim.userInput['discardunusedvaccine']
        self.factoryBatchInterval= self.daysPerYear/self.sim.userInput['factoryshipmentsperyear']
        self.defaultPullMeanFrequency= self.sim.userInput['defaultpullmeaninterval']
        self.defaultTruckInterval= self.sim.userInput['defaulttruckinterval']
        self.defaultTruckTypeName= self.sim.userInput['defaulttrucktypename']
        self.autoUpdateThresholdsFlag = self.sim.userInput['autoupdatethresholds']

        self.monthlyReportActivated= False
        if self.sim.userInput['monthlyreports']:
            self.monthlyReportProcess= MonthlyReportProcess(sim,float(self.daysPerMonth),5.0)
        else:
            self.monthlyReportProcess= None

        self.demandModelTuple = self._generateDemandModelTuple(self.daysPerYear,
                                                               sampler=sampler.PoissonSampler())

        if self.sim.perfect:
            for dm in self.demandModelTuple:
                dm.setPerfectCanStore()

        self.levelList = self.sim.userInput['levellist']
        #print "level list is: %s"%self.levelList
        self.centralLevelList = self.sim.userInput['centrallevellist']
        self.clinicLevelList = self.sim.userInput['cliniclevellist']

        ## Just a check to make sure that the above are defined somewhat appropriately
        for cLevel in self.centralLevelList:
            if not cLevel in self.levelList:
                raise RuntimeError("The model's CentralLevelList is not defined correctly as %s is not in the levelList"%cLevel)

        for clLevel in self.clinicLevelList:
            if not clLevel in self.levelList:
                raise RuntimeError("The model's clinicLevelList is not defined correctly as %s is not in the levelList"%clLevel)

        # Info for loss due to breakage [Central Store, Region, Province, District, Clinic]
        lll = len(self.levelList)
        storageBreakage = _createAndExtendList(lll, self.sim.userInput['storagebreakage'], 0.0)
        transitBreakage = _createAndExtendList(lll, self.sim.userInput['transitbreakage'], 0.0)
        self.breakage = zip(storageBreakage, transitBreakage)
        #print "breakage: %s"%self.breakage

        ### These have no business being here
        #self.vizWidths = _createAndExtendList(lll, self.sim.userInput['vizwidths'], 0.1)
        #self.vizShapes = _createAndExtendList(lll, self.sim.userInput['vizshapes'], 'c')

        #print self.vizWidths
        #print self.vizShapes

        # A shipment can request goods that the warehouse cannot provide, because some other shipment
        # has stolen the goods away in the mean time.  If this happens, how long should the shipment be
        # delayed waiting for new goods to arrive before it is simply canceled?
        # NOTE: Must not exactly equal transit time!
        self.orderPendingLifetime= self.sim.userInput['orderpendinglifetime']

        # If a patient arrives at a clinic and there is currently no supply of the vaccine needed, how
        # long should the patient wait before giving up?  During this time (in days) a shipment may arrive,
        # allowing the vaccination to take place.
        self.patientWaitInterval= self.sim.userInput['patientwaitinterval']

        ##################
        # End of info provided via the input file
        ##################

        # Check 'getDefaultSupplier()' below- it is set up to assume
        # only warehouses with idcodes greater than 10000 have a
        # default supplier.  This works for Thailand and Vietnam, but
        # not for Niger.

        self.breakageModelList= [breakagemodel.PoissonBreakageModel(a,b) for a,b in self.breakage]

    def getTotalRunDays(self):
        """
        We sandwich the activation of the reporting process in here for lack of
        anywhere better to put it.
        """
        if self.monthlyReportProcess is not None and not self.monthlyReportActivated:
            self.sim.activate(self.monthlyReportProcess,self.monthlyReportProcess.run())
            self.monthlyReportActivated= True
        return self.getBurninDays() + self.getRunDays()

    def _getsFactory(self,storeDict,code):
        """
        This function should figure out if the specified warehouse should be directly supplied
        by a factory.  If so it should return True; otherwise False.
        """
        wh= storeDict[code]
        return isinstance(wh,Model.CentralWarehouse)

    def isClinic(self,storeDict,code):
        wh= storeDict[code]
        return (isinstance(wh,warehouse.Clinic))

    def _separateVaccines(self,shippableCollection):
        allVC= shippableCollection.copy()
        vaccinesOnlyVC= allVC.splitOut(vaccinetypes.VaccineType, abstractbaseclasses.ShippableType)
        # allVC now contains only the non-vaccines
        return vaccinesOnlyVC, allVC
#         vTuples= []
#         oTuples= []
#         for tp,n in shippableCollection.getTupleList():
#             if isinstance(tp,vaccinetypes.VaccineType):
#                 vTuples.append((tp,n))
#             else:
#                 oTuples.append((tp,n))
#         return self.sim.vaccines.getCollection(vTuples), self.sim.vaccines.getCollection(oTuples)

    def clinicShipQuantityFunc(self,fromW, toW, pullMeanFrequencyDays, timeNow):
        assert(isinstance(toW,warehouse.Clinic))
        # These are 'pull' shipments.  This function may be
        # called at start-up time, before the MonthlyOrderProcesses have
        # installed an instantaneous demand for the downstream clinics.
        vC = toW.getProjectedDemandVC((timeNow,timeNow+pullMeanFrequencyDays))

        #vC= toW.shippingDemandModel.getDemandExpectationVials(toW.getPopServedPC(),
        #                                                 toW.getUseVialsTickInterval(),
        #                                                 pullMeanFrequencyDays,
        #                                                 timeNow=timeNow)
        vC = self.sim.shippables.addPrepSupplies(vC)
        vaccinesOnlyVC, othersVC= self._separateVaccines(vC)
        if self.autoUpdateThresholdsFlag:
            threshVialsVC = vaccinesOnlyVC * 0.25
            threshVialsVC.roundUp()
            fVC,cVC,wVC = toW.calculateStorageFillRatios(threshVialsVC+othersVC)
            threshVialsVC = threshVialsVC * (fVC + cVC + wVC)
            threshVialsVC.roundDown()
            toW.resetLowThresholds(threshVialsVC)
            #print "clinicShipQuantityFunc %s: thresholds reset to %s"%\
            #      (toW.name, [(v.name,n) for v,n in threshVialsVC.items()])
        vaccinesOnlyVC *= 1.25
        vaccinesOnlyVC.roundUp() #yes, round up twice.
        fVC,cVC,wVC= toW.calculateStorageFillRatios(othersVC+vaccinesOnlyVC)
        fillVC= fVC+cVC+wVC
        # a fillVC value of of 0.0 implies toW has no storage, which means it's
        # an attached clinic, which means we shouldn't be dealing with it
        scaledQuantityVC= vaccinesOnlyVC*fillVC
        scaledQuantityVC.roundDown()
        lowVC= scaledQuantityVC \
            - self.sim.shippables.getCollectionFromGroupList([s for s in toW.theBuffer
                                                            if isinstance(s,abstractbaseclasses.Shippable)])
        lowVC.floorZero()
        lowVC += othersVC # we want to *always* order cold boxes
        lowVC = toW.getPackagingModel().applyPackagingRestrictions(lowVC)
        #print "clinicShipQuantityFunc %s: %s"%(toW.name,lowVC)
        #print "    vaccinesOnlyVC was %s"%vaccinesOnlyVC
        #print "    fillVC was %s"%fillVC
        #print "    fVC: %s"%fVC
        #print "    cVC: %s"%cVC
        #print "    wVC: %s"%wVC
        return lowVC

    def clinicShipThresholdFunc(self,toW,pullMeanFrequencyDays):
        assert(isinstance(toW,warehouse.Clinic))
        # These are 'pull' shipments.  This function may be
        # called at start-up time, before the MonthlyOrderProcesses have
        # installed an instantaneous demand for the downstream clinics.
        vC= toW.shippingDemandModel.getDemandExpectationVials(toW.getPopServedPC(),
                                                         toW.getUseVialsTickInterval(),
                                                         pullMeanFrequencyDays)
        vC = self.sim.shippables.addPrepSupplies(vC)

        vaccinesOnlyVC, othersVC= self._separateVaccines(vC)
        vaccinesOnlyVC *= 0.25
        vaccinesOnlyVC.roundUp() #yes, round up twice.
        fVC,cVC,wVC= toW.calculateStorageFillRatios(othersVC+vaccinesOnlyVC)
        fillVC= fVC+cVC+wVC
        # a fillVC value of of 0.0 implies toW has no storage, which means it's
        # an attached clinic, which means we shouldn't be dealing with it
        whatFitsVC= vaccinesOnlyVC*fillVC
        whatFitsVC.roundDown()
        #print "clinicShipThresholdFunc %s: %s"%(toW.name,[(v.name,n) for v,n in whatFitsVC.items()])
        return whatFitsVC

    def warehouseShipQuantityFunc(self,fromW, toW, pullMeanFrequencyDays, timeNow):
        # These are 'pull' shipments.  This function may be
        # called at start-up time, this functions is now using the InstantaneousDemand
        # to get the vial counts below correct.  This means that MonthlyOrder process must
        # be running in order for this to be correct.
        vC = toW.getProjectedDemandVC((timeNow,timeNow+pullMeanFrequencyDays))
        vaccineVialsVC,otherVialsVC= self._separateVaccines(vC)

        if self.autoUpdateThresholdsFlag:
            threshVialsVC = vaccineVialsVC * 0.25
            threshVialsVC.roundUp()
            fVC,cVC,wVC = toW.calculateStorageFillRatios(threshVialsVC+otherVialsVC)
            threshVialsVC = threshVialsVC * (fVC + cVC + wVC)
            threshVialsVC.roundDown()
            toW.resetLowThresholds(threshVialsVC)
            #print "warehouseShipQuantityFunc %s: thresholds reset to %s"%\
            #      (toW.name, [(v.name,n) for v,n in threshVialsVC.items()])
        vaccineVialsVC *= 1.25
        vaccineVialsVC.roundUp()
        fVC,cVC,wVC= toW.calculateStorageFillRatios(vaccineVialsVC+otherVialsVC)
        fillVC= fVC+cVC+wVC
        scaledVaccineVialsVC= vaccineVialsVC*fillVC
        scaledVaccineVialsVC.roundDown()
#         lowVC= (scaledVaccineVialsVC+otherVialsVC) \
#                - self.sim.shippables.getCollectionFromGroupList([s for s in toW.theBuffer
#                                                                if isinstance(s,abstractbaseclasses.Shippable)])
        # Never order non-vaccines
        lowVC= (scaledVaccineVialsVC) \
               - self.sim.shippables.getCollectionFromGroupList([s for s in toW.theBuffer
                                                               if isinstance(s,abstractbaseclasses.Shippable)])
        lowVC.floorZero()
        lowVC = toW.getPackagingModel().applyPackagingRestrictions(lowVC)
        #print "warehouseShipQuantityFunc %s: %s"%(toW.name,lowVC)
        return lowVC

    def warehouseShipThresholdFunc(self, toW, pullMeanFrequencyDays):
        # These are 'pull' shipments.  This function may be
        # called at start-up time, before the MonthlyOrderProcesses have
        # installed an instantaneous demand for the downstream clinics.
        vC= self.demandModelTuple[0].getDemandExpectation(toW.getTotalDownstreamPopServedPC(),
                                                          pullMeanFrequencyDays)
        vaccineDosesVC, otherDosesVC= self._separateVaccines(vC)
        vaccineVialsVC= self._scaleDemandByType(vaccineDosesVC) # includes OVW and rounding up
        otherVialsVC= otherDosesVC # Assumes all non-vaccines are "1 dose per vial"
        #totalVialsVC = vaccineVialsVC+otherVialsVC
        totalVialsVC = vaccineVialsVC # non-vaccines never go in the threshold
        totalVialsVC = self.sim.shippables.addPrepSupplies(totalVialsVC)
        fVC,cVC,wVC= toW.calculateStorageFillRatios(totalVialsVC)
        fillVC= fVC+cVC+wVC
        scaledVaccineVialsVC= vaccineVialsVC*fillVC
        threshVC= scaledVaccineVialsVC*0.25
        # This is to prevent there being no threshold at all
        for v,n in threshVC.items():
            if n > 0.0 and n < 1.0:
                threshVC[v] = 1.0
        threshVC.roundDown()
        threshVC= scaledVaccineVialsVC*0.25
        return threshVC

    def getApproxScalingVC(self,storeDict,code):
        wh= storeDict[code]
        # If we can't actually get the 'tick interval' for the warehouse, we'll just
        # use 90 days, as that's a fairly common inter-shipment interval for upstream
        # warehouses.
        if hasattr(wh,'getUseVialsTickInterval'): interval= wh.getUseVialsTickInterval()
        else: interval= 90.0
        vC = self.demandModelTuple[0].getDemandExpectation(wh.getTotalDownstreamPopServedPC(),
                                                           interval)
        vC = self.sim.shippables.addPrepSupplies(vC)
        return vC

    def _scaleDemandByType(self, shipDosesVC):
        """
        Input is in doses; output in vials rounded up.
        The 'wastage' bit is a hack to implement some estimated
        wastage constants peculiar to Generic.
        """
        shipVialsVC= shipDosesVC*self.sim.vaccines.getDosesToVialsVC()
        scaledTupleList= []
        for v,nVials in shipVialsVC.items():
            wastage = 1.0-self.wastageEstimates[v]
            scaledTupleList.append( (v,int(math.ceil(nVials/wastage))) )
        return self.sim.shippables.getCollection(scaledTupleList)

    def getScheduledShipmentSize(self, fromW, toW, shipInterval, timeNow):
        # The function is called repeatedly, every time a shipment is being set up.
        # The InstantaneousDemand has been set by the MonthlyOrderProcesses of the
        # downstream clinics; it includes any attached clinics but does not include
        # safety stock.
        #demandDownstreamVialsVC= toW.getInstantaneousDemandVC((timeNow,timeNow+shipInterval))            
        demandDownstreamVialsVC= toW.getProjectedDemandVC((timeNow,timeNow+shipInterval))
        #if fromW.idcode == 1:
        #    print "Demand: " + str(demandDownstreamVialsVC)
        vaccineVialsVC,otherVialsVC= self._separateVaccines(demandDownstreamVialsVC)

        # Warehouses try for a buffer stock of 1.25.
        vaccineVialsVC *= 1.25
        # Believe you need a round up here, or the buffer may not get added to the system for small vial counts
        # (e.g. if the number of vials is 3, and then the buffer makes it 3.75, the next set of commands
        # cause it to be 3 rather than 4, which is the right answer.
        vaccineVialsVC.roundUp()

        # This must now be scaled by available space so that we don't end up immediately
        # discarding things on delivery.  Outreach clinics are presumed to have no storage
        # except at the time of treatment (the PVSD arrives with the drugs), so in that case
        # we do not scale by available storage.
#        if isinstance(toW,Model.OutreachClinic):
#            scaledVaccineVialsVC = vaccineVialsVC
#        else:
        suppliers = toW.getSuppliers()
        supplierRoute = suppliers[0][1]
        if supplierRoute['Type']=='askingpush':
            lowVC = vaccineVialsVC
        else:
            fVC,cVC,wVC= toW.calculateStorageFillRatios(vaccineVialsVC)
            fillVC= fVC+cVC+wVC
            scaledVaccineVialsVC= vaccineVialsVC*fillVC
            scaledVaccineVialsVC.roundDown()
    
            onhandVC= self.sim.shippables.getCollectionFromGroupList([s for s in toW.getStore().theBuffer
                                                                    if isinstance(s,abstractbaseclasses.Shippable)])
            lowVC= scaledVaccineVialsVC - onhandVC
        lowVC.floorZero()
        lowVC.roundUp()
        #if fromW.idcode == 1:
        #    print "lowVC = " + str(lowVC)
        #print "shipment %s -> %s"%(fromW,toW.name)
        #print "lowVC: %s"%[(v.name,n) for v,n in lowVC.items()]
        #print "otherVialsVC: %s"%[(v.name,n) for v,n in otherVialsVC.items()]
        #print "fillVC: %s"%[(v.name,n) for v,n in fillVC.items()]
        return toW.getPackagingModel().applyPackagingRestrictions(lowVC + otherVialsVC)

    def getDeliverySize(self, toW, availableVC, shipInterval, timeNow):
        """
        For those rare shipping patterns where the truck may not drop off the full
        size of an order, for example in the VillageReach shipping pattern.  This
        method is called for some particular route types immediately before the
        delivery is actually transferred to toW, and the amount delivered is
        the lesser of the returned VaccineCollection and availableVC.
        """
        
        vc = self.getScheduledShipmentSize(None, toW, shipInterval, timeNow)
        vc.roundUp()
        return vc

    def addedCatchupDemand(self, storeDict, cudemand):
        raise RuntimeError("The addCatchupDemand approach to campaign modeling is deprecated.")

    def _getFactoryProductionVC(self, factory, daysSinceLastShipment, timeNow,
                                daysUntilNextShipment):
        totalShipment = {}
        for prop, targetStore in factory.targetStores:
            if factory.demandType == "Projection":
                ### Get demand in vials as a projection of the population demand
                demandDownstreamVialsVC = targetStore.getProjectedDemandVC((timeNow, timeNow + daysUntilNextShipment))
                #print "Before: {0}".format(demandDownstreamVialsVC)
                scaledTupleList = []
                
                if factory.wasteEstimatesDict:
                    for v,nVials in demandDownstreamVialsVC.items():
                        wastage = 1.0
                        if v.name in factory.wasteEstimatesDict.keys():
                            wastage = 1.0 + float(factory.wasteEstimatesDict[v.name])
                        #print wastage
                        scaledTupleList.append((v, math.ceil(demandDownstreamVialsVC[v]*(wastage))))

                    vaccineVialsTotVC = self.sim.shippables.getCollection(scaledTupleList)
                else:
                    vaccineVialsTotVC = demandDownstreamVialsVC
                #print "After: {0}".format(vaccineVialsTotVC)
                vaccineVialsVC, otherVialsVC = self._separateVaccines(vaccineVialsTotVC)
            elif factory.demandType == "Expectation":
                ### Use the demand expectation in doses and scale it by wastage estimates
                demandDownstreamDosesVC = self.demandModelTuple[0].getDemandExpectation(targetStore.getTotalDownstreamPopServedPC(),
                                                                                        daysUntilNextShipment)
                vaccineDosesVC,otherDosesVC = self._separateVaccines(demandDownstreamDosesVC)

                vaccineD2VVC= vaccineDosesVC*self.sim.vaccines.getDosesToVialsVC()

                scaledTupleList = []
                if factory.wasteEstimatesDict:
                    for v,nVials in vaccineD2VVC.items():
                        wastage = 1.0
                        if v.name in factory.wasteEstimatesDict.keys():
                            wastage =1.0 + float(factory.wasteEstimatesDict[v.name])
                        scaledTupleList.append((v,math.ceil(nVials*wastage)))

                    vaccineVialsVC = self.sim.shippables.getCollection(scaledTupleList)
            else:
                raise RuntimeError("in getFactoryProductionVC, invalid demandType of %s for %s" % (factory.demandType, factory.name))

            #print "getFactoryProductionVC: vaccineVialsVC: " + str([(v.name,n) for v,n in vaccineVialsVC.items()])
            #print factory.overstockScale
            ### Filter by vaccines produced by this factory
            if factory.vaccinesProd is not None:
                for v, n in vaccineVialsVC.items():
                    if v.name not in factory.vaccinesProd:
                        vaccineVialsVC[v] = 0.0
            vaccineVialsVC *= prop * factory.overstockScale
            
            #print "getFactoryProductionVC: vaccineVialsVC: " + str([(v.name,n) for v,n in vaccineVialsVC.items()])
            fVC, cVC, wVC = targetStore.calculateStorageFillRatios(vaccineVialsVC)
            fillVC = fVC + cVC + wVC
            # print factory.name + " getFactoryProductionVC: fillVC: " + str([(v.name,n) for v,n in fillVC.items()])
            scaledVaccineVialsVC = vaccineVialsVC * fillVC
            scaledVaccineVialsVC.roundDown()
            onhandVC = self.sim.shippables.getCollectionFromGroupList([s for s in targetStore.getStore().theBuffer
                                                                if isinstance(s, abstractbaseclasses.Shippable)])
            lowVC = scaledVaccineVialsVC - onhandVC
            lowVC.floorZero()
            lowVC = targetStore.getPackagingModel().applyPackagingRestrictions(lowVC)
            lowVC.roundUp()
            totalShipment[targetStore] = lowVC
            #print "getFactoryProductionVC for %s: Actual amount: %s" % \
            #    (targetStore.name, [(v.name, n) for v, n in lowVC.items()])
        #print "Total Shipment = " + str(totalShipment)
        return totalShipment

    def getFactoryProductionFunction(self, storeDict, code, alwaysTrue=False):
        if alwaysTrue:
            return self._getFactoryProductionVC
        if not self._getsFactory(storeDict, code): return None
        else: return self._getFactoryProductionVC

    def getFactoryStartupLatency(self,storeDict,code):
        """
        If the given Warehouse should have an attached Factory, return
        the delay in days before the factory's first shipment is delivered.
        If the given Warehouse has no factory (in which case getFactoryYearlyProduction
        will have returned None), this function will not be called or its return value
        will be ignored.
        """
        return self.factoryStartupLatency

    def getFactoryOverStockScale(self, storeDict, code):
        """
        If the given Warehouse should have an attached Factory, return
        the scale for defining the buffer stock taht should be applied.
        Should return None if this Warehouse has no factory.
        """
        return self.factoryOverstockScale

    def getModelMonthlyOrderProcess(self):
        return MonthlyOrderProcess

    def getTruckInterval(self,storeDict,code):
        raise RuntimeError("getTruckInterval is deprecated- use the ShipIntervalDays field of the Routes file")

    def getShipStartupLatency(self,storeDict,code):
        if self.defaultShipStartupLatency is None:
            raise RuntimeError("getShipStartupLatency is deprecated- use the StartupLatencyDays field of the Routes file")
        else:
            return self.defaultShipStartupLatency

    def getOrderPendingLifetime(self,storeDict,code):
        return self.orderPendingLifetime

    def getShipInterval(self,storeDict,code):
        raise RuntimeError("getShipInterval is deprecated- use the ShipIntervalDays field of the Routes file")

    def getPullMeanFrequency(self,storeDict,code):
        raise RuntimeError("getPullMeanFrequency is deprecated- use the PullOrderAmountDays field of the Routes file")

    def getPullControlFuncs(self,storeDict,code):
        if self.isClinic(storeDict,code):
            tFunc= self.clinicShipThresholdFunc
            qFunc= self.clinicShipQuantityFunc
        else:
            tFunc= self.warehouseShipThresholdFunc
            qFunc= self.warehouseShipQuantityFunc
        return (tFunc,qFunc)

    def getDefaultSupplier(self,storeDict,code):
        """
        This implements the two main schemes of encoding supplier/client relationships
        in id codes.
        """
        if code>=1000000:
            # Original deprecated Niger scheme: relationships are encoded in digit pairs
            clinicCode= code % 100
            code /= 100
            districtCode= code % 100
            code /= 100
            regionCode= code % 100
            if clinicCode == 0:
                if districtCode ==  0:
                    if regionCode == 0:
                        return None # This is the top of the tree
                    else:
                        return long("%d%02d%02d%02d"%(1,0,0,0))
                else:
                    return long("%d%02d%02d%02d"%(1,regionCode,0,0))
            else:
                return long("%d%02d%02d%02d"%(1,regionCode,districtCode,0))
        else:
            if code>10000:
                candidate= code%10000
                if candidate in storeDict: return candidate
                else: return None
            else: return None

    def getDefaultTruckInterval(self,fromWH,toWH):
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,
        return the minimum number of days between departures to be used
        to implement the implied 'pull' shipment.
        """
        return self.defaultTruckInterval

    def getDefaultPullMeanFrequency(self,storeDict,code):
        return self.defaultPullMeanFrequency

    def getDefaultTruckTypeName(self,fromWH,toWH):
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,
        return the name of the truck type to be used to implement the
        implied 'pull' shipment to be created.
        """
        return self.defaultTruckTypeName

    def getUseVialsProcess(self,storeDict,code):
        wh= storeDict[code]
        if self.isClinic(storeDict,code):
            totalLatency= wh.getUseVialsLatency()
            tickInterval= wh.getUseVialsTickInterval()
            patientWaitInterval= self.patientWaitInterval
            if self.discardUnusedVaccine:
                if isinstance(wh,Model.SurrogateClinic):
                    # Surrogates never follow this policy, as they are generally
                    # substituting for whole sub-trees of the shipping graph.
                    useVials= warehouse.UseVialsSilently(wh,
                                                         tickInterval,
                                                         patientWaitInterval,
                                                         C.useVialPriority,
                                                         totalLatency)
                elif isinstance(wh,Model.OutreachClinic):
                    useVials= warehouse.UseOrRecycleVials(wh,
                                                          tickInterval,
                                                          patientWaitInterval,
                                                          C.useVialPriority,
                                                          totalLatency)
                else:
                    useVials= warehouse.UseOrDiscardVials(wh,
                                                          tickInterval,
                                                          patientWaitInterval,
                                                          C.useVialPriority,
                                                          totalLatency)
            else:
                if isinstance(wh,Model.SurrogateClinic):
                    useVials= warehouse.UseVialsSilently(wh,
                                                         tickInterval,
                                                         patientWaitInterval,
                                                         C.useVialPriority,
                                                         totalLatency)
                elif isinstance(wh,Model.OutreachClinic):
                    useVials= warehouse.UseOrRecycleVials(wh,
                                                          tickInterval,
                                                          patientWaitInterval,
                                                          C.useVialPriority,
                                                          totalLatency)
                else:
                    useVials= warehouse.UseVials(wh,
                                                 tickInterval,
                                                 patientWaitInterval,
                                                 C.useVialPriority,
                                                 totalLatency)
            return useVials
        else:
            return None

    def _getPackagingPairs(self, rec):
        pairs = []
        for k,v in rec.items():
            if self.sim.shippables.validTypeName(k):
                if v is None or v=='': continue
                elif k in ['CATEGORY','FUNCTION','NAME','idcode','Conditions']:
                    raise RuntimeError('Input files have defined a shippable item with the forbidden name %s'%k)
                elif self.sim.packaging.validTypeName(v):
                    #print 'Packaging: at %s(%d), %s uses %s'%(rec['NAME'],rec['idcode'],k,v)
                    pairs.append((k,v))
                else:
                    raise RuntimeError("Stores file specifies that %s keeps %s in %s, but %s is not a package type"%\
                                       (rec['NAME'],k,v,v))
        return [(self.sim.shippables.getTypeByName(k),self.sim.packaging.getTypeByName(v)) for k,v in pairs]

    def factoryFromRec(self, sim, rec, factoryProdFunc, factoryWasteEstRecs, 
                      trackThis=None, trackingShipmentNumber=0):

        from util import parseInventoryString

        # # Check if store is done
        if len(sim.storeDict) == 0:
            raise RuntimeError("Warehouses must be initialized before Factories are parsed")

        assert 'idcode' in rec, "Factories table lacks the column 'idcode'"
        idcode = rec['idcode']
        assert 'Name' in rec, "Factories table lacks the column 'Name'"
        name = rec['Name']
        assert 'Targets' in rec, "Factories table lacks the column 'Targets'"
        targetsString = rec['Targets']
        assert 'Vaccines' in rec, "Factories table lacks the column 'Vaccines'"
        vaccinesString = rec['Vaccines']
        startupLatencyDays = float(rec['StartupLatencyDays'])
        interval = float(rec['ProductionIntervalDays'])
        overscale = float(rec['OverstockScale'])

        # # Parse Targets

        if isinstance(targetsString, int):
            targets = [(1.0, self.sim.storeDict[targetsString])]
        else:
            targetsTuples = parseInventoryString(targetsString, True)
            # Vet the targets
            for prop, tId in targetsTuples:
                if long(tId) not in sim.storeDict.keys():
                    raise RuntimeError("Factory record for %s has a target ID that is not in the model: %s" % (name, tId))
            targets = [(x[0], self.sim.storeDict[long(x[1])]) for x in targetsTuples]
            
        if vaccinesString == "All":
            vaccines = None
        else:
            vaccineTuples = parseInventoryString(vaccinesString)

            # ## vet this list
            for prod, vaccName in vaccineTuples:
                if vaccName not in sim.vaccines.getActiveTypeNames():
                    raise RuntimeError("Factory record for %s has a vaccine name that is not in the model: %s" % (name, vaccName))

            vaccines = [x[1] for x in parseInventoryString(vaccinesString)]

        wasteEstDict = None
        if factoryWasteEstRecs is not None:
            wasteEstDict = {}
            for wRec in factoryWasteEstRecs:
                print str(wRec)
                if wRec['FactoryID'] == idcode:
                    if wRec['VaccineName'] not in sim.vaccines.getActiveTypeNames():
                        continue
                        ### Thought better about this, if it is not there, just ignore
                        #raise RuntimeError("Factory Rec %s has vaccine %s in waste estimate file %s that is not valid" % (name, rec['VaccineName'], wasteEstFileName))
                    if vaccines is not None and wRec['VaccineName'] not in vaccines:
                        continue
                        ### Thought better about this, if it is not produced, just ignore
                        #raise RuntimeError("Factory Rec %s has vaccine %s in waste estimate file %s that it doesn't produce" % (name, rec['VaccineName'], wasteEstFileName))
                    wasteEstDict[wRec['VaccineName']] = wRec['WastageFraction']

        acceptableDT = ['Expectation', 'Projection']

        demandType = rec['DemandType']
        if demandType not in acceptableDT:
            raise RuntimeError("Factory record for %s has an unacceptable ")
        return warehouse.Factory(targets, interval,
                                 factoryProdFunc, vaccineProd=vaccines, startupLatency=startupLatencyDays,
                                 name=name, overstockScale=overscale, wasteEstimates=wasteEstDict,
                                 demandType=demandType)

    def warehouseOrClinicFromRec(self, sim, rec, expectedType,
                                 recordTheseStoresDict={},
                                 recordTheseVaccineNames=[]):
        assert 'CATEGORY' in rec, "Stores table lacks the column 'CATEGORY'"
        category= rec['CATEGORY']
        assert 'FUNCTION' in rec, "Stores table lacks the column 'FUNCTION'"
        function = rec['FUNCTION']
        assert 'NAME' in rec, "Stores table lacks the column 'NAME'"
        name= rec['NAME']
        assert 'idcode' in rec, "Stores table lacks the column 'idcode'"
        code= long(rec['idcode'])
        #print "building warehouse %s: %s"%(category,func,name,code)
        targetPopPC= self._peopleCollectionFromTableRec(rec)
        #name= "%s_%s"%(name,code)
        if 'Conditions' in rec and rec['Conditions'] != "": conditions = rec['Conditions']
        else: conditions = None

        isCentral = False
        if category in self.centralLevelList:
            isCentral = True

        if category in self.clinicLevelList:
            assert function.lower() in ['administration','surrogate','outreach'],\
                "Store %s %ld is at Clinic level but not Administration, Surrogate, or Outreach"%(name,code)
        brModel= self.breakageModelList[self.levelList.index(category)]

        # Function information must be consistent with expectedType.
        isClinic = issubclass(expectedType,warehouse.Clinic)
        isSurrogate = False
        isOutreach = False
        if function.lower()=="surrogate":
            isClinic = True
            isSurrogate = True
            isOutreach = False
            assert issubclass(Model.SurrogateClinic,expectedType), \
                'Location %s(%ld) is marked as a Surrogate but is not used like a SurrogateClinic'%(name, code)
        elif function.lower() == "administration":
            isClinic = True
            isSurrogate = False
            isOutreach = False
        elif function.lower() == "outreach":
            isClinic = True
            isSurrogate = False
            isOutreach = True
        elif function.lower() == "distribution":
            isClinic = False
            isSurrogate = False
            assert not issubclass(expectedType, warehouse.Clinic), \
                'Location %s(%ld) is marked as a distribution facility but is not used like a Warehouse'%(name, code)
        else:
            raise RuntimeError("Unknown FUNCTION %s for %s(%ld)"%(function,name,code))

        if 'Device Utilization Rate' in rec and rec['Device Utilization Rate'] != "":
            sUF = float(rec['Device Utilization Rate'])
        else:
            sUF = 1.0

        latitude = rec.safeGetFloat(['Latitude','WHO_Lat','Pop_Lat'], 0.0, ignore=0.0)
        longitude = rec.safeGetFloat(['Longitude','WHO_Long','Pop_Long'], 0.0, ignore=0.0)

        if rec.has_key('UseVialsLatency'):
            clinicLatency = rec.safeGetFloat(['UseVialsLatency'],0.0)
        else:
            raise RuntimeError('The Stores file for this model must have a UseVialsLatency column')
        if rec.has_key('UseVialsInterval'):
            clinicInterval = rec.safeGetFloat(['UseVialsInterval'],0.0)
        else:
            raise RuntimeError('The Stores file for this model must have a UseVialsInterval column')
        if isClinic:
            if clinicInterval in [None,'NA','',0.0] or clinicInterval<0.0:
                raise RuntimeError('The interval between sessions of clinic %s %ld is invalid'%(name,code))

        w= None
        inventory = self._inventoryFromTableRec(rec, sUF)
        inventoryOrg = None
        if self.sim.perfect== True:
            inventoryOrg= copy(inventory)
            inventory = self._perfectInventoryFromOrgInventory(inventoryOrg)

        storageSpace= []
        for t in [g for g in inventory if isinstance(g,abstractbaseclasses.CanStore)]:
            storageSpace += [t.getType()] # CanStore instances are always singletons
        storageSC= self._getTotalVolumeSC(storageSpace)
        totalStorage= sim.storage.getTotalRefrigeratedVol(storageSC)
        if issubclass(expectedType, warehouse.AttachedClinic) and totalStorage != 0.0:
            raise RuntimeError('The Stores file information for %s says it has storage, but it is an Attached Clinic'%name)
        coolStorage= sim.storage.getTotalCoolVol(storageSC)

        packagingInfoList = self._getPackagingPairs(rec)
        if len(packagingInfoList) == 0:
            packagingModel = packagingmodel.SimplePackagingModel()
        else:
            packagingModel = packagingmodel.ListPackagingModel(packagingInfoList)

        if (( targetPopPC is None or targetPopPC.totalCount()==0) and totalStorage==0.0):
            return None # dead warehouse
        elif isClinic:
            if isSurrogate:
                #print w.category, w.function, w.name
                if conditions is not None:
                    print "***Warning*** Conditions set for surrogate clinic %s(%ld) will be ignored"%(name,code)
                w= Model.SurrogateClinic(sim,None,
                                         targetPopPC,
                                         name=name, breakageModel=brModel, demandModel=self.demandModelTuple,
                                         useVialsLatency=clinicLatency, useVialsTickInterval= clinicInterval)
            elif isOutreach:
                w= Model.OutreachClinic(sim, sim.shippables.getActiveTypes(),
                                        storagetypes.storageTypes,
                                        inventory,
                                        targetPopPC,
                                        func=function,category=category,name=name,breakageModel=brModel,
                                        demandModel=self.demandModelTuple,
                                        packagingModel=packagingModel,
                                        storageModel=storagemodel.StorageModel(True),
                                        latitude=latitude,longitude=longitude,
                                        useVialsLatency = clinicLatency, useVialsTickInterval= clinicInterval,
                                        conditions = conditions,origCapacityInfoOrInventory=inventoryOrg)
            elif coolStorage==0.0 or issubclass(expectedType, warehouse.AttachedClinic):
                # This is an attached clinic.
                if conditions is not None:
                    print "***Warning*** Conditions set for attached clinic %s(%ld) will be ignored"%(name,code)
                w= warehouse.AttachedClinic(sim, None,
                                            targetPopPC,
                                            name=name, breakageModel=brModel, demandModel= self.demandModelTuple,
                                            useVialsLatency=clinicLatency,
                                            useVialsTickInterval=clinicInterval)

            else:
                # This is a clinic
                w= warehouse.Clinic(sim, sim.shippables.getActiveTypes(),
                                    storagetypes.storageTypes,
                                    inventory,
                                    targetPopPC,
                                    func=function,category=category,name=name,breakageModel=brModel,
                                    demandModel=self.demandModelTuple,
                                    packagingModel=packagingModel,
                                    storageModel=storagemodel.StorageModel(True),
                                    latitude=latitude,longitude=longitude,
                                    useVialsLatency = clinicLatency, useVialsTickInterval= clinicInterval,
                                    conditions = conditions,origCapacityInfoOrInventory=inventoryOrg)
                #print "Using " + str(clinicInterval) + " " + str(clinicLatency)
        else:
            # This is a warehouse
            targetPopPC= self.sim.people.getCollection() # These don't have an actual local target pop

            if isCentral:
                w= Model.CentralWarehouse(sim,sim.shippables.getActiveTypes(),
                                          storagetypes.storageTypes,
                                          inventory,
                                          targetPopPC,
                                          func=function,category=category,name=name,
                                          breakageModel=brModel,
                                          packagingModel=packagingModel,
                                          storageModel=storagemodel.StorageModel(False),
                                          latitude=latitude,longitude=longitude, conditions=conditions,
                                          origCapacityInfoOrInventory=inventoryOrg)
            else:
                w= warehouse.Warehouse(sim,sim.shippables.getActiveTypes(),
                                       storagetypes.storageTypes,
                                       inventory,
                                       targetPopPC,
                                       func=function,category=category,name=name,
                                       breakageModel=brModel,
                                       packagingModel=packagingModel,
                                       storageModel=storagemodel.StorageModel(False),
                                       latitude=latitude, longitude=longitude, conditions=conditions,
                                       origCapacityInfoOrInventory=inventoryOrg)

        #print w.category,w.name
        w.setNoteHolder(sim.notes.createNoteHolder())
        w.noteHolder.addNote({"name":name,"code":code,
                              "category":category, "function":function,
                              #"ClassName":w.__class__.__name__
                              })
        for tp,vol in storageSC.items():
                    w.noteHolder.addNote({(tp.name+"_vol"):vol/C.ccPerLiter})

        # Attach the idcode to the warehouse, for convenience later.
        w.idcode= code
        w.runningAveQ = None
        w.runningAveVC = None
        return w


