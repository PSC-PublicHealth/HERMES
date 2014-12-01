#!/usr/bin/env python

########################################################################
# Copyright C 2009, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__="""networkbuilder.py
This package provides convenience functions for assembling a
shipping network from specification files.
"""

_hermes_svn_id_="$Id$"

import types

from SimPy.Simulation  import *
#from SimPy.SimulationTrace  import *
#from SimPy.SimulationGUIDebug import *

import constants as C
import globals as G
import csv_tools
import warehouse
import storagetypes
import trackabletypes
import trucktypes
import peopletypes
import util
from powercut import PowerCut, AddPowerCutInfo
import random
from reportinghierarchy import ReportingHierarchyNode
from delayinfo import DelayInfo

# Where to look in a route list for the supplier entry, by route type
supplierOffsetByRouteType= {'push':0, 'varpush':0, 'pull':0, 'attached':0, 'askingpush':0,
                            'schedfetch':1, 'schedvarfetch':1, 'demandfetch':1, 'dropandcollect':0,
                            'persistentpull':0, 'persistentdemandfetch':1}

def _conditionsFromRec(rec):
    if 'Conditions' in rec:
        if rec['Conditions'] is not None and rec['Conditions'] != "":
	           return rec['Conditions']
        else:
	           return "normal"
    else:
        return "normal"
    
def _perDiemNameFromRec(rec):
    if ('PerDiemType' in rec
            and rec['PerDiemType'] is not None):
        return rec['PerDiemType']
    else:
        return None

def _genericRouteChecks(locList,storeDict):
    """
    Do some consistency checks on the route information
    """
    perDiemName = _perDiemNameFromRec(locList[0])
    for rec in locList:
        assert _perDiemNameFromRec(rec) == perDiemName, \
            ("Inconsistent per diem policies for route %s" %
             rec['RouteName'])
        if 'LocName' in rec:
            if storeDict[rec['idcode']] is None:
                print "***Error*** route %s references location %d which is considered dead."%\
                    (rec['RouteName'],rec['idcode'])
                print "reasons could include lack of population and/or lack of storage."
                raise RuntimeError("route references dead location %d"%rec['idcode'])
#             if rec['LocName'] != storeDict[rec['idcode']].name:
# #                 print "***Warning*** Name mismatch on route %s id %ld: <%s> vs. <%s>"%\
# #                       (rec['RouteName'].encode('utf8'),rec['idcode'],
# #                        rec['LocName'].encode('utf8'),storeDict[rec['idcode']].bName)
#                 print type(rec['RouteName'])
#                 print repr(rec['RouteName'])
#                 print type(rec['LocName'])
#                 print repr(rec['LocName'])
#                 print type(storeDict[rec['idcode']].name)
#                 print type(storeDict[rec['idcode']].bName)
#                 print repr(storeDict[rec['idcode']].name)
#                 print repr(storeDict[rec['idcode']].bName)
#                 print "***Warning*** Name mismatch on route %s id %ld: <%s> vs. <%s>"%\
#                       (rec['RouteName'],rec['idcode'],rec['LocName'],storeDict[rec['idcode']].bName)

def _innerBuildScheduledRoute(routeName, sim, locList, storeDict, getShipInterval, getStartupLatency, getTruckInterval,
                              getOrderPendingLifetime, shipperProcType):
    
    supplierRec= locList[0]
    supplierKey= supplierRec['idcode']
    supplierWH= storeDict[supplierKey]
    if supplierWH is None:
        raise RuntimeError("Route %s originates from dead warehouse at code %d"%(routeName,supplierKey))
    supplierTruckType= supplierRec['TruckType']
    
    locList= locList[1:]
    transitChain= []
    routeClients = []
    leftoverTimeHours= 0.0 # for coping with stops at dead warehouses
    if 'ShipIntervalDays' in supplierRec:
        shipInterval= float(supplierRec['ShipIntervalDays'])
    else:
        shipInterval= getShipInterval(storeDict,supplierKey)
        if shipInterval != getTruckInterval(storeDict,supplierKey):
            raise RuntimeError('Possible consistency error: shipInterval and truckInterval differ for the scheduled route %s'%routeName)
    if 'ShipLatencyDays' in supplierRec:
        shipStartupLatency = float(supplierRec['ShipLatencyDays'])
    else:
        # print str(supplierRec)
        shipStartupLatency = getStartupLatency(storeDict, supplierKey)
    conditions = _conditionsFromRec(supplierRec)
    transitTimeHours= float(supplierRec['TransitHours']) 
    if transitTimeHours > 0.0:
        # encoded with first leg transit time in first slot, return trip transit time in last slot
        for rec in locList:
            keyCode= rec['idcode']
            clientWH= storeDict[keyCode]
            if clientWH is None: # this is a dead warehouse
                leftoverTimeHours += transitTimeHours
            else:
                if 'TruckType' in rec and rec['TruckType']!=supplierTruckType:
                    raise RuntimeError("Route %s has two different truck types"%routeName)
                if 'ShipIntervalDays' in rec and float(rec['ShipIntervalDays'])!=shipInterval:
                    raise RuntimeError("ShipInterval values are inconsistent for route %s"%routeName)
                if 'ShipLatencyDays' in rec and float(rec['ShipLatencyDays'])!=shipStartupLatency:
                    raise RuntimeError("Startup latency values are inconsistent for route %s"%routeName)
                if keyCode not in routeClients: # dropandcollect visits each client twice
                    routeClients.append(keyCode)
                    supplierWH.addClient(clientWH)
                    clientWH.addSupplier(supplierWH,rec)
                transitChain.append((((transitTimeHours+leftoverTimeHours)/float(C.hoursPerDay)),
                                     clientWH,
                                     conditions))
                leftoverTimeHours= 0.0
            conditions = _conditionsFromRec(rec)
            transitTimeHours= float(rec['TransitHours'])
        # Add the return trip
        transitChain.append((((transitTimeHours+leftoverTimeHours)/float(C.hoursPerDay)),
                             supplierWH,
                             conditions))
    else:
        # backward compatibility: first leg transit time is in first client slot, and is re-used for return trip
        for rec in locList:
            keyCode= rec['idcode']
            transitTimeHours= float(rec['TransitHours'])
            clientWH= storeDict[keyCode]
            newConditions= _conditionsFromRec(rec)
            if clientWH is None: # this is a dead warehouse
                leftoverTimeHours += transitTimeHours
            else:
                if 'TruckType' in rec and rec['TruckType']!=supplierTruckType:
                    raise RuntimeError("Route %s has two different truck types"%routeName)
                if 'ShipIntervalDays' in rec and float(rec['ShipIntervalDays'])!=shipInterval:
                    raise RuntimeError("ShipInterval values are inconsistent for route %s"%routeName)
                if 'ShipLatencyDays' in rec and float(rec['ShipLatencyDays'])!=shipStartupLatency:
                    raise RuntimeError("Startup latency values are inconsistent for route %s"%routeName)
                if keyCode not in routeClients: # dropandcollect visits each client twice
                    routeClients.append(keyCode)
                    supplierWH.addClient(clientWH)
                    clientWH.addSupplier(supplierWH,rec)
                transitChain.append((((transitTimeHours+leftoverTimeHours)/float(C.hoursPerDay)),
                                     clientWH,
                                     conditions))
                leftoverTimeHours= 0.0
            conditions = newConditions
            # Add the return trip
        transitTimeHours = transitChain[0][0]*float(C.hoursPerDay)
        transitChain.append((((transitTimeHours+leftoverTimeHours)/float(C.hoursPerDay)),
                             supplierWH,
                             conditions))
            
    # Requests need to be placed before the truck leaves, but no earlier than time 0.0!
    reqCycleStartupLatency= shipStartupLatency-0.01
    if reqCycleStartupLatency<0.0:
        reqCycleStartupLatency= 0.0
        shipStartupLatency= 0.01

    truckType= sim.trucks.getTypeByName(supplierTruckType, sim=sim)

    delayInfo = _GetDelayInfo(sim.userInput, supplierRec, sim)

    shipperProc= shipperProcType(supplierWH, transitChain,
                                 shipInterval,
                                 getOrderPendingLifetime(storeDict,
                                                         supplierKey),
                                 C.shipPriority,
                                 startupLatency=shipStartupLatency,
                                 truckType=truckType,
                                 name="%s_%s_%s"%(shipperProcType.__name__,supplierWH.name,routeName),
                                 delayInfo=delayInfo)
    
    shipperProc.setNoteHolder( sim.notes.createNoteHolder() )
    shipperProc.noteHolder.addNote({"RouteName":routeName,
                                    "RouteTruckType":truckType.bName})
    
    allShippingProcs= [shipperProc]
    
    supplierWH.addClientRoute(name = routeName, 
                              proc = shipperProc,
                              clientIds = routeClients,
                              routeType = supplierRec['Type'],
                              truckType = truckType,
                              interval = shipInterval,
                              latency = shipStartupLatency)

    
    return supplierWH, shipInterval, reqCycleStartupLatency, transitChain, allShippingProcs

def _buildPushRoute(routeName, sim, locList, storeDict, 
                    getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                    getPullMeanFrequency, getOrderPendingLifetime):
        
    supplierWH, shipInterval, reqCycleStartupLatency, transitChain, allShippingProcs= \
        _innerBuildScheduledRoute(routeName, sim, locList, storeDict, 
                                  getShipInterval, getStartupLatency, getTruckInterval, getOrderPendingLifetime,
                                  warehouse.ShipperProcess)
    
    # Last stop in the chain is the supplier (after the return leg); everyone else is a client
    for clientWH in [wh for transitTime,wh,conditions in transitChain[:-1]]:
        ship= warehouse.ScheduledShipment(supplierWH, clientWH,
                                          shipInterval, None,
                                          startupLatency=reqCycleStartupLatency)
        allShippingProcs.append(ship)

    return allShippingProcs

def _buildVarPushRoute(routeName, sim, locList, storeDict, 
                       getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                       getPullMeanFrequency, getOrderPendingLifetime):
        
    supplierWH, shipInterval, reqCycleStartupLatency, transitChain, allShippingProcs= \
        _innerBuildScheduledRoute(routeName, sim, locList, storeDict, 
                                  getShipInterval, getStartupLatency, getTruckInterval, getOrderPendingLifetime,
                                  warehouse.ShipperProcess)
    
    # Last stop in the chain is the supplier (after the return leg); everyone else is a client
    for clientWH in [wh for transitTime,wh,conditions in transitChain[:-1]]:
        ship= warehouse.ScheduledVariableSizeShipment(supplierWH, clientWH,
                                                      shipInterval, None,
                                                      startupLatency=reqCycleStartupLatency)
        allShippingProcs.append(ship)

    return allShippingProcs

def _buildAskingPushRoute(routeName, sim, locList, storeDict, 
                           getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                           getPullMeanFrequency, getOrderPendingLifetime):
    supplierWH, shipInterval, reqCycleStartupLatency, transitChain, allShippingProcs= \
        _innerBuildScheduledRoute(routeName, sim, locList, storeDict, 
                                  getShipInterval, getStartupLatency, getTruckInterval, getOrderPendingLifetime,
                                  warehouse.AskOnDeliveryShipperProcess)
    
    # Last stop in the chain is the supplier (after the return leg); everyone else is a client
    for clientWH in [wh for transitTime,wh,conditions in transitChain[:-1]]:
        ship= warehouse.ScheduledVariableSizeShipment(supplierWH, clientWH,
                                                      shipInterval, None,
                                                      startupLatency=reqCycleStartupLatency)
        allShippingProcs.append(ship)

    return allShippingProcs

def _buildDropAndCollectRoute(routeName, sim, locList, storeDict, 
                              getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                              getPullMeanFrequency, getOrderPendingLifetime):
    supplierWH, shipInterval, reqCycleStartupLatency, transitChain, allShippingProcs= \
        _innerBuildScheduledRoute(routeName, sim, locList, storeDict, 
                                  getShipInterval, getStartupLatency, getTruckInterval, getOrderPendingLifetime,
                                  warehouse.DropAndCollectShipperProcess)
    
    # Last stop in the chain is the supplier (after the return leg); everyone else is a client
    visited = set()
    for clientWH in [wh for transitTime,wh,conditions in transitChain[:-1]]:
        if clientWH not in visited:
            ship= warehouse.ScheduledVariableSizeShipment(supplierWH, clientWH,
                                                          shipInterval, None,
                                                          startupLatency=reqCycleStartupLatency)
            allShippingProcs.append(ship)
            visited.add(clientWH)

    return allShippingProcs
    

def _innerBuildScheduledFetchRoute(routeName, sim, locList, storeDict, getShipInterval, getStartupLatency, 
                                   getTruckInterval, getOrderPendingLifetime):
    
    startingRec= locList[0]
    startingKey= startingRec['idcode']
    startingWH= storeDict[startingKey]
    if startingWH is None:
        raise RuntimeError("Route %s originates from dead warehouse at code %d"%(routeName,startingKey))
    startingTruckType= startingRec['TruckType']
    if 'ShipIntervalDays' in startingRec:
        shipInterval= float(startingRec['ShipIntervalDays'])
    else:
        shipInterval= getShipInterval(storeDict,startingKey)
        if shipInterval != getTruckInterval(storeDict,startingKey):
            raise RuntimeError('Possible consistency error: shipInterval and truckInterval differ for the scheduled route %s'%routeName)
    if 'ShipLatencyDays' in startingRec:
        shipStartupLatency = float(startingRec['ShipLatencyDays'])
    else:
        shipStartupLatency = getStartupLatency(storeDict,startingKey)

    supplierRec= locList[1]
    supplierKey= supplierRec['idcode']
    supplierWH= storeDict[supplierKey]
    if supplierWH is None:
        raise RuntimeError("Route %s fetches supplies from dead warehouse at code %d"%(routeName,supplierKey))
    if 'TruckType' in supplierRec and supplierRec['TruckType']!=startingTruckType:
        raise RuntimeError("Route %s has two different truck types"%routeName)
    if 'ShipIntervalDays' in supplierRec and float(supplierRec['ShipIntervalDays'])!=shipInterval:
        raise RuntimeError("ShipInterval values are inconsistent for route %s"%routeName)
    if 'ShipLatencyDays' in supplierRec and float(supplierRec['ShipLatencyDays'])!=shipStartupLatency:
        raise RuntimeError("Startup latency values are inconsistent for route %s"%routeName)
    
    routeClients = [startingKey]
    supplierWH.addClient(startingWH)
    startingWH.addSupplier(supplierWH,startingRec)
    transitChain = None 
    conditions = _conditionsFromRec(startingRec)
    transitTimeHours= float(startingRec['TransitHours'])
    if transitTimeHours > 0.0:
        # encoded with first leg transit time in first slot, return trip transit time in last slot
        transitChain = [(transitTimeHours/float(C.hoursPerDay), supplierWH, conditions)]
        leftoverTimeHours= 0.0 # for coping with stops at dead warehouses
        for rec in locList[2:]:
            keyCode= rec['idcode']
            clientWH= storeDict[keyCode]
            if clientWH is None: # this is a dead warehouse
                leftoverTimeHours += transitTimeHours
            else:
                if 'TruckType' in rec and rec['TruckType']!=startingTruckType:
                    raise RuntimeError("Route %s has two different truck types"%routeName)
                if 'ShipIntervalDays' in rec and float(rec['ShipIntervalDays'])!=shipInterval:
                    raise RuntimeError("ShipInterval values are inconsistent for route %s"%routeName)
                if 'ShipLatencyDays' in rec and float(rec['ShipLatencyDays'])!=shipStartupLatency:
                    raise RuntimeError("Startup latency values are inconsistent for route %s"%routeName)
                routeClients.append(keyCode)
                supplierWH.addClient(clientWH)
                clientWH.addSupplier(supplierWH,rec)
                transitChain.append((((transitTimeHours+leftoverTimeHours)/float(C.hoursPerDay)),
                                     clientWH,
                                     conditions))
                leftoverTimeHours= 0.0
            conditions = _conditionsFromRec(rec)
            transitTimeHours= float(rec['TransitHours'])
        # Add the return trip
        transitChain.append((((transitTimeHours+leftoverTimeHours)/float(C.hoursPerDay)),
                             startingWH,
                             conditions))
    else:
        # backward compatibility: first leg transit time is in first client slot, and is re-used for return trip
        print "***Warning*** Route %s uses a DEPRECATED pattern of transit time layouts"%routeName
        transitTimeHours= float(supplierRec['TransitHours'])
        transitChain = [(transitTimeHours/float(C.hoursPerDay), supplierWH, conditions)]
        leftoverTimeHours= 0.0 # for coping with stops at dead warehouses
        for rec in locList[2:]:
            keyCode= rec['idcode']
            clientWH= storeDict[keyCode]
            if clientWH is None: # this is a dead warehouse
                leftoverTimeHours += transitTimeHours
            else:
                if 'TruckType' in rec and rec['TruckType']!=startingTruckType:
                    raise RuntimeError("Route %s has two different truck types"%routeName)
                if 'ShipIntervalDays' in rec and float(rec['ShipIntervalDays'])!=shipInterval:
                    raise RuntimeError("ShipInterval values are inconsistent for route %s"%routeName)
                if 'ShipLatencyDays' in rec and float(rec['ShipLatencyDays'])!=shipStartupLatency:
                    raise RuntimeError("Startup latency values are inconsistent for route %s"%routeName)
                transitTimeHours= float(rec['TransitHours'])
                routeClients.append(keyCode)
                supplierWH.addClient(clientWH)
                clientWH.addSupplier(supplierWH,rec)
                transitChain.append((((transitTimeHours+leftoverTimeHours)/float(C.hoursPerDay)),
                                     clientWH,
                                     conditions))
                leftoverTimeHours= 0.0
            conditions = _conditionsFromRec(rec)
        # Add the return trip: use the transit time from the first leg
        transitTimeHours= transitChain[0][0]
        transitChain.append((((transitTimeHours+leftoverTimeHours)/float(C.hoursPerDay)),
                             startingWH,
                             conditions))
            
    # Requests need to be placed before the truck leaves, but no earlier than time 0.0!
    reqCycleStartupLatency= shipStartupLatency-0.01
    if reqCycleStartupLatency<0.0:
        reqCycleStartupLatency= 0.0
        shipStartupLatency= 0.01

    truckType= sim.trucks.getTypeByName(startingTruckType, sim=sim)

    delayInfo = _GetDelayInfo(sim.userInput, supplierRec, sim)

    shipperProc= warehouse.FetchShipperProcess(startingWH, transitChain,
                                               shipInterval,
                                               getOrderPendingLifetime(storeDict,
                                                                       supplierKey),
                                               C.shipPriority,
                                               startupLatency=shipStartupLatency,
                                               truckType=truckType,
                                               name="ShipperProcess_%s_%s"%(supplierWH.name,
                                                                            routeName),
                                               delayInfo=delayInfo)
    
    shipperProc.setNoteHolder( sim.notes.createNoteHolder() )
    shipperProc.noteHolder.addNote({"RouteName":routeName,
                                    "RouteTruckType":truckType.bName})
    
    allShippingProcs= [shipperProc]
    
    supplierWH.addClientRoute(name = routeName, 
                              proc = shipperProc,
                              clientIds = routeClients,
                              routeType = supplierRec['Type'],
                              truckType = truckType,
                              interval = shipInterval,
                              latency = shipStartupLatency)

    return supplierWH, shipInterval, reqCycleStartupLatency, transitChain, allShippingProcs

def _buildScheduledFetchRoute(routeName, sim, locList, storeDict, 
                              getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                              getPullMeanFrequency, getOrderPendingLifetime):
            
    supplierWH, shipInterval, reqCycleStartupLatency, transitChain, allShippingProcs= \
        _innerBuildScheduledFetchRoute(routeName, sim, locList, storeDict, 
                                       getShipInterval, getStartupLatency, getTruckInterval, 
                                       getOrderPendingLifetime)
    
    # Last stop in the chain is the supplier (after the return leg); everyone else is a client
    for clientWH in [wh for transitTime,wh,conditions in transitChain[1:]]:
        ship= warehouse.ScheduledShipment(supplierWH, clientWH,
                                          shipInterval, None,
                                          startupLatency=reqCycleStartupLatency)
        allShippingProcs.append(ship)

    return allShippingProcs

def _buildScheduledVarFetchRoute(routeName, sim, locList, storeDict, 
                                 getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                                 getPullMeanFrequency, getOrderPendingLifetime):

    supplierWH, shipInterval, reqCycleStartupLatency, transitChain, allShippingProcs= \
        _innerBuildScheduledFetchRoute(routeName, sim, locList, storeDict, 
                                       getShipInterval, getStartupLatency, getTruckInterval, 
                                       getOrderPendingLifetime)
    
    # Last stop in the chain is the supplier (after the return leg); everyone else is a client
    for clientWH in [wh for transitTime,wh,conditions in transitChain[1:]]:
        ship= warehouse.ScheduledVariableSizeShipment(supplierWH, clientWH,
                                                      shipInterval, None,
                                                      startupLatency=reqCycleStartupLatency)
        allShippingProcs.append(ship)

    return allShippingProcs

def _innerBuildPullRoute(routeName, sim, locList, storeDict, 
                    getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                    getPullMeanFrequency, getOrderPendingLifetime, shipperProcType, procTypeString ):

    if len(locList)!=2:
        #print locList
        raise RuntimeError("Route file specifies %s route %s with other than two entries"%\
                           (procTypeString,routeName))

    assert procTypeString in supplierOffsetByRouteType, "Unknown demand route type %s"%procTypeString

    supplierOffset = supplierOffsetByRouteType[procTypeString]
    clientOffset = 1 - supplierOffset
    supplierRec= locList[supplierOffset]
    supplierKey= supplierRec['idcode']
    supplierWH= storeDict[supplierKey]
    clientRec= locList[clientOffset]
    clientKey= clientRec['idcode']
    routeType= clientRec['Type']
    clientWH= storeDict[clientKey]

    if clientWH is None:
        return [] # nothing to create
    else:
        if supplierWH is None:
            raise RuntimeError("Warehouse with key %d is marked dead but has %d %s as a client"%\
                               (supplierKey,clientKey,clientWH))        

        truckTypeStr= supplierRec['TruckType']
        if clientRec['TruckType'] != truckTypeStr and clientRec['TruckType'] != "default":
            raise RuntimeError("Route %s specifies two different truck types"%routeName)

        if 'ShipIntervalDays' in supplierRec:
            truckInterval= float(supplierRec['ShipIntervalDays'])
        else:
            truckInterval= getTruckInterval(storeDict,supplierKey)
        if 'ShipIntervalDays' in clientRec and float(clientRec['ShipIntervalDays']) != truckInterval:
            raise RuntimeError("ShipInterval values are inconsistent for route %s"%routeName)

        if 'ShipLatencyDays' in supplierRec:
            startupLatency= float(supplierRec['ShipLatencyDays'])
        else:
            startupLatency= getStartupLatency(storeDict,supplierKey)
        if 'ShipLatencyDays' in clientRec and float(clientRec['ShipLatencyDays']) != startupLatency:
            raise RuntimeError("Startup latency values are inconsistent for route %s"%routeName)

        if 'PullOrderAmountDays' in clientRec:
            pullMeanFrequencyDays= float(clientRec['PullOrderAmountDays'])
        else:
            pullMeanFrequencyDays= getPullMeanFrequency(storeDict,clientKey)
        # check pullMeanFrequencyDays.  Invalid values create ugly errors.
        if pullMeanFrequencyDays <= 0.0:
            raise RuntimeError('PullOrderAmountDays/pullMeanFrequencyDays is invalid for route %s'%routeName)

        toTimeHours = float(supplierRec['TransitHours'])
        froTimeHours = float(clientRec['TransitHours'])
        if toTimeHours == 0.0: # supplier rec has no value
            if froTimeHours == 0.0: # client rec has no value
                raise RuntimeError('TransitHours is zero or less for route %s; FTL travel is not supported'%routeName)
            else:
                toTimeHours = froTimeHours
        if froTimeHours == 0.0:
            # client rec has no value, but supplier rec does
            froTimeHours = toTimeHours
        
        if 'Conditions' in supplierRec:
            if supplierRec['Conditions'] is not None and supplierRec['Conditions'] != "":
                conditions = supplierRec['Conditions']
            else:
                conditions = "normal"
            if clientRec['Conditions'] is not None and clientRec['Conditions'] != "":
                if clientRec['Conditions'] != conditions:
                    raise RuntimeError("Inconsistent trip conditions for route %s: %s vs. %s"%\
                                       (routeName,conditions,clientRec['Conditions']))
            else:
                if conditions != "normal":
                    raise RuntimeError("Inconsistent trip conditions for route %s: %s vs. %s"%\
                                       (routeName,conditions,clientRec['Conditions']))
        else:
            conditions = "normal"
            
        supplierWH.addClient(clientWH)
        clientWH.addSupplier(supplierWH,supplierRec)
        tFunc,qFunc= getPullControlFuncs(storeDict,clientKey)
        truckType= sim.trucks.getTypeByName(truckTypeStr, sim=sim)

        delayInfo = _GetDelayInfo(sim.userInput, supplierRec, sim)

        ship= shipperProcType(supplierWH, clientWH,
                              tFunc,
                              qFunc,
                              (toTimeHours/float(C.hoursPerDay),
                               froTimeHours/float(C.hoursPerDay)),
                              getOrderPendingLifetime(storeDict,
                                                      supplierKey),
                              pullMeanFrequencyDays,
                              C.shipPriority,
                              startupLatency=startupLatency,
                              truckType=truckType,
                              minimumDaysBetweenShipments=truckInterval,
                              delayInfo=delayInfo,
                              conditions=conditions)
        
        ship.setNoteHolder(sim.notes.createNoteHolder())
        ship.noteHolder.addNote({"RouteName":routeName,
                                 "RouteTruckType":truckType.bName})
        
        allShippingProcs= [ship]
        supplierWH.addClientRoute(name = routeName, 
                                  proc = ship,
                                  clientIds = [clientKey],
                                  routeType = routeType,
                                  truckType = truckType,
                                  interval  = pullMeanFrequencyDays,
                                  latency   = startupLatency)
        
    return allShippingProcs


def _buildPullRoute(routeName, sim, locList, storeDict, 
                    getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                    getPullMeanFrequency, getOrderPendingLifetime ):

    return _innerBuildPullRoute(routeName, sim, locList, storeDict,
                                getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                                getPullMeanFrequency, getOrderPendingLifetime,
                                warehouse.OnDemandShipment,"pull")

def _buildPersistentPullRoute(routeName, sim, locList, storeDict, 
                              getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                              getPullMeanFrequency, getOrderPendingLifetime ):

    return _innerBuildPullRoute(routeName, sim, locList, storeDict,
                                getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                                getPullMeanFrequency, getOrderPendingLifetime,
                                warehouse.PersistentOnDemandShipment,"persistentpull")

def _buildDemandFetchRoute(routeName, sim, locList, storeDict, 
                           getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                           getPullMeanFrequency, getOrderPendingLifetime ):

    return _innerBuildPullRoute(routeName, sim, locList, storeDict,
                                getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                                getPullMeanFrequency, getOrderPendingLifetime,
                                warehouse.FetchOnDemandShipment,"demandfetch")

def _buildPersistentDemandFetchRoute(routeName, sim, locList, storeDict, 
                                     getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                                     getPullMeanFrequency, getOrderPendingLifetime ):

    return _innerBuildPullRoute(routeName, sim, locList, storeDict,
                                getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                                getPullMeanFrequency, getOrderPendingLifetime,
                                warehouse.PersistentFetchOnDemandShipment,"persistentdemandfetch")

def _buildAttachedRoute(routeName,sim,locList,storeDict,
                        getShipInterval, getStartupLatency, getTruckInterval, getPullControlFuncs,
                        getPullMeanFrequency, getOrderPendingLifetime):                        
    if len(locList)!=2:
        #print locList
        raise RuntimeError("Route file specifies attached route %s with other than two entries"%\
                           routeName)
        
    supplierRec= locList[0]
    supplierKey= supplierRec['idcode']
    supplierWH= storeDict[supplierKey]
    clientRec= locList[1]
    clientKey= clientRec['idcode']
    clientWH= storeDict[clientKey]

    if clientWH is None:
        return [] # nothing to create
    else:
        if supplierWH is None:
            raise RuntimeError("Warehouse with key %d is marked dead but has %d %s as a client"%\
                               (supplierKey,clientKey,clientWH))        

        # Things don't 'ship' to an attached clinic; they
        # just get used directly from the supplier's stores
        supplierWH.addClient(clientWH)
        clientWH.addSupplier(supplierWH,{'Type':'attached_clinic'})
        supplierWH.addClientRoute(name = 'Attached_%s'%clientWH.bName, 
                                  proc = None,
                                  clientIds = [clientWH.code],
                                  routeType = 'attached_clinic',
                                  truckType = None,
                                  interval  = None,
                                  latency   = None)

    return []

def _addImplicitAttachedClinic(rec, sim, storeDict, warehouseFromRec):
    """
    This routine generates a minimally defined attached clinic to associate demand with a Distribution
    location.  rec is the Stores record which was used to create the parent store.
    storeDict is updated in place by the addition of the new AttachedClinic, the idcode of which
    is the negative of the idcode specified in the input rec.
    """
    ownerId = rec['idcode']
    assert ownerId>0, "Attempt to add an implicit attached clinic to a Store with a non-positive IDCODE"
    owner = storeDict[ownerId]
    tweakedRec = csv_tools.CSVDict(rec) # shallow copy
    tweakedRec['CATEGORY'] = sim.userInput['cliniclevellist'][0]
    tweakedRec['FUNCTION'] = 'administration'
    tweakedRec['NAME'] = '%d_attached'%ownerId
    attachedId = -ownerId
    tweakedRec['idcode'] = attachedId
    # The attached clinic record must not contain inventory, to prevent error messages
    for k in ["Walk in -(lit)","Walk in +(lit)"]:
        if k in tweakedRec: tweakedRec[k] = 0.0
    for k in ["Inventory","Storage"]:
        if k in tweakedRec: tweakedRec[k] = ""
    attachedWh = warehouseFromRec(sim, tweakedRec, expectedType=warehouse.AttachedClinic)
    assert attachedWh is not None, "Unable to create an implicit attached warehouse for %d"%ownerId
    assert isinstance(attachedWh, warehouse.AttachedClinic), "Expected to produce an attached clinic"
    attachedWh.code = attachedId
    AddPowerCutInfo(sim, attachedWh, sim.userInput, rec)
    storeDict[attachedId] = attachedWh
    
    # Substitute the original NoteHolder for the new one created with this clinic.  The
    # NoteHolder ends up doubly linked, but this should be OK.
    attachedWh.setNoteHolder(owner.getNoteHolder())

    routeName= "implicit_attached_neg%ld"%ownerId
    return _buildAttachedRoute(routeName, sim, [rec, tweakedRec], storeDict, 
                               None, None, None, None, None, None)

def buildNetwork(storeKeys, storeRecList, 
		 routeKeys, routeRecList, 
		 sim, 
         warehouseFromRec,
         getShipInterval,
         getStartupLatency,
         getPullControlFuncs,
         getOrderPendingLifetime,
         getTruckInterval,
         getPullMeanFrequency,
         getDefaultSupplier,
         getDefaultTruckTypeName,
         getDefaultTruckInterval,
         getDefaultPullMeanFrequency):
    """
    buildNetwork creates the warehouses, clinics and transport routes of a simulation network.  
    The return value is a tuple (storeDict, shipperProcList) where storeDict is a dictionary
    of Warehouse class instances by ID code and shipperProcList is a list of processes implementing
    shipping routes.  Those processes have not yet been registered or activated.
    
    Legacy mechanisms are included for producing 'implied' pull routes and attached clinics, but
    those mechanisms are deprecated and may not be reliable.
    
    storeKeys, storeRecList contain records from the stores csv file containing Warehouse and Clinic information.
    routeKeys, routeRecList contain records from the routes csv file containing routing information.
    sim is the instance of HermesSim into which the warehouses will be defined.
    The signatures of the functions passed as parameters are:

        wh= warehouseFromRec(sim,rec)
        shipIntervalInDays=getShipInterval(storeDict,code)
        startupLatencyDays=getStartupLatency(storeDict,code)
        orderPendingLifetimeDays= getOrderPendingLifetime(storeDict,code)
        shippingIntervalDays= getTruckInterval(storeDict,code)
        meanPullIntervalDays= getPullMeanFrequency(storeDict,truckTypeString)
        supplierWarehouseIdCode= getDefaultSupplier(storeDict,clientWarehouseIdCode)
        truckNameString=getDefaultTruckTypeName(fromWH,toWH)
        shippingIntervalDays= getDefaultTruckInterval(fromWH,toWH)
        meanShippingIntervalDays= getDefaultPullMeanFrequency(storeDict,code)

      where code is a warehouse ID code,
      wh, fromWH and toWH are instances of classes derived from warehouse,
      rec is a CSV record, which is a dictionary containing column data;

        tFunc,qFunc= getPullControlFuncs(storeDict,code)
    
      where:
          vaccineCollection= tFunc(toWH)
          vaccineCollection= qFunc(fromWH,toWH,timeNow)

      where those vaccine collections specify the trigger quantities
      and shipping quantities for pull shipments.

    This function returns a tuple containing:
        A dictionary containing warehouses, the keys of which are warehouse
         ID codes.
        A list of Processes which implement the shipping routes; they have not
         yet been registered or activated.
    
    The following columns of routesCsvFile are required and/or recognized:
        idcode (required; long positive integer)
        RouteName (required; string)
        Type (required string; one of 'push','varpush', 'pull', or 'attached',
              'askingpush', 'schedfetch', 'schedvarfetch', 'demandfetch', 
              'persistentpull', 'persistentdemandfetch', or 'dropandcollect')
        TruckType (optional trucktype string; default is 'default')
        RouteOrder (required; integer, unique within a given RouteName)
        TransitHours (required; float, the value for the originating site must be
                      present but its value may be None)
        ShipIntervalDays (optional float; default is to call getTruckInterval for
                          'pull' routes or getShipInterval for others.  Only
                          the value for the originating site is used.  This value
                          sets the interval between shipments for non-'pull' shipments,
                          and the minimum allowed interval between shipments for
                          'pull' shipments.
        ShipLatencyDays (optional float; default is to call getStartupLatency.  Only
                          the value for the originating site is used.)
        PullOrderAmountDays (optional float; default is to call getPullMeanFrequency.
                          Only the value for the destination site is used.  This value
                          is ignored for all shipments which are not 'pull'.)
        
    buildNetwork also instantiates any PeopleTypes or inventory types specified for the
    network.  


    """
    
    # Scan for Stores columns matching known PeopleTypes
    for k in storeKeys:
        if sim.people.validTypeName(k):
            sim.people.getTypeByName(k) # force instantiation as a side effect
    if len(sim.people.getActiveTypeNames())==0:
        sim.people.getTypeByName(peopletypes.genericPeopleTypeName)
    
    # Index the store records for easy access
    storeRecDict= {} # will contain records which have not yet been converted to Warehouse instances
    for rec in storeRecList:
        # Watch out for blank fields in coding!
        if not isinstance(rec['idcode'],int) and \
               not isinstance(rec['idcode'],long): 
            util.logWarning("dropping record with no idcode")
            continue
        if rec['idcode'] <= 0:
            raise RuntimeError("Store IDCODE values must be positive; other values are reserved for special cases")

        # drop any records marked "disabled"
        if 'recdisabled' in rec:
            if rec['recdisabled']:
                continue
            
        code= rec['idcode']
        assert code>0, "Store IDCODE values must be positive"
        if code in storeRecDict:
            raise RuntimeError("Duplicate warehouse code %d"%code)
        storeRecDict[code]= rec
    
    # Some reality checks on the routes file
    for k in ['Type','RouteName','idcode','RouteOrder','TransitHours']:
        if not k in routeKeys:
            raise RuntimeError("Route file is missing required key %s"%k)
    
    routeDict= {} # entries to be indexed by route name
    for rec in routeRecList:
        # Some reality checks on the record
        ### this is where we would put some logic to check if the inputs are consistent - STB
        for k in ['ShipIntervalDays','ShipLatencyDays','PullMeanOrderAmount']:
            if k in rec:
                if isinstance(rec[k], types.StringTypes) and len(rec[k])==0:
                    del rec[k]
                elif not(type(rec[k]) in [types.IntType, types.LongType, types.FloatType]):
                    raise RuntimeError("In routes file, column %s must be a number"%k)
        for k in ['idcode','RouteOrder','TransitHours']:
            if k in rec:
                if isinstance(rec[k], types.StringTypes) and len(rec[k])==0:
                    rec[k]= 0L
                elif not(type(rec[k]) in [types.IntType, types.LongType, types.FloatType]):
                    raise RuntimeError("In routes file, column %s must be a number"%k)
        
        rec['idcode']= long(rec['idcode'])
        if not rec['idcode'] in storeRecDict:
            raise RuntimeError("In routes file, route %s references warehouse with non-existent idcode %ld"%\
                               (rec['RouteName'],rec['idcode']))
        routeName= rec['RouteName']
        if not 'TruckType' in rec or len(rec['TruckType'])==0:
            rec['TruckType']= 'default'
        if not routeName in routeDict:
            routeDict[routeName]= []
        routeDict[routeName].append( (rec['RouteOrder'],rec) )

    # Make sure route delivery order is correct
    for routeName in routeDict:
        l= routeDict[routeName]
        l.sort()
        routeDict[routeName]= [infoRec for o,infoRec in l] # @UnusedVariable

    # Check routes for consistency of type and sequence number
    for routeName,l in routeDict.items():
        if len(l)<2: raise RuntimeError("Route %s has only one stop"%routeName)
        seq= None
        for infoRec in l:
            if infoRec['RouteOrder']==seq:
                raise RuntimeError('Route %s has multiple stops at RouteOrder %s'%\
                                   (routeName,seq))
            seq= infoRec['RouteOrder']
        typeList= [r['Type'] for r in l]
        if not all([t==typeList[0] for t in typeList]):
            raise RuntimeError('Type information is inconsistent for route %s'%routeName)
        if typeList[0] in ['pull','attached','demandfetch','persistentpull','persistentdemandfetch'] and len(l)!=2:
            raise RuntimeError('Route %s is of type %s and so must have exactly two stops'%\
                               (routeName,typeList[0]))
            
    # But wait!  Store records for which no route was defined may get a default routing.  Find those
    # records and check.  We will only try to do this backwards-compatible deprecated feature if
    # the unconnected warehouse is expected to be a Clinic.
    for routeName,l in routeDict.items():
        for infoRec in l[1:]:
            storeRecDict[infoRec['idcode']]['_hasSupplier'] = True
        storeRecDict[l[0]['idcode']]['_hasClient'] = True
        
    storeDict= {}
    allShippingProcs= []
    shippingProcDict= {}

    for idcode,storeRec in storeRecDict.items():
        if not '_hasSupplier' in storeRec and not '_hasClient' in storeRec: 
            # Finding the supplier requires calling model.getDefaultSupplier(storeDict,idcode),
            # but we don't yet have storeDict.  Backward compatibility sucks.  No existing model
            # actually uses the storeDict parameter, so we'll try to get away with the following.
            supplierID = None
            wh = None
            try:
                wh= warehouseFromRec(sim, storeRecDict[idcode], expectedType=warehouse.Clinic)
                if wh is not None and not isinstance(wh, warehouse.Clinic):
                    raise RuntimeError("%s(%ld) was expected to be some kind of Clinic"%(wh.bName,idcode))
            except Exception,e:
                import traceback
                traceback.print_exc()
                raise RuntimeError("Unable to build routeless store %s(%ld): %s"%(storeRec['NAME'],idcode,e))
            try:
                storeDict[idcode]= wh
                if wh is not None: 
                    supplierID = getDefaultSupplier(storeDict, idcode)
                    wh.code = idcode
                    AddPowerCutInfo(sim, wh, sim.userInput, storeRecDict[idcode])
                if supplierID is not None:
                    if isinstance(wh, warehouse.AttachedClinic):
                        routeName= "implicit_attached_%ld"%idcode
                        supplierRec= storeRecDict[supplierID]
                        routeRec0= {'RouteName':routeName, 'Type':'attached', 'LocName':supplierRec['NAME'], 'idcode':supplierID, 'RouteOrder':0}
                        routeRec1= {'RouteName':routeName, 'Type':'attached', 'LocName':storeRec['NAME'], 'idcode':idcode, 'RouteOrder':1}
                        routeDict[routeName]= [routeRec0, routeRec1]
                    else:
                        routeName= "rdefault_%ld_%ld"%(supplierID,idcode)
                        supplierRec= storeRecDict[supplierID]
                        routeRec0= {'RouteName':routeName, 'Type':'pull', 'LocName':supplierRec['NAME'], 'idcode':supplierID, 'RouteOrder':0}
                        routeRec1= {'RouteName':routeName, 'Type':'pull', 'LocName':storeRec['NAME'], 'idcode':idcode, 'RouteOrder':1}
                        routeRec0['TruckType'] = routeRec1['TruckType'] = getDefaultTruckTypeName(None, wh)
                        routeRec0['ShipIntervalDays'] = routeRec1['ShipIntervalDays'] = getDefaultTruckInterval(None,wh)
                        routeRec0['ShipLatencyDays'] = routeRec1['ShipLatencyDays'] = getStartupLatency(storeDict,supplierID)
                        routeRec0['PullOrderAmountDays'] = routeRec1['PullOrderAmountDays'] = getDefaultPullMeanFrequency(storeDict,idcode)
                        routeRec0['TransitHours'] = routeRec1['TransitHours'] = 24.0
                        routeDict[routeName]= [routeRec0, routeRec1]
                    print \
"""
This model includes an implied %s link between %s(%ld) and %s(%ld).
The use of implied links is DEPRECATED and unreliable, and will not be supported in the future.
"""%(routeRec0['Type'],supplierRec['NAME'],supplierID,wh.bName,idcode)
            except Exception,e:
                print "Unable to check for implied suppliers for %s(%ld) : %s"%(storeRec['NAME'],idcode,e)
        
    # To determine node types, we need client and supplier counts for the nodes.
    clientDict= {}   # Entries are [ (clientID,routeType),... ] indexed by supplierID
    supplierDict= {} # Entries are [ (supplierID,routeType),... ] indexed by clientID
    for routeName, locList in routeDict.items():
        supplierOffset = supplierOffsetByRouteType[locList[0]['Type']] # already checked that types all match
        supplierRec= locList[supplierOffset]
        supplierID= long(supplierRec['idcode'])
        routeType= supplierRec['Type']
        if not supplierID in clientDict: clientDict[supplierID]= []
        for r in locList[:supplierOffset]+locList[supplierOffset+1:]:
            clientID= long(r['idcode'])
            #netDict[supplierID].append((clientID,routeType))
            if not clientID in supplierDict: supplierDict[clientID]= []
            supplierDict[clientID].append((supplierID,routeType))
            clientDict[supplierID].append((clientID,routeType))
    
    # Now we construct the shipping chains!
    for routeName,l in routeDict.items():
        routeType= l[0]['Type']

        # Build nodes if necessary
        for routeStopRec in l:
            idcode= long(routeStopRec['idcode'])
            if idcode in clientDict: nClients= len(clientDict[idcode])
            else: nClients= 0
            if idcode in supplierDict: nSuppliers= len(supplierDict[idcode])
            else: nSuppiers= 0
            
            expectedType= None
            #print "%s %d: %d %d"%(routeStopRec['RouteName'],idcode,nClients,nSuppliers)
            if nClients==0:
                if nSuppliers==0:
                    # This is always a clinic.  It might have no suppliers and still be valid, as
                    # a factory could get connected to it directly.
                    expectedType= warehouse.Clinic
                else:
                    # This could be a Clinic or an AttachedClinic, depending on the route type.
                    if routeType=='attached':
                        expectedType= warehouse.AttachedClinic
                    else:
                        expectedType= warehouse.Clinic
            else:
                # Something is downstream, so this must be a Warehouse.
                expectedType= warehouse.Warehouse
    
            if idcode in storeDict:
                wh= storeDict[idcode]
                assert wh is None or isinstance(wh,expectedType), \
                    "Internal error resolving type of warehouse for idcode %ld: %s when expecting %s"%\
                    (idcode,type(wh),expectedType)
            else:
                wh= warehouseFromRec(sim, storeRecDict[idcode], expectedType=expectedType)
                storeDict[idcode]= wh 
                assert wh is None or isinstance(wh,expectedType), \
                    "Internal error: model produced the wrong type of warehouse for idcode %ld: %s when expecting %s"%\
                    (idcode, type(wh), expectedType)
                # warehouseFromRec can return None in the case of a 'dead' warehouse.
                if wh is not None:
                    wh.code = idcode
                    AddPowerCutInfo(sim, wh, sim.userInput, storeRecDict[idcode])
                    specifiedPopPC = sim.model.getPeopleCollectionFromTableRec(storeRecDict[idcode])
                    if wh.getPopServedPC() != specifiedPopPC:
                        shippingProcList = _addImplicitAttachedClinic(storeRecDict[idcode], sim, storeDict, warehouseFromRec)
                        allShippingProcs += shippingProcList


        # Cache travel distances if provided
        startRec = csv_tools.CSVDict(l[0])
        startWh = lastWh = storeDict[long(startRec['idcode'])]
        conditions = _conditionsFromRec(startRec)
        km = startRec.safeGetFloat('DistanceKM',None)
        for routeStopRec in [csv_tools.CSVDict(r) for r in l[1:]]:
            wh = storeDict[long(routeStopRec['idcode'])]
            if km is not None:
                sim.geo.setKmBetween( lastWh, wh, km, lastWh.category, conditions )
            conditions = _conditionsFromRec(routeStopRec)
            km = routeStopRec.safeGetFloat('DistanceKM',None)
            lastWh = wh
        if km is not None:
            sim.geo.setKmBetween( lastWh, startWh, km, lastWh.category, conditions )

        # All the nodes in this route are now guaranteed to exist
        _genericRouteChecks(l,storeDict)
        shippingProcList = None 
        buildFuncDict= {'push':_buildPushRoute, 
                        'varpush':_buildVarPushRoute,
                        'pull':_buildPullRoute, 
                        'attached':_buildAttachedRoute,
                        'schedfetch':_buildScheduledFetchRoute,
                        'schedvarfetch':_buildScheduledVarFetchRoute,
                        'demandfetch':_buildDemandFetchRoute,
                        'askingpush':_buildAskingPushRoute,
                        'dropandcollect':_buildDropAndCollectRoute,
                        'persistentpull':_buildPersistentPullRoute,
                        'persistentdemandfetch':_buildPersistentDemandFetchRoute
                        }
        if routeType in buildFuncDict:
            shippingProcList = buildFuncDict[routeType](routeName, sim, l, storeDict,
                                                        getShipInterval, getStartupLatency, getTruckInterval, 
                                                        getPullControlFuncs, getPullMeanFrequency,
                                                        getOrderPendingLifetime)
            allShippingProcs += shippingProcList
        else:
            raise RuntimeError('Route %s is of unknown type %s'%(routeName,routeType))

        shippingProcDict[routeName] = shippingProcList

    # Insert these nodes into the reporting hierarchies
    shippingTreeReportingHierarchyDict= {}
    byCategoryReportingHierarchyDict= {}
    parentRHN = None
    for idcode, wh in storeDict.items():
        if wh is None: continue
        elif idcode <= 0: continue # an implicit attached clinic or other invisible special case
        category = storeRecDict[idcode]['CATEGORY']
        elaboratedName = "%s(%ld)"%(wh.bName,idcode)
        if category not in byCategoryReportingHierarchyDict:
            byCategoryReportingHierarchyDict[category] = ReportingHierarchyNode('all', category,
                                        overrides={'LaborCost':sim.costManager.getOverrideTotal,
                                                   })
        nh= wh.getNoteHolder()
        if nh is not None: 
            rhn= ReportingHierarchyNode(category, "%s(%ld)"%(nh['name'],idcode), [nh])
            byCategoryReportingHierarchyDict[category].add( rhn )

    for routeName, l in routeDict.items():
        shippingProcList= shippingProcDict[routeName]
        startingID= l[0]['idcode']
        perDiemName = _perDiemNameFromRec(l[0])
        category= storeRecDict[startingID]['CATEGORY']
        for p in shippingProcList: 
            if hasattr(p,'getNoteHolder'): 
                nh = p.getNoteHolder()
                if nh is not None: 
                    nh.addNote({'category':category})
                    rhn= ReportingHierarchyNode(category, nh['RouteName'], [nh])
                    byCategoryReportingHierarchyDict[category].add( rhn )
            if hasattr(p,'setPerDiemModel'):
                p.setPerDiemModel(sim.costManager.getPerDiemModel(perDiemName))

    byCategoryTopRHN = ReportingHierarchyNode('-top-','all',byCategoryReportingHierarchyDict.values(),
                                        overrides={'InventoryChangeCost':sim.costManager.getOverrideTotal
                                                   })
    shippingTreeTopRHNList = []
    for rhn in shippingTreeReportingHierarchyDict.values():
        if rhn.parent is None: shippingTreeTopRHNList.append(rhn)
    allTopRHNs = shippingTreeTopRHNList + [byCategoryTopRHN]   
    
    return storeDict, allShippingProcs, allTopRHNs


def finishBuild(storeDict,allShippingProcs,getScheduledShipmentSize):
    """
    The input should be a fully connected distribution network in the form
    of a dictionary of all warehouses and a list of all shipping processes.
    This routine completes warehouse initialization tasks that cannot be
    carried out until the shipping processes have been defined, and vice 
    versa.  getScheduledShipmentSize has the signature:
    
    vaccineCollection= getScheduledShipmentSize(fromWarehouse,toWarehouse,
                                                shipInterval)

    """
    for wh in storeDict.values():
        if wh is not None:
            wh.finishBuild()
    for shipProc in allShippingProcs:
        shipProc.finishBuild(getScheduledShipmentSize)

def realityCheck(sim):
    """
    The input should be a ready-to-run instance of hermes.HermesSim .
    Simple reality checks are performed to look for the sorts of errors that can 
    arise due to problems in the input tables.
    """

    inputList= []
    warningMessages= []
    fatalMessages= []

    # Look for orphans and warehouses with no cooled storage; find
    # stores connected to factories.

    for code,wh in sim.storeDict.items():
        if wh is None: continue      # dead warehouse
        if len(wh.getSuppliers())==0:
            directPopServed= wh.getPopServedPC()
            if directPopServed.totalCount()>0:
                fatalMessages.append("%s %ld has %s direct clients and no suppliers"%\
                                     (wh,code,wh.getPopServedPC()))
        else:
            for s in wh.getSuppliers():
                if isinstance(s[0],warehouse.Factory):
                    inputList.append((wh,code))
                    break
            if wh.getPopServedPC().totalCount()>0:
                totStorageVol= 0.0
                for sb in wh.getStorageBlocks():
                    if sb.storageType != sim.storage.discardStorage():
                        totStorageVol += sb.volAvail
                if totStorageVol==0.0:
                    warningMessages.append("%s %d is active but has no storage"%(wh.bName,code))
                    sim.outputfile.write("%s %ld: %s\n"%(wh.bName,code,wh.getStorageBlocks()))

                    
    if len(inputList)>1 and len(inputList)>0.2*len(sim.storeDict):
        fatalMessages.append("There are %d factories, which is implausible."%\
                             len(inputList))

    for topTierWH,topCode in inputList:
        nTotWh,whTierDict,popTierDict= \
             topTierWH.getTotalDownstreamClientsByTier()
        sim.outputfile.write("Top tier warehouse %s %ld serves %d clients including itself:\n"%\
                             (topTierWH.bName,topCode,nTotWh))
        offset= 0
        topPop= popTierDict[0]
        while whTierDict.has_key(offset):
            sim.outputfile.write("    Tier %d: %d warehouses, %s total population served\n"%\
                                 (offset,whTierDict[offset],popTierDict[offset]))
            # Now that population totals are at least sometimes computed recursively,
            # the following test makes no sense.
            #if popTierDict[offset]!=topPop:
            #    warningMessages.append("Tier %d below %s %ld has the wrong "\
            #                           %(offset,topTierWH.bName,topCode)
            #                           +"total client count")

            offset += 1
            
    if len(warningMessages)>0:
        sim.outputfile.write("%d Warnings:\n"%(len(warningMessages)))
        for m in warningMessages: sim.outputfile.write(m+'\n')
    if len(fatalMessages)>0:
        sim.outputfile.write("%d Fatal Problems:\n"%(len(fatalMessages)))
        for m in fatalMessages: sim.outputfile.write(m+'\n')
        raise RuntimeError("Fatal problems with network during reality check")
            

def _GetDelayInfo(userInput, rec, sim):
    delayInfo= DelayInfo(userInput, rec, sim)
    if delayInfo.valid(): return delayInfo
    else: return None

