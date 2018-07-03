#!/usr/bin/env python
from sqlalchemy.orm.exc import _safe_cls_name


####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id: truckhooks.py 2262 2015-02-09 14:38:25Z stbrown $"

import sys,os,os.path,time,json,math,types
import bottle
import ipath
import shadow_network_db_api
import shadow_network
import session_support_wrapper as session_support
from HermesServiceException import HermesServiceException
from gridtools import orderAndChopPage
import privs
import htmlgenerator
import typehelper
from trucktypes import fuelTranslationDict
import typehooks

from ui_utils import _logMessage, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults,\
    _safeGetReqParam

inlizer=session_support.inlizer
_=session_support.translateString

fuelOptions = [(x,y[1],[],[]) for  x,y in fuelTranslationDict.items()]
fieldMap = [{ 'label':_('Data Base ID'), 'key':'Name', 'id':'name', 'info':False, 'edit':False,'req':True, 'type':'dbkey', 'default':None},
            { 'label':_('Name'), 'key':'DisplayName', 'id':'displayname', 'info':True, 'edit':True,'req':True, 'type':'string', 'default':None},
            { 'label':_('Capital Cost'), 'key':'BaseCost', 'id':'baseprice', 'info':True, 'edit':True, 'type':'cost','req':True, 'recMap':['BaseCost', 'BaseCostCurCode', 'BaseCostYear']},
            { 'label':_('Lifetime of Vehicle (KM)'), 'key':'AmortizationKm', 'id':'amortkm', 'info':True, 'edit':True, 'req':True, 'type':'float'},
            { 'label':_('Fuel Type'), 'key':'Fuel', 'id':'fuel', 'info':True, 'edit':True, 'req':True, 'type':'select','options':fuelOptions,'default':'P'},
            { 'label':_('Fuel Consumption Rate'), 'key':'FuelRate', 'id':'fuelrate', 'info':True, 'edit':True, 'req':True,
             'type':'dynamicunit', 'lookup':'Fuel','lookupDict':fuelTranslationDict,'recMap':['FuelRate','FuelRateUnits']},
            { 'label':_('Net Storage at 2-8C <br>Outside of Storage Devices (L)'),
             'key':'CoolVolumeCC', 'id':'coolvolumecc', 'info':True, 'edit':True, 'req':False, 'type':'scaledfloat','scale':1.0/1000.0},
            { 'label':_('Storage on Vehicle'), 'key':'Storage', 'id':'storage', 'info':True, 'edit':True, 'req':False, 'type':'custtruckstoragetable'},
            { 'label':_('Requires'), 'key':'Requires', 'id':'requires', 'info':False, 'edit':False, 'req':False, 'type':'string'},
            { 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'info':True, 'edit':True, 'req':False, 'type':'stringbox'},
                   
            ]

@bottle.route('/truck-edit')
def truckEditPage(db, uiSession):
    return typehooks.typeEditPage(db, uiSession, 'trucks')

@bottle.route('/edit/edit-truck.json', method='POST')
def editTruck(db,uiSession):  
    return typehooks.editType(db, uiSession, 'trucks')
        

def jsonTruckEditFn(attrRec, m):
# FuelRateUnits is completely determined by energy type
    #print "Truck AttrRec-----------------------------------------"
    #print attrRec
    if attrRec['Fuel']:
        attrRec['FuelRateUnits'] = fuelTranslationDict[attrRec['Fuel'].encode('utf-8')][2]
    else:
        attrRec['FuelRateUnits'] = None
    return attrRec
    
@bottle.route('/json/truck-edit-verify-commit')
def jsonTruckEditVerifyCommit(db, uiSession):
    return typehooks.jsonTypeEditVerifyAndCommit(db, uiSession, 'trucks', fieldMap,
                                                 jsonTruckEditFn)
            
@bottle.route('/json/truck-info')
def jsonTruckInfo(db, uiSession):
    return typehooks.jsonTypeInfo(db, uiSession, htmlgenerator.getTruckInfoHTML)
    
@bottle.route('/json/truck-edit-form')
def jsonTruckEditForm(db, uiSession):
    return typehooks.jsonTypeEditForm(db, uiSession, 'trucks', fieldMap)


