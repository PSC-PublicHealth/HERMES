#!/usr/bin/env python
###################################################################################
# Copyright  2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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

from kitchen.text.display import fill

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
import crumbtracks
import serverconfig


from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
sI = site_info.SiteInfo()

inlizer=session_support.inlizer
_=session_support.translateString

@bottle.route('/network_results_visualization')
def createNetworkResultsViz(db,uiSession):
    modelId= modelId= _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
    hRG = db.query(shadow_network.HermesResults).filter(shadow_network.HermesResults.resultsId==resultsId).one().resultsGroup
    m = shadow_network_db_api.ShdNetworkDB(db,hRG.modelId)
    #temporary non-functional crumbtrack to display model and resultsgroup name
    # This is going in a separate tab, so we have to create a completely separate crumbtrack
    crumbTrack = crumbtracks.StackCrumbTrail(serverconfig.rootPath)
    crumbTrack.push(('/'+serverconfig.topPath, _("Network Visualization")))
    crumbTrack.push((bottle.request.path + '?' + bottle.request.query_string, 
                     _("Model: {0}, Result: {1}").format(m.name,hRG.name)))
    
    return bottle.template('results_show_structure.tpl',{"breadcrumbPairs":crumbTrack,
                                            "pageHelpText":_("This is intended to show page-specific help")},
                                            _=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId)

@bottle.route('/geographic_visualization')
def createGeographicViz(db,uiSession):
    modelId= modelId= _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
    hRG = db.query(shadow_network.HermesResults).filter(shadow_network.HermesResults.resultsId==resultsId).one().resultsGroup
    m = shadow_network_db_api.ShdNetworkDB(db,hRG.modelId)
    levels = m.getLevelList()
    maxpop = m.getMaxPopulationByWalkOfClients(m.rootStores()[0].idcode)
    #temporary non-functional crumbtrack to display model and resultsgroup name
    # This is going in a separate tab, so we have to create a completely separate crumbtrack
    crumbTrack = crumbtracks.StackCrumbTrail(serverconfig.rootPath)
    crumbTrack.push(('/'+serverconfig.topPath, _("Geographic Visualization")))
    crumbTrack.push((bottle.request.path + '?' + bottle.request.query_string, 
                     _("Model: {0}, Result: {1}").format(m.name,hRG.name)))
    return bottle.template('results_geo_visualization.tpl',{"breadcrumbPairs":crumbTrack,
                                            "pageHelpText":_("This is intended to show page-specific help")},
                                            _=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId,
                                            levels=levels,maxpop=maxpop,leila="false")

@bottle.route('/geographic_visualization_leila')
def createGeographicVizLeila(db,uiSession):
    modelId= modelId= _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
    hRG = db.query(shadow_network.HermesResults).filter(shadow_network.HermesResults.resultsId==resultsId).one().resultsGroup
    m = shadow_network_db_api.ShdNetworkDB(db,hRG.modelId)
    #temporary non-functional crumbtrack to display model and resultsgroup name
    # This is going in a separate tab, so we have to create a completely separate crumbtrack
    crumbTrack = crumbtracks.StackCrumbTrail(serverconfig.rootPath)
    crumbTrack.push(('/'+serverconfig.topPath, _("Geographic Visualization")))
    crumbTrack.push((bottle.request.path + '?' + bottle.request.query_string, 
                     _("Model: {0}, Result: {1}").format(m.name,hRG.name)))
    return bottle.template('results_geo_visualization.tpl',{"breadcrumbPairs":crumbTrack,
                                            "pageHelpText":_("This is intended to show page-specific help")},
                                            _=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId,leila="true")

@bottle.route('/json/model-structure-tree-results-d3')
def jsonModelStructureTreeD3(db,uiSession):
    try:
        import locale
        print locale.getdefaultlocale()[1]
        modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        model = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = model.getResultById(resultsId)
        
        json = model.getWalkOfClientsDictForJson(model.rootStores()[0].idcode)
        
        
        json['success']=True
        
        return json
    except Exception,e:
        return {'success':False,
                'msg':str(e)
                }
        
### This will return stores with results attached            
@bottle.route('/json/storelocations')
def generateStoreInfoJSON(db, uiSession):
    modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
   
    uiSession.getPrivs().mayReadModelId(db,modelId)
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    returnJson = m.getGeoJson()
    return returnJson['storejson']

@bottle.route('/json/routelines')
def generateRouteLinesJSON(db, uiSession):
    modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
   
    uiSession.getPrivs().mayReadModelId(db,modelId)
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    returnJson = m.getGeoJson()
    return returnJson['routejson']

