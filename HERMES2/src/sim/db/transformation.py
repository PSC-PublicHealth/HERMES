#!/usr/bin/env python 

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


__doc__=""" transformation.py
This module holds a series of complex transformations on the supply chain network
"""

_hermes_svn_id_="$Id: util.py 1425 2013-08-30 19:55:57Z stbrown $"

import shadow_network

def setLatenciesByNetworkPosition(shdNtwk,incrementDays=2,initialLatencyDays=0,limitDays=20,stagger=False,
                                  doNotModifySet=None,debug=False):
    """
    doNotModifySet is a set of store IDs to be left alone.  The fixed values at those stores may influence values at 
    downstream stores.  Note that stores in this set still count against the list of available transport.
    """
    if doNotModifySet is None: doNotModifySet = set()
    
    # Generate a list of the whole tree, sorted in breadth-first order
    sortedList = shdNtwk.addSortedClients(shdNtwk.rootStores()[0])
    
    for storeId in sortedList:
        thisStore = shdNtwk.stores[storeId]
        if len(thisStore.clientRoutes())==0:
            continue
        supLatencyDays = 0
        if thisStore not in shdNtwk.rootStores():
            if len(thisStore.suppliers()) != 1:
                print "!!!WARNING: There are more than one supplier route for Store %d, choosing the first route in list to determine latency!!!"
            supplierStore = thisStore.suppliers()[0]
            supLatencyDays = supplierStore[1].ShipLatencyDays
     
        startLatencyDays = supLatencyDays + initialLatencyDays + incrementDays
        
        if startLatencyDays > limitDays:
            startLatencyDays = startLatencyDays - limitDays
        
        queueCounts = {} # entries are truckType.name:n where n is zero-based position in line 
        for clientRoute in thisStore.clientRoutes():
            routeType = shadow_network.ShdRoute.types[clientRoute.Type]
            if routeType.isAttached(): continue
            elif (not stagger or routeType.supplierStop() != 0):
                if storeId not in doNotModifySet:
                    if debug:
                        print "setting Route %s to %g"%(clientRoute.RouteName,startLatencyDays)
                    shdNtwk.routes[clientRoute.RouteName].ShipLatencyDays = startLatencyDays
            else:
                truckTypeName = clientRoute.TruckType
                if truckTypeName not in queueCounts: queueCounts[truckTypeName] = 0
                nQ = queueCounts[truckTypeName]
                queueCounts[truckTypeName] += 1
                nSuchTrucks = max(thisStore.countInventory(truckTypeName),1) # protect against error of not including a truck
                nTurn = nQ/nSuchTrucks # round down is correct
                myStartTime = startLatencyDays + nTurn*incrementDays
                if storeId not in doNotModifySet:
                    if debug:
                        print "setting Route %s to %g ( %d in line for %d trucks)"%(clientRoute.RouteName,myStartTime,nQ,nSuchTrucks)
                    shdNtwk.routes[clientRoute.RouteName].ShipLatencyDays = myStartTime
                
def setUseVialLatenciesAsOffsetOfShipLatencyFromRoute(shdNtwk,offset=0.1,storeFilters=[], doNotModifySet=None):
    """
    For each location which is a leaf or which has non-zero population, set the UseVialsLatency based on the 
    latency of the incoming shipment.  Filters are functions taking a shadow_network.ShdStore as the only argument 
    and returning True or False; if there are no filters or any filter returns True the latency for that Store is set.

    doNotModifySet is a set of store IDs to be left alone.  The fixed values at those stores may influence values at 
    downstream stores.  Note that stores in this set still count against the list of available transport.
    """
    if doNotModifySet is None: doNotModifySet = set()

    for storeId,store in shdNtwk.stores.items():
        popTot = sum( [inv.count for inv in store.demand])
        #print 'Store %s: popTot %s'%(store.NAME,popTot)
        if (popTot>0 or len(store.clientRoutes())==0):
            if storeFilters==[] or any([f(store) for f in storeFilters]):
                if len(store.suppliers()) > 0: 
                    supplierRoute = store.suppliers()[0][1]
                    latency = supplierRoute.ShipLatencyDays + offset
                else:
                    latency = offset
                if storeId not in doNotModifySet:
                    #print "setting Store %s to %g"%(store.NAME,latency)
                    store.UseVialsLatency = latency

