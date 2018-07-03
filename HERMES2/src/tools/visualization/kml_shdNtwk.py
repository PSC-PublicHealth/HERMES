#! /usr/bin/env python


from __future__ import with_statement
__doc__=""" kml.py
This is a utility for creating kml elements for Google Earth Visualizations for a HERMES Output.
"""
_hermes_svn_id_="$Id: google_earth_viz.py 973 2012-05-25 19:42:44Z welling $"

from constants import *
import math
import visualization_shdntwk as viz
from datetime import *
import os,sys,shutil
from util import zipper

placemarkTypes = ["point","circle","square","line",'linestring']

class KMLVisualization(viz.Visualization):
    def __init__(self,shadow_network_=None,resultsID_=None,kmlDate_=None,
                 numberOfColors_=100,columnHeight_=100,populationRadius_=0.2,
                 vaccineAvailRadius_=0.05,
                 title_=None):
        viz.Visualization.__init__(self,shadow_network_=shadow_network_,
                                   resultsID_=resultsID_,
                                   numberOfColors_=numberOfColors_,
                                   columnHeight_=columnHeight_,
                                   populationRadius_=populationRadius_,
                                   vaccineAvailRadius_=vaccineAvailRadius_,
                                   title_=title_)
        
        self.kmlDate = kmlDate_
        
        ## directories for HERMES Visualization
        self.KMZFileTempDir = './ge_viz'
        self.KMZFileName = 'GoogleEarthVizualization.kmz'
        self.KMZVizFileName = self.KMZFileTempDir + "/visualization.kml"
        self.KMZImageDir = self.KMZFileTempDir + "/images"
        
        self.supportedElements = [Folder,Placemark]

    def addElement(self,elem=None):
        supported = False
        for elementType in self.supportedElements:
            if isinstance(elem,elementType):
                supported = True
                
        if not supported:
            raise RuntimeError("Attempting to add a unsuppored element %s to KMLVisualization"%type(element))
        
        thisName = elem.name
        if elem.name in self.elementNames:
            count = 1
            while "%s #%d"%(elem.name,count) in self.elementNames:
                count+=1
            thisName = "%s #%d"%(elem.name,count)
        
        self.elements.append(elem)
        self.elementNames.append(thisName)
        
    def build(self):
        
        for storeID,store in self.shdNtwk.stores.items():
            self.vizStores[storeID] = KMLVizStore(storeID,self.shdNtwk,self.resultsID,self)
        
        for routeID,route in self.shdNtwk.routes.items():
            self.vizRoutes[routeID] = KMLVizRoute(routeID,self.shdNtwk,self.resultsID,self)
        
        #popFolder = Folder("Population",Id_="population_folder",visible_=True)
        #vaccFolder = Folder("Vaccines",Id_="vaccine_folder")
        utilFolder = Folder("Utilization",Id_="utilization_folder",opened_=True)
        #print "doing populations"
        #for storeId,store in self.vizStores.items():
        #    if store.kmlPopulationPlacemark() is not None:
        #        popFolder.addElement(store.kmlPopulationPlacemark(visibility=True))
        
#                if store.kmlVaccineAvailPlacemark() is not None:
#                    vaccFolder.addElement(store.kmlVaccineAvailPlacemark())
        #print "Vaccine Names " + str(self.vaccineNames)       
        #for vaccine,vaccineName in self.vaccineNames:
        #    vaccineFolder = Folder("%s"%vaccineName,Id_="vaccine_%s_folder"%vaccineName)
        #    for storeId,store in self.vizStores.items():
        #        if store.kmlVaccineAvailPlacemark(vaccine) is not None:
        #            print "Vaccine not None"
        #            vaccineFolder.addElement(store.kmlVaccineAvailPlacemark(vaccine))
        #    vaccFolder.addElement(vaccineFolder)
        
        for level in ['State']:#self.levels:
            levelFolder = Folder("%s"%level,Id_="utilization_%s_folder"%level)
            for storeId,store in self.vizStores.items():
                if store.level == level:
                    if store.kmlUtilizationPlacemark() is not None:
                        levelFolder.addElement(store.kmlUtilizationPlacemark())
            if len(levelFolder.elements) > 0:
                utilFolder.addElement(levelFolder)
        
        #routeFolder = Folder("Routes")
        #for routeId,route in self.vizRoutes.items():
        #    if route.visualize is True:
        #        if route.kmlRouteLinePlacemark() is not None:
        #            routeFolder.addElement(route.kmlRouteLinePlacemark(visibility=True))
        
        #self.addElement(routeFolder)            
        #self.addElement(popFolder)
        #self.addElement(vaccFolder)
        self.addElement(utilFolder)

    def output(self,removeFiles = True):
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
            f.write('<open>1</open>')
            f.write(self.createStyles("-1","-1",self.numberOfColors,"")) 
            
            for elem in self.elements:
                f.write(elem.kmlString(pretty=True))
            
            f.write("</Document></kml>")
        
        #Move appropriate Image Files
        imgTmpList = os.listdir(self.imageTmpDir)
        for img in imgTmpList:
            shutil.move(self.imageTmpDir+"/"+img,self.KMZImageDir)
        
