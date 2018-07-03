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
from htmlHelper import HTMLTable

placemarkTypes = ["point","circle","square","line",'linestring']

class KMLVisualization(viz.Visualization):
    def __init__(self,shadow_network_db_=None, resultsID_=None,kmlDate_=None,
                 numberOfColors_=100,columnHeight_=100000,populationRadius_=0.2,
                 vaccineAvailRadius_=0.05,
                 title_=None):
        viz.Visualization.__init__(self,shadow_network_=shadow_network_db_._net,
                                   resultsID_=resultsID_,
                                   numberOfColors_=numberOfColors_,
                                   columnHeight_=columnHeight_,
                                   populationRadius_=populationRadius_,
                                   vaccineAvailRadius_=vaccineAvailRadius_,
                                   title_=title_)
        
        self.kmlDate = kmlDate_
        self.KMZVizFileName = 'visualization.kml'
        self.supportedElements = [Folder,Placemark]
        self.shdNtwkDB = shadow_network_db_
    def addElement(self,elem=None):
        supported = False
        for elementType in self.supportedElements:
            if isinstance(elem,elementType):
                supported = True
                
        if not supported:
            raise RuntimeError("Attempting to add a unsuppored element %s to KMLVisualization"%type(elem))
        
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
            kmlS = KMLVizStore(storeID,self.shdNtwk,self.resultsID,self)
            if kmlS.visualize:
                self.vizStores[storeID] = kmlS
        
        for routeID,route in self.shdNtwk.routes.items():
            kmlR = KMLVizRoute(routeID,self.shdNtwk,self.resultsID,self)
            if kmlR.visualize:
                self.vizRoutes[routeID] = kmlR
       
         
        popFolder = Folder("Population",Id_="population_folder",visible_=True)
        vaccFolder = Folder("Vaccines",Id_="vaccine_folder")
        utilFolder = Folder("Utilization",Id_="utilization_folder",opened_=True)
        routeFolder = Folder("Routes",Id_="route_folder")
        for storeId,store in self.vizStores.items():
            if store.kmlPopulationPlacemark() is not None:
                popFolder.addElement(store.kmlPopulationPlacemark(visibility=True))
        for storeId,store in self.vizStores.items():
            if store.kmlVaccineAvailPlacemark("allvax") is not None:
                vaccFolder.addElement(store.kmlVaccineAvailPlacemark('allvax'))
        for storeId,store in self.vizStores.items():
            if store.kmlUtilizationPlacemark() is not None:
                utilFolder.addElement(store.kmlUtilizationPlacemark())
        for routeId,route in self.vizRoutes.items():
            if route.kmlRouteLinePlacemark() is not None:
                routeFolder.addElement(route.kmlRouteLinePlacemark()) 
        self.addElement(popFolder)
        self.addElement(vaccFolder)
        self.addElement(utilFolder)
        self.addElement(routeFolder)

    def output(self,removeFiles = True):
        import session_support_wrapper as session_support
        import db_routines 
        
        ## Create the vizualization string
        stringList = ['<kml xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:'\
                           +'atom="http://www.w3.org/2005/Atom" xmlns="http://www.opengis.net/kml/2.2">'\
                           +'<Document>']
        if self.title:
            stringList.append('<name>'+self.title+'</name>')
        stringList.append(self.createStyles("-1","-1",self.numberOfColors,""))
        for elem in self.elements:
            stringList.append(elem.kmlString(pretty=False))
        
        
        stringList.append('</Document></kml>')
        
        packString = ''.join(stringList).replace('\n','')
        ### Get the results Group
        
        #resultsGToProc = self.shdNtwk.getResultsGroupByName(self.resultsGpId_)
        resultsSN = self.shdNtwk.getResultById(self.resultsID)
        resultsSN.setKmlVizString(packString)
       
        self.shdNtwkDB._dbSession.commit()
        
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
        stringList = ["var deviceData = ["]
        for devRec in self.inventoryList:
            stringList.append("{name: '%s', count: %d, fridge: %g, freezer: %g},"%\
                              (devRec['name'], devRec['count'],
                               devRec['volumes']['cooler'],
                               devRec['volumes']['freezer']))
        stringList.append("];")
        
        return ''.join(stringList)
    
    def createTransportDeviceListingTable(self,title="Vehicle Information"):
        stringList = ["var vehicleData = ["]
        for devRec in self.transportList:
            stringList.append("{name: '%s', count: %d, fridge: %g, freezer: %g},"%\
                              (devRec['name'], devRec['count'],
                               devRec['volumes']['cooler'],
                               devRec['volumes']['freezer']))
        stringList.append("];")
        
        return ''.join(stringList)
    
    def createVaccineAvailPlot(self):
        if self.isAttached:
            return "var vaccAvailPlotData = [];"
        if self.hasVaccine is False:
            return "var vaccAvailPlotData = [];"
        
        vDataDict = self.vaccineDataDict
        stringList = ["var vaccAvailPlotData = {'categories':["]
        
        for vaccineName,dataDict in vDataDict.items():
            if vaccineName != 'allvax':
                stringList.append("'%s',"%dataDict['displayName'])
        stringList.append("'%s'"%vDataDict['allvax']['displayName'])
        
        stringList.append("],'data':[")
        
        for vaccineName,dataDict in vDataDict.items():
            if vaccineName != 'allvax':
                stringList.append("%3.2f,"%(float(dataDict['availability'])*100.0))
        stringList.append("{y:%3.2f,color:'red'}"%(vDataDict['allvax']['availability']*100.0))
        
        stringList.append("]};")
        
        return ''.join(stringList)
        
        
    def createLinePlotForStorageVials(self):
        if self.isAttached:
            return "var plotData = [];"
        
        stringList = ["var plotData = ["]
        for i in range(0,len(self.volumeT)):
            stringList.append("[%g,%g],"%(self.volumeT[i],self.volumeF[i]))
        
        stringList[len(stringList)-1] = stringList[len(stringList)-1][:-1] + "];"
        
        return ''.join(stringList)
        
    def createVaccineAdminListingTable(self, vDataDict):# vaPlotFilename,title="Vaccine Data"):
        stringList = ["var allVacAvalData = ["]
        
        if vDataDict['allvax']['patients'] == 0.0:
            stringList.append('{name:"All Vaccines",patients:0,treated:0,avail:0.0)')
        else:
            for vaccineName in sorted(vDataDict.keys()):
                if vaccineName == "allvax":
                    continue
                dataDict = vDataDict[vaccineName]
                
                stringList.append('{name:"%s",patients:%d,treated:%d,avail:%3.2f},'\
                                  %(dataDict['displayName'],
                                    dataDict['patients'],
                                    dataDict['treated'],
                                    dataDict['availability']*100.0))
                
            stringList.append('{name:"All Vaccines",patients:%d,treated:%d,avail:%3.2f}'\
                              %(vDataDict['allvax']['patients'],
                                vDataDict['allvax']['treated'],
                                vDataDict['allvax']['availability']*100.0))
                                
        stringList.append('];') 
            
        return ''.join(stringList) 
    
    def createInfoTable(self,title="General Information"):
        stringList = ["var genInfoData = ["]
        stringList.append('{feature: "Name", value:"%s"},'%self.parsedName)
        stringList.append('{feature: "ID", value: "%s"},'%str(self.iD))
        stringList.append('{feature: "Level", value: "%s"},'%str(self.parsedLevel))
        stringList.append('{feature: "Latitude", value: %10.2f},'%self._shdNtwkStore.Latitude)
        stringList.append('{feature: "Longitude", value: %10.2f}'%(self._shdNtwkStore.Longitude))
        
        stringList.append('];')
        return ''.join(stringList)
    
    def createStorageFillTable(self,title="Storage Information"):
        stringList = ["var utilData = ["]
        stringList.append("{info: 'Refrigerator (2-8 C) Storage',"\
                            +"category:'Total Volume (L)',value:%10.2f},"\
                            %self.storageFillDict['cooler']['volume_avail'])
        
        stringList.append("{info: 'Refrigerator (2-8 C) Storage',"\
                          +"category:'Max Volume Used (L)',value:%10.2f},"\
                          %self.storageFillDict['cooler']['max_volume_used'])
        
        stringList.append("{info: 'Refrigerator (2-8 C) Storage',"\
                          "category:'Max Utilization %%',value:%4.2f},"\
                          %self.storageFillDict['cooler']['max_percent_used'])
        
        stringList.append("{info: 'Freezer (Below 2 C) Storage',"\
                            +"category:'Total Volume (L)',value:%10.2f},"\
                            %self.storageFillDict['freezer']['volume_avail'])
        
        stringList.append("{info: 'Freezer (Below 2 C) Storage',"\
                          +"category:'Max Volume Used (L)',value:%10.2f},"\
                          %self.storageFillDict['freezer']['max_volume_used'])
        
        stringList.append("{info: 'Freezer (Below 2 C) Storage',"\
                          "category:'Max Utilization %%',value:%4.2f}"\
                          %self.storageFillDict['freezer']['max_percent_used'])  
        
        stringList.append("];")
                  
        return ''.join(stringList)
    
