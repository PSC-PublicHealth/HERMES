#! /usr/bin/env python

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
from __future__ import with_statement
__doc__=""" visualizaton_tools.py
This has a number of utilities for creating visualizations for HERMES Output.
"""
_hermes_svn_id_="$Id: google_earth_viz.py 973 2012-05-25 19:42:44Z welling $"
from constants import * 
import network
import load_typemanagers
import vaccinetypes
import cgi
import os,shutil,sys
import shadow_network
import model



class Visualization:
    '''
    This is the base class for creating visualizations.
    
    The class holds all of the general visualization parameters, and it is
    intended to have concrete classes that define specific types of visualizations
    '''
    def __init__(self,shadow_network_=None ,resultsID_=None,
                 numberOfColors_=100,columnHeight_=100000,
                 populationRadius_=0.2,
                 vaccineAvailRadius_=0.05,
                 title_=None):
        
        self.shdNtwk = shadow_network_
        self.resultsID = resultsID_
        ### Defined in the kvp file
        self.levels = self.shdNtwk.getParameterValue("levellist")
        
        vizwidths = self.shdNtwk.getParameterValue("vizwidths")
        vizshapes = self.shdNtwk.getParameterValue("vizshapes")
        if vizwidths is None:
            print "Automatically generating Levels and vizinfo"
            self.levels = self.shdNtwk.getLevelList()
            vizwidths = []
            vizshapes = []
            levelCount = 1.0
            currentShape = "c"
            for level in self.levels:
                vizwidths.append(0.2/levelCount)
                levelCount *= 2.0
                vizshapes.append(currentShape)
                if currentShape == "c":
                    currentShape = "s"
                else:
                    currentShape = "c"
                    
        self.clinicLevelList = self.shdNtwk.parms['cliniclevellist'].parse()
        self.levelRadDict = {}
        for level in self.levels:
            self.levelRadDict[level] = (vizwidths[self.levels.index(level)],
                                        vizshapes[self.levels.index(level)])
        self.burninDays = self.shdNtwk.parms['burnindays'].parse()
        self.runDays = self.shdNtwk.parms['rundays'].parse()
        
        
        self.majorColor = "black"
        self.minorColor = "yellow"
        self.numberOfColors = numberOfColors_
        self.columnHeight = columnHeight_
        self.title = title_
        self.storeNoteDict = None
        self.routeNoteDict = None
        self.netInfo = None
        self.typeManagers = None
        self.vaccineNames = []
        
        self.populationRadius = populationRadius_
        self.vaccineAvailRadius = vaccineAvailRadius_
        
        self.maxPopulation = 0.0
        self.totalPopulation = 0.0
        
        ### This allows for the createion of image files to put in viz files
        self.imageTmpDir = 'image_tmp'
        try:
            os.mkdir(self.imageTmpDir)
        except:
            shutil.rmtree(self.imageTmpDir)
            os.mkdir(self.imageTmpDir)
        
        self.storeNoteDict = {}

        self.maxPopulation = computeMaxPopulationFromShdNtwk(self.shdNtwk)
        self.sumPopulation = computeSumPopulationFromShdNtwk(self.shdNtwk)
        
        ### Each visualization is made up of a series of elements
        self.elements = []
        self.elementNames = []
        
        self.vizStores = {}
        self.vizRoutes = {}
               
    def colorFromValue(self,value):
        if value < 0:
            return -1
        elif (value*self.numberOfColors) >= self.numberOfColors:
            return self.numberOfColors-1
        else:
            return int(float(self.numberOfColors)*value)
    
    def addElement(self,element=None):
        raise RuntimeError("addElement should not be called from the visualization base class")   
     
    def build(self):
        raise RuntimeError("Build should not be called from the visualization base class")
    
    def output(self, removeFiles = True):
        raise RuntimeError("Output should not be called from the visualization base class")
    
