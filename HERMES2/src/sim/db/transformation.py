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
                                  doNotModifySet=None):
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
        popTot = sum( [inv.Count for inv in store.demand])
        print 'Store %s: popTot %s'%(store.NAME,popTot)
        if (popTot>0 or len(store.clientRoutes())==0):
            if storeFilters==[] or any([f(store) for f in storeFilters]):
                if len(store.suppliers()) > 0: 
                    supplierRoute = store.suppliers()[0][1]
                    latency = supplierRoute.ShipLatencyDays + offset
                else:
                    latency = offset
                if storeId not in doNotModifySet:
                    print "setting Store %s to %g"%(store.NAME,latency)
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
    for storeId,store in shdNtwk.stores.items():
        ### If this is at the start level, then we should go through making loops
        if store.CATEGORY == startLevel:
            hubLoc = [store.Longitude,store.Latitude,store]
            if hubLoc[2].FUNCTION == "Surrogate":
                continue
            print "working on %s"%store.NAME
            locList = []
            
            for client in store.clients():
                if client[0].CATEGORY == endLevel:
                    if client[1].Type != "attached":
                        locList.append([client[0].Longitude,client[0].Latitude,client[0]])
                        shdNtwk.removeRoute(client[1])
            
            print "Makeing Loops with Store %d as Hub"%hubLoc[2].idcode
            print "And..."
            for loc in locList:
                print "   %d"%loc[2].idcode
            
            (bestDistance,bestConnections) = findBestLoops(hubLoc,locList,placesPerLoop,iterations)
            
            print "The Best Distance is: %10.10f"%bestDistance
            print "The Best Loops are %s"%str(bestConnections)
            
            ### Add vehicles to Place if they do not exist
            count = hubLoc[2].countInventory(vehicleType)
            print "Count of Vehicle %s = %d %d %d"%(vehicleType,len(bestConnections),numberOfLoopsPerVehicle,count)
            numVehiclesNeeded = int(math.ceil(float(len(bestConnections))/float(numberOfLoopsPerVehicle)))
            print "Number of Vehicles Needed = %d"%numVehiclesNeeded
            if numVehiclesNeeded > count:
                print "Adding %d %s to location %d"%(numVehiclesNeeded-count,vehicleType,hubLoc[2].idcode)
                hubLoc[2].addInventory(vehicleType,numVehiclesNeeded-count)
            ### convert best Connections to newRoutes
              
            for loop in bestConnections:
                newLoopCount += 1
                cumTime = 0.0
                print "%d, %f,%f"%(loop[0],locList[loop[0]][0],locList[loop[0]][1])
                distances = []
                times = []
                lat = locList[loop[0]][1]
                lon = locList[loop[0]][0]
                firstDistance,firstTime = util.getGoogleDirectionsDistanceLatLon(hubLoc[1],hubLoc[0],
                                                                                 lat,lon)                                                          
                                                              
                distances.append(firstDistance)
                times.append(firstTime)
                
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
                    print "Calculating distance for %f,%f: %f,%f"%(lat1,lon1,lat2,lon2)
                    distanceKM,timeHr = util.getGoogleDirectionsDistanceLatLon(lat1,lon1,lat2,lon2)
                    distances.append(distanceKM)
                    times.append(timeHr)
                actualTimes = fixTimesByMaxTripLength(times,maxTravelTime)

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
                        'PickupDelayFrequency':0
                        }
                    ]
                loopCount = 0
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
                            'PickupDelayFrequency':0
                            }
                        )
                    
                shdNtwk.addRoute(newRoute)
        
    
