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
import model as M
from information_dialog_box_hooks import generatePopulationListingForStore,generateVaccineStatsForStore


from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
sI = site_info.SiteInfo()

inlizer=session_support.inlizer
_=session_support.translateString

@bottle.route('/geographic_visualization')
def createGeographicViz(db,uiSession):
    modelId= _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
    return bottle.template('results_geo_visualization.tpl',{"breadcrumbPairs":[("top",_("Welcome"))],
                                            "pageHelpText":_("This is intended to show page-specific help")},
                                            _=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId)

### This will just return the locations of the stores with no results
@bottle.route('/json/storelocations')
def generateStoreInfoJSON(db, uiSession):
    from visualizationUtils import circleLonLat
    try:
        from geojson import Feature,Point,Polygon,FeatureCollection,dumps
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        levels = m.getLevelList()
        f = [Feature(geometry=Point([x.Longitude,x.Latitude]),id=x.idcode,name=x.NAME,level=levels.index(x.CATEGORY))\
             for y,x in m.stores.items()\
             if ((x.supplierRoute() is None) or (x.supplierRoute().Type != "attached" and x.CATEGORY != "Surrogate")) ]
        
        FC = FeatureCollection(f)
                    
        return {'success':True,"geoFC":FC}      
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

### This will just return the route lines with no results
@bottle.route('/json/routelines')
def generateRouteLinesJSON(db,uiSession):
    try:
        #print "Shoot"
        from geojson import Feature,FeatureCollection,dumps,LineString
        modelId= _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        #print "YES"
        f = []
        #print "THERE"
        for routeId,route in m.routes.items():
            if route.Type != 'attached':
                if len(route.stops) == 2:
                    start = route.stops[0].store
                    end = route.stops[1].store
                    if (start.Latitude != 0.0 and start.Longitude != 0.0) and \
                       (end.Latitude != 0.0 and end.Longitude != 0.0):
                        #print "HERE"
                        f.append(Feature(geometry=LineString([(start.Longitude,start.Latitude),(end.Longitude,end.Latitude)]),id=routeId))
        
        FC = FeatureCollection(f)
        
        return {'success':True,'geoFC':FC}  
        
    except Exception,e:
        result = {'success':False, 'msg':"%s: %s"%(sys.exc_traceback.tb_lineno,str(e))}
        return result
        

### This will return stores with results attached             
@bottle.route('/json/storeresultslocations')
def generateStoreUtilInfoJSON(db, uiSession):
    #from visualizationUtils import circleLonLat
    try:
        from geojson import Feature,Point,Polygon,FeatureCollection,dumps
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
                
        levels = m.getLevelList()
        
        f = []
        
        maxPop = m.getMaxPopulationByWalkOfClients(m.rootStores()[0].idcode)
        for storeId,store in m.stores.items():
            flag = False
            if store.supplierRoute() is None: 
                flag = True
            else: 
                if (store.supplierRoute().Type != "attached" and store.CATEGORY != "Surrogate" and store.CATEGORY != "OutreachClinic"): 
                    flag = True
            if flag:
                pop = generatePopulationListingForStore(m,store)
                vac = generateVaccineStatsForStore(m,r,storeId)
                f.append(Feature(geometry=Point([store.Longitude,store.Latitude]),id=store.idcode,\
                         name=store.NAME,
                         level=levels.index(store.CATEGORY),
                         util=r.storesRpts[storeId].storage['cooler'].fillRatio,
                         pop=pop['all']['count']/maxPop,
                         va=vac['allvax']['avail']))
             
        FC = FeatureCollection(f)
                    
        return {'success':True,"geoFC":FC}      
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result


### This will return routes with results attached
@bottle.route('/json/routeresultslines')
def generateRouteUtilizationLinesJSON(db,uiSession):
    try:
        #print "Shoot"
        from geojson import Feature,FeatureCollection,dumps,LineString
        modelId= _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
        
        #print "YES"
        f = []
        #print "THERE"
        for routeId,route in m.routes.items():
            if route.Type != 'attached':
                if len(route.stops) == 2:
                    start = route.stops[0].store
                    end = route.stops[1].store
                    if (start.Latitude != 0.0 and start.Longitude != 0.0) and \
                       (end.Latitude != 0.0 and end.Longitude != 0.0):
                        #print "HERE"
                        #print "theeee"
                        fill = r.routesRpts[routeId].RouteFill
                        if fill > 1.0:
                            fill = 1.0
                            
                        f.append(Feature(geometry=LineString([(start.Longitude,start.Latitude),(end.Longitude,end.Latitude)]),
                                         id=routeId,util=fill))
                else:
                    for i in range(0,len(route.stops)):
                        start = route.stops[i].store
                        if i == len(route.stops)-1:
                            end = route.stops[0].store
                        else:
                            end = route.stops[i+1].store
                        if (start.Latitude != 0.0 and start.Longitude != 0.0) and \
                            (end.Latitude != 0.0 and end.Longitude != 0.0):
                            fill = r.routesRpts[routeId].RouteFill
                            if fill > 1.0:
                                fill = 1.0
                            
                            f.append(Feature(geometry=LineString([(start.Longitude,start.Latitude),(end.Longitude,end.Latitude)]),
                                             id=routeId,util=fill))
        FC = FeatureCollection(f)
        
        return {'success':True,'geoFC':FC}  
        
    except Exception,e:
        result = {'success':False, 'msg':"%s: %s"%(sys.exc_traceback.tb_lineno,str(e))}
        return result

### Deprecated
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

    
    
### This visualization is deprecated, but left in here since it could still be useful.
@bottle.route('/google_earth_demo')
def googleEarthTopPage(db, uiSession):
    modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    runId = _safeGetReqParam(bottle.request.params,'runId',isInt=True)    
    ## Get the appropriate KMLString and extract it to a file
    return bottle.template("google_earth_demo.tpl",{"breadcrumbPairs":[("top",_("Welcome"))],
                               "pageHelpText":_("This is intended to show page-specific help")},
                               _=_,inlizer=inlizer,modelId=modelId,runId=runId)