class VizStore:
    def __init__(self,storeID_,shdNtwk_,resultsID_,visualizationInfo_,sim_=None):
        self.iD = storeID_
        self.resultsID = resultsID_
        self._note = None
        self.visualizationInfo = visualizationInfo_
        self.sim = sim_
        
        ### These are flags that allow me to screen the viz
        self.hasPopulation = False
        self.hasVaccine = False
        self.hasThisVaccine = False
        self.hasOutreachVaccine = False
        self.hasOutreach = False
        self.isAttached = False
        self.isOutreach = False
        self.hasStorageDevices = False
        self.hasTransportVehicles = False
        self.visualize = True
 
        self._shdNtwkStore = shdNtwk_.stores[self.iD]
        if self._shdNtwkStore.NAME[0:4] == "Fake":
            print "Not Visualizing " + self._shdNtwkStore.NAME
            self.visualize = False
            return 
        self._report = self._shdNtwkStore.reports[resultsID_]
        
        self.parsedName = cgi.escape(self._shdNtwkStore.NAME)
        self.parsedLevel = self._shdNtwkStore.CATEGORY
        self.level = self._shdNtwkStore.CATEGORY
        
        self.isAttached = False
        if len(self._shdNtwkStore.inventory) == 0:
            self.isAttached = True
        
        if self._shdNtwkStore.FUNCTION == "Outreach":
            self.isOutreach = True
        
        self.peopleTypeExcludeList = ['Service1']
        ### Get list of attached clinics for this store
        #attachedStoreIds = getAttachedClinisFromNetInfo(netInfo_,self.iD)
        self.attachedStores = {}
        for aID in getAttachedClinics(self._shdNtwkStore):
            self.attachedStores[aID] = shdNtwk_.getStore(aID)
                        
        ### Get Data for population 
        
        self.peopleServedDict = {}#computeServedPopulationForNetStore(netInfo_,storeID)
        self.peopleServedDict['all'] = {'displayName': 'All People','count':0}
        
        for demand in self._shdNtwkStore.demand:
            if demand.invName not in self.peopleTypeExcludeList:
                if not self.peopleServedDict.has_key(demand.invName):
                    self.peopleServedDict[demand.invName]= {'count':0,
                                                            'displayName':demand.invType.getDisplayName()}
                self.peopleServedDict[demand.invName]['count'] += demand.count
                self.peopleServedDict['all']['count'] += demand.count
                        
        ### now add attached Clinics
        for aID,aStore in self.attachedStores.items():
            for demand in aStore.demand:
                if demand.invName not in self.peopleTypeExcludeList:
                    if not self.peopleServedDict.has_key(demand.invName):
                        self.peopleServedDict[demand.invName]= {'count':0,
                                                                'displayName':demand.invType.getDisplayName()}
                    self.peopleServedDict[demand.invName]['count'] += demand.count
                    self.peopleServedDict['all']['count'] += demand.count
                    
        
        #self.totalPeopleServedDict= dict(self.peopleServedDict.items() + self.peopleOutreachDict.items())        
        self.totalPeopleServedDict = self.peopleServedDict
        if self.totalPeopleServedDict['all']['count'] > 0:
            self.hasPopulation = True
        
        ### Gather Vaccine Data
        self.vaccineDataDict = {'allvax':{'patients':0,'treated':0,
                                          'expired':0,'outages':0,
                                          'vials':0,'availability':0}}
        #self.outreachVaccineDataDict = {'allvax':{'patients':0,'treated':0,'availability':0}}
        
        ### Fill in the vaccine names that were distributed at this place
        vaccineNames = []
        
        for v,n in self._report.vax.items():
            vaccineNames.append(v)
            
        ### Run through the note at this place    
        for v,n in self._report.vax.items():
            if self.vaccineDataDict.has_key(v) is False:
                self.vaccineDataDict[v] = {}
                self.vaccineDataDict[v]['patients'] = 0
                self.vaccineDataDict[v]['treated']  = 0
                self.vaccineDataDict[v]['expired']  = 0
                self.vaccineDataDict[v]['outages']  = 0
                self.vaccineDataDict[v]['vials']    = 0
            
            self.vaccineDataDict[v]['patients'] += n.patients
            self.vaccineDataDict[v]['treated']  += n.treated
            self.vaccineDataDict[v]['expired']  += n.expired
            self.vaccineDataDict[v]['outages']  += n.outages
            self.vaccineDataDict[v]['vials']    += n.vials
            self.vaccineDataDict['allvax']['patients'] += n.patients
            self.vaccineDataDict['allvax']['treated']  += n.treated
            self.vaccineDataDict['allvax']['expired']  += n.expired
            self.vaccineDataDict['allvax']['outages']  += n.outages
            self.vaccineDataDict['allvax']['vials']    += n.vials
            
        for aStoreID in self.attachedStores:
            aStore = shdNtwk_.getStore(aStoreID)
            for v,n in aStore.reports[resultsID_].vax.items():
                if self.vaccineDataDict.has_key(v) is False:
                    self.vaccineDataDict[v] = {}
                    self.vaccineDataDict[v]['patients'] = 0
                    self.vaccineDataDict[v]['treated']  = 0
                    self.vaccineDataDict[v]['expired']  = 0
                    self.vaccineDataDict[v]['outages']  = 0
                    self.vaccineDataDict[v]['vials']    = 0
            
                self.vaccineDataDict[v]['patients'] += n.patients
                self.vaccineDataDict[v]['treated']  += n.treated
                self.vaccineDataDict[v]['expired']  += n.expired
                self.vaccineDataDict[v]['outages']  += n.outages
                self.vaccineDataDict[v]['vials']    += n.vials
                self.vaccineDataDict['allvax']['patients'] += n.patients
                self.vaccineDataDict['allvax']['treated']  += n.treated
                self.vaccineDataDict['allvax']['expired']  += n.expired
                self.vaccineDataDict['allvax']['outages']  += n.outages
                self.vaccineDataDict['allvax']['vials']    += n.vials
     
        ## add the vaccine display names to the vaccineDataDict
        for vaccineName,dataDict in self.vaccineDataDict.items():
            if vaccineName == "allvax":
                dataDict['displayName'] = "All Vaccines"
            else:
                dataDict['displayName'] = \
                    shdNtwk_.vaccines[vaccineName].DisplayName
            dataDict['availability'] = 0.0
            if dataDict['patients'] > 0:
                dataDict['availability'] = \
                    float(dataDict['treated'])/float(dataDict['patients'])
    

        ### Create a combined vaccine data dictionary
        self.totalVaccineDict = self.vaccineDataDict
        
        if self.totalVaccineDict['allvax']['patients'] > 0:
            self.hasVaccine = True
            for vaccineKey,vaccine in self.totalVaccineDict.items():
                if (vaccineKey,vaccine['displayName']) not in self.visualizationInfo.vaccineNames:
                    self.visualizationInfo.vaccineNames.append((vaccineKey,vaccine['displayName']))
                    
        ## Get Utilization Data
        ### HACK need to alleviate
        self.storageTypes = ["cooler","freezer"]
        print "STORE FICKING HERE " + str(self.iD)
        self.storageFillDict = {}
        self.inventoryList = []
        self.transportList = []
        self.storePlotFilename = None
        if not self.isAttached:
            totalVol = 0.0
            for st in self.storageTypes:
                self.storageFillDict[st] = {}
                if self._report.storage.has_key(st):
                    self.storageFillDict[st]["max_volume_used"]=float(self._report.storage[st].vol_used)
                    self.storageFillDict[st]["volume_avail"]=float(self._report.storage[st].vol)
                    self.storageFillDict[st]["max_percent_used"]=float(self._report.storage[st].fillRatio)*100.0
                    totalVol+= self.storageFillDict[st]["volume_avail"]
                else:
                    self.storageFillDict[st]["max_volume_used"]=0.0
                    self.storageFillDict[st]["volume_avail"]=0.0
                    self.storageFillDict[st]["max_percent_used"]=0.0
            
            for device in self._shdNtwkStore.inventory:
                if type(device.invType)==shadow_network.ShdStorageType:
                    self.hasStorageDevices = True
                    invDict = {'name':device.invType.getDisplayName(),
                               'count':device.count,'volumes':{}}
                    invDict['volumes']['cooler'] = device.invType.cooler
                    invDict['volumes']['freezer'] = device.invType.freezer
                    self.inventoryList.append(invDict)
                    
                if type(device.invType) == shadow_network.ShdTruckType:
                    self.hasTransportVehicles = True
                    tranDict = {'name':device.invType.getDisplayName(),
                                'count':device.count,'volumes':{}}
                    tranDict['volumes']= {'cooler':0.0,'freezer':0.0}
                    tranDict['volumes']['cooler'] += device.invType.CoolVolumeCC/1000.0
                    itemList = model.parseInventoryString(device.invType.Storage)
                    for (count,name) in itemList:
                        storeDevice = shdNtwk_.types[name]
                        tranDict['volumes']['cooler']  += count*storeDevice.cooler
                        tranDict['volumes']['freezer'] += count*storeDevice.freezer
                
                    self.transportList.append(tranDict)
            ### Lets try to parse a stock plot from the storage ratio AccumVal
            self.volumeT = []
            self.volumeF = []
            
            storageRatioMV = self._report.storageRatioMV()
             
            storeVialCountMV = self._report.storeVialCountMV()
            if storeVialCountMV is not None:                
                for iEntry in range(0,storeVialCountMV.count()):
                    storeVialDict = storeVialCountMV.getEntryDict(iEntry)
                    
                    self.volumeT.append(storeVialDict['time']-self.visualizationInfo.burninDays)
                    thisCount = 0.0
                    for v,n in storeVialDict.items():
                        if v != "time":
                            thisCount += n
                    self.volumeF.append(thisCount)
                self.storeHCString = self.createHCLinePlotForStorageVolume()
                 
    def createBarGraphForVaccineData(self,variable,percent=False):
        vDataDict = None
        if variable == "outreachAvail":
            if not self.hasOutreach:
                raise RuntimeError("VizStore:createBarGraphForVaccineData: Trying to create a outreach"\
                                   +" for a place that doesn't have outreach")
                
            if self.outreachVaccineDataDict is None:
                raise RuntimeError("VizStore:createBarGraphForVaccineData: Trying to create a bar graph prior"\
                                   +" to filling outreach vaccine data")
                
            vDataDict = self.outreachVaccineDataDict
            filePrefix = "vaccine_outreach_"
            variable = "availability"
        else:
            if self.vaccineDataDict is None:
                raise RuntimeError("VizStore:createBarGraphForVaccineData: Trying to create a bar graph prior"\
                                   +" to filling vaccine data")
            vDataDict = self.vaccineDataDict
            filePrefix = "vaccine_"
        if self.hasVaccine is False:
            return None
        
        bars = []
        barheights = []
        filaName = None
        xlabel = None
        ylabel = None
        maxHeight = None
        
        percentFact=1.0
        if percent is True:
            percentFact = 100.0
            maxHeight = 100.0
            ylabel = "Pecent Vaccine %s"%(variable.title())
        else:
            ylabel = "%s"%(variable.title())
        for vaccineName, dataDict in vDataDict.items():
            if dataDict.has_key(variable):
                bars.append(dataDict['displayName'])
                barheights.append(float(dataDict[variable])*percentFact)      
        fileName = "%s/%s_%s_%s.png"%(self.visualizationInfo.imageTmpDir,
                                           filePrefix,variable,
                                           self.iD)
        returnfileName = "images/%s_%s_%s.png"%(filePrefix,variable,
                                                self.iD)
        xlabel = "Vaccines"
        if maxHeight is None:
            maxHeight = max(barheights)
        createBarGraph(bars,barheights,xlabel,ylabel,fileName,maxHeight)
    
        return returnfileName
    
    def createHCLinePlotForStorageVolume(self,percent=False):
        if self.visualize is False:
            return None
        if self.isAttached:
            return None
        
        name = "storagePlot_%s"%self.iD
        xlabel = "Days"
        ylabel = "Volume (L)"
        
        
        totVol = 0.0
        for st in self.storageFillDict.keys():
            totVol += self.storageFillDict[st]['volume_avail']

        return createLinePlot(self.volumeF,self.volumeT,xlabel,ylabel,name,engine="highcharts")
        
    
         
    def createLinePlotForStorageVolume(self,percent=False):
        if self.visualize is False:
            return None
        if self.isAttached:
            return None
        
        filePrefix = "storagePlot_"
        xlabel = "Days"
        ylabel = "Volume (L)"
        
        fileName = "%s/%s%s.png"%(self.visualizationInfo.imageTmpDir,
                                   filePrefix,self.iD)
        returnFileName = "images/%s%s.png"%(filePrefix,self.iD)
        
        totVol = 0.0
        for st in self.storageFillDict.keys():
            totVol += self.storageFillDict[st]['volume_avail']

        createLinePlot(self.volumeF,self.volumeT,xlabel,ylabel,fileName)
        
        return returnFileName
    
        
