_hermes_svn_id_="$Id$"

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

import util
import hermes
import csv_tools
import storagetypes
import math
import constants as C

def HermesGap(userInputList, unifiedInput, gblInputs,outputList, mergedOutput):
    hermes_orig = hermes.HermesSim(userInputList[0],unifiedInput,0)
    ## Create a Gap Report
    ## Populate replacement List
    replacementStorageKeyList = []
    replacementStorageRecList = []
    
    with util.openDataFullPath(userInputList[0]['gapstorefile'],"rU") as f:
        replacementStorageKeyList, replacementStorageRecList = csv_tools.parseCSV(f)
    
    #Dictionary with Levels as keys and storage devices as values
    replacementStorageDict = {}
    for rec in replacementStorageRecList:
        if not replacementStorageDict.has_key(rec['Level']):
            replacementStorageDict[rec['Level']] = []
        
        replacementStorageDict[rec['Level']].append(hermes_orig.fridges.getTypeByName(rec['Device']))
    
#    replacementTransportKeyList = []
#    replacementTransportRecList = []
#    
#    with util.openDataFullPath(userInputList[0]['gaptransportfile'],"rU") as f:
#        replacementTransportKeyList,replacementTransportRecList = csv_tools.parseCSV(f)
#    
#    replacementTransportDict = {}
#    """
#    Each route can at this point only have one option... will make more robust later
#    """
#    
#    for rec in replacementTransportRecList:
#        
#    #for fridgeCode in replacementStorageKeyList:
    
    storeKeyList = []
    storeRecList = []
    with util.openDataFullPath(userInputList[0]['storesfile'],"rU") as f:
        storeKeyList, storeRecList = csv_tools.parseCSV(f)

    storeGapDict = {}
    truckGapDict = {}

    outputFileRoot = userInputList[0]['outputfile']
    store_gap_file_name = outputFileRoot + "_storage_gap.csv"
    route_gap_file_name = outputFileRoot + "_transport_gap.csv"
    summaryGapFileName = outputFileRoot + "_gap_summary.csv"
    storefileStringList = userInputList[0]['storesfile'].split('.')[:1]
    storefileString = ""
    for sfs in storefileStringList:
	storefileString+=sfs
    newStoresFileName = storefileString + "_Fixed.csv"

    ### get the stockmonitorinterval so we know how to gauge time in histograms
    stockmonitorinterval_days = userInputList[0]['stockmonitorinterval']

    for store_code in mergedOutput.stores.keys():
        print "looking at store " + str(store_code)
        store_note = mergedOutput.stores[store_code]['note']
        if store_note is not None:
            ##go find this stores cooler_volume
            store_rec = None
            for store in storeRecList:
                if store['idcode'] == store_code:
                    store_rec = store
                    break
            if store_rec.has_key('FUNCTION') and store_rec['FUNCTION'] == 'Surrogate':
                print "This store is a Surrogate"
                continue
            
            sUF = 1.0
            if store_rec.has_key('Device Utilization Rate'):
                sUF = float(store_rec['Device Utilization Rate'])
            
            storageSpace = hermes_orig.model._storageSpaceFromTableRec(store_rec,sUF)
            #print str(storageSpace)
