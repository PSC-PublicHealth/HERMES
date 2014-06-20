#! /usr/bin/env python

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

__doc__=""" main.py
This is a utility to create Store and Routes files.  Just the shell of a
utility, actually.
"""
_hermes_svn_id_="$Id$"

import sys,os,optparse,types

import csv_tools

def makeStoreAndRouteRecs(inRec, storeKeys, routeKeys):
    """
    This should return a list of Store records (which are dictionaries) for the given store name
    """
    storeRecList = []
    routeRecList = []
    
    # Unpack the info about this PHC
    phcName = inRec['Names of PHCs']
    idcode = inRec['ID codes']
    nPerDay = inRec['No. outreach sites visited in a day']
    loopsPerDay = inRec['No. of loops per day']
    sitesInEachLoop = inRec['No. of sites in each loop']

    newStoreCounter = 1 # to help build idcodes of the created stores
    clientTuples = []
    
    # Make the store record for the PHC itself
    phcRec = { 'CATEGORY':'PHC', 'FUNCTION':'Distribution', 'NAME':phcName, 'idcode':idcode}
    storeRecList.append(phcRec)
    # Make the store record for the attached clinic
    attachedClinicName = phcName+'_clinic'
    attachedClinicId = (10000000*newStoreCounter)+idcode
    attachedRec = { 'CATEGORY':'PHC', 'FUNCTION':'Administration', 'NAME':attachedClinicName, 
                   'idcode':attachedClinicId}
    storeRecList.append(attachedRec)
    newStoreCounter += 1
    
    # make the nPerDay new outreach sites
    for i in xrange(nPerDay):
        orIdcode = (10000000*newStoreCounter)+idcode
        orName = "%s_outreach%d"%(phcName,i+1)
        orRec = { 'CATEGORY':'Clinic', 'FUNCTION':'Outreach', 'NAME':orName,'idcode':orIdcode }
        storeRecList.append(orRec)
        newStoreCounter += 1
        clientTuples.append((orName, orIdcode))

    # generate the 'attached' loop for the attached clinic
    routeName = "r_%d_attached"%idcode
    startRec = {'RouteName':routeName, 'idcode':idcode, 'LocName':phcName, 'CATEGORY':'PHC', 'Type':'attached',
                'RouteOrder':0, 'TransitHours':'', 'TruckType':'',
                'ShipIntervalDays':'', 'ShipLatencyDays':'', 'PullOrderAmountDays':'', 'Notes':'', 'DistanceKM':''}
    routeRecList.append(startRec)
    stopRec =  {'RouteName':routeName, 'idcode':attachedClinicId, 'LocName':attachedClinicName, 'CATEGORY':'PHC', 'Type':'attached',
                'RouteOrder':1, 'TransitHours':'', 'TruckType':'',
                'ShipIntervalDays':'', 'ShipLatencyDays':'', 'PullOrderAmountDays':'', 'Notes':'', 'DistanceKM':''}
    routeRecList.append(stopRec)

    # generate the loops
    stopsPerLoopList = map(int,str(sitesInEachLoop).split('.'))
    assert len(stopsPerLoopList) == loopsPerDay, 'Loop sizes %s does not give %d sizes'%(sitesInEachLoop,loopsPerDay)
    assert sum(stopsPerLoopList) == nPerDay, 'Loop sizes %s do not make %d sites'%(stopsPerLoopList,nPerDay)
    startOffset = 0
    for loop in xrange(loopsPerDay):
        nThisLoop = stopsPerLoopList[loop]
        routeOrder = 0
        loopStopTuples = clientTuples[startOffset:startOffset+nThisLoop]
        startOffset += nThisLoop
        routeName = "r_%s_or%d"%(phcName,loop+1)
        stopRec = { 'RouteName':routeName, 'idcode':idcode, 'LocName':phcName, 'CATEGORY':'PHC',
                   'Type':'dropandcollect','RouteOrder':routeOrder, 'TransitHours':1, 'TruckType':'I_TwoWheeler',
                   'ShipIntervalDays':3, 'ShipLatencyDays':6, 'PullOrderAmountDays':'', 'Notes':'', 'DistanceKM':''}
        routeOrder += 1
        routeRecList.append(stopRec)
        
        for nm, stopId in loopStopTuples:
            stopRec = { 'RouteName':routeName, 'idcode':stopId, 'LocName':nm, 'CATEGORY':'Clinic',
                       'Type':'dropandcollect','RouteOrder':routeOrder, 'TransitHours':1, 'TruckType':'I_TwoWheeler',
                       'ShipIntervalDays':3, 'ShipLatencyDays':6, 'PullOrderAmountDays':'', 'Notes':'', 'DistanceKM':''}
            routeOrder += 1
            routeRecList.append(stopRec)
        loopStopTuples.reverse() # For the return trip
        for index,tpl in enumerate(loopStopTuples):
            nm, stopId = tpl
            if index == 0 : transitHours = 8 # driver takes a nap
            else: transitHours = 1
            stopRec = { 'RouteName':routeName, 'idcode':stopId, 'LocName':nm, 'CATEGORY':'Clinic',
                       'Type':'dropandcollect','RouteOrder':routeOrder, 'TransitHours':transitHours, 'TruckType':'I_TwoWheeler',
                       'ShipIntervalDays':3, 'ShipLatencyDays':6, 'PullOrderAmountDays':'', 'Notes':'', 'DistanceKM':''}
            routeOrder += 1
            routeRecList.append(stopRec)
    
    return storeRecList, routeRecList

