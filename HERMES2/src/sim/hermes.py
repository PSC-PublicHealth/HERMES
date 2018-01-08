#! /usr/bin/env python

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


__doc__=""" hermes.py
This is the class that will run and define a single HERMES simulation
"""
_hermes_svn_id_="$Id$"

import sys, os, optparse, types, socket
import time
import random
#from SimPy.Simulation import Simulation,Process,hold
from SimPy.SimulationStep import *
#from SimPy.SimulationTrace  import *
#import SimPy.SimulationTrace.SimulationTrace.SimulationTrace as Simulation

import constants as C
import globals as G
import curry
import util
import noteholder
import abstractbaseclasses
import typemanager
import storagetypes
import vaccinetypes
import peopletypes
import trucktypes
import fridgetypes
import icetypes
import recorders
import demandmodel
import warehouse
import input
from reporter import Reporter
#from report_stb import ReportDailyStock, ReportDailyTotalVaccinated
import networkbuilder as nbldr
import HermesOutput
import dummycostmodel
import costmodel
import statsmodel
import csv_tools
import csv_overlays
import geomanager
import shadow_network as shd
import load_networkrecords
import load_typemanagers
import eventlog

##############
# Notes-
# -my 'curry' is doing the case where len(args)<=1 incorrectly?
# -All the shipper processes serving clinics from a given warehouse have
#  the same name.
# -There is surely a better way to handle parallel code for freezer,
#  cooler, roomtemp in vaccinetypes.py
# -Are we using the priority values?  I think maybe they are obsolete.
##############

class BurninTrigger( Process ):
    def __init__(self,model,sim):
        Process.__init__(self,sim=sim)
        self.model = model
        self.burninTriggered = False
        self.burninTriggerDay = 0
    def run(self):
        yield hold,self,self.model.getBurninDays()
        self.sim.outputfile.write("\nBurnin complete at %g\n"%self.sim.now())
        self.sim.syncStatistics()
        self.sim.clearStatistics()
        self.sim.recorders.resetAll()
        self.sim.typeManager.resetAllCounters()
        self.sim.costManager.startCostingInterval()
        self.sim.statsManager.startStatsInterval()
        self.sim.notes.enableAll()
        self.burninTriggered = True
        self.burninTriggerDay = int(self.sim.now())

class TickProcess( Process ):
    def __init__(self,sim=None):
        Process.__init__(self,sim=sim)
        self.ticksThisRow= 0
        self.totalTicks= 0
    def run(self):
        while True:
            yield hold,self,1.0
            self.sim.outputfile.write("*")
            self.sim.outputfile.flush()
            #sys.stdout.write("*")
            #sys.stdout.flush()
            self.ticksThisRow += 1
            self.totalTicks += 1
            if self.ticksThisRow >= 60:
                self.sim.outputfile.write("  %d\n"%self.totalTicks)
                self.ticksThisRow= 0
    def reset(self):
        self.ticksThisRow=0

class PercentDoneTickProcess( Process ):
    def __init__(self,sim=None):
        Process.__init__(self,sim=sim)
        self.totalTicks= 0.0
    def run(self):
        while True:
            yield hold,self,1.0
            sys.__stderr__.write("#FracDone %f\n"%(self.totalTicks/self.sim.model.getTotalRunDays()))
            self.totalTicks += 1.0
    def reset(self):
        pass

class DBTickProcess( Process ):
    def __init__(self, sim):
        import db_routines as db
        iface = db.DbInterface()
        self.session = iface.Session()
        
        Process.__init__(self, sim=sim)
        self.totalTicks = 0.0

        print dir(sim.shdNet)

        tickId = sim.userInput.getValue("db_status_id")
        self.stp = self.session.query(shd.ShdTickProcess).filter_by(tickId=tickId).one()

        self.stp.modelName = sim.shdNet.name
        self.stp.processId = os.getpid()
        self.stp.hostName = socket.gethostname()
        self.stp.status = "simulation setup (simulation %d of %d)"%(self.sim.runNumber+1, self.stp.runCount)
        self.stp.fracDone = 0.0
        self.stp.lastUpdate = int(time.time())
        
        self.session.add(self.stp)
        self.session.commit()

        #atexit.register(self.cleanup)
        
    def run(self):
        while True:
            yield hold, self, 1.0
            self.stp.fracDone = self.totalTicks / self.sim.model.getTotalRunDays()
            self.stp.status = "running %0.2f"%(self.stp.fracDone * 100) + "%" + " (simulation %d of %d)"%(self.sim.runNumber+1, self.stp.runCount)
            self.session.commit()
            self.totalTicks += 1.0

    def cleanup(self):
        self.stp.status = "finished"
        self.session.commit()
        
            
    def reset(self):
        pass
    
    
