#!/usr/bin/env python
__doc__=""" consolidate_places_in_level.py
This program takes a stores file, route file and a csv that describes places to be changed, and creates new stores and routes files executing the alterations.
"""

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

_hermes_svn_id_="$Id: consolidate_places_in_level.py 1053 2012-08-16 17:47:26Z stbrown $"


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
    %prog [-v][--storefile][--routefile][--replacementfile][--consolidatestorage]
    """)
    parser.add_option("-s","--storefile",help="HERMES store file you wish to process")
    parser.add_option("-r","--routefile",help="HERMES route file you wish to process")
    parser.add_option("-l","--level",help="Level to remove from the system")
    parser.add_option("-f","--replacementfile",help="File that gives the places to change in the system")
    parser.add_option("-p","--peoplefile",help="UnifiedPeopleTypeFile",default="findPeopleFile")
    parser.add_option("-c","--consolidatestorage",help="Flag to move storage from removed places to new places",
                      action="store_true",default=False)
    parser.add_option("-d","--distscalefile",help="The CSV that describes the scaling factors between two levels")

    opts,args=parser.parse_args()

    return {'storefile':opts.storefile,'routefile':opts.routefile,
            'replacementfile':opts.replacementfile,'peoplefile':opts.peoplefile,
            'consolidatestorage':opts.consolidatestorage}    

if __name__ == '__main__':

    inputDict = parseCommandLine()
    storeFile = inputDict['storefile']
    routeFile = inputDict['routefile']
    replacementFile = inputDict['replacementfile']
    outputStoreCSV = inputDict['storefile'][:-3] + 'altered.csv'
    outputRouteCSV = inputDict['routefile'][:-3] + 'altered.csv'
    constore = False
    if inputDict['consolidatestorage']:
        constore = True
    
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

    replacementDict = {}
    with open(replacementFile,"rb") as f:
        keylist,reclist = csv_tools.parseCSV(f)
        for rec in reclist:
            replacementDict[str(rec['From'])] = str(rec['To'])

    print str(replacementDict)
    hd = hermes_data.hermes_data(storeFile, routeFile, None, peopleFile)

    ### deep copy of the hermes Data routes:
    newStores = {}
    for store in hd.stores.keys():
        newStores[store] = hd.stores[store]
    
    newRoutes = {}
    for route in hd.routes.keys():
        newRoutes[route] = hd.routes[route]

    for id,s in hd.stores.items():
        #print "ID = " + str(id)
        if id in replacementDict.keys():
            print "Altering " + str(id)
            replaceID = replacementDict[str(id)]

            replaceStore = hd.stores[replaceID]
        ### Find Current Stores information
            parent = s['parent']
            children = s['children']
            parentRoute = s['parentRoute']
            childRoutes = s['childRoutes']

            if replaceStore['parent'] != parent:
                raise RuntimeError("Places %s and %s do not share the same parent")

        ### If we are to consolidate storage, move old place's storage to new
            if constore:
                if s.has_key('Inventory'):
                    newStores[replaceID]['Inventory'] += "+" + str(s['Inventory'])
                if s.has_key('Storage'):
                    newStores[replaceID]['Storage'] += "+" + str(s['Storage'])
        
        ### Add Old Store's Children to the New Store's

            for child in children:
                newStores[replaceID]['children'].append(child)
            for cRoutes in childRoutes:
                newStores[replaceID]['childRoutes'].append(cRoutes)                                                

            for child in s['children']:
                childNewStore = newStores[child]
                childNewStore['parent'] = replaceID

        ### Go through each children's route and change the destination
                thisChildsParentRoute = hd.routes[hd.stores[child]['parentRoute']]
                for i in range(0,len(thisChildsParentRoute['stops'])):
                    if newRoutes[hd.stores[child]['parentRoute']]['stops'][i][1] == id:
                        newRec = newRoutes[hd.stores[child]['parentRoute']]['stops'][i][3]
                        newRec['idcode'] = replaceID
                        newRec['LocName'] = hd.stores[replaceID]['NAME']
        
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

            
    
    
                


               
    

        
                          


			    
	
