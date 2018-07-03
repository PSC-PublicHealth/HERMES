#!/usr/bin/env python
__doc__ = """ consolidate_places_in_level.py
This program takes a stores file, route file and a csv that describes places to be changed, and creates new stores and routes files executing the alterations.
"""


_hermes_svn_id_ = "$Id: consolidate_places_in_level.py 1053 2012-08-16 17:47:26Z stbrown $"

import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
import input
from copy import deepcopy
import sys
import optparse
import simplejson,urllib,time
import util

def getGoogleDirectionsDistanceLatLon(lat1,lng1,lat2,lng2):
    url = 'http://maps.googleapis.com/maps/api/directions/json?origin='+\
	  str(lat1)+','+str(lng1)+'&destination='+str(lat2)+','+str(lng2)+'&sensor=false'
    result = simplejson.load(urllib.urlopen(url))
    #print url
    #print result['status']
    if result['status'] != "OK":
	return -1.0
    else:
	return (float(result['routes'][0]['legs'][0]['distance']['value'])/1000.0,float(result['routes'][0]['legs'][0]['duration']['value'])/3600.0)

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-d db_id]
    """)
    parser.add_option("-i", "--inputfile", default=None)
    parser.add_option("-p", "--popfile", default=None)
    # parser.add_option("-d","--use_db",type=int,default=None)
    opts, args = parser.parse_args()
    
    return (opts, args)

if __name__ == '__main__':
    import csv_tools
    import math
    
    
    opts, args = parseCommandLine()
        
    userInput = input.UserInput(opts.inputfile, False)
    shdTypes = shadow_network.loadShdTypes(userInput, input.UnifiedInput())
    shdNtwk = shadow_network.loadShdNetwork(userInput, shdTypes, "Kerala_dist")

#     ### add a new inventory type for InfStorage
#     newStoreType = { 
#                     'Name':'I_InfStorage',
#                     'DisplayName':'Infinite Storage Placeholder',
#                     'cooler':231435435134355134355,
#                     'freezer':43541345135151513334,
#                     }
#     
    
    inputDict={}
    with open(opts.popfile,"rb") as f:
        keyList,recList = csv_tools.parseCSV(f)
        for rec in recList:
            inputDict[rec['District']] = {}
            for key in keyList:
                inputDict[rec['District']][key] = rec[key]
    
    newDistrictCode = 10          
    for dKey,distRec in inputDict.items():
        newDistrictCode += 1
        newName = dKey + " District"
        newCategory = "District"
        newInterval = None
        
        divisionToAttch = distRec['HERMES DIV ID']
        
        thisDistTemp = { 'idcode':newDistrictCode,
                         'NAME':newName,
                         'CATEGORY':newCategory,
                         'FUNCTION':'Distribution',
                         'Device Utilization Rate':1.0,
                         'UseVialsLatency':3,
                         'UseVialsInterval':1,
                         'Latitude':distRec['LAT'],
                         'Longitude':distRec['Lon'],
                         'Inventory':'I_InfStorage+I_InfTransport',
                         'Notes':'Added Automatically'
                         #'Newborn':rec['Newborn']
                         }
        for key in shdNtwk.people.keys():
            thisDistTemp[key] = 0
        
        thisDistAttch = {
            'idcode':newDistrictCode+100,
            'NAME':newName + "_att",
            'CATEGORY':newCategory,
            'FUNCTION':'Surrogate',
            'Device Utilization Rate':1.0,
            'UseVialsLatency':3,
            'UseVialsInterval':20,
            'Latitude':rec['LAT'],
            'Longitude':rec['Lon'],
            'Inventory':'',
            'Notes':'Added Automatically'
            #'Newborn':rec['Newborn']
            }
        for key,value in distRec.items():
            if key in shdNtwk.people.keys():
                thisDistAttch[key] = value
        
        originStore = shdNtwk.getStore(divisionToAttch)
        print "LonLats = %10.10f %10.10f: %10.10f %10.10f"%(originStore.Latitude,originStore.Longitude,
                                                                    distRec['LAT'],distRec['Lon'])
        distanceGM,timeGM = util.getGoogleDirectionsDistanceLatLon(originStore.Latitude,originStore.Longitude,
                                                                    distRec['LAT'],distRec['Lon'])
        
        print "Google Distance = " + str(distanceGM) + " " + str(timeGM)
        ### Get the distance from Google
        time.sleep(1.5)
        thisVarTemp = [
            {
               'RouteName': "d_" + str(newDistrictCode), 
                        'Type':'schedvarfetch',
                        'LocName':newName,
                        'idcode':newDistrictCode,
                        'RouteOrder':0,
                        'TransitHours':timeGM,
                        'ShipIntervalDays':'60',
                        'ShipLatencyDays':'2',
                        'PullOrderAmount':'',
                        'Notes':'',
                        'Conditions':'',
                        'TruckType':'I_InfTransport',
                        'DistanceKM':distanceGM},
            {
                        
                        'Type':'schedvarfetch',
                        'LocName':originStore.NAME,
                        'idcode':originStore.idcode,
                        'RouteOrder':1,
                        'TransitHours':timeGM,
                        'ShipIntervalDays':'60',
                        'ShipLatencyDays':'2',
                        'PullOrderAmount':'',
                        'Notes':'',
                        'Conditions':'',
                        'TruckType':'I_InfTransport',
                        'DistanceKM':distanceGM}
                        ]
        thisAttTemp = [{
                        'RouteName': "e_" + str(newDistrictCode) + "_att",
                        'Type':'attached',
                        'LocName':newName,
                        'idcode':newDistrictCode,
                        'RouteOrder':0,
                        'TransitHours':'0',
                        'ShipIntervalDays':'',
                        'ShipLatencyDays':'',
                        'PullOrderAmount':'',
                        'Notes':'',
                        'Conditions':'',
                        'TruckType':''},
                        {
                        'Type':'attached',
                        'LocName':newName,
                        'idcode':newDistrictCode+100,
                        'RouteOrder':1,
                        'TransitHours':'0',
                        'ShipIntervalDays':'',
                        'ShipLatencyDays':'',
                        'PullOrderAmount':'',
                        'Notes':'',
                        'Conditions':'',
                        'TruckType':''}]
        print "Adding Store %s"%str(newDistrictCode)
        shdNtwk.addStore(thisDistTemp)
        shdNtwk.addStore(thisDistAttch)
        shdNtwk.addRoute(thisVarTemp)
        shdNtwk.addRoute(thisAttTemp)
    shdNtwk.writeCSVRepresentation()
        
