#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id: infomration_dialog_box_hooks.py 1435 2013-09-12 18:31:51Z welling $"

import sys,os,os.path,time,json,math,types
import bottle
from sqlalchemy.exc import SQLAlchemyError
import ipath
import site_info
import shadow_network_db_api
import privs
import session_support_wrapper as session_support
import shadow_network
import util
from htmlgenerator import getStoreDialogHTML,getRouteDialogHTML
import model as M

from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
sI = site_info.SiteInfo()

inlizer=session_support.inlizer
_=session_support.translateString


### This route creates the Dialog box HTML and can easily be used with ajax 
### to define a dialog:  see veiws/dialogboxdemo.tpl for the example of how to use this.
@bottle.route('/json/dialoghtmlforstore')
def generateStoreDialogHTML(db,uiSession):
    try:
        boxName = _getOrThrowError(bottle.request.params,'name',isInt=False)
        genInfo = _safeGetReqParam(bottle.request.params,'geninfo',isBool=True,default=False)
        popInfo = _safeGetReqParam(bottle.request.params,'popinfo',isBool=True,default=False)
        utilInfo = _safeGetReqParam(bottle.request.params,'utilinfo',isBool=True,default=False)
        storeDev = _safeGetReqParam(bottle.request.params,'storedev',isBool=True,default=False)
        transDev = _safeGetReqParam(bottle.request.params,'transdev',isBool=True,default=False)
        vaccAvail = _safeGetReqParam(bottle.request.params,'vacavail',isBool=True,default=False)
        fillRatio = _safeGetReqParam(bottle.request.params,'fillratio',isBool=True,default=False)
        invent = _safeGetReqParam(bottle.request.params,'invent',isBool=True,default=False)
        availPlot = _safeGetReqParam(bottle.request.params,'availplot',isBool=True,default=False)
        htmlString = getStoreDialogHTML(db, uiSession, boxName,genInfo=genInfo,popInfo=popInfo,
                                        util=utilInfo,storeDev=storeDev,transDev=transDev,vaccAvail=vaccAvail,
                                        fillRatio=fillRatio,invent=invent,availPlot=availPlot)
        return {'success':True,'htmlString':htmlString}
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result
    
@bottle.route('/json/dialoghtmlforroute')
def generateRouteDialogHTML(db,uiSession):
    try:
        boxName = _getOrThrowError(bottle.request.params,'name',isInt=False)
        genInfo = _safeGetReqParam(bottle.request.params,'geninfo',isBool=True,default=False)
        utilInfo = _safeGetReqParam(bottle.request.params,'utilinfo',isBool=True,default=False)
        tripMan = _safeGetReqParam(bottle.request.params,'tripman',isBool=True,default=False)
        htmlString = getRouteDialogHTML(db, uiSession, boxName,genInfo=genInfo,util=utilInfo,tripMan=tripMan)
        return {'success':True,'htmlString':htmlString}
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result
### Route to demo page for testing and examples 
@bottle.route('/dialogdemo')
def dialogDemoPage(db,uiSession):
    modelId= _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
    storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
    routeId = _getOrThrowError(bottle.request.params,'routeId',isInt=False)
    return bottle.template('dialogboxdemo.tpl',{"breadcrumbPairs":[("top",_("Welcome"))],
                                            "pageHelpText":_("This is intended to show page-specific help")},
                                            _=_,inlizer=inlizer,modelId=modelId,storeId=storeId,routeId=routeId,resultsId=resultsId)
    


