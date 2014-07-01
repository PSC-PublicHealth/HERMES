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
import costmodel
import typehelper

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _safeGetReqParam

inlizer=session_support.inlizer
_=session_support.translateString

@bottle.route('/cost-top')
def costTopPage(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Costs")))
    if 'selectedModelId' in uiSession:
        _maybeScanCurrencyTable(db, uiSession['selectedModelId'])
        minYear = _currencyInfoTuple[0]
        maxYear = _currencyInfoTuple[1]
    else:
        minYear = 2002
        maxYear = 2011
    return bottle.template("cost_top.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Costs"),
                                           "minYear":minYear, "maxYear":maxYear})

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

@bottle.route('/cost-edit-fridge')
def costEditFridge(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Storage")))
    return bottle.template("cost_edit_fridge.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Costs")})

_currencyInfoTuple = None
_currencyModelId = None

def _maybeScanCurrencyTable(db, modelId):
    global _currencyInfoTuple
    global _currencyModelId
    if modelId == _currencyModelId and _currencyInfoTuple is not None:
        return
    m = shadow_network_db_api.ShdNetworkDB(db, modelId)
    start = True
    minYear = None
    maxYear = None
    currencyDict = {}
    for rec in m.currencyTable:
        if start:
            start = False
            minYear = rec.year
            maxYear = rec.year
            code = rec.code.strip()
            currencyDict[code] = rec.currency.strip()
        else:
            if rec.year < minYear: minYear = rec.year
            elif rec.year > maxYear: maxYear = rec.year
            code = rec.code.strip()
            if code not in currencyDict:
                currencyDict[code] = rec.currency.strip()
    _currencyInfoTuple = (minYear, maxYear, currencyDict)
    _currencyModelId = modelId
            
    

def getCurrencyDict(db, modelId):
    _maybeScanCurrencyTable(db, modelId)
    return _currencyInfoTuple[2]

@bottle.route('/list/select-currency')
def handleListCurrency(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        selectedCurrencyId = _safeGetReqParam(bottle.request.params, 'idstring')
        if 'defaultCurrencyId' not in uiSession: uiSession['defaultCurrencyId'] = 'EUR'
        if (selectedCurrencyId is None or selectedCurrencyId=='') and 'defaultCurrencyId' in uiSession:
            selectedCurrencyId = uiSession['defaultCurrencyId']
        selectedCurrencyName = ''
        orderedPairs = [(b,a) for a,b in getCurrencyDict(db, modelId).items()]
        orderedPairs.sort()
        s = ""
        for name, thisId in orderedPairs: 
            if selectedCurrencyId is None:
                uiSession['defaultCurrencyId'] = selectedCurrencyId = thisId
                s += "<option value=%s selected>%s</option>\n"%(urllib.quote(thisId),urllib.quote(name))
                selectedCurrencyName = name
            elif thisId == selectedCurrencyId:
                s += "<option value=%s selected>%s</option>\n"%(urllib.quote(thisId),urllib.quote(name))
                selectedCurrencyName = name
            else:
                s += "<option value=%s>%s</option>\n"%(urllib.quote(thisId),urllib.quote(name))
        quotedPairs = [(urllib.quote(a), urllib.quote(b)) for a,b in orderedPairs]
        return {"menustr":s, "pairs":quotedPairs, 
                "selid":urllib.quote(selectedCurrencyId), 
                "selname":urllib.quote(selectedCurrencyName), "success":True}
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}

