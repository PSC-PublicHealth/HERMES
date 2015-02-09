#!/usr/bin/env python
__doc__=""" calculate_route_distances.py
A program that calculates the straight line and google road distances
for all of the route in a HERMES model
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

_hermes_svn_id_="$Id: calculate_route_distances.py 1053 2012-08-16 17:47:26Z stbrown $"


import sys

try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    # also need the directory above
    updir = os.path.join(cwd, '..')
    if updir not in sys.path:
        sys.path.append(updir)
except:
    pass

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

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][--storefile][--routefile][--outputprefix][--gmdelay]
    """)
    parser.add_option("-s","--storefile",help="HERMES store file you wish to process")
    parser.add_option("-r","--routefile",help="HERMES route file you wish to process")
    parser.add_option("-o","--outputprefix",help="Output file name prefix",default='Distances')
    parser.add_option("-g","--gmdelay",type="float",help="Delay between Google Map web service calls",
                      default=1.5)

    opts,args=parser.parse_args()

    return {'storefile':opts.storefile,'routefile':opts.routefile,
            'outprefix':opts.outputprefix,'gmdelay':opts.gmdelay}

def getGoogleDirectionsDistance(origin, destination):
    url = 'http://maps.googleapis.com/maps/api/directions/json?origin="'+\
	  origin + '"&destination="'+ destination + '"&sensor=false'
    result = simplejson.load(urllib.urlopen(url))
    print url
    print result['status']
    if result['status'] != "OK":
	return -1.0
    else:
	return float(result['routes'][0]['legs'][0]['distance']['value'])/1000.0

def getGoogleDirectionsDistanceLatLon(lat1,lng1,lat2,lng2):
    url = 'http://maps.googleapis.com/maps/api/directions/json?origin='+\
	  str(lat1)+','+str(lng1)+'&destination='+str(lat2)+','+str(lng2)+'&sensor=false'
    result = simplejson.load(urllib.urlopen(url))
    #print url
    #print result['status']
    if result['status'] != "OK":
	return -1.0
    else:
	return float(result['routes'][0]['legs'][0]['distance']['value'])/1000.0