#        stockList = os.listdir('./stockPlots')
#        for stockPlot in stockList:     
#            shutil.move('./stockPlots/'+stockPlot,self.KMZImageDir)
        
        zipper(self.KMZFileTempDir,self.KMZFileName)
        if removeFiles:
            shutil.rmtree(self.imageTmpDir)
            shutil.rmtree('stockPlots')
            shutil.rmtree(self.KMZFileTempDir)
        
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

class KMLVizStore(viz.VizStore):
    def __init__(self,storeID_,shdNtwk_=None, resultsID_=None, visualizationInfo_=None,sim_=None):  
        if not isinstance(visualizationInfo_,KMLVisualization):
            raise RuntimeError("Trying to create a KMLVizStore with an improper visualizationInfo")
        
        viz.VizStore.__init__(self,storeID_,shdNtwk_,resultsID_,visualizationInfo_,sim_)
        
    
    def createDeviceListingTable(self,title="Storage Devices"):
        devTable = htmlTable("Device Table for %s"%str(self.iD),title)
        devTable.addRow(["Device Name","Count","2-8 C Net Storage (L)", "Below 0 C Storage(L)"],
                        ['b',1,1,1,1])
        for devRec in self.inventoryList:
            devTable.addRow([devRec['name'],"%d"%devRec['count'],
                             "%.2f"%devRec['volumes']['cooler'],
                             "%.2f"%devRec['volumes']['freezer']],
                            ['b',1,1,1,1])
        
        return devTable
    
    def createTransportDeviceListingTable(self,title="Vehicle Information"):
        devTable = htmlTable("Vehicle Table for %s"%str(self.iD),title) 
        devTable.addRow(["Vehicle","Count",
                         "2-8 C Net Storage (L)",
                         "Below 0 C Storage(L)"],
                         ['b',1,1,1,1])
        for devRec in self.transportList:
            devTable.addRow([devRec['name'],
                             "%d"%devRec['count'],
                             "%.2f"%devRec['volumes']['cooler'],
                             "%.2f"%devRec['volumes']['freezer']],
                             ['b',1,1,1,1])
        
        return devTable
    
    def createVaccineAdminListingTable(self, vDataDict, vaPlotFilename,title="Vaccine Data"):
        vacTable = htmlTable("Vaccine Availability for %s"%str(self.iD),title)
        
        if vDataDict['allvax']['patients'] == 0.0:
            vacTable.addRow(['No Vaccines Distributed at this Location'],['b',4])
        else:
            vacTable.addRow(['<img src="%s" width = "400px"></img>'%vaPlotFilename],
                            ["b",4])
            vacTable.addRow(['Vaccine',
                             'Doses Demanded',
                             'Doses Administered',
                             'Vaccine Availability'],
                             ['n',1,1,1,1])
            
            for vaccineName in sorted(vDataDict.keys()):
                if vaccineName == "allvax":
                    continue
                
                dataDict = vDataDict[vaccineName]
                vacTable.addRow([dataDict['displayName'],
                                 "%d"%dataDict['patients'],
                                 "%d"%dataDict['treated'],
                                 "%.2f%%"%(dataDict['availability']*100.0)],
                                 ["b",1,1,1,1])
            vacTable.addRow(['All Vaccines',
                             "%d"%vDataDict['allvax']['patients'],
                             "%d"%vDataDict['allvax']['treated'],
                             "%.2f%%"%(vDataDict['allvax']['availability']*100.0)],
                             ["n",1,1,1,1])
        return vacTable
    def createInfoTable(self,title="General Information"):
        genTable = htmlTable("General Info for %s"%self.iD,title)
        genTable.addRow(["ID:",str(self.iD)],["b",1,3])
        genTable.addRow(["Level:",str(self.parsedLevel)],["b",1,3])
        
        return genTable
    
    def createStorageFillTable(self,title="Storage Information"):
        storTable = htmlTable("Storage Fill for %s"%str(self.iD),title)
        
        ### Stock Plot
        #imgfileName = str(self.iD) + "_all_storage_curve.png"
        
        #imgfileName = "storagePlot_" + str(self.iD) + ".png"
        
        storTable.addRow(['Stock Over Time (Vials)'],['n',4])
        storTable.addRow(['<div id="%s"></div>\n<script>%s</script>'\
                          %("storagePlot_%d"%self.iD,self.storeHCString)],['b',4])
        
        #storTable.addRow(['<img width="400px" src="images/%s"></img>'%imgfileName],
        #                ['b',4])
        
        storTable.addRow(['Storage Information'],['m',4])
        storTable.addRow(['Refrigerator (2-8 C) Storage'],['b',4])
        storTable.addRow(['<pre>     </pre>',
                          'Total Volume (L)',
                          "%.2f"%self.storageFillDict['cooler']['volume_avail']],
                         ['b',1,2,1])
        storTable.addRow(['','Max Volume Used (L)',
                          "%.2f"%self.storageFillDict['cooler']['max_volume_used']],
                          ['b',1,2,1])
        storTable.addRow(['','Max Utilization',
                          "%.2f%%"%self.storageFillDict['cooler']['max_percent_used']],
                          ['b',1,2,1])
        
        if self.storageFillDict['freezer']['volume_avail'] > 0.0:
            storTable.addRow(['Freezer (below 0 C) Storage'],['b',4])
            storTable.addRow([' ',
                              'Total Volume (L)',
                              self.storageFillDict['freezer']['volume_avail']],
                              ['b',1,2,1])
            storTable.addRow([' ',
                              'Max Volume Used (L)',
                              "%.2f"%self.storageFillDict['freezer']['max_volume_used']],
                              ['b',1,2,1])
            storTable.addRow([' ',
                              'Max Utilization',
                              "%.2f%%"%self.storageFillDict['freezer']['max_percent_used']],
                              ['b',1,2,1])
        return storTable
      