### The rest of these are a series of json helpers to get data to populate the dialog boxes.
@bottle.route('/json/get-general-info-for-store')   
def generateGeneralStoreInfoJson(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
        storeIdClean = storeId.replace("store_","")
        ### Check permissions
        uiSession.getPrivs().mayReadModelId(db,modelId)
    
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        store = model.getStore(int(storeIdClean))
    
        features = [_("Name"),"ID",_("Level")]
        values = [store.NAME,str(store.idcode),store.CATEGORY]
        
        if store.Latitude > 0.0:
            features.append(_("Latitude"))
            values.append(str(store.Latitude))
            features.append(_("Longitude"))
            values.append(str(store.Longitude))
        
        ### put 
        rows = []
        for feature in features:
            rows.append({"feature":feature,"value":values[features.index(feature)]})
        
        result = {'success':True, 
                  'rows':rows,
                  'total':1,
                  'page':1}
        return result
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result

@bottle.route('/json/get-storage-utilization-for-store')
def  generateUtilizationForStore(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
        resId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)  
         
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resId)
         
        storeIdClean = storeId.replace("store_","")
        print "getting store" + storeIdClean
        thisStore = m.getStore(int(storeIdClean))
        #print "getting result"
        thisStoreRes = r.storesRpts[thisStore.idcode]
        #print "not getting"
        rows = []
        rows.append({'info':_('Refrigerator (2-8 C) Storage'),'category':_('Total Volume (L)'),'value':thisStoreRes.storage['cooler'].vol})
        rows.append({'info':_('Refrigerator (2-8 C) Storage'),'category':_('Max Volume Used (L)'),'value':thisStoreRes.storage['cooler'].vol_used})
        rows.append({'info':_('Refrigerator (2-8 C) Storage'),'category':_('Max Utilization %'),'value':thisStoreRes.storage['cooler'].fillRatio*100.0})
        rows.append({'info':_('Freezer (below 0 C) Storage'),'category':_('Total Volume (L)'),'value':thisStoreRes.storage['freezer'].vol})
        rows.append({'info':_('Freezer (below 0 C) Storage'),'category':_('Max Volume Used (L)'),'value':thisStoreRes.storage['freezer'].vol_used})
        rows.append({'info':_('Freezer (below 0 C) Storage'),'category':_('Max Utilization %'),'value':thisStoreRes.storage['freezer'].fillRatio*100.0})
        result = {'success':True,
                  'rows':rows,
                  'total':1,
                  'page':1
                  }
        return result
   
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result
        

