#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id$"

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

from ui_utils import _logMessage, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults

inlizer=session_support.inlizer
_=session_support.translateString

fieldMap = [{'row':1, 'label':_('Name'), 'key':'Name', 'id':'name', 'type':'string'},
            {'row':1, 'label':_('DisplayName'), 'key':'DisplayName', 'id':'displayname', 'type':'string'},
            {'row':1, 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'type':'string'},
            {'row':2, 'label':_('Storage'), 'key':'Storage', 'id':'storage', 'type':'string'},  
            {'row':2, 'label':_('CoolVolume (cc)'), 'key':'CoolVolumeCC', 'id':'coolvolumecc', 'type':'float'},
            {'row':2, 'label':_('Requires'), 'key':'Requires', 'id':'requires', 'type':'string'},
            {'row':3, 'label':_('Base Price'), 'key':'BaseCost', 'id':'baseprice', 'type':'price'},  
            {'row':3, 'label':_('Price Units'), 'key':'BaseCostCur', 'id':'basecostcur', 'type':'currency'},   
            {'row':3, 'label':_('Price Year'), 'key':'BaseCostYear', 'id':'basecostyear', 'type':'int'},  
            {'row':4, 'label':_('Km To Amortize'), 'key':'AmortizationKm', 'id':'amortkm', 'type':'float'},
            {'row':4, 'label':_('Fuel'), 'key':'Fuel', 'id':'fuel', 'type':'fuel'},
            {'row':4, 'label':_('Fuel Consumption'), 'key':'FuelRate', 'id':'fuelrate', 'type':'float'},
            {'row':4, 'label':_('Units'), 'key':'FuelRateUnits', 'id':'fuelunits', 'type':'hide'},
            ]

@bottle.route('/truck-top')
def truckTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Transport")))
    return bottle.template("truck_top.tpl",{"breadcrumbPairs":crumbTrack})

@bottle.route('/truck-edit')
def truckEditPage(db, uiSession):
    try:
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in bottle.request.params.items()]
        _logMessage("Hit truck-edit; params=%s"%paramList)
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        protoName = _getOrThrowError(bottle.request.params,'protoname')
        protoName = _smartStrip(protoName)
        crumbTracks = uiSession.getCrumbs().push((bottle.request.path,_("Create Modified Version")))
        return bottle.template("truck_edit.tpl",{"breadcrumbPairs":crumbTracks,
                               "protoname":protoName,"modelId":modelId})
    except Exception,e:
        return bottle.template("error.tpl",{"breadcrumbPairs":uiSession.getCrumbs(),
                               "bugtext":str(e)})

@bottle.route('/edit/edit-truck.json', method='POST')
def editTruck(db,uiSession):  
    if bottle.request.params['oper']=='edit':
        if 'modelId' not in bottle.request.params.keys():
            return {}
        modelId = int(bottle.request.params['modelId'])
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = bottle.request.params['name']
        _logMessage("Name = %s"%name)
        pT = m.trucks[name]
        if 'dispnm' in bottle.request.params:
            _logMessage("New Display Name = %s"%bottle.request.params['dispnm'])
            pT.DisplayName = bottle.request.params['dispnm']
        return {}
    elif bottle.request.params['oper']=='add':
        raise bottle.BottleException(_('unsupported operation'))
    elif bottle.request.params['oper']=='del':
        raise bottle.BottleException(_('unsupported operation'))

        
@bottle.route('/json/manage-truck-table')
def jsonManageTruckTable(db, uiSession):
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
    
@bottle.route('/json/truck-edit-verify-commit')
def jsonTruckEditVerifyCommit(db, uiSession):
    m,attrRec,badParms,badStr = _mergeFormResults(bottle.request, db, uiSession, fieldMap) # @UnusedVariable
            # FuelRateUnits is completely determined by energy type
    if attrRec['Fuel']:
        attrRec['FuelRateUnits'] = fuelTranslationDict[attrRec['Fuel'].encode('utf-8')][2]
    else:
        attrRec['FuelRateUnits'] = None
    if badStr and badStr!="":
        result = {'success':True, 'value':False, 'msg':badStr}
    else:
        newTruck = shadow_network.ShdTruckType(attrRec.copy()) 
        db.add(newTruck)
        m.types[attrRec['Name']] = newTruck
        crumbTrack = uiSession.getCrumbs().pop()
        result = {'success':True, 'value':True, 'goto':crumbTrack.currentPath()}
    return result
            
@bottle.route('/json/truck-info')
def jsonTruckInfo(db, uiSession):
    try:
        modelId = int(bottle.request.params['modelId'])
        name = bottle.request.params['name']
        htmlStr, titleStr = htmlgenerator.getTruckInfoHTML(db,uiSession,modelId,name)
        result = {'success':True, "htmlstring":htmlStr, "title":titleStr}
        return result
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        return result
    
@bottle.route('/json/truck-edit-form')
def jsonTruckEditForm(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        protoname = _getOrThrowError(bottle.request.params, 'protoname')
        proposedName = typehelper.getSuggestedName(db,modelId,"truck", protoname, excludeATM=True)
        canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, protoname) # @UnusedVariable
        attrRec = {}
        shadow_network._copyAttrsToRec(attrRec,typeInstance)
        htmlStr, titleStr = htmlgenerator.getTypeEditHTML(db,uiSession,"truck",modelId,protoname,
                                                          typehelper.elaborateFieldMap(proposedName, attrRec,
                                                                                       fieldMap))
        result = {"success":True, "htmlstring":htmlStr, "title":titleStr}
    except privs.PrivilegeException:
        result = {'success':False, 'msg':_('User cannot read this model')}
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
    return result  