### Graph Creators
    def createPopulationListingTable(self, pDataDict,title="Population Information"):
        popTable = htmlTable("Population Info for %s"%self.iD, title)
        if pDataDict['all']['count'] == 0:
            popTable.addRow(["No Population Vaccinated at this Location"],["b",4])
        else:
            popTable.addRow(["Population Class","Yearly Catchment Size"],
                            ["n",3,1])
            for peopleKey in sorted(pDataDict.keys()):
                if peopleKey != "all":
                    print str(pDataDict)
                    popTable.addRow([pDataDict[peopleKey]['displayName'],
                                     "%d"%pDataDict[peopleKey]['count']],
                                    ["b",3,1])
        return popTable
    
### KML String Creators
    def kmlUtilizationInfoDescription(self):
        if self.isAttached:
            return None
        if self.isOutreach:
            return None
        
        descBubble = DescriptionBubble(self.visualizationInfo.majorColor,
                                           self.visualizationInfo.minorColor,
                                           600,"Utilization")
        descBubble.addTable(self.createInfoTable())
        descBubble.addTable(self.createStorageFillTable())
        if self.hasStorageDevices is True:
            descBubble.addTable(self.createDeviceListingTable())
        if self.hasTransportVehicles is True:
            descBubble.addTable(self.createTransportDeviceListingTable())
        
        return descBubble
        
    def kmlUtilizationPlacemark(self,storeType = "cooler",visibility=False):
        if self.isAttached:
            return None
        if self.isOutreach:
            return None
        
        kmlList = []
        maxFill = self.storageFillDict[storeType]['max_percent_used']/100.0
        height = int(maxFill*self.visualizationInfo.columnHeight)
        #print "Height = " + str(maxFill) + " " + str(height)
        color = self.visualizationInfo.colorFromValue(maxFill)
        radius = self.visualizationInfo.levelRadDict[self.level][0]
        shape = self.visualizationInfo.levelRadDict[self.level][1]
        #print "shape = " + shape
        if shape == 's': shapeType = "square"
        elif shape=='c': shapeType = "circle"
        else: shapeType = "point"
        
        placemark = Placemark(name_=self.parsedName,
                                  type_=shapeType,
                                  Id_ = "util_%s_%s_%s"%(self.iD,
                                                    self.parsedName,
                                                    self.level),
                                  coordinates_=(self._shdNtwkStore.Longitude,
                                                self._shdNtwkStore.Latitude),
                                  extrude_=True,
                                  style_= 'style%d'%color,
                                  height_=height,
                                  radius_=radius,
                                  description_=self.kmlUtilizationInfoDescription(),
                                  visibility_=visibility)
        
        return placemark
    
    def kmlVaccineInfoDescription(self):
        if not self.hasVaccine:
            return None
        if self.isOutreach:
            return None
        
        descBubble = DescriptionBubble(self.visualizationInfo.majorColor,
                                           self.visualizationInfo.minorColor,
                                           600,"Vaccine")
        
        descBubble.addTable(self.createInfoTable())
        if self.hasVaccine:
            descBubble.addTable(self.createVaccineAdminListingTable(self.vaccineDataDict,self.vaccineAvailPlotFilename))
        if self.hasOutreachVaccine:
            descBubble.addTable(self.createVaccineAdminListingTable(self.outreachVaccineDataDict,
                                                               self.outreachVaccineAvailPlotFilename,
                                                               title = "Outreach Vaccine Information"))
                                    
        return descBubble
    
    def kmlVaccineAvailPlacemark(self,vaccineName='allvax',visibility=False):
        if not self.hasVaccine:
            return None
        if self.isAttached is True:
            return None
        if self.isOutreach is True:
            return None
        
        kmlList = []
        totalAvail = 0.0
        if self.totalVaccineDict.has_key(vaccineName):
            totalAvail = self.totalVaccineDict[vaccineName]['availability']
        radius = self.visualizationInfo.vaccineAvailRadius
        if totalAvail == 0.0:
            height = 100.0
        else:
            height = 100.0+(1.0/totalAvail)
        color = self.visualizationInfo.colorFromValue(1.0-totalAvail)
        
        placemark = Placemark(name_=self.parsedName,
                                  type_='circle',
                                  Id_ = "vac_%s_%s_%s"%(self.iD,
                                                    self.parsedName,
                                                    self.level),
                                  coordinates_=(self._shdNtwkStore.Longitude,
                                                self._shdNtwkStore.Latitude),
                                  extrude_=False,
                                  style_= 'styleva%d'%color,
                                  height_=height,
                                  radius_=radius,
                                  description_=self.kmlVaccineInfoDescription(),
                                  visibility_=visibility)
        return placemark
     
    def kmlPopulationDescription(self):
        if self.isAttached is True:
            return None
        if self.hasPopulation is False:
            return None
        if self.isOutreach is True:
            return None
        
        descBubble = DescriptionBubble(self.visualizationInfo.majorColor,
                                           self.visualizationInfo.minorColor,
                                           600,"Population")
        
        descBubble.addTable(self.createInfoTable())
        descBubble.addTable(self.createPopulationListingTable(self.peopleServedDict))
        if self.hasOutreach:
            descBubble.addTable(self.createPopulationListingTable(self.peopleOutreachDict,
                                                                  title="Outreach Population Information"))
        
        return descBubble
   
    def kmlPopulationPlacemark(self,visibility=False):
        kmlList = []
        if self.hasPopulation is False:
            return None
        if self.isAttached:
            return None
        if self.isOutreach:
            return None
        
        percentOfMax = float(self.totalPeopleServedDict['all']['count'])\
                        /float(self.visualizationInfo.maxPopulation)
        #print "PopStuff" + str(self.totalPeopleServedDict['all']) + " " + str(self.visualizationInfo.maxPopulation)
        radius = self.visualizationInfo.populationRadius*percentOfMax
        
        if radius > 0:
            height = 100.0*(0.1/radius) ##NOTE Variablize
        else:
            height = 10.0
            
        color = self.visualizationInfo.colorFromValue(percentOfMax)
        #print "color = " + str(color)
        placemark = Placemark(name_=self.parsedName,
                              type_='circle',
                              Id_ = "pop_%s_%s_%s"%(self.iD,
                                                    self.parsedName,
                                                    self.level),
                              coordinates_=(self._shdNtwkStore.Longitude,
                                            self._shdNtwkStore.Latitude),
                              extrude_=False,
                              style_= 'stylepop%d'%color,
                              height_=height,
                              radius_=radius,
                              description_=self.kmlPopulationDescription(),
                              visibility_=visibility)
        
        
        return placemark