###!!!!!!   STB HACK to exclude PVSDs at higher levels from the gap analysis
            if(store_rec.has_key('FUNCTION') and store_rec['FUNCTION'] != "Administration"):
                for i in range(len(storageSpace)-1,-1,-1):
                    if str(storageSpace).find('PVSD')>=0:
                        del storageSpace[i]
            
            storageSC = hermes_orig.model._getTotalVolumeSC(storageSpace)
            #if userInputList[0]['debug']:
            print "Current Store: %s = %s"%(store['idcode'],str(storageSC))

            store_cooler_vol_cc  = hermes_orig.storage.getTotalCoolVol(storageSC)
            store_freezer_vol_cc = hermes_orig.storage.getTotalRefrigeratedVol(storageSC) - store_cooler_vol_cc

            store_cooler_vol_L  = store_cooler_vol_cc/C.ccPerLiter
            store_freezer_vol_L = store_freezer_vol_cc/C.ccPerLiter
            
            #Skip if it is an attached clinic
            if store_rec.has_key('FUNCTION') and store_rec['FUNCTION'] == "Administration":
                if store_cooler_vol_cc == 0.0 and store_freezer_vol_cc == 0.0:
                    continue
            #if userInputList[0]['debug']:
            print "Store Vols L: %10.2f %10.2f"%(store_cooler_vol_L,store_freezer_vol_L)

            cooler_volume_L = 0.0
            freezer_volume_L = 0.0
            if store_note.has_key('cooler_vol_used'):
                cooler_volume_L = store_note['cooler_vol_used'].max()#store_note['cooler_vol'].max()*store_note['cooler'].max()
            if store_note.has_key('freezer_vol_used'):
                freezer_volume_L = store_note['freezer_vol_used'].max()#store_note['freezer_vol'].max()*store_note['freezer'].max()
            #if userInputList[0]['debug']:
            print "Needed Vols L: %10.2f %10.2f"%(cooler_volume_L,freezer_volume_L)

            cooler_gap_L = cooler_volume_L - store_cooler_vol_L
            if cooler_gap_L < 0.0: cooler_gap_L = 0.0
            freezer_gap_L = freezer_volume_L - store_freezer_vol_L
            if freezer_gap_L < 0.0: freezer_gap_L = 0.0

            #if userInputList[0]['debug']:
            print "Gap Vol L: %10.2f %10.2f"%(cooler_gap_L,freezer_gap_L)

            cooler_time_over = store_note['gap_cooler_overstock_time']
            freezer_time_over = store_note['gap_freezer_overstock_time']
            #if userInputList[0]['debug']:
            print "Intervals Over %10f %10f"%(cooler_time_over.mean()*stockmonitorinterval_days,
                                              freezer_time_over.mean()*stockmonitorinterval_days)

            ### If there is a gap, figure out what to fill it with
            """
             Here is the rule....
              If only one device is specified, how ever many of those devices will be needed fill the gap.
              If more than one device is specified, then it goes:
                    the devices that can fill the gap with the least number of devices win
                    if multiple devices fit above, then the lowest volume device wins
            """
            gapCoolDeviceFllTuple = None
            gapFreezeDeviceFillTuple = None
            if(cooler_gap_L > 0.0):
                level = store_rec['CATEGORY']
                gapCoolDeviceFillTuple = fillStorageGap(store_rec,cooler_gap_L,"cooler",replacementStorageDict[level])
                if gapCoolDeviceFillTuple is None:
                    raise RuntimeError("No devices specified to fill the cooler gap at <%s,%s> Level: %s"%(store_rec['idcode'],store_rec['NAME'],level))
            else:
                gapCoolDeviceFillTuple = ("","")
                
            if(freezer_gap_L > 0.0):
                level = store_rec['CATEGORY']
                gapFreezeDeviceFillTuple = fillStorageGap(store_rec,freezer_gap_L,"freezer",replacementStorageDict[level])
                if gapFreezeDeviceFillTuple is None:
                        raise RuntimeError("No devices specified to fill the freezer gap at <%s,%s> Level: %s"%(store_rec['idcode'],store_rec['NAME'],level))
            else:
                gapFreezeDeviceFillTuple = ("","")
            
            
            # Combine the storage devices if there are duplication