class HermesSim(SimulationStep):
    """
    This class and its attributes contain an entire HERMES model, including separate instances
    of each vaccine, people, and truck type, a shipping network and output streams.
    """
    def __init__(self,userInput,unifiedInput,runNumber=0,perfect=False, shdNet=None):
        SimulationStep.__init__(self)

        self.runNumber = runNumber
        self.uniqueNum = 0
        self.shdNet = shdNet

        self.userInput = userInput
        # assert Unified Input is right
        assert(isinstance(unifiedInput,input.UnifiedInput))
        self.unifiedInput = unifiedInput
        # if output is going to a DB we should init the results structure
        self.results = shd.HermesResults(userInput['resultsGroupId'], runNumber, 'single')
        ### We need to initialize an output file for this HERMES Run
        if self.userInput['outputfile'] is not None:
            outfilename = self.userInput.getValue("outputfile") + "." + str(self.runNumber) + ".log"
            self.outputfileIsStdout = False
            self.outputfile = util.openOutputFile(outfilename, useTempFile = True)
        else:
            self.outputfileIsStdout = True
            self.outputfile = sys.stdout

        self.minion = self.userInput.getValue("minion")
        self.verbose = self.userInput.getValue("verbose")
        self.debug = self.userInput.getValue("debug")
        self.staticDemand = self.userInput.getValue("usestaticdemand")

        self.recordTheseStoresDict = {}
        self.monitorTheseVaccineNames = []
        self.uniqueIdDict = {}
        self.warehouseWeakRefs = []
        self.processWeakRefs = []

        ## STB Do we need perfect storage to perform crude gap analysis
        self.perfect = perfect

        for recorderType in ['monitor','tally']:
            if self.userInput.has_key(recorderType) and self.userInput[recorderType] is not None:
                for v in self.userInput[recorderType]:
                    self.recordTheseStoresDict[v]= recorderType

        if self.userInput.has_key('saveall') and self.userInput['saveall'] is not None:
            self.saveAllFile = self.userInput['saveall']
            self.recordTheseStoresDict['all'] = 'monitor'
            self.monitorTheseVaccineNames= ['everyvaccine']
        else:
            self.saveAllFile = None
            if self.userInput.has_key('monvax'):
                self.monitorTheseVaccineNames= self.userInput.getValue('monvax')

        self.trackThisVial= self.userInput.safeGetValue('trackvial', None)
        self.trackVialShipmentNumber= self.userInput.safeGetValue('trackshipment',0)
        self.reportFileName= self.userInput.safeGetValue('reportfile', None)

        ### Stock Monitor input variables
        self.stockMonitorInterval = self.userInput.safeGetValue('stockmonitorinterval',1.0)
        self.stockMonitorThresh = self.userInput.safeGetValue('stockmonitorthres',0.99)

        # pick which storage allocation scheme to use
        fc = self.userInput.getValue('fillcalculation')
        self.fc = fc
        if fc == 'sharecool':
            self.fillCalculationRoutine = warehouse.shareCool_calculateOwnerStorageFillRatios
            self.allocateStorageRoutine = warehouse.shareCool_allocateOwnerStorageSpace
        elif fc == 'share3':
            self.fillCalculationRoutine = warehouse.share3_calculateOwnerStorageFillRatios
            self.allocateStorageRoutine = warehouse.share3_allocateOwnerStorageSpace
        else:
            raise RuntimeError("Invalid fillcalculation in user input")

        self.limitedRoomTemp = False
        if self.userInput.getValue('limitedroomtemp'):
            self.limitedRoomTemp = True
        #
        #  Create the sim-wide type manager, and define all initially known types.
        #
        (self.typeManager, typeManagers) = \
            load_typemanagers.loadTypeManagers(self.userInput, unifiedInput, self, self.verbose, self.debug)
        #unpack the dict of individual type managers
        for (attr,tm) in typeManagers.items():
            setattr(self, attr, tm)
        self.tms = typeManagers

        self.recorders= recorders.RecorderGroup(self)
        self.notes= noteholder.NoteHolderGroup()

        modelName= userInput['model'] # we want an error if this is not specified
        self.outputfile.write("Loading model '%s'\n"%modelName)