def setRouteByPolicyBetweenLevels(shdNtwk,levelFrequencies):  
    ''' This transformation will set the frequencies by level according to a global 
        supply chain policy.
        The format of the levelFrequency list must be each element with a tuple:
        ( originLevel, toLevel, frequencyDays )
        if more than one level is needed in "toLevel", this can be a list.
        If the route does not match a tuple, it will not alter it, so currently it is up
        to the user to ensure the list is appropriate
    '''
    
    for routeId,route in shdNtwk.routes.items():
        originLevel = route.stops[0].store.CATEGORY
        destinationLevels = []
        for stop in route.stops[1:-1]:
            if stop.store.CATEGORY not in destinationLevels:
                destinationLevels.append(stop.store.CATEGORY)
        
        for oLevel,dLevel,freq in levelFrequencies:
            dLevelList = []
            if not isinstance(dLevel,list):
                ## if dLevel is not a list, make it a list so I don't have to write two loops
                dLevelList.append(dLevel)
            else:
                dLevelList = dLevel
            
            if originLevel == oLevel:
                for routeDLevel in destinationLevels:
                    if routeDLevel not in dLevelList:
                        continue
            else:
                continue
            
            ### if we make it here, set it the route to this frequency
            route.ShipIntervalDays = freq
            for stop in route.stops:
                if stop.PullOrderAmountDays is not None:
                    stop.PullOrderAmountDays = freq
    
def convertLoopToSurrogate(shdNtwk,routeId,connectToStore=None):
    storesToConvert = []
    routesToRemove = []
    
    routeToConvert = shdNtwk.routes[routeId]
    
    for stop in routeToConvert.stops[1:]:
        #storesToConvert.append(stop.store)
        (sConv,rConv,sRej) = shdNtwk.storesAndRoutesBelow(stop.store)
        print "store: {0} removing {1}".format(stop.store,sConv)
        for s in sConv:
            if s not in storesToConvert:
                storesToConvert.append(s)
        for r in rConv:
            routesToRemove.append(r)
    
    supStore = routeToConvert.stops[0].store
    thisStore = routeToConvert.stops[1].store
    #supplyRoute = thisStore.supplierRoute()
    #print thisStore.idcode
    #print supplyRoute
    totDemandRec = thisStore.demandToRec()
    
    for store in storesToConvert:
        if store == thisStore:
            continue
        storeDemRec = store.demandToRec()
        
        for k,v in storeDemRec.items():
            if k in totDemandRec.keys():
                totDemandRec[k]+= v 
            else:
                totDemandRec[k] = v 
    thisStore.clearDemand()
    thisStore.demandFromRec(totDemandRec)
    

        
    ### NOw make the store a surrogate
    thisStore.clearInventory()
    #supplyRoute = thisStore.supplierRoute()
    thisStore.Latitude = -1.0
    thisStore.Longitude = -1.0
    thisStore.FUNCTION = "Surrogate"
    #if supplyRoute.Type in ['pull','demandfetch']:
    #    thisStore.UseVialsInterval = supplyRoute.stops[0].PullOrderAmountDays
    #elif supplyRoute.Type in ['attached']:
    #    pass
    #else:
    thisStore.UseVialsInterval = routeToConvert.ShipIntervalDays
    thisStore.UseVialsLatency = routeToConvert.ShipLatencyDays
    if connectToStore is None:
        newRoute = [
                    {
                     'RouteName':'{0}_surrogate_route'.format(thisStore.idcode),
                     'Type':'attached',
                     'LocName':supStore.NAME,
                     'idcode':supStore.idcode,
                     'RouteOrder':0
                     },
                    {
                     'Type':'attached',
                     'LocName':thisStore.NAME,
                     'idcode':thisStore.idcode,
                     'RouteOrder':1
                     }
                    ]
    else:
        connectStore = shdNtwk.stores[connectToStore]
        newRoute = [
                    {
                     'RouteName':'{0}_surrogate_route'.format(thisStore.idcode),
                     'Type':'attached',
                     'LocName':connectStore.NAME,
                     'idcode':connectStore.idcode,
                     'RouteOrder':0
                     },
                    {
                     'Type':'attached',
                     'LocName':thisStore.NAME,
                     'idcode':thisStore.idcode,
                     'RouteOrder':1
                     }
                    ]
    print "New Route = {0}".format(newRoute)
    if connectToStore is None:
        shdNtwk.removeRoute(routeToConvert)
    
        ### delete all of the children stores
    for route in routesToRemove:
        print "Removing Route: {0}".format(route.RouteName)
        shdNtwk.removeRoute(route)
    
    #shdNtwk.removeRoute(routeId)    
    for store in storesToConvert:
        if store != thisStore:
            print "Removing Store {0}".format(store.idcode)
            shdNtwk.removeStore(store)
        
    shdNtwk.addRoute(newRoute)
    
    stopsToRemove= []
    for storeId,store in shdNtwk.stores.items():
        if store.FUNCTION == "Surrogate":
            if store.NAME[-4:] == "stop":
                stopsToRemove.append(storeId)
    
    for storeId in stopsToRemove:
        thisStore = shdNtwk.stores[storeId]
        #shdNtwk.removeRoute(thisStore.supplierRoute())
        shdNtwk.removeStore(thisStore)
    
        #print "Stop Store: {0}".format(stop.store.idcode)
        
    