@bottle.route('/json/get-population-listing-for-store')
def generatePopulationListingForStore(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
        ### Check permissions
        uiSession.getPrivs().mayReadModelId(db,modelId)
        
        storeIdClean = storeId.replace("store_","")
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        thisStore = model.getStore(storeIdClean)
        
        ### Convert to Rest somehow
        excludeList = ['Service1']
        storeIdsToAdd = [thisStore.idcode]
        
        for client in thisStore.clients():
            if client[1].Type == "attached" and client[0].FUNCTION != "Surrogate":
                storeIdsToAdd.append(client[0].idcode)
        
        ### Get all attached clinics for this location
        #print str(storeIdsToAdd)
        peopleServedDict = {'all':{'displayName':_('Total Served'),'count':0}}
        for storeId in storeIdsToAdd:
            store = model.getStore(storeId)
            for demand in store.demand:
                if demand.invName not in excludeList:
                    if not peopleServedDict.has_key(demand.invName):
                        peopleServedDict[demand.invName] = {'count':0,
                                                            'displayName':demand.invType.getDisplayName()}
                    
                    peopleServedDict[demand.invName]['count']+= demand.count
                    peopleServedDict['all']['count'] += demand.count
        
        #print str(peopleServedDict)
        rows = []
        if peopleServedDict['all']['count'] == 0:
            rows.append({'class':_('Total Served'),'count':_('No Population Vaccinated at Location')})
        else:
            for psD in peopleServedDict.values():
                rows.append({'class':psD['displayName'],'count':psD['count']})
            
        results = {'success':True,
                   'total':1,
                   'page':1,
                   'rows':rows
                   }
        
        return results
    
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result
    
@bottle.route('/json/get-device-listing-for-store')
def generateDeviceListingForStore(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
        ### Check permissions
        uiSession.getPrivs().mayReadModelId(db,modelId)
        
        storeIdClean = storeId.replace("store_","")
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        thisStore = model.getStore(storeIdClean)
        
        ### Convert to Rest somehow
        excludeList = ['Service1']
        storeIdsToAdd = [thisStore.idcode]
    
        rows =[]
        for device in thisStore.inventory:
            if type(device.invType) == shadow_network.ShdStorageType:
                rows.append({'name':device.invType.getDisplayName(),
                             'count':device.count,
                             'cooler':device.invType.cooler,
                             'freezer':device.invType.freezer})
                
        return {'success':True,
                'total':1,
                'page':1,
                'rows':rows
                }
            
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result

@bottle.route('/json/get-transport-listing-for-store')
def generateTransportListingForStore(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
        ### Check permissions
        uiSession.getPrivs().mayReadModelId(db,modelId)
        
        storeIdClean = storeId.replace("store_","")
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        thisStore = m.getStore(storeIdClean)
        
        ### Convert to Rest somehow
        excludeList = ['Service1']
        storeIdsToAdd = [thisStore.idcode]
    
        rows =[]
        for device in thisStore.inventory:
            if type(device.invType) == shadow_network.ShdTruckType:
                entryDict = {'name':device.invType.getDisplayName(),
                             'count':device.count,
                             'cooler':0.0,
                             'freezer':0.0}
                
                entryDict['cooler'] += device.invType.CoolVolumeCC/1000.0
                for count,name in M.parseInventoryString(device.invType.Storage):
                    storageDevice = m.types[name]
                    entryDict['cooler'] += count*storageDevice.cooler
                    entryDict['freezer'] + count*storageDevice.freezer
                rows.append(entryDict)
                
                
        return {'success':True,
                'total':1,
                'page':1,
                'rows':rows
                }
            
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result

@bottle.route('/json/get-vials-plot-for-store')
def generateVialsPlotForStore(db,uiSession):
        try:
            import time
            
            modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
            storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
            resId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)  
             
            uiSession.getPrivs().mayReadModelId(db,modelId)
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
            r = m.getResultById(resId)
            
            storeIdClean = storeId.replace("store_","")
            thisStore = m.getStore(int(storeIdClean))

            thisStoreRes = r.storesRpts[thisStore.idcode]
            
           
            storeVialCountMV = thisStoreRes.storeVialCountMV()     
            countDict = storeVialCountMV.getDictFormat()
            returnDict = []
            burnDays = m.getParameterValue('burnindays')
            timeList = countDict['time']
            totalList = [0.0 for x in range(0,len(timeList))]
            
            for key,data in countDict.items():
                if key == "time":
                    continue
                if type(m.types[key]) == shadow_network.ShdVaccineType:
                    name = m.types[key].Abbreviation
                    thisDict = {'name':name,'data':[]}
                    
                    for i in xrange(0,len(data)):
                        thisDict['data'].append([timeList[i]-burnDays,data[i]])
                        totalList[i]+= data[i]
                
                    returnDict.append(thisDict)
            
            totalDict = {'name':'All Vaccines','data':[]}
            for i in xrange(0,len(totalList)):
                totalDict['data'].append([timeList[i]-burnDays,totalList[i]])
            returnDict.append(totalDict)
            
            return {
                    'success':True,
                    'data':returnDict
                    }
       
        except Exception,e:
            result = {'success':False,
                     'msg':str(e)}
            return result 

@bottle.route('/json/get-fill-ratio-time-for-store')
def generateFillRatioTimeForStore(db,uiSession):
        try:
            import time
            
            modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
            storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
            resId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)  
             
            uiSession.getPrivs().mayReadModelId(db,modelId)
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
            r = m.getResultById(resId)

            storeIdClean = storeId.replace("store_","")
            thisStore = m.getStore(int(storeIdClean))

            thisStoreRes = r.storesRpts[thisStore.idcode]
        
            storageRatioMV = thisStoreRes.storageRatioMV()      
            countDict = storageRatioMV.getDictFormat()
            print countDict
            returnDict = []

            burnDays = m.getParameterValue('burnindays')
            timeList = countDict['time']
            for key,data in countDict.items():
                if key == "time":
                    continue
                if key == "cooler":
                    name = "2-8 C Storage"
                elif key == "freezer":
                    name = "below 0 C Storage"
                else:
                    continue
                    #name = key
                
                thisDict = {'name':name,'data':[]}
                for i in xrange(0,len(data)):
                    thisDict['data'].append([timeList[i]-burnDays,data[i]*100.0])
                
                returnDict.append(thisDict)

            return {
                    'success':True,
                    'data':returnDict
                    }
       
        except Exception,e:
            result = {'success':False,
                     'msg':str(e)}
            return result 
@bottle.route('/json/get-vaccine-stats-for-store') 
def generateVaccineStatsForStore(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
        resId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)  
             
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resId)

        storeIdClean = storeId.replace("store_","")
        thisStore = m.getStore(int(storeIdClean))

        #thisStoreRes = r.storesRpts[thisStore.idcode]
        
        excludeList = ['Service1']
        storeIdsToAdd = [thisStore.idcode]
        
        for client in thisStore.clients():
            if client[1].Type == "attached" and client[0].FUNCTION != "Surrogate":
                storeIdsToAdd.append(client[0].idcode)
        
        vacDict = {'allvax':{'name':'All Vaccines','patients':0,'treated':0,'expired':0,'outages':0,'vials':0}}
        for storeID in storeIdsToAdd:
            sRep = r.storesRpts[storeID]
            for v,n in sRep.vax.items():
                vName = m.types[v].DisplayName
                if vName not in vacDict.keys():
                    vacDict[v] = {'name':vName,'patients':0,'treated':0,'expired':0,'outages':0,'vials':0}
                vacDict[v]['patients'] += n.patients
                vacDict[v]['treated']  += n.treated
                vacDict[v]['expired']  += n.expired
                vacDict[v]['outages']  += n.outages
                vacDict[v]['vials']    += n.vials
                vacDict['allvax']['patients'] += n.patients
                vacDict['allvax']['treated']  += n.treated
                vacDict['allvax']['expired']  += n.expired
                vacDict['allvax']['outages']  += n.outages
                vacDict['allvax']['vials']    += n.vials
        
        for v,d in vacDict.items():
            if d['patients'] > 0.0:
                d['avail'] = (float(d['treated'])/float(d['patients']))*100.0
            else:
                d['avail'] = 0.0
        ### make a sorted set of rows for the json
        
        keys = sorted([x for x in vacDict.keys() if x != "allvax"])
        
        rows = []
        
        for key in keys:
            rows.append(vacDict[key])

        rows.append(vacDict['allvax'])
        
        return {'success':True,
                'total':1,
                'page':1,
                'rows':rows
                }
        
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result 

