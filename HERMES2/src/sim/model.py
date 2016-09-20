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


__doc__=""" model.py
This is meant to be a base class for all models.  Every HERMES
simulation has one Model, which describes the situation being
simulated.  That model is a derived class of this base class.
"""
_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math,zipfile
import globals as G

import abstractbaseclasses
import csv_tools
import constants as C
import recorders
import typemanager
import vaccinetypes
import trucktypes
import peopletypes
import fridgetypes
from util import openDataFullPath, filteredWriteCSV, openOutputFile, parseInventoryString
from noteholder import NoteHolderGroup
import warehouse
import csv_tools
import demandmodel
import util
from copy import copy, deepcopy
import shadow_network as shd



def parseInventoryString(string):
    ret = []
    string = unicode(string).strip()
    if string is None:
        return ret
    if string in ['', 'None']:
        return ret

    words = string.split('+')
    for word in words:
        bits = word.split('*')
        if len(bits) == 2:
            count = int(bits[0])
            name = bits[1].strip()
        elif len(bits) == 1:
            count = 1
            name = word.strip()
        else:
            raise RuntimeError('Unparsable Storage description %s'%string)
        ret.append((count, name))
    return ret

class Model:
    lotsOfSpaceLiters= 1.0e9; # used for room temp storage
    class UpdateWastageEstimates(warehouse.PeriodicProcess):
        def __init__(self,sim,updatefreq,startupLatency):
            warehouse.PeriodicProcess.__init__(self,sim,"UpdateWastage",updatefreq,startupLatency)
        def cycle(self,timeNow):
            for v,n in self.sim.model.wastageEstimates.getTupleList():
                if isinstance(v,abstractbaseclasses.HasOVW):
                    self.sim.model.wastageEstimates[v] = v.computeWastage()
            if self.sim.debug == True:
                print "Model Wastage Estimate at %d = %s"%(self.sim.now(),str(self.sim.model.wastageEstimates))
    
    def __init__(self, sim):
        """
        sim is an instance of HermesSim; this model instance will exist in the context
        of that simulation.  Derived classes are expected to define daysPerMonth and
        daysPerYear; those quantities are not defined here so that errors will be produced
        if the derived class fails to do so.
        """
        self.reportingInterval = 1
        self.sim= sim
        
        
    def initializeOVWEstimates(self):
        """
        The model carries a table of open vial waste estimates, but that table cannot be built
        until model initialization is otherwise complete because the model's creation of the
        relevant DemandModels determines which vaccine types will be active.  It is generally
        not necessary for the derived class to override this function.
        
        This routine loads a table of OVW estimates if the user has provided one.  This is
        a CSV file containing at least the columns 'Name' (matching the row in the vaccine
        definition file) and 'OVW', a value between 0.0 and 1.0 with 0.0 indicating perfect
        efficiency.  
        
        The model can prevent this initialization process simply by defining its own value
        for the 'wastageEstimates' attribute.
        """
        if not hasattr(self,'wastageEstimates'):
            if self.sim.userInput['initialovw'] is None:
                ## start this estimates out at something reasonable
                wasteTupleList = []
                for v in self.sim.vaccines.getActiveTypes():
                    if isinstance(v,vaccinetypes.VaccineType):
                        wasteTupleList.append((v,0.5))
                    else:
                        wasteTupleList.append((v,0.0))
                self.wastageEstimates = self.sim.vaccines.getCollection(wasteTupleList)
            else:
                if self.sim.shdNet is not None:
                    keys, recDicts = self.sim.shdNet.getInitialOVWRecs()
                else:
                    with openDataFullPath(self.sim.userInput['initialovw'],'rU') as f:
                        keys,recDicts= csv_tools.parseCSV(f)
                    for k in ['Name','OVW']:
                        assert(k in keys)
                d= {}
                for r in recDicts: 
                    d[r['Name']]= r
                wasteTupleList = []
                for v in self.sim.vaccines.getActiveTypes():
                    if isinstance(v,abstractbaseclasses.HasOVW):
                        ovw= float(d[v.name]['OVW']) # raises exception if that vaccine is missing
                        assert(ovw>=0.0 and ovw<=1.0)
                    else:
                        ovw= 0.0
                    wasteTupleList.append((v,ovw))
                self.wastageEstimates= self.sim.vaccines.getCollection(wasteTupleList)
                
    def _clinicShipQuantityFunc(self, fromW, toW, pullMeanFrequencyDays, timeNow):
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")

    def _clinicShipThresholdFunc(self, toW, pullMeanFrequencyDays):
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")

    def _warehouseShipQuantityFunc(self, fromW, toW, pullMeanFrequencyDays, timeNow):
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")

    def _warehouseShipThresholdFunc(self, toW, pullMeanFrequencyDays):
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")

    def addedCatchupDemand(self, storeDict,catchupdemandmodel):
        """
        This is a function that should calculate the added
        demand associated with a catchup campaign.
        """
        raise RuntimeError("The specific derived model class must "\
                           + "define this method")


    def getScheduledShipmentSize(self, fromW, toW, shipInterval, timeNow):
        """
        Given the source and destination warehouses (fromW and toW) and
        the interval between shipments, return a VaccineCollection giving
        the size of the scheduled shipment.  This is called once at the
        beginning of the simulation for ScheduledShipment (push) delivery 
        routes, and once per shipment (slightly before the shipment time) 
        for ScheduledVariableSizeShipment (varpush) delivery routes.
        For pull-type shipment control, see getPullControlFuncs() .
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")

    def getDeliverySize(self, toW, availableVC, shipInterval, timeNow):
        """
        For those rare shipping patterns where the truck may not drop off the full
        size of an order, for example in the VillageReach shipping pattern.  This
        method is called for some particular route types immediately before the
        delivery is actually transferred to toW, and the amount delivered is
        the lesser of the returned VaccineCollection and availableVC.
        """
        raise RuntimeError("The model class must define this special-purpose method")
        
    def getModelMonthlyOrderProcess(self):
        """
        returns the MonthlyOrderProcess object appropriate to the specific model
        that is being used.
        """
        raise RuntimeError("The specific derived model class must "\
                           + "define this method")
        
          
    def getDemandModel(self, storeDict, code):
        """
        returns a DemandModel object appropriate to the specified warehouse
        or clinic, or None if the direct patient demand is zero.
        """
        raise RuntimeError("This function is obsolete- if it is getting called, code needs to get fixed")

    def getApproxScalingVC(self,storeDict,code):
        """
        Feturns a VaccineCollection giving a rough scale for the
        number of vials of each type passing through the warehouse.
        This is used only to scale graphs; it does not effect the
        actual simulation.
        """
        return self.sim.vaccines.getCollection([(v,100.0)
                                                for v in vaccinetypes.activeVaccineTypes])

    def getFactoryProductionFunction(self,storeDict,code):
        """
        If the given Warehouse should have an attached Factory, return a
        function with signature:
        
        vaccineCollection getProductionVC(factory, daysSinceLastShipment, timeNow,
                                          daysUntilNextShipment)
                                          
        If the warehouse should not get an attached factory, return None.
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")        

    def getFactoryStartupLatency(self,storeDict,code):
        """
        If the given Warehouse should have an attached Factory, return
        the delay in days before the factory's first shipment is delivered.
        If the given Warehouse has no factory (in which case getFactoryYearlyProduction
        will have returned None), this function will not be called or its return value 
        will be ignored.
        """
        return 0.0

    def getFactoryBatchInterval(self,storeDict,code):
        """
        Return the interval in days between deliveries from the factory
        attached to this warehouse.
        """
        if hasattr(self,"factoryBatchInterval"):
            return self.factoryBatchInterval
        else:
            raise RuntimeError("The model must provide a 'factoryBatchInterval' or "\
                               +"reimplement Model.getFactoryBatchIntervalInterval()")

    def getTruckInterval(self,storeDict,code):
        """
        Returns the minimum time in days between truck departures of a specific
        truck from this warehouse.  For fixed-interval shipments this will
        typically be the same as the value returned by getShipInterval. In this
        case the value expected from the model's getTruckInterval method gives
        the actual time between truck trips; the value from the getShipInterval
        method gives the time between the placement of orders. For variable-
        interval (pull) shipments this will set the minimum number of days
        between departures of the pull shipment.  If the value 'ShipIntervalDays'
        is present in the file defining routes, that value will supersede this
        function.
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")        

    def getShipStartupLatency(self,storeDict,code):
        """
        Returns the number of days' delay before shipping processes
        leaving this warehouse start up.
        """
        return 0.0

    def getOrderPendingLifetime(self,storeDict,code):
        """
        Returns the number of days for which an order to get resources
        from this warehouse can remain pending before it is dropped
        because it cannot be even partially filled.
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")        

    def getShipInterval(self,storeDict,code):
        """
        Returns the number of days between scheduled shipments from this
        warehouse.   This value is only relevant for fixed-interval shipments.
        Typically this will be the same as the value returned by
        getTruckInterval.  The value expected from the model's getTruckInterval
        method gives the actual time between truck trips; the value from the
        getShipInterval method gives the time between the placement of orders.
        If the value 'ShipIntervalDays' is present in the file defining routes,
        that value will supersede this function.
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")

    def getPullMeanFrequency(self,storeDict,code):
        """
        Returns the average number of days planned between pull shipments originating
        from this warehouse.  The actual interval will vary depending on demand,
        but this value is the 'planning target'.
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")
        

    def getPullControlFuncs(self,storeDict,code):
        """
        Returns a tuple (tFunc,qFunc) containing functions giving
        the warehouse's reorder threshold and order quantity functions.
        The signatures of the functions are:

        vaccineCollection= tFunc(warehouse, pullMeanFrequencyDays)
        vaccineCollection= qFunc(fromWarehouse,toWarehouse,pullMeanFrequencyDays,currentTime)
        """
        if Model.getDemandModel(storeDict,code) is None:
            tFunc= Model._warehouseShipThresholdFunc
            qFunc= Model._warehouseShipQuantityFunc
        else:
            tFunc= Model._clinicShipThresholdFunc
            qFunc= Model._clinicShipQuantityFunc
        return (tFunc,qFunc)

    def getDefaultSupplier(self,storeDict,code):
        """
        If no supplier is explicitly specified for a warehouse, this
        function is called for that warehouse.  If it returns an idcode
        value, a 'pull' shipment is created between the warehouse
        specified by idcode and the given warehouse.  If it returns
        None, no such route is created and the warehouse is left without
        a supplier.
        """
        return None

    def getDefaultTruckTypeName(self,fromWH,toWH):
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,
        return the name of the truck type to be used to implement the
        implied 'pull' shipment to be created.
        """
        return "default"
    
    def getDefaultTruckInterval(self,fromWH,toWH):
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,
        return the minimum number of days between departures to be used
        to implement the implied 'pull' shipment.
        """
        return 0.0

    def getDefaultPullMeanFrequency(self,storeDict,code):
        """
        If no supplier is explicitly specified for a warehouse and
        getDefaultSupplier() returns a valid idcode for that warehouse,        
        return the average number of days planned between pull shipments originating
        from this warehouse.  The actual interval will vary depending on demand,
        but this value is the 'planning target'.
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")

    def getUseVialsProcess(self,storeDict,code):
        """
        returns a UseVials process appropriate to the specified warehouse
        or clinic, or None if the direct patient demand is zero.
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")        

    def getUseVialsTickIntervalDays(self,storeDict,code):
        """
        Returns the number of days between days when this clinic is 'open';
        for example if the clinic operates one day a week this function
        should return the value 7.0.
        """
        raise RuntimeError("This function is obsolete; anything that calls it is broken")        

    def getUseVialsStartupLatencyDays(self,storeDict,code):
        """
        Returns the number of days' delay before the clinic should start
        its operating cycle.
        """
        raise RuntimeError("This function is obsolete; anything that calls it is broken")        
        
    def warehouseOrClinicFromRec(self, sim, rec,
                                 recordTheseStoresDict={},
                                 recordTheseVaccineNames=[]):
        """
        This function takes a record (itself a dictionary) as stored in the file
        returned by getWarehouseFile, and constructs and returns a Warehouse or
        Clinic.  The 'sim' parameter is the HermesSim instance into which the
        warehouse is to be defined.  The 'recordThese' parameters
        are provided in case the model wants to construct and attach
        a custom RMonitor or RTally.  They can be ignored, in which
        case the network building system will add appropriate recorders.
        """
        raise RuntimeError("The specific derived model class must "\
                           +"define this method")        

           
    def getWarehouseFile(self):
        """
        Return the name of a .csv file specifying the warehouses and
        clinics to be included in the simulation.  The records from the
        file are subsequently processed by warehouseOrClinicFromRec().
        The .csv file must contain a column named 'idcode' with a unique
        long interger code for each warehouse; otherwise the table may
        have any form.
        """
        if hasattr(self,"warehouseFile"):
            return self.warehouseFile
        else:
            raise RuntimeError("The model must provide a 'warehouseFile' or "\
                               +"reimplement Model.getWarehouseFile()")

    def getRouteFile(self):
        """
        Return the name of a .csv file specifying the shipping routes
        to be used in the simulation.  Warehouses or clinics for which
        no route is specified may still acquire a default route, via
        getDefaultSupplier() and getDefaultTruckTypeName().
        """
        if hasattr(self,"routeFile"):
            return self.routesFile
        else:
            raise RuntimeError("The model must provide a 'routeFile' or "\
                               +"reimplement Model.getRouteFile()")

    def getPatientWaitInterval(self,storeDict,code):
        """
        Return the interval in days for which a patient will wait at
        a clinic for a shipment of an unavailable vaccine.  A typical
        return value would be 0.3.
        """
        raise RuntimeError("This function is obsolete- any code that calls it needs to be fixed")

    def getBurninDays(self):
        """
        Return the total number of 'burn-in' days in the simulation, over
        which the simulation runs but statistics are not gathered.
        """
        if hasattr(self,"burninDays"):
            return self.burninDays
        else:
            raise RuntimeError("The model must provide a 'burninDays' or "\
                               +"reimplement Model.getBurninDays()")

    def getRunDays(self):
        """
        Return the number of days over which the simulatin should run and
        gather statistics.  
        """
        if hasattr(self,"runDays"):
            return self.runDays
        else:
            raise RuntimeError("The model must provide a 'runDays' or "\
                               +"reimplement Model.getRunDays()")

    def getTotalRunDays(self):
        """
        Return the total number of days the simulation should run, including
        burn-in.  The base method returns getBurninDays()+getRunDays()
        """
        return self.getBurninDays() + self.getRunDays()

    @classmethod
    def getReportingInterval(self):
        """
        If a journal file is requested to capture the time history of
        the entire simulation, how often in days should history entries
        be recorded?
        """
        return self.reportingInterval

    def checkSummary(self, fileNameRoot='report', clear=False):
        """
        This function can be called at any point to write summary files.
        It does not return a value.
        
        If fileNameRoot is 'report' (the default), the per-store summary
        file will be called 'report.csv' and the condensed summary will be 
        called  'report_summary.csv'.  If clear is True, the summary statistics
        will be cleared after the summary is written.  This feature can be used
        to write periodic summaries of sub-parts of the simulation.
        """
        if fileNameRoot[-4:]=='.csv':
            fileNameRoot= fileNameRoot[:-4]

        self.sim.statsManager.writeStatsRecordList(fileNameRoot+'_stats.csv',
                                                   self.sim.allReportingHierarchies[0])
        
        allKeys = set()
        allRecs = []
        sim = self.sim
        for tp in util.createSubclassIterator(typemanager.SubTypeManager,
                                              lambda c: len(c.__subclasses__()) == 0):
            entityList = getattr(sim, tp.subTypeKey).getActiveTypes()
            for entity in entityList:
                sDict = entity.getSummaryDict()
                for k in sDict.keys():
                    if k not in allKeys:
                        allKeys.add(k)
                allRecs.append(sDict)
        allKeys = list(allKeys)
        allKeys.sort()
        
        if self.sim.userInput.fromDb:
            self.sim.results.addSummaryRecs(self.sim.shdNet, allRecs)
        else:
            with openOutputFile(fileNameRoot+"_summary.csv","w") as f:
                filteredWriteCSV(f,allKeys,allRecs,quoteStrings=True)
        
        if self.sim.userInput.fromDb:
            self.sim.costManager.writeCostRecordsToResultsEntry(self.sim.shdNet,
                                                                self.sim.allReportingHierarchies[0],
                                                                self.sim.results)
            self.sim.notes.writeNotesToResultsEntry(self.sim.shdNet, self.sim.results)
        else:
            self.sim.costManager.writeCostRecordList(fileNameRoot+'_costs.csv',
                                                     self.sim.allReportingHierarchies[0])
            self.sim.notes.writeNotesAsCSV(fileNameRoot+'.csv')
            keys,recs = self.sim.statsManager.generateStatsRecordInfo(self.sim.allReportingHierarchies[0])
            #print "Keys in Model: {0}".format(keys)
            csv_tools.castColumn(recs,'ReportingLevel',csv_tools.castTypes.STRING)
            csv_tools.castColumn(recs,'ReportingBranch',csv_tools.castTypes.STRING)
            with openOutputFile(fileNameRoot+"_timethroughsystem.csv") as f:
                vaxKeys = ["{0}_daysretention".format(n) for n in self.sim.vaccines.getActiveTypeNames()]
                vaxKeys.append("AllVaccines_daysretention")
                headString = u"ReportingLevel,ReportingBranch,"
                for v in vaxKeys:
                    headString += u"{0}_mean,{0}_median,{0}_max,{0}_min,".format(v)
                f.write("{0}\n".format(headString[:-1]))
                 
                 
                ### top first
                #for rec in recs:
                #    if rec['ReportingLevel'] == u'-top-':
                #        stringHere = u"{0},{1},".format(rec['ReportingLevel'],rec['ReportingBranch'])
                #        for v in vaxKeys:
                #            stringHere += u'{0},{1},{2},'.format(rec["{0}_mean".format(v)],rec["{0}_max".format(v)],rec["{0}_min".format(v)])
                #         
                #        f.write(u"{0}\n".format(stringHere[:-1]))
                #        break
                stringHere = u'--top--,--top--,'
                totalHisto = util.HistoVal([])
                for v in self.sim.vaccines.getActiveTypes():
                    d = v.getSummaryDict()
                    totalHisto += v.totalTransitHisto
                    stringHere += u'{0},{1},{2},{3},'.format(d['TransitTime_mean'],d['TransitTime_median'],
                                                             d['TransitTime_max'],d['TransitTime_min'])
                
                stringHere += u'{0},{1},{2},{3},'.format(totalHisto.mean(),totalHisto.median(),
                                                         totalHisto.max(),totalHisto.min())
                f.write(u'{0}\n'.format(stringHere[:-1]))
                
                ### Alls next
                recsToUse = {}
                for rec in recs:
                    if rec['ReportingLevel'] == u'all':
                        #print u"{0} : {1}".format(rec['ReportingLevel'],rec['ReportingBranch'])
                        recsToUse[rec['ReportingBranch']] = rec
                 
                for level in self.levelList:
                    rec = recsToUse[level]
                    stringHere = u"{0},{1},".format(rec['ReportingLevel'],rec['ReportingBranch'])
                    for v in vaxKeys:
                        stringHere += u'{0},{1},{2},{3},'.format(rec["{0}_mean".format(v)],
                                                             rec["{0}_median".format(v)],
                                                             rec["{0}_max".format(v)],
                                                             rec["{0}_min".format(v)])
                     
                    f.write(u"{0}\n".format(stringHere[:-1]))
                 
                ### now the individual locations   
                for level in self.levelList:
                    
                    for rec in recs:
                        if rec['ReportingLevel'] == level:
                            stringHere = u"{0},{1},".format(rec['ReportingLevel'],rec['ReportingBranch'])
                            stringOrig = stringHere
                            writeFlag = False    
                            for v in vaxKeys:
                                if u"{0}_mean".format(v) in rec.keys():
                                    writeFlag = True
                                    stringHere += u'{0},{1},{2},{3},'.format(rec["{0}_mean".format(v)],
                                                                         rec["{0}_median".format(v)],
                                                                         rec["{0}_max".format(v)],
                                                                         rec["{0}_min".format(v)])
                                else:
                                    stringHere += u'0,0,0,0,'
                            #if stringHere != stringOrig:
                            if writeFlag:
                                f.write(u"{0}\n".format(stringHere[:-1]))
                         
                    
                        