class VizRoute:
    def __init__(self,routeID_,shdNtwk_,resultsID_,visualizationInfo_,sim_=None):
        self.iD = routeID_
        self.visualizationInfo = visualizationInfo_
        # still need the sim, should not.
        self.sim = sim_
            
        self._shdNtwkRoute = shdNtwk_.getRoute(routeID_)
        if self._shdNtwkRoute.reports.has_key(resultsID_) is True:
            self._report = self._shdNtwkRoute.reports[resultsID_]
        else:
            self.visualize = False
            self._report = None
            return
        
        self.latlonCoordinates = []
        self.parsedName = ""
        self.parsedType = ""
        self.type = self._shdNtwkRoute.Type
        self.parsedLevelName = ""
        self.visualize = True
        
        ### Create the names for the route
        for stop in self._shdNtwkRoute.stops:
            stopStore = stop.store
            if stop.store.NAME[0:4] == "Fake":
                self.visualize = False
                return
            self.latlonCoordinates.append((float(stopStore.Longitude),float(stopStore.Latitude)))
            self.parsedName += "%s -> "%(stopStore.NAME)
            self.parsedLevelName += "%s -> "%(stopStore.CATEGORY)
        self.parsedName = cgi.escape(self.parsedName[:-4])
        self.parsedLevelName = cgi.escape(self.parsedLevelName[:-4])
            
        ### Create the description of the route
        if self._shdNtwkRoute.Type in ["varpush","schedvarfetch"]:
            self.parsedType = "Fixed Schedule / Variable Amount "
        elif self._shdNtwkRoute.Type in ["push", "schedfetch"]:
            self.parsedType = "Fixed Schedule / Fixed Amount "
        elif self._shdNtwkRoute.Type in ["pull","demandfetch","persistentpull","persistentdemandfetch"]:
            self.parsedType = "Variable Schedule / Variable Amount "
        elif self._shdNtwkRoute.Type in ["askingpush"]:
            self.parsedType = "Fixed Schedule / Topping Strategy "
        elif self._shdNtwkRoute.Type in ["attached"]:
            self.parsedType = "Attached Clinic"
        else:
            self.parsedType = "UKNOWN"
            self.visualize = False
            print "WARNING: Unknown Route Type to Plot " + self._shdNtwkRoute.Type
        
        if self.parsedType == "Attached Clinic":
            self.visualize = False
            return 
        
        
        if len(self._shdNtwkRoute.stops) > 2:
            self.parsedType += "Loop Route"
        elif self._shdNtwkRoute.Type in ["schedvarfetch", "schedfetch", "demandfetch", "persistentdemandfetch"]:
            self.parsedType += "Client Pickup Route"
        else:
            self.parsedType += "Supplier Delivered Route"
        
        self.parsedType = cgi.escape(self.parsedType)
        self.transportInfo = []
        device = shdNtwk_.types[self._shdNtwkRoute.TruckType]
        if type(device) == shadow_network.ShdTruckType:
            self.hasTransportVehicles = True
            tranDict = {'name':device.getDisplayName(),
                        'volL':0.0}
            tranDict['volL'] += device.CoolVolumeCC/1000.0
            itemList = model.parseInventoryString(device.Storage)
            for (count,name) in itemList:
                storeDevice = shdNtwk_.types[name]
                tranDict['volL'] += count*storeDevice.cooler
            
            self.transportInfo.append(tranDict)    
        ### Gather the transport information for the route
    
        ### How full is the route
        self.maximumFracFill = self._report.RouteFill
        self.overMaxFracFill = 0.0
        if self.maximumFracFill > 1.0:
            self.overMaxFracFill = self.maximumFracFill - 1.0
            self.maximumFracFill = 1.0
                
        #### Building a Trip Manifest to facilitate printing and visualization
        self.numberOfTrips = self._report.RouteTrips
        self.tripManifest = []
        
        if self.numberOfTrips == 0:
            self.tripManifest.append({'start':"",
                                      'end':"",
                                      'tStart':0,
                                      'tEnd':0,
                                      'LitersCarried':0})
        else:
            iStart = 0
            iEnd = 1
    
            tripTimesMV = self._report.tripTimesMV()
            
            for iTrip in range(0,tripTimesMV.count()):
                tripDict = tripTimesMV.getEntryDict(iTrip)
                tripTime = (tripDict['startTime'],tripDict['endTime'])
                routeVol = tripDict['distance']
                
                if iEnd == 0:
                    iStart = 0
                    iEnd = 1
                if iStart == len(self._shdNtwkRoute.stops)-1:
                    iEnd = 0
                    
                self.tripManifest.append({'start':self._shdNtwkRoute.stops[iStart].store.NAME,
                                          'end':self._shdNtwkRoute.stops[iEnd].store.NAME,
                                          'tStart':tripTime[0],
                                          'tEnd':tripTime[1],
                                          'LitersCarried':routeVol})
                iStart  += 1

