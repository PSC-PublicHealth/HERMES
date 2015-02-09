#! /usr/bin/env python

########################################################################
# Copyright   2010, Pittsburgh Supercomputing Center (PSC).            #
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
__doc__=""" GEViz.py
This is a utility for creating Google Earth Visualizations for a HERMES Output.
"""
_hermes_svn_id_="$Id: google_earth_viz.py 973 2012-05-25 19:42:44Z welling $"
from constants import * 
from datetime import *
from util import TimeStampAccumVal
import math
import network
import load_typemanagers
import vaccinetypes
from contextlib import closing
import zipfile
#from zipfile import ZipFile, ZIP_DEFLATED
import os,sys,shutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np
import cgi
import time

### Utility function to create a set of points in a circle
def createCircle(center_x, center_y, radius, resolution):
    points = []
    for i in range(resolution, 0, -1):
        angle = (2 * math.pi / float(resolution)) * float(i)
        points.append((center_x + radius * math.sin(angle), center_y + radius * math.cos(angle)))

    return points

### Utility function to create a set of points for a square centered at x,y
def createSquare(center_x, center_y, length):
    points = []
    x = length / math.sqrt(2.0)
    points.append((center_x + x, center_y + x))
    points.append((center_x - x, center_y + x))
    points.append((center_x - x, center_y - x))
    points.append((center_x + x, center_y - x))
    points.append((center_x + x, center_y + x))

    return points

### Dummy utility that returns a point
def createPoint(center_x, center_y):
    return [(center_x, center_y)]

class GoogleDate:
    """
    The Google Date class is intended to be used to return KML friendly date strings 
    from an initial date
    """
    
    def __init__(self,initialYear=2012,initialMonth=1,initialDay=1,
                 initialHour=9,initialMinute=0,initialSeconds=0):
        
        self.initialDate = datetime(initialYear,initialMonth,initialDay,
                                    initialHour,initialMinute,initialSeconds)
        self.initialKMLString = self._getKMLString(self.initialDate)
        
    def _getKMLString(self,dateTime):
        return dateTime.strftime("%Y-%m-%dT%H:%M:%S")
    
    def _getFormatedString(self,dateTime):
        return dateTime.strftime("%x %I:%M %p")
    
    def _getFormatedDateString(self,dateTime):
        return dateTime.strftime("%x")
    
    def getDateInFuture(self,decimalTimeInHours):
        secondsForward = timedelta(seconds=(decimalTimeInHours*86400.0))
        newDate = self.initialDate + secondsForward
        return self._getFormatedString(newDate)
    
    def getDateTimeInFuture(self,decimalTimeInHours):
        secondsForward = timedelta(seconds=(decimalTimeInHours*86400.0))
        newDate = self.initialDate + secondsForward
        return self._getFormatedString(newDate)
    
    def getDateTimeInFutureKML(self,decimalTimeInHours):
        secondsForward = timedelta(seconds=(decimalTimeInHours*86400.0))
        newDate = self.initialDate + secondsForward
        return self._getKMLString(newDate)
        
        
class GoogleVisualizaton:
    def __init__(self,outputName_,hermesRun_,hermesOutput_,googleDate_,
                 numberOfColors_=100,columnHeight_=100,title_=None):
        self.hermesRun = hermesRun_
        self.hermesOutput = hermesOutput_
        self.googleDate = googleDate_

        ## directories for HERMES Visualization
        self.KMZFileTempDir = './ge_viz'
        self.KMZFileName = 'GoogleEarthVizualization.kmz'
        self.KMZVizFileName = self.KMZFileTempDir + "/visualization.kml"
        self.KMZImageDir = self.KMZFileTempDir + "/images"
        
    	levels = self.hermesRun.model.levelList
    	vizwidths = self.hermesRun.model.vizWidths
    	vizshapes = self.hermesRun.model.vizShapes
        self.clinicLevelList = self.hermesRun.model.clinicLevelList
    	self.levelRadDict = {}
    	for level in levels:
    	    self.levelRadDict[level] = (vizwidths[levels.index(level)],vizshapes[levels.index(level)])
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
    
    def _setup(self):
        '''
        This member will fill the prerequisite data structure to build visualizations,
        and will be replaced eventually with the shadowNetwork
        '''
        self.storeNoteDict = {}
        print "calling Setup"
        for storeKey in self.hermesOutput.stores.keys():
            store = self.hermesOutput.stores[storeKey]
            if store['note'] is not None:
                storeTS = store['note']
                self.storeNoteDict[str(store['code'])] = {'note':storeTS,
                                                          'lat':self.hermesRun.storeDict[store['code']].latitude,
                                                          'longitude':self.hermesRun.storeDict[store['code']].longitude,
                                                          'level':self.hermesRun.storeDict[store['code']].category}
    
        
#        self.routeNoteDict = {}
#        for routeKey in self.hermesOutput.routes.keys():
#            route = self.hermesOutput.routes[routeKey]
#            latlongList = []
#            if route['note'] is not None:
#                routeTS = None
#                if 'RouteFill' in route['note'].keys():
#                    routeTS = route['note']['RouteFill']
#                    supplier = route['supplier']
#                    note = route['note']
#                    supplierStore = self.hermesRun.storeDict[supplier['code']]
#                    latlongList.append((supplierStore.latitude,supplierStore.longitude))
#                    routeInfo = None
#                    for clientRoute in supplier['clientRoutes']:
#                        if clientRoute['name'] == routeKey:
#                            routeInfo = clientRoute
#                            break
#                    for client in clientRoute['clients']:
#                        clientCode = client['code']
#                        clientStore = self.hermesRun.storeDict[clientCode]
#                        latlongList.append((clientStore.latitude,clientStore.longitude))
#                    latlongList.append((supplierStore.latitude,supplierStore.longitude))    
#                    self.routeNoteDict[routeKey] = {'Note':note,
#                                                    'latlongs':latlongList}
    
        ### going to instantiate this myself for now
        (self.hermesRun.typeManager,self.typeManagers) = \
              load_typemanagers.loadTypeManagers(self.hermesRun.userInput, self.hermesRun.unifiedInput,\
                                                 self.hermesRun, self.hermesRun.verbose,self.hermesRun.debug)

        for (attr,tm) in self.typeManagers.items():
            setattr(self,attr,tm)

        self.netInfo = network.loadNetwork(self.hermesRun.userInput, self.hermesRun.typeManager, self.typeManagers)
        
