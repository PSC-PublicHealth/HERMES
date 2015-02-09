#!/usr/bin/env python

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


__doc__=""" main.py of the program HERMES
This tool takes a 'stores' table in .csv format and constructs
an all-push route table from it, using default rules.
"""

_hermes_svn_id_="$Id$"

import sys,os,getopt,types
from random import *

import constants as C
import csv_tools, warehouse, vaccinetypes, storagetypes, util

##############
# Notes-
##############

class G:
    verbose= False
    debug= False
    
    warehouseFile= None
    routeFile= None

    # We need some vaccine and storage info to initialize the warhouses
    storageUtilFactor= [1.0,1.0,1.0,1.0]
    wastage= [1.0,1.0,1.0,1.0]
    vaccinePresentationsFile = "UnifiedVaccineTypeInfo.csv"
    activeVaccineTypes= [ "DTP" ]
    vaccinetypes.initialize(vaccinePresentationsFile)
    vaccineTypes= [vaccinetypes.getVaccineTypeByName(name)
                   for name in activeVaccineTypes]
    storageTypes= storagetypes.storageTypes
    lotsOfSpace= 1000000000.0; # used for room temp storage

    

def getShipIntervalFromSupplierCode(code):
    regionCode,districtCode,clinicCode= code
    if regionCode==0:
        # supplier is central store
        return G.centralStoreShipInterval
    elif districtCode==0:
        # supplier is a region
        return G.regionalStoreShippingInterval
    elif clinicCode==0:
        return G.districtStoreShippingInterval
    else:
        raise RuntimeError("Scheduled shipments originating from clinics are not supported.")
    return None

def warehouseOrClinicFromRec(rec,recordTheseStoresDict):
    "This is just for convenience"
    #print "building warehouse %s: %s %s %s"%(rec['NAME'],rec['Region code'],
    #                                         rec['District code'],
    #                                         rec['Clinic code'])
    name= rec['NAME']
    #name= "%s_%s_%s_%s"%(rec['NAME'],rec['Region code'],
    #                     rec['District code'],
    #                     rec['Clinic code'])
    print recordTheseStoresDict.keys()
    if recordTheseStoresDict.has_key('all'):
        monitorName= "%s_%s_%s_%s"%(rec['NAME'],rec['Region code'],
                                    rec['District code'],
                                    rec['Clinic code'])
        recorder= getRecorderFromRecorderType(recordTheseStoresDict[name],
                                              monitorName)
        #print "Monitoring %s with %s!\n"%(monitorName,recordTheseStoresDict[name])
    else:
        recorder= None
        
    #For Niger
    if rec['Region code'] == 0:
        sUF = G.storageUtilFactor[0]
        wastage = G.wastage[0]
    elif rec['District code'] == 0:
        sUF = G.storageUtilFactor[1]
        wastage = G.wastage[1]
    elif rec['Clinic code'] == 0:
        sUF = G.storageUtilFactor[2]
        wastage = G.wastage[2]
    else:
        sUF = G.storageUtilFactor[3]
        wastage = G.wastage[3]

##    #For Niger - no regional level
##     #Raise runtimeerror if len(wastage) , len(storageUtilFactor) != 3
##    if rec['District code'] == 0:
##        sUF = G.storageUtilFactor[0]
##        wastage = G.wastage[0]
##    elif rec['Clinic code'] == 0:
##        sUF = G.storageUtilFactor[1]
##        wastage = G.wastage[1]
##    else:
##        sUF = G.storageUtilFactor[2]
##        wastage = G.wastage[2]
    
    if rec['Clinic code']==0:
        return warehouse.Warehouse(G.vaccineTypes,
                                   G.storageTypes,
                                   [('freezer',
                                     C.ccPerLiter*sUF*(rec['Walk in -(lit)'] + \
                                                       rec['VOL - (lit)'])),
                                    ('cooler',
                                     C.ccPerLiter*sUF*(rec['Walk in +(lit)'] + \
                                                       rec['VOL + (lit)'])),
                                    ('roomtemperature',G.lotsOfSpace)],
                                   rec['Target Population'],
                                   name,recorder,wastage)
    else:
        return warehouse.Clinic(G.vaccineTypes,
                                G.storageTypes,
                                [('freezer',
                                  # Clinics are never to use the freezer!
                                  #C.ccPerLiter*(rec['Walk in -(lit)'] + \
                                  #              rec['VOL - (lit)'])
                                  0.0
                                  ),
                                 ('cooler',
                                  C.ccPerLiter*sUF*(rec['Walk in +(lit)'] + \
                                                    rec['VOL + (lit)'])),
                                 ('roomtemperature',G.lotsOfSpace)],
                                int(0.7*rec['Target Population']),
                                name,recorder,wastage)

###########
# main
###########

