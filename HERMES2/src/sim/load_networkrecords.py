#! /usr/bin/env python

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
    if userInput['factoryfile'] is None:
        factoryKeys = None
        factoryRecList = None
    else:
        with util.logContext("reading factory CVS"):
            with util.openDataFullPath(userInput['factoryfile'], "rb") as FactoryFileHandle:
                factoryKeys, factoryRecList = csv_tools.parseCSV(FactoryFileHandle)
    
    
    return (storeKeys, storeRecList, routeKeys, routeRecList, factoryKeys, factoryRecList)