@bottle.route('/json/get-vaccine-availability-plot-for-store') 
def generateVaccineAvailabilityPlotForStore(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
        resId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)  
             
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resId)

        storeIdClean = storeId.replace("store_","")
        thisStore = m.getStore(int(storeIdClean))

        #thisStoreRes = r.storesRpts[thisStore.idcode]
        
        excludeList = ['Service1']
        storeIdsToAdd = [thisStore.idcode]
        
        for client in thisStore.clients():
            if client[1].Type == "attached" and client[0].FUNCTION != "Surrogate":
                storeIdsToAdd.append(client[0].idcode)
        
        vacDict = {'allvax':{'name':'All Vaccines','patients':0,'treated':0,'expired':0,'outages':0,'vials':0}}
        for storeID in storeIdsToAdd:
            sRep = r.storesRpts[storeID]
            for v,n in sRep.vax.items():
                vName = m.types[v].DisplayName
                if vName not in vacDict.keys():
                    vacDict[v] = {'name':vName,'patients':0,'treated':0,'expired':0,'outages':0,'vials':0}
                vacDict[v]['patients'] += n.patients
                vacDict[v]['treated']  += n.treated
                vacDict[v]['expired']  += n.expired
                vacDict[v]['outages']  += n.outages
                vacDict[v]['vials']    += n.vials
                vacDict['allvax']['patients'] += n.patients
                vacDict['allvax']['treated']  += n.treated
                vacDict['allvax']['expired']  += n.expired
                vacDict['allvax']['outages']  += n.outages
                vacDict['allvax']['vials']    += n.vials
        
        
        keys = sorted([x for x in vacDict.keys() if x != "allvax"])
        categories = [vacDict[x]['name'] for x in keys]
        categories.append("All Vaccines")
        data = [float(vacDict[x]['treated'])/float(vacDict[x]['patients'])*100.0 if vacDict[x]['patients'] > 0 else 0.0 for x in keys]
        allav = 0.0
        if vacDict['allvax']['patients'] > 0.0:
            allav = float(vacDict['allvax']['treated'])/float(vacDict['allvax']['patients'])*100.0
    
        data.append({"y":allav,"color":"red"})
        
        return {
                'data':{'categories':categories,'plotData':data},
                'success':True
                }
        
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result 
    