#        self.vizStores = {}
#        for storeKey in self.hermesOutput.stores.keys():
#            self.vizStores[storeKey] = vizStore(storeKey,self.storeNoteDict,self.netInfo)

        self.vizRoutes = {}
        for routeID in self.netInfo.routes.keys():
            self.vizRoutes[routeID] = vizRoute(routeID,self.hermesOutput,self.netInfo,self)
        ### Create KMZ directory
        try:
            os.mkdir(self.KMZFileTempDir)
        except:
            shutil.rmtree(self.KMZFileTempDir)
            os.mkdir(self.KMZFileTempDir)
        #os.chdir(kmzDirectoryName)
        os.mkdir(self.KMZImageDir)
        # Start the KML file
        with open(self.KMZVizFileName,"wb") as f:
            f.write('<kml xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:'\
                           +'atom="http://www.w3.org/2005/Atom" xmlns="http://www.opengis.net/kml/2.2">'\
                           +'<Document>')
            if self.title:
                f.write('<name>'+self.title+'</name>')
            f.write(self.createStyles("-1","-1",self.numberOfColors,"")) 
    
    def colorFromValue(self,value):
        if value < 0:
            return -1
        elif (value*self.numberOfColors) >= self.numberOfColors:
            return self.numberOfColors-1
        else:
            return int(float(self.numberOfColors)*value)
            
  
    def buildVaccineAvailablilyFolder(self,storesList):
        '''
        This member will build a Vaccine availability folder for the stores 
        specified in the storesList
        '''
        
        if self.storeNoteDict is None:
            self._setup()
        
        print "Should be writing here!"
        with open(self.KMZVizFileName,"a+b") as f:
            f.write('<Folder><name>Vaccine Aviailability</name>')
            for storeKey in storesList:
                #for storeKey in storeNoteDict.keys():
                storeNet = self.netInfo.stores[long(storeKey)]
                if len(storeNet.inventoryList) > 0:
                    store = self.storeNoteDict[str(storeKey)]
                    orig_y = store['lat']
                    orig_x = store['longitude']
                    level = store['level']
                    name = storeKey
                else:
                    continue
                ## Get Vaccine Availablities for Description
                availDict = computeVaccineAvailabilityForNetStore(self.netInfo,storeKey,
                                                                  self.storeNoteDict)
                ## Must find attached clinics to decide if they have vaccines
                availStores = getAttachedClinicsFromNetStore(self.netInfo,storeKey)
                availStores.append(storeKey)
                vaFileName = None
                if len(availDict) > 0:
                    vaFileName = self.createVaccineAvailabilityBarGraph(availDict,storeKey)
                    ## Must find attached clinics to decide if they have vaccines
                if availDict.has_key('allvax') is False:
                    availDict['allvax'] = {'patients':0.0,'treated':0.0}
                
                if availDict['allvax']['treated'] > 0.0:
                    aveVacAvail = availDict['allvax']['treated']/availDict["allvax"]['patients']
                    circPoint = createCircle(orig_x, orig_y, 0.05, 20)
                    pointStrings = []
                    for point in circPoint:
                        pointStrings.append(str(point[0]) + "," + str(point[1]) + ",")
                    pointStrings.append(str(circPoint[0][0]) + "," + str(circPoint[0][1]) + ",")
    
    #    ### Calculate Height
                    height = 100*(1.0/aveVacAvail)
        ### Calculate Color
                    color = int(self.numberOfColors * (1.0-aveVacAvail))
                    if color > 99:
                        color = 99
        #print "color " + str(color) + "vac " + str(aveVacAvail)
                    ptsString = ""
                    for pointStr in pointStrings:
                        ptsString += pointStr + str(height) + " "
    
                    f.write('<Placemark>\n')
                    f.write('<name>' + cgi.escape(store['note']['name']) + '</name>')
                    f.write('<visibility>0</visibility>')
                    f.write('<description><table width="600" cellspacing="0" cellpadding="3">')
                    f.write('<tr bgcolor="'+ self.majorColor + '"><td colspan="4"><font color = "' + self.minorColor +\
                            '">General Information</font></td></tr>')
                    
                    f.write('<tr><td colspan="3">ID:</td><td>'+str(name) + '</td></tr>')
                    f.write('<tr><td colspan="3">Level: </td><td>'+level+'</td></tr>')
    ### Begin Vaccine Information
                    f.write('<tr bgcolor="' + self.majorColor + '"><td colspan="4"><font color="' +\
                            self.minorColor + '">Vaccine Data</font></td></tr>')
                    
                    if availDict['allvax']['patients'] == 0.0:
                        f.write('<tr><td colspan="4">No Vaccines Distributed at this Location</td></tr>')
                    else:
                        f.write('<tr><td colspan="4"><img src="%s" width = "400px"></img></td></tr>'\
                                %vaFileName)
                        f.write('<tr bgcolor="' + self.minorColor + '">')
                        f.write('<td><font color="' + self.majorColor + '">Vaccine</font></td>')
                        f.write('<td><font color="' + self.majorColor + '">Doses Demanded</font></td>')
                        f.write('<td><font color="' + self.majorColor + '">Doses Administered</font></td>')
                        f.write('<td><font color="' + self.majorColor + '">Vaccine Availability (%)</font></td>')
                        f.write('</tr>')
                        for vaccineName in sorted(availDict.keys()):
                            if vaccineName == "allvax":
                                continue
                            #f.write('<tr><td>%s</td>'%vaccineName)
                            f.write('<tr><td>%s</td>'%self.typeManagers['vaccines'].getTypeByName(vaccineName).displayName)
                            f.write('<td>%10.0lf</td>'%availDict[vaccineName]['patients'])
                            f.write('<td>%10.0lf</td>'%availDict[vaccineName]['treated'])
                            avail = 0.0
                            if(availDict[vaccineName]['patients'] > 0.0):
                                avail = (availDict[vaccineName]['treated']/availDict[vaccineName]['patients'])*100.0
    
                            f.write('<td>%3.2lf</td></tr>'%avail)
                        f.write('<tr><td bgcolor="' + self.minorColor + '"><font color="' + self.majorColor +\
                                '">All Vaccines</font></td>')
                        f.write('<td bgcolor="' + self.minorColor + '"><font color="' + self.majorColor +\
                                '">%10.0lf</font></td>'%availDict['allvax']['patients'])
                        f.write('<td bgcolor="' + self.minorColor + '"><font color="' + self.majorColor +\
                                '">%10.0lf</font></td>'%availDict['allvax']['treated'])
                        avail = 0.0
                        if(availDict['allvax']['patients'] > 0.0):
                            avail = (availDict['allvax']['treated']/availDict['allvax']['patients'])*100.0
                        f.write('<td bgcolor="' + self.minorColor + '"><font color="' + self.majorColor +\
                                '">%3.2lf</font></td></tr>'%avail)
    
                    f.write('</table></description>')
                    f.write('<styleUrl>#styleva' + str(color) + '</styleUrl>')
                    f.write('<Polygon>')
                    f.write('<altitudeMode>relativeToGround</altitudeMode>')
                    f.write('<extrude>0</extrude>')
                    f.write('<outerBoundaryIs><LinearRing>')
                    f.write('<coordinates>' + ptsString + '</coordinates>')
                    f.write('</LinearRing></outerBoundaryIs>')
                    f.write('</Polygon>')
                    f.write('</Placemark>')
            f.write("</Folder>")

    def buildAvailabilityStill(self,numberOfColors=100,columnHeight=10000.0):
        pass
#                    
#    def buildLevelSpecificUtilizationStills(self, numberOfColors=100, columnHeight=10000.0):
#        for level in self.levelRadDict.keys():
#            self.buildUtilizationStill(numberOfColors,columnHeight,level,"none")
    
    def buildPopulationFolder(self,storesList):
        if self.storeNoteDict is None:
            self._setup()
        
        with open(self.KMZVizFileName,"a+b") as f:
            f.write('<Folder><name>Population</name>')
            f.write('<open>0</open>')
            populationSum = computeSumPopulationFromNetInfo(self.netInfo)
            populationMax = computeMaxPopulationFromNetInfo(self.netInfo)

            for storeKey in storesList:
                netStore = self.netInfo.stores[long(storeKey)]
                ### We don't want to put Attached Storage in this plot
                #if store['note'] is not None:
                if len(netStore.inventoryList) > 0:
                    store = self.storeNoteDict[str(storeKey)]
                    orig_y = store['lat']
                    orig_x = store['longitude']
                    level = store['level']
                    name = storeKey
                    peopleDict = computeServedPopulationForNetStore(self.netInfo,storeKey)
                    if peopleDict['all'] > 0:
                        radius = 0.2*(float(peopleDict['all'])/float(populationMax))
                        #print "People = " + str(peopleDict['all']) + ": radius = " + str(radius)
                        circPoint = createCircle(orig_x, orig_y, radius, 20)
                        pointStrings = []
                        for point in circPoint:
                            pointStrings.append(str(point[0]) + "," + str(point[1]) + ",")
                        pointStrings.append(str(circPoint[0][0]) + "," + str(circPoint[0][1]) + ",")
                                            
                        #height = int(float(peopleDict['all']/float(populationMax)) * columnHeight)
                        height = 100*(0.1/radius)
        
                        ### Calculate Color
                        color = int(self.numberOfColors * (float(peopleDict['all'])/float(populationMax)))
                        if color >= self.numberOfColors: color = 99
                        drawOrder = int(color)
                        
                        ptsString = ""
                        for pointStr in pointStrings:
                            ptsString += pointStr + str(height) + " "
                        
                        
                        
                        ### Begin the placemark for a store
                        f.write('<Placemark>\n')
                        f.write('<name>' + cgi.escape(store['note']['name']) + '</name>')
                        ### Begin the description section
                        f.write('<description><table width="600" cellspacing="0" cellpadding="3">')
                        f.write('<tr bgcolor="blue"><td colspan="4"><font color = "' + self.minorColor +\
                                '">General Information</font></td></tr>')
                        f.write('<tr><td colspan="3">ID:</td><td>'+str(name) + '</td></tr>')
                        f.write('<tr><td colspan="3">Level: </td><td>'+level+'</td></tr>')
                        f.write('<tr bgcolor="' + self.majorColor + '"><td colspan="4"><font color="' +\
                                    self.minorColor + '">Population Information</font></td></tr>')
                            
                        if peopleDict['all'] == 0:
                            f.write('<tr><td colspan="4">No Population Vaccinated at this Location</td></tr>')
                        else:
                            f.write('<tr bgcolor="' + self.minorColor + '"><td colspan="3"><font color="' +\
                                    self.majorColor + '">Population Class</font></td>')
                            f.write('<td><font color="' + self.majorColor + '">Yearly Catchment Size'\
                                    '</font></td></tr>')
                            for peopleKey in sorted(peopleDict.keys()):
                                if peopleKey != "all":
                                    f.write('<tr><td colspan="3">%s</td><td>%10d</td></tr>'\
                                            %(peopleKey,peopleDict[peopleKey]))
                        f.write('</table></description>')
                        f.write('<styleUrl>#stylepop' + str(color) + '</styleUrl>')
                        f.write('<Polygon>')
                        f.write('<altitudeMode>relativeToGround</altitudeMode>')
                        f.write('<extrude>1</extrude>')
                        f.write('<outerBoundaryIs><LinearRing>')
                        f.write('<coordinates>' + ptsString + '</coordinates>')
                        f.write('</LinearRing></outerBoundaryIs>')
                        f.write('</Polygon>')
                        f.write('</Placemark>')
            f.write('</Folder>')
    def buildUtilizationFolder(self,storeList,folderName="Utilization"):
        if self.storeNoteDict is None:
            self._setup()
        
        with open(self.KMZVizFileName,"a+b") as f:
            f.write('<Folder><name>%s</name>'%folderName)
            for storeKey in storeList:
                storeNet = self.netInfo.stores[long(storeKey)]
                ### We don't want to put Attached Storage in this plot
                #if store['note'] is not None:
                if len(storeNet.inventoryList) > 0:
                    store = self.storeNoteDict[str(storeKey)]
                    orig_y = store['lat']
                    orig_x = store['longitude']
                    level = store['level']
                    name = storeKey
                                
                    if self.levelRadDict[level][1] == "s":
                        circPoint = createSquare(orig_x, orig_y, self.levelRadDict[level][0])
                    else:
                        circPoint = createCircle(orig_x, orig_y, self.levelRadDict[level][0], 10)
                    pointStrings = []
                    for point in circPoint:
                        pointStrings.append(str(point[0]) + "," + str(point[1]) + ",")
                    pointStrings.append(str(circPoint[0][0]) + "," + str(circPoint[0][1]) + ",")

                    ## Get Vaccine Availablities for Description
                    peopleDict = {'all':0}
                    deviceDict = {}
                    sumPatients = 0.0
                    sumTreated = 0.0
                    
                    peopleDict = computeServedPopulationForNetStore(self.netInfo,storeKey)
      
                    height = 0
                    color = 0
                    if store.has_key('note'):
                        if store['note'].has_key('cooler'):
                            height = int(float(store['note']['cooler']) * self.columnHeight)
                        ### Calculate Color
                            color = int(self.numberOfColors * float(store['note']['cooler']))
                            ptsString = ""
                            for pointStr in pointStrings:
                                ptsString += pointStr + str(height) + " "
    
                            ### Begin the placemark for a store
                            f.write('<Placemark>\n')
                            f.write('<visibility>0</visibility>')
                            f.write('<name>' + cgi.escape(store['note']['name']) + '</name>')
                            ### Begin the description section
                            f.write('<description><table width="600" cellspacing="0" cellpadding="3">')
                            f.write('<tr bgcolor="' + self.majorColor + '"><td colspan="4"><font color = "' + self.minorColor +\
                                    '">General Information</font></td></tr>')
                            f.write('<tr><td colspan="3">ID:</td><td>'+str(name) + '</td></tr>')
                            f.write('<tr><td colspan="3">Level: </td><td>'+level+'</td></tr>')
    
                            ### Stock Plot
                            imgfileName = str(storeKey) + "_all_storage_curve.png"
                            f.write('<tr bgcolor="' + self.majorColor + '"><td colspan="4"><font color="' +\
                                    self.minorColor + '">Stock Over Time</font></td></tr>')
                            f.write('<tr><td colspan="4"><img width="400px" src="images/%s"></img></td></tr>'\
                                    %imgfileName)
    
                            ### Storage Information
                            f.write('<tr bgcolor="' + self.majorColor + '"><td colspan="4"><font color="' +\
                                    self.minorColor + '">Storage Information</font></td></tr>')
                            f.write('<tr><td colspan="4">Refrigerated (2-8 C) Storage</td></tr>')
                            f.write('<tr><td></td><td colspan="2">Total Volume (L)</td><td>%10.2f</td></tr>'\
                                    %store['note']['cooler_vol'])
                            f.write('<tr><td></td><td colspan="2">Max Volume Used (L)</td><td>%10.2f</td></tr>'\
                                    %store['note']['cooler_vol_used'].max())                                                                                        
                            f.write('<tr><td></td><td colspan="2">Max Utilization</td><td>%10.2f%%</td></tr>'\
                                    %(float(store['note']['cooler'].max())*100.0))
                            if store['note'].has_key('freezer'):
                                 f.write('<tr><td colspan="4">Freezer (below 0 C) Storage</td></tr>')
                                 f.write('<tr><td></td><td colspan="2">Total Volume (L)</td><td>%10.2f</td></tr>'\
                                         %store['note']['freezer_vol'])
                                 f.write('<tr><td></td><td colspan="2">Max Volume Used (L)</td><td>%10.2f</td></tr>'\
                                         %store['note']['freezer_vol_used'].max())                                                                                  
                                 f.write('<tr><td></td><td colspan="2">Max Utilization</td><td>%10.2f%%</td></tr>'\
                                         %(float(store['note']['freezer'].max())*100.0))
    
                            ## Devices
                            f.write('<tr bgcolor="' + self.minorColor + '"><td colspan="4"><font color="' +\
                                    self.majorColor + '">Storage Devices</font></td></tr>')
                            f.write('<tr><td>Device Name</td><td>Count</td><td>2-8 C Net Storage (L)</td>'\
                                    '<td>Below 0 Storage (L)</td></tr>')
                            for (count,deviceType) in self.netInfo.stores[long(storeKey)].inventoryList:
                                if self.typeManagers['fridges'].validTypeName(deviceType.name):
                                    f.write('<tr><td>%s</td><td>%10d</td><td>%10.2f</td><td>%10.2f</td></tr>'%\
                                            (deviceType.getDisplayName(),count,float(deviceType.getTotalVolByName('cooler'))/1000.0,\
                                             float(deviceType.getTotalVolByName('freezer'))/1000.0))
                            ### Begin Vehicle Information
                            f.write('<tr bgcolor="' + self.majorColor + '"><td colspan="4"><font color="' +\
                                    self.minorColor + '">Vehicle Information</font></td></tr>')
                            f.write('<tr><td>Vehicle</td><td>Count</td><td>2-8 C Net Storage (L)</td>'\
                                    '<td>Below 0 Storage (L)</td></tr>')
                            for (count,deviceType) in self.netInfo.stores[long(storeKey)].inventoryList:
                                if self.typeManagers['trucks'].validTypeName(deviceType.name):
                                    totVolSC = deviceType.getNetStorageCapacity()
                                    ### Start here Shawn
                                    displayName = deviceType.name
                                    if deviceType.displayName != "":
                                        displayName = deviceType.displayName
                                    cooler = 0.0
                                    if totVolSC.has_key('cooler'):
                                        cooler = totVolSC['cooler']
                                    freezer = 0.0
                                    if totVolSC.has_key('freezer'):
                                        freezer = totVolSC['freezer']
                                    f.write('<tr><td>%s</td><td>%d</td><td>%10.2f</td><td>%10.2f</td></tr>'%\
                                            (displayName,count,cooler/1000.0,freezer/1000.0))
                            f.write('</table></description>')
                            f.write('<styleUrl>#style' + str(color) + '</styleUrl>')
                            f.write('<Polygon>')
                            f.write('<altitudeMode>relativeToGround</altitudeMode>')
                            f.write('<extrude>1</extrude>')
                            f.write('<outerBoundaryIs><LinearRing>')
                            f.write('<coordinates>' + ptsString + '</coordinates>')
                            f.write('</LinearRing></outerBoundaryIs>')
                            f.write('</Polygon>')
                            f.write('</Placemark>')
            f.write('</Folder>')  
                 
    def buildUtilizationStill(self):

        print "\n\nCreating Google Earth Interactive Visualization with the following parameters"
        print "\tNumber of Color Gradients:\t%d"%self.numberOfColors
        print "\tMaximum Column Height\t\t%d"%self.columnHeight
        #print "\tLevel To Draw\t\t%s"%levelToDraw
        #print "\tRoutes To Draw\t\t%s"%routesToDraw
        levelToDraw = "all"
        routesToDraw = "all"
        if self.storeNoteDict is None:
            self._setup()
        
        allStoresList = [ x for x in self.storeNoteDict.keys()]
        
        ### check syntax on Levels and Routes
        if levelToDraw not in self.levelRadDict.keys() and levelToDraw != "all":
            raise RuntimeError("In buildUtilizationStill: levelToDraw: %s does not exist in this model"\
                               %levelToDraw)

                
        ### Begin the building of the visualization KML writing
        
        with open(self.KMZVizFileName,"a+b") as f:
            ### Draw Routes
            #f.write('<open>1</open>')
            f.write('<Folder><name>Routes</name>')