### This will just return the locations of the stores with no results
def generateStoreInfoJSONFromModel(m):
    from visualizationUtils import circleLonLat
    try:
        from geojson import Feature,Point,Polygon,FeatureCollection,dumps
                
        levels = m.getLevelList()
        maxPop = m.getMaxPopulationByWalkOfClients(m.rootStores()[0].idcode)
        f = []
        for storeId,store in m.stores.items():
            flag = False
            if store.supplierRoute() is None: 
                flag = True
            else: 
                if (store.supplierRoute().Type != "attached" and store.CATEGORY != "Surrogate" and store.CATEGORY != "OutreachClinic" and
                    (float(store.Latitude) != 0.0 and float(store.Longitude)!= 0.0)): 
                    flag = True
            if flag:
                bold="false"
                pop = generatePopulationListingForStore(m,store)
                f.append(Feature(geometry=Point([store.Longitude,store.Latitude]),id=store.idcode,\
                         name=store.NAME,
                         level=levels.index(store.CATEGORY),
                         pop=pop['all']['count']/maxPop,
                         bold=bold))
             
#         FC = FeatureCollection(f)
#         f = [Feature(geometry=Point([x.Longitude,x.Latitude]),id=x.idcode,name=x.NAME,level=levels.index(x.CATEGORY))\
#              for y,x in m.stores.items()\
#              if ((x.supplierRoute() is None) or (x.supplierRoute().Type != "attached" and x.CATEGORY != "Surrogate")) ]
        
        FC = FeatureCollection(f)
                    
        return {'success':True,"geoFC":FC}      
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

### This will just return the route lines with no results
def generateRouteLinesJSONFromModel(m):
    try:
        #print "Shoot"
        from util import longitudeLatitudeSep
        from geojson import Feature,FeatureCollection,dumps,LineString
       
        #print "YES"
        f = []
        #print "THERE"
        routeIndexDict = {}
        count = 1
        for routeId,route in m.routes.items():
            if routeId not in routeIndexDict.keys():
                routeIndexDict[routeId] = count
                count += 1
        
        maxCount = count - 1
        
        for routeId,route in m.routes.items():
            if route.Type != 'attached':
                if len(route.stops) == 2:
                    start = route.stops[0].store
                    end = route.stops[1].store
                    if (start.Latitude != 0.0 and start.Longitude != 0.0) and \
                       (end.Latitude != 0.0 and end.Longitude != 0.0) and \
                       (start.Latitude != None and start.Longitude != None) and \
                       (end.Latitude != None and end.Longitude != None):
                        
                        bold = "false"
                            
                        f.append(Feature(geometry=LineString([(start.Longitude,start.Latitude),(end.Longitude,end.Latitude)]),
                                         id=routeId,onIds=[x.store.idcode for x in route.stops],
                                         rindex=routeIndexDict[routeId],maxcount=maxCount,bold=bold))
                else:
                    print routeId
                    for i in range(0,len(route.stops)):
                        start = route.stops[i].store
                        if i == len(route.stops)-1:
                            end = route.stops[0].store
                        else:
                            end = route.stops[i+1].store
                        if (start.Latitude != 0.0 and start.Longitude != 0.0) and \
                            (end.Latitude != 0.0 and end.Longitude != 0.0):
                            f.append(Feature(geometry=LineString([(start.Longitude,start.Latitude),(end.Longitude,end.Latitude)]),
                                             id=routeId,onIds=[x.store.idcode for x in route.stops],
                                             rindex=routeIndexDict[routeId],maxcount=maxCount))
        FC = FeatureCollection(f)
#         for routeId,route in m.routes.items():
#             if route.Type != 'attached':
#                 if len(route.stops) == 2:
#                     start = route.stops[0].store
#                     end = route.stops[1].store
#                     if (start.Latitude != 0.0 and start.Longitude != 0.0) and \
#                        (end.Latitude != 0.0 and end.Longitude != 0.0):
#                         bold = "false"
#                         if longitudeLatitudeSep(start.Longitude,start.Latitude,end.Longitude,end.Latitude) > 50.0:
#                             bold = "true"
#                         #print "HERE"
#                         f.append(Feature(geometry=LineString([(start.Longitude,start.Latitude),(end.Longitude,end.Latitude)]),
#                                          id=routeId,startId=route.stops[0].store.idcode,endId=route.stops[1].idcode,rindex=routeIndexDict[routeId],maxcount=maxCount),bold=bold)
#         
#         FC = FeatureCollection(f)
        
        return {'success':True,'geoFC':FC}  
        
    except Exception,e:
        result = {'success':False, 'msg':"%s: %s"%(sys.exc_traceback.tb_lineno,str(e))}
        return result
        

### This will return stores with results attached            
@bottle.route('/json/storeresultslocations')
def generateStoreUtilInfoJSON(db, uiSession):
    modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
    resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        
    uiSession.getPrivs().mayReadModelId(db,modelId)
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    r = m.getResultById(resultsId)
    returnJson = r.getGeoResultsJson()
    return returnJson['storejson']

def generateStoreUtilInfoJSONFromResult(r):
    import session_support_wrapper as session_support
    import db_routines
    try:
        iface = db_routines.DbInterface(echo=False)
        session = iface.Session()
        rG = session.query(shadow_network.HermesResultsGroup).filter(shadow_network.HermesResultsGroup.resultsGroupId == r.resultsGroupId).one()
        m = session.query(shadow_network.ShdNetwork).filter(shadow_network.ShdNetwork.modelId == rG.modelId).one()
        if m.hasGeoCoordinates():
            return generateStoreUtilInfoJSONNoSession(m, r)
        else:
            return {'success':True,'msg':'There are no coordinates'}
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result
    