#           if gapCoolDeviceFillTuple
            storeGapDict[str(store_code)] = (store_rec['NAME'],store_rec['CATEGORY'],cooler_gap_L,
                                       freezer_gap_L,cooler_time_over.mean()*stockmonitorinterval_days,
                                       freezer_time_over.mean()*stockmonitorinterval_days,gapCoolDeviceFillTuple,gapFreezeDeviceFillTuple)

    for routeName in mergedOutput.routes.keys():
        routeSupplyLevel = mergedOutput.routes[routeName]['supplier']['note']['category']
        routeNote = mergedOutput.routes[routeName]['note']
        if not routeNote.has_key('Route_L_vol_used_time'):
            continue

        routeVolumeL = routeNote['Route_L_vol_used_time'].max()
        routeTruck = routeNote['RouteTruckType']
        truckT = hermes_orig.typeManager.getTypeByName(routeTruck)

        storageSC = truckT.sim.fridges.getTotalVolumeSCFromFridgeTypeList(truckT.storageCapacityInfo)
        truckVolumeL = truckT.sim.storage.getTotalRefrigeratedVol(storageSC)/C.ccPerLiter
        routeVolumeGapL = routeVolumeL - truckVolumeL
        if routeVolumeGapL < 0.0: routeVolumeGapL = 0.0
        
        ## calculate the number of trucks needed to fill this gap
        trucksToFillGapL = None
        if routeVolumeGapL > 0.0:
            trucksToFillGapTuple  = (truckT,int(math.ceil(routeVolumeGapL/truckVolumeL)))
        else:
            trucksToFillGapTuple = ("","")
        
        if userInputList[0]['debug']:
            print "Truck Vols: %20s %10.2f %10.2f %10.2f"%(routeTruck,routeVolumeL,
                                                           truckVolumeL,routeVolumeGapL)

        routeTripsOver = None

        for output in [mergedOutput]:
            routeNoteOut = output.routes[routeName]['note']
        routeTripsOver = 0
        if routeNoteOut.has_key('gap_route_trip_over'):
            routeTripsOver = routeNoteOut['gap_route_trip_over']
        if userInputList[0]['debug']:    
            print "Trips Over %10.2f"%routeTripsOver.mean()

        truckGapDict[routeName] = (routeSupplyLevel,routeTruck,float(routeVolumeGapL),
                                    routeTripsOver,trucksToFillGapTuple)

    print "Writing Gap Analysis Output files ....."
    with util.openOutputFile(store_gap_file_name,"w") as f:
        f.write("ID, Name, Function, Refrid_Gap_L, Freezer_Gap_L, Refrid_Gap_Time_Days, Freezer_Gap_Time_Days, Refrid_Gap_Fill_Devices, Freezer_Gap_Fill_Devices\n")
        sortedKeyList = []
        for key in storeGapDict.keys():
            sortedKeyList.append(key)
        sortedKeyList.sort()
        for key in sortedKeyList:
            coolGapString = ""
            if storeGapDict[key][6][1] > 1 and storeGapDict[key][6][1] != "":
                coolGapString = str(storeGapDict[key][6][1]) + "*"
            
            coolGapString += str(storeGapDict[key][6][0])
            freezeGapString = ""
            if storeGapDict[key][7][1] > 1 and storeGapDict[key][7][1] != "":
                freezeGapString = str(storeGapDict[key][7][1]) + "*"
            
            freezeGapString += str(storeGapDict[key][7][0])
            
            
            f.write("%s,%s,%s,%10.2f,%10.2f,%10.2f,%10.2f,%s,%s\n"%(key,storeGapDict[key][0],
                                                                    storeGapDict[key][1],                                    
                                                                    storeGapDict[key][2], 
                                                                    storeGapDict[key][3], 
                                                                    storeGapDict[key][4],
                                                                    storeGapDict[key][5],
                                                                    coolGapString, freezeGapString))

    with util.openOutputFile(route_gap_file_name,"w") as f:
        f.write("ID,Level,TruckName,Gap_L,Gap_Over_Trips\n")
        sortedKeyList = []
        for key in truckGapDict.keys():
            sortedKeyList.append(key)
        sortedKeyList.sort()
        for key in sortedKeyList:
            truckGapString = ""
            if truckGapDict[key][4][1] > 1 and truckGapDict[key][4][1] != "":
                truckGapString = str(truckGapDict[key][4][1]) + "*"
            truckGapString += str(truckGapDict[key][4][0])
            
            f.write("%s,%s,%s,%10.2f,%10.0f,%s\n"%(key,truckGapDict[key][0],
                                                   truckGapDict[key][1], 
                                                   truckGapDict[key][2],
                                                   truckGapDict[key][3],
                                                   truckGapString))
     
    ## Create a Gap Summary File, similar to Sheng-I's 
    
    ## Storage, by level by device
    storageGapByLevelDict = {}
    for key in storeGapDict.keys():
        print "Key = " + str(key) + " entry: " + str(storeGapDict[key])
        level = storeGapDict[key][1]
        if key == "3":
            print "Level3 = " + level
        if not storageGapByLevelDict.has_key(level):
            storageGapByLevelDict[level] = {}
        if storeGapDict[key][6][1] > 0 and storeGapDict[key][6][1] != "":
            if not storageGapByLevelDict[level].has_key(storeGapDict[key][6][0]):
                storageGapByLevelDict[level][storeGapDict[key][6][0]] = 0
            storageGapByLevelDict[level][storeGapDict[key][6][0]] += storeGapDict[key][6][1]
            
        #if storeGapDict[key][7][1] > 1 and storeGapDict[key][7][1] != "":
        #    if not storageGapByLevelDict[level].has_key(storeGapDict[key][7][0]):
        #        storageGapByLevelDict[level][storeGapDict[key][7][0]] = 0
        #    storageGapByLevelDict[level][storeGapDict[key][7][0]] += storeGapDict[key][7][1]
    
    truckGapByLevelDict = {}
    for key in truckGapDict.keys():
        level = truckGapDict[key][0]
        if not truckGapByLevelDict.has_key(level):
            truckGapByLevelDict[level] = {}
        if truckGapDict[key][4][1] > 1 and truckGapDict[key][4][1] != "":
            if not truckGapByLevelDict[level].has_key(truckGapDict[key][4][0]):
                truckGapByLevelDict[level][truckGapDict[key][4][0]] = 0 
            truckGapByLevelDict[level][truckGapDict[key][4][0]] += truckGapDict[key][4][1]
    levelHigh = ["Central","National","SubNationl","Region","Province","Provencial","District","Clinic","Health Post","Health Center","Integrated Health Center"]
     
    print str(storageGapByLevelDict)   
    with util.openOutputFile(summaryGapFileName,"w") as f:
        f.write("Level,Device,NumberToAcquire\n")
        levelString = ""
        #for level in storageGapByLevelDict.keys():
        for level in levelHigh:
            if storageGapByLevelDict.has_key(level):
                levelString += level + ","
                if len(storageGapByLevelDict[level].keys())==0:
                    levelString += ",,\n"
                for device in storageGapByLevelDict[level].keys():
                    levelString += str(device)+ "," + str(storageGapByLevelDict[level][device]) + "\n,"
                levelString = levelString[:-2] + "\n"
        f.write("%s"%levelString)
    
        f.write("\n\n\n")
        f.write("Level, Transport, NumberToAcquire\n")
        levelString = ""
        for level in levelHigh:
            if truckGapByLevelDict.has_key(level):
                levelString += level + ","
                if len(truckGapByLevelDict[level].keys()) == 0:
                    levelString += ",,\n"
                for device in truckGapByLevelDict[level].keys():
                    levelString += str(device)+"," + str(truckGapByLevelDict[level][device]) + "\n,"
                levelString = levelString[:-2] + "\n"
        f.write("%s"%levelString)
    