def convertToSurrogate(shdNtwk,storeId,connectToStore=None):
    (storesToConvert,routesToRemove,storesRejected) = shdNtwk.storesAndRoutesBelow(shdNtwk.stores[storeId])
    print "Stores To Convert"
    for x in storesToConvert:
        print "StoreID: {0}".format(x.idcode)
    print "Routes To Remove"
    for x in routesToRemove:
        print "Route Number: {0}".format(x.RouteName)
    thisStore = shdNtwk.stores[storeId]
    
    totDemandRec = thisStore.demandToRec()
    
    for store in storesToConvert:
        if store.idcode == storeId:
            continue
        storeDemRec = store.demandToRec()
        
        for k,v in storeDemRec.items():
            if k in totDemandRec.keys():
                totDemandRec[k]+= v 
            else:
                totDemandRec[k] = v 
    thisStore.clearDemand()
    thisStore.demandFromRec(totDemandRec)
    
    ### delete all of the children stores
    for route in routesToRemove:
        print "Removing Route: {0}".format(route.RouteName)
        shdNtwk.removeRoute(route)
        
    for store in storesToConvert:
        if store != thisStore:
            print "Removing Store {0}".format(store.idcode)
            shdNtwk.removeStore(store)
        
    ### NOw make the store a surrogate
    thisStore.clearInventory()
    supplyRoute = thisStore.supplierRoute()
    thisStore.Latitude = -1.0
    thisStore.Longitude = -1.0
    thisStore.FUNCTION = "Surrogate"
    if supplyRoute.Type in ['pull','demandfetch']:
        thisStore.UseVialsInterval = supplyRoute.stops[0].PullOrderAmountDays
    elif supplyRoute.Type in ['attached']:
        pass
    else:
        thisStore.UseVialsInterval = supplyRoute.ShipIntervalDays
    thisStore.UseVialsLatency = supplyRoute.ShipLatencyDays
    if connectToStore is None:
        newRoute = [
                    {
                     'RouteName':'{0}_surrogate_route'.format(thisStore.idcode),
                     'Type':'attached',
                     'LocName':thisStore.supplierStore().NAME,
                     'idcode':thisStore.supplierStore().idcode,
                     'RouteOrder':0
                     },
                    {
                     'Type':'attached',
                     'LocName':thisStore.NAME,
                     'idcode':thisStore.idcode,
                     'RouteOrder':1
                     }
                    ]
    else:
        connectStore = shdNtwk.stores[connectToStore]
        newRoute = [
                    {
                     'RouteName':'{0}_surrogate_route'.format(thisStore.idcode),
                     'Type':'attached',
                     'LocName':connectStore.NAME,
                     'idcode':connectStore.idcode,
                     'RouteOrder':0
                     },
                    {
                     'Type':'attached',
                     'LocName':thisStore.NAME,
                     'idcode':thisStore.idcode,
                     'RouteOrder':1
                     }
                    ]
    print "New Route = {0}".format(newRoute)
    if connectToStore is None:
        shdNtwk.removeRoute(supplyRoute)
    shdNtwk.addRoute(newRoute)
    
    stopsToRemove= []
    for storeId,store in shdNtwk.stores.items():
        if store.FUNCTION == "Surrogate":
            if store.NAME[-4:] == "stop":
                stopsToRemove.append(storeId)
    
    for storeId in stopsToRemove:
        thisStore = shdNtwk.stores[storeId]
        shdNtwk.removeRoute(thisStore.supplierRoute())
        shdNtwk.removeStore(thisStore)