#            for routeID in self.netInfo.routes.keys():
#                routeNet = self.netInfo.routes[routeID]
#            
#                #routeNote = routeNoteDict[routeID]
#                #routeFill = float(route['Note']['RouteFill']
            for routeId,route in self.vizRoutes.items():
                kmlString = route.kmlPrint()
                if kmlString is not None:
                    f.write(kmlString)
            f.write('</Folder>')
            
        self.buildPopulationFolder(allStoresList)
        
        with open(self.KMZVizFileName,"a+b") as f:            
            f.write('<Folder><name>Utilization</name>')
            f.write('<open>1</open>')
            ### Draw Stores By Level
        for levelHere in self.levelRadDict.keys():
            thisLevelStores = []
            for storeKey,store in self.netInfo.stores.items():
                if store.CATEGORY == levelHere:
                    thisLevelStores.append(storeKey)
            self.buildUtilizationFolder(thisLevelStores,"%s Level Stores"%(levelHere))

        with open(self.KMZVizFileName,"a+b") as f:
            f.write('</Folder>')
            
                ### Create Availability Folder
        self.buildVaccineAvailablilyFolder(allStoresList)
        with open(self.KMZVizFileName,"ab") as f:
            f.write("</Document></kml>")

        ### move stockPlots to the images directory
        stockList = os.listdir('./stockPlots')
        for stockPlot in stockList:     
            shutil.move('./stockPlots/'+stockPlot,self.KMZImageDir)
        shutil.rmtree('stockPlots')
        zipper(self.KMZFileTempDir,self.KMZFileName)
        #shutil.rmtree(self.KMZFileTempDir)
        #print "Time to create VA plots = %g sec"%(timeVA)
        
    def buildUtilizationAnimation(self,numberOfSegments=1,numberOfColors=100,columnHeight=100000.0):
        pass