## Utility Functions

def computeMaxPopulationFromShdNtwk(shdNtwk):
    max = -999999
    for storeID,store in shdNtwk.stores.items():
        if store.FUNCTION == "Surrogate":
            continue
        availStoreIDs = getAttachedClinics(store)
        availStoreIDs.append(storeID)
        sum=0  
        for aStoreKey in availStoreIDs:
            aStore = shdNtwk.getStore(aStoreKey)
            for demand in aStore.demand:
                sum+= demand.count
        if sum > max: 
            max = sum
    return max

def computeSumPopulationFromShdNtwk(shdNtwk):
    sum = 0.0
    for storeID,store in shdNtwk.stores.items():
        for demand in store.demand:
            sum += demand.count
    return sum

def createBarGraph(bars,barheights,xlabel,ylabel,filename,
                   maximumValue=None, engine='matplotlib'):
    if engine == "matplotlib":
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        import numpy as np
    
        NRange = np.arange(len(bars))
        if maximumValue is None:
            maximumValue = max(barheights)
        width = 0.5
        fig = Figure(figsize=(8,8))
        subpt = fig.add_subplot(111,autoscaley_on=True,ymargin=1.0)
        subpt.set_xlabel(xlabel)
        subpt.set_ylabel(ylabel)
        subpt.bar(NRange,barheights,width=width)
        subpt.set_xticks(NRange+width/2)
        subpt.set_xticklabels(bars,rotation=30,fontsize=9)
        subpt.axis([0,len(bars),0,int(maximumValue)])
        canvas = FigureCanvasAgg(fig)
        canvas.print_figure(filename,dpi=40)
    else:
        raise RuntimeError("Unsupported Bar Graph Engine %s"%engine)