def makeLoopsOptimizedByDistanceBetweenLevels(shdNtwk,startLevel,endLevel,placesPerLoop,
                                              maxTravelTime=8.0,vehicleType="GenericVehicle",iterations = 100000, 
                                              add_vehicles=True,
                                              numberOfLoopsPerVehicle=10):
    ''' This transormation will create loops between two levels trying to optimize by distance 
        travelled.  It uses Google Maps to compute the distances of the loops and sets the times 
        according to a maxTravelTime
    '''
    from loopUtils import findBestLoops,fixTimesByMaxTripLength
    import util
    import math
    
    newLoopCount = 0
    
    storesToHub = []
    ### First, make a list of the stores that will be the start of a loop
    for storeId,store in shdNtwk.stores.items():
        if store.isAttached() or store.isSurrogate():
            continue
        if store.CATEGORY == startLevel:
            ## lets check that this store is not already part of a loop and is not the start of it
            supplierRoute = store.supplierRoute()
            addToList = True
            if supplierRoute:
                if len(supplierRoute.stops) > 2:
                    storesInLoop = [x.store for x in supplierRoute.stops]
                    if storesInLoop.index(store) > 0:
                        addToList = False
            
            if addToList:
                storesToHub.append(storeId)
    
    ## Ok now we need to run through all of these stores and go to town creating a loop
    for storeId in storesToHub:
        ### If this is at the start level, then we should go through making loops
        store = shdNtwk.stores[storeId]
        hubLoc = [store.Longitude,store.Latitude,store]
        
        print "working on %s"%store.NAME
        clientsToLoopList = []
        clientRoutesToRemove = set()
        for client in store.clients():
            #print client
            if client[0].CATEGORY == endLevel or endLevel == "all":
                if client[1].Type != "attached":
                    clientsToLoopList.append(client[0].idcode)
                    clientRoutesToRemove.add(client[1])
                    #if client[0] == client[1].stops[:-1]:
                    #    shdNtwk.removeRoute(client[1])
        
        for cR in clientRoutesToRemove:
            print "Removing Route {0}".format(cR.RouteName)
            shdNtwk.removeRoute(cR)
        print "Loop Origin = {0}".format(store.NAME)   
        print "Clients = {0}".format(clientsToLoopList) 
    
    
        print "Making Loops with Store %d as Hub"%hubLoc[2].idcode
        print "And..."
        #for loc in locList:
        #    print u"   %d"%loc[2].idcode
        
        locList = []
        for x in clientsToLoopList:
            lon = shdNtwk.stores[x].Longitude
            lat = shdNtwk.stores[x].Latitude
            store = shdNtwk.stores[x]
            locList.append((lon,lat,store))
        
        print "finding loops for {0} iterations".format(iterations)
        (bestDistance,bestConnections) = findBestLoops(hubLoc,locList,placesPerLoop,iterations)