#        print "\n\nCreating Google Utilization Animation with the following parameters"
#        print "\tNumber of Segments\t\t%d"%numberOfSegments
#        print "\tNumber of Color Gradients:\t%d"%numberOfColors
#        print "\tMaximum Column Height\t\t%d"%columnHeight
#        print "\tStarting Date\t\t\t%s"%str(self.googleDate.initialDate)
#        
#        ## Dicts to organize data
#        storeNoteDict = {}
#        routeNoteDict = {}
#        thisValuesDict = {}
#        for storeKey in self.hermesOutput.stores.keys():
#            store = self.hermesOutput.stores[storeKey]
#            if store['note'] is not None:
#                storeTS = None
#                if 'cooler_timestamp' in store['note'].keys():
#                    storeTS = store['note']['cooler_timestamp']
#                    storeNoteDict[str(store['code'])] = {'note':storeTS,
#                                                        'lat':self.hermesRun.storeDict[store['code']].latitude,
#                                                        'longitude':self.hermesRun.storeDict[store['code']].longitude,
#                                                        'level':self.hermesRun.storeDict[store['code']].category}
#        for routeKey in self.hermesOutput.routes.keys():
#            route = self.hermesOutput.routes[routeKey]
#            latlongList = []
#            if route['note'] is not None:
#                routeTS = None
#                if 'triptimes_timestamp' in route['note'].keys():
#                    routeTS = route['note']['triptimes_timestamp']
#                    supplier = route['supplier']
#                    note = route['note']
#                    supplierStore = self.hermesRun.storeDict[supplier['code']]
#                    latlongList.append((supplierStore.latitude,supplierStore.longitude))
#                    routeInfo = None
#                    for clientRoute in supplier['clientRoutes']:
#                        if clientRoute['name'] == routeKey:
#                            routeInfo = clientRoute
#                            break
#                    for client in clientRoute['clients']:
#                        clientCode = client['code']
#                        clientStore = self.hermesRun.storeDict[clientCode]
#                        latlongList.append((clientStore.latitude,clientStore.longitude))
#                        
#                    routeNoteDict[routeKey] = {'note':routeTS,
#                                               'latlongs':latlongList}
#                    
#        
#        ### Create KMZ directory
#        kmzDirectoryName = self.KMLFileBase
#        try:
#            os.mkdir(kmzDirectoryName)
#        except:
#            shutil.rmtree(kmzDirectoryName)
#            os.mkdir(kmzDirectoryName)
#        os.chdir(kmzDirectoryName)
#        os.mkdir('timesteps')
#        timeStep = 0.5
#        numberOfTimeSteps = int(float(self.runDays)/timeStep)
#        ### create the overall network file
#        
#        with open("visualization.kml","wb") as f:
#            f.write("<Document>\n")
#            for i in range(0,numberOfTimeSteps):
#                begin = self.googleDate.getDateTimeInFuture(i)
#                end = self.googleDate.getDateTimeInFuture(i+1)
#                f.write("<NetworkLink>\n")
#                f.write("<name>" + str(begin) + "-" + str(end) + "</name>\n")
#                f.write("<visibility>1</visibility>\n")
#                f.write('<TimeSpan>\n<begin>' + begin + '</begin>\n')
#                f.write('<end>' + end + '</end>\n</TimeSpan>\n')
#                f.write('<Link><href>timesteps/vis_ts.'+str(i)+'.kml</href></Link>\n')
#                f.write('</NetworkLink>\n')
#            f.write('</Document>')
#        printFlag =  False
#        for i in range(0,numberOfTimeSteps):
#            if i > 0:
#                printFlag = True
#            timeStart = i*timeStep+self.burninDays
#            timeEnd = timeStart + timeStep
#            
#            tsFilename = "timesteps/vis_ts."+str(i)+".kml"
#            
#            ### First Put the Routes that appear in this time step 
#            with open(tsFilename,"wb") as f:
#                f.write('<Document>')
#                styleString = self.createStyles("-1","-1",numberOfColors,"")
#                f.write(styleString)
#                
#                for routeKey in routeNoteDict.keys():
#                    route = routeNoteDict[routeKey]
#                    if route['note'] is not None:
#                        routeLocations = route['latlongs']
#                        numberTrips = len(routeLocations)-1
#                        timesLists = [route['note'].t[i:i+numberTrips] \
#                                      for i in xrange(0,len(route['note'].t),numberTrips)]
#                        flatTimeList = []
#                        for timesList in timesLists:
#                            fillPer = route['note'].v[timesLists.index(timesList)]
#                            for i in range(0,len(timesList)):
#                                flatTimeList.append((timesList[i],fillPer,routeLocations[i],routeLocations[i+1]))
#                        #print 'Route(' + str(routeKey) + ': ' + str(flatTimeList)
#                        for entry in flatTimeList:
#                            #if routeKey == "r141004":
#                            #    print "Times:" + str(timeStart) + " - " + str(timeEnd) + ": " + str(entry[0][0]) + " - " + str(entry[0][1])
#                            if (entry[0][0] >= timeStart and entry[0][0] < timeEnd) or (entry[0][1] >= timeStart and entry[0][1] < timeEnd):
#                                    ### This route appears in this timestep.
#                                #if routeKey == "r141004":
#                                #    print "1"
#                                color = 0
#                                if entry[1] > 1.0:
#                                    color = numberOfColors - 1
#                                else:
#                                    color = int(float(numberOfColors)*entry[1])
#                                    
#                                #begin = self.googleDate.getDateTimeInFuture(entry[0][0])
#                                #end = self.googleDate.getDateTimeInFuture(entry[0][1])
#                #                
#                                f.write('<Placemark>\n')#<TimeSpan>\n<begin>' + begin + '</begin>\n')
#                                #f.write('<end>' + end + '</end>\n</TimeSpan>\n')
#                                f.write('<styleUrl>#styletrans' + str(color) + '</styleUrl>\n')
#                                f.write('<LineString>\n')
#                                f.write('<altitudeMode>clampToGround</altitudeMode>\n')
#                                f.write('<coordinates>\n')
#                                f.write('%f,%f,0.0 '%(entry[2][1],entry[2][0]))
#                                f.write('%f,%f,0.0 '%(entry[3][1],entry[3][0]))
#                                f.write('</coordinates>\n')
#                                f.write('</LineString>\n')
#                                f.write('</Placemark>\n')
#                
#                for storeKey in storeNoteDict.keys():
#                    store = storeNoteDict[storeKey]
#                    if 1==1:
#                    #if storeKey == "150100" or storeKey == "150108":
#                        if store['note'] is not None:
#                            orig_y = store['lat']
#                            orig_x = store['longitude']
#                            level = store['level']
#                            name = storeKey
#                            #print "Level = " + str(level)
#                            timeSeries = store['note']
#                            times = timeSeries.t
#                            values = timeSeries.v
#                            #if printFlag is False:
#                            #    print "Times for " + str(storeKey) + ": " +str(times)
#                            #    print "Values for " + str(storeKey) + ": " + str(values)
#                            ### Eliminate redundant time values    
#                            tPrev = None
#                            cleanTimes = [0.0]
#                            cleanValues = [0.0]
#                            for i in range(0, len(times)):
#                                if times[i] != tPrev:
#                                    cleanTimes.append(times[i])
#                                    cleanValues.append(values[i])
#                                    tPrev = times[i]
#                            ## Find the appropriate level for this timeStep
#                            #if printFlag is False:
#                                #print "Clean Times for " + str(storeKey) + ": " +str(times)
#                                #print "Clean Values for " + str(storeKey) + ": " + str(values)
#                            thisTime = 0
#                            thisValue = 0
#                            if thisValuesDict.has_key(storeKey) is False:
#                                timeC = 0
#                                tcount = 0
#                                while timeC < self.burninDays:
#                                    timeC = cleanTimes[tcount]
#                                    tcount += 1
#                                #print "Here"
#                                thisValuesDict[storeKey] = cleanValues[cleanTimes.index(timeC)]
#                            thisValueList = []
#                            for timeC in cleanTimes:
#                                if timeC >= timeStart and timeC < timeEnd:
#                                    #print "Using Value " + str(cleanValues[cleanTimes.index(timeC)])
#                                    thisValueList.append(cleanValues[cleanTimes.index(timeC)])
#                                
#                            if len(thisValueList)>0:
#                                thisValue = sum(thisValueList)/float(len(thisValueList))
#                            #    print "Setting value for " + storeKey + " to " + str(thisValue) + " at " + str(timeC)
#                                thisValuesDict[storeKey] = thisValue  
#                                    
#                            #print "TimeStart = " + str(timeStart) + " TimeEnd = "+str(timeEnd)
#                            #print "This Value " + str(storeKey) + "= " + str(thisValuesDict[storeKey])
#                            if self.levelRadDict[level][1] == "s":
#                                circPoint = createSquare(orig_x, orig_y, self.levelRadDict[level][0])
#                            else:
#                                circPoint = createCircle(orig_x, orig_y, self.levelRadDict[level][0], 10)
#                            
#                            #if level == "Central" or level == "Region":
#                            if level !="Something else":
#                                pointStrings = []
#                                #for i in range(len(circPoint)-1,0,-1):
#                                for point in circPoint:
#                                    pointStrings.append(str(point[0]) + "," + str(point[1]) + ",")
#                                pointStrings.append(str(circPoint[0][0]) + "," + str(circPoint[0][1]) + ",")
#                        
#                                #for s in range(0, numberOfSegments):
#                                #    for i in range(1, len(cleanTimesSeg[s])):
#                                ### Calculate Height
#                                height = int(thisValuesDict[storeKey] * columnHeight)
#                                ### Calculate Color
#                                color = int(numberOfColors * thisValuesDict[storeKey])
#                        
#                                ### get Times
#                                        #begin = self.googleDate.getDateTimeInFuture(cleanTimesSeg[s][i - 1])
#                                        #end = self.googleDate.getDateTimeInFuture(cleanTimesSeg[s][i])
#                        
#                                ptsString = ""
#                                for pointStr in pointStrings:
#                                    ptsString += pointStr + str(height) + " "
#                
#                                f.write('<Placemark>')
#                                f.write('<name>' + str(name) + '</name>')
#                                f.write('<styleUrl>#style' + str(color) + '</styleUrl>')
#                                f.write('<Polygon>')
#                                f.write('<altitudeMode>relativeToGround</altitudeMode>')
#                                f.write('<extrude>1</extrude>')
#                                f.write('<outerBoundaryIs><LinearRing>')
#                                f.write('<coordinates>' + ptsString + '</coordinates>')
#                                f.write('</LinearRing></outerBoundaryIs>')
#                                f.write('</Polygon>')
#                                f.write('</Placemark>')
#                f.write('</Document>')
#        ### Start writing the file, have to do this because string concantination is 
#        ### abyssmally slow
#        os.chdir('../')
#        zipper(kmzDirectoryName,'testAnim.kmz')
#        sys.exit()
        ## This will make a series of files that are segmented in time to allow for more
        ## robust visualization on Google Earth, due to its assness of not being able to 
        ## display a lot of stuff.
        