def main():

    try:
        (opts,pargs) = getopt.getopt(sys.argv[1:],"vd",[])
    except:
        sys.exit("%s: Invalid command line parameter" % sys.argv[0])

    recordTheseStoresDict= {}
    trackThisVial= None

    # Parse args
    for a,b in opts:
        if a=="-v":
            G.verbose= True
        if a=="-d":
            G.debug= True

    if len(pargs)!=2:
        sys.exit("usage: %s storeFile.csv routeFileOut.csv")

    G.warehouseFile= pargs[0]
    G.routeFile= pargs[1]

    #------------------
    # Create the network
    #------------------

    chainDict= {}
    topSum=0
    regionSum= 0
    districtSum= 0
    clinicSum= 0

    #------------------
    # Stage 1: load the warehouse/clinic description file and instantiate
    # the warehouses and clinics.
    #------------------
    
    with openDataFullPath(G.warehouseFile) as f:
        keys, storeDictList= csv_tools.parseCSV(f)

    #print keys
    storeDict= {}
    for rec in storeDictList:
        # Watch out for blank fields in coding!
        for k in ['Region code', 'District code', 'Clinic code']:
            if not isinstance(rec[k],int): 
                rec[k]= 0
        regionCode= rec['Region code']
        districtCode= rec['District code']
        clinicCode= rec['Clinic code']
        keyTuple= (regionCode,districtCode,clinicCode)
        wh= warehouseOrClinicFromRec(rec,recordTheseStoresDict)
        storeDict[keyTuple]= (wh, wh.popServed)

    #------------------
    # Stage 2: Synthesize the route table.  We'll give each supplier
    #          a single outgoing route.
    #------------------

    routeDict= {}
    newLinkList= []
    for t in storeDict.keys():
        regionCode,districtCode,clinicCode= t
        wh,totalClients= storeDict[t]
        supplier= None

        if regionCode==0:
            # This is the central store, and it gets automatically attached
            # to a factory.  Thus we do nothing.
            print "Central Store <- (some factory)"
            pass

        elif districtCode==0:
            if len(wh.suppliers) == 0:
                #supplier= (0,0,0)
                supplier= None

        elif clinicCode==0:
            if len(wh.suppliers) == 0:
                #supplier= (regionCode,0,0)
                supplier= (0,0,0)

        else:
            if len(wh.suppliers) == 0:
                #supplier= (regionCode,districtCode,0)
                supplier= None

        if supplier is not None:
            fromWh,junk= storeDict[supplier]
            wh.addSupplier(fromWh)
            fromWh.addClient(wh)
            if not routeDict.has_key(supplier):
                routeDict[supplier]= [(supplier,fromWh)]
            routeDict[supplier].append((t,wh))
            newLinkList.append((supplier,t))
            print "%s <- %s"%(wh.name, fromWh.name)

    #------------------
    # Stage 3: Generate and write out route table records
    #------------------

    currentRouteID= 1
    recList= []
    #for k,destList in routeDict.items():
    #     currentRouteName= "route%03d"%currentRouteID
    #     currentRouteOrder= 0
    #     for t,wh in destList:
    #         regionCode,districtCode,clinicCode= t
    #         # First dest is actually the supplier, numbered 0
    #         d= {}
    #         d['RouteName']= currentRouteName
    #         d['Type']= "push"
    #         d['LocName']= wh.name
    #         d['Region code']= regionCode
    #         d['District code']= districtCode
    #         d['Clinic code']= clinicCode
    #         d['RouteOrder']= currentRouteOrder
    #         d['TransitHours']= 1.0
    #         currentRouteOrder += 1
    #         recList.append(d)
    #     currentRouteID += 1

    for supplierCode,clientCode in newLinkList:
         currentRouteName= "route%03d"%currentRouteID
         dict= {}
         r,d,c= supplierCode
         w,junk= storeDict[supplierCode]
         dict['RouteName']= currentRouteName
         dict['Type']= "pull"
         dict['LocName']= w.name
         dict['Region code']= r
         dict['District code']= d
         dict['Clinic code']= c
         dict['RouteOrder']= 0
         recList.append(dict)
         dict= {}
         r,d,c= clientCode
         w,junk= storeDict[clientCode]
         dict['RouteName']= currentRouteName
         dict['Type']= "pull"
         dict['LocName']= w.name
         dict['Region code']= r
         dict['District code']= d
         dict['Clinic code']= c
         dict['RouteOrder']= 1
         dict['TransitHours']= 24.0
         recList.append(dict)
         currentRouteID += 1


    f= open(util.getDataFullPath(G.routeFile),"w")
    csv_tools.writeCSV(f,
                       ['RouteName', 'Type', 'LocName',
                        'Region code', 'District code', 'Clinic code',
                        'RouteOrder', 'TransitHours'],
                       recList, quoteStrings=True)
    f.close()
    print "### wrote %s ###"%G.routeFile

############
# Main hook
############

if __name__=="__main__":
    main()
