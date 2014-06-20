#!/usr/bin/env python

########################################################################
# Copyright C 2009, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" model_vietnam.py
This is a variant of the Vietnam model for the vaccine distribution
simulator HERMES
"""

##########################
# Notes-
# -don't forget to add something to delete left-overs from clinics which use cold box storage
# -Apparently IVAC supplies the northern region via the Central Store, unlike others?
# -is V_DTwP real?
# -The pull trigger threshold functions are a total hack, and almost certainly incorrect.
##########################

_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math

import SimPy.Simulation

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
import model
import csv_tools

### Only used by varpush
### being executed by pull as well.
class MonthlyOrderProcess(warehouse.PeriodicProcess):
    def __init__(self,interval, startupLatency,wh):
        warehouse.PeriodicProcess.__init__(self, wh.sim, "MonthlyOrderProcess_%s"%wh.name,
                                           interval,startupLatency)
        self.wh= wh
        assert(hasattr(self.wh,'shippingDemandModel'))
    def cycle(self,timeNow):
        dosesNeededVC= self.wh.shippingDemandModel.getDemandExpectation(self.wh.getPopServedPC(),
                                                                        self.interval)
        dosesNeededVC *= 1.0 # safety stock to be specified by the user of this info
        vialsVC= self.sim.model._scaleDemandByType(dosesNeededVC)
        vialsVC = self.sim.shippables.addPrepSupplies(vialsVC)
        self.wh.registerInstantaneousDemandVC(vialsVC,self.interval)
        
class MonthlyReportProcess(warehouse.PeriodicProcess):
    def __init__(self,sim,interval,startupLatency):
        warehouse.PeriodicProcess.__init__(self,sim,"MonthlyReportProcess",interval,startupLatency)
        self.counter= 0 
    def cycle(self,timeNow):
        nameRoot= 'report_%03d'%self.counter
        print "\nWriting %s"%nameRoot
        self.sim.syncStatistics()
        Model.checkSummary(nameRoot,clear=True)
        self.counter += 1
        
class Model(model.Model):
    
    def __init__(self, sim):
        model.Model.__init__(self,sim)
        # Vietnam has short years because of the need to keep weekly and monthly
        # shipments synchronized.
        self.daysPerMonth = 30
        self.daysPerYear= C.monthsPerYear*self.daysPerMonth

        #self.storageUtilFactor = [1.0,1.0,1.0,1.0]
        #self.storageUtilFactor = [0.9,0.9,0.9,0.5]   # [Central Store, Region, District, Clinic]
        
        # Info for loss due to breakage
        #self.breakage = [0.01,0.01,0.01,.01]
        self.breakage = [(0.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0)] # [Central Store, Region, District, Clinic]
        #self.breakage = [(0.0,0.0),(0.0,0.0),(0.0,0.0),(0.0,0.0)]
        self.runDays= self.sim.userInput['rundays']
        self.burninDays= self.sim.userInput['burnindays']

        # The factory actually delivers 4 times a year, but to the central store.
        # Stock is shipped from there to the regional stores monthly.  Since the
        # central store is not in our model, we'll pretend that the factory
        # ships directly to the regional store monthly.
        #self.factoryBatchInterval= 365.0/4.0
        self.factoryBatchInterval= 90.0
        
        self.reportingInterval = 1
        self.truckInterval= 10.0 # how often trucks may leave on circuits, unless specified in Routes table
        self.orderPendingLifetime= 1.1 # must not exactly equal transit time!
        self.patientWaitInterval= 0.3
        self.clinicTickInterval= 30.0 
        self.clinicStartupLatency= 16.0
        self.factoryOverstockScale= 1.0 #Top level warehouses not maintaining buffer stock, can tune up to handle that.
    
        self.pullMeanFrequency= 30.0

        self.updateWasteEstimateFreq= self.sim.userInput['wasteestfreq']
        self.demandModelFile= self.sim.userInput['demandfile']

        ## Catchup Campaign parameters
        self.catchupDemandModelFile= self.sim.userInput['catchupfile']
        self.catchupNumberOfDays = self.sim.userInput['catchupdays']
        self.catchupNumberOfMonths= self.catchupNumberOfDays/self.daysPerMonth
        
        self.catchupStartDay = self.burninDays + self.sim.userInput['catchupstart']
        self.catchupVaccineNames = ['V_Dengue']
        
        self.demandModel = self._generateDemandModel(self.daysPerYear, 
                                                     sampler=sampler.PoissonSampler())
        
        self.breakageModelList= [breakagemodel.PoissonBreakageModel(a,b) for a,b in self.breakage]

        self.truckCounts= self._loadTruckCounts()
        
        # Uncomment to produce monthly reports
        self.monthlyReportProcess= None
        #self.monthlyReportProcess= MonthlyReportProcess(sim,28.0,5.0)
        self.monthlyReportActivated= False
    
        # This model has multiple factories with different products.  The VCs in this dict
        # encode that; a given factory's VC will be 1.0 for vaccines it produces, 0.0 otherwise.
        # Entries are by ID code of the supplied warehouse.
        self.factoryProductFilterDict= {1:self.sim.vaccines.getCollection([(sim.vaccines.getTypeByName('V_HepB'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_JE'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_Cholera'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_Oral Polio'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_MR'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_Measles'),1.0),             
                                                                           (sim.vaccines.getTypeByName('V_Tuberculosis'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_DTP'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_DTP_HB_Hib_small'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_DTP_HB_Hib_large'),1.0),
                                                                           #(sim.vaccines.getTypeByName('V_DTP_HB_Hib_10 dose'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_HPV_small'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_HPV_large'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_Rotavirus_small'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_Rotavirus_large'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_Pneumococcal'),1.0),
                                                                           (sim.vaccines.getTypeByName('V_Tetanus_Toxoid'),1.0)]),
#                                        10:self.sim.vaccines.getCollection([(sim.vaccines.getTypeByName('V_Tuberculosis'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP_HB_Hib_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP_HB_Hib_large'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_large'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Rotavirus_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Rotavirus_large'),1.0),
#                                                                          #(sim.vaccines.getTypeByName('V_DTP_HB_Hib_10 dose'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Pneumococcal'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Tetanus_Toxoid'),1.0)]),
#                                        18:self.sim.vaccines.getCollection([(sim.vaccines.getTypeByName('V_Tuberculosis'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP_HB_Hib_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP_HB_Hib_large'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_large'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Rotavirus_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Rotavirus_large'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Pneumococcal'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Tetanus_Toxoid'),1.0)]),
#                                        33:self.sim.vaccines.getCollection([(sim.vaccines.getTypeByName('V_Tuberculosis'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP_HB_Hib_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_DTP_HB_Hib_large'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_large'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_HPV_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Rotavirus_small'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Rotavirus_large'),1.0),
#                                                                          #(sim.vaccines.getTypeByName('V_DTP_HB_Hib_10 dose'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Pneumococcal'),1.0),
#                                                                           (sim.vaccines.getTypeByName('V_Tetanus_Toxoid'),1.0)]),
                                            }
   
        
                                                                   
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
        #return (Model.decomposeId(code)==(0,0,0)) # Only the central store
        return (code in self.factoryProductFilterDict.keys())

    def isClinic(self,storeDict,code):
        wh= storeDict[code]
        return (isinstance(wh,warehouse.Clinic) or isinstance(wh,warehouse.AttachedClinic))

    def clinicShipQuantityFunc(self, fromW, toW, pullMeanFrequency, timeNow):
        assert(isinstance(toW,warehouse.Clinic))
        assert(hasattr(toW,"idcode")) # added when the wh was constructed
        # These are the warehouses with 'pull' shipments.  This function will be
        # called once at start-up time, before the MonthlyOrderProcess's have
        # installed an instantaneous demand for the downstream clinics.
        dosesNeededVC= toW.shippingDemandModel.getDemandExpectation(toW.getPopServedPC(),
                                                                    self.clinicTickInterval)
        dosesNeededVC *= 1.0
        clinicVC= self._scaleDemandByType(dosesNeededVC)
        onhandVC= self.sim.shippables.getCollectionFromGroupList(toW.getStore().theBuffer)
        lowVC=  clinicVC - onhandVC
        lowVC.floorZero()
        lowVC.roundUp()
        lowVC = self.sim.shippables.addPrepSupplies(lowVC)

        #print "clinic %s fed by %s at %f: clinicVC %s"%(toW.name,fromW.name,timeNow,clinicVC)
        #print "clinic %s fed by %s at %f: lowVC %s"%(toW.name,fromW.name,timeNow,lowVC)
        return lowVC

    def clinicShipThresholdFunc(self, toW, pullMeanFrequency):
        assert(isinstance(toW,warehouse.Clinic))
        dosesNeededVC= toW.shippingDemandModel.getDemandExpectation(toW.getPopServedPC(),
                                                                    self.clinicTickInterval)
        dosesNeededVC *= 0.25 # for safety stock
        vialsVC= self._scaleDemandByType(dosesNeededVC)
        vialsVC = self.sim.shippables.addPrepSupplies(vialsVC)        
        return vialsVC

    def warehouseShipQuantityFunc(self, fromW, toW, pullMeanFrequency, timeNow):
        # These are the warehouses with 'pull' shipments.  This function will be
        # called once at start-up time, before the MonthlyOrderProcess's have
        # installed an instantaneous demand for the downstream clinics.
        dosesVC= self.demandModel.getDemandExpectation(toW.getTotalDownstreamPopServedPC(),
                                                       pullMeanFrequency)
        dosesVC *= 1.25
        demandDownstreamVC= self._scaleDemandByType(dosesVC)
        onhandVC= self.sim.shippables.getCollectionFromGroupList(toW.getStore().theBuffer)
        lowVC= demandDownstreamVC - onhandVC
        lowVC.floorZero()
        lowVC.roundUp()
        lowVC = self.sim.shippables.addPrepSupplies(lowVC)
        #print "warehouse %s fed by %s: demandDownstreamVC %s"%(toW.name,fromW.name,demandDownstreamVC)
        #print "warehouse %s fed by %s: myAttachedClinicsVC %s"%(toW.name,fromW.name,myAttachedClinicsVC)
        #print "warehouse %s fed by %s: onhandVC %s"%(toW.name,fromW.name,onhandVC)
        #print "warehouse %s fed by %s: lowVC %s"%(toW.name,fromW.name,lowVC)
        return lowVC

    def warehouseShipThresholdFunc(self, toW, pullMeanFrequency):
        # These are the warehouses with 'pull' shipments.  This function will be
        # called once at start-up time, before the MonthlyOrderProcess's have
        # installed an instantaneous demand for the downstream clinics.
        dosesVC= self.demandModel.getDemandExpectation(toW.getTotalDownstreamPopServedPC(),
                                                       pullMeanFrequency)
        whatWeWantToOrderVC= self._scaleDemandByType(dosesVC)
        whatWeWantToOrderVC = self.sim.shippables.addPrepSupplies(whatWeWantToOrderVC)
        fVC,cVC,wVC= toW.calculateStorageFillRatios(whatWeWantToOrderVC)
        whatFitsVC= whatWeWantToOrderVC*(fVC+cVC+wVC)
        threshVC= whatFitsVC*0.25
        threshVC.roundDown()
        return threshVC

    def getScheduledShipmentSize(self, fromW, toW, shipInterval, timeNow):
        assert(hasattr(toW,"idcode")) # added when the wh was constructed
        # The function is called repeatedly, every time a shipment is being set up.
        # The downstream demand will include any attached clinics, and includes 
        # safety stock.
        demandDownstreamVialsVC= toW.getInstantaneousDemandVC(shipInterval)
        if isinstance(toW,warehouse.Clinic):
            # The demand will be exactly as specified- no buffer.
            # This must now be scaled by available space so that we don't end up immediately
            # discarding things on delivery.
            fVC,cVC,wVC= toW.calculateStorageFillRatios(demandDownstreamVialsVC)
            fillVC= fVC+cVC+wVC
            scaledShipVC= demandDownstreamVialsVC*fillVC
            scaledShipVC.roundDown()
            return scaledShipVC
        else:
            # Warehouses try for a buffer stock of 1.25.
            demandDownstreamVialsVC *= 1.25
            # This must now be scaled by available space so that we don't end up immediately
            # discarding things on delivery.
            fVC,cVC,wVC= toW.calculateStorageFillRatios(demandDownstreamVialsVC)
            fillVC= fVC+cVC+wVC
            scaledShipVC= demandDownstreamVialsVC*fillVC
            scaledShipVC.roundDown()
            # We subtract only part of our on-hand supply- this helps stabilize the buffer stock level
            onhandVC= self.sim.shippables.getCollectionFromGroupList(toW.getStore().theBuffer)
            lowVC= scaledShipVC - (onhandVC*0.8) # the factor is to provide for the 1.25 safety stock
            lowVC.floorZero()
            lowVC.roundUp()
            return lowVC

    def _scaleDemandByType(self, shipDosesVC):
        """
        Input is in doses; output in vials rounded up.  
        The 'wastage' bit is a hack to implement some estimated
        wastage constants peculiar to Vietnam.
        """
        shipVialsTupleList= [(v,n/v.getNDosesPerVial())
                             for v,n in shipDosesVC.getTupleList()]
        scaledTupleList= []
        for v,nVials in shipVialsTupleList:
            if self.updateWasteEstimateFreq > 0:
                wastage = 1.0-self.wastageEstimates[v]
            else:
                wastage= 1.0
    
                if v.name=="V_Tuberculosis": wastage= 1.0-0.38
                elif v.name=="V_HepB": wastage= 1.0-0.04
                elif v.name=="V_DTP": wastage= 1.0-0.15
                elif v.name=="V_DTP-HepB": wastage= 1.0-0.10
                elif v.name=="V_Oral Polio": wastage= 1.0-0.20
                elif v.name=="V_Measles": wastage= 1.0-.27
                elif v.name=="V_JE": wastage= 1.0-0.04
                elif v.name=="V_MMR": wastage= 1.0-0.04
                elif v.name=="V_MR": wastage= 1.0-0.04
                #elif v.name=="V_MMR": wastage= 0.99
                elif v.name=="V_Diphtheria-tetanus-lowdose": wastage= 1.0-0.20
                #elif v.name=="V_DTP_HB_Hib_1 dose": wastage= 1.0-0.0
                #elif v.name=="V_DTP_HB_Hib_2 dose": wastage= 1.0-0.4
                #elif v.name=="V_DTP_HB_Hib_10 dose": wastage= 1.0-0.10
                elif v.name=="V_Pneumococcal": wastage= 0.9
                elif v.name=="V_DTP_HB_Hib_small": wastage= 0.9
                elif v.name=="V_DTP_HB_Hib_large": wastage= 0.9
                elif v.name=="V_HPV_small": wastage= 0.9
                elif v.name=="V_HPV_large": wastage= 0.9
                elif v.name=="V_Rotavirus_small": wastage= 0.9
                elif v.name=="V_Rotavirus_large": wastage= 0.9
                elif v.name=="V_MMR-unidose": wastage= 1.0-0.0
                elif v.name=="V_Measles-unidose": wastage= 1.0-0.0
                elif v.name in ["V_RotavirusV1",
                                "V_RotavirusV2",
                                "V_RotavirusV3",
                                "V_RotavirusV4",
                                "V_RotavirusV5",
                                "V_RotavirusV6",
                                "V_Rotavirus"]: wastage= 0.9
                elif v.name=="V_Influenza": wastage= 0.9
                elif v.name=="V_Dengue": wastage = 1.0-0.05 
                elif v.name=='V_DTwP': wastage= 1.0-0.15
                elif v.name=='V_Cholera': wastage= 1.0-0.15
                elif v.name=='V_Tetanus_Toxoid': wastage= 1.0-0.15
                else:
                    raise RuntimeError("Don't know wastage for %s"%v.name)
            scaledTupleList.append( (v,int(math.ceil(nVials/wastage))) )
        #print "%s: %s %s"%(toW.name,shipDosesVC,["%s:%d"%(v.name,n) for v,n in scaledTupleList])
        return self.sim.vaccines.getCollection(scaledTupleList)

    def addedCatchupDemand(self, storeDict, cudemand):
        assert(isinstance(cudemand,demandmodel.CatchupDemandModel))
        ## First obtain the catch for the districts
        catchupPrefix = 'cu_'
        
        with openDataFullPath(cudemand.catchupDemandFileName,'rU') as f:
            keyList,recList= csv_tools.parseCSV(f)
        catchupDict = {}
        ## Dictionary of PeopleCollections that holds the total additional demand
        
        ## Create new people types for the catchup campaign
        for peopleKey in keyList:
            if peopleKey != 'District':  
                if not self.sim.people.validTypeName(catchupPrefix + str(peopleKey)):
                    raise RuntimeError("CatchupDemandFile has non-existent peopletype %s"%catchupPrefix+str(peopleKey))

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
                self.sim.outputfile.write('District Name = ' + districtName + '\n')
                districtWarehouse = warehouse.getStoreByName(storeDict,districtName)
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
                ## commpute the proportional factors
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
                if G.debug is True:
                    print "Clinic: %s %s"%(clinic.name,clinic.getPopServedPC())         
        
    def getApproxScalingVC(self,storeDict,code):
        wh= storeDict[code]
        # This should get customized for the specific warehouse, but I don't know the pattern for Vietnam
        tickInterval= 28.0
        vC = self.demandModel.getDemandExpectation(wh.getTotalDownstreamPopServedPC(),
                                                     tickInterval)
        vC = self.sim.shippables.addPrepSupplies(vC)
        return vC

    def _getFactoryProductionVC(self, factory, daysSinceLastShipment, timeNow,
                               daysUntilNextShipment):
        assert(hasattr(factory.targetStore,"idcode")) # added when the wh was constructed
        
        demandDownstreamVialsVC= factory.targetStore.getInstantaneousDemandVC(daysUntilNextShipment)
        onhandVC= self.sim.shippables.getCollectionFromGroupList(factory.targetStore.getStore().theBuffer)
        lowVC= demandDownstreamVialsVC - (onhandVC*0.8) # the factor is to provide for the 1.25 safety stock
        # Filter to only allow delivery of this factory's products
        filteredLowVC= lowVC*self.factoryProductFilterDict[factory.targetStore.idcode]
        filteredLowVC.floorZero()
        filteredLowVC.roundUp()
        return filteredLowVC

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
        """
        return 0.0 

    def getTruckInterval(self,storeDict,code):
        return self.truckInterval

    def getShipStartupLatency(self,storeDict,code):
        raise RuntimeError("getShipStartupLatency is superceded by route file info for the Vietnam model")