@bottle.route('/json/get-general-info-for-route',method="post")
def generateGeneralInformationForRoute(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        routeId = _getOrThrowError(bottle.request.params,'routeId',isInt=False)
        
        ### Check permissions
        uiSession.getPrivs().mayReadModelId(db,modelId)
    
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        route = model.getRoute(routeId)
        
        features = [_("Name"),_("Levels"),"ID",_("Type")]
        parsedName = ""
        parsedLevelName = ""
        fixedFrequency = -1
        variableFrequency = -1
        daysOfStock = -1
        orderThresh = -1
        for stop in route.stops:
            stopStore = stop.store
            parsedName += "%s -> "%(stopStore.NAME)
            parsedLevelName += "%s -> "%(stopStore.CATEGORY)
        
        if route.Type in ["varpush","schedvarfetch"]:
            parsedType = "Fixed Schedule / Variable Amount Based on Frequency "
            fixedFrequency = route.ShipIntervalDays
        elif route.Type in ["push", "schedfetch"]:
            parsedType = "Fixed Schedule / Fixed Amount "
            fixedFrequency = route.ShipIntervalDays
        elif route.Type in ["pull","demandfetch"]:
            parsedType = "Variable Schedule (As Needed with Minimum Wait Time Between Shipments, When Stock Falls Below Threshold) / Variable Amount "
            variableFrequency = route.ShipIntervalDays
            daysOfStock= route.stops[0].PullOrderAmountDays
            orderThresh = "25%"
        elif route.Type in ["persistentpull","persistentdemandfetch"]:
            parsedType = "Variable Schedule (As Needed When Stock Falls Below Threshold) / Variable Amount "
            daysOfStock = route.stops[0].PullOrderAmountDays
            orderThresh = "25%"
        elif route.Type in ["askingpush"]:
            parsedType = "Fixed Schedule / Toping Off Strategy "
            fixedFrequency = route.ShipIntervalDays
        elif route.Type in ["dropandcollect"]:
            parsedType = "Drop off vaccines and return to collect"
            fixedFrequency = route.ShipIntervalDays
        elif route.Type in ["attached"]:
            parsedType = "Attached Clinic"
        else:
            parsedType = "UKNOWN"
            
        values = [parsedName[:-4],
                  parsedLevelName[:-4],
                  route.RouteName,
                  parsedType]
        
        if fixedFrequency != -1:
            features.append(_("Frequency (Fixed)"))
            values.append(fixedFrequency)
        if variableFrequency != -1:
            features.append(_("Mimimum Wait Between Shipments"))
            values.append(variableFrequency)
        if daysOfStock != -1:
            features.append(_("Amount of Days For Which To Order"))
            values.append(daysOfStock)
        if orderThresh != -1:
            features.append(_("Stock Threshold for Reordering"))
            values.append(orderThresh)
        
        ### put 
        rows = []
        for feature in features:
            rows.append({"feature":feature,"value":values[features.index(feature)]})
        
        result = {'success':True, 
                  'rows':rows,
                  'total':1,
                  'page':1}
        return result
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result
    
    
@bottle.route('/json/get-utilization-for-route',method='post') 
def generateUtilizationForRoute(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        routeId = _getOrThrowError(bottle.request.params,'routeId',isInt=False)
        resId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)  
             
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resId)

        route = m.getRoute(routeId)  
        routeRpt = r.routesRpts[routeId]
        
        rows = []
        features = [_('Vehicle'),_('Amount of Storage'),_('Average Volume Carried'),_('Maximum Volume Carried(L)')]
        values = []
        vol = 0.0
        device = m.types[route.TruckType]
    
        values.append(device.getDisplayName())
        vol += device.CoolVolumeCC/1000.00
        for (count,name) in M.parseInventoryString(device.Storage):
            storageDevice = m.types[name]
            vol += count*storageDevice.cooler
        values.append("%10.2f L"%vol)
        
        tripTimesDict = routeRpt.tripTimesMV().getDictFormat()
        
        iStart = 0
        iEnd = 1
        
        volsAve = []
        for i in range(0,len(tripTimesDict['startTime'])):
            if iEnd == 0:
                iStart = 0
                iEnd = 1
                volsAve.append(tripTimesDict['volumeCarried'][i])
            if iStart == len(route.stops)-1:
                iEnd = 0
            
            print type(iStart)
            iStart += 1 
        
        aSum = sum(volsAve)
        aAve = aSum/float(len(volsAve))
        valueString = "%10.2f L (%3.2f%%)"%(aAve,(aAve/vol)*100.00)
        values.append(valueString) # Need to do this
        maxFill = routeRpt.RouteFill
        overFill = 0.0
        if maxFill > 1.0:
            maxFill = 1.0
            overFill = maxFill - 1.0
        
        fillString = "%10.2f L (%3.2f%%)"%(maxFill*vol,maxFill*100.00)
        values.append(fillString)
        if overFill > 0.0:
            features.append(_('Additional Capacity Needed'))
            overString = "%10.2 L"%(overFill*vol)
            values.append(fillString)
        
        features.append(_('Trips Taken on Route'))
        values.append(routeRpt.RouteTrips)
        
        rows = []
        for feature in features:
            rows.append({"feature":feature,"value":values[features.index(feature)]})
        
        result = {'success':True, 
                  'rows':rows,
                  'total':1,
                  'page':1}
        return result
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result
        
                
@bottle.route('/json/get-tripman-for-route',method='post') 
def generateTripManifestForRoute(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        routeId = _getOrThrowError(bottle.request.params,'routeId',isInt=False)
        resId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)  
             
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resId)

        route = m.getRoute(routeId)  
        routeRpt = r.routesRpts[routeId]
        
        rows = []
            
        iStart = 0
        iEnd = 1
        burnDays = m.getParameterValue('burnindays')
        
        tripTimesDict = routeRpt.tripTimesMV().getDictFormat()   
        for i in range(0,len(tripTimesDict['startTime'])):
            if iEnd == 0:
                iStart = 0
                iEnd= 1
            if iStart == len(route.stops)-1:
                iEnd = 0
            
            rows.append({'start':route.stops[iStart].store.NAME,
                        'end':route.stops[iEnd].store.NAME,
                        'tStart':tripTimesDict['startTime'][i]-burnDays,
                        'tEnd':tripTimesDict['endTime'][i]-burnDays,
                        'LitersCarried':tripTimesDict['volumeCarried'][i]})
            iStart += 1
        result = {'success':True, 
                'rows':rows,
                'total':1,
                'page':1}
        return result
    except Exception,e:
        result = {'success':False,
                  'msg':str(e)}
        return result        
                
            
        
          