#
#         print "The Best Distance is: %10.10f"%bestDistance
#         print "The Best Loops are %s"%str(bestConnections)
#          
        ### Add vehicles to Place if they do not exist
        count = hubLoc[2].countInventory(vehicleType)
        print u"Count of Vehicle %s = %d %d %d"%(vehicleType,len(bestConnections),numberOfLoopsPerVehicle,count)
        numVehiclesNeeded = int(math.ceil(float(len(bestConnections))/float(numberOfLoopsPerVehicle)))
        print u"Number of Vehicles Needed = %d"%numVehiclesNeeded
        if numVehiclesNeeded > count:
            print u"Adding %d %s to location %d"%(numVehiclesNeeded-count,vehicleType,hubLoc[2].idcode)
            print u"HERE = {0}".format(numVehiclesNeeded-count)
            hubLoc[2].addInventory(vehicleType,numVehiclesNeeded-count)
        ### convert best Connections to newRoutes
            
        for loop in bestConnections:
            newLoopCount += 1
            cumTime = 0.0
            print u"%d, %f,%f"%(loop[0],locList[loop[0]][0],locList[loop[0]][1])
            distances = []
            times = []
            lat = locList[loop[0]][1]
            lon = locList[loop[0]][0]
            print "ha = {0} {1}".format(lat,lon)
            print "Meh = {0}".format(hubLoc)
            print "yo = {0} {1}".format(hubLoc[1],hubLoc[0])
            firstDistance,firstTime = util.getGoogleDirectionsDistanceLatLon(hubLoc[1],hubLoc[0],
                                                                             lat,lon)                                                          
            #firstDistance,firstTime = util.longitudeLatitudeSep(hubLoc[1],hubLoc[0], lat,lon)  
            print "first dist and time = {0} {1}".format(firstDistance,firstTime)                              
            distances.append(firstDistance)
            times.append(firstTime)
            
            print "Loop here = {0}".format(loop)
            for stop in loop:
                lat1 = locList[stop][1]
                lon1 = locList[stop][0]
                print lat1
                print lon1
                ind = loop.index(stop)
                if ind == len(loop)-1:
                    lat2 = hubLoc[1]
                    lon2 = hubLoc[0]
                else:
                    lat2 = locList[loop[ind+1]][1]
                    lon2 = locList[loop[ind+1]][0]
                print lon2
                print lat2
                print "Calculating distance for %f,%f: %f,%f"%(lat1,lon1,lat2,lon2)
                distanceKM,timeHr = util.getGoogleDirectionsDistanceLatLon(lat1,lon1,lat2,lon2)
                #distanceKM,timeHr = util.longitudeLatitudeSep(lat1,lon1,lat2,lon2)
                distances.append(distanceKM)
                times.append(timeHr)
            print "Computing Max Times"
            actualTimes = fixTimesByMaxTripLength(times,maxTravelTime)
            print "Creating Route"
            loopMoniker = "l_%s_%s"%(startLevel,endLevel)
            newRoute = [
                {
                    'RouteName':"%s_%d"%(loopMoniker,newLoopCount),
                    'Type':'varpush',
                    'LocName':hubLoc[2].NAME,
                    'idcode':hubLoc[2].idcode,
                    'RouteOrder':0,
                    'TransitHours':actualTimes[0],
                    'ShipIntervalDays':20,
                    'ShipLatencyDays':2,
                    'PullOrderAmountDays':'',
                    'Notes':'Automatically Generated',
                    'Conditions':'',
                    'TruckType':vehicleType,
                    'DistanceKM':distances[0],
                    'PickupDelayMagnitude':0,
                    'PickupDelaySigma':0,
                    'PickupDelayFrequency':0,
                    'PerDiem':'Std_PerDiem_None'
                    }
                ]
            loopCount = 0
            print "Loop = {0}".format(loop)
            for stop in loop:
                lat1 = locList[stop][1]
                lon1 = locList[stop][0]
                ind = loop.index(stop)
                if ind == len(loop)-1:
                    lat2 = hubLoc[1]
                    lon2 = hubLoc[0]
                else:
                    lat2 = locList[loop[ind+1]][1]
                    lon2 = locList[loop[ind+1]][0]
                  
                #distanceKM,timeHr = util.getGoogleDirectionsDistanceLatLon(lat1,lon1,lat2,lon2)
                  
                #if (curLeftover + timeHr) > 8.0:
                      
                loopCount += 1 
                location = locList[stop]
                newRoute.append(
                    {
                        'Type':'varpush',
                        'LocName':location[2].NAME,
                        'idcode':location[2].idcode,
                        'RouteOrder':loopCount,
                        'TransitHours':actualTimes[ind],
                        'ShipIntervalDays':20,
                        'ShipLatencyDays':2,
                        'PullOrderAmountDays':'',
                        'Notes':'Automatically Generated',
                        'Conditions':'',
                        'TruckType':vehicleType,
                        'DistanceKM':distances[ind],
                        'PickupDelayMagnitude':0,
                        'PickupDelaySigma':0,
                        'PickupDelayFrequency':0,
                        'PerDiem':'Std_PerDiem_None'

                        }
                    )
                  
            shdNtwk.addRoute(newRoute)