@bottle.route('/json/set-currency-base-year')
def jsonSetCurrencyBaseYear(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        baseYear = _getOrThrowError(bottle.request.params, 'baseYear', isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        m.addParm(shadow_network.ShdParameter('currencybaseyear',str(baseYear)))

        result = { 'baseYear':baseYear, 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/set-cost-inflation-percent')
def jsonSetCostInflationPercent(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        inflation = _getOrThrowError(bottle.request.params, 'inflation', isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        m.addParm(shadow_network.ShdParameter('priceinflation',str(0.01*inflation)))

        result = { 'inflation':inflation, 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/get-currency-info')
def jsonGetCurrencyInfo(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        baseCurrencyId = m.getParameterValue('currencybase')
        currencyBaseYear = m.getParameterValue('currencybaseyear')
        priceInflation = int(round(100*m.getParameterValue('priceinflation')))
        result = { 'success':True, 'baseCurrencyId':baseCurrencyId, 'currencyBaseYear':currencyBaseYear,
                  'priceInflation':priceInflation,
                  'fuelLabel':getFuelButtonLabel(db, uiSession, m),
                  'truckLabel':getTruckButtonLabel(db, uiSession, m),
                  'fridgeLabel':getFridgeButtonLabel(db, uiSession, m),
                  'vaccineLabel':getVaccineButtonLabel(db, uiSession, m),
                  'salaryLabel':getSalaryButtonLabel(db, uiSession, m),
                  'buildingLabel':getBuildingButtonLabel(db, uiSession, m),
                  }
        return result
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
            result = { 'id':urllib.quote(currencyId), 'name':urllib.quote(getCurrencyDict(db,modelId)[currencyId]), 'success':True }
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
        result = { 'id':rawCurrencyId, 'name':urllib.quote(getCurrencyDict(db,modelId)[currencyId]), 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/get-base-currency')
def jsonGetBaseCurrency(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        baseCurrency = m.getParameterValue('currencybase')
        result = { 'id':urllib.quote(baseCurrency), 'name':urllib.quote(getCurrencyDict(db,modelId)[baseCurrency]), 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 
        
        
@bottle.route('/json/set-base-currency')
def jsonSetBaseCurrency(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        rawCurrencyId = _getOrThrowError(bottle.request.params, 'id') # Note that this is a string!
        currencyId = urllib.unquote(rawCurrencyId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        m.addParm(shadow_network.ShdParameter('currencybase',currencyId))
        uiSession['defaultCurrencyId'] = currencyId
        result = { 'id':rawCurrencyId, 'name':urllib.quote(getCurrencyDict(db,modelId)[currencyId]), 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

_fuelNames = {'propane':'pricepropaneperkg', 'kerosene':'pricekeroseneperl', 
              'gasoline':'pricegasolineperl', 'diesel':'pricedieselperl', 
              'electric':'priceelectricperkwh','solar':'pricesolarperkw'}

def getFuelButtonLabel(db, uiSession, m):
    vList = _fuelNames.values();
    nSet = sum([v is not None and v!='' for v in [m.getParameterValue(vv) for vv in vList]])
    print '!!!!! nSet: %d len: %d'%(nSet, len(vList))
    if nSet==0: return _("Begin")
    elif nSet==len(vList): return _("Revisit")
    else: return _("Continue")

def getTruckButtonLabel(db, uiSession, m):
    return _("Unimplemented");

def getFridgeButtonLabel(db, uiSession, m):
    return _("Unimplemented");

def getVaccineButtonLabel(db, uiSession, m):
    return _("Unimplemented");

def getSalaryButtonLabel(db, uiSession, m):
    return _("Unimplemented");

def getBuildingButtonLabel(db, uiSession, m):
    return _("Unimplemented");


def _getCurrencyConverter(db, uiSession, m):
    currencyBase = m.getParameterValue('currencybase')
    currencyBaseYear = m.getParameterValue('currencybaseyear')
    if 'currencyConverter' not in uiSession or 'currencyConverterModelId' not in uiSession \
        or uiSession['currencyConverterModelId'] != m.modelId \
        or uiSession['currencyConverter'].getBaseCurrency() != currencyBase \
        or uiSession['currencyConverter'].getBaseYear() != currencyBaseYear:
            uiSession['currencyConverter'] = costmodel.CurrencyConverter( m.getCurrencyTableRecs(),
                                                                          currencyBase, currencyBaseYear )
            uiSession['currencyConverterModelId'] = m.modelId
            uiSession.changed()

    return uiSession['currencyConverter']

@bottle.route('/json/get-fuel-price-info')
def jsonGetFuelPriceInfo(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        currencyBase = m.getParameterValue('currencybase')
        currencyConverter = _getCurrencyConverter(db, uiSession, m)
        result = {}
        for fuel,fuelParamName in _fuelNames.items():
            fuelCurString = '%sCurrency'%fuel
            fuelPriceString = '%sPrice'%fuel
            if fuelCurString not in uiSession: uiSession[fuelCurString] = currencyBase
            result[fuelCurString] = urllib.quote(uiSession[fuelCurString])
            fuelPrice = m.getParameterValue(fuelParamName)
            if fuelPrice is None:
                result[fuelPriceString] = None
            else:
                result[fuelPriceString] = currencyConverter.convertTo(currencyBase, fuelPrice, uiSession[fuelCurString])
        result['success'] = True
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/set-fuel-price/<fuelName>')
def jsonSetFuelPrice(db, uiSession, fuelName):
    try:
        assert fuelName in _fuelNames.keys(), _("{0} is not a valid fuel type").format(fuelName)
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        currencyId = urllib.unquote(_getOrThrowError(bottle.request.params, 'id'))
        currencyParamName = _fuelNames[fuelName]
        price = _safeGetReqParam(bottle.request.params, 'price', isFloat=True)
        priceInBaseCurrency = _getCurrencyConverter(db, uiSession, m).convertTo(currencyId,price,
                                                                                m.getParameterValue('currencybase'))
        m.addParm(shadow_network.ShdParameter(currencyParamName, priceInBaseCurrency))
        result = {'success':True, 'price':price, 'id':urllib.quote(currencyId)}
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/set-fuel-price-currency/<fuelName>')
def jsonSetFuelPriceCurrency(db, uiSession, fuelName):
    try:
        assert fuelName in _fuelNames.keys(), _("{0} is not a valid fuel type").format(fuelName)
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        currencyId = urllib.unquote(_getOrThrowError(bottle.request.params, 'id'))
        currencyParamName = _fuelNames[fuelName]
        price = _safeGetReqParam(bottle.request.params, 'price', isFloat=True)
        paramPrice = m.getParameterValue(currencyParamName)
        converter = _getCurrencyConverter(db, uiSession, m)
        if paramPrice is None: priceInTargetCurrency = None
        else: priceInTargetCurrency = converter.convertTo(converter.getBaseCurrency(),paramPrice, currencyId)
        result = {'success':True, 'price':priceInTargetCurrency, 'id':urllib.quote(currencyId)}
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/manage-fridge-cost-table')
def jsonManageFridgeTable(db, uiSession):
    modelId = int(bottle.request.params['modelId'])
    try:
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d'%modelId)
    tList = typehelper.getTypeList(db, modelId, 'fridges', fallback=False)
    for rec in tList:
        if 'DisplayName' not in rec['DisplayName'] \
            or rec['DisplayName'] is None or rec['DisplayName']=='':
            rec['DisplayName'] = rec['Name']
    nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                        {'name':'DisplayName'},
                                                        bottle.request)
    result = {
              "total":nPages,    # total pages
              "page":thisPageNum,     # which page is this
              "records":totRecs,  # total records
              "rows": [ {"name":t['DisplayName'], 
                         "cell":[t['DisplayName'], 'foo', 'bar', 'mycurrency', t['Name']]}
                       for t in tList ]
              }
    return result
    