if __name__ == '__main__':

    inputDict = parseCommandLine()
    #storeFile = "NigerStoreInfo_REALITY_2015_NewPopModel.csv"
    #routeFile = "NigerRoutes.csv"
    #storePKL = "NigerStore.pkl"
    #routePKL = "NigerRoutes.pkl"
    #storeFile = "BeninStoreInfo_2012.latlon.8.27.9.48.csv"
    storeFile = inputDict['storefile']
    routeFile = inputDict['routefile']
    storePKL = inputDict['outprefix']+ '.Store.pkl'
    routePKL = inputDict['outprefix']+ '.Route.pkl'
    outputCSV = inputDict['outprefix']+ '.distances.csv'
    outputStatCSV = inputDict['outprefix'] + '.stats.csv'
    
    storeDict = {}
    routeDict = {}

    with open(storeFile,"rb") as f:
	keylist,reclist = csv_tools.parseCSV(f)
	for rec in reclist:
	    address = ""
	    storeDict[str(rec['idcode'])] = {'latitude':float(rec['Latitude']),
                                             'longitude':float(rec['Longitude']),
                                             'category':rec['CATEGORY'],'name':rec['NAME'],
                                             'function':rec['FUNCTION']}



    pickle.dump(storeDict,open(storePKL,"wb"))

    with open(routeFile,"rb") as f:
	keylist,reclist = csv_tools.parseCSV(f)

    ### Want to ensure that the route segments are ordered
	routeSegs = {}
	for rec in reclist:
            if rec['Type'] != 'attached':
                if not routeSegs.has_key(rec['RouteName']):
                    routeSegs[rec['RouteName']] = 1
                else:
                    routeSegs[rec['RouteName']] += 1

	for rec in reclist:
            if rec['Type'] != "attached":
                if not routeDict.has_key(rec['RouteName']):
                    routeDict[rec['RouteName']] = []
                    for i in range(0,routeSegs[rec['RouteName']]):
                        routeDict[rec['RouteName']].append(0)
                routeDict[rec['RouteName']][int(rec['RouteOrder'])] = {'idcode':rec['idcode'],
                                                                       'category':"",
                                                                       'distanceGM':0.0,
                                                                       'distanceSL':0.0}
    with open(outputCSV,"wb") as f:
        f.write("RouteName,RouteOrder,CATEGORY,FromID,ToID,FromLat,FromLon,ToLat,ToLon,GoogleDist,SLDist\n")
        for routeKey in routeDict.keys():
            route = routeDict[routeKey]
            print "Computing Distances for Route: " + str(routeKey)

            if len(route) == 2:
                fromWH = str(route[0]['idcode'])
                toWH = str(route[1]['idcode'])
                distanceGM = getGoogleDirectionsDistanceLatLon(storeDict[fromWH]['latitude'],
                                                               storeDict[fromWH]['longitude'],
                                                               storeDict[toWH]['latitude'],
                                                               storeDict[toWH]['longitude'])
                ## This is here to prevent GoogleMap API from overloading
                time.sleep(1.5)

                distanceSL = longitudeLatitudeSep(storeDict[fromWH]['longitude'],
                                                storeDict[fromWH]['latitude'],
                                                storeDict[toWH]['longitude'],
                                                storeDict[toWH]['latitude'])
                route[0]['distanceGM'] = distanceGM
                route[1]['distanceGM'] = distanceGM
                route[0]['distanceSL'] = distanceSL
                route[1]['distanceSL'] = distanceSL
                route[0]['category'] = storeDict[fromWH]['category'] + "-" +\
                                       storeDict[toWH]['category']
                route[1]['category'] = storeDict[toWH]['category'] + "-" +\
                                       storeDict[fromWH]['category']

                f.write("%s,%d,%s,%s,%s,%10.10f,"\
                      "%10.10f,%10.10f,%10.10f,%10.10f,%10.10lf\n"%(routeKey,
                                                                    0,
                                                                    route[0]['category'],
                                                                    fromWH,
                                                                    toWH,
                                                                    storeDict[fromWH]['latitude'],
                                                                    storeDict[fromWH]['longitude'],
                                                                    storeDict[toWH]['latitude'],
                                                                    storeDict[toWH]['longitude'],
                                                                    distanceGM,distanceSL))
                f.write("%s,%d,%s,%s,%s,%10.10f,"\
                        "%10.10f,%10.10f,%10.10f,%10.10f,%10.10lf\n"%(routeKey,
                                                                      1,
                                                                      route[1]['category'],
                                                                      toWH,
                                                                      fromWH,
                                                                      storeDict[toWH]['latitude'],
                                                                      storeDict[toWH]['longitude'],
                                                                      storeDict[fromWH]['latitude'],
                                                                      storeDict[fromWH]['longitude'],
                                                                      distanceGM,distanceSL))
                f.flush()

            else:    
                for i in range(0,len(route)):
                    fromWH = str(route[i]['idcode'])
                    ### Get the toWH for Segment
                    if i == len(route)-1:
                        toWH = str(route[0]['idcode'])
                    else:
                        toWH = str(route[i+1]['idcode'])

                    distanceGM = getGoogleDirectionsDistanceLatLon(storeDict[fromWH]['latitude'],
                                                                   storeDict[fromWH]['longitude'],
                                                                   storeDict[toWH]['latitude'],
                                                                   storeDict[toWH]['longitude'])
                    #This is here to prevent Google Earth from overloading
                    time.sleep(1.5)

                    distanceSL = longitudeLatitudeSep(storeDict[fromWH]['longitude'],
                                                      storeDict[fromWH]['latitude'],
                                                      storeDict[toWH]['longitude'],
                                                      storeDict[toWH]['latitude'])

                    route[i]['distanceGM'] = distanceGM
                    route[i]['distanceSL'] = distanceSL
                    route[i]['category'] = storeDict[fromWH]['category'] + "-" +\
                                           storeDict[toWH]['category']
                    
		f.write("%s,%d,,%s,%s,%s,%10.10f,%10.10f,"\
                      "%10.10f,%10.10f,%10.10f,%10.10lf\n"%(routeKey,
                                                            i,
                                                            route[i]['category'],
                                                            fromWH,
                                                            toWH,
                                                            storeDict[fromWH]['latitude'],
                                                            storeDict[fromWH]['longitude'],
                                                            storeDict[toWH]['latitude'],
                                                            storeDict[toWH]['longitude'],
                                                            distanceGM,distanceSL))
                f.flush()
										  
    pickle.dump(routeDict,open(routePKL,"wb"))

    ### Let's compute the road scaling factors
    routeScaleDict = {}
    for routeKey in routeDict.keys():
        route = routeDict[routeKey]
        for segment in route:
            if segment['distanceGM'] != -1.0 and segment['distanceSL'] != 0.0:
                factor = float(segment['distanceGM'])/float(segment['distanceSL'])
            
                if segment['category'] not in routeScaleDict.keys():
                    routeScaleDict[segment['category']] = AccumVal(factor)
                else:
                    routeScaleDict[segment['category']]+= AccumVal(factor)


    with open(outputStatCSV,"wb") as f:
        f.write("Category,Mean,Max,Min,Stdev\n")
        for category in routeScaleDict.keys():
            routeData = routeScaleDict[category]
            f.write("%s,%10.10f,%10.10f,%10.10f,%10.10f\n"%(category,
                                                            routeData.mean(),
                                                            routeData.max(),
                                                            routeData.min(),
                                                            routeData.stdv()))
    

               
    

        
                          


			    
	