#	if getattr(sys,'frozen',None):
#	    modelPkg=__import__(sys._MEIPASS)
#	else:
        modelPkg= __import__(modelName)
        self.model = modelPkg.Model(self) # triggers creation of DemandModel(s) within the model

        self.statsManager = statsmodel.StatsManager(self, self.model)

        self.costManager = costmodel.getCostManager(self, userInput)
        
        if not isinstance(self.costManager, dummycostmodel.DummyCostManager):
            self.geo = geomanager.GeoManager(required=True)
        else:
            self.geo = geomanager.GeoManager(required=False)

        if userInput['eventlog'] is None:
            self.evL = eventlog.DummyEventLog()
        else:
            logfilename = self.userInput.getValue("eventlog") + "." + str(self.runNumber) + ".csv"
            self.evL = eventlog.FileEventLog(logfilename)
            logThese = []
            #print "Here is what userInput Gives me %s"%(str(userInput['eventloglist']))

            if userInput['eventloglist'] is not None:
                for eStr in userInput['eventloglist']:
                    event = eventlog.getEventFromEventName(eStr)
                    if event is None:
                        raise RuntimeError("Input parameter 'eventloglist' specified invalid event '%s'"%eStr)
                    else:
                        logThese.append(event)
                if len(logThese)>0: self.evL.setEventList(logThese)
                if userInput['eventlogregex'] is not None:
                    try:
                        self.evL.setFilterRegex(userInput['eventlogregex'])
                    except Exception,e:
                        raise RuntimeError("Your logging filter regular expression <%s> would not compile: %s"%\
                                           (userInput['eventlogregex'],e))

        self.writeConfigInfo()

        ### initialize the overall run's random seed
        self.rndm = random.Random()
        myRandomSeed= self.userInput.safeGetValueFromList('seed', self.runNumber, None)
        if myRandomSeed is None:
            myRandomSeed= self._getRandSeed()
        self.outputfile.write("seed for this run: %s\n"%repr(myRandomSeed))
        if not self.outputfileIsStdout:
            print "seed for this run: %s"%myRandomSeed
        self.randomRounder = util.RandomRounder(myRandomSeed)
        if myRandomSeed is not None:
            self.rndm.seed(myRandomSeed)
            for v in self.vaccines.getActiveTypes():
                if isinstance(v,vaccinetypes.VaccineType):
                    v.randSeed(myRandomSeed)
        self.model.initializeOVWEstimates() # must happen after the rest of the model is initialized
        ## Are using a Waste Frequency Estimation
        self.wasteEstimateFrequency = self.userInput.getValue("wasteestfreq")

        #self.initialize()

        ### Now it is time to set up the model
        #------------------
        # Create the network
        #------------------
        #------------------
        # Stages 1 through 3: load the warehouse/clinic description file and the routes file and
        # instantiate the warehouses, clinics and shipping network.  This includes default links.
        #------------------
        self.outputfile.write("Stores file is %s\n"%self.userInput['storesfile'])
        self.outputfile.write("Routes file is %s\n"%self.userInput['routesfile'])


        if shdNet is not None:
            print "\n\n***** getting recs from shdNet ****\n"
            storeKeys,storeRecList = shdNet.createStoreRecs()
            routeKeys,routeRecList = shdNet.createRouteRecs()
            factoryKeys, factoryRecList = shdNet.createFactoryRecs()
            tripManifestKeys = None
            tripManifestRecList = None
        else:
            (storeKeys, storeRecList, routeKeys, routeRecList, factoryKeys, factoryRecList, tripManifestKeys, tripManifestRecList) = \
                load_networkrecords.readNetworkRecords(self.userInput)


#        print "storeRecList: %s"%storeRecList