class KMLVizRoute(viz.VizRoute):
    def __init__(self,routeID_,shdNtwk_,resultsID_,visualizationInfo_,sim_=None):
        if not isinstance(visualizationInfo_,KMLVisualization):
            raise RuntimeError("Trying to create a KMLVizRoute with an improper visualizationInfo")
        
        viz.VizRoute.__init__(self,routeID_,shdNtwk_,resultsID_,visualizationInfo_,sim_)
        
    def createRouteInfoTable(self):
        routeTab = htmlTable("RouteInfo for %s"%self.iD,"Route Information")
        
        routeTab.addRow(['Type:',str(self.parsedType)],['b',2,2])
        routeTab.addRow(['Levels:',str(self.parsedLevelName)],['b',2,2])
        routeTab.addRow(['<p></p>'],['b',4])
        routeTab.addRow(['Transport Information'],['m',4])
        routeTab.addRow(['Vehicle','2-8C Net Storage (L)',
                         'Maximum Utilization','Number of Trips'],
                        ['n',1,1,1,1])
        for vehicle in self.transportInfo:
            routeTab.addRow([vehicle['name'],"%.2f"%vehicle['volL'],
                             "%.2f%%"%(self.maximumFracFill*100.0),"%d"%self.numberOfTrips],
                            ['b',1,1,1,1])
        return routeTab
    
    def createTripManifestTable(self):
        manTab = htmlTable("Trip Manifest for %s"%self.iD,"Trip Manifest")
        
        manTab.addRow(['Segment','Time Start','Time Arrived','Vol Carried (L)'],
                      ['n',1,1,1,1])
        for trip in self.tripManifest:
            manTab.addRow(["%s to %s"%(trip['start'],trip['end']),
                                      self.visualizationInfo.kmlDate.getDateTimeInFuture(trip['tStart']),
                                      self.visualizationInfo.kmlDate.getDateTimeInFuture(trip['tEnd']),
                                      "%.2f"%trip['LitersCarried']],
                                      ['b',1,1,1,1])
            
        
        return manTab    
    
    def kmlRouteDescription(self):
        if self.visualize is False:
            return None
        
        descBubble= DescriptionBubble(self.visualizationInfo.majorColor,
                                           self.visualizationInfo.minorColor,
                                           600,"RouteInfo")
        descBubble.addTable(self.createRouteInfoTable())
        descBubble.addText(" ")
        descBubble.addTable(self.createTripManifestTable())
        
        return descBubble
    
    def kmlRouteLinePlacemark(self,visibility=False):
        if self.visualize is False:
            #print "Returning None"
            return None
        
        if self.maximumFracFill == 0:
            color = -1
        else:
            color = self.visualizationInfo.colorFromValue(self.maximumFracFill)
            
        placemark = Placemark(name_ = self.parsedName,
                              type_ = 'linestring',
                              Id_ = 'route_%s_%s_%s'%(self.iD,
                                                      self.parsedLevelName,
                                                      self.type),
                              coordinates_=self.latlonCoordinates,
                              extrude_ = False,
                              style_ = 'styletrans%d'%color,
                              height_=0.0,
                              radius_=0.0,
                              description_=self.kmlRouteDescription(),
                              visibility_=visibility)
        
        return placemark
                                                                                                                          