### Graph Creators
    def createPopulationListingTable(self, pDataDict,title="Population Information"):
        
        stringList = ["var popInfoData = ["]
        
        if pDataDict['all']['count'] == 0:
            ### STB to fill in aggregated populations
            stringList.append('{class:%s,count:%d},'%("Total",0))
        else:
            for peopleKey in sorted(pDataDict.keys()):
                if peopleKey != "all":
                    stringList.append('{class:"%s",count:%d},'\
                                      %(pDataDict[peopleKey]['displayName'],
                                        pDataDict[peopleKey]['count']))
        
        stringList.append("];")
        
        return ''.join(stringList)
        
### KML String Creators
    def kmlUtilizationInfoDescription(self):
        if self.isAttached:
            return None
        if self.isOutreach:
            return None
        
        descBubble = DescriptionBubble(self.visualizationInfo.majorColor,
                                           self.visualizationInfo.minorColor,
                                           600,"Utilization")
        descBubble.addScript(self.createInfoTable())
        descBubble.addScript(self.createStorageFillTable())
        descBubble.addScript(self.createLinePlotForStorageVials())
        if self.hasStorageDevices is True:
            descBubble.addScript(self.createDeviceListingTable())
        else:
            descBubble.addScript("var deviceInfo = [];")
        if self.hasTransportVehicles is True:
            descBubble.addScript(self.createTransportDeviceListingTable())
        else:
            descBubble.addScript("var vehicleInfo = [];")
        
        htmlString = "<ul><li style='font-size:small'><a href='#tab-1'>Gen Info</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-2'>Vials Plot</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-3'>Utilization</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-4'>Devices</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-5'>Vehicles</a></li></ul>"\
                    + "<div id='tab-1'><table id='GenInfo'></table></div>"\
                    + "<div id='tab-2'><div id='VialsPlot'></div></div>"\
                    + "<div id='tab-3'><table id='Utilization'></table></div>"\
                    + "<div id='tab-4'><table id='Device'></table></div>"\
                    + "<div id='tab-5'><table id='Vehicles'></table></div>"
        descBubble.addText(htmlString)
        
        return descBubble
        
    def kmlUtilizationPlacemark(self,storeType = "cooler",visibility=False):
        if self.isAttached:
            return None
        if self.isOutreach:
            return None
        
        kmlList = []
        maxFill = self.storageFillDict[storeType]['max_percent_used']/100.0
        height = int(maxFill*self.visualizationInfo.columnHeight)
        color = self.visualizationInfo.colorFromValue(maxFill)
        radius = self.visualizationInfo.levelRadDict[self.level][0]
        shape = self.visualizationInfo.levelRadDict[self.level][1]
        
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
                                  description_= self.kmlUtilizationInfoDescription(),
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
        
        descBubble.addScript(self.createInfoTable())
        if self.hasVaccine:
            descBubble.addScript(self.createVaccineAdminListingTable(self.vaccineDataDict))
            descBubble.addScript(self.createVaccineAvailPlot())
        
        htmlString = "<ul><li style='font-size:small'><a href='#tab-1'>Gen Info</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-2'>Avail Plot</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-3'>Availability</a></li></ul>"\
                    + "<div id='tab-1'><table id='GenInfo'></table></div>"\
                    + "<div id='tab-2'><div id='AvailPlot'></div></div>"\
                    + "<div id='tab-3'><table id='Availability'></table></div>"
        
        descBubble.addText(htmlString)
        
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
            height = 1000.0
        else:
            height = 1000.0+(1.0/totalAvail)
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
        
        descBubble.addScript(self.createInfoTable())
        descBubble.addScript(self.createPopulationListingTable(self.peopleServedDict))
        #if self.hasOutreach:
        #    descBubble.addTable(self.createPopulationListingTable(self.peopleOutreachDict,
        #                                                          title="Outreach Population Information"))
        htmlString = "<ul><li style='font-size:small'><a href='#tab-1'>Gen Info</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-2'>Population</a></li></ul>"\
                    + "<div id='tab-1'><table id='GenInfo'></table></div>"\
                    + "<div id='tab-2'><table id='Population'></table></div>"
        
        descBubble.addText(htmlString)
        
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

        radius = self.visualizationInfo.populationRadius*percentOfMax
        
        if radius > 0:
            height = 1000.0*(0.1/radius) ##NOTE Variablize
        else:
            height = 100.0
            
        color = self.visualizationInfo.colorFromValue(percentOfMax)
        
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
        stringList = ['var routeInfoData = [']
        stringList.append('{feature: "Name",value: "%s"},'%self.parsedName)
        stringList.append('{feature: "ID",value: "%s"},'%str(self.iD))
        stringList.append('{feature: "Type",value: "%s"},'%str(self.parsedType))
        stringList.append('];')
        
        return ''.join(stringList)
    
    def createUtilizationInfoTable(self):
        stringList = ['var routeUtilInfoData = [']
        for vehicle in self.transportInfo:
            stringList.append('{name:"%s",storage:%10.2f,util:%3.2f,trips:%d},'\
                              %(vehicle['name'],
                                vehicle['volL'],
                                self.maximumFracFill*100.0,
                                self.numberOfTrips))
        stringList.append('];')
        
        return ''.join(stringList)
    
    
    def createTripManifestTable(self):
        stringList = ['var tripManifestInfo = [']
        
        
        for trip in self.tripManifest:
            stringList.append('{segment:"%s to %s",start:"%s",end:"%s",vol:%.2f},'\
                                %(trip['start'],trip['end'],
                                  self.visualizationInfo.kmlDate.getDateTimeInFuture(trip['tStart']),
                                  self.visualizationInfo.kmlDate.getDateTimeInFuture(trip['tEnd']), 
                                  trip['LitersCarried']))
        stringList.append('];')
        
        return ''.join(stringList)    
            
    def kmlRouteDescription(self):
        if self.visualize is False:
            return None
        
        descBubble= DescriptionBubble(self.visualizationInfo.majorColor,
                                           self.visualizationInfo.minorColor,
                                           600,"RouteInfo")
        descBubble.addScript(self.createRouteInfoTable())
        descBubble.addScript(self.createUtilizationInfoTable())
        descBubble.addScript(self.createTripManifestTable())
        
        htmlString = "<ul><li style='font-size:small'><a href='#tab-1'>Route Info</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-2'>Utilization</a></li>"\
                    + "<li style='font-size:small'><a href='#tab-3'>Trip Manifest</a></li></ul>"\
                    + "<div id='tab-1'><table id='RouteInfo'></table></div>"\
                    + "<div id='tab-2'><table id='RouteUtil'></table></div>"\
                    + "<div id='tab-3'><table id='RouteMan'></table></div>"
        
        descBubble.addText(htmlString)
        return descBubble
    
    def kmlRouteLinePlacemark(self,visibility=False):
        if self.visualize is False:
            return None
        
        if self.maximumFracFill == 0:
            color = -1
        else:
            color = self.visualizationInfo.colorFromValue(self.maximumFracFill)
            
        placemark = Placemark(name_ = self.parsedName,
                              type_ = 'linestring',
                              Id_ = 'route_%s'%(str(self.iD)),
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
        
class DescriptionBubble:
    def __init__(self,majorColor_= "black",minorColor_="yellow",width_=550,title_="Description"):
        self.majorColor = majorColor_
        self.minorColor = minorColor_
        self.width = width_
        self.title = title_
        self.finalized = False
        self.stringList = ["<description>"]
        self.tables = {}
        self.scripts = []
        
    def addTable(self,table):
        #if name_ is None: name_ = "Table %d"%(len(self.tables)+1)
        thisName = table.name
        if self.tables.has_key(table.name):
            count = 1
            while self.tables.has_key("%s_%d"%(table.name,count)):
                count += 1
        
            thisName = "%s_%d"%(table.name,count)
        self.tables[thisName] = table
        self.stringList.append("<<TABLE>>%s"%thisName)
        #self.tables[name] = {'header':headers_,'data':[])}
    
    def addText(self,textString=""):
        self.stringList.append("<p>%s</p>"%textString)

    def addScript(self,textString=""):
        self.scripts.append(textString)  
        #self.stringList.append("<<SCRIPT>>%d"%len(self.scripts)-1)
    
    def kmlString(self,pretty=False):
        ### insert final element
        if self.finalized is False:
            self.stringList.append("]]></description>")
            self.finalized = True
        ## insert elements
        ## prepend javascript after <description>
        scriptStringList = ["<script>"]
        scriptStringList.append(''.join(self.scripts))
        scriptStringList.append("</script>")
        self.stringList.insert(1,''.join(scriptStringList))
        
        ##Tables
        for i in range(0,len(self.stringList)):
            txtString = self.stringList[i]
            if txtString[0:9] == "<<TABLE>>":
                self.stringList[i]=self.tables[txtString[9:]].printHTML(self.majorColor,
                                                                        self.minorColor,
                                                                        self.width,
                                                                        pretty=pretty)
        
        ## Add CDATA Statements
        self.stringList.insert(1,'<![CDATA[')
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
    test_table = HTMLTable("Table")
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
        
        
    
    
    