#        timeLimit = int(self.runDays/float(numberOfSegments))
#        files = []
#        for s in range(0,numberOfSegments):
#            files.append(open(self.KMLFileBase + '.seg' + str(s) + '.kml',"wb"))
#            files[s].write('<kml xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:'\
#                           +'atom="http://www.w3.org/2005/Atom" xmlns="http://www.opengis.net/kml/2.2">'\
#                           +'<Document>')
#        
#        
#        styleString = self.createStyles("-1","-1",numberOfColors,"")
#        for s in range(0,numberOfSegments):
#            files[s].write(styleString)
#
#        ### Build the route lines for the viz
#        ### this is a bit messy, but it works.
#        
#        for routeKey in routeNoteDict.keys():
#            route = routeNoteDict[routeKey]
#            if route['note'] is not None:
#                routeLocations = route['latlongs']
#                numberTrips = len(routeLocations) - 1
#                timesLists = [route['note'].t[i:i+numberTrips] for i in xrange(0,len(route['note'].t),numberTrips)]
#                flatTimeList = []
#                for timesList in timesLists:
#                    fillPer = route['note'].v[timesLists.index(timesList)]
#                    for i in range(0,len(timesList)):
#                        flatTimeList.append((timesList[i],fillPer,routeLocations[i],routeLocations[i+1]))
#                
#                flatTimeSegments = []
#                for i in range(0,numberOfSegments):
#                    flatTimeSegments.append([])
#                for entry in flatTimeList:
#                    if entry[0][1] < self.burninDays:
#                        flatTimeList.remove(entry)
#        
#                if flatTimeList[0][0][0] < self.burninDays:
#                    flatTimeSegments[0].append(((0.0,flatTimeList[0][0][1]),flatTimeList[0][1],flatTimeList[0][2],flatTimeList[0][3]))
#                    flatTimeList.remove(flatTimeList[0])
#                    
#                segmentCount=0
#                for entry in flatTimeList:
#                    beginTime = entry[0][0] - self.burninDays
#                    endTime = entry[0][1] - self.burninDays
#                    
#                    if endTime > timeLimit*(segmentCount+1):
#                        if beginTime < timeLimit*(segmentCount+1):
#                            flatTimeSegments[segmentCount].append(((beginTime,timeLimit),entry[1],entry[2],entry[3]))
#                            flatTimeSegments[segmentCount+1].append(((timeLimit,endTime),entry[1],entry[2],entry[3]))
#                            segmentCount+=1
#                            continue
#                        else:
#                            segmentCount+=1
#                    flatTimeSegments[segmentCount].append(((beginTime,endTime),entry[1],entry[2],entry[3]))
#                
#                for s in range(0,numberOfSegments):
#                    for entry in flatTimeSegments[s]:
#                        color = 0
#                        if entry[1] > 1.0:
#                            color = numberOfColors - 1
#                        else:
#                            color = int(float(numberOfColors)*entry[1])
#                            
#                        begin = self.googleDate.getDateTimeInFuture(entry[0][0])
#                        end = self.googleDate.getDateTimeInFuture(entry[0][1])
#        #                
#                        files[s].write('<Placemark>\n<TimeSpan>\n<begin>' + begin + '</begin>\n')
#                        files[s].write('<end>' + end + '</end>\n</TimeSpan>\n')
#                        files[s].write('<styleUrl>#styletrans' + str(color) + '</styleUrl>\n')
#                        files[s].write('<LineString>\n')
#                        files[s].write('<altitudeMode>clampToGround</altitudeMode>\n')
#                        files[s].write('<coordinates>\n')
#                        files[s].write('%f,%f,0.0 '%(entry[2][1],entry[2][0]))
#                        files[s].write('%f,%f,0.0 '%(entry[3][1],entry[3][0]))
#                        files[s].write('</coordinates>\n')
#                        files[s].write('</LineString>\n')
#                        files[s].write('</Placemark>\n')
#                        
#        for storeKey in storeNoteDict.keys():
#            store = storeNoteDict[storeKey]
#            if store['note'] is not None:
#                orig_y = store['lat']
#                orig_x = store['longitude']
#                level = store['level']
#                name = storeKey
#                #print "Level = " + str(level)
#                timeSeries = store['note']
#                times = timeSeries.t
#                values = timeSeries.v
#                
#                ### Eliminate burnin and redundant time values    
#                tPrev = None
#                cleanTimes = [0.0]
#                cleanValues = [0.0]
#                for i in range(0, len(times)):
#                    if times[i] != tPrev:
#                        cleanTimes.append(times[i] - self.hermesRun.model.burninDays)
#                        cleanValues.append(values[i])
#                        tPrev = times[i]
#            
#                cleanTimesSeg = []
#                cleanValuesSeg = []
#                    
#            
#                for i in range(0, numberOfSegments):
#                    cleanTimesSeg.append([])
#                    cleanValuesSeg.append([])
#            
#            
#                segCount = 0
#                for i in range(0, len(cleanTimes) - 1):
#                    if(cleanTimes[i] <= timeLimit * (segCount + 1)):
#                        cleanTimesSeg[segCount].append(cleanTimes[i])
#                        cleanValuesSeg[segCount].append(cleanValues[i])
#                    else:
#                        #print "Updating SegCount with time " + str(cleanTimes[i])
#                        cleanTimesSeg[segCount].append(timeLimit * (segCount + 1))
#                        cleanValuesSeg[segCount].append(cleanValues[i - 1])
#                        segCount += 1
#                        cleanTimesSeg[segCount].append(timeLimit * segCount)
#                        cleanValuesSeg[segCount].append(cleanValues[i - 1])
#                        
#			#if level == "Region" or level == "Integrated Health Center":
#		if self.levelRadDict[level][1] == "s":
#                    circPoint = createSquare(orig_x, orig_y, self.levelRadDict[level][0])
#                else:
#                    circPoint = createCircle(orig_x, orig_y, self.levelRadDict[level][0], 10)
#                #if level == "Central" or level == "Region":
#                if level !="Something else":
#                    pointStrings = []
#                    #for i in range(len(circPoint)-1,0,-1):
#                    for point in circPoint:
#                        pointStrings.append(str(point[0]) + "," + str(point[1]) + ",")
#                    pointStrings.append(str(circPoint[0][0]) + "," + str(circPoint[0][1]) + ",")
#            
#                    for s in range(0, numberOfSegments):
#                        for i in range(1, len(cleanTimesSeg[s])):
#                    ### Calculate Height
#                            height = int(cleanValuesSeg[s][i-1] * columnHeight)
#                    ### Calculate Color
#                            color = int(numberOfColors * cleanValuesSeg[s][i-1])
#            
#                    ### get Times
#                            begin = self.googleDate.getDateTimeInFuture(cleanTimesSeg[s][i - 1])
#                            end = self.googleDate.getDateTimeInFuture(cleanTimesSeg[s][i])
#            
#                            ptsString = ""
#                            for pointStr in pointStrings:
#                                ptsString += pointStr + str(height) + " "
#            
#                            files[s].write('<Placemark><TimeSpan><begin>' + begin + '</begin>')
#                            files[s].write('<end>' + end + '</end></TimeSpan>')
#                            files[s].write('<name>' + str(name) + '</name>')
#                            files[s].write('<styleUrl>#style' + str(color) + '</styleUrl>')
#                            files[s].write('<Polygon>')
#                            files[s].write('<altitudeMode>relativeToGround</altitudeMode>')
#                            files[s].write('<extrude>1</extrude>')
#                            files[s].write('<outerBoundaryIs><LinearRing>')
#                            files[s].write('<coordinates>' + ptsString + '</coordinates>')
#                            files[s].write('</LinearRing></outerBoundaryIs>')
#                            files[s].write('</Polygon>')
#                            files[s].write('</Placemark>')
#                            
#        for s in range(0, numberOfSegments):
#            files[s].write("</Document></kml>")
#            files[s].close()  
#            print "Wrote " + self.KMLFileBase + '.seg' + str(s) + '.kml to disk'                       
        
    def createStyles(self,beginColor,endColor,numberGradients,styleSuffix):
        ###! Right now only supports ' + self.majorColor + ' to red
        ### need to add additional color support
        styleString = ""
        
        for i in range(0, numberGradients):
            blue = 255 - int(255.0 / float(numberGradients) * i)
            blue_hex = hex(blue)[2:4]
            blue_hex_str = str(blue_hex)
            if len(blue_hex_str) == 1:
                blue_hex_str = "0" + blue_hex_str
            red = int(255.0 / float(numberGradients) * i)
            red_hex = hex(red)[2:4]
            red_hex_str = str(red_hex)
            if len(red_hex_str) == 1:
                red_hex_str = "0" + red_hex_str
    
            styleString += '<Style id = "style' + str(i) + styleSuffix + '">\n<LineStyle><color>ff' + blue_hex_str + '00' + red_hex_str
            styleString += '</color></LineStyle>\n<PolyStyle><color>ff' + blue_hex_str + '00' + red_hex_str
            styleString += '</color></PolyStyle>\n</Style>\n'
            styleString += '<Style id = "styletrans' + str(i) + styleSuffix + '">\n<LineStyle><color>ff' + blue_hex_str + '00' + red_hex_str
            styleString += '</color><width>3.0</width></LineStyle>\n</Style>\n'
            styleString += '<Style id = "stylepop' + str(i) + styleSuffix + '">\n<LineStyle><color>ff000000'
            styleString += '</color></LineStyle>\n<PolyStyle><color>ff' + blue_hex_str + '00' + red_hex_str
            styleString += '</color></PolyStyle>\n</Style>\n'
            styleString += '<Style id = "styleva' + str(i) + styleSuffix + '">\n<PolyStyle><outline>0</outline><color>ff' + blue_hex_str + '00' + red_hex_str
            styleString += '</color></PolyStyle>\n</Style>\n'
        styleString += '<Style id = "styletrans-1' + styleSuffix + '"><LineStyle><color>ffffffff</color><width>4.0</width></LineStyle></Style>'
        
        return styleString            

    ### NOTE Refactor once network graph is in output
    def createVaccineAvailabilityBarGraph(self,availDict,storeID):
            bars = []
            barheights = []
            
            for vaccine in availDict.keys():
                if vaccine != "allvax":
                    
                    bars.append(self.typeManagers['vaccines'].getTypeByName(vaccine).displayName)
                    if availDict[vaccine]['patients'] == 0:
                        barheights.append(0.0)
                    else:
                        barheights.append((float(availDict[vaccine]['treated'])/float(availDict[vaccine]['patients']))*100.0)
            vaFileName = "%s/vaccine_avail_%s.png"%(self.KMZImageDir,storeID)
                
            NRange = np.arange(len(bars))
            #VAsubpt.bar(NRange,barheights,width=width)
            #VAcanvas.draw()
            width = 0.5
            VAfig = Figure(figsize=(8,8))
            VAsubpt = VAfig.add_subplot(111,autoscaley_on=True,ymargin=1.0)
            VAsubpt.set_xlabel("Vaccine")
            VAsubpt.set_ylabel("Percentage Vaccine Available")
            VAsubpt.bar(NRange,barheights,width=width)
            VAsubpt.set_xticks(NRange+width/2)
            VAsubpt.set_xticklabels(bars,rotation=30,fontsize=9)
            VAsubpt.axis([0,len(bars),0,100])
            VAcanvas = FigureCanvasAgg(VAfig)
            VAcanvas.print_figure(vaFileName,dpi=40)
            return vaFileName