#        print net.routes
#        print "routeRecList: %s"%routeRecList

        self.initialize()

        with util.logContext("Building Network"):
            self.powerCutDict = {}
            # the following has the side effect of loading power cut information
            # since there isn't a 1-1 relationship between power cut processes and
            # warehouses it is saved separately in self.powerCutDict (I'm sorry!)
            self.storeDict, self.allShippingProcs, self.allReportingHierarchies = \
                nbldr.buildNetwork(storeKeys, storeRecList,
                                   routeKeys, routeRecList,
                                   self,
                                   curry.curry(self.model.warehouseOrClinicFromRec,
                                               recordTheseStoresDict=self.recordTheseStoresDict,
                                               recordTheseVaccineNames=self.monitorTheseVaccineNames),
                                   self.model.getShipInterval,
                                   self.model.getShipStartupLatency,
                                   self.model.getPullControlFuncs,
                                   self.model.getOrderPendingLifetime,
                                   self.model.getTruckInterval,
                                   self.model.getPullMeanFrequency,
                                   self.model.getDefaultSupplier,
                                   self.model.getDefaultTruckTypeName,
                                   self.model.getDefaultTruckInterval,
                                   self.model.getDefaultPullMeanFrequency,
                                   tripManifestKeys,tripManifestRecList
                                   )

        # We have to do this here because finishBuild may trigger the calculation of shipment
        # quantities, which can depend on model.wastageEstimates, which is initialized by the
        # creation of the UpdateWastageEstimates process.
        if self.wasteEstimateFrequency > 0:
