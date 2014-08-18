#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id$"

import json, types, urllib
from StringIO import StringIO
import bottle
import ipath
import site_info
import shadow_network_db_api
import shadow_network
import privs
import htmlgenerator
import typehelper
from sqlalchemy.orm.exc import NoResultFound
from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _safeGetReqParam
from gridtools import orderAndChopPage
from model_edit_hooks import updateDBRouteType, jsonRecursiveStoreEditCreate
import session_support_wrapper as session_support

inlizer=session_support.inlizer
_=session_support.translateString

_typeCategoryNameMap = {'people':_('population types'),
                        'trucks':_('trucks'),
                        'ice':_('ice types'),
                        'vaccines':_('vaccines'),
                        'fridges':_('cold storage'),
                        'packaging':_('packaging')}

@bottle.route('/hrmwidgets.js')
def getHrmWidgetsJS(db, uiSession):
    bottle.response.set_header('content-type','text/javascript')
    return bottle.template("hrmwidgets.tpl") # to fill in rootPath

@bottle.route('/clientArray', method='POST')
def noOpCall():
    """
    jqGrid tries to access this as a URL during some local edit operations.  The easiest work-around
    is to provide a no-op URL.
    """
    raise bottle.BottleException('I think this URL is no longer necessary')
    #return {}

@bottle.route('/json/widget-create')
def jsonWidgetCreate(db, uiSession):
    try:
        widget = _getOrThrowError(bottle.request.params, 'widget')
        if 'developerMode' in uiSession and uiSession['developerMode']:
            _logMessage('widget-create for widget %s'%widget)
            for k,v in bottle.request.params.items():
                _logMessage('%s: <%s>'%(k,v))
        if widget=='storeEditor':
            return jsonStoreEditCreate(db, uiSession)
        elif widget=='routeEditor':
            return jsonRouteEditCreate(db, uiSession)
        elif widget=='recursiveStoreEditor':
            return jsonRecursiveStoreEditCreate(db, uiSession)
        else:
            raise bottle.BottleException(_("Unknown widget type {0}").format(widget))
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {"success":False, "msg":str(e)}

