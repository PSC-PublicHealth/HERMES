#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id: google_earth_hooks.py 1435 2013-09-12 18:31:51Z welling $"

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
import kml_jquery_shdNtwk as kml
import htmlgenerator


from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
sI = site_info.SiteInfo()

inlizer=session_support.inlizer
_=session_support.translateString

#def googleEarthTopPage():
@bottle.route('/google_earth_demo')
def googleEarthTopPage(db, uiSession):
    modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    runId = _safeGetReqParam(bottle.request.params,'runId',isInt=True)    
    ## Get the appropriate KMLString and extract it to a file
    return bottle.template("google_earth_demo.tpl",{"breadcrumbPairs":[("top",_("Welcome"))],
                               "pageHelpText":_("This is intended to show page-specific help")},
                               _=_,inlizer=inlizer,modelId=modelId,runId=runId)

@bottle.route('/geojson_demo')
def geojsonTopPage(db,uiSession):
    modelId= _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    return bottle.template('geojson_demo.tpl',{"breadcrumbPairs":[("top",_("Welcome"))],
                                               "pageHelpText":_("This is intended to show page-specific help")},
                                               _=_,inlizer=inlizer,modelId=modelId)

@bottle.route('/d3geodemo')
def d3geoDemoPage(db,uiSession):
    modelId= _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    return bottle.template('d3democlickzoom.tpl',{"breadcrumbPairs":[("top",_("Welcome"))],
                                            "pageHelpText":_("This is intended to show page-specific help")},
                                            _=_,inlizer=inlizer,modelId=modelId)
    
@bottle.route('/json/storelocations')
def generateJSON(db, uiSession):
    from visualizationUtils import circleLonLat
    try:
        from geojson import Feature,Point,Polygon,FeatureCollection,dumps
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        # 
        #f = {'success':True,'features':[]}
        levels = m.getLevelList()
        f = [Feature(geometry=Point([x.Longitude,x.Latitude]),id=x.idcode,name=x.NAME,level=levels.index(x.CATEGORY)) for y,x in m.stores.items() if ((x.supplierRoute() is None) or (x.supplierRoute().Type != "attached" and x.CATEGORY != "Surrogate")) ]
        FC = FeatureCollection(f)
#         for storeId,store in m.stores.items():
#             f['features'].append(Feature(geometry=Point([store.Longitude,store.Latitude])))
#                                          #Polygon([circleLonLat(store.Longitude+0.001,store.Latitude+0.001,0.01,20)]),
#                                          #properties={'popupContent':store.NAME}))
            
        return {'success':True,"geoFC":FC}      
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result


@bottle.route('/json/get-general-info-for-store')   
def generateGeneralStoreInfoJson(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        storeId = _getOrThrowError(bottle.request.params,'storeId',isInt=False)
        storeIdClean = storeId.replace("store_","")
        ### Check permissions
        uiSession.getPrivs().mayReadModelId(db,modelId)
    
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        store = model.getStore(storeIdClean)
    
        features = ["Name","ID","Level"]
        values = [store.NAME,str(store.idcode),store.CATEGORY]
        
        if store.Latitude > 0.0:
            features.append("Latitude")
            values.append(str(store.Latitude))
            features.append("Longitude")
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
        
        peopleServedDict = {'all':{'displayName':'Total Served','count':0}}
        for storeId in storeIdsToAdd:
            store = model.getStore(storeIdClean)
            for demand in store.demand:
                if demand.invName not in excludeList:
                    if not peopleServedDict.has_key(demand.invName):
                        peopleServedDict[demand.invName] = {'count':0,
                                                            'displayName':demand.invType.getDisplayName()}
                    
                    peopleServedDict[demand.invName]['count']+= demand.count
                    peopleServedDict['all']['count'] += demand.count
        
        
        rows = []
        if peopleServedDict['all']['count'] == 0:
            rows.append({'class':'Total Served','count':'No Population Vaccinated at Location'})
        else:
            for psD in peopleServedDict.values():
                rows.append({'class':psD['displayName'],'count':psD['count']})
            
        #classes = [x['displayName'] for x in peopleServedDict.values()]
        #counts  = [x['count'] for x in peopleServedDict.values()]
        results = {'success':True,
                   'total':1,
                   'page':1,
                   'rows':rows
                   }
        
                   #'class':classes,
                   #'count':counts}
        
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

 
@bottle.route('/json/google-earth-kmlstring')
def jsonGoogleEarthKMLString(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        #print "ModelId = " + str(modelId) + " ResultsId = " + str(resultsId)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
    
        result = {}
    
        kmlString = r.getKmlVizString()
        if kmlString is None or kmlString == '':
            _logMessage("Building KML visualization")
            kDate = kml.KMLDate(2013,1,1)
            viz = kml.KMLVisualization(shadow_network_db_= m, 
                                       resultsID_= resultsId,    
                                       kmlDate_=kDate,
                                       title_="GEViz")
            if viz is None:
                raise Exception
            _logMessage("Done making viz")
            viz.build()
            _logMessage("Done building")
            viz.output() 
            _logMessage("Done outputing")
         
        kmlString = r.getKmlVizString()
        
        if kmlString is None or kmlString == "":
            result['kmlString'] = ''
        else:
            result['kmlString'] = kmlString.replace('\n','')
            
        result['success'] = True
        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

    
    