def checkRecs(recList, keys, note):
    for rec in recList:
        for k in keys:
            if k not in rec:
                sys.exit("%s: %s"%(note,k))

def main():
    verbose= False
    debug= False
    storeProtoFname = None
    routeProtoFname = None
    
    parser= optparse.OptionParser(usage="""
    %%prog --storeproto sp.csv --routeproto rp.csv names.csv
    
    names.csv is a csv file containing the records that will get processed to
    produce the outputs. Each record of this file may produce many records in
    the output stores and routes files. sp.csv and rp.csv are prototypes for the
    Stores and Routes files; they are used only to get the column names.
    
    The files stores_out.csv and routes_out.csv will be written.
    """)
    parser.add_option("-v","--verbose",action="store_true",help="verbose output")
    parser.add_option("-d","--debug",action="store_true",help="debugging output")
    parser.add_option("--storeproto",help="The output Stores file should look like this")
    parser.add_option("--routeproto",help="The output Routes file should look like this")

    opts,args= parser.parse_args()

    if len(args)!=1:
        parser.error("Found %d arguments, expected 1"%len(args))
    if opts.storeproto is None:
        parser.error("Required option --storeproto is missing")
    else:
        storeProtoFname = opts.storeproto
    if opts.routeproto is None:
        parser.error("Required option --routeproto is missing")
    else:
        routeProtoFname = opts.routeproto

    # Parse args
    if opts.verbose:
        verbose= True
        csv_tools.verbose= True
    if opts.debug:
        debug= True
        csv_tools.debug= True
    
    # Clean up command line parser
    parser.destroy()

    with open(storeProtoFname,"rU") as f:
        storeKeys, protoStoreRecs = csv_tools.parseCSV(f)
    with open(routeProtoFname,"rU") as f:
        routeKeys, protoRouteRecs = csv_tools.parseCSV(f)

    storeRecs = []
    routeRecs = []

    with open(args[0],'rU') as f:
        inputKeys, inputRecs = csv_tools.parseCSV(f)
        
    for rec in inputRecs:
        print rec
        newStoreRecs, newRouteRecs = makeStoreAndRouteRecs(rec, storeKeys, routeKeys)
        checkRecs(newStoreRecs, storeKeys, "No value is being set for this Store key")
        storeRecs += newStoreRecs
        checkRecs(newRouteRecs, routeKeys, "No value is being set for this Route key")
        routeRecs += newRouteRecs
            
    with open('stores_out.csv','w') as f:
        csv_tools.writeCSV(f, storeKeys, storeRecs)

    with open('routes_out.csv','w') as f:
        csv_tools.writeCSV(f, routeKeys, routeRecs)
        
############
# Main hook
############

if __name__=="__main__":
    main()