@bottle.route('/json/route-edit-create')
def jsonRouteEditCreate(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        routeName = _getOrThrowError(bottle.request.params, 'routename')
        closeOnSuccess = _safeGetReqParam(bottle.request.params,'closeOnSuccess')
        if 'storeEditorUniqueId' not in uiSession:
            uiSession['storeEditorUniqueId'] = 1;
        unique = uiSession['storeEditorUniqueId'];
        uiSession['storeEditorUniqueId'] += 1;
        try:
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        except NoResultFound:
            raise bottle.BottleException(_("No such model {0}").format(modelId))
        try:
            route = m.getRoute(routeName)
        except NoResultFound:
            raise bottle.BottleException(_("Model {0} has no route with name {1}").format(modelId,routeName))
        if route.routeTypes[route.Type] == 0: # supplier first
            firstClientIndex = 1
        else:
            firstClientIndex = 0
        pullOrderAmountDays = route.stops[firstClientIndex].PullOrderAmountDays
        if not pullOrderAmountDays or pullOrderAmountDays in ['null','None']:
            pullOrderAmountDays = ''
        routeIsScheduled = { k:(not v.usesPullMeanFrequency()) for k,v in route.types.items() }
        if (not routeIsScheduled[route.Type]) and pullOrderAmountDays=='':
            pullOrderAmountDays = route.ShipIntervalDays
        return { 
                'success':True, 
                'htmlstring':bottle.template("route_edit_wgt.tpl",{'modelId':modelId,
                                                                   'modelName':m.name,
                                                                   'routeName':routeName,
                                                                   'unique':unique,
                                                                   'ShipIntervalDays':route.ShipIntervalDays,
                                                                   'ShipLatencyDays':route.ShipLatencyDays,
                                                                   'truckType':route.TruckType,
                                                                   'routeType':route.Type,
                                                                   'Conditions':route.Conditions,
                                                                   'PullOrderAmountDays':pullOrderAmountDays,
                                                                   'routeTypeIsScheduledDict':routeIsScheduled,
                                                                   'closeOnSuccess':closeOnSuccess
                                                                   })
                }
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {"success":False, "msg":str(e)}
        
@bottle.route('/json/store-edit-create')
def jsonStoreEditCreate(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        idcode = _getOrThrowError(bottle.request.params, 'idcode', isInt=True)
        closeOnSuccess = _safeGetReqParam(bottle.request.params,'closeOnSuccess')
        if 'storeEditorUniqueId' not in uiSession:
            uiSession['storeEditorUniqueId'] = 1;
        unique = uiSession['storeEditorUniqueId'];
        uiSession['storeEditorUniqueId'] += 1;
        try:
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        except NoResultFound:
            raise bottle.BottleException(_("No such model {0}").format(modelId))
        try:
            store = m.getStore(idcode)
            levelNames = _smartStrip(m.getParameterValue('levellist'))
        except NoResultFound:
            raise bottle.BottleException(_("Model {0} has no store with idcode {1}").format(modelId,idcode))
        functionNameTs = [(s,_(s)) for s in ['Distribution','Administration','Outreach']]
        return { 
                'success':True, 
                'htmlstring':bottle.template("store_edit_wgt.tpl",{'modelId':modelId,
                                                                   'modelName':m.name,
                                                                   'idcode':idcode,
                                                                   'unique':unique,
                                                                   'storeName':store.NAME,
                                                                   'CATEGORY':store.CATEGORY,
                                                                   'FUNCTION':store.FUNCTION,
                                                                   'utilizationRate':store.utilizationRate,
                                                                   'Latitude':(store.Latitude if store.Latitude else 0.0),
                                                                   'Longitude':(store.Longitude if store.Longitude else 0.0),
                                                                   'UseVialsInterval':store.UseVialsInterval,
                                                                   'UseVialsLatency':store.UseVialsLatency,
                                                                   'Notes':store.Notes,
                                                                   'levelNames':levelNames,
                                                                   'functionNameTs':functionNameTs,
                                                                   'closeOnSuccess':closeOnSuccess
                                                                   })
                }
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {"success":False, "msg":str(e)}

@bottle.route('/json/store-edit-manage-table')
def jsonStoreEditManageTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        idcode = _getOrThrowError(bottle.request.params, 'idcode', isInt=True)
        unique = _getOrThrowError(bottle.request.params, 'unique', isInt=True)
        invtype = _safeGetReqParam(bottle.request.params, 'invtype')
        try:
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        except NoResultFound:
            raise bottle.BottleException(_("No such model {0}").format(modelId))
        try:
            store = m.getStore(idcode)
        except NoResultFound:
            raise bottle.BottleException(_("Model {0} has no store with idcode {1}").format(modelId,idcode))
        #attachedClinics = [r.stops[-1].store for r in store.clientRoutes() if r.Type=='attached']
        attachedClinics = []
        tDictDict = {}
        if invtype is None:
            for s in [store]+attachedClinics:
                for thing in s.inventory+s.demand:
                    if thing.count>0:
                        demandFlag = ( thing.invType=='people' )
                        if thing.invName in tDictDict:
                            tDictDict[thing.invName]['count'] += s.countInventory(thing, useDemandList=demandFlag)
                        else:
                            tDictDict[thing.invName] = {'Name':thing.invName,
                                                        'count':s.countInventory(thing, useDemandList=demandFlag), 
                                                        'category':_typeCategoryNameMap[thing.invType.shdType],
                                                        'description':thing.invType.getDisplayName()}
                            
            nPages,thisPageNum,totRecs,tList = orderAndChopPage(tDictDict.values(),
                                                                {'typestring':'Name', 'count':'count',
                                                                 'category':'category'},
                                                                bottle.request,
                                                                defaultSortIndex='typestring')
            
            result = {
                      "success":True,
                      "total":nPages,    # total pages
                      "page":thisPageNum,     # which page is this
                      "records":totRecs,  # total records
                      "rows": [ {"name":t['Name'], 
                                 "cell":[t['category'], t['Name'], t['description'], t['count'], t['Name']]}
                               for t in tList ]
                      }
        elif invtype=='fridges':
            for s in [store]+attachedClinics:
                for thing in s.inventory:
                    if thing.invType.shdType=='fridges' and thing.count>0:
                        if thing.invName in tDictDict:
                            d = tDictDict[thing.invName]
                            d['count'] += s.countInventory(thing)
                            d['freezer'] += thing.invType.freezer
                            d['cooler'] += thing.invType.cooler
                            d['roomtemperature'] += thing.invType.roomtemperature
                        else:
                            tDictDict[thing.invName] = {'Name':thing.invName,
                                                        'count':s.countInventory(thing), 
                                                        'category':_typeCategoryNameMap[thing.invType.shdType],
                                                        'description':thing.invType.getDisplayName(),
                                                        'freezer':thing.invType.freezer,
                                                        'cooler':thing.invType.cooler,
                                                        'roomtemperature':thing.invType.roomtemperature}
            totals = {"description":"Totals","freezer":0.0, "cooler":0.0, "warm":0.0, "count":0}
            for thing in tDictDict.values():
                totals['freezer'] += thing['count']*thing['freezer']
                totals['cooler'] += thing['count']*thing['cooler']
                totals['warm'] += thing['count']*thing['roomtemperature']
                totals['count'] += thing['count']
                
            nPages,thisPageNum,totRecs,tList = orderAndChopPage(tDictDict.values(),
                                                                {'typestring':'Name', 'count':'count',
                                                                 'category':'category',
                                                                 'cool':'cooler','freeze':'freezer',
                                                                 'warm':'roomtemperature'},
                                                                bottle.request,
                                                                defaultSortIndex='typestring')
            
            
            result = {
                      "success":True,
                      "total":nPages,    # total pages
                      "page":thisPageNum,     # which page is this
                      "records":totRecs,  # total records
                      "rows": [ {"name":t['Name'], 
                                 "cell":[t['Name'], t['count'], t['Name'],t['description'], t['freezer'], t['cooler'],
                                         t['roomtemperature'], t['count'], t['Name']]}
                               for t in tList ],
                      "userdata":totals
                      }
        elif invtype=='trucks':
            for s in [store]+attachedClinics:
                for thing in s.inventory:
                    if thing.invType.shdType=='trucks' and thing.count>0:
                        if thing.invName in tDictDict:
                            d = tDictDict[thing.invName]
                            d['count'] += s.countInventory(thing)
                            d['cooler'] += 0.001*thing.invType.CoolVolumeCC
                            d['storage'] = d['storage'] + '+' + thing.invType.Storage
                        else:
                            tDictDict[thing.invName] = {'Name':thing.invName,
                                                        'count':s.countInventory(thing), 
                                                        'category':_typeCategoryNameMap[thing.invType.shdType],
                                                        'description':thing.invType.getDisplayName(),
                                                        'cooler':0.001*thing.invType.CoolVolumeCC,
                                                        'storage':thing.invType.Storage}
            totals = {"description":"Totals","storage":"","cooler":0.0, "count":0}
            for thing in tDictDict.values():
                totals['cooler'] += thing['count']*thing['cooler']
                totals['count'] += thing['count']
                
            nPages,thisPageNum,totRecs,tList = orderAndChopPage(tDictDict.values(),
                                                                {'typestring':'Name', 'count':'count',
                                                                 'category':'category',
                                                                 'cooler':'cooler','storage':'storage'},
                                                                bottle.request,
                                                                defaultSortIndex='typestring')
            
            
            result = {
                      "success":True,
                      "total":nPages,    # total pages
                      "page":thisPageNum,     # which page is this
                      "records":totRecs,  # total records
                      "rows": [ {"name":t['Name'], 
                                 "cell":[t['Name'], t['count'],t['Name'],t['description'], t['cooler'],
                                         t['storage'], t['count'], t['Name']]}
                               for t in tList ],
                      "userdata":totals
                      }
        elif invtype=='vaccines':
            for s in [store]+attachedClinics:
                for thing in s.inventory:
                    if thing.invType.shdType=='vaccines' and thing.count>0:
                        if thing.invName in tDictDict:
                            d = tDictDict[thing.invName]
                            d['count'] += s.countInventory(thing)
                        else:
                            tDictDict[thing.invName] = {'Name':thing.invName,
                                                        'count':s.countInventory(thing), 
                                                        'category':_typeCategoryNameMap[thing.invType.shdType],
                                                        'description':thing.invType.getDisplayName(),
                                                        'dosespervial':thing.invType.dosesPerVial,
                                                        'requires':thing.invType.Requires}
            totals = {"description":"Totals","count":0}
            for thing in tDictDict.values():
                totals['count'] += thing['count']
                
            nPages,thisPageNum,totRecs,tList = orderAndChopPage(tDictDict.values(),
                                                                {'typestring':'Name', 'count':'count',
                                                                 'category':'category',
                                                                 'dosespervial':'dosespervial',
                                                                 'requires':'requires'},
                                                                bottle.request,
                                                                defaultSortIndex='typestring')
            
            
            result = {
                      "success":True,
                      "total":nPages,    # total pages
                      "page":thisPageNum,     # which page is this
                      "records":totRecs,  # total records
                      "rows": [ {"name":t['Name'], 
                                 "cell":[t['Name'], t['count'], t['Name'],t['description'], t['dosespervial'], t['requires'],
                                         t['count'], t['Name']]}
                               for t in tList ],
                      "userdata":totals
                      }
        elif invtype=='people':
            for s in [store]+attachedClinics:
                for thing in s.demand:
                    if thing.invType.shdType=='people' and thing.count>0:
                        if thing.invName in tDictDict:
                            tDictDict[thing.invName]['count'] += s.countDemand(thing)
                        else:
                            tDictDict[thing.invName] = {'Name':thing.invName,
                                                        'count':s.countDemand(thing), 
                                                        'category':_typeCategoryNameMap[thing.invType.shdType],
                                                        'description':thing.invType.getDisplayName()}
            totals = {"description":"Totals","count":0}
            for thing in tDictDict.values():
                totals['count'] += thing['count']
                
            nPages,thisPageNum,totRecs,tList = orderAndChopPage(tDictDict.values(),
                                                                {'typestring':'Name', 'count':'count',
                                                                 'category':'category'},
                                                                bottle.request,
                                                                defaultSortIndex='typestring')
            
            
            result = {
                      "success":True,
                      "total":nPages,    # total pages
                      "page":thisPageNum,     # which page is this
                      "records":totRecs,  # total records
                      "rows": [ {"name":t['Name'], 
                                 "cell":[t['Name'], t['count'], t['Name'],t['description'], t['count'], t['Name']]}
                               for t in tList ],
                      "userdata":totals
                      }
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = {"success":False,
                  "msg":str(e)}
    return result

@bottle.route('/json/route-edit-manage-stop-table')
def jsonRouteEditManageStopTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        routeName = _getOrThrowError(bottle.request.params, 'routename')
        routeType = _safeGetReqParam(bottle.request.params, 'routetype' )
        try:
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        except NoResultFound:
            raise bottle.BottleException(_("No such model {0}").format(modelId))
        try:
            route = m.getRoute(routeName)
        except NoResultFound:
            raise bottle.BottleException(_("Model {0} has no route with name {1}").format(modelId,routeName))

        if not routeType or routeType=='' or routeType=='null':
            routeType = route.Type;

        tList = [{'Name':stop.store.NAME, 'idcode':stop.store.idcode, 
                  'transitHours':stop.TransitHours, 'distanceKM':stop.DistanceKM} for stop in route.stops]

        # If this is an archaic file with '0.0' for the first transit time, convert to new ordering
        if tList[0]['transitHours'] == 0.0:
            timeList = [s['transitHours'] for s in tList]
            for new,stop in zip(timeList[1:],tList[:-1]):
                stop['transitHours'] = new

        # If route order notation is different between the real route and this hypothetical route, reverse order
        # of the first two stops.        
        if route.routeTypes[routeType] != route.routeTypes[route.Type]:
            tList = [tList[1]] + [tList[0]] + tList[2:]

        for idx,stop in enumerate(tList):
            if route.routeTypes[routeType] == idx:
                if idx==0: infoStr = _("Supplier; route starts and ends here")
                else: infoStr = _("Supplier")
            else:
                if idx==0: infoStr = _("Route starts and ends here")
                else: infoStr = ''
            stop['info'] = infoStr
            
        nPages = 1
        thisPageNum = 0
        totRecs = len(tList)
            
        result = {
                  "success":True,
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"name":t['Name'], 
                             "cell":[t['Name'], t['idcode'], t['transitHours'], t['distanceKM'], t['info']]}
                           for t in tList ]
                  }
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = {"success":False,
                  "msg":str(e)}
    return result