#        wh= storeDict[code]
#        if code==1:
#            # central store
#            return Model.centralStoreStartupLatency
#        elif code in [2,10,18,33]:
#            # regional store
#            return Model.regionalStoreStartupLatency
#        elif (isinstance(wh,warehouse.Clinic) or isinstance(wh,warehouse.AttachedClinic)):
#            # clinic or attached clinic
#            raise RuntimeError("Scheduled shipments originating from clinics are not supported. (getStatupLatency)")
#        else:
#            return Model.districtStoreStartupLatency

    def getOrderPendingLifetime(self,storeDict,code):
        return self.orderPendingLifetime

    def getShipInterval(self,storeDict,code):
        raise RuntimeError("getShipInterval is superceded by route file info for the Vietnam model.")
            
    def getPullControlFuncs(self,storeDict,code):
        if self.isClinic(storeDict,code):
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
        # return code as is unless code is an attached clinic
        if code<10000:
            return None           
        else:
            return (code % 10000)
    
    def getUseVialsProcess(self,storeDict,code):
        wh= storeDict[code]
        if self.isClinic(storeDict,code):
            totalLatency= wh.useVialsLatency
            tickInterval= self.clinicTickInterval
            patientWaitInterval= self.patientWaitInterval
            if code<10000:
                useVials= warehouse.UseOrDiscardVials(wh,
                                                      tickInterval,
                                                      patientWaitInterval,
                                                      C.useVialPriority,
                                                      totalLatency)
            else:
                useVials= warehouse.UseVialsSilently(wh,
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

        #print 'Remove the following line!'
        rec['Device Utilization Rate']= 0.9
        #print 'Remove the preceeding line!'

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
        if rec.has_key('UseVialsLatency'):
            clinicLatency = rec['UseVialsLatency']
        else:
            clinicLatency = self.clinicStartupLatency
        if rec.has_key('UseVialsInterval'):
            clinicInterval = rec['UseVialsInterval']
        else:
            clinicInterval = self.clinicTickInterval

        w= None
        storageSpace= self._storageSpaceFromTableRec(rec,sUF)
        storageSC= self._getTotalVolumeSC(storageSpace)
        totalStorage= sim.storage.getTotalRefrigeratedVol(storageSC)
        if issubclass(expectedType, warehouse.AttachedClinic) and totalStorage>0.0:
            raise RuntimeError('The Stores file information for %s says it has storage, but it is an Attached Clinic'%wh.name)
        coolStorage= sim.storage.getTotalCoolVol(storageSC)
        if not isClinic:
            # This is a warehouse
            targetPopPC= self.sim.people.getCollection() # These don't have an actual local target pop
            w= warehouse.Warehouse(sim,sim.vaccines.getActiveTypes(),
                                   storagetypes.storageTypes,
                                   storageSpace,
                                   targetPopPC,
                                   func=function,category=category,name=name,
                                   breakageModel=brModel,
                                   latitude=latitude,longitude=longitude)
            w.setNoteHolder(sim.notes.createNoteHolder())
            #print w.category,w.name
        elif function=='Administration' and (coolStorage==0.0 or issubclass(expectedType,warehouse.AttachedClinic)):
            # This is an attached clinic
            #print w.category, w.function, w.name
            w= warehouse.AttachedClinic(sim,None,
                                        targetPopPC,
                                        name=name, breakageModel=brModel, demandModel=self.demandModel,
                                        useVialsLatency=clickLatency)
            w.setNoteHolder(sim.notes.createNoteHolder())
            w.orderProcess= MonthlyOrderProcess(clinicInterval,
                                                clickLatency+1.0,
                                                w)
            self.sim.activate(w.orderProcess,w.orderProcess.run())
        elif function=='Surrogate':
            assert(code>10000)
            w= warehouse.AttachedClinic(sim, None,
                                        targetPopPC,
                                        name=name, breakageModel=brModel, demandModel= self.demandModel,
                                        useVialsLatency=clinicLatency)
            # Surrogates get no NoteHolders to reduce the number of statistics they generate
#            w.orderProcess= MonthlyOrderProcess(self.clinicTickInterval,
#                                                self.clinicStartupLatency+1.0,
#                                                w)
            w.orderProcess= MonthlyOrderProcess(clinicInterval,
                                                clinicLatency+1.0,
                                                w)
            self.sim.activate(w.orderProcess,w.orderProcess.run())
        else:
            # This is a clinic
            w= warehouse.Clinic(sim, sim.vaccines.getActiveTypes(),
                                storagetypes.storageTypes,
                                storageSpace,
                                targetPopPC,
                                func=function,category=category,name=name,breakageModel=brModel,
                                demandModel=self.demandModel,
                                latitude=latitude,longitude=longitude,
                                useVialsLatency = clinicLatency)

            w.orderProcess= MonthlyOrderProcess(clinicInterval,
                                                clinicLatency+1.0,
                                                w)
            self.sim.activate(w.orderProcess,w.orderProcess.run())
            w.setNoteHolder(sim.notes.createNoteHolder())
        if w.noteHolder is not None:
            w.noteHolder.addNote({"name":name,"code":code,
                                  "category":category, "function":function})
            for st,vol in storageSC.items():
                w.noteHolder.addNote({(st.name+"_vol"):vol/C.ccPerLiter})
        # Attach the idcode to the warehouse, for convenience later.
        w.idcode= code
        return w
            

