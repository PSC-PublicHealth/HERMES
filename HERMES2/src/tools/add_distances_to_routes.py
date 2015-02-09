#!/usr/bin/env python
__doc__=""" add_distances_to_routefile.py
A program that calculates the straight line from a route table, scales them based on
sL to road distance factors, and then computes the transit times.  This program produces a new
routes csv
"""

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

_hermes_svn_id_="$Id: add_distances_to_routefile.py 1053 2012-08-16 17:47:26Z stbrown $"


import sys
import simplejson,urllib
try:
    from util import longitudeLatitudeSep,AccumVal
except:
    raise RuntimeError("Cannot import HERMES utilities.  PYTHONPATH environment variable must be set"\
                       "to include your HERMES main directory in order to use this tool")

import csv_tools
import time
import pickle
import optparse
import math

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][--storefile][--routefile][--outputprefix][--gmdelay]
    """)
    parser.add_option("-s","--storefile",help="HERMES store file you wish to process")
    parser.add_option("-r","--routefile",help="HERMES route file you wish to process")
    parser.add_option("-d","--distscalefile",help="The CSV that describes the scaling factors between two levels")

    opts,args=parser.parse_args()

    return {'storefile':opts.storefile,'routefile':opts.routefile,
            'distscalefile':opts.distscalefile}

if __name__ == '__main__':

    inputDict = parseCommandLine()
    storeFile = inputDict['storefile']
    routeFile = inputDict['routefile']
    outputCSV = inputDict['routefile'][:-4] + '.withdists.csv'
    scalingCSV = inputDict['distscalefile']
    
    storeDict = {}
    routeDict = {}
    scalingMatrix = {}
    speedOfVehicle = {}
    hoursCanTravel = {}
    with open(scalingCSV,"rb") as f:
        keylist,reclist = csv_tools.parseCSV(f)
        for rec in reclist:
            scalingMatrix[rec['Level1'] + "-" + rec['Level2']] = rec['ScalingFactor']
            speedOfVehicle[rec['Level1'] + "-" + rec['Level2']] = rec['VehicleSpeedKMPH']
            hoursCanTravel[rec['Level1'] + "-" + rec['Level2']] = rec['HoursCanTravel']
            
            
    ## scalingMatrix = {"Commune-Department":1.47,"HealthPost-Commune":1.50,
    ##                  "Central-Department":1.29,"Department-Department":1.29,
    ##                  "Department-Commune":1.47,"Commune-HealthPost":1.50,
    ##                  "Department-Central":1.29}

    ## speedOfVehicle = {"Commune-Department":60,"HealthPost-Commune":50,
    ##                  "Central-Department":60,"Department-Department":60,
    ##                  "Department-Commune":60,"Commune-HealthPost":50,
    ##                  "Department-Central":60}

    #hoursOfDay = 8
    
    with open(storeFile,"rb") as f:
	keylist,reclist = csv_tools.parseCSV(f)
	for rec in reclist:
	    address = ""
	    storeDict[str(rec['idcode'])] = {'latitude':float(rec['Latitude']),
                                             'longitude':float(rec['Longitude']),
                                             'category':rec['CATEGORY'],'name':rec['NAME'],
                                             'function':rec['FUNCTION']}


    newRouteFile = open(outputCSV,"wb")

    keylist = []
    reclist = []
    
    with open(routeFile,"rb") as f:
	keylist,reclist = csv_tools.parseCSV(f)
        headString = ""
        for key in keylist:
            headString += str(key) + ","
        headString = headString + "DistanceKM" + "\n"

        newRouteFile.write("%s"%headString)
        
    ### Want to ensure that the route segments are ordered

	routeSegs = {}
	for rec in reclist:
            if not routeSegs.has_key(rec['RouteName']):
                routeSegs[rec['RouteName']] = 1
            else:
                routeSegs[rec['RouteName']] += 1

	for rec in reclist:
            if not routeDict.has_key(rec['RouteName']):
                routeDict[rec['RouteName']] = []
                for i in range(0,routeSegs[rec['RouteName']]):
                    routeDict[rec['RouteName']].append({})
            for key in rec.keys():
                routeDict[rec['RouteName']][int(rec['RouteOrder'])][str(key)] = rec[key]
                
            routeDict[rec['RouteName']][int(rec['RouteOrder'])]['category'] = ""
            routeDict[rec['RouteName']][int(rec['RouteOrder'])]['distanceKM'] = 0.0


        for routeKey in routeDict.keys():
            route = routeDict[routeKey]
            for i in range(0,len(route)):
                routeSeg = route[i]
                #print "Route Seg(" + routeKey + "," + str(i) + ")" + str(routeSeg)
                sys.stdout.flush()
                if routeSeg['Type'] == 'attached':
                    distanceSL = 0.0
                else:
                    fromWH = str(route[i]['idcode'])
                ### Get the toWH for Segment
                    if i == len(route)-1:
                        toWH = str(route[0]['idcode'])
                    else:
                        toWH = str(route[i+1]['idcode'])

                    distanceSL = longitudeLatitudeSep(storeDict[fromWH]['longitude'],
                                                      storeDict[fromWH]['latitude'],
                                                      storeDict[toWH]['longitude'],
                                                      storeDict[toWH]['latitude'])
                

                cat = storeDict[fromWH]['category'] + "-" + storeDict[toWH]['category']
                scale = float(scalingMatrix[cat])
                speed = float(speedOfVehicle[cat])
                hoursOfDay = float(hoursCanTravel[cat])
                
                distanceKM = distanceSL*scale
                routeSeg['distanceKM'] = distanceKM

                ## Compute the time travelled
               

                timeTraveledSeg = distanceKM/speed
                previousDist = 0.0
                previousTime = 0.0
                if i != 0:
                    for j in range(0,i):
                        previousDist += float(route[j]['distanceKM'])
                        previousTime += float(route[j]['TransitHours'])
                timeTraveledFull = (previousDist+distanceKM)/speed
                timeTraveledFull += math.floor(timeTraveledFull/hoursOfDay)*(24.0-hoursOfDay)    
                timeTraveled = timeTraveledFull - previousTime
                if timeTraveled == 0.0 or math.fabs(timeTraveled) < 0.0001:
                    timeTraveled = 0.00001
                routeSeg['TransitHours'] = timeTraveled
                

        routeKeyList = []
        for routeKey in routeDict.keys():
            routeKeyList.append(routeKey)

        routeKeyList.sort()

        for rkey in routeKeyList:
            route = routeDict[rkey]
            for i in range(0,len(route)):
                routeSeg = route[i]
                lineStr = ""
                for key in keylist:
                    lineStr += str(routeSeg[key])+","

                lineStr += str(routeSeg['distanceKM'])

                newRouteFile.write("%s\n"%lineStr)

        newRouteFile.close()
                


               
    

        
                          


			    
	
