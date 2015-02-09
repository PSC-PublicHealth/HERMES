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



__doc__=""" model_niger.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math
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
import model_generic
import csv_tools

class MonthlyReportProcess(warehouse.PeriodicProcess):
    def __init__(self, sim, interval, startupLatency):
        warehouse.PeriodicProcess.__init__(self, sim, "MonthlyReportProcess",interval,startupLatency)
        self.counter= 0 
    def cycle(self,timeNow):
        nameRoot= 'report_%03d'%self.counter
        print "\nWriting %s"%nameRoot
        self.sim.syncStatistics()
        self.sim.checkSummary(nameRoot,clear=True,graph=False)
        self.counter += 1

class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        self.daysPerMonth = 28
        self.daysPerYear= C.monthsPerYear*self.daysPerMonth
        
        self.storageUtilFactor = [1.0,1.0,1.0,1.0]
        # waste due to breakage
        self.breakage = [(0.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0)] 
        
        self.runDays= self.sim.userInput['rundays']
        self.burninDays= self.sim.userInput['burnindays']
        
        ## Default file names for this model -- To Be Depricated
        #lotsOfSpace= 1000000000.0; # used for room temp storage
        
        self.factoryBatchInterval= self.daysPerYear/2.0
        self.centralStoreShipInterval= self.daysPerYear/4.0
        self.regionalStoreShipInterval= self.daysPerYear/12.0
        self.districtStoreShipInterval= self.daysPerYear/12.0
        self.reportingInterval = 1
        self.orderPendingLifetime= 1.1 # must not exactly equal transit time!
        self.patientWaitInterval= 0.3
        self.clinicTickInterval= 1.0
        self.clinicStartupLatency= self.burninDays # allow fill before customers arrive

        self.updateWasteEstimateFreq= self.sim.userInput['wasteestfreq']
        
        self.pullMeanFrequency= self.daysPerMonth
        self.nTrucks= 695
        
        self.factoryOverstockScale= 1.5/1.25
        
        self.demandModel = self._generateDemandModel(self.daysPerYear, sampler=None)
            
        self.breakageModelList= [breakagemodel.PoissonBreakageModel(a,b) for a,b in self.breakage]
            
        self.activeVaccineTypes= [ "N_Tuberculosis",
                                   "N_Tetanus_Toxoid",
                                   "N_Measles",
                                   "N_Oral Polio",
                                   "N_Yellow Fever",
                                   "N_DTP-HepB-Hib liquid",
                                   "N_Pneumococcal13",
                                   "N_RotavirusV5"
                                   ]
    

        self.truckCounts= self._loadTruckCounts()
        
#        self.predictedOVWR= { "N_Tuberculosis":0.8526,
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
#                              "N_Pneumococcal13":0.0
#                              }
        
        # Uncomment to produce monthly reports
        self.monthlyReportProcess= None
        #self.monthlyReportProcess= MonthlyReportProcess(sim,28.0,5.0)
        self.monthlyReportActivated= False
        
    @staticmethod
    def decomposeId(code):
        #print "decomposeId: %d -> "%code,
        clinicCode= code % 100
        code /= 100
        districtCode= code % 100
        code /= 100
        regionCode= code % 100
        #print "(%d,%d,%d)"%(regionCode,districtCode,clinicCode)
        return (regionCode,districtCode,clinicCode)

    @staticmethod
    def composeId(regionCode,districtCode,clinicCode):
        result= long("%d%02d%02d%02d"%(1,regionCode,districtCode,clinicCode))
        #print "composeId: (%d %d %d) -> %ld"%(regionCode,districtCode,
        #                                      clinicCode,result)
        return result

    def _getsFactory(self,storeDict,code):
        return (self.decomposeId(code)==(0,0,0)) # Only the central store

    def _isClinic(self,storeDict,code):
        regionCode,districtCode,clinicCode= self.decomposeId(code)
        return (clinicCode!=0)

#    def _scaleDemandByType(self, shipDosesVC, postCeilFactor):
#        """
#        Input is in doses; output in vials rounded up.  
#        The 'wastage' bit is a hack to implement some estimated
#        wastage constants peculiar to Niger.
#        """
#        shipVialsVC= shipDosesVC*self.sim.vaccines.getDosesToVialsVC()
#        shipVialsTupleList= [(v,n) for v,n in shipVialsVC.getTupleList()]
#        scaledTupleList= []
#        for v,nVials in shipVialsTupleList:
#            if self.updateWasteEstimateFreq > 0:
#                wastage = 1.0-self.wastageEstimates[v]
#            elif v.name in self.predictedOVWR:
#                wastage= 1.0-self.predictedOVWR[v.name]
#            elif isinstance(v,abstractbaseclasses.HasOVW):
#                # We want to explicitly trap vaccines not listed in our predictedOVWR table
#                raise RuntimeError("Don't know wastage for %s"%v.name)
#            else:
#                wastage= 1.0
#            scaledTupleList.append( (v,math.ceil(nVials)*(postCeilFactor/wastage)) )
#        return self.sim.vaccines.getCollection(scaledTupleList)
    
    def clinicShipQuantityFunc(self,fromW, toW, pullMeanFrequency, timeNow):
        assert(isinstance(toW,warehouse.Clinic))
        vC= toW.shippingDemandModel.getDemandExpectation(toW.getPopServedPC(),
                                                         self.clinicTickInterval)
        vC *= self.sim.vaccines.getDosesToVialsVC()
        vC.roundUp()
        vC = self.sim.shippables.addPrepSupplies(vC)
        vaccinesOnlyVC= vC.splitOut(vaccinetypes.VaccineType)
        # vC now contains only the non-vaccines
        vaccinesOnlyVC *= 1.25*(pullMeanFrequency/self.clinicTickInterval)
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

    def clinicShipThresholdFunc(self,toW,pullMeanFrequency):
        assert(isinstance(toW,warehouse.Clinic))
        vC= toW.shippingDemandModel.getDemandExpectation(toW.getPopServedPC(),
                                                         self.clinicTickInterval)
        vC *= self.sim.vaccines.getDosesToVialsVC()
        vC.roundUp()
        vC = self.sim.shippables.addPrepSupplies(vC)
        vaccinesOnlyVC= vC.splitOut(vaccinetypes.VaccineType)
        vaccinesOnlyVC *= 0.25*(pullMeanFrequency/self.clinicTickInterval)
        vaccinesOnlyVC.roundUp() #yes, round up twice.
        fVC,cVC,wVC= toW.calculateStorageFillRatios(vC+vaccinesOnlyVC)
        whatFitsVC= vaccinesOnlyVC*(fVC+cVC+wVC)
        threshVC= whatFitsVC
        threshVC.roundDown()

        return threshVC

    def warehouseShipQuantityFunc(self,fromW, toW, pullMeanFrequency, timeNow):
        vC= self.demandModel.getDemandExpectation(toW.getTotalDownstreamPopServedPC(),
                                                   self.clinicTickInterval)
        vC *= self.sim.vaccines.getDosesToVialsVC()
        vaccinesOnlyVC= vC.splitOut(vaccinetypes.VaccineType)
        tupleList= [(v,
                     math.ceil(1.25*rate \
                               *(pullMeanFrequency/self.clinicTickInterval) \
                               /(1.0-self.wastageEstimates[v])))
                    for v,rate in vaccinesOnlyVC.items()]
        orderToQuantityVC= self.sim.vaccines.getCollection(tupleList)
        orderToQuantityVC.roundUp()
        vC = self.sim.shippables.addPrepSupplies(vC)
        orderToQuantityVC = self.sim.shippables.addPrepSupplies(orderToQuantityVC)
        fVC,cVC,wVC= toW.calculateStorageFillRatios(orderToQuantityVC)
        fillVC= fVC+cVC+wVC
        #print "%s: %s"%(toW.name,fillVC)
        scaledQuantityVC= orderToQuantityVC*fillVC
        scaledQuantityVC.roundDown()
        lowVC= (vC+scaledQuantityVC) \
               - self.sim.vaccines.getCollectionFromGroupList(toW.theBuffer)
        lowVC.floorZero()
        return lowVC

    def warehouseShipThresholdFunc(self,toW,pullMeanFrequency):
        vC= self.demandModel.getDemandExpectation(toW.getTotalDownstreamPopServedPC(),
                                                  self.clinicTickInterval)
        vC *= self.sim.vaccines.getDosesToVialsVC()
        vaccinesOnlyVC= vC.splitOut(vaccinetypes.VaccineType)
        tupleList= [(v,
                     math.ceil(n) \
                     *(pullMeanFrequency/self.clinicTickInterval) \
                     /(1.0-self.wastageEstimates[v]))
                    for v,n in vaccinesOnlyVC.items()]
        whatWeWantToOrderVC= self.sim.vaccines.getCollection(tupleList)
        whatWeWantToOrderVC = self.sim.shippables.addPrepSupplies(whatWeWantToOrderVC)
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
                                               *(1.0-self.wastageEstimates[v]))
                                       ))
                                for v,n in vaccineDosesVC.getTupleList()]
        vaccineVialsVC = self.sim.vaccines.getCollection(vaccineVialsTupleList)
        vaccineVialsVC = self.sim.shippables.addPrepSupplies(vaccineVialsVC)
        vC = self.sim.shippables.addPrepSupplies(vC)
        return vaccineVialsVC+vC

    def getApproxScalingVC(self,storeDict,code):
        wh= storeDict[code]
        if wh.name.find("dist_clinic")>=0:
            tickInterval= 7.0
        else:
            tickInterval= 28.0
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
        return scaledVC # The factory is never to deliver anything but vaccines
    
    def getFactoryProductionFunction(self,storeDict,code):
        if not self._getsFactory(storeDict,code): return None
        else: return self._getFactoryProductionVC
        
    def getShipInterval(self,storeDict,code):
        regionCode,districtCode,clinicCode= self.decomposeId(code)
        if regionCode==0 and districtCode==0 and clinicCode==0:
            # supplier is central store
            return self.centralStoreShipInterval
        elif districtCode==0 and clinicCode==0:
            # supplier is a region
            return self.regionalStoreShipInterval
        elif clinicCode==0:
            return self.districtStoreShipInterval
        else:
            raise RuntimeError("Scheduled shipments originating from clinics are not supported.")
        return None

    def getShipStartupLatency(self,storeDict,code):
        return 0.0

    def getOrderPendingLifetime(self,storeDict,code):
        return self.orderPendingLifetime

    def getTruckInterval(self,storeDict,code):
        regionCode,districtCode,clinicCode= self.decomposeId(code)
        if regionCode==0 and districtCode==0 and clinicCode==0:
            # supplier is central store
            return self.centralStoreShipInterval
        elif districtCode==0 and clinicCode==0:
            # supplier is a region
            return self.regionalStoreShipInterval
        elif clinicCode==0:
            return 7.0 # One shipment per week, max
        else:
            raise RuntimeError("Scheduled shipments originating from clinics are not supported.")
        return None

    def getPullControlFuncs(self,storeDict,code):
        if self._isClinic(storeDict,code):
            tFunc= self.clinicShipThresholdFunc
            qFunc= self.clinicShipQuantityFunc
        else:
            tFunc= self.warehouseShipThresholdFunc
            qFunc= self.warehouseShipQuantityFunc
        return (tFunc,qFunc)

    def getPullMeanFrequency(self,storeDict,code):
        return self.pullMeanFrequency

    def getDefaultPullMeanFrequency(self,storeDict,code):
        return self.pullMeanFrequency

    def getDefaultSupplier(self,storeDict,code):
        regionCode,districtCode,clinicCode= self.decomposeId(code)
        if regionCode==0 and districtCode==0 and clinicCode==0:
            return None # This is the central store
        else:
            wh= storeDict[code]
            if wh.getPopServedPC().totalCount()==0 and len(wh.getClients())==0:
                # deactivated warehouse
                return None
            elif districtCode==0 and clinicCode==0:
                # region; supplier is central store
                return self.composeId(0,0,0) 
            elif clinicCode==0:
                # district; supplier is region
                return self.composeId(regionCode,0,0) 
            else:
                # clinic; supplier is district
                return self.composeId(regionCode,districtCode,0) 

    @staticmethod
    def getDefaultTruckTypeName(fromWH,toWH):
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,
        return the name of the truck type to be used to implement the
        implied 'pull' shipment to be created.
        """
        return "N_vaccine_carrier"

    @staticmethod
    def getDefaultTruckInterval(fromWH,toWH):
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,
        return the minimum number of days between departures to be used
        to implement the implied 'pull' shipment.
        """
        return 7.0

    def getUseVialsProcess(self,storeDict,code):
        wh= storeDict[code]
        if self._isClinic(storeDict,code):
            totalLatency= self.clinicStartupLatency
            tickInterval= self.clinicTickInterval
            patientWaitInterval= self.patientWaitInterval
            useVials= warehouse.UseVials(wh,
                                         tickInterval,
                                         patientWaitInterval,
                                         C.useVialPriority,
                                         totalLatency)
            return useVials
        else:
            return None
        
