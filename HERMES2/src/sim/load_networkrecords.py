#! /usr/bin/env python



_hermes_svn_id_="$Id$"

import util
import csv_tools
import csv_overlays

def readNetworkRecords(userInput):
    """
    read in any stores and routes csv files based on the userInput structure.

    returns (storeKeys, storeRecList, routeKeys, routeRecList, factoryKeys, factoryRecList)
    """
    with util.logContext("reading routes CSV"):
        with util.openDataFullPath(userInput['routesfile'],"rb") as RoutesFileHandle:
            routeKeys, routeRecList= csv_tools.parseCSV(RoutesFileHandle)
        if userInput['routesoverlayfiles'] is not None:
            (routeKeys, routeRecList) = \
                csv_overlays.parseOverlayCSV(routeKeys,
                                             routeRecList,
                                             ('RouteName','RouteOrder'),
                                             userInput['routesoverlayfiles'])
                # I don't know of anything to use for secondary keys
        for col in ['RouteName','LocName']:
            csv_tools.castColumn(routeRecList,col, [csv_tools.castTypes.STRING])


    with util.logContext("reading stores CSV"):
        with util.openDataFullPath(userInput['storesfile'],"rb") as StoresFileHandle:
            storeKeys, storeRecList= csv_tools.parseCSV(StoresFileHandle)
        if userInput['storesoverlayfiles'] is not None:
            (storeKeys, storeRecList) = \
                csv_overlays.parseOverlayCSV(storeKeys, 
                                             storeRecList, 
                                             'idcode', 
                                             userInput['storesoverlayfiles'],
                                             'CATEGORY')
        csv_tools.castColumn(storeRecList,'NAME',[csv_tools.castTypes.STRING])
    if userInput['factoryfile'] is None:
        factoryKeys = None
        factoryRecList = None
    else:
        with util.logContext("reading factory CSV"):
            with util.openDataFullPath(userInput['factoryfile'], "rb") as FactoryFileHandle:
                factoryKeys, factoryRecList = csv_tools.parseCSV(FactoryFileHandle)
    
    if userInput['tripmanifestfile'] is None:
        tripManifestKeys = None
        tripManifestRecList = None
    else:
        with util.logContext("reading trip manifest CSV"):
            with util.openDataFullPath(userInput['tripmanifestfile'],"rb") as TripManFileHandle:
                tripManifestKeys,tripManifestRecList = csv_tools.parseCSV(TripManFileHandle)
    
    return (storeKeys, storeRecList, routeKeys, routeRecList, factoryKeys, factoryRecList, tripManifestKeys, tripManifestRecList)