### Create New Stores file based on the storage gap analysis

    with open(newStoresFileName,"wb") as f:
	headerString = ""
	for key in storeKeyList:
	    headerString += key + ","
	headerString = headerString[:-1]
	f.write("%s\n"%headerString)
	for rec in storeRecList:
	    #print 'Code = ' + str(rec['idcode'])
	    store_gap_rec = None
	    if str(rec["idcode"]) in storeGapDict.keys():
		store_gap_rec = storeGapDict[str(rec["idcode"])]
	    lineString = ""
	    for key in storeKeyList:
		if (key.lower() == "inventory" or key.lower() == "storage") and store_gap_rec is not None:
		    lineString += str(rec[key])
		    if store_gap_rec[6][1] != "":
			lineString += "+" + str(store_gap_rec[6][1]) + "*" + str(store_gap_rec[6][0])
		    if store_gap_rec[7][1] != "":
			lineString += "+" + str(store_gap_rec[7][1]) + "*" + str(store_gap_rec[7][0])
		    lineString += ","	
		else:
		    lineString += str(rec[key]) + ","
	    lineString = lineString[:-1]
	    f.write("%s\n"%lineString)
    
#    for key in truckGapDict.keys():
        
        
def fillStorageGap(wh_rec,gapInL,storageTypeString,devicesToChooseFrom):
    """
        Here is the rule....
        If only one device is specified, how ever many of those devices will be needed fill the gap.
        If more than one device is specified, then it goes:
                the devices that can fill the gap with the least number of devices win
                if multiple devices fit above, then the lowest volume device wins
    """
    gapDeviceInt = {}
    minimumCount = 999999
    for device in devicesToChooseFrom:
        devVolL = device.getTotalVolByName(storageTypeString)/1000.0
        if devVolL > 0.0:
            numberDevices = int(math.ceil(gapInL/devVolL))
            gapDeviceInt[device] = numberDevices
            if numberDevices < minimumCount:
                minimumCount = numberDevices
    
    if len(gapDeviceInt) == 0:
        return None
    
    minimumStorage = None
    for device in gapDeviceInt.keys():
        if gapDeviceInt[device] != minimumCount:
            gapDeviceInt.pop(device)
        else:
            if (minimumStorage is None) or (device.getTotalVolByName(storageTypeString) < minimumStorage.getTotalVolByName(storageTypeString)):
                minimumDevice = device
    
    
    print "( %s,%d)"%(str(minimumDevice),gapDeviceInt[minimumDevice])
    return (minimumDevice,gapDeviceInt[minimumDevice])