def createLinePlot(yseries,tseries,xlabel,ylabel,filename,
                   maximumValue=None, title=None, engine='matplotlib'):
    
    if engine == "matplotlib":
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        import numpy as np
        
        fig = Figure(figsize=(10,4))
        subpt = fig.add_subplot(111)
        subpt.set_xlabel(xlabel)
        subpt.set_ylabel(ylabel)
        #subpt.autoscale_on(True)
        subpt.autoscale_view(True,True,True)
        tseriesNP = np.array(tseries)
        yseriesNP = np.array(yseries)
        ymax = yseriesNP.max()
        if maximumValue is not None:
            ymax = maximumValue
            
        xmax = tseriesNP.max()
        subpt.set_ylim(0,ymax)
        subpt.plot(tseriesNP,yseriesNP)
        canvas = FigureCanvasAgg(fig)
        canvas.print_figure(filename,dpi=40)
    
    elif engine == "highcharts":
        ymax = max(yseries)
        stringList = []
        stringList.append(    "$('#%s').highcharts({\n"%filename)
        stringList.append(    "     chart:{type:'line', height: 150, width:300},\n")
        if title:
            stringList.append("     title: { text: '%s' },\n"%title)
        else:
            stringList.append("     title: { text: null},\n")
        stringList.append(    "     legend: { enabled: false },\n")
        stringList.append(    "     plotOptions: { series: { marker: { enabled: false } } },\n")
        stringList.append(    "     xAxis: { title: { text:'%s' } },\n"%xlabel)        
        stringList.append(    "     yAxis:{ title: { text:'%s'\n }, min: 0, max: %d, endOnTick:false },\n"%(ylabel,int(ymax)))
        stringList.append(    "     series: [{\n")
        stringList.append(    "       data: [\n")
        for i in range(0,len(tseries)):
            stringList.append("               [%g,%g ],\n"%(tseries[i],yseries[i]))
        stringList.append(    "             ]\n")
        stringList.append(    "      }]\n")
        stringList.append(    "});\n")
        
        return ''.join(stringList)
    else:
        raise RuntimeError("Unsupported Line Plot engine %s"%(engine))
    

def getAttachedClinics(shdStore):   
    attachedStoreIDs = []
    
    for client in shdStore.clients():
        if client[1].Type == "attached" and client[0].FUNCTION != "Surrogate":
            attachedStoreIDs.append(client[0].idcode)
            
    return attachedStoreIDs

