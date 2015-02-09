#! /usr/bin/env python

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

class Visualization:
    '''
    This is the base class for creating visualizations.
    
    The class holds all of the general visualization parameters, and it is
    intended to have concrete classes that define specific types of visualizations
    '''
    def __init__(self,outputName_,hermesRun_,hermesOutput_,
                 numberOfColors_=100,columnHeight_=100,populationRadius_=0.2,
                 vaccineAvailRadius_=0.05,
                 title_=None):
        
        self.hermesRun = hermesRun_
        self.hermesOutput = hermesOutput_
        
        ### Defined in the kvp file
        self.levels = self.hermesRun.model.levelList
        vizwidths = self.hermesRun.model.vizWidths
        vizshapes = self.hermesRun.model.vizShapes
        self.clinicLevelList = self.hermesRun.model.clinicLevelList
        self.levelRadDict = {}
        for level in self.levels:
            self.levelRadDict[level] = (vizwidths[self.levels.index(level)],
                                        vizshapes[self.levels.index(level)])
        self.burninDays = self.hermesRun.model.burninDays
        self.runDays = self.hermesRun.model.runDays
        
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

        for storeKey in self.hermesOutput.stores.keys():
            store = self.hermesOutput.stores[storeKey]
            if store['note'] is not None:
                storeTS = store['note']
                self.storeNoteDict[str(store['code'])] = {'note':storeTS,
                                                          'lat':self.hermesRun.storeDict[store['code']].latitude,
                                                          'longitude':self.hermesRun.storeDict[store['code']].longitude,
                                                          'level':self.hermesRun.storeDict[store['code']].category}
    
        ### going to instantiate this myself for now
        (self.hermesRun.typeManager,self.typeManagers) = \
              load_typemanagers.loadTypeManagers(self.hermesRun.userInput, self.hermesRun.unifiedInput,\
                                                 self.hermesRun, self.hermesRun.verbose,self.hermesRun.debug)

        for (attr,tm) in self.typeManagers.items():
            setattr(self,attr,tm)

        self.netInfo = network.loadNetwork(self.hermesRun.userInput, self.hermesRun.typeManager, self.typeManagers)
        
        self.maxPopulation = computeMaxPopulationFromNetInfo(self.netInfo)
        self.sumPopulation = computeSumPopulationFromNetInfo(self.netInfo)
        
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
    def __init__(self,storeID_,hermesOutput_,netInfo_,visualizationInfo_,sim_=None):
        self.iD = storeID_
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
        
        if self.iD in hermesOutput_.stores.keys():
            self._note = hermesOutput_.stores[self.iD]['note']
        
        self._netInfoStore = netInfo_.stores[self.iD]
        
        self.parsedName = cgi.escape(self._netInfoStore.NAME)
        self.parsedLevel = self._netInfoStore.CATEGORY
        self.level = self._netInfoStore.CATEGORY
        
        self.isAttached = False
        if len(self._netInfoStore.inventoryList) == 0:
            self.isAttached = True
        
        if self._netInfoStore.FUNCTION == "Outreach":
            self.isOutreach = True
        
        self.peopleTypeExcludeList = ['Service1']
        ### Get list of attached clinics for this store
        #attachedStoreIds = getAttachedClinisFromNetInfo(netInfo_,self.iD)
        self.attachedStores = {}
        for aID in getAttachedClinicsFromNetInfo(netInfo_,self.iD):
            self.attachedStores[aID] = None
            if hermesOutput_.stores.has_key(aID):
                self.attachedStores[aID] = (netInfo_.stores[aID],hermesOutput_.stores[aID]['note'])
            else:
                self.attachedStores[aID]= (netInfo_.stores[aID],None)
        
        self.outreachStoresIDs = []
        self.outreachStores = {}
        if not self.isOutreach:
            self.outreachStoresIDs = getOutreachClinicsFromNetInfo(netInfo_,self.iD)
        
        for oID in self.outreachStoresIDs:
            self.outreachStores[oID] = None
            if hermesOutput_.stores.has_key(oID):
                self.outreachStores[oID] = (netInfo_.stores[oID],hermesOutput_.stores[oID]['note'])
            else:
                self.outreachStores[oID] = (netInfo_.stores[oID],None)
                                
        if len(self.outreachStores) > 0:
            self.hasOutreach = True
            
        ### Get Data for population 
        self.peopleServedDict = {'all':0}#computeServedPopulationForNetStore(netInfo_,storeID)
        for peopleKey,n in self._netInfoStore.people.items():
            if peopleKey not in self.peopleTypeExcludeList:
                if not self.peopleServedDict.has_key(peopleKey):
                    self.peopleServedDict[peopleKey] = 0
                self.peopleServedDict[peopleKey] += n
                self.peopleServedDict['all'] += n
        
        ### now add attached Clinics
        for aID in self.attachedStores.keys():
            for peopleKey,n in self.attachedStores[aID][0].people.items():
                if peopleKey not in self.peopleTypeExcludeList:
                    if not self.peopleServedDict.has_key(peopleKey):
                        self.peopleServedDict[peopleKey] = 0
                    self.peopleServedDict[peopleKey] += n
                    self.peopleServedDict['all'] += n
        
        ### now add Outreach
        self.peopleOutreachDict = {'all':0}
        if self.hasOutreach:
            for oID,oStore in self.outreachStores.items():
                #oStore = netInfo_.stores[oID]
                for peopleKey,n in oStore[0].people.items():
                    if peopleKey not in self.peopleTypeExcludeList:
                        if not self.peopleOutreachDict.has_key(peopleKey):
                            self.peopleOutreachDict[peopleKey] = 0
                        self.peopleOutreachDict[peopleKey] += n
                        self.peopleOutreachDict['all'] += n
        
        self.totalPeopleServedDict= dict(self.peopleServedDict.items() + self.peopleOutreachDict.items())        
        if self.totalPeopleServedDict['all'] > 0:
            self.hasPopulation = True
        
        ### Gather Vaccine Data
        self.vaccineDataDict = {'allvax':{'patients':0,'treated':0,'availability':0}}
        self.outreachVaccineDataDict = {'allvax':{'patients':0,'treated':0,'availability':0}}
        
        ### Fill in the vaccine names that were distributed at this place
        vaccineNames = []
        for noteKey in self._note.keys():
            if noteKey[-9:] == "_patients":
                vaccineNames.append(noteKey[:-9])
        
        ### Run through the note at this place             
        for noteKey in self._note.keys():
            noteSplit = noteKey.rsplit("_",1)
            if len(noteSplit) == 2:
                vaccineName = noteSplit[0]
                dataType = noteSplit[1]
                if vaccineName in vaccineNames:
                    value = self._note[noteKey]
                    if self.vaccineDataDict.has_key(vaccineName) is False:
                        self.vaccineDataDict[vaccineName] = {}
                    
                    if self.vaccineDataDict[vaccineName].has_key(dataType) is False:
                        self.vaccineDataDict[vaccineName][dataType] = value
        
        ### Run through the notes at attached clinics
        for aID,aStore in self.attachedStores.items():
            if aStore[1] is not None:
                for noteKey in aStore[1].keys():
                    if noteKey[-9:] == "_patients":
                        if noteKey[:-9] not in vaccineNames:
                            vaccineNames.append(noteKey[:-9])
                
                for noteKey in aStore[1].keys():
                    noteSplit = noteKey.rsplit("_",1)
                    if len(noteSplit) == 2:
                        vaccineName = noteSplit[0]
                        dataType = noteSplit[1]
                        if vaccineName in vaccineNames:
                            value = aStore[1][noteKey]
                            if self.vaccineDataDict.has_key(vaccineName) is False:
                                self.vaccineDataDict[vaccineName] = {}
                            
                            if self.vaccineDataDict[vaccineName].has_key(dataType) is False:
                                self.vaccineDataDict[vaccineName][dataType] = 0
                            
                            self.vaccineDataDict[vaccineName][dataType] += int(value)
        
        ### IF there is outreach, run through those places
        if self.hasOutreach:
            for oID,oStore in self.outreachStores.items():
                if oStore[1] is not None:
                    for noteKey in oStore[1].keys():
                        if noteKey[-9:] == "_patients":
                            if noteKey[:-9] not in vaccineNames:
                                vaccineNames.append(noteKey[:-9])
                
                    for noteKey in oStore[1].keys():
                        noteSplit = noteKey.rsplit("_",1)
                        if len(noteSplit) == 2:
                            vaccineName = noteSplit[0]
                            dataType = noteSplit[1]
                            if vaccineName in vaccineNames:
                                value = oStore[1][noteKey]
                                if self.outreachVaccineDataDict.has_key(vaccineName) is False:
                                    self.outreachVaccineDataDict[vaccineName] = {}
                                
                                if self.outreachVaccineDataDict[vaccineName].has_key(dataType) is False:
                                    self.outreachVaccineDataDict[vaccineName][dataType] = 0
                                
                                self.outreachVaccineDataDict[vaccineName][dataType] += value
             
        ### add the vaccine display names to the vaccineDataDict
        for vaccineName,dataDict in self.vaccineDataDict.items():
            if vaccineName == "allvax":
                dataDict['displayName'] = "All Vaccines"
            else:
                dataDict['displayName'] = \
                    self.visualizationInfo.typeManagers['vaccines'].getTypeByName(vaccineName).displayName
            dataDict['availability'] = 0.0
            if dataDict['patients'] > 0:
                dataDict['availability'] = \
                    float(dataDict['treated'])/float(dataDict['patients'])
    
        if self.hasOutreach:
        ### add the vaccine display names to the vaccineDataDict
            for vaccineName,dataDict in self.outreachVaccineDataDict.items():
                if vaccineName == "allvax":
                    dataDict['displayName'] = "All Vaccines"
                else:
                    dataDict['displayName'] = \
                        self.visualizationInfo.typeManagers['vaccines'].getTypeByName(vaccineName).displayName
                dataDict['availability'] = 0.0
                if dataDict['patients'] > 0:
                    dataDict['availability'] = \
                        float(dataDict['treated'])/float(dataDict['patients'])
         
                ### Create a combined vaccine data dictionary
        self.totalVaccineDict = {}
        
        for vaccineName in self.vaccineDataDict.keys():
            if vaccineName in self.outreachVaccineDataDict.keys():
                a = self.vaccineDataDict[vaccineName]
                b = self.outreachVaccineDataDict[vaccineName]
                ### How is this for a mother fucking list comprehension
                self.totalVaccineDict[vaccineName] = dict([(x,a[x] + b[x])\
                                                                        if x in a and x in b and x != "availability" and x != "displayName" \
                                                                        else (x,(a[x]+b[x])/2.0) if x in a and x in b and x == "availability" \
                                                                        else (x,a[x]) if x == "displayName" \
                                                                        else (x,a[x]) if (x in a)\
                                                                        else (x,b[x]) for x in set(a.keys()+b.keys())])
            else:
                self.totalVaccineDict[vaccineName] = self.vaccineDataDict[vaccineName]
        
        for vaccineName in self.outreachVaccineDataDict.keys():
            if vaccineName not in self.vaccineDataDict.keys():
                self.totalVaccineDict[vaccineName] = self.outreachVaccineDataDict[vaccineName]
        
        if self.totalVaccineDict['allvax']['patients'] > 0:
            self.hasVaccine = True
            for vaccineKey,vaccine in self.totalVaccineDict.items():
                if (vaccineKey,vaccine['displayName']) not in self.visualizationInfo.vaccineNames:
                    self.visualizationInfo.vaccineNames.append((vaccineKey,vaccine['displayName']))
    
        if self.vaccineDataDict['allvax']['patients'] > 0:
            self.hasThisVaccine = True
        if self.outreachVaccineDataDict['allvax']['patients'] > 0:
            self.hasOutreachVaccine = True
                                
        self.vaccineAvailPlotFilename = None
        if self.hasThisVaccine:
            if self.isAttached is False:
                self.vaccineAvailPlotFilename = \
                self.createBarGraphForVaccineData("availability",percent=True)
        
        self.outreachVaccineAvailPlotFileName = None
        if self.hasOutreach:
            if self.hasOutreachVaccine:
                if len(self.outreachVaccineDataDict) > 0:
                    self.hasVaccine = True
                    self.outreachVaccineAvailPlotFilename = \
                        self.createBarGraphForVaccineData("outreachAvail",percent=True)
            
        
        ## Get Utilization Data
        ### HACK need to alleviate
        self.storageTypes = ["cooler","freezer"]
        
        self.storageFillDict = {}
        self.inventoryList = []
        self.transportList = []
        
        if not self.isAttached:
            for st in self.storageTypes:
                self.storageFillDict[st] = {}
                if st+"_vol_used" in self._note.keys():
                    self.storageFillDict[st]["max_volume_used"]=float(self._note[st+"_vol_used"].max())
                    self.storageFillDict[st]["volume_avail"]=float(self._note[st+"_vol"])
                    self.storageFillDict[st]["max_percent_used"]=float(self._note[st])*100.0
                else:
                    self.storageFillDict[st]["max_volume_used"]=0.0
                    self.storageFillDict[st]["volume_avail"]=0.0
                    self.storageFillDict[st]["max_percent_used"]=0.0
            
            for count,deviceType in self._netInfoStore.inventoryList:
                if self.visualizationInfo.typeManagers['fridges'].validTypeName(deviceType.name):
                    self.hasStorageDevices = True
                    invDict = {'name':deviceType.getDisplayName(),
                                'count':count,'volumes':{}}
                    for st in self.storageTypes:
                        invDict['volumes'][st] = float(deviceType.getTotalVolByName(st)/1000.0)
                    
                    self.inventoryList.append(invDict)
                
                elif self.visualizationInfo.typeManagers['trucks'].validTypeName(deviceType.name):
                    self.hasTransportVehicles = True
                    totVolSC = deviceType.getNetStorageCapacity()
                    tranDict = {'name':deviceType.name,'count':count,
                                'volumes':{}}
                    for st in self.storageTypes:
                        tranDict['volumes'][st] = 0.0
                        if totVolSC.has_key(st):
                            tranDict['volumes'][st] = float(totVolSC[st])/1000.0   

                    self.transportList.append(tranDict)
                    
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
                            