class vizRoute:
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
        
        ### Create the names for the route
        for stop in self._netInfo.stops:
            stopStore = stop.store
            self.latlonCoordinates.append((float(stopStore.Latitude),float(stopStore.Longitude)))
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

                    #routeVol = self.totVolAvail*tripFill if tripFill != -1.0 else 0.0
                    
                    
                    self.tripManifest.append({'start':self._netInfo.stops[iStart].store.NAME,
                                              'end':self._netInfo.stops[iEnd].store.NAME,
                                              'tStart':tripTime[0],
                                              'tEnd':tripTime[1],
                                              'LitersCarried':routeVol}
                                             )
                    iStart  += 1
                           
    def kmlPrint(self):
        kmlList = []
        print "KML Printing Route " + str(self.iD)
        if self._note is None:
            return None
        
        kmlList.append('<Placemark>')
        kmlList.append('<name>%s</name>'%self.parsedName)
        if self._note.has_key('RouteFill'):
            routeFill = self._note['RouteFill'].mean()
            routeOver = 0.0
            if routeFill > 1.0:
                routeOver = routeFill - 1.0
                routeFill = 1.0
            color = self.visualizationInfo.colorFromValue(routeFill)
            #print str(routeFill) + " " + str(color)
        else:   
            color = -1
            routeFill = 0.0
        kmlList.append('<styleUrl>#styletrans%d</styleUrl>'%color)
        kmlList.append('<LineString>')
        kmlList.append('<altitudeMode>clampToGround</altitudeMode>')
        kmlList.append('<coordinates>')
        for i in range(0,len(self.latlonCoordinates)):
            kmlList.append('%f,%f,0.0 '%(self.latlonCoordinates[i][1],
                                         self.latlonCoordinates[i][0]))
        kmlList.append('</coordinates>')
        kmlList.append('</LineString>')
        kmlList.append('<description><table width="700" cellspacing="0" cellpadding="3">')
        kmlList.append('<tr bgcolor="' + self.visualizationInfo.majorColor + '"><td colspan="4">'\
                       +'<font color = "' + self.visualizationInfo.minorColor \
                       + '">Route Information</font></td></tr>')
        kmlList.append('<tr><td>Type: </td><td colspan="3">'+str(self.parsedType) + '</td></tr>')
        kmlList.append('<tr><td>Levels: </td><td colspan="3">'+str(self.parsedLevelName) + '</td></tr>')
        
        kmlList.append('<tr bgcolor="'+self.visualizationInfo.minorColor+'"><td colspan="4"><font color="'+\
                       self.visualizationInfo.majorColor+ '">Transport Information</font></td></tr>')
        kmlList.append('<tr><td>Vehicle</td><td>2-8 C Net Storage(L)</td>'\
                       +'<td>Maximum Utilization</td><td>Number of Trips</td></tr>')
        for vehicle in self.transportInfo:
            kmlList.append('<tr><td>%s</td><td>%10.0f</td><td>%10.2f%%</td><td>%10.0d</td></tr>'\
                           %(vehicle['name'],vehicle['volL'],\
                             routeFill*100.0,self.numberOfTrips))
        
        kmlList.append('<tr bgcolor="'+self.visualizationInfo.minorColor+'"><td colspan="4"><font color="'+\
                       self.visualizationInfo.majorColor+ '">Trip Manifest</font></td></tr>')  
        kmlList.append('<tr><td>Segment</td><td>Time Start</td><td>Time Arrived</td><td>Vol Carried (L)</td></tr>')  
        for trip in self.tripManifest:
            kmlList.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%10.2f</td></tr>'%(\
                            trip['start']+\
                            " to "+ trip['end'], 
                            self.visualizationInfo.googleDate.getDateTimeInFuture(trip['tStart']),
                            self.visualizationInfo.googleDate.getDateTimeInFuture(trip['tEnd']),
                            trip['LitersCarried']))
            
        #vehicleType = self.visualizationInfo.typeManagers['trucks'].getTypeByName(vehicle)
        #kmlList.append('<tr><td colspan="3">Vehicle:</td><td>'+str(vehicleType.getDisplayName())+'</td></tr>')
        #kmlList.append('<tr><td colspan="3">Maximum Utilization:</td><td>'+str(routeFill*100.0)+'%%</td></tr>')
        #kmlList.append('<tr><td colspan="3">Number of Trips Made:</td><td>'+str(self._note['RouteTrips']))
        
        #if routeOver > 0.0:
        #    kmlList.append('<tr><td colspan="3">Percentage Over )
        kmlList.append('</table></description>')
                       
        kmlList.append('')
        kmlList.append('</Placemark>')
        return ''.join(kmlList)
        
        ### first determine 
        