#             with openOutputFile(fileNameRoot+"_retention_histograms.zip") as f:
#                 with zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED) as myzip:
#                     vaxKeys = ["%s_daysretention"%n for n in self.sim.vaccines.getActiveTypeNames()]
#                     for rec in recs:
#                         #print "{0} {1}".format(rec['ReportingLevel'],rec['ReportingLevel']==u'-top-')
#                         if rec['ReportingLevel'] == '-top-':
#                             print "vaxKeys = {0}".format(vaxKeys)
#                             print "-----------------------------------------"
#                             for k in rec.keys():   
#                                 print '{0}'.format(k)
#                             for vK in vaxKeys:
#                                 print u'{0}_raw'.format(vK) 
#                                 print u"{0}".format(u'{0}_raw'.format(vK) in rec.keys())
#                                 if u'{0}_raw'.format(vK) in rec.keys():
#                                     print u"{0}: {1}".format(vK,type(rec[u'{0}_raw'.format(vK)]))#.toJSON())
#                         for vK in vaxKeys:
#                             if vK in rec:
#                                 histo = rec[vK]
#                                 nm = vK[:-14]+'.histo' # trim off '_daysretention'
#                                 arcname = u"%s/%s/%s"%(rec['ReportingLevel'],rec['ReportingBranch'],nm)
#                                 if isinstance(arcname,types.UnicodeType): arcname = arcname.encode('utf-8')
#                                 arcname = '_'.join(arcname.split()) # remove whitespace
#                                 myzip.writestr(arcname, histo.toJSON())
#   
#           
#   
#           
#             with openOutputFile(fileNameRoot+"_transit_histograms.zip") as f:
#                 with zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED) as myzip:
#                     for rec in allRecs:
#                         if 'TransitTime' in rec:
#                             nm = rec['Name']+'.histo'
#                             if isinstance(nm, types.UnicodeType): arcname = nm.encode('utf-8')
#                             else: arcname = nm
#                             arcname = '_'.join(arcname.split()) # remove whitespace
#                             myzip.writestr(arcname, rec['TransitTime'].toJSON())
                  
        if clear:
            for wh in [r() for r in self.sim.warehouseWeakRefs if r() is not None]:
                wh.clearStockIntervalHistograms()
            self.sim.notes.clearAll(keepRegex='.*(([Nn]ame)|([Tt]ype)|([Cc]ode)|(_vol))')
            for manager in [self.sim.vaccines, self.sim.people, self.sim.trucks]:
                manager.resetAllCounters()
        self.sim.costManager.startCostingInterval()
        self.sim.statsManager.startStatsInterval()

    def calcPerDiemDays(self, tripJournal, homeWH):
        """
        This function is called once at the end of each full round trip for any
        shipping process to calculate the number of days of per diem pay the
        driver is to receive, based on the details of the just- completed trip.
        
        tripJournal is a list of tuples describing the steps of the just-completed trip.
        tripJournal entries all start with (stepname, legStartTime, legEndTime, legConditions...);
        see the description of warehouse.createTravelGenerator for additional details.

        homeWH is the warehouse which is the driver's 'home'; that is, where the driver
        might be expected to sleep for free. Typically legEndTime for one leg
        will equal legStartTime for the next.
        
        The return value of this function is expected to be a number.
        """
        totDays = 0.0
        currentWH = homeWH
        for tpl in tripJournal:
            op = tpl[0]
            if op == 'move':
                opString,legStart,legEnd,conditions,fromWH,toWH,litersCarried,miscCosts = tpl # @UnusedVariable
                currentWH = toWH
            else:                                
                legStart = tpl[1]
                legEnd = tpl[2]
                conditions = tpl[3]
            if conditions is None: conditions = 'normal'
            if homeWH.getKmTo(currentWH, currentWH.category, conditions) > 100.0:
                totDays += math.floor(legEnd)-math.floor(legStart)
        return totDays

    def _peopleCollectionFromTableRec(self,rec):
        return self.getPeopleCollectionFromTableRec(rec)
    
    def getPeopleCollectionFromTableRec(self,rec):
        tupleList= []
        for k,v in rec.items():
            if self.sim.people.validTypeName(k):
                if v=='': nThisType= 0
                else:
                    try:
                        nThisType = float(v)
                    except:
                        util.raiseRuntimeError("Unparsable number of %s-type people: <%s>"%(k,v))

                tupleList.append((self.sim.people.getTypeByName(k),nThisType))
        if len(tupleList)==0:
            if rec.has_key('Target Population'):
                nPeople= int(rec['Target Population'])
                if nPeople==0: 
                    return None
                else:
                    tupleList.append((self.sim.people.getTypeByName(peopletypes.genericPeopleTypeName),
                                      nPeople))
        return self.sim.people.getCollection(tupleList)
    
    def getTotalPopFromTableRec(self,rec):
        """
        This is a convenience function used by other modules that need to know if a record describes
        a population.
        """
        pC= self._peopleCollectionFromTableRec(rec)
        return pC.totalCount()
    
    def _storageSpaceFromTableRec(self,rec,storageUtilityFactor):
        