class VizRoute:
    def __init__(self,routeID_,hermesOutput_,netInfo_,visualizationInfo_,sim_=None):
        self.iD = routeID_
        self._note = None
        self.visualizationInfo = visualizationInfo_
        # still need the sim, should not.
        self.sim = sim_
        
        if self.iD in hermesOutput_.routes.keys():
            self._note = hermesOutput_.routes[routeID_]['note']
        
        self._netInfo = netInfo_.routes[routeID_]
        
        self.latlonCoordinates = []
        self.parsedName = ""
        self.parsedType = ""
        self.parsedLevelName = ""
        self.visualize = True
        
        ### Create the names for the route
        for stop in self._netInfo.stops:
            stopStore = stop.store
            self.latlonCoordinates.append((float(stopStore.Longitude),float(stopStore.Latitude)))
            self.parsedName += "%s -> "%(stopStore.NAME)
            self.parsedLevelName += "%s -> "%(stopStore.CATEGORY)
        self.parsedName = self.parsedName[:-4]
        self.parsedLevelName = self.parsedLevelName[:-4]
            
        ### Create the description of the route
        if self._netInfo.Type in ["varpush","schedvarfetch"]:
            self.parsedType = "Fixed Schedule / Variable Amount "
        elif self._netInfo.Type in ["push", "schedfetch"]:
            self.parsedType = "Fixed Schedule / Fixed Amount "
        elif self._netInfo.Type in ["pull","demandfetch","persistentpull","persistentdemandfetch"]:
            self.parsedType = "Variable Schedule / Variable Amount "
        elif self._netInfo.Type in ["askingpush"]:
            self.parsedType = "Fixed Schedule / Topping Strategy "
        elif self._netInfo.Type in ["attached"]:
            self.parseType = "Attached Clinic"
        else:
            self.parsedType = "UKNOWN"
            self.visualize = False
            print "WARNING: Unknown Route Type to Plot " + self._netInfo.Type
        
        if len(self._netInfo.stops) > 2:
            self.parsedType += "Loop Route"
        elif self._netInfo.Type in ["schedvarfetch", "schedfetch", "demandfetch", "persistentdemandfetch"]:
            self.parsedType += "Client Pickup Route"
        else:
            self.parsedType += "Supplier Delivered Route"
            
        ### Gather the transport information for the route
        self.transportInfo = []
        for vehicle in self._netInfo.transportTypes:
            vehVolSC = vehicle.getNetStorageCapacity()
            displayName = vehicle.displayName if vehicle.displayName != "" else vehicle.name
            cooler = vehVolSC['cooler']/1000.0 if vehVolSC.has_key('cooler') else 0.0
            self.transportInfo.append({'name':displayName,'volL':cooler})
        self.totVolAvail = sum(x['volL'] for x in self.transportInfo)
        
        ### How full is the route
        self.maximumFracFill = 0.0
        self.overMaxFracFill = 0.0
        if self._note is not None:
            if self._note.has_key('RouteFill'):
                self.maximumFracFill = self._note['RouteFill'].mean()
                if self.maximumFracFill > 1.0:
                    self.overMaxFracFill = self.maximumFracFill - 1.0
                    self.maximumFracFill = 1.0
        
        #### Building a Trip Manifest to facilitate printing and visualization
        self.numberOfTrips = 0
        self.tripManifest = []
        iStart = 0
        iEnd = 1
        if self._note is not None:
            if self._note.has_key('RouteTrips'):
                self.numberOfTrips = int(self._note['RouteTrips'])
            if self._note.has_key('triptimes_timestamp'):  
                for iTrip in range(0,len(self._note['triptimes_timestamp'].t)):
                    tripTime = self._note['triptimes_timestamp'].t[iTrip]
                    routeVol = self._note['triptimes_timestamp'].v[iTrip]
                    if iEnd == 0:
                        iStart = 0
                        iEnd = 1
                    if iStart == len(self._netInfo.stops)-1:
                        iEnd = 0
                        
                    self.tripManifest.append({'start':self._netInfo.stops[iStart].store.NAME,
                                              'end':self._netInfo.stops[iEnd].store.NAME,
                                              'tStart':tripTime[0],
                                              'tEnd':tripTime[1],
                                              'LitersCarried':routeVol})
                    iStart  += 1