class KMLDate:
    """
    The KML Date class is intended to be used to return KML friendly date strings 
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
        
def circleString(center_x, center_y, radius, height, resolution, extrude = False, pretty = False):
    points = []
    pointStringList = []
    pointStringList.append('<Polygon>')
    pointStringList.append('<altitudeMode>relativeToGround</altitudeMode>')
    if extrude:
        pointStringList.append('<extrude>1</extrude>')
    pointStringList.append('<outerBoundaryIs><LinearRing><coordinates>')
    orgPoint=None
    for i in range(resolution, 0, -1):
        angle = (2 * math.pi / float(resolution)) * float(i)
        #print str(angle) + " " + str(center_x) + " " + str(center_y) + " " + str(radius)
        #print "Angles: " + str(math.sin(angle)) + " " + str(math.cos(angle))
        if i == resolution:
            orgPoint = (float(center_x) + float(radius)* math.sin(angle), float(center_y)+ float(radius) * math.cos(angle))
        pointStringList.append("%g,%g,%g "%(float(center_x) + radius * math.sin(angle), 
                                            float(center_y) + radius * math.cos(angle),
                                            height))
    pointStringList.append("%g,%g,%g "%(orgPoint[0],orgPoint[1],height))

    pointStringList.append("</coordinates></LinearRing></outerBoundaryIs></Polygon>")
    if pretty:
        return '\n'.join(pointStringList)
    else:
        return ''.join(pointStringList)

def squareString(center_x, center_y, length, height, extrude = False, pretty = False):
    points = []
    pointStringList = []
    pointStringList.append('<Polygon>')
    pointStringList.append('<altitudeMode>relativeToGround</altitudeMode>')
    if extrude:
        pointStringList.append('<extrude>1</extrude>')
    pointStringList.append('<outerBoundaryIs><LinearRing><coordinates>')
    x = length / math.sqrt(2.0)
    
    pointStringList.append("%g,%g,%g "%(center_x + x,center_y + x, height))
    pointStringList.append("%g,%g,%g "%(center_x - x,center_y + x, height))
    pointStringList.append("%g,%g,%g "%(center_x - x,center_y - x, height))
    pointStringList.append("%g,%g,%g "%(center_x + x,center_y - x, height))
    pointStringList.append("%g,%g,%g "%(center_x + x,center_y + x, height))
    pointStringList.append("</coordinates></LinearRing></outerBoundaryIs></Polygon>")
    if pretty:
        return '\n'.join(pointStringList)
    else:
        return ''.join(pointStringList) 

def pointString(center_x, center_y, height, extrude = False, pretty = False):
    pointStringList = []
    pointStringList.append('<Polygon>')
    pointStringList.append('<altitudeMode>relativeToGround</altitudeMode>')
    if extrude:
        pointStringList.append('<extrude>1</extrude>')
    pointStringList.append('<outerBoundaryIs><LinearRing><coordinates>')
    pointStringList.append('%g,%g,%g '%(center_x,center_y,height))
    pointStringList.append("</coordinates></LinearRing></outerBoundaryIs></Polygon>")
    if pretty:
        return '\n'.join(pointStringList)
    else:
        return ''.join(pointStringList)

def lineString(centers, height=0, extrude=False, pretty=False): 
    pointStringList = []
    pointStringList.append('<LineString>')
    pointStringList.append('<altitudeMode>clampToGround</altitudeMode>')
    if extrude:
        pointStringList.append('<extrude>1</extrude>')
    pointStringList.append('<coordinates>')
    for center in centers:
        pointStringList.append('%g,%g,%g '%(center[0],center[1],height))
        
    pointStringList.append('</coordinates>')
    pointStringList.append('</LineString>')
    
    if pretty:
        return '\n'.join(pointStringList)
    else:
        return ''.join(pointStringList)
    
class Style:
    def __init__(self,name_="style1",):
        pass
        
class Styles:
    def __init__(self,name_="styleSet"):
        pass
    
class Color:
    pass
         
class Folder:
    def __init__(self,name_="Folder",Id_="folder", opened_=False,visible_=False):
        
        self.name = name_
        self.id = Id_
        self.opened = opened_
        self.visible = visible_
        self.elements = []
        self.elementNames = []
        
    def addElement(self,elem=None):
        if elem is None:
            raise RuntimeError("Trying to add None to the element list of kml.Folder %s"%self.name)
        if not isinstance(elem,Folder) and not isinstance(elem,Placemark):
            raise RuntimeError("Trying to add an unsupported KML element %s to kml Folder %s"%(str(elem.type),self.name))
        
        thisName = elem.name
        if elem.name in self.elementNames:
            count = 1
            while "%s #%d"%(elem.name,count) in self.elementNames:
                count+=1
            thisName = "%s #%d"%(elem.name,count)
        
        self.elements.append(elem)
        self.elementNames.append(thisName)
        
    def kmlString(self,pretty=False):
        stringList = ["<Folder id='%s'>"%self.id]
        stringList.append("<name>%s</name>"%self.name)
        if self.opened:
            stringList.append("<open>1</open>")
        if self.visible:
            stringList.append("<visibility>1</visibility>")
            
        ### Now do all of the elements
        for elem in self.elements:
            stringList.append(elem.kmlString(pretty=pretty))
        
        stringList.append("</Folder>")
        
        if pretty:
            return '\n'.join(stringList)
        else:
            return ''.join(stringList)

class htmlTable:
    def __init__(self,name_="Table",title_="Title Goes Here"):

        self.nCols = 0
        self.nRows = 0
        self.name = name_
        self.title = title_
        
        self.data = []
        self.possibleFormats = ["m","n","c"] #Major, Minor, Clear
        self.rowFormats = []
        
    def addRow(self,rowList,rowFormats):
        if len(rowList)+1 != len(rowFormats):
            print "RowList: " + str(rowList)
            print "RowFormats: " + str(rowFormats)
            raise RuntimeError("In Table %s, incorrect list being passed to add row"%self.name)
        self.data.append(rowList)
        self.rowFormats.append(rowFormats) ## Add Checking for format
        ncols = sum(rowFormats[1:])
        if ncols > self.nCols:
            self.nCols = ncols
        
    def printHTML(self,majorColor,minorColor,width,border=1,pretty=False):
        #print "Rows = " + str(self.data)
        #print "RowForms = " + str(self.rowFormats)
        htmlList = ['<table style="width:%d;border-spacing:0;border-collapse:collapse;border:%dpx;">'%(width,border)]
        htmlList.append('<tr style="background:%s;color:%s">'%(majorColor,minorColor))
        htmlList.append('<td colspan="%d">%s</td>'%(self.nCols,self.title))
        htmlList.append('</tr>')
        for i in range(0,len(self.data)):
            row = self.data[i]
            rowFormat = self.rowFormats[i]
            rowStyle = rowFormat.pop(0)

            if rowStyle == 'm':
                htmlList.append('<tr style="background:%s;color:%s;">'%(majorColor,minorColor))
            elif rowStyle == 'n':
                htmlList.append('<tr style="background:%s;color:%s;">'%(minorColor,majorColor))
            else:
                htmlList.append('<tr>')
            
            for col in row:
                colspan = int(rowFormat.pop(0))
                strHere = '<td colspan="%d">'%colspan
                if isinstance(col,float):
                    strHere += '%.2f'%col
                elif isinstance(col,int):
                    strHere += '%d'%col
                else:
                    strHere += str(col)
                strHere += '</td>'    
                htmlList.append(strHere)
                    
            htmlList.append('</tr>')
        htmlList.append('</table>')
        
        if pretty:
            return '\n'.join(htmlList)
        else:
            return ''.join(htmlList)
                
class DescriptionBubble:
    def __init__(self,majorColor_= "black",minorColor_="yellow",width_=550,title_="Description"):
        self.majorColor = majorColor_
        self.minorColor = minorColor_
        self.width = width_
        self.title = title_
        self.finalized = False
        self.stringList = ["<description>"]
        self.tables = {}
        
    def addTable(self,table):
        #if name_ is None: name_ = "Table %d"%(len(self.tables)+1)
        thisName = table.name
        if self.tables.has_key(table.name):
            count = 1
            while self.tables.has_key("%s_%d"%(table.name,count)):
                count += 1
        
            thisName = "%s_%d"%(table.name,count)
        #print "This Name = %s"%thisName
        self.tables[thisName] = table
        self.stringList.append("<<TABLE>>%s"%thisName)
        #self.tables[name] = {'header':headers_,'data':[])}
    
    def addText(self,textString=""):
        self.stringList.append("<p>%s</p>"%str(textString))
    
    def kmlString(self,pretty=False):
        ### insert final element
        if self.finalized is False:
            self.stringList.append("</description>")
            self.finalized = True
        ## insert elements

        ##Tables
        for i in range(0,len(self.stringList)):
            txtString = self.stringList[i]
            #print txtString[0:9]
            if txtString[0:9] == "<<TABLE>>":
                self.stringList[i]=self.tables[txtString[9:]].printHTML(self.majorColor,
                                                                        self.minorColor,
                                                                        self.width,
                                                                        pretty=pretty)
        if pretty:
            return '\n'.join(self.stringList)
        return ''.join(self.stringList)
    
class Placemark:
    ### STB TO DO 
    ### Make Coordinates a separate class
    def __init__(self,name_="PlaceMark",Id_='placemark',type_="point",coordinates_=None,
                 extrude_ = False, style_=None, height_ = 1, radius_ = 1,
                 description_ = None, visibility_=False):
        self.name = name_
        self.id = Id_
        
        if type_ not in placemarkTypes:
            print ('Placemark type %s not supported, defaulting to point'%type_)
            self.type = 'point'
        else:
            self.type = type_
        
        self.points = None
        if coordinates_ is None:
            raise RuntimeError("Creating a Placemark without coordinates")
        #if not isinstance(coordinates_,tuple):
            #if self.type_ == "linestring":
            #    raise RuntimeError("Trying to assign coordinates to Line Placemark that is not a 4D Tuple")
            #else:
            #    if len(coordinates_) != 2:
            #        raise RuntimeError("Trying to assign coordinates that are not a 2D Tuple in Placemark")
        
        self.coordinates = coordinates_
            
        ## Placemark characteristics
        self.extrude = extrude_
        self.style = style_
        self.height = float(height_)
        self.radius = float(radius_)
        self.visibility = visibility_
        
        if description_ is not None:
            if not isinstance(description_,DescriptionBubble):
                raise RuntimeError("Trying to create a Placemark with a description that is not of the class DescriptionBubble")
        self.description = description_
        
    def kmlString(self, pretty = False):
        stringList = ['<Placemark id="%s">'%str(self.id)]
        stringList.append('<name>%s</name>'%self.name)
        
        if self.visibility: stringList.append('<visibility>1</visibility>')
        else: stringList.append('<visibility>0</visibility>')    
                                 
        if self.style:
            stringList.append('<styleUrl>#%s</styleUrl>'%self.style)
        
        if self.description:
            stringList.append(self.description.kmlString(pretty=pretty))
        
        if self.type == "point":
            stringList.append(pointString(self.coordinates[0],self.coordinates[1],
                                          self.height,self.extrude,pretty))
        elif self.type == "circle":
            #print str(self.height) + " " + str(self.coordinates[0]) + " " + str(self.coordinates[1])
            stringList.append(circleString(self.coordinates[0],self.coordinates[1],
                                           self.radius,self.height,20,self.extrude,
                                           pretty))
        elif self.type == "square":
            stringList.append(squareString(self.coordinates[0],self.coordinates[1],
                                           self.radius,self.height,self.extrude,pretty))
        
        elif self.type == "linestring":
            stringList.append(lineString(self.coordinates,
                                         self.height,self.extrude,pretty))
        stringList.append('</Placemark>')
        
        if pretty:
            return '\n'.join(stringList)
        else:
            return ''.join(stringList)
                        
def main():
    
    descBubble = DescriptionBubble("maroon","gold",600,"My Description")
    descBubble.addText("This is a description with a Table")
    test_table = htmlTable("Table")
    test_table.addRow(["This is a Table"],["m",5])
    test_table.addRow(["Stores","People","Vaccine","Vials","Trucks"],
                      ["n",1,1,1,1,1])
    test_table.addRow(["Warehouse","NewBorns","BCG","Hilux"],
                      ["b",1,1,2,1])
    descBubble.addTable(test_table)
    
    with open("testTab.html","wb") as f:
        f.write("<html><body>\n")
        f.write("%s"%descBubble.kmlString())
        f.write("</html>")
    
    
if __name__=="__main__":
    main()        
        
        
    
    
    
