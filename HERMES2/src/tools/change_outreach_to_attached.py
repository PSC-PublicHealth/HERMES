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
from copy import copy, deepcopy
from transformation import setLatenciesByNetworkPosition

import sys
import optparse


routesOutputFields = []
storesOutputFields = []
storesOutputList = []
routesOutputList = []

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][--storefile][--routefile][--replacementfile][--consolidatestorage]
    """)
    parser.add_option("-d", "--use_db", type=int, default=None)
    parser.add_option("-i", "--input", default=None)
    parser.add_option("-n","--name",default="attached")

    opts, args = parser.parse_args()

    return {'usedb':opts.use_db,
            'input':opts.input,
            'name':opts.name}

if __name__ == '__main__':

    inputDict = parseCommandLine()

    if inputDict['usedb']:
        import session_support_wrapper as session_support
        import db_routines

        iface = db_routines.DbInterface(echo=False)
        session = iface.Session()
        shdNtwkDB = ShdNetworkDB(session, inputDict['usedb'])
        shdNtwkDB.useShadowNet()
        shdNtwk = shdNtwkDB._net
    else:
        userInput = input.UserInput(inputDict['input'], False)
        shdTypes = shadow_network.loadShdTypes(userInput, input.UnifiedInput())
        shdNtwk = shadow_network.loadShdNetwork(userInput, shdTypes, inputDict['name'])

    
    ### First Set the network latencies
    setLatenciesByNetworkPosition(shdNtwk)
    
    attachedTemp = None
    for id, route in shdNtwk.routes.items():
        if route.Type == "attached":
            attachedTemp = route.createRecords()
            print attachedTemp
            break
    for id, route in shdNtwk.routes.items():
        if route.Type == "dropandcollect":
            originStore = route.stops[0].store
            # ## create a new rec from the stops
            prevID = None
            count = 1
            thisStop = route.stops[1].store
            # firstRec = thisStop.createRecord()
            # first = False
            changeStores = []
            newOriginNewBorn = 0.0
            has_clinic = False
            has_NewBornDTPHEP = False
            while prevID != thisStop.idcode:
                changeStores.append(thisStop)
                # if first == False:
                #    newRecDict = thisStop.createRecord()
                #    first = True
                # else:
                #    for v,n in thisStop.createRecord().items():
                #        newRecDict[v] += n
                    #    print 'v = ' +str(v) + 'n = ' + str(n)
                    # newRecDict += thisStop.createRecord()
                for demand in thisStop.demand:
                    if demand.invName == "Newborn":
                        newOriginNewBorn += demand.count
                prevID = thisStop.idcode
                count += 1
                print "This Stop id = %d count = %d" % (thisStop.idcode, count)
                thisStop = route.stops[count].store

            # print "NewCount = " + str(newOriginNewBorn)
            for client in originStore.clients():
                # print client[0].NAME[-7:]
                if client[0].NAME[-7:] == "_clinic":
                    has_clinic = True
                    for demand in client[0].demand:
                        if demand.invName == "Newborn_DTPHEP":
                            has_NewBornDTPHEP = True
                            # print "Adding %d to %s Newborn"%(newOriginNewBorn,client[0].NAME)
                            demand.count += newOriginNewBorn
            print "Remove Route = %s" % (route.RouteName)
            shdNtwk.removeRoute(route)
            for thisStore in changeStores:

                newRecDict = thisStore.createRecord()
                # newOriginNewBorn += newRecDict['Newborn']

                # # Make this an attached record
                newName = thisStore.NAME + "_attached"
                newIdcode = thisStore.idcode
                newRecDict['NAME'] = newName
                newRecDict['Type'] = "attached"
                newRecDict['Inventory'] = ""
                newRecDict['UseVialsLatency'] = float(int(newRecDict['UseVialsLatency']))
                # newRecDict['UseVialsInterval'] = firstRec['UseVialsInterval']
                newRecDict['idcode'] = newIdcode
                newRecDict['Longitude'] = originStore.Longitude
                newRecDict['Latitude'] = originStore.Latitude
                newRecDict['Device Utilization Rate'] = 1.0
                newRecDict['FUNCTION'] = "Administration"
                newRecDict['CATEGORY'] = "OutreachClinic"
                newRecDict['Service1'] = 0
                if has_clinic:
                    newRecDict['Newborn_DTPHEP'] = 0
                newRecDict['Notes'] = ''


                # ## Remove this Route

                # ## Create Attached Route template
                # thisAttTemp = {'RouteName'
                thisAttTemp = [{
                               'RouteName': "r_" + str(newIdcode) + "_att",
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
                               'idcode':newIdcode,
                               'RouteOrder':1,
                               'TransitHours':'0',
                               'ShipIntervalDays':'',
                               'ShipLatencyDays':'',
                               'PullOrderAmount':'',
                               'Notes':'',
                               'Conditions':'',
                               'TruckType':''}]

                print "Removing Store: %s: %s" % (str(thisStore.idcode), thisStore.NAME)
                shdNtwk.removeStore(thisStore)

                print "Adding Store: %s: %s" % (str(newRecDict['idcode']), newRecDict['NAME'])
                shdNtwk.addStore(newRecDict)
                shdNtwk.addRoute(thisAttTemp)

            # for demand in originStore.demand:
            #    if demand.invName == "Newborns":
            #        demand.count = newOriginNewBorn

            # print thisAttTemp[0]
            # print "IdCode: " + str(originStore.idcode) + " recDict " + str(newRecDict)
    shdNtwk.writeCSVRepresentation()
    # newStoreIdList = []
    # ## create a  list of store ids and route ids to keep
    # newStoreIdList.append(inputDict['centralplace'])

#    supStoreIds = shdNtwk.getWalkOfSupplierIds(inputDict['centralplace'])
#    cliStoreIds = shdNtwk.getWalkOfClientIds(inputDict['centralplace'])
#
#    print "Suppliers: "
#    for ID in supStoreIds:
#        newStoreIdList.append(ID)
#        print str(ID)
#
#    print "Clients: "
#    for ID in cliStoreIds:
#        newStoreIdList.append(ID)
#        print str(ID)
#
#    ## compile a list of Routes to remove
#    routesToRemove = []
#    for id,store in shdNtwk.stores.items():
#        if id not in newStoreIdList:
#            ## First remove all of the routes
#            for supStore,supRoute in store.suppliers():
#                routesToRemove.append(supRoute.RouteName)
#
#            for cliStore,cliRoute in store.clients():
#                routesToRemove.append(cliRoute.RouteName)
#
#    routesToRemoveSet = set(routesToRemove)
#
#    for routeName in routesToRemoveSet:
#        shdNtwk.removeRoute(shdNtwk.getRoute(routeName))
#
#    ### Now actually remove the Stores
#    for id,store in shdNtwk.stores.items():
#        if id not in newStoreIdList:
#            print "Removing Store: " + str(id)
#            shdNtwk.removeStore(store)
#
#    shdNtwk.writeCSVRepresentation()
            # store.clients = None
            # shdNtwk.removeStore(store)
    # suppliers = privotStoreSuppliers()

    # for supplier in pivotStore.suppliers():
    #    while supplier is not None:
    #        newStoreIdList.append(supplier[0].idcode)



#    if pivotStore['parentRoute'] is not None:
#        newRouteIdList.append(pivotStore['parentRoute'])

    # for ids in newStoreIdList:
    #    print str(ids)
    # sys.exit()
#    shdNtwk = shadow_network.loadShdNetwork(inputDict['input'], shdTypes, name)
#    if inputDict['peoplefile'] == "findPeopleFile":
#        hermesDataPath = ""
#        try:
#            hermesDataPath = os.environ['HERMES_DATA_PATH']
#        except:
#            raise RuntimeError('HERMES_DATA_PATH must be defined to use this module')
#
#        peopleFile = hermesDataPath + "/UnifiedPeopleTypeInfo.csv"
#    else:
#        peopleFile = inputDict['peoplefile']
#
#    with open(storeFile,"rb") as f:
#        storesOutputFields,reclist = csv_tools.parseCSV(f)
#
#    with open(routeFile,"rb") as f:
#        routesOutputFields,reclist = csv_tools.parseCSV(f)
#
#    hd = hermes_data.hermes_data(storeFile, routeFile, None, peopleFile)
#
#    ### deep copy of the hermes Data routes:
#    newStores = {}
#    newRoutes = {}
#
#    if inputDict['centralplace'] not in hd.stores.keys():
#        raise RuntimeError("pivot store not in this input file %s"%str(inputDict['centralplace']))
#
#
#    pivotStore = hd.stores[inputDict['centralplace']]
#    newStores[inputDict['centralplace']] = pivotStore
#    if pivotStore['parentRoute'] is not None:
#        newRoutes[pivotStore['parentRoute']] = hd.routes[pivotStore['parentRoute']]
#
#    if pivotStore['childRoutes'] is not None:
#        for cID in pivotStore['childRoutes']:
#            newRoutes[cID] = hd.routes[cID]
#    ### Walk up the from Pivot and add all parents:
#    parentID = pivotStore['parent']
#    while parentID is not None:
#        newStores[parentID] = hd.stores[parentID]
#    ### Have to alter to take care of loops
#        if hd.stores[parentID]['parentRoute']:
#            newRoutes[parentID] = hd.routes[hd.stores[parentID]['parentRoute']]
#        parentID = hd.stores[parentID]['parent']
#        print "New Parent ID = " + str(parentID)
#
#
#    childrenIDs = set(getAllChildrenIds(inputDict['centralplace'],hd.stores))
#
#    for childrenID in childrenIDs:
#        newStores[childrenID] = hd.stores[childrenID]
#        for routeID in newStores[childrenID]['childRoutes']:
#            newRoutes[routeID] = hd.routes[routeID]
#
#
#    for routeID in newRoutes.keys():
#        print str(routeID)
#    ### Write New Store file
#    storeKeyList = []
#    for store in newStores.keys():
#        storeKeyList.append(store)
#    storeKeyList.sort()
#
#    with open(outputStoreCSV,"wb") as f:
#        headStr = ""
#        for field in storesOutputFields:
#            headStr += str(field) + ","
#        headStr = headStr[:-1] + "\n"
#        f.write("%s"%headStr)
#        for skey in storeKeyList:
#            if newStores[skey] is not None:
#                lineStr = ""
#                for field in storesOutputFields:
#                    lineStr += str(newStores[skey][field]) + ","
#                lineStr = lineStr[:-1] + "\n"
#                f.write("%s"%lineStr)
#
#    ##    ### Write New Route file
#    routeKeyList = []
#    for route in newRoutes.keys():
#        if newRoutes[route] is not None:
#            routeKeyList.append(route)
#    routeKeyList.sort()
#
#    with open(outputRouteCSV,"wb") as f:
#        headStr = ""
#        for field in routesOutputFields:
#            headStr += str(field) + ","
#        headStr = headStr[:-1] + "\n"
#        f.write("%s"%headStr)
#
#        for rkey in routeKeyList:
#            route = newRoutes[rkey]
#            for i in range(0,len(route['stops'])):
#                stop = route['stops'][i][3]
#                lineStr = ""
#                for field in routesOutputFields:
#                    lineStr += str(stop[field]) + ","
#                lineStr = lineStr[:-1] + "\n"
#                f.write("%s"%lineStr)

# #    for id,s in hd.stores.items():
# #        #print "ID = " + str(id)
# #        if id in replacementDict.keys():
# #            print "Altering " + str(id)
# #            replaceID = replacementDict[str(id)]

# #            replaceStore = hd.stores[replaceID]
# #        ### Find Current Stores information
# #            parent = s['parent']
# #            children = s['children']
# #            parentRoute = s['parentRoute']
# #            childRoutes = s['childRoutes']

# #            if replaceStore['parent'] != parent:
# #                raise RuntimeError("Places %s and %s do not share the same parent")

# #        ### If we are to consolidate storage, move old place's storage to new
# #            if constore:
# #                if s.has_key('Inventory'):
# #                    newStores[replaceID]['Inventory'] += "+" + str(s['Inventory'])
# #                if s.has_key('Storage'):
# #                    newStores[replaceID]['Storage'] += "+" + str(s['Storage'])

# #        ### Add Old Store's Children to the New Store's

# #            for child in children:
# #                newStores[replaceID]['children'].append(child)
# #            for cRoutes in childRoutes:C:\Users\Shawn\Workspaces\Eclipse 3.6 Classic\HERMES\src\
# #                newStores[replaceID]['childRoutes'].append(cRoutes)

# #            for child in s['children']:
# #                childNewStore = newStores[child]
# #                childNewStore['parent'] = replaceID

# #        ### Go through each children's route and change the destination
# #                thisChildsParentRoute = hd.routes[hd.stores[child]['parentRoute']]
# #                for i in range(0,len(thisChildsParentRoute['stops'])):
# #                    if newRoutes[hd.stores[child]['parentRoute']]['stops'][i][1] == id:
# #                        newRec = newRoutes[hd.stores[child]['parentRoute']]['stops'][i][3]
# #                        newRec['idcode'] = replaceID
# #                        newRec['LocName'] = hd.stores[replaceID]['NAME']

# #                        newTuple = (i,parent,99999.0,newRec)
# #                        newRoutes[hd.stores[child]['parentRoute']]['stops'][i] = newTuple

# #        ### Remove the parent route
# #    C:\Users\Shawn\Workspaces\Eclipse 3.6 Classic\HERMES\src\        newRoutes[parentRoute] = None
# #            newStores[id] = None


# #    ### Write New Store file
# #    storeKeyList = []
# #    for store in newStores.keys():
# #        storeKeyList.append(store)
# #    storeKeyList.sort()

# #    with open(outputStoreCSV,"wb") as f:
# #        headStr = ""
# #    C:\Users\Shawn\Workspaces\Eclipse 3.6 Classic\HERMES\src\    for field in storesOutputFields:
# #            headStr += str(field) + ","
# #        headStr = headStr[:-1] + "\n"
# #        f.write("%s"%headStr)
# #        for skey in storeKeyList:
# #            if newStores[skey] is not None:
# #                lineStr = ""
# #                for field in storesOutputFields:
# #                    lineStr += str(newStores[skey][field]) + ","
# #                lineStr = lineStr[:-1] + "\n"
# #                f.write("%s"%lineStr)

# #    ### Write New Route file
# #    routeKeyList = []
# #    for route in newRoutes.keys():
# #        if newRoutes[route] is not None:
# #            routeKeyList.append(route)
# #    routeKeyList.sort()

# #    with open(outputRouteCSV,"wb") as f:
# #        headStr = ""
# #        for field in routesOutputFields:
# #            headStr += str(field) + ","
# #        headStr = headStr[:-1] + "\n"
# #        f.write("%s"%headStr)

# #        for rkey in routeKeyList:
# #            route = newRoutes[rkey]
# #            for i in range(0,len(route['stops'])):
# #                stop = route['stops'][i][3]
# #                lineStr = ""
# #                for field in routesOutputFields:
# #                    lineStr += str(stop[field]) + ","
# #                lineStr = lineStr[:-1] + "\n"
# #                f.write("%s"%lineStr)
















