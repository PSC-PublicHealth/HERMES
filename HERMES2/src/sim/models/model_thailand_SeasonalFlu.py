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

__doc__=""" model_thailand.py
This is a variant of the Thailand model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math
from collections import deque

from SimPy.Simulation import hold # for SchoolOrderProcess

import constants as C
import storagetypes
import recorders
import vaccinetypes
import trucktypes
import peopletypes as pt
from util import openDataFullPath
from noteholder import NoteHolderGroup
import warehouse
import sampler
import demandmodel
import breakagemodel
import model
import csv_tools


def createRunningAverageQue(initialVC):
    return deque([initialVC.copy() 
                  for i in xrange(Model.nRunningAverageShipments)])

class SchoolOrderProcess(warehouse.PeriodicProcess):
    def __init__(self, interval, startupLatency, wh):
        warehouse.PeriodicProcess.__init__(self, wh.sim, "SchoolOrderProcess_%s"%wh.name,
                                           interval,startupLatency)
        self.wh= wh
        self.daysPerMonth= self.wh.sim.model.daysPerMonth
    def cycle(self,timeNow):
        shipDosesVC= self.wh.shippingDemandModel.getDemandExpectation(self.wh.getPopServedPC(),
                                                                      self.interval,timeNow+self.daysPerMonth)
        shipVialsVC= shipDosesVC*self.sim.vaccines.getDosesToVialsVC()
        shipVialsVC.roundUp()
        shipVialsVC = self.sim.shippables.addPrepSupplies(shipVialsVC)
        self.wh.registerInstantaneousDemandVC(shipVialsVC,self.interval)
        timeNow= yield hold,self,28.0 # Leave the request in place for a month
        shipVialsVC= self.sim.vaccines.getCollection() # We won't need any more until next cycle
        self.wh.registerInstantaneousDemandVC(shipVialsVC,self.interval)        
        
class MonthlyOrderProcess(warehouse.PeriodicProcess):
    def __init__(self,interval, startupLatency, wh):
        warehouse.PeriodicProcess.__init__(self, wh.sim, "MonthlyOrderProcess_%s"%wh.name,
                                           interval,startupLatency)
        self.wh= wh
        self.daysPerMonth= wh.sim.model.daysPerMonth
    def cycle(self,timeNow):
        vialsThisMonth= self.wh.getAccumulatedUsageVC()
        self.wh.clearAccumulatedUsage()
        if self.wh.runningAveQ is None:
            self.wh.runningAveQ= createRunningAverageQue(vialsThisMonth)
            self.wh.runningAveVC= vialsThisMonth*len(self.wh.runningAveQ)
        else:
            self.wh.runningAveVC -= self.wh.runningAveQ.pop() # remove from right end
            self.wh.runningAveVC += vialsThisMonth
            self.wh.runningAveQ.appendleft(vialsThisMonth.copy()) # insert from left
            
        aveVC= self.wh.runningAveVC*(1.0/len(self.wh.runningAveQ))
        vaccT = self.sim.vaccines.getTypeByName("T_Influenza")
        if aveVC.has_key(vaccT):
            aveVC[vaccT] = self.wh.shippingDemandModel.getDemandExpectation(self.wh.getPopServedPC(),
                                                                            self.interval,timeNow+self.daysPerMonth)[vaccT]
        aveVC = self.sim.shippables.addPrepSupplies(aveVC)                                                      
        self.wh.registerInstantaneousDemandVC(aveVC,self.interval)
        
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
        
class Model(model.Model):
    
    nRunningAverageShipments= 1
    
    def __init__(self, sim):
        model.Model.__init__(self,sim)
        # Thailand has short years because of the need to keep weekly and monthly
        # shipments synchronized.
        self.daysPerMonth = 28
        self.daysPerYear= C.monthsPerYear*self.daysPerMonth
        
        #self.storageUtilFactor = [1.0,1.0,1.0,1.0]
        #self.storageUtilFactor = [0.9,0.9,0.9,0.5]   # [Central Store, Region, District, Clinic]
        #self.breakage = [0.01,0.01,0.01,.01]
        
        # waste due to breakage
        self.breakage = [(0.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0)]          # [Central Store, Region, District, Clinic]
        
        self.runDays= self.sim.userInput['rundays']
        self.burninDays= self.sim.userInput['burnindays']
        
        # The factory actually delivers 4 times a year, but to the central store.
        # Stock is shipped from there to the regional stores monthly.  Since the
        # central store is not in our model, we'll pretend that the factory
        # ships directly to the regional store monthly.
        #self.factoryBatchInterval= 365.0/4.0
        self.factoryBatchInterval= 28.0
        #self.centralStoreShipInterval= 365.0/4.0
        self.centralStoreShipInterval= 28.0
        self.centralStoreStartupLatency= 0.0
        #self.regionalStoreShipInterval= 365.0/12.0
        self.regionalStoreShipInterval= 28.0
        self.regionalStoreStartupLatency= 7.0
        #self.districtStoreShipInterval= 365.0/12.0
        self.districtStoreShipInterval= 28.0
        self.districtStoreStartupLatency= 14.0
        self.reportingInterval = 1
        self.truckInterval= 28.0 # how often trucks leave on circuits
        self.orderPendingLifetime= 1.1 # must not exactly equal transit time!
        self.patientWaitInterval= 0.3
        self.clinicTickInterval= None # varies for this model; should be days

        self.updateWasteEstimateFreq= self.sim.userInput['wasteestfreq']
        
        self.factoryOverstockScale= 1
        
        self.demandModelFile= self.sim.userInput['demandfile']
        
        ## Catchup Campaign parameters
        self.catchupDemandModelFile= self.sim.userInput['catchupfile']
        self.catchupNumberOfDays = self.sim.userInput['catchupdays']
        self.catchupNumberOfMonths= self.catchupNumberOfDays/self.daysPerMonth
        
        self.catchupStartDay = self.burninDays + self.sim.userInput['catchupstart']
        self.catchupVaccineNames = ['T_Dengue']
        
        self.demandModel = self._generateDemandModel(self.daysPerYear, sampler=None)
    
        self.schoolDemandModel = self._generateDemandModel(self.daysPerYear,
                                                           sampler=sampler.ConstantSampler(),
                                                           ignoreCalendarFile=True)
        
        self.breakageModelList= [breakagemodel.SimpleBreakageModel(a,b) for a,b in self.breakage]
        
        self.truckCounts= self._loadTruckCounts()
    
        # Uncomment to produce monthly reports
        self.monthlyReportProcess= None
        #self.monthlyReportProcess= MonthlyReportProcess(self.sim,28.0,5.0)
        self.monthlyReportActivated= False

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
        return (code==1)

    def _isClinic(self,storeDict,code):
        wh= storeDict[code]
        return (isinstance(wh,warehouse.Clinic) or isinstance(wh,warehouse.AttachedClinic))

    def getSchoolCycleAndLatency(self,wh):
        assert(hasattr(wh,'schoolcode'))
        supplierLatency= self.districtStoreStartupLatency
        supplierInterval= self.districtStoreShipInterval
        if wh.schoolcode==0:
            # school1 type: dT and MMR; happens in September (month 9, or 8 counting from 0)
            # The 14 is to shift vaccination day to the middle of the month, to give vaccine
            # time to be delivered.
            extraLatency= 8*28+14
        elif wh.schoolcode==1:
            # school2 type: MMR only; happens in July (month 7, or 6 counting from 0)
            # The 14 is to shift vaccination day to the middle of the month, to give vaccine
            # time to be delivered.
            extraLatency= 6*28+14
        else:
            raise RuntimeError("Unknown schoolcode %s"%wh.schoolcode)
        netLatency= supplierLatency+extraLatency
        return 12*28.0,netLatency

    def clinicShipQuantityFunc(self, fromW, toW, routeName, pullMeanFrequency, timeNow):
        assert(isinstance(toW,warehouse.Clinic))
        raise RuntimeError("Thailand model has only scheduled shipments")

    def clinicShipThresholdFunc(self,toW,pullMeanFrequency):
        assert(isinstance(toW,warehouse.Clinic))
        raise RuntimeError("Thailand model has only scheduled shipments")

    def warehouseShipQuantityFunc(self, fromW, toW, routeName, pullMeanFrequency, timeNow):
        raise RuntimeError("Thailand model has only scheduled shipments")

    def warehouseShipThresholdFunc(self, toW, pullMeanFrequency):
        raise RuntimeError("Thailand model has only scheduled shipments")

    def _scaleDemandByType(self, shipDosesVC):
        """
        Input is in doses; output in vials rounded up.  
        The 'wastage' bit is a hack to implement some estimated
        wastage constants peculiar to Thailand.
        """
        shipVialsTupleList= [(v,n/v.getNDosesPerVial())
                             for v,n in shipDosesVC.getTupleList()]
        scaledTupleList= []
        for v,nVials in shipVialsTupleList:
            if self.updateWasteEstimateFreq > 0:
                wastage = 1.0-self.wastageEstimates[v]
            else:
                wastage= 1.0
    
    #            if v.name=="T_Tuberculosis": wastage= 0.5
    #            elif v.name=="T_HepB": wastage= 0.9
    #            elif v.name=="T_DTP": wastage= 0.75
    #            elif v.name=="T_DTP-HepB": wastage= 0.75
    #            elif v.name=="T_Oral Polio": wastage= 0.75
    #            elif v.name=="T_Measles": wastage= 0.75
    #            elif v.name=="T_Japanese Encephalitis": wastage= 0.9
    #            elif v.name=="T_MMR": wastage= 0.9
    #            elif v.name=="T_Diphtheria-tetanus-lowdose": wastage= 0.9
    #            elif v.name=="T_Pneumococcal": wastage= 0.9
    #            elif v.name=="T_MMR-unidose": wastage= 0.9
    #            elif v.name=="T_Measles-unidose": wastage= 0.9
    #            elif v.name in ["T_RotavirusV1",
    #                            "T_RotavirusV2",
    #                            "T_RotavirusV3",
    #                            "T_RotavirusV4",
    #                            "T_RotavirusV5",
    #                            "T_RotavirusV6",
    #                            "T_RotavirusV7"]: wastage= 0.9
    #            elif v.name=="T_Influenza": wastage= 0.9
    
                if v.name=="T_Tuberculosis": wastage= 1.0-0.26
                elif v.name=="T_HepB": wastage= 1.0-0.04
                elif v.name=="T_DTP": wastage= 1.0-0.15
                elif v.name=="T_DTP-HepB": wastage= 1.0-0.10
                elif v.name=="T_Oral Polio": wastage= 1.0-0.20
                elif v.name=="T_Measles": wastage= 1.0-.27
                elif v.name=="T_Japanese Encephalitis": wastage= 1.0-0.04
                elif v.name=="T_MMR": wastage= 1.0-0.04
                #elif v.name=="T_MMR": wastage= 0.99
                elif v.name=="T_Diphtheria-tetanus-lowdose": wastage= 1.0-0.20
                elif v.name=="T_Pneumococcal": wastage= 0.9
                elif v.name=="T_MMR-unidose": wastage= 1.0-0.0
                elif v.name=="T_Measles-unidose": wastage= 1.0-0.0
                elif v.name in ["T_RotavirusV1",
                                "T_RotavirusV2",
                                "T_RotavirusV3",
                                "T_RotavirusV4",
                                "T_RotavirusV5",
                                "T_RotavirusV6",
                                "T_RotavirusV7"]: wastage= 0.9
                elif v.name=="T_Influenza": wastage= 0.9
                elif v.name=="T_Dengue": wastage = 1.0-0.05 
                else:
                    raise RuntimeError("Don't know wastage for %s"%v.name)
            scaledTupleList.append( (v,int(math.ceil(nVials/wastage))) )
        #print "%s: %s %s"%(toW.name,shipDosesVC,["%s:%d"%(v.name,n) for v,n in scaledTupleList])
        return self.sim.vaccines.getCollection(scaledTupleList)

    def addedCatchupDemand(self,storeDict,cudemand):
        assert(isinstance(cudemand,demandmodel.CatchupDemandModel))
        ## First obtain the cache for the districts
        catchupPrefix = 'cu_'
        
        with openDataFullPath(cudemand.catchupDemandFileName,'rU') as f:
            keyList,recList= csv_tools.parseCSV(f)
        catchupDict = {}
        ## Dictionary of PeopleCollections that holds the total additional demand
        
        ## Create new people types for the catchup campaign
        for peopleKey in keyList:
            if peopleKey != 'District':  
                if not self.sim.people.validTypename(catchupPrefix + str(peopleKey)):
                    raise RuntimeError("CatchupDemandFile has a peopletype that does not exist %s"%catchupPrefix+str(peopleKey))

        for rec in recList:
            dN = rec['District']
            catchupDict[dN] = self._peopleCollectionFromTableRec(rec)
    
        ## Now we need to run through the districts and update their 
        ## targetPop to include the proper catchup campaign numbers
        for cuD in catchupDict.keys():
            #clinicDict = dict()
            #districtName = cuD + "_DHO"
            districtList = cuD.split(":")
            clinicList = []
            for districtName in districtList:
                print 'District Name = ' + districtName
                districtWarehouse = warehouse.getStoreByName(storeDict,districtName)
                #districtWarehouse = storeDict[districtName]
                if districtWarehouse.function == "Administration":
                    clinicList.append(districtWarehouse)
                else:
                    clinicListTmp = districtWarehouse.getClients()
                    for clin in clinicListTmp:
                        clinicList.append(clin)
                        
                ## get a sum of the target Population for these clients
            sumPeopleCollection = self.sim.people.getCollection()
                
            for clinic in clinicList:
                sumPeopleCollection += clinic.getPopServedPC()
                
            ## HACK Have to take care of age groups that are not in the stores file
            oddKeyList = sumPeopleCollection.keysNotInCollection(catchupDict[cuD])
            ## for odd Keys we will use the total proportion to determine the fraction
            totalSum = sumPeopleCollection.totalCount()
                
            for oddKey in oddKeyList:
                sumPeopleCollection[oddKey] = totalSum
                
            sumPeopleCollection += 0.000000001
                ## I know I could do this in probably one line
                ## but it is easier to read for me if I separate
                ## compute the proportional factors
            weightingFactorsDict = dict()
            for clinic in clinicList:
                weightingFactorsDict[clinic] = clinic.getPopServedPC() / sumPeopleCollection                   
                for oddKey in oddKeyList:
                    weightingFactorsDict[clinic][oddKey] = clinic.getPopServedPC().totalCount()/sumPeopleCollection[oddKey]
                
            cuDict = dict()
            for clinic in clinicList:
                ## Proportion of demand to go to this clinic
                cuDict[clinic] = catchupDict[cuD] * weightingFactorsDict[clinic]
                
                ## We need to subtract off the number of people that would normally 
                ## Be getting vaccinated
                
                
                ## STB To Do: Apply a distribution that allows for weighting demand to not be even
                ##catchupDict[clinic].scale(monthsOfCatchup)
                ## subtract off the people that would be normally getting vaccinated
                scaledPopServedPC = clinic.getPopServedPC()*(cudemand.catchupNumberOfMonths/C.monthsPerYear)
                cuDict[clinic] -= scaledPopServedPC
                ### Make sure that we are not accounting for persons that are not there.
                cuDict[clinic].floorZero()
            
            ## Build Monthly Catchup demand schedule 
            for clinic in clinicList:
                clinic.getPopServedPC().addPrefixedCollection(cuDict[clinic],"cu_")
                clinic.getPopServedPC().round()
                if self.sim.debug is True:
                    print "Clinic: %s %s"%(clinic.name,clinic.getPopServedPC())         
        
    def getScheduledShipmentSize(self, toW, routeName, shipInterval,timeNow):
        demandDownstreamVC= toW.getInstantaneousDemandVC(fromW, shipInterval)
        # The downstream demand will include any attached clinics
        onhandVC= self.sim.vaccines.getCollectionFromGroupList(toW.getStore().theBuffer)
        lowVC= demandDownstreamVC - onhandVC
        lowVC.floorZero()
        lowVC.roundUp()
        #print "warehouse %s fed by %s: demandDownstreamVC %s"%(toW.name,fromW.name,demandDownstreamVC)
        #print "warehouse %s fed by %s: myAttachedClinicsVC %s"%(toW.name,fromW.name,myAttachedClinicsVC)
        #print "warehouse %s fed by %s: onhandVC %s"%(toW.name,fromW.name,onhandVC)
        #print "warehouse %s fed by %s: lowVC %s"%(toW.name,fromW.name,lowVC)
        return lowVC
    
    def getApproxScalingVC(self,storeDict,code):
        wh= storeDict[code]
        if wh.name.find("_Hosp")>=0 or wh.name.find("_MHC")>=0:
            tickInterval= 7.0
        else:
            tickInterval= 28.0
        vC = self.demandModel.getDemandExpectation(wh.getTotalDownstreamPopServedPC(),
                                                    tickInterval)
        vC = self.sim.shippables.addPrepSupplies(vC)
        return vC

    def _getFactoryProductionVC(self, factory, daysSinceLastShipment, timeNow,
                               daysUntilNextShipment):
        shipDosesVC= self.demandModel.getDemandExpectation(factory.targetStore.getTotalDownstreamPopServedPC(recalculate=True),
                                                            daysUntilNextShipment, timeNow + 0.0*self.daysPerMonth)
        ## Making this behave like vietnam
        shipInflDosesVC= factory.targetStore.getInstantaneousDemandVC(factory.name, daysUntilNextShipment)
        vaccT = self.sim.vaccines.getTypeByName('T_Influenza')
        shipDosesVC[vaccT] = shipInflDosesVC[vaccT]
        totalVC= self._scaleDemandByType(shipDosesVC)
        scaledVC= totalVC * self.factoryOverstockScale
        scaledVC.roundUp()
        scaledVC = self.sim.shippables.addPrepSupplies(scaledVC)
        return scaledVC
    
    def getFactoryProductionFunction(self,storeDict,code):
        if not self._getsFactory(storeDict, code): return None
        else: return self._getFactoryProductionVC
        
    def getFactoryStartupLatency(self,storeDict,code):
        """
        If the given Warehouse should have an attached Factory, return
        the delay in days before the factory's first shipment is delivered.
        If the given Warehouse has no factory (in which case getFactoryYearlyProduction
        will have returned None), this function will not be called or its return value 
        will be ignored.
        
        Because of the shipment size scheduling mechanism, nothing gets shipped during
        the first month of burn-in in Thailand.  Delay factory production by a month
        to prevent vaccine aging in the top-level warehouse.
        """
        return 28.0 

    def getTruckInterval(self,storeDict,code):
        return self.truckInterval

    def getShipStartupLatency(self,storeDict,code):
        wh= storeDict[code]
        if code==1:
            # central store
            return self.centralStoreStartupLatency
        elif code==2:
            # regional store
            return self.regionalStoreStartupLatency
        elif code==49:
            # Special case of Yantakhow_Hosp- extra step in the link so one
            # additional day of latency.
            return self.regionalStoreStartupLatency+1.0           
        elif (isinstance(wh,warehouse.Clinic) or isinstance(wh,warehouse.AttachedClinic)):
            # clinic or attached clinic
            raise RuntimeError("Scheduled shipments originating from clinics are not supported. (getStatupLatency)")
        else:
            return self.districtStoreStartupLatency

    def getOrderPendingLifetime(self,storeDict,code):
        return self.orderPendingLifetime

    def getShipInterval(self,storeDict,code):
        wh= storeDict[code]
        if code==1:
            # supplier is central store
            return self.centralStoreShipInterval
        elif code==2:
            # supplier is regional store
            return self.regionalStoreShipInterval           
        elif (isinstance(wh,warehouse.Clinic) or isinstance(wh,warehouse.AttachedClinic)):
            raise RuntimeError("Shipment out of %s (%ld): Scheduled shipments originating from clinics are not supported."%\
                               (wh.name,code))
        else:
            # supplier is a region or district (both the same in Thailand Model)
            return self.districtStoreShipInterval
            
    def getPullControlFuncs(self,storeDict,code):
        if self._isClinic(storeDict,code):
            tFunc= self.clinicShipThresholdFunc
            qFunc= self.clinicShipQuantityFunc
        else:
            tFunc= self.warehouseShipThresholdFunc
            qFunc= self.warehouseShipQuantityFunc
        return (tFunc,qFunc)

    def getPullMeanFrequency(self,storeDict,code):
        raise RuntimeError("Thailand model has only scheduled shipments")

    def getDefaultPullMeanFrequency(self,storeDict,code):
        raise RuntimeError("Thailand model has only scheduled shipments")

    def getDefaultSupplier(self,storeDict,code):
        if code==1:
            # Code 1 is central store
            return None           
        else:
            # return code as is unless code is District Hospital/Hosp_Clinic fix
            return (code % 10000)

    def _getUseVialsTickIntervalDays(self,storeDict,code):
        wh= storeDict[code]
        if code<20000:
            # This is a clinic- but at what level?
            if wh.name.find("_Hosp")>=0 or wh.name.find("_MHC")>=0:
                tickInterval= 7.0
            else:
                tickInterval= 28.0
        elif code<40000:
            # This is a school
            tickInterval,latency= self.getSchoolCycleAndLatency(wh)
        else:
            # This is a flu clinic
            tickInterval= 1.0
        return tickInterval
    
    def _getUseVialsStartupLatencyDays(self,storeDict,code):
        """
        In Thailand, clinics run one day after their vaccine arrives.
        """
        wh= storeDict[code]
        if code<20000:
             # This is a clinic- but at what level?
            if wh.name.find("_Hosp")>=0 or wh.name.find("_MHC")>=0:
                # District level
                supplierLatency= self.regionalStoreStartupLatency
                supplierInterval= self.regionalStoreShipInterval
                firstDelivery= supplierLatency
            else:
                # Subdistrict level
                supplierLatency= self.districtStoreStartupLatency
                supplierInterval= self.districtStoreShipInterval
                firstDelivery= supplierLatency
                if code>50 and code<68:
                    # special clause to deal with extra day's delay in
                    # Yantakhow supply chain
                    firstDelivery += 1.0
            totalLatency= firstDelivery+2.0
        elif code<40000:
            # This is a school
            tickInterval,totalLatency= self.getSchoolCycleAndLatency(wh)
        else:
            # This is a flu clinic
            totalLatency= 7.0

        return totalLatency
    
    def getUseVialsProcess(self,storeDict,code):
        wh= storeDict[code]
        if self._isClinic(storeDict,code):
            totalLatency= self._getUseVialsStartupLatencyDays(storeDict,code)
            tickInterval= self._getUseVialsTickIntervalDays(storeDict,code)
            patientWaitInterval= self.patientWaitInterval
            useVials= warehouse.UseVials(wh,
                                         tickInterval,
                                         patientWaitInterval,
                                         C.useVialPriority,
                                         totalLatency)
            return useVials
        else:
            return None
    
    def warehouseOrClinicFromRec(self, sim, rec, expectedType,
                                 recordTheseStoresDict={},
                                 recordTheseVaccineNames=[]):
        category= rec['CATEGORY']
        function = rec['FUNCTION']
        name= rec['NAME']
        code= long(rec['idcode'])
        #print "building warehouse %s: %s"%(category,func,name,code)
        targetPopPC= self._peopleCollectionFromTableRec(rec)
        #name= "%s_%s"%(name,code)

        isClinic=False
        if code==1: 
            # District Store
            brModel=  self.breakageModelList[0]
        elif function=='Distribution': 
            # Region and District use the same values for Thailand model
            brModel=  self.breakageModelList[1]
        else:
            # Clinic (and Attached)
            # Do Hospitals and Hospital Clinics use same values?
            brModel=  self.breakageModelList[3]
            isClinic=True

        sUF= float(rec['Device Utilization Rate'])

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
        w= None
        storageSpace= self._storageSpaceFromTableRec(rec,sUF)
        storageSC= self._getTotalVolumeSC(storageSpace)
        totalStorage= sim.storage.getTotalRefrigeratedVol(storageSC)
        if issubclass(expectedType, warehouse.AttachedClinic) and totalStorage>0.0:
            raise RuntimeError('The Stores file information for %s says it has storage, but it is an Attached Clinic'%wh.name)
        coolStorage= sim.storage.getTotalCoolVol(storageSC)
        if not isClinic:
            # This is a warehouse
            w= warehouse.Warehouse(sim, sim.vaccines.getActiveTypes(),
                                   storagetypes.storageTypes,
                                   storageSpace,
                                   targetPopPC,
                                   func=function,category=category,name=name,
                                   breakageModel=brModel,
                                   latitude=latitude,longitude=longitude)
            #print w.category,w.name
        elif function=='Administration' and (coolStorage==0.0 or issubclass(expectedType,warehouse.AttachedClinic)):
            # This is an attached clinic
            #print w.category, w.function, w.name
            w= warehouse.AttachedClinic(sim, None,
                                    targetPopPC,
                                    name=name, breakageModel=brModel,
                                    demandModel= None)
            if w.name.find("_school")>=0:
                if w.name.find("_school1")>=0:
                    w.schoolcode= 0
                elif w.name.find("_school2")>=0:
                    w.schoolcode= 1
                interval,latency= self.getSchoolCycleAndLatency(w)
                orderLatency= latency-28.0 # Order 1 month before use
                while orderLatency<0.0: orderLatency += interval
                w.orderProcess= SchoolOrderProcess(interval,orderLatency,w)
                w.setDemandModel(self.schoolDemandModel)
            else:
                w.orderProcess= MonthlyOrderProcess(28.0,3.0*7.0,w)
                w.setDemandModel(self.demandModel)
            self.sim.activate(w.orderProcess,w.orderProcess.run())
        else:
            # This is a clinic
            w= warehouse.Clinic(sim, sim.vaccines.getActiveTypes(),
                                storagetypes.storageTypes,
                                storageSpace,
                                targetPopPC,
                                func=function,category=category,name=name,breakageModel=brModel,
                                demandModel= self.demandModel,
                                latitude=latitude,longitude=longitude)
            w.orderProcess= MonthlyOrderProcess(28.0,3.0*28.0,w)
            self.sim.activate(w.orderProcess,w.orderProcess.run())
        w.setNoteHolder(sim.notes.createNoteHolder())
        w.noteHolder.addNote({"name":name,"code":code,
                              "category":category, "function":function})
        for st,vol in storageSC.items():
            w.noteHolder.addNote({(st.name+"_vol"):vol/C.ccPerLiter})
        # Attach the idcode to the warehouse, for convenience later.
        w.idcode= code
        # This is for a deque and VC to be used for running average
        w.runningAveQ= None
        w.runningAveVC= None
        return w
            