@bottle.route('/truck-top')
def truckTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Transport")))
    return bottle.template("truck_top.tpl",{"breadcrumbPairs":crumbTrack},pagehelptag="database")

@bottle.route('/json/manage-truck-table')
def jsonManageTruckTable(db, uiSession):
    try:
        modelId = int(bottle.request.params['modelId'])
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        tList = typehelper.getTypeList(db,modelId,'trucks')
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                            {'name':'Name', 'usedin':'modelId', 'dispnm':'DisplayName'},
                                                            bottle.request)
        result = {
                  "success":True,
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"name":t['Name'], 
                             "cell":[t['Name'], t['_inmodel'], t['DisplayName'], t['Name']]}
                           for t in tList ]
                  }
        return result
    except Exception,e:
        result = {'success':False,'msg':"Manage-Truck-table: " + str(e)}
        return result


@bottle.route('/json/manage-truck-storage-table')
def jsonManageTruckStorageTable(db,uiSession):
    try:
        from widgethooks import _typeCategoryNameMap
        
        modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db,modelId)
        typename = _getOrThrowError(bottle.request.params,'typename')
        unique = _getOrThrowError(bottle.request.params,'unique')
        
        ### These are hear to make sure they are present
        #sord = _getOrThrowError(bottle.request.params,'sord')
        #page = _getOrThrowError(bottle.request.params,'page',isInt=True)
        #rowsPerPage = _getOrThrowError(bottle.request.params,'rows',isInt=True)
        #sidx = _getOrThrowError(bottle.request.params,'sidx')
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        if typename != "new":    
            truck = typehelper.getTypeWithFallback(db, modelId, typename)[1]
            storageList = truck.getStorageDeviceList(m)
            tDictDict= {}
            if storageList is not None:
                for count,dev in storageList:
                    print dev.Name
                    if count > 0:
                        if dev.Name in tDictDict:
                            d = tDictDict[dev.Name]
                            d['count'] += count
                            d['freezer'] += dev.freezer
                            d['cooler'] += dev.cooler
                            d['roomtemperature'] += dev.roomtemperature
                        else:
                            tDictDict[dev.Name] = {'Name':dev.Name,
                                                      'count':count, 
                                                      'category':"fridges",
                                                      'description':dev.getDisplayName(),
                                                      'freezer':dev.freezer,
                                                      'cooler':dev.cooler,
                                                      'roomtemperature':dev.roomtemperature}
                        
            totals = {"description":"Totals","freezer":0.0, "cooler":0.0, "warm":0.0, "count":0}
            for dev in tDictDict.values():
                totals['freezer'] += dev['count']*dev['freezer']
                totals['cooler'] += dev['count']*dev['cooler']
                totals['warm'] += dev['count']*dev['roomtemperature']
                totals['count'] += dev['count'] 
            
            totals['freezer'] = round(totals['freezer'],2)
            totals['cooler'] = round(totals['cooler'],2)
            totals['warm'] = round(totals['warm'],2)
            nPages,thisPageNum,totRecs,tList = orderAndChopPage(tDictDict.values(),
                                                                {'typestring':'Name', 'count':'count',
                                                                 'category':'category',
                                                                 'cool':'cooler','freeze':'freezer',
                                                                 'warm':'roomtemperature'},
                                                                bottle.request,
                                                                defaultSortIndex='typestring')
            rows = [ {"name":t['Name'], 
                             "cell":[t['Name'], t['count'], t['Name'],t['description'], t['freezer'], t['cooler'],
                                     t['roomtemperature'], t['count'], t['Name']]}
                           for t in tList ]
        else:
            nPages = 1
            thisPageNum = 1
            totRecs = 0
            rows = []
            totals = {"description":"Totals","freezer":0.0, "cooler":0.0, "warm":0.0, "count":0}
            
        
        #print "{0} {1} {2} {3}".format(nPages,thisPageNum,totRecs,tList)
        result = {
                  "success":True,
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": rows,
                  "userdata":totals
                  }
        
        return result
            
    except Exception,e:
        result = {'success':False,'msg':"Manage-Truck-Storage-Table: {0}".format(str(e))}
        return result