#            print "Setting an automatic wastage estimate starting %d with frequency of %d"\
#                %(self.userInput['wasteestupdatelatency'],G.updateWastageEstimate)
            updatewaste = self.model.UpdateWastageEstimates(self,self.model.updateWasteEstimateFreq,
                                                            self.userInput['wasteestupdatelatency'])
            self.activate(updatewaste,updatewaste.run(),at=0.0)

        nbldr.finishBuild(self.storeDict, self.allShippingProcs, self.model.getScheduledShipmentSize)

        #------------------
        # Stage 4: Activate the shipping processes
        #------------------
        for proc in self.allShippingProcs:
            self.activate(proc,proc.run())

        # activate power outage processes as well
        for proc in self.powerCutDict.values():
            self.activate(proc, proc.run())

        #------------------
        # Stage 5: Generate UseVials and factory processes as specified
        #          by the model, and add recorders as required.
        #          add a process to monitor the stock as a function of time.
        #------------------
        for t,wh in self.storeDict.items():
            if wh is None: continue
            if wh.recorder is None:
                if self.recordTheseStoresDict.has_key(wh.name):
                    recorderType= self.recordTheseStoresDict[wh.name]
                elif self.recordTheseStoresDict.has_key(str(t)):
                    recorderType= self.recordTheseStoresDict[str(t)]
                elif self.recordTheseStoresDict.has_key('all'):
                    recorderType= "monitor"
                else:
                    recorderType= None
                if recorderType is not None:
                    scaleVC= self.model.getApproxScalingVC(self.storeDict,t)
                    recorder= self.recorders.buildRecorderObject(recorderType,
                                                                 "%s_%s"%(wh.name,t),
                                                                 scaleVC,
                                                                 self.monitorTheseVaccineNames)
                    wh.setRecorder(recorder)
            useVials= self.model.getUseVialsProcess(self.storeDict,t)
            if useVials is not None:
                self.activate(useVials,useVials.run())

            monitorstocks = warehouse.MonitorStock(self.stockMonitorInterval,
                                                   self.model.getBurninDays(),
                                                   self.stockMonitorThresh,
                                                   wh)
            self.activate(monitorstocks,monitorstocks.run())
        #------------------
        # Stage 6: Generate factories if necessary
        #------------------
        self.factories = []
        factoryWasteEstRecs = None
        
        if self.userInput['factorywastagefile'] is not None:
            if shdNet is not None:
                tmpkeys,factoryWasteEstRecs = shdNet.getFactoryWastageRecs()
            else:
                with util.openDataFullPath(self.userInput['factorywastagefile']) as f:
                    factoryWasteEstKeys, factoryWasteEstRecs = csv_tools.parseCSV(f)    
            
        #print "Factory Rec List = " + str(factoryRecList)
        #print "Factory Waste Rec List = " + str(factoryWasteEstRecs)
        if factoryRecList is not None and len(factoryRecList) > 0:
            for rec in factoryRecList:
                facProdFun = self.model.getFactoryProductionFunction(self.storeDict, None, alwaysTrue=True)
                self.factories.append(self.model.factoryFromRec(self, rec, facProdFun, factoryWasteEstRecs))
        else:
            # ## Backward compatibility
            for t, wh in self.storeDict.items():
                factoryProductionFunc = self.model.getFactoryProductionFunction(self.storeDict, t)
                if factoryProductionFunc is not None:
                    startupLatency = self.model.getFactoryStartupLatency(self.storeDict, t)
                    batchInterval = self.model.getFactoryBatchInterval(self.storeDict, t)
                    overStockScale = self.model.getFactoryOverStockScale(self.storeDict, t)
                    if self.verbose:
                        self.outputfile.write("%s: building factory, batch interval %f, latency %f\n" % \
                                              (wh.name, batchInterval, startupLatency))

                    self.factories.append(warehouse.Factory([(1.0,wh)],
                                                             batchInterval,
                                                             factoryProductionFunc,
                                                             vaccineProd=None,
                                                             trackThis=self.trackThisVial,
                                                             trackingShipmentNumber=self.trackVialShipmentNumber,
                                                             startupLatency=startupLatency,
                                                             overstockScale=overStockScale))

        for factory in self.factories:
            print repr(factory)
            self.activate(factory, factory.run())

                #else: print "Skipping %s!"%wh.name
        #------------------
        # Stage 7: Do some diagnostics and print statistics from the tree.
        #------------------

        #Scan for some types of internal inconsistencies
        nbldr.realityCheck(self)
        self.costManager.realityCheck()
        if shdNet is not None:
            if not costmodel.getCostModelVerifier(shdNet).checkReady(shdNet):
                raise RuntimeError('cost model verification failed!')

        ###################
        # The model is now fully initialized.
        ###################

        tpD = {}
        for tp in self.typeManager.getActiveTypes():
            key = tp.typeName
            if key in tpD:
                tpD[key].append(tp)
            else:
                tpD[key] = [tp]
        for key, tL in tpD.items():
            self.outputfile.write("\n\nFollowing %d %s types are included in the simulation:\n" %
                                  (len(tL), key))
            for tp in tL:
                self.outputfile.write(tp.summarystring())

        #Activate burninTrigger
        self.burninTrigger= BurninTrigger(self.model,sim=self)
        self.activate(self.burninTrigger, self.burninTrigger.run())

        #Disable note taking during burn-in
        #(burninTrigger will turn it back on)
        self.notes.disableAll()

        if self.minion:
            if not self.outputfileIsStdout:
                assert self.outputfile.type == 'filehandle', 'in minion mode but output file is not a filehandle'
                sys.__stderr__.write("#LogFilePath %s\n"%self.outputfile.fh.name)
            #self.tickProcess = PercentDoneTickProcess(sim=self)
            #self.activate(self.tickProcess,self.tickProcess.run())
            self.tickProcess = DBTickProcess(sim=self)
            self.activate(self.tickProcess,self.tickProcess.run())
        elif not (self.verbose or self.debug):
            self.tickProcess = TickProcess(sim=self)
            self.activate(self.tickProcess,self.tickProcess.run())
        else:
            self.tickProcess = None

        if self.reportFileName is not None:
            reporter=Reporter(self, self.model.getReportingInterval(), self.model.getTotalRunDays(),
                              self.reportFileName,
                              self.model.activeVaccineTypeInfo.getActiveVaccineTypeNames(),
                              sim=self)
            self.activate(reporter, reporter.run())

    def _importTypeRecords(self, fileName, whatType):
        if fileName is None:
            return
        self.typeManager.addTypeRecordsFromFile(fileName, whatType, self.verbose, self.debug)

    def _getRandSeed(self):
        """
        This uses code stolen from the Python 2.6 maintenance release to generate a random
        seed when none is provided.  The seed value is returned; the value is a long.
        """
        try:
            import binascii
            a = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            import time
            a = long(time.time() * 256) # use fractional seconds
        return a

    def getUniqueNum(self):
        """
        Returns an integer which is unique within the sim, for things which want to number themselves.
        """
        retval = self.uniqueNum
        self.uniqueNum += 1
        return retval

    def writeConfigInfo(self):
        verStringList= [m._hermes_svn_id_[4:-2] for m in sys.modules.values() if hasattr(m,'_hermes_svn_id_')]
        verStringList.sort()
        self.outputfile.write('-'*60 + '\n')
        self.outputfile.write('SVN version information:\n\n')
        for s in verStringList:
            self.outputfile.write('   %s\n'%s)
        self.outputfile.write('-'*60 + '\n')

    def passthrough(self):
        return

    def runModel(self, until=None):
        #Run the simulation
        self.outputfile.write("\nRunning the model\n")
        self.outputfile.write("="*60)
        self.outputfile.write("\nSimulating %g days\n\n"%self.model.getTotalRunDays())
        if until is None:
            until= self.model.getTotalRunDays()
        self.simulate(until=until)
        self.outputfile.write("\n")
        self.outputfile.write("="*60)
        self.outputfile.write("\n")

        # Force all the warehouses to touch all their vaccines, so that the
        # age of all vaccine groups will be updated to the end of the simulation
        # and storage statistics will be complete.
        self.syncStatistics()
        self.costManager.endCostingInterval()
        self.statsManager.endStatsInterval()
        self.evL.close()
        return HermesOutput.HermesOutput(self)

    def runModelStep(self, until=None, callback=None):
        if(self.now() == 0.0):
            self.outputfile.write("\nRunning the model\n")

        self.startStepping()
        if callback is None:
            self.callback = self.passthrough
        else:
            self.callback = callback

        if self.now() < self.model.getBurninDays():
            self.outputfile.write("\nBurning in the model for %g days\n\n"%self.model.getBurninDays())
            while self.burninTrigger.burninTriggered == False:
                self.step()

            self.outputfile.write("\nModel Burnin Complete at day %g\n"%int(self.now()))


        #Run the simulation
        if until is None or until > self.model.getTotalRunDays():
            until= self.model.getTotalRunDays()
        self.outputfile.write("\nSimulating %g days at %g of total %g\n\n"%(int(until-self.now()),int(self.now()),self.model.getTotalRunDays()))
        if self.tickProcess is not None: self.tickProcess.reset()
        while self.now() < until:
            self.step()

        # Force all the warehouses to touch all their vaccines, so that the
        # age of all vaccine groups will be updated to the end of the simulation
        # and storage statistics will be complete.
        if int(self.now()) == self.model.getTotalRunDays():
            print "\n"
            self.syncStatistics()
            self.costManager.endCostingInterval()
            self.statsManager.endStatsInterval()
            self.evL.close()
        return HermesOutput.HermesOutput(self)

    def syncStatistics(self):
        """
        VaccineGroups that have been in storage for a long time have not
        provided up-to-date summary information about the state of their
        vaccines.  This forces all Warehouses to scan their VaccineGroups,
        causing the statistics to update.
        """
        count= 0
        for r in self.warehouseWeakRefs:
            w= r()
            if w is not None:
                junkVC= w.getSupplySummary()
                count += 1
        if self.debug: print 'Scanned %d warehouses'%count

    def clearStatistics(self):
        """
        Clear internal statistics of warehouses and processes
        """
        count= 0
        for r in self.warehouseWeakRefs + self.processWeakRefs:
            thing= r()
            if thing is not None and hasattr(thing,'clearStatistics'):
                thing.clearStatistics()
                count += 1
        if self.debug: print 'Cleared %d objects'%count

    def printStatistics(self):
        #Print summary statistics
        seenSet = set()
        for typeManager in self.tms.values():
            for t in typeManager.getActiveTypes():
                if t not in seenSet:
                    self.outputfile.write("%s\n"%t.statisticsstring())
                    seenSet.add(t)

    def checkSummary(self, outfname=None, clear=False, graph=False):

        #Give the model an opportunity to look at the results
        if outfname is not None:
            self.model.checkSummary(outfname, clear=clear)
        elif self.userInput['outputfile'] is None:
            self.model.checkSummary(clear=clear)
        else:
            self.model.checkSummary(self.userInput['outputfile']+'.%d'%self.runNumber, clear=clear)

        #Do any requested summary graphics
        if graph:
            #self.recorders.printHistograms(ofile=self.outputfile)
            if (self.saveAllFile):
                self.recorders.saveMonitors(self.saveAllFile,self.storeDict)
                # uncomment this to save a binary version of this
                #self.recorders.saveMonitorsCompressed(self.saveAllFile,self.storeDict)
            #elif self.userInput['googleearthviz'] is True:
            #    #pass
            #    self.recorders.createMatPlotLibStockPlots(self.storeDict)
            else:
                #self.recorders.createMatPlotLibStockPlots(self.storeDict)
                self.recorders.plotHistograms()
                self.recorders.plotCurves()
                self.recorders.showPlots()

    def getUniqueString(self, base):
        """
        This is used by various components to generate names, primarily for debugging.
        If called with base='foo' (for example), it will return first 'foo0', then 'foo1',
        etc.
        """
        if not self.uniqueIdDict.has_key(base):
            self.uniqueIdDict[base]= 0
        retVal= "%s%d"%(base,self.uniqueIdDict[base])
        self.uniqueIdDict[base] += 1
        return retVal

    def cleanupOutputs(self):
        """
        close any outputs after the simulation is finished

        don't close anything we didn't create (ie avoid closing stdout)
        """
        if not self.outputfileIsStdout:
            self.outputfile.close()