#        storageSpace= self.sim.fridges.fridgeTypeListFromTableRec(rec, storageUtilityFactor)
#
#        # Every warehouse gets a lot of room temperature storage
#        storageSpace.append(self.sim.fridges.getOnTheFlyFridgeType(self.sim.storage.roomtempStorage().name,
#                                                                   self.lotsOfSpaceLiters))
#        return storageSpace
    
        return [ thing.getType() for thing in self._inventoryFromTableRec(rec, storageUtilityFactor)
                if isinstance(thing,abstractbaseclasses.CanStore)]
    
    def _inventoryFromTableRec(self,rec,storageUtilityFactor):
        
        inventory= []
        
        # Exclude mutually exclusive column names
        for str1,str2 in [('CoolVolumeCC','CoolVolumeLiters')]:
            if str1 in rec and str2 in rec:
                raise RuntimeError('Input record contains both %s and %s columns- probably an error'%
                                   (str1,str2))
        
        # For the 'traditional' record fields, set things up so that the Warehouse.__init__()
        # method generates an on-the-fly fridge to match
        for stStr,key in [('freezer','VOL - (lit)'),('cooler','VOL + (lit)'),
                          ('freezer','Walk in -(lit)'),('cooler','Walk in +(lit)'),
                          ('cooler','CoolVolumeLiters')]:
            if key in rec:
                volLiters= storageUtilityFactor*float(rec[key])
                if volLiters>0.0:
                    inventory.append(self.sim.fridges.getOnTheFlyFridgeType(stStr,volLiters).createInstance())
        for stStr,key in [('cooler','CoolVolumeCC')]:
            if key in rec:
                volCC= storageUtilityFactor*float(rec[key])
                if volCC>0.0:
                    inventory.append(self.sim.fridges.getOnTheFlyFridgeType(stStr,volCC/C.ccPerLiter).createInstance())
        for column in ['Storage','Inventory']:
            if column not in rec:
                continue
            try:
                itemList = parseInventoryString(rec[column])
                for (fac,name) in itemList:
                    newType = self.sim.typeManager.getTypeByName(name, sim=self.sim)

                    if storageUtilityFactor != 1.0 and isinstance(newType, abstractbaseclasses.CanStoreType):
                        newType = self.sim.fridges.getPartiallyUtilizedFridge(newType, 
                                                                              storageUtilityFactor)

                    if isinstance(newType,trucktypes.TruckType):
                        for _ in xrange(fac): inventory.append(newType.createInstance())
                    elif isinstance(newType,abstractbaseclasses.GroupedShippableType):
                        inventory.append(newType.createInstance(count=fac))
                    else:
                        for _ in xrange(fac): inventory.append(newType.createInstance())
            except:
                import traceback
                traceback.print_exc()
                raise RuntimeError('Invalid storage description "%s" for location %s'%(rec[column],rec['NAME']))

        # Every warehouse gets a lot of room temperature storage
        inventory.append(self.sim.fridges.getOnTheFlyFridgeType(self.sim.storage.roomtempStorage().name,
                                                                self.lotsOfSpaceLiters).createInstance())

        return inventory
    
    def _perfectInventoryFromOrgInventory(self,inventory):
        inventoryPerf = copy(inventory)
        fridgeTypeList= [g.getType() for g in inventoryPerf if isinstance(g,abstractbaseclasses.CanStore)]
        ### Add to return list things that do not need to be made perfect
        inventoryPerf= [g for g in inventoryPerf if not isinstance(g,abstractbaseclasses.CanStore)]
        ### Add perfect fridges
        inventoryPerf += [g.createInstance() for g in self.sim.fridges.perfectFridgeTypeList(fridgeTypeList)]
        return inventoryPerf
    def _getTotalVolumeSC(self,storageSpace):
        """
        Returns a StorageCollection containing the total volume described in storageSpace.
        """
        assert all([isinstance(entry,abstractbaseclasses.CanStoreType) for entry in storageSpace]),\
            "Old-style storage tuple in what should be a list of FridgeTypes"
        return self.sim.fridges.getTotalVolumeSCFromFridgeTypeList(storageSpace)

    def _checkDemandModelDefinitionConflicts(self):
        """
        This routine checks for disallowed combinations of user input entries relating to
        demand model creation.  An exception is thrown if conflicts are found.
        """
        ui = self.sim.userInput
        for nm1,nm2 in [("demandfile","shippingdemandfile"),("demandfile","consumptiondemandfile"),
                        ("calendarfile","shippingcalendarfile"),("calendarfile","consumptioncalendarfile")]:
            if ui[nm1] is not None and ui[nm2] is not None:
                print '%s:%s and %s:%s'%(nm1,ui[nm1],nm2,ui[nm2])
                raise RuntimeError("The imput file specifies both %s and %s; this is not allowed."%(nm1,nm2))

        for nm1,nm2 in [("shippingdemandfile","consumptiondemandfile")]:
            if (ui[nm1] is None and ui[nm2] is not None) or (ui[nm1] is not None and ui[nm2] is None):
                raise RuntimeError("The input file specifies just one of %s and %s; this is not allowed."%\
                                   (nm1,nm2))

    def _generateDemandModel(self, daysPerYear, sampler=None, ignoreCalendarFile=False):
        ui = self.sim.userInput
        
        self._checkDemandModelDefinitionConflicts()
        if ui['demandfile'] is None:
            raise RuntimeError("The model requested input for demandfile but it was not provided")

        if ui['demanddayspattern'] is not None:
            dm = demandmodel.CalendarStringScaleDemandModel(self.sim,
                                                            ui['demandfile'],
                                                            ui['demanddayspattern'],
                                                            daysPerYear,
                                                            sampler,
                                                            shd.DemandEnums.TYPE_UNIFIED)
        elif ui['demanddaysbytypepattern'] is not None:
            print ui['demanddaysbytypepattern']
            words = [w.split(':',1) for w in ui['demanddaysbytypepattern']]
            patternDict = {w[0]:w[1] for w in words if self.sim.people.validTypeName(w[0])}
            print patternDict
            dm = demandmodel.CalendarStringScaleDemandModel(self.sim,
                                                            ui['demandfile'],
                                                            patternDict,
                                                            daysPerYear,
                                                            sampler,
                                                            shd.DemandEnums.TYPE_UNIFIED)
        elif ui['calendarfile'] is not None and not ignoreCalendarFile:
            if ui['calendarcycle'] is None or ui['calendarcycle']==0:
                raise RuntimeError("Calendar cycle time is not set- add 'calendarcycle' to your input file")
            dm = demandmodel.TabularCalendarScaleDemandModel(self.sim,
                                                             ui['demandfile'],
                                                             ui['calendarfile'],
                                                             ui['calendarcycle'],
                                                             daysPerYear,
                                                             sampler,
                                                             shd.DemandEnums.TYPE_UNIFIED)
        else:
            dm = demandmodel.TabularDemandModel(self.sim,
                                                ui['demandfile'],
                                                daysPerYear,
                                                sampler,
                                                shd.DemandEnums.TYPE_UNIFIED)

        if ui['scaledemandactual'] != 1.0 or ui['scaledemandexpected'] != 1.0:
            dm = demandmodel.ScaleVaxDemandModel(dm,
                                                 ui['scaledemandactual'],
                                                 ui['scaledemandexpected'])

        if ui['scaledemandbytypeactual'] is not None or ui['scaledemandbytypeexpected'] is not None:
            dm = demandmodel.ScaleVaxDemandByTypeModel(self.sim, 
                                                       dm,
                                                       ui['scaledemandbytypeactual'],
                                                       ui['scaledemandbytypeexpected'])

        return dm

    def _generateDemandModelTuple(self, daysPerYear, sampler=None, ignoreCalendarFile=False):
        """
        Parse the user input fields to determine the desired demand models, and return them
        as a tuple (shippingDemandModel, consumptionDemandModel).
        """
        self._checkDemandModelDefinitionConflicts()
        ui = self.sim.userInput

        # After the consistency checks in _checkDemandModelDefinitionConflicts(), the
        # presence of 'demandfile' implies that a single model has been specified.
        if ui['demandfile'] is not None:
            dm = self._generateDemandModel(daysPerYear, sampler, ignoreCalendarFile)
            return (dm,dm)
        else:
            if ui['shippingcalendarfile'] is not None:
                # consistency check guaranteed we have consumption file also
                if ui['calendarcycle'] is None or ui['calendarcycle']==0:
                    raise RuntimeError("Calendar cycle time is not set- add 'calendarcycle' to your input file")

                sdm = demandmodel.TabularCalendarScaleDemandModel(self.sim,
                                                                  ui['shippingdemandfile'],
                                                                  ui['shippingcalendarfile'],
                                                                  ui['calendarcycle'],
                                                                  daysPerYear,
                                                                  sampler,
                                                                  shd.DemandEnums.TYPE_SHIPPING)

            else:
                sdm = demandmodel.TabularDemandModel(self.sim,
                                                     ui['shippingdemandfile'],
                                                     daysPerYear,
                                                     sampler,
                                                     shd.DemandEnums.TYPE_SHIPPING)

            if ui['consumptioncalendarfile'] is not None:
                cdm = demandmodel.TabularCalendarScaleDemandModel(self.sim,
                                                                  ui['consumptiondemandfile'],
                                                                  ui['consumptioncalendarfile'],
                                                                  ui['calendarcycle'],
                                                                  daysPerYear,
                                                                  sampler,
                                                                  shd.DemandEnums.TYPE_CONSUMPTION)
            else:
                cdm = demandmodel.TabularDemandModel(self.sim,
                                                     ui['consumptiondemandfile'],
                                                     daysPerYear,
                                                     sampler,
                                                     shd.DemandEnums.TYPE_CONSUMPTION)



            if ui['scaledemandactual'] != 1.0 or ui['scaledemandexpected'] != 1.0:
                sdm = demandmodel.ScaleVaxDemandModel(sdm,
                                                      ui['scaledemandactual'],
                                                      ui['scaledemandexpected'])
                cdm = demandmodel.ScaleVaxDemandModel(cdm,
                                                      ui['scaledemandactual'],
                                                      ui['scaledemandexpected'])

            if ui['scaledemandbytypeactual'] is not None or ui['scaledemandbytypeexpected'] is not None:
                sdm = demandmodel.ScaleVaxDemandByTypeModel(self.sim, 
                                                            sdm,
                                                            ui['scaledemandbytypeactual'],
                                                            ui['scaledemandbytypeexpected'])
                cdm = demandmodel.ScaleVaxDemandByTypeModel(self.sim, 
                                                            cdm,
                                                            ui['scaledemandbytypeactual'],
                                                            ui['scaledemandbytypeexpected'])

            return (sdm,cdm)