#    def warehouseOrClinicFromRec(self,sim,rec,
#                                 recordTheseStoresDict={},
#                                 recordTheseVaccineNames=[]):
#        name= rec['NAME']
#        code= long(rec['idcode'])
#        #print "building warehouse %s: %s"%(name,code)
#        regionCode,districtCode,clinicCode= Model.decomposeId(code)
#        if clinicCode==0:
#            targetPopPC= None
#        else:
#            targetPopPC= self._peopleCollectionFromTableRec(rec)
#            
#        if len(self.breakage)!=4 or len(self.storageUtilFactor)!=4:
#            raise RuntimeError("Globals have not been updated for this model")
#        if regionCode == 0:
#            sUF = self.storageUtilFactor[0]
#            brModel= self.breakageModelList[0]
#        elif districtCode == 0:
#            sUF = self.storageUtilFactor[1]
#            brModel= self.breakageModelList[1]
#        elif clinicCode == 0:
#            sUF = self.storageUtilFactor[2]
#            brModel= self.breakageModelList[2]
#        else:
#            sUF = self.storageUtilFactor[3]
#            brModel= self.breakageModelList[3]
#
#        if rec.has_key('WHO_Lat') and rec['WHO_Lat']!=0.0:
#            latitude= rec['WHO_Lat']
#        elif rec.has_key('Pop_Lat') and rec['Pop_Lat']!=0.0:
#            latitude= rec['Pop_Lat']
#        else:
#            latitude= 0.0
#        if rec.has_key('WHO_Long') and rec['WHO_Long']!=0.0:
#            longitude= rec['WHO_Long']
#        elif rec.has_key('Pop_Long') and rec['Pop_Long']!=0.0:
#            longitude= rec['Pop_Long']
#        else:
#            longitude= 0.0
#
#        storageSpace= self._storageSpaceFromTableRec(rec,sUF)
#        storageSC= self._getTotalVolumeSC(storageSpace)
#        totalStorage= sim.storage.getTotalRefrigeratedVol(storageSC)
#        coolStorage= sim.storage.getTotalCoolVol(storageSC)
#        if clinicCode==0:
#            if (( targetPopPC is None or targetPopPC.totalCount()==0) 
#                and totalStorage==0.0):
#                return None # dead warehouse
#            else:
#                #??? should vaccineTypes be changed.
#                w= warehouse.Warehouse(sim, sim.vaccines.getActiveTypes(),
#                                       storagetypes.storageTypes,
#                                       storageSpace,
#                                       targetPopPC,
#                                       name=name,breakageModel=brModel,
#                                       latitude=latitude,longitude=longitude)
#        else:
#            if coolStorage==0.0:
#                if targetPopPC.totalCount()==0:
#                    return None # dead warehouse
#                else:
#                    w= warehouse.AttachedClinic(sim,None,
#                                                targetPopPC,
#                                                name=name, breakageModel=brModel,
#                                                demandModel= self.demandModel)
#            else:
#                w= warehouse.Clinic(sim,sim.vaccines.getActiveTypes(),
#                                    storagetypes.storageTypes,
#                                    storageSpace,
#                                    targetPopPC,
#                                    name=name,breakageModel=brModel,
#                                    demandModel= self.demandModel,
#                                    latitude=latitude,longitude=longitude)
#        w.setNoteHolder(sim.notes.createNoteHolder())
#        w.noteHolder.addNote({"name":name,"code":code})
#        w.idcode= code
#        for st,vol in storageSC.items():
#            w.noteHolder.addNote({(st.name+"_vol"):vol/C.ccPerLiter})
#        return w
    
     