@bottle.route('/json/update-truck-storage',method='POST')
def updateTruckStrorage(db,uiSession):
    import json
    from sqlalchemy.orm.exc import NoResultFound
    
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        typename = _getOrThrowError(bottle.request.params, 'typename')
        unique = _safeGetReqParam(bottle.request.params, 'unique', isInt=True)
        
        try:
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        except NoResultFound:
            raise bottle.BottleException(_("No such model {0}").format(modelId))
        
        truckTup = typehelper.getTypeWithFallback(db, modelId, typename)
        if truckTup[0]:
            truck = truckTup[1]
        storeString = ""
        offset = 0
        while True:
            count = _safeGetReqParam(bottle.request.params,"storedata[%d][%s]"%(offset,'count'),isInt=True)
            if count is not None:
                name = _getOrThrowError(bottle.request.params,"storedata[%d][%s]"%(offset,'visibletypename'))
                countString = ''
                if count > 1:
                    countString = "{0}*".format(count)
                storeString += "{0}{1}+".format(countString,name)
                offset+=1
            else:
                break
        storeString = storeString[:-1]
        truck.Storage = storeString
        
        return {'success':True,'msg':'Truck type {0} for modelId {1} has been successfully updated'.format(typename,modelId) }    
    except Exception,e:
        result = {'success':False,'msg':str(e)}
        return result

@bottle.route('/json/manage-truck-explorer',method='POST')
def jsonManageTruckExplorerTable(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        searchTerm = _safeGetReqParam(bottle.request.params, 'searchterm', default=None)
        #searchTerm = u"{0}".format(searchTermStr)
        excludeTypesFromModel = _safeGetReqParam(bottle.request.params,'excludeTypesFromModel',isInt=True,default=-1)
        newTypesJson = _safeGetReqParam(bottle.request.params,'newTypes',default='[]')
        newTypes = json.loads(newTypesJson)
        newTypesOnly = _safeGetReqParam(bottle.request.params,'newTypesOnly',isBool=True,default=False)
        #forLevelOnlyArg = _safeGetReqParam(bottle.request.params,'forLevelOnly',default=None)
        #if forLevelOnlyArg == "":
        #    forLevelOnly = None
        #else:
        #    forLevelOnly = forLevelOnlyArg
        
        deviceCountsJson = _safeGetReqParam(bottle.request.params,'deviceCounts',default='{}')
        deviceCounts = json.loads(deviceCountsJson)
            
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException(_('Current User does not have access to model with Id = {0}: from json/manaage-truck-explorer'.format(modelId)))
    except ValueError, e:
        print 'Empty parameters supplied to manage-truck-explorer'
        print str(e)
        return {'success': 'false'}
    try:
        tList = typehelper.getTypeList(db,modelId,'trucks',fallback=False)
        #print tList
        
        exTList = []
        if excludeTypesFromModel > -1:
            exTList = [x['Name'] for x in typehelper.getTypeList(db,excludeTypesFromModel,'fridges',fallback=False)]
        
        
        rows = []
        for v in tList:
            if v['Name'] in exTList:
                continue
            rank=20
            
           
            
            if len(newTypes) > 0:
                if v['Name'] in newTypes:
                    rank=1
            
            if newTypesOnly:
                if v['Name'] not in newTypes:
                    continue
            
            count = 1
            
            if v['Name'] in deviceCounts.keys():
                count = int(deviceCounts[v['Name']])
            
            cat = v['Category']
            if cat is None or cat == "":
                cat = u'Other'
                
            row = {'id':v['Name'],
                   'name':v['DisplayName'],
                   'type':cat,
                   'details':v['Name'],
                   'rank': rank,
                   'count':count
                   }
            
            if searchTerm:
                ## does this match name, manufacturer...
                for v in row.values():
                    if v.lower().find(searchTerm.lower()) > -1:
                        rows.append(row)
                        break
            else:
                rows.append(row)
            #rows.append(row)
            
        return {'success':True,
                'total':1,
                'page':1,
                'records':len(rows),
                'rows':rows
                }
    except Exception,e:
        return {'success':False,'msg':'manage-vaccine-table-all: {0}'.format(str(e))}
    