#class vizStore:
#    '''
#          This is a class that should be used to build in all of the information for a 
#    storage facilities visualization, including members that will print out 
#    records for whatever vizualization one wants
#    
#    Starting with Google Earth and will generalize
#    '''
#    def __init__(self,storeID_,storeOut_,netInfo_):
#        self.clinics = getAttachedClinicsFromNetStore(netInfo_,storeID_)
#        self.clinics.append(storeID_)
#    
#        self._notes = {}
#        self._nets = {}
#        for clinic in self.clinics:
#            self._notes[clinic] = storeNoteDict_[clinic]
#            self._nets[clinic] = storeNoteDict_[long(clinic)]
#        
#        
#        self.vaccineAvail = self.computeVaccineAvailability()
#        self.populationServed = self.computeServedPopulation()
#        
#        
#    def computeVaccineAvailability(self):
#        #for storeKey in self.clinics:
#        #    astore = storeNoteDict[str(astoreKey)]
#        #aNetStore = netInfo.stores[long(astoreKey)]
#        availDict = {}
#        for note in self.notes:
#            for noteKey in note['note']:
#                if noteKey[-9:] == "_patients":
#                    vaccineName = noteKey[:-9]
#                    if not availDict.has_key(vaccineName):
#                        availDict[vaccineName] = {'patients':0.0,'treated':0.0}
#                
#                    availDict[vaccineName]['patients'] = availDict[vaccineName]['patients']\
#                                                     + float(note[noteKey])
#                    availDict[vaccineName]['treated']  = availDict[vaccineName]['treated']\
#                                                     +float(note[vaccineName + "_treated"])
#        return availDict
#    
#    def computeServedPopulationForNetStore(self):
#        peopleDict = {'all':0.0}
#        for netStore in self._nets:
#        #for astoreKey in self.clinics:
#            #aNetStore = netinfo.stores[long(astoreKey)]
#            for peopleKey in netStore.people.keys():
#                if not peopleDict.has_key(peopleKey):
#                    peopleDict[peopleKey] = 0
#                peopleDict[peopleKey] = peopleDict[peopleKey] +\
#                                    netStore.people[peopleKey]
#                peopleDict['all'] = peopleDict['all']+\
#                                    netStore.people[peopleKey]
#                                        
#        return peopleDict 
def zipper(dir, zip_file):
    zip = zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED)
    root_len = len(os.path.abspath(dir))
    for root, dirs, files in os.walk(dir):
        archive_root = os.path.abspath(root)[root_len:]
        for f in files:
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            #print f
            zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    zip.close()
    return zip_file

### This doesn't work at the momemnt
def getChildrenPopulations(netinfo,storeID):
    storeRoutes = []
    populationDict = {}
    ### First add the population for this store
    store = netinfo.stores[long(storeID)]
    for peopleKey in store.people.keys():
        populationDict[peopleKey] = store.people[peopleKey]
    ## Find all of the routes from this store
    for route in netinfo.routes.keys():
        if str(netinfo.routes[route].supplier.idcode) == str(storeID):
            ## if attached, always
            storeRoutes.append(route)
    #print "Routes for " + str(storeID) + " are " + str(storeRoutes)
    populationChildDict = {}
    for route in storeRoutes:
        #print "Route: " + route + " Child = " + str(netinfo.routes[route].clients[0].idcode)
        populationChildDict = getChildrenPopulations(netinfo,
                                                     netinfo.routes[route].clients[0].idcode)
    
        for peopleKey in populationChildDict.keys():
            if peopleKey in populationDict.keys():
                populationDict[peopleKey] += populationChildDict[peopleKey]
            else:
                populationDict[peopleKey] = populationChild[peopleKey]
    
    #print "for Store " + str(storeID) + " population" + str(populationDict['Newborn'])    
    return populationDict
            
    
def getAttachedClinicsFromNetStore(netinfo, storeID):   
    attachedStoreIDs = []
    for route in netinfo.routes.keys():
        if str(netinfo.routes[route].supplier.idcode) == str(storeID):
            if netinfo.routes[route].Type == "attached":
                attachedKey = netinfo.routes[route].clients[0].idcode
                attachedStoreIDs.append(attachedKey)
    
    
    return attachedStoreIDs

def computeVaccineAvailabilityForNetStore(netinfo,storeID,storeNoteDict):
    availStoreIDs = getAttachedClinicsFromNetStore(netinfo,storeID)
    availStoreIDs.append(storeID)
    availDict = {}
    # Compute the Vaccine Availability for the store and attached stores
    for astoreKey in availStoreIDs:
        astore = storeNoteDict[str(astoreKey)]
        #aNetStore = netInfo.stores[long(astoreKey)]
        for noteKey in astore['note'].keys():
            if noteKey[-9:] == "_patients":
                vaccineName = noteKey[:-9]
                if not availDict.has_key(vaccineName):
                    availDict[vaccineName] = {'patients':0.0,'treated':0.0}
                
                availDict[vaccineName]['patients'] = availDict[vaccineName]['patients']\
                                                 + float(astore['note'][noteKey])
                availDict[vaccineName]['treated']  = availDict[vaccineName]['treated']\
                                                 +float(astore['note'][vaccineName + "_treated"])
    return availDict

def computeServedPopulationForNetStore(netinfo,storeID):
    availStoreIDs = getAttachedClinicsFromNetStore(netinfo,storeID)
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

def computeMaxPopulationFromNetInfo(netinfo):
    max = -999999
    for storeID in netinfo.stores.keys():
        store = netinfo.stores[long(storeID)]
        if len(store.inventoryList) > 0:
#            if int(storeID) > 500000: 
#                print "StoreID = " + str(storeID) + " Inventory = " + str(store.inventoryList)
            
            availStoreIDs = getAttachedClinicsFromNetStore(netinfo,storeID)
            availStoreIDs.append(storeID)
#            if int(storeID) == 141002:
#                print str(availStoreIDs)
            sum = 0.0
            for astoreKey in availStoreIDs:
                aNetStore = netinfo.stores[long(astoreKey)]
                for peopleKey in store.people.keys():
#                    if int(storeID) == 141002:
#                        print peopleKey + " " + str(storeID) + " = " + str(store.people[peopleKey])
                    sum += aNetStore.people[peopleKey]
            if sum > max: 
#                print "Setting Max at " + str(sum) + " for " + str(storeID)
                max = sum
    return max

def computeSumPopulationFromNetInfo(netinfo):
    sum = 0.0
    for storeID in netinfo.stores.keys():
        store = netinfo.stores[storeID]
        for peopleKey in store.people.keys():
            sum += store.people[peopleKey]
    
    return sum


                                 
def main():
    "Provides a few test routines"

    googleDate = GoogleDate()
    googleDateExpl = GoogleDate(initialYear=2015,initialMonth=9,initialDay=16)
    print googleDate.getDateTimeInFuture(450.03)
    print googleDateExpl.getDateTimeInFuture(6.02)
    print googleDate.getDateTimeInFutureKML(450.03)
    print googleDateExpl.getDateTimeInFutureKML(6.02)
    
    print "Dates: %s %s"%(googleDate.initialKMLString,googleDateExpl.initialKMLString)
############
# Main hook
############

if __name__=="__main__":
    main()

    
