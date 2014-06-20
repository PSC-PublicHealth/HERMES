#!/usr/bin/env python

_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types
import bottle
import urllib
import ipath
import shadow_network_db_api
import shadow_network
import session_support_wrapper as session_support
from serverconfig import rootPath
from HermesServiceException import HermesServiceException
from gridtools import orderAndChopPage
import privs
import htmlgenerator
import typehelper

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _safeGetReqParam

inlizer=session_support.inlizer
_=session_support.translateString

@bottle.route('/cost-top')
def costTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Costs")))
    return bottle.template("cost_top.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Costs")})

@bottle.route('/cost-edit-power')
@bottle.route('/cost-edit-truck')
@bottle.route('/cost-edit-fridge')
@bottle.route('/cost-edit-vaccine')
@bottle.route('/cost-edit-salary')
@bottle.route('/cost-edit-building')
@bottle.route('/cost-check-complete')
def costUnimplemented(db, uiSession):
    bottle.redirect('%snotimpl'%rootPath)

@bottle.route('/cost-edit-fuel')
def costEditFuel(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Fuel")))
    return bottle.template("cost_edit_fuel.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Costs")})

def _getCurrencyDict(db, modelId):
    return {'EUR':'Euro', 'USD':'US Dollars', 'THB':'Thai Bhat'}


@bottle.route('/list/select-currency')
def handleListCurrency(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        selectedCurrencyId = _safeGetReqParam(bottle.request.params, 'idstring')
        if selectedCurrencyId is None and 'defaultCurrencyId' in uiSession:
            selectedCurrencyId = uiSession['defaultCurrencyId']
        selectedCurrencyName = ''
        pairs = _getCurrencyDict(db, modelId).items()
        s = ""
        for thisId,name in pairs: 
            if selectedCurrencyId is None:
                uiSession['defaultCurrencyId'] = selectedCurrencyId = thisId
                s += "<option value=%s selected>%s</option>\n"%(urllib.quote(thisId),urllib.quote(name))
                selectedCurrencyName = name
            elif thisId == selectedCurrencyId:
                s += "<option value=%s selected>%s</option>\n"%(urllib.quote(thisId),urllib.quote(name))
                selectedCurrencyName = name
            else:
                s += "<option value=%s>%s</option>\n"%(urllib.quote(thisId),urllib.quote(name))
        quotedPairs = [(urllib.quote(a), urllib.quote(b)) for a,b in pairs]
        return {"menustr":s, "pairs":quotedPairs, 
                "selid":urllib.quote(selectedCurrencyId), 
                "selname":urllib.quote(selectedCurrencyName), "success":True}
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/get-default-currency')
def jsonGetDefaultCurrency(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        if 'defaultCurrencyId' in uiSession:
            currencyId = uiSession['defaultCurrencyId']
            result = { 'id':urllib.quote(currencyId), 'name':urllib.quote(_getCurrencyDict(db,modelId)[currencyId]), 'success':True }
        else:
            result = { 'id':None, 'name':None, 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 
        

@bottle.route('/json/set-default-currency')
def jsonSetDefaultCurrency(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        rawCurrencyId = _getOrThrowError(bottle.request.params, 'id') # Note that this is a string!
        currencyId = urllib.unquote(rawCurrencyId)
        uiSession['defaultCurrencyId'] = currencyId
        result = { 'id':rawCurrencyId, 'name':urllib.quote(_getCurrencyDict(db,modelId)[currencyId]), 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 
        
