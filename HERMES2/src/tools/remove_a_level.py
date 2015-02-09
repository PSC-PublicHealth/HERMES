#!/usr/bin/env python
__doc__=""" remove_a_level.py
A program that removes a specified level and reroutes the network
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

_hermes_svn_id_="$Id: remove_a_level.py 1053 2012-08-16 17:47:26Z stbrown $"


import sys,os
import simplejson,urllib
try:
    from util import longitudeLatitudeSep,AccumVal
except:
    raise RuntimeError("Cannot import HERMES utilities.  PYTHONPATH environment variable must be set"\
                       "to include your HERMES main directory in order to use this tool")
import hermes_data
import csv_tools
import time
import pickle
import optparse
import math

     
routesOutputFields = []
storesOutputFields = []
storesOutputList = []
routesOutputList = []

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][--storefile][--routefile][--level]
    """)
    parser.add_option("-s","--storefile",help="HERMES store file you wish to process")
    parser.add_option("-r","--routefile",help="HERMES route file you wish to process")
    parser.add_option("-l","--level",help="Level to remove from the system")
    parser.add_option("-p","--peoplefile",help="UnifiedPeopleTypeFile",default="findPeopleFile")
    parser.add_option("-d","--distscalefile",help="The CSV that describes the scaling factors between two levels")

    opts,args=parser.parse_args()

    return {'storefile':opts.storefile,'routefile':opts.routefile,
            'level':opts.level,'peoplefile':opts.peoplefile}    

if __name__ == '__main__':

    inputDict = parseCommandLine()
    storeFile = inputDict['storefile']
    routeFile = inputDict['routefile']
    levelToRemove = inputDict['level']
    outputStoreCSV = inputDict['storefile'][:-3] + levelToRemove + '_removed.csv'
    outputRouteCSV = inputDict['routefile'][:-3] + levelToRemove + '_removed.csv'

    peopleFile = ""
    if inputDict['peoplefile'] == "findPeopleFile":
        hermesDataPath = ""
        try:
            hermesDataPath = os.environ['HERMES_DATA_PATH']
        except:
            raise RuntimeError('HERMES_DATA_PATH must be defined to use this module')

        peopleFile = hermesDataPath + "/UnifiedPeopleTypeInfo.csv"
    else:
        peopleFile = inputDict['peoplefile']
                    
    with open(storeFile,"rb") as f:
        storesOutputFields,reclist = csv_tools.parseCSV(f)
    
    with open(routeFile,"rb") as f:
        routesOutputFields,reclist = csv_tools.parseCSV(f)
    
    #print str(routesOutputFields)
    hd = hermes_data.hermes_data(storeFile, routeFile, None, peopleFile)

    ### deep copy of the hermes Data routes:
    newStores = {}
    for store in hd.stores.keys():
        newStores[store] = hd.stores[store]
    
    newRoutes = {}
    for route in hd.routes.keys():
        newRoutes[route] = hd.routes[route]

#    print "Finished Deep Copy"
    for id,s in hd.stores.items():
        if s['CATEGORY'] == levelToRemove:
        ### Find Current Stores information
            parent = s['parent']
            children = s['children']
            parentRoute = s['parentRoute']
            childRoutes = s['childRoutes']
        ### Change Store information in the new Store Dict
            parentNewStore = newStores[parent]
            parentNewStore['children'] = children
            parentNewStore['childRoutes'] = childRoutes

            for child in s['children']:
                childNewStore = newStores[child]
                childNewStore['parent'] = parent

        ### Go through each children's route and change the destination
                thisChildsParentRoute = hd.routes[hd.stores[child]['parentRoute']]
                for i in range(0,len(thisChildsParentRoute['stops'])):
                    if newRoutes[hd.stores[child]['parentRoute']]['stops'][i][1] == id:
                        newRec = newRoutes[hd.stores[child]['parentRoute']]['stops'][i][3]
                        newRec['idcode'] = parent
                        newRec['LocName'] = hd.stores[parent]['NAME']
        
                        newTuple = (i,parent,99999.0,newRec)
                        newRoutes[hd.stores[child]['parentRoute']]['stops'][i] = newTuple
                                        
        ### Remove the parent route
            newRoutes[parentRoute] = None
            newStores[id] = None
            
 
    ### Write New Store file
    storeKeyList = []
    for store in newStores.keys():
        storeKeyList.append(store)
    storeKeyList.sort()

    with open(outputStoreCSV,"wb") as f:
        headStr = ""
        for field in storesOutputFields:
            headStr += str(field) + ","
        headStr = headStr[:-1] + "\n"
        f.write("%s"%headStr)
        for skey in storeKeyList:
            if newStores[skey] is not None:
                lineStr = ""
                for field in storesOutputFields:
                    lineStr += str(newStores[skey][field]) + ","
                lineStr = lineStr[:-1] + "\n"
                f.write("%s"%lineStr)

    ### Write New Route file
    routeKeyList = []
    for route in newRoutes.keys():
        if newRoutes[route] is not None:
            routeKeyList.append(route)
    routeKeyList.sort()

    with open(outputRouteCSV,"wb") as f:
        headStr = ""
        for field in routesOutputFields:
            headStr += str(field) + ","
        headStr = headStr[:-1] + "\n"
        f.write("%s"%headStr)

        for rkey in routeKeyList:
            route = newRoutes[rkey]
            for i in range(0,len(route['stops'])):
                stop = route['stops'][i][3]
                lineStr = ""
                for field in routesOutputFields:
                    lineStr += str(stop[field]) + ","
                lineStr = lineStr[:-1] + "\n"
                f.write("%s"%lineStr)
            
    
    
                


               
    

        
                          


			    
	