def setStorageForEntireLevel(shdNtwk, shdTypes, levelToChange=[],storageDeviceName=None,storageDeviceRec=None,addToReplace=True,
                             daysPerMonth=28,powerCost=0.0):
    import math
    
    if levelToChange is None:
        raise RuntimeError("transformation.setStorageForEntireLevel called with no level name")
    for level in levelToChange:
        if level not in shdNtwk.getLevelList():
            raise RuntimeError("transformation.setStorageForEntireLevel called with a level {0} that is not in the model".format(level))
    if storageDeviceName is None and storageDeviceRec is None:
        raise RuntimeError("transformation.setStorageForEntireLevel called with no storage device name or record")
    newType = None
    if storageDeviceName is not None:
        if storageDeviceName not in shdNtwk.types.keys():
            raise RuntimeError("transformation.setStorageForEntireLevel storage device {0} does not exist in this model,".format(storageDeviceName)\
                                +"please choose something in the model or define the new device by storageDeviceRec")
        newType = shdNtwk.fridges[storageDeviceName]    
    else:
        storeDeviceRecHere = None
        if len(shdNtwk.priceTable) == 0:
            ### we are good
            storeDeviceRecHere = storageDeviceRec
            pass
        else:
            capDep = float(storageDeviceRec['BaseCost'])/float(storageDeviceRec['AmortYears'])
            powerUse = 0.0
            if storageDeviceRec['PowerRateUnits'] == 'kWh/day':
                powerUse=powerCost*float(storageDeviceRec['PowerRate'])*daysPerMonth*12
            priceRec = {
                        'Name':storageDeviceRec['Name'],
                        'Currency':storageDeviceRec['BaseCostCurCode'],
                        'PerKM':0,
                        'PerYear':capDep*1.05 + powerUse,
                        'PerTrip':0,
                        'PerTreatmentDay':0,
                        'PerDiem':0,
                        'PerVial':0,
                        'Level':'',
                        'Conditions':'',
                        'Notes':''
                        }
            costEntry = shadow_network.ShdCosts(priceRec)
            shdNtwk.addPriceEntry(costEntry)
            newStorageRec = {
                            'Name':storageDeviceRec['Name'],
                            'DisplayName':storageDeviceRec['DisplayName'],
                            'Make':storageDeviceRec['Make'],
                            'Model':storageDeviceRec['Model'],
                            'Year':storageDeviceRec['Year'],
                            'Energy':storageDeviceRec['Energy'],
                            'Category':storageDeviceRec['Category'],
                            'freezer':storageDeviceRec['freezer'],
                            'cooler':storageDeviceRec['cooler'],
                            'roomtemperature':storageDeviceRec['roomtemperature'],
                            'Notes':storageDeviceRec['Notes']
                            }
            storeDeviceRecHere = newStorageRec

        shdTypesClass = shadow_network.ShdTypes.typesMap['fridges']
        newType = shdTypesClass(storageDeviceRec)
        shdNtwk.fridges['help'] = newType
        
    
    for storeId,store in shdNtwk.stores.items():
        if store.CATEGORY in levelToChange:
        #if storeId == 110100:
            inv = store.countAllInventory
            ## get total volume of current cold storage
            vols = {'cooler':0.0,
                    'freezer':0.0}
            toRem = []
            for t in store.inventory:
                print t.invName
                print t.invType
                if type(t.invType) == shadow_network.ShdStorageType and t.invName != "proxy":
                    
                    vols['cooler'] += t.invType.cooler*t.count
                    vols['freezer'] += t.invType.freezer*t.count
                    #store.updateInventory(t.invType,0)
                    toRem.append(t.invType)
            
            for tr in toRem:
                store.updateInventory(tr,0)
                
            newCount = math.ceil(vols['cooler']/float(newType.cooler))
            store.addInventory(newType,newCount)
            #print vols
                
        #shdNtwk.types.addType(newType)
        #shdTypes.addType(newType)
    
    

            
        
    
    