## Utility Functions

def computeMaxPopulationFromNetInfo(netinfo):
    max = -999999
    for storeID in netinfo.stores.keys():
        store = netinfo.stores[long(storeID)]
        if len(store.inventoryList) > 0:            
            availStoreIDs = getAttachedClinicsFromNetInfo(netinfo,storeID)
            availStoreIDs.append(storeID)
            sum = 0.0
            for astoreKey in availStoreIDs:
                aNetStore = netinfo.stores[long(astoreKey)]
                for peopleKey in store.people.keys():
                    sum += aNetStore.people[peopleKey]
            if sum > max: 
                max = sum
    return max

def computeSumPopulationFromNetInfo(netinfo):
    sum = 0.0
    for storeID in netinfo.stores.keys():
        store = netinfo.stores[storeID]
        for peopleKey in store.people.keys():
            sum += store.people[peopleKey]
    
    return sum

def createBarGraph(bars,barheights,xlabel,ylabel,filename,
                   maximumValue=None, engine='matplotlib'):
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
    
def computeServedPopulationForNetStore(netinfo,storeID):
    availStoreIDs = getAttachedClinicsFromNetInfo(netinfo,storeID)
    availStoreIDs.append(storeID)
    peopleDict = {'all':0.0}
    for astoreKey in availStoreIDs:
        aNetStore = netinfo.stores[long(astoreKey)]
        for peopleKey in aNetStore.people.keys():
            if not peopleDict.has_key(peopleKey):
                peopleDict[peopleKey] = 0
            peopleDict[peopleKey] = peopleDict[peopleKey] +\
                                aNetStore.people[peopleKey]
            peopleDict['all'] = peopleDict['all']+\
                                aNetStore.people[peopleKey]
                                    
    return peopleDict

def getAttachedClinicsFromNetInfo(netinfo, storeID):   
    attachedStoreIDs = []
    for route in netinfo.routes.keys():
        if str(netinfo.routes[route].supplier.idcode) == str(storeID):
            if netinfo.routes[route].Type == "attached":
                attachedKey = netinfo.routes[route].clients[0].idcode
                attachedStoreIDs.append(attachedKey)
       
    return attachedStoreIDs

def getOutreachClinicsFromNetInfo(netinfo,storeID):
    outreachStoreIDs = []
    for routeID,route in netinfo.routes.items():       
        if str(route.supplier.idcode) == str(storeID):
            # look to see if the first stop is an outreach location
            if route.stops[1].store.FUNCTION == "Outreach":
                # We have an outreach route
                for stop in route.stops:
                    if stop.store.idcode not in outreachStoreIDs:
                        outreachStoreIDs.append(stop.store.idcode)
                        
    
    return outreachStoreIDs