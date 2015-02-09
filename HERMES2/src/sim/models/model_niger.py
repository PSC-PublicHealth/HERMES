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



__doc__ = """ model_niger.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id$"

import sys, os, getopt, types, math
from collections import deque

import constants as C
import abstractbaseclasses
import storagetypes
import recorders
import vaccinetypes
import trucktypes
import peopletypes as pt
from noteholder import NoteHolderGroup
import warehouse
import sampler
import demandmodel
import breakagemodel
import model
import csv_tools

class MonthlyReportProcess(warehouse.PeriodicProcess):
    def __init__(self, sim, interval, startupLatency):
        warehouse.PeriodicProcess.__init__(self, sim, "MonthlyReportProcess", interval, startupLatency)
        self.counter = 0 
    def cycle(self, timeNow):
        nameRoot = 'report_%03d' % self.counter
        print "\nWriting %s" % nameRoot
        self.sim.syncStatistics()
        self.sim.checkSummary(nameRoot, clear=True, graph=False)
        self.counter += 1

class Model(model.Model):

    def __init__(self, sim):
        model.Model.__init__(self, sim)
        self.daysPerMonth = 28
        self.daysPerYear = C.monthsPerYear * self.daysPerMonth
        
        #self.storageUtilFactor = [1.0, 1.0, 1.0, 1.0]
        # waste due to breakage
        #self.breakage = [(0.01, 0.01), (0.01, 0.01), (0.01, 0.01), (0.01, 0.01)]
        self.breakage = [(0.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0)]
        self.runDays = self.sim.userInput['rundays']
        self.burninDays = self.sim.userInput['burnindays']
        
        ## Default file names for this model -- To Be Deprecated
        #lotsOfSpace= 1000000000.0; # used for room temp storage
        
        self.factoryBatchInterval = self.daysPerYear / 2.0
        #self.centralStoreShipInterval = self.daysPerYear / 4.0
        #self.regionalStoreShipInterval = self.daysPerYear / 12.0
        #self.districtStoreShipInterval = self.daysPerYear / 12.0
        self.reportingInterval = 1
        self.orderPendingLifetime = 1.1 # must not exactly equal transit time!
        self.patientWaitInterval = 0.3
        self.clinicTickInterval = 1.0
        self.clinicStartupLatency = self.burninDays # allow fill before customers arrive
        
        self.pullMeanFrequencyDays = self.daysPerMonth
        self.nTrucks = 695
        
        self.factoryOverstockScale = 1.5 / 1.25
        
        self.demandModel = self._generateDemandModel(self.daysPerYear, sampler=None)
        
        self.breakageModelList = [breakagemodel.PoissonBreakageModel(a, b) for a, b in self.breakage]
            
        self.activeVaccineTypes = [ "N_Tuberculosis",
                                   "N_Tetanus_Toxoid",
                                   "N_Measles",
                                   "N_Oral Polio",
                                   "N_Yellow Fever",
                                   "N_DTP-HepB-Hib liquid",
                                   "N_Pneumococcal13",
                                   "N_RotavirusV5",
                                   "N_RotavirusV4",
                                   "N_MenAfriVac"
                                   ]
    

        self.truckCounts = self._loadTruckCounts()
        
#        self.predictedOVWR = { "N_Tuberculosis":0.8526,
#                              "N_DTP":0.3400,
#                              "N_Tetanus_Toxoid":0.0017,
#                              "N_Measles":0.7126,
#                              "N_Measles-unidose":0.0,
#                              "N_Measles-twodose":0.2100,
#                              "N_Measles-fivedose":0.5600,
#                              "N_Oral Polio":0.0033,
#                              "N_Yellow Fever":0.7060,
#                              "N_DTP-HepB-Hib liquid":0.0,
#                              "N_RotavirusV5":0.0,
#                              "N_Pneumococcal13":0.0,
#                              "N_RotavirusV4":0.0,
#                              "N_MenAfriVac":0.67
#                              }
        
        # Uncomment to produce monthly reports
        self.monthlyReportProcess = None
        #self.monthlyReportProcess= MonthlyReportProcess(sim,28.0,5.0)
        self.monthlyReportActivated = False
        
    @staticmethod
    def decomposeId(code):
        raise RuntimeError("decomposeID has been deprecated in the NewNiger model")
 
    @staticmethod
    def composeId(regionCode, districtCode, clinicCode):
        raise RuntimeError("composeID has been deprecated in the NewNiger model")


    def _getsFactory(self, storeDict, code):
        if code != 1: return None
        return code  # only the central store

    def _isClinic(self, storeDict, code):
        wh= storeDict[code]
        return (isinstance(wh,warehouse.Clinic) or isinstance(wh,warehouse.AttachedClinic))
    
    def clinicShipQuantityFunc(self,fromW, toW, pullMeanFrequencyDays, timeNow):
        assert(isinstance(toW,warehouse.Clinic))
        vC= toW.shippingDemandModel.getDemandExpectation(toW.getPopServedPC(),
                                                         self.clinicTickInterval)
        vC *= self.sim.vaccines.getDosesToVialsVC()
        vC.roundUp()
        vC = self.sim.shippables.addPrepSupplies(vC)
        vaccinesOnlyVC= vC.splitOut(vaccinetypes.VaccineType)
        # vC now contains only the non-vaccines
        vaccinesOnlyVC *= 1.25*(pullMeanFrequencyDays/self.clinicTickInterval)
        vaccinesOnlyVC.roundUp() #yes, round up twice.
        fVC,cVC,wVC= toW.calculateStorageFillRatios(vC+vaccinesOnlyVC)
        fillVC= fVC+cVC+wVC
        #print "%s: %s"%(toW.name,fillVC)
        # a fillVC value of of 0.0 implies toW has no storage, which means it's
        # an attached clinic, which means we shouldn't be dealing with it
        scaledQuantityVC= vaccinesOnlyVC*fillVC
        scaledQuantityVC.roundDown()
        lowVC= scaledQuantityVC - self.sim.vaccines.getCollectionFromGroupList(toW.theBuffer)
        lowVC.floorZero()
        lowVC += vC # we want to *always* order cold boxes
        return lowVC

    def clinicShipThresholdFunc(self,toW,pullMeanFrequencyDays):
        assert(isinstance(toW,warehouse.Clinic))
        vC= toW.shippingDemandModel.getDemandExpectation(toW.getPopServedPC(),
                                                         self.clinicTickInterval)
        vC *= self.sim.vaccines.getDosesToVialsVC()
        vC.roundUp()
        vC = self.sim.shippables.addPrepSupplies(vC)
        vaccinesOnlyVC= vC.splitOut(vaccinetypes.VaccineType)
        vaccinesOnlyVC *= 0.25*(pullMeanFrequencyDays/self.clinicTickInterval)
        vaccinesOnlyVC.roundUp() #yes, round up twice.
        fVC,cVC,wVC= toW.calculateStorageFillRatios(vC+vaccinesOnlyVC)
        whatFitsVC= vaccinesOnlyVC*(fVC+cVC+wVC)
        threshVC= whatFitsVC
        threshVC.roundDown()

        return threshVC

    def warehouseShipQuantityFunc(self,fromW, toW, pullMeanFrequencyDays, timeNow):
        vC= self.demandModel.getDemandExpectation(toW.getTotalDownstreamPopServedPC(),
                                                   self.clinicTickInterval)
        vC *= self.sim.vaccines.getDosesToVialsVC()
        vC = self.sim.shippables.addPrepSupplies(vC)
        vaccinesOnlyVC= vC.splitOut(vaccinetypes.VaccineType)
        #print "Wasteage = " + str(self.wastageEstimates["N_MenAfriVac"])
        tupleList= [(v,
                     math.ceil(1.25*rate \
                               *(pullMeanFrequencyDays/self.clinicTickInterval) \
                               /(1.0-float(self.wastageEstimates[v]))))
                    for v,rate in vaccinesOnlyVC.items()]
        orderToQuantityVC= self.sim.vaccines.getCollection(tupleList)
        orderToQuantityVC.roundUp()
        fVC,cVC,wVC= toW.calculateStorageFillRatios(orderToQuantityVC)
        fillVC= fVC+cVC+wVC
        #print "%s: %s"%(toW.name,fillVC)
        scaledQuantityVC= orderToQuantityVC*fillVC
        scaledQuantityVC.roundDown()
        lowVC= (vC+scaledQuantityVC) \
               - self.sim.vaccines.getCollectionFromGroupList(toW.theBuffer)
        lowVC.floorZero()
        return lowVC

    def warehouseShipThresholdFunc(self,toW,pullMeanFrequencyDays):
        vC= self.demandModel.getDemandExpectation(toW.getTotalDownstreamPopServedPC(),
                                                  self.clinicTickInterval)
        vC *= self.sim.vaccines.getDosesToVialsVC()
        vC = self.sim.shippables.addPrepSupplies(vC)
        vaccinesOnlyVC= vC.splitOut(vaccinetypes.VaccineType)
        tupleList= [(v,
                     math.ceil(n) \
                     *(pullMeanFrequencyDays/self.clinicTickInterval) \
                     /(1.0-float(self.wastageEstimates[v])))
                    for v,n in vaccinesOnlyVC.items()]
        whatWeWantToOrderVC= self.sim.vaccines.getCollection(tupleList)
        fVC,cVC,wVC= toW.calculateStorageFillRatios(whatWeWantToOrderVC)
        whatFitsVC= whatWeWantToOrderVC*(fVC+cVC+wVC)
        threshVC= whatFitsVC*0.25
        threshVC.roundDown()
        return threshVC

    def getScheduledShipmentSize(self,fromW, toW, shipInterval,timeNow):
        vC= self.demandModel.getDemandExpectation(toW.getTotalDownstreamPopServedPC(),
                                                  shipInterval)
        vaccineDosesVC= vC.splitOut(vaccinetypes.VaccineType)
        vaccineVialsTupleList= [(v,int(1.25*n/(v.getNDosesPerVial()
                                               *(1.0-float(self.wastageEstimates[v])))
                                       ))
                                for v,n in vaccineDosesVC.getTupleList()]
        vaccineVialsVC= self.sim.vaccines.getCollection(vaccineVialsTupleList)
        vaccineVialsVC = self.sim.shippables.addPrepSupplies(vaccineVialsVC)
        vC = self.sim.shippables.addPrepSupplies(vC)
        # So VaccineVialsVC now contains vaccines, and vC contains non-vaccines.
        # The latter always have count=1, so there is no difference between doses and 
        # vials.
        if isinstance(toW,warehouse.Clinic):
            # We are functionally at district level, so we will be supplying any
            # moving fridges and we expect them to be used in outgoing shipments
            whatWeWantToOrderVC= vaccineVialsVC+vC
            fVC,cVC,wVC= toW.calculateStorageFillRatios(whatWeWantToOrderVC+vC)
            whatFitsVC= whatWeWantToOrderVC*(fVC+cVC+wVC)
            whatFitsVC.roundDown()
            lowVC= whatFitsVC - self.sim.vaccines.getCollectionFromGroupList(toW.theBuffer)
            lowVC.floorZero()
            return lowVC+vC
        else:
            # We are above district, possibly supplying district.  But we will
            # never use or deliver moving fridges.
            whatWeWantToOrderVC= vaccineVialsVC
            fVC,cVC,wVC= toW.calculateStorageFillRatios(whatWeWantToOrderVC)
            whatFitsVC= whatWeWantToOrderVC*(fVC+cVC+wVC)
            whatFitsVC.roundDown()
            lowVC= whatFitsVC - self.sim.vaccines.getCollectionFromGroupList(toW.theBuffer)
            lowVC.floorZero()
            return lowVC
            
    def getApproxScalingVC(self, storeDict, code):
#        raise RuntimeError("getApproxScalingVC has been deprecated in the new Niger Model")
        wh = storeDict[code]
        tickInterval = 28.0
        vC = self.demandModel.getDemandExpectation(wh.getTotalDownstreamPopServedPC(),
                                                     tickInterval)
        vC = self.sim.shippables.addPrepSupplies(vC)
        return vC

    def _getFactoryProductionVC(self, factory, daysSinceLastShipment, timeNow,
                               daysUntilNextShipment):
        totalVC= self.getScheduledShipmentSize(None,factory.targetStore,
                                                daysUntilNextShipment, timeNow)
        vaccineVC= totalVC.splitOut(vaccinetypes.VaccineType)
        scaledVC= vaccineVC * self.factoryOverstockScale
        scaledVC.roundUp()
        return scaledVC # Factory is never to deliver anything but vaccines
    
    def getFactoryProductionFunction(self, storeDict, code):
        if not self._getsFactory(storeDict, code): return None
        else: return self._getFactoryProductionVC
        
    def getShipInterval(self, storeDict, code):
        raise RuntimeError("getShipInterval is superceded by the route file for New NigerModel")

    def getShipStartupLatency(self, storeDict, code):
        return 0.0

    def getOrderPendingLifetime(self, storeDict, code):
        return self.orderPendingLifetime

    def getTruckInterval(self, storeDict, code):
        raise RuntimeError("getTruckInterval is superceded by the routes file in the New NigerModel")
        #regionCode, districtCode, clinicCode = self.decomposeId(code)

    def getPullControlFuncs(self, storeDict, code):
        if self._isClinic(storeDict, code):
            tFunc = self.clinicShipThresholdFunc
            qFunc = self.clinicShipQuantityFunc
        else:
            tFunc = self.warehouseShipThresholdFunc
            qFunc = self.warehouseShipQuantityFunc
        return (tFunc, qFunc)

    def getPullMeanFrequency(self,storeDict,code):
        return self.pullMeanFrequency

    def getDefaultPullMeanFrequency(self,storeDict,code):
        return self.pullMeanFrequency

    def getDefaultSupplier(self, storeDict, code):
        if code == 1:
            return None 
        if isinstance(storeDict[code],warehouse.AttachedClinic):
            return code % 100000
    @staticmethod
    def getDefaultTruckTypeName(fromWH, toWH):
        raise RuntimeError("getDefaultTruckTypeName is deprecated in the new NigerModel")
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,
        return the name of the truck type to be used to implement the
        implied 'pull' shipment to be created.
        """
        #return "N_vaccine_carrier"

    @staticmethod
    def getDefaultTruckInterval(fromWH, toWH):
        raise RuntimeError("getDefaultTruckInterval is deprecated in the new NigerModel")
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,
        return the minimum number of days between departures to be used
        to implement the implied 'pull' shipment.
        """
        #return 7.0

    def getUseVialsProcess(self, storeDict, code):
        wh = storeDict[code]
        if self._isClinic(storeDict, code):
            totalLatency = self.clinicStartupLatency
            tickInterval = self.clinicTickInterval
            patientWaitInterval = self.patientWaitInterval
            useVials = warehouse.UseVials(wh,
                                         tickInterval,
                                         patientWaitInterval,
                                         C.useVialPriority,
                                         totalLatency)
            return useVials
        else:
            return None
        
    def warehouseOrClinicFromRec(self,sim,rec,expectedType,
                                 recordTheseStoresDict={},
                                 recordTheseVaccineNames=[]):
        name= rec['NAME']
        code= long(rec['idcode'])
        category = rec['CATEGORY']
        function  = rec['FUNCTION']
        name = rec['NAME']
        code = long(rec['idcode'])

        #print "building warehouse %s: %s"%(name,code)
        #regionCode,districtCode,clinicCode= Model.decomposeId(code)
#        if clinicCode==0:
#            targetPopPC= None
#        else:
        targetPopPC= self._peopleCollectionFromTableRec(rec)
            
        if category == "Central":
            brModel = self.breakageModelList[0]
        elif category == "Region":
            brModel = self.breakageModelList[1]
        elif category == "District":
            brModel = self.breakageModelList[2]
        elif category == "Integrated Health Center":
            brModel = self.breakageModelList[3]
        
        isClinic = False
        if function == "Administration":
            isClinic = True

        if rec.has_key('WHO_Lat') and rec['WHO_Lat']!=0.0:
            latitude= rec['WHO_Lat']
        elif rec.has_key('Pop_Lat') and rec['Pop_Lat']!=0.0:
            latitude= rec['Pop_Lat']
        else:
            latitude= 0.0
        if rec.has_key('WHO_Long') and rec['WHO_Long']!=0.0:
            longitude= rec['WHO_Long']
        elif rec.has_key('Pop_Long') and rec['Pop_Long']!=0.0:
            longitude= rec['Pop_Long']
        else:
            longitude= 0.0
        if rec.has_key('useVialsLatency'):
            clinicLatency = rec['UseVialsLatency']
        else:
            clinicLatency = self.clinicStartupLatency
        if rec.has_key('useVialsInterval'):
            clinicInterval = rec['UseVialsInterval']
        else:
            clinicInterval = self.clinicTickInterval

        sUF = float(rec['Device Utilization Rate'])
        
        inventory= self._inventoryFromTableRec(rec,sUF)
        storageSpace= []
        for t,n in [(g.getType(),g.getCount()) for g in inventory if isinstance(g,abstractbaseclasses.CanStore)]:
            storageSpace += n*[t]
        storageSC= self._getTotalVolumeSC(storageSpace)
        totalStorage= sim.storage.getTotalRefrigeratedVol(storageSC)
        if issubclass(expectedType, warehouse.AttachedClinic) and totalStorage>0.0:
            raise RuntimeError('The Stores file information for %s says it has storage, but it is an Attached Clinic'%wh.name)
        coolStorage= sim.storage.getTotalCoolVol(storageSC)
        if not isClinic:
            # This is a warehouse
            targetPopPC = sim.people.getCollection() # These don't have an actual local target pop
            if coolStorage==0.0:
                return None # dead warehouse
            else:
                w = warehouse.Warehouse(sim, sim.vaccines.getActiveTypes(),
                                       storagetypes.storageTypes,
                                       inventory,
                                       targetPopPC,
                                       name=name, breakageModel=brModel,
                                       latitude=latitude, longitude=longitude)
        else:
            if coolStorage==0.0 or issubclass(expectedType,warehouse.AttachedClinic):
                if targetPopPC.totalCount()==0:
                    return None # dead warehouse
                else:
                    w= warehouse.AttachedClinic(sim,None,
                                                targetPopPC,
                                                name=name, breakageModel=brModel,
                                                demandModel= self.demandModel,
                                                useVialsLatency=clinicLatency)
            else:
                w= warehouse.Clinic(sim,sim.vaccines.getActiveTypes(),
                                    storagetypes.storageTypes,
                                    inventory,
                                    targetPopPC,
                                    name=name,breakageModel=brModel,
                                    demandModel= self.demandModel,
                                    latitude=latitude,longitude=longitude,
                                    useVialsLatency=clinicLatency)
        w.setNoteHolder(sim.notes.createNoteHolder())
        w.noteHolder.addNote({"name":name,"code":code,
                              "category":category, "function":function})
        w.idcode= code
        for st,vol in storageSC.items():
            w.noteHolder.addNote({(st.name+"_vol"):vol/C.ccPerLiter})
        return w        

     