@bottle.route('/list/select-route-type')
def handleListRouteType(db,uiSession):
    try:
        typestring = _safeGetReqParam(bottle.request.params, 'typestring')
        if typestring=='null' or typestring=='': typestring = None
        typeList = shadow_network.ShdRoute.routeTypes.keys()[:]
        sio = StringIO()
        for t in typeList:
            if typestring and typestring==t:
                sio.write("  <option value='%s' selected >%s</option>\n"%(t,t))
            else:
                sio.write("  <option value='%s'>%s</option>\n"%(t,t))
        
        return {"success":True,
                "menustr":sio.getvalue(),
                "selected":( typestring if typestring is not None else typeList[0] )
                }
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {"success":False, "msg":str(e)}

@bottle.route('/list/select-type')
def handleListType(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        invtype = _getOrThrowError(bottle.request.params, 'invtype')
        typestring = _safeGetReqParam(bottle.request.params, 'typestring')
        escapeFlag = _safeGetReqParam(bottle.request.params, 'encode')
        if typestring=='null' or typestring=='': typestring = None
        typeList = typehelper.getTypeList(db,modelId,invtype,fallback=False)
        sio = StringIO()
        for t in typeList:
            
            if escapeFlag: eName = urllib.quote(t['Name'])
            else: eName = t['Name']
            
            if typestring and typestring==t['Name']:
                sio.write("  <option value='%s' selected >%s</option>\n"%(eName,t['Name']))
            else:
                sio.write("  <option value='%s'>%s</option>\n"%(eName,t['Name']))
        
        return {"success":True,
                "menustr":sio.getvalue(),
                "selected":( typestring if typestring is not None else typeList[0] )
                }
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {"success":False, "msg":str(e)}

@bottle.route('/list/select-type-full')
def listSelectTypeFull(db, uiSession):
    """
    Return a pure HTML string for a <select> element, as per jgGrid edittype="select" editoptions dataURL
    """
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        invtype = _getOrThrowError(bottle.request.params, 'invtype')
        typestring = _safeGetReqParam(bottle.request.params, 'typestring')
        if typestring=='null': typestring = None
        typeList = typehelper.getTypeList(db,modelId,invtype,fallback=False)
        optionInfo = handleListType(db, uiSession)
        return "<select>\n"+optionInfo['menustr']+"</select>\n"
    except Exception,e:
        raise bottle.BottleException(str(e))

@bottle.route('/edit/store-edit-edit',method='POST')
def editStoreEditEdit(db, uiSession):
    try:
#         for k,v in bottle.request.params.items():
#             print 'param: %s : %s'%(k,v)
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        try:
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        except NoResultFound:
            raise bottle.BottleException(_("No such model {0}").format(modelId))
        idcode = _getOrThrowError(bottle.request.params, 'idcode', isInt=True)
        try:
            store = m.getStore(idcode)
        except NoResultFound:
            raise bottle.BottleException(_("Model {0} has no store with idcode {1}").format(modelId,idcode))
        invtype = _getOrThrowError(bottle.request.params, 'invtype')
        visibletypestring = _safeGetReqParam(bottle.request.params, 'visibletypestring')
        count = _safeGetReqParam(bottle.request.params, 'count', isInt=True)
        demandFlag = (invtype=='people')
        oper = _getOrThrowError(bottle.request.params, 'oper')
        if oper=='edit':
            typestring = _getOrThrowError(bottle.request.params, 'typestring')
            if typestring==visibletypestring:
                if count is None:
                    pass
                else:
                    store.updateInventory(typestring, count, useDemandList=demandFlag)
            else:
                oldCountNewType = store.countInventory(visibletypestring, useDemandList=demandFlag)
                oldCountOldType = store.countInventory(typestring, useDemandList=demandFlag)
                if count: changedCount = count
                else: changedCount = oldCountOldType
                newCountNewType = oldCountNewType + changedCount
                store.updateInventory(typestring, 0, useDemandList=demandFlag)
                store.updateInventory(visibletypestring, newCountNewType, useDemandList=demandFlag)
        elif oper=='add':
            typestring = _getOrThrowError(bottle.request.params, 'typestring')
            if count is None:
                pass
            else:
                store.updateInventory(visibletypestring, count, useDemandList=demandFlag)
        elif oper=='del':
            typestring = _getOrThrowError(bottle.request.params, 'id')
            store.updateInventory(typestring, 0, useDemandList=demandFlag)
        else:
            raise bottle.BottleException(_("Unknown editing operation {0}").format(oper))
        return {'success':True}
    except Exception,e:
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/type-info')
def jsonTypeInfo(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        name = _getOrThrowError(bottle.request.params, 'typestring')
        htmlStr, titleStr = htmlgenerator.getGenericTypeInfoHTML(db,uiSession,modelId,name)
        result = {'success':True, "htmlstring":htmlStr, "title":titleStr}
        return result
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        return result
    
@bottle.route('/json/type-dict')
def jsonTypeDict(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        name = _getOrThrowError(bottle.request.params, 'typestring')
        owned,t = typehelper.getTypeWithFallback(db, modelId, name)
        attrRec = {}
        shadow_network._copyAttrsToRec(attrRec,t)
        if isinstance(t,shadow_network.ShdTruckType):
            attrRec['CoolVolumeL'] = 0.001*attrRec['CoolVolumeCC'] # offer value in liters
        attrRec['DisplayName'] = t.getDisplayName()
        result = {'success':True, "value":attrRec}
        return result
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        return result
    
@bottle.route('/json/store-update',method='POST')
def jsonStoreUpdate(db, uiSession):
    try:
#         for k,v in bottle.request.params.items():
#             print '%s: <%s>'%(k,v)
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        idcode = _getOrThrowError(bottle.request.params, 'idcode', isInt=True)
        unique = _safeGetReqParam(bottle.request.params, 'unique', isInt=True)
        try:
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        except NoResultFound:
            raise bottle.BottleException(_("No such model {0}").format(modelId))
        try:
            store = m.getStore(idcode)
        except NoResultFound:
            raise bottle.BottleException(_("Model {0} has no store with idcode {1}").format(modelId,idcode))
        levelNames = _smartStrip(m.getParameterValue('levellist'))
        functionNames = ['Distribution','Administration','Outreach']
        functionNameTs = [(s,_(s)) for s in functionNames]
        badParms = []
        goodPairs = []
        for key,name,isInt,isFloat,vList,range in [('name','NAME',False,False,None,None),
                                                   ('category','CATEGORY',False,False,levelNames,None),
                                                   ('function','FUNCTION',False,False,functionNames,None),
                                                   ('notes','Notes',False,False,None,None),
                                                   ('usevialsinterval','UseVialsInterval',False,True,None,(0.0,336.0)),
                                                   ('usevialslatency','UseVialsLatency',False,True,None,(0.0,336.0)),
                                                   ('utilizationrate','utilizationRate',False,True,None,(0.0,1.0)),
                                                   ('longitude','Longitude',False,True,None,(-180.0,180.0)),
                                                   ('latitude','Latitude',False,True,None,(-90.0,90.0)),
                                                   ]:
            v = _safeGetReqParam(bottle.request.params, key)
            if v:
                if isInt: v = int(v)
                if isFloat: v = float(v)
                if vList and v not in vList:
                    badParms.append(_("{0} has an invalid value").format(key))
                elif range and ( v<range[0] or v>range[1] ):
                    badParms.append(_("{0} must be in the range {1} to {2}".format(key,range[0],range[1])))
                else:
                    goodPairs.append((name,v))
        if badParms==[]:
            for name,v in goodPairs:
                setattr(store, name, v)
        else:
            return {'success':True, 'value':False, 'msg':"\n".join(badParms)}

        for invtype in ['fridgedata','truckdata','peopledata','vaccinedata']:
            offset = 0
            demandFlag = ( invtype=='peopledata' )
            while True:
                count = _safeGetReqParam(bottle.request.params,"%s[%d][%s]"%(invtype,offset,'count'),isInt=True)
                if count is not None:
                    origcount = _safeGetReqParam(bottle.request.params,"%s[%d][%s]"%(invtype,offset,'origcount'),isInt=True)
                    origtypename = _getOrThrowError(bottle.request.params,"%s[%d][%s]"%(invtype,offset,'typename'))
                    typename = _getOrThrowError(bottle.request.params,"%s[%d][%s]"%(invtype,offset,'visibletypename'))
                    if origcount is None:
                        # This is an add or delete operation
                        store.updateInventory(typename, count, useDemandList=demandFlag)
                    else:
                        # This is an edit of an existing line
                        if origtypename==typename:
                            if origcount==count:
                                pass
                            else:
                                store.updateInventory(origtypename, count, useDemandList=demandFlag)
                        else:
                            store.updateInventory(origtypename, 0, useDemandList=demandFlag)
                            store.updateInventory(typename, count, useDemandList=demandFlag)
                    offset += 1
                else:
                    break
            
        return {'success':True, 'value':True}
    except Exception,e:
        return {'success':False, 'msg':str(e)}
            
@bottle.route('/json/route-update',method='POST')
def jsonRouteUpdate(db, uiSession):
    try:
        #for k,v in bottle.request.params.items():
        #    print '%s: <%s>'%(k,v)
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        routename = _getOrThrowError(bottle.request.params, 'routename')
        unique = _safeGetReqParam(bottle.request.params, 'unique', isInt=True)
        try:
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        except NoResultFound:
            raise bottle.BottleException(_("No such model {0}").format(modelId))
        try:
            route = m.getRoute(routename)
        except NoResultFound:
            raise bottle.BottleException(_("Model {0} has no route with name {1}").format(modelId,routename))
        pullOrderAmountDays = _safeGetReqParam(bottle.request.params,'pullorderamountdays')
        badParms = []
        goodTuples = []
        pullMeanFreqNeeded = ( route.types[route.Type].usesPullMeanFrequency() )
        for key,name,isInt,isFloat,vList,range in [('routeType','Type',False,False,route.types.keys(),None),
                                                   ('truckType','TruckType',False,False,[],None),
                                                   ('shipintervaldays','ShipIntervalDays',False,True,None,(0.0,336.0)),
                                                   ('shiplatencydays','ShipLatencyDays',False,True,None,(0.0,336.0)),
                                                   ('conditions','Conditions',False,False,None,None),
                                                   ]:
            v = _safeGetReqParam(bottle.request.params, key)
            if isInt: v = int(v)
            if isFloat: v = float(v)
            if vList and v not in vList:
                badParms.append(_("{0} has an invalid value").format(key))
            elif range and ( v<range[0] or v>range[1] ):
                badParms.append(_("{0} must be in the range {1} to {2}".format(key,range[0],range[1])))
            else:
                goodTuples.append((key,name,v))
                
            if key=='routeType':
                pullMeanFreqNeeded = route.types[v].usesPullMeanFrequency()
                
        if pullMeanFreqNeeded:
            v = _safeGetReqParam(bottle.request.params, 'pullorderamountdays', isFloat=True)
            if v is None:
                badParms.append(_("This route type requires a valid value for On-Demand Order Days"))
            else:
                goodTuples.append(('pullorderamountdays',None,v))
 
        invtype = 'stopdata'
        offset = 0
        goodStopTuples = []
        noTransitTimeLocs = []
        while True:
            idcode = _safeGetReqParam(bottle.request.params,"%s[%d][%s]"%(invtype,offset,'idcode'),isInt=True)
            if idcode is not None:
                tripTime = _safeGetReqParam(bottle.request.params,"%s[%d][%s]"%(invtype,offset,'triptime'),isFloat=True)
                tripKM = _safeGetReqParam(bottle.request.params,"%s[%d][%s]"%(invtype,offset,'tripkm'),isFloat=True)
                stopName = _getOrThrowError(bottle.request.params,"%s[%d][%s]"%(invtype,offset,'name'))
                if tripTime is None: 
                    badParms.append(_('Transit time for the stop at {0} ({1}) is missing or invalid').format(stopName,idcode))
                else:
                    goodStopTuples.append((idcode,tripTime,tripKM))
                offset += 1
            else:
                break

        if badParms==[]:
            for key,name,v in goodTuples:
                if key=='routeType':
                    updateDBRouteType(route, v) # Includes re-ordering stops if necessary
                elif key in frozenset(['truckType','shipintervaldays','shiplatencydays',
                                       'conditions']):
                    setattr(route, name, v)
                elif key=='pullorderamountdays':
                    for stop in route.stops: stop.PullOrderAmountDays = v
                else:
                    raise RuntimeError('hit unknown change key %s %s'%(key,name))
                    
                #setattr(route, name, v)
            stopDict = {s.store.idcode:s for s in route.stops}
            for idcode,tripTime,tripKM in goodStopTuples:
                stop = stopDict[idcode]
                setattr(stop,'TransitHours',tripTime)
                setattr(stop,'DistanceKM',tripKM)
        else:
            return {'success':True, 'value':False, 'msg':"\n".join(badParms)}
            
        return {'success':True, 'value':True}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {'success':False, 'msg':str(e)}