def generateStoreUtilInfoJSONNoSession(m,r):
    #from visualizationUtils import circleLonLat
    try:
        from util import longitudeLatitudeSep
        from geojson import Feature,Point,Polygon,FeatureCollection,dumps
        
                
        levels = m.getLevelList()
        
        f = []
        maxPop = m.getMaxPopulationByWalkOfClients(m.rootStores()[0].idcode)
        for storeId,store in m.stores.items():
            flag = False
            if store.supplierRoute() is None: 
                flag = True
            else: 
                if (store.supplierRoute().Type != "attached" and store.CATEGORY != "Surrogate" and store.CATEGORY != "OutreachClinic" and
                    (float(store.Latitude) != 0.0 and float(store.Longitude)!= 0.0)): 
                    flag = True
            if flag:
                bold="false"
                pop = generatePopulationListingForStore(m,store)
                vac = generateVaccineStatsForStore(m,r,storeId)
                f.append(Feature(geometry=Point([store.Longitude,store.Latitude]),id=store.idcode,\
                         name=store.NAME,
                         level=levels.index(store.CATEGORY),
                         util=r.storesRpts[storeId].storage['cooler'].fillRatio,
                         pop=pop['all']['count']/maxPop,
                         va=vac['allvax']['avail'],
                         bold=bold))
             
        FC = FeatureCollection(f)
                    
        return {'success':True,"geoFC":FC}      
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result


### This will return routes with results attached
@bottle.route('/json/routeresultslines')
def generateRouteUtilizationLinesJSON(db,uiSession):
    try:
        modelId= _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
        returnJson = r.getGeoResultsJson()
        return returnJson['routejson']

    except Exception,e:
        result = {'success':False, 'msg':"%s: %s"%(sys.exc_traceback.tb_lineno,str(e))}
        return result

def generateRouteUtilizationLinesJSONFromResult(r):
    import session_support_wrapper as session_support
    import db_routines
    try:
        iface = db_routines.DbInterface(echo=False)
        session = iface.Session()
        rG = session.query(shadow_network.HermesResultsGroup).filter(shadow_network.HermesResultsGroup.resultsGroupId == r.resultsGroupId).one()
        
        m = session.query(shadow_network.ShdNetwork).filter(shadow_network.ShdNetwork.modelId == rG.modelId).one()
        if m.hasGeoCoordinates():
            return generateRouteUtilizationLinesJSONNoSession(m, r)
        else:
            return {'success':True,'message':'There are no coordinates'}
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result
    
def generateRouteUtilizationLinesJSONNoSession(m,r):
    try:
        #from util import longitudeLatitudeSep
        from geojson import Feature,FeatureCollection,dumps,LineString
        f = []
        routeIndexDict = {}
        count = 1
        for routeId,route in m.routes.items():
            if routeId not in routeIndexDict.keys():
                if route.Type != 'attached' and route.stops[1].store.CATEGORY != "OutreachClinic":
                    routeIndexDict[routeId] = count
                    count += 1
        
        maxCount = count - 1
        
        print routeIndexDict
        for routeId,route in m.routes.items():
            if route.Type != 'attached':
                if len(route.stops) == 2:
                    start = route.stops[0].store
                    end = route.stops[1].store
                    if (start.Latitude != 0.0 and start.Longitude != 0.0) and \
                       (end.Latitude != 0.0 and end.Longitude != 0.0) and \
                       (start.Latitude != None and start.Longitude != None) and \
                       (end.Latitude != None and end.Longitude != None):
                        fill = r.routesRpts[routeId].RouteFill
                        bold = "false"
                        if fill > 1.0:
                            fill = 1.0
                            
                        f.append(Feature(geometry=LineString([(start.Longitude,start.Latitude),(end.Longitude,end.Latitude)]),
                                         id=routeId,onIds=[x.store.idcode for x in route.stops],
                                         util=fill,rindex=routeIndexDict[routeId],maxcount=maxCount,bold=bold))
                else:
                    print routeId
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
                                             id=routeId,onIds=[x.store.idcode for x in route.stops],
                                             util=fill,rindex=routeIndexDict[routeId],maxcount=maxCount))
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
    m = shadow_network_db_api.ShdNetworkDB(db,modelId)
    ## Get the appropriate KMLString and extract it to a file
    crumbTrack = uiSession.getCrumbs()
    # This is going in a separate tab, so we have to create a completely separate crumbtrack
    crumbTrack = crumbtracks.StackCrumbTrail(serverconfig.rootPath)
    crumbTrack.push(('/'+serverconfig.topPath, _("Google Earth Visualization")))
    crumbTrack.push((bottle.request.path + '?' + bottle.request.query_string,
                     _("Model: {0}, Run: {1}").format(m.name,runId)))
    return bottle.template("google_earth_demo.tpl",{"breadcrumbPairs":crumbTrack,
                               "pageHelpText":_("This is intended to show page-specific help")},
                               _=_,inlizer=inlizer,modelId=modelId,runId=runId)
