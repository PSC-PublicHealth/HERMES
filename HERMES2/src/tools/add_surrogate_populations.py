#!/usr/bin/env python
__doc__ = """ consolidate_places_in_level.py
This program takes a stores file, route file and a csv that describes places to be changed, and creates new stores and routes files executing the alterations.
"""

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

_hermes_svn_id_ = "$Id: consolidate_places_in_level.py 1053 2012-08-16 17:47:26Z stbrown $"

import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
import input
from copy import deepcopy
import sys
import optparse

def hPrint(store, dataDict, level=0, levelToStop=None):
    spaceString = ""
    for i in range(0, level):
        spaceString += ","
    print("%s%s,%10.2f" % (spaceString, store.NAME, dataDict[store.idcode]))
    for cli in store.clients():
        hPrint(cli[0], dataDict, level=level + 1)
        
        
routesOutputFields = []
storesOutputFields = []
storesOutputList = []
routesOutputList = []

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-d db_id]
    """)
    parser.add_option("-i", "--inputfile", default=None)
    parser.add_option("-p", "--popfile", default=None)
    # parser.add_option("-d","--use_db",type=int,default=None)
    opts, args = parser.parse_args()
    
    return (opts, args)

def getPopulation(shdNtwk, storeID):
    clientIDs = shdNtwk.getWalkOfClientIds(storeID)
    clientIDs.append(storeID)
    totalPopDict = {}
    for cID in clientIDs:
        if clientIDs.count(cID) > 1:
            print "Fuck for cID %d " % cID
        cStore = shdNtwk.getStore(cID)
        for demand in cStore.demand:
            if demand.invName not in totalPopDict.keys():
                totalPopDict[demand.invName] = 0.0
            totalPopDict[demand.invName] += demand.count
    
    return totalPopDict

if __name__ == '__main__':
    import csv_tools
    import math
    
    
    opts, args = parseCommandLine()
        
    userInput = input.UserInput(opts.inputfile, False)
    shdTypes = shadow_network.loadShdTypes(userInput, input.UnifiedInput())
    shdNtwk = shadow_network.loadShdNetwork(userInput, shdTypes, "Bihar_surr")
    
    inputDict = {}
    with open(opts.popfile, "rb") as f:
        keyList, recList = csv_tools.parseCSV(f)
        for rec in recList:
            inputDict[rec['idcode']] = {}
            for key in keyList:
                inputDict[rec['idcode']][key] = rec[key]
    
    
    # ## test
    #totRoot = getPopulation(shdNtwk, 1101001)
    # print str(totRoot)
    
    # for key,value in inputDict.items():
        # print "KEY: %d Newborns %d"%(key,value['Newborn'])
    totNewborns = 0
    for sKey, storeRec in inputDict.items():
        print "sKey = " + str(sKey)
        newSurId = int(sKey + 7 * math.pow(10, (int(math.log10(sKey)) + 1)))
        newName = None
        newCategory = None
        newInterval = 20
        newLatency = None
        diffDict = {}
        if sKey in shdNtwk.stores.keys():

            totalPopDict = getPopulation(shdNtwk, sKey)
            totNewborns += totalPopDict["Newborn"]
            
            # print "ID: %d TotPop: %d"%(sKey,totalPopDict["Newborn"])
            thisStore = shdNtwk.getStore(sKey)
            # # Compute the difference
            for key in totalPopDict.keys():
                if storeRec.has_key(key):
                    diffDict[key] = storeRec[key] - totalPopDict[key]
        
            newName = thisStore.NAME + "_surr"
            newCategory = 'District'
            newLatency = 2
            suppliers = thisStore.suppliers()
            if len(suppliers) > 1:
                raise RuntimeError("Fuck this wont work with more than one supplier")
            originStore = thisStore
            
        else:
            for key, value in inputDict[sKey].items():
                if key in shdNtwk.people.keys():
                    diffDict[key] = inputDict[sKey][key]
            # print str(diffDict)
            newName = storeRec['NAME']
            newCategory = 'Division'
            newLatency = 6
            originStore = shdNtwk.rootStores()[0]
        # print "Creating a Store %d"%(newSurId)   
        thisSurTemp = {
                       'idcode':newSurId,
                       'NAME':newName,
                       'CATEGORY':newCategory,
                       'FUNCTION':'Surrogate',
                       'Device Utilization Rate':1.0,
                       'UseVialsLatency':newLatency,
                       'UseVialsInterval':newInterval,
                       'Latitude':-1.0,
                       'Longitude':-1.0,
                       'Inventory':'',
                       'Notes':'Added Automatically'
                       }
        for key, value in diffDict.items():
            thisSurTemp[key] = value
        print str(thisSurTemp)
        # print "Creating a Route %d -> %d"%(originStore.idcode,newSurId)
        thisAttTemp = [{
                        'RouteName': "r_" + str(newSurId) + "_sur",
                        'Type':'attached',
                        'LocName':originStore.NAME,
                        'idcode':originStore.idcode,
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
                        'idcode':newSurId,
                        'RouteOrder':1,
                        'TransitHours':'0',
                        'ShipIntervalDays':'',
                        'ShipLatencyDays':'',
                        'PullOrderAmount':'',
                        'Notes':'',
                        'Conditions':'',
                        'TruckType':''}]
            
        shdNtwk.addStore(thisSurTemp)
        # ## Verify
        testStore = shdNtwk.getStore(newSurId)
        shdNtwk.addRoute(thisAttTemp) 
    
    # ## Verify
    print "Verify"
    print "Found newborns %d" % (totNewborns)
    # Getting the State attached places
    #Kpop = getPopulation(shdNtwk, 1119001)
    #Npop = getPopulation(shdNtwk, 1122001)
    #print "KPop = %d" % Kpop["Newborn"]
    #print "NPop = %d" % Npop["Newborn"]
    for sKey, storeRec in inputDict.items():
        print "SKey = " + str(sKey)
        newSurId = int(sKey + 7 * math.pow(10, (int(math.log10(sKey)) + 1)))
        newBorns = 0
        if sKey in shdNtwk.stores.keys():
            totalDict = getPopulation(shdNtwk, sKey)
            surStore = shdNtwk.getStore(newSurId)
            for demand in surStore.demand:
                if demand.invName == "Newborn":
                    newBorns = demand.count
            newBorns += totalDict['Newborn']
            print "ID: %d Newborns: %d" % (sKey, newBorns)
        else:
            print "ID: %d Newborns: %d" % (sKey, storeRec["Newborn"])
    
    sortedList = shdNtwk.addSortedClients(shdNtwk.rootStores()[0])
    with open('sort.csv', "wb") as f:
        for iD in sortedList:
            store = shdNtwk.getStore(iD)
            f.write("%d, %s, %s\n" % (store.idcode, store.NAME, store.CATEGORY))
    shdNtwk.writeCSVRepresentation()

