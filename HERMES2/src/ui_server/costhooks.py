#!/usr/bin/env python

_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types
import bottle
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
from fridgetypes import energyTranslationDict
import currencyhelper

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _safeGetReqParam, _mergeFormResults

from microcostmodel import priceKeyTable as _fuelNames

inlizer=session_support.inlizer
_=session_support.translateString

@bottle.route('/cost-top')
def costTopPage(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Costs")))
    if 'selectedModelId' in uiSession:
        minYear = currencyhelper.getCurrencyMinYear(db, uiSession['selectedModelId'])
        maxYear = currencyhelper.getCurrencyMaxYear(db, uiSession['selectedModelId'])
    else:
        aTMId = typehelper._getAllTypesModel(db).modelId
        minYear = currencyhelper.getCurrencyMinYear(db, aTMId)
        maxYear = currencyhelper.getCurrencyMaxYear(db, aTMId)
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

@bottle.route('/cost-edit-fridge2')
def costEditFridge2(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Storage")))
    return bottle.template("cost_edit_fridge_version2.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Costs Version 2")})

@bottle.route('/cost-edit-fridge3')
def costEditFridge3(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Storage")))
    return bottle.template("cost_edit_fridge_version3.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Costs Version 3")})

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
        orderedPairs = [(b,a) for a,b in currencyhelper.getCurrencyDict(db, modelId).items()]
        orderedPairs.sort()
        s = ""
        for name, thisId in orderedPairs: 
            if selectedCurrencyId is None:
                #print thisId
                uiSession['defaultCurrencyId'] = selectedCurrencyId = thisId
                s += "<option value=%s selected>%s</option>\n"%(thisId,name)
                selectedCurrencyName = name
            elif thisId == selectedCurrencyId:
                s += "<option value=%s selected>%s</option>\n"%(thisId,name)
                selectedCurrencyName = name
            else:
                s += '<option value="%s">"%s"</option>\n'%(thisId,name)
        quotedPairs = [(a, b) for a,b in orderedPairs]
        return {"menustr":s, "pairs":quotedPairs, 
                "selid":selectedCurrencyId, 
                "defaultid":uiSession['defaultCurrencyId'],
                "selname":selectedCurrencyName, "success":True}
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
        microCostingEnabled = (m.getParameterValue('costmodel') == 'micro1')
        result = { 'success':True, 'baseCurrencyId':baseCurrencyId, 'currencyBaseYear':currencyBaseYear,
                  'priceInflation':priceInflation,
                  'microCostingEnabled':microCostingEnabled,
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
            result = { 'id':currencyId, 
                      'name':currencyhelper.getCurrencyDict(db,modelId)[currencyId],
                      'success':True }
        else:
            result = { 'id':None, 'name':None, 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/set-microcosting-enabled')
def jsonSetMicroCostingEnabled(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        enableFlag = _getOrThrowError(bottle.request.params, 'enabled', isBool=True)
        if enableFlag:
            m.addParm(shadow_network.ShdParameter('costmodel','micro1'))
        else:
            m.addParm(shadow_network.ShdParameter('costmodel','legacy')) # falls back to default automatically
        return {'success':True,
                'microCostingEnabled':(m.getParameterValue('costmodel')=='micro1')
                }
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 
    
@bottle.route('/json/cost-check-completeness')
def jsonCostCheckCompleteness(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        costModelVerifier = costmodel.getCostModelVerifier(m)
        problemList = costModelVerifier.getProblemList(m)
        if len(problemList) == 0:
            if m.getParameterValue('costmodel')=='micro1':
                msg = _("This model is ready to run with microcosting.")
            else:
                msg = _("This model is ready to run with legacy costing or no cost analysis.")
            return {"success":True, "value":True,
                    "msg":msg
                    }
        else:
            return {"success":True, "value":False,
                    'msgList':problemList,
                    "msg":_("The cost information for this model is not complete")
                    }
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 
    

@bottle.route('/json/set-default-currency')
def jsonSetDefaultCurrency(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        currencyId = _getOrThrowError(bottle.request.params, 'id') # Note that this is a string!
        uiSession['defaultCurrencyId'] = currencyId
        result = { 'id':currencyId, 
                  'name':currencyhelper.getCurrencyDict(db,modelId)[currencyId], 
                  'success':True }
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
        result = { 'id':baseCurrency, 
                  'name':currencyhelper.getCurrencyDict(db,modelId)[baseCurrency], 
                  'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 
        
        
@bottle.route('/json/set-base-currency')
def jsonSetBaseCurrency(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        currencyId = _getOrThrowError(bottle.request.params, 'id') # Note that this is a string!
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        m.addParm(shadow_network.ShdParameter('currencybase',currencyId))
        uiSession['defaultCurrencyId'] = currencyId
        result = { 'id':currencyId, 
                  'name':currencyhelper.getCurrencyDict(db,modelId)[currencyId], 
                  'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

def getFuelButtonLabel(db, uiSession, m):
    vList = []
    for val in _fuelNames.values():
        if isinstance(val, types.TupleType):
            vList += list(val)
        else:
            vList.append(val)
    nSet = sum([v is not None and v!='' and v!=0.0 for v in [m.getParameterValue(vv) for vv in vList]])
    if nSet==0: return _("Begin")
    elif nSet==len(vList): return _("Revisit")
    else: return _("Continue")

def getFridgeButtonLabel(db, uiSession, m):
    count = 0
    possible = 0
    tList = typehelper.getTypeList(db, m.modelId, 'fridges', fallback=False)
    for t in tList:
        for fld in ['BaseCost','BaseCostCur','BaseCostYear','PowerRate']:
            v = t[fld]
            possible += 1
            if not(v is None or v=='' or v<0): count += 1
    if count == 0: return _("Begin")
    elif count == possible: return _("Revisit")
    else: return _("Continue")

def getTruckButtonLabel(db, uiSession, m):
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
    inflationRate = m.getParameterValue('priceinflation')
    if 'currencyConverter' not in uiSession or 'currencyConverterModelId' not in uiSession \
        or uiSession['currencyConverterModelId'] != m.modelId \
        or uiSession['currencyConverter'].getBaseCurrency() != currencyBase \
        or uiSession['currencyConverter'].getBaseYear() != currencyBaseYear \
        or uiSession['currencyConverter'].getInflationRate() != inflationRate:
            uiSession['currencyConverter'] = costmodel.CurrencyConverter( m.getCurrencyTableRecs(),
                                                                          currencyBase, currencyBaseYear,
                                                                          inflationRate )
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
            fuelValueString = '%sValue'%fuel
            if fuelCurString not in uiSession: uiSession[fuelCurString] = currencyBase
            result[fuelCurString] = uiSession[fuelCurString]
            if isinstance(fuelParamName, types.TupleType):
                fuelAmortName = fuelParamName[1]
                fuelParamName = fuelParamName[0]
                fuelAmortString = '%samortValue'%fuel
                fuelPrice = m.getParameterValue(fuelParamName)
                #print "%s: %s"%(fuelParamName, fuelPrice)
                if fuelPrice is None:
                    result[fuelValueString] = None
                else:
                    result[fuelValueString] = currencyConverter.convertTo(fuelPrice, currencyBase, uiSession[fuelCurString])
                fuelAmort = m.getParameterValue(fuelAmortName)
                result[fuelAmortString] = fuelAmort
            else:
                fuelPrice = m.getParameterValue(fuelParamName)
                #print "%s: %s"%(fuelParamName, fuelPrice)
                if fuelPrice is None:
                    result[fuelValueString] = None
                else:
                    result[fuelValueString] = currencyConverter.convertTo(fuelPrice, currencyBase, uiSession[fuelCurString])
        print result
        result['success'] = True
        #print 'returning %s'%result
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/json/set-fuel-price/<fuelName>')
@bottle.route('/json/set-fuel-price-currency/<fuelName>')
def jsonSetFuelPrice(db, uiSession, fuelName):
    """
    This also handles setting of amortization lifetime, based on the presence of suffix 'amort'
    """
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        currencyId = _getOrThrowError(bottle.request.params, 'id')
        if fuelName.endswith('amort'):
            fuelName = fuelName[:-len('amort')]
            assert fuelName in _fuelNames.keys(), _("{0} is not a valid fuel type").format(fuelName)
            tpl = _fuelNames[fuelName]
            assert isinstance(tpl, types.TupleType), _("The fuel {0} has no amortization period".format(fuelName))
            fuelAmortName = tpl[1]
            amort = _safeGetReqParam(bottle.request.params, 'price', isFloat=True)
            if amort is not None and amort!='':
                m.addParm(shadow_network.ShdParameter(fuelAmortName, amort))
            result = {'success':True, 'price':amort, 'id':None}

        else:
            assert fuelName in _fuelNames.keys(), _("{0} is not a valid fuel type").format(fuelName)
            currencyParamName = _fuelNames[fuelName]
            if isinstance(currencyParamName, types.TupleType):
                currencyParamName = currencyParamName[0]
            price = _safeGetReqParam(bottle.request.params, 'price', isFloat=True)
            if price is not None and price!='':
                priceInBaseCurrency = _getCurrencyConverter(db, uiSession, m).convertTo(price, currencyId,
                                                                                        m.getParameterValue('currencybase'))
                m.addParm(shadow_network.ShdParameter(currencyParamName, priceInBaseCurrency))
            result = {'success':True, 'price':price, 'id':currencyId}
        print result
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

# def jsonSetFuelPriceCurrency(db, uiSession, fuelName):
#     try:
#         assert fuelName in _fuelNames.keys(), _("{0} is not a valid fuel type").format(fuelName)
#         modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
#         uiSession.getPrivs().mayReadModelId(db, modelId)
#         m = shadow_network_db_api.ShdNetworkDB(db, modelId)
#         currencyId = urllib.unquote(_getOrThrowError(bottle.request.params, 'id'))
#         currencyParamName = _fuelNames[fuelName]
#         oldPriceInBaseCurrency = m.getParameterValue(currencyParamName)
#         price = _safeGetReqParam(bottle.request.params, 'price', isFloat=True)
#         converter = _getCurrencyConverter(db, uiSession, m)
#         if oldPriceInBaseCurrency is not None:
#             pass
#         if paramPrice is None: priceInTargetCurrency = None
#         else: priceInTargetCurrency = converter.convertTo(paramPrice, converter.getBaseCurrency(), currencyId)
#         result = {'success':True, 'id':urllib.quote(currencyId)}
#         return result
#     except Exception,e:
#         _logStacktrace()
#         return {"success":False, "msg":str(e)} 

@bottle.route('/json/manage-fridge-cost-table-2')
def jsonManageFridgeCostTable2(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        tList = typehelper.getTypeList(db, modelId, 'fridges', fallback=False)
        tList = [t for t in tList if t['Category'] != '-chained-'
                 and t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if 'DisplayName' not in rec \
                or rec['DisplayName'] is None or rec['DisplayName']=='':
                rec['DisplayName'] = rec['Name']
            if 'Category' not in rec \
                or rec['Category'] is None or rec['Category']=='':
                rec['Category'] = _('Uncategorized')
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                            {'category':'Category',
                                                             'name':'Name',
                                                             'displayname':'DisplayName',
                                                             'basecost':'BaseCost',
                                                             'currency':'BaseCostCurCode',
                                                             'basecostyear':'BaseCostYear',
                                                             },
                                                            bottle.request)
        for t in tList:
            for k in ['BaseCost','BaseCostYear','PowerRate']: 
                if t[k] == 0: t[k] = None
            if t['PowerRateUnits'] and energyTranslationDict[t['Energy']][2] and t['PowerRateUnits'].lower() != energyTranslationDict[t['Energy']][2].lower():
                raise RuntimeError("Power units for %s are inconsistent: %s vs. %s"%\
                                   (t['Name'],t['PowerRateUnits'],energyTranslationDict[t['Energy']][2]))
                
        result = {
                  'success':True,
                  "total":1,    # total pages
                  "page":1,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"name":t['Name'],
                            "category":t['Category'],
                            "displayname":t['DisplayName'],
                            "detail":t['Name'],
                            "basecost":t['BaseCost'],
                            "currency":t['BaseCostCur'],
                            "basecostyear":t['BaseCostYear'],
                            "powerrate":t['PowerRate'],
                            "powerrateunits":t['PowerRateUnits'],
                            "energy":energyTranslationDict[t['Energy']][1]
                             }
                           for t in tList if t['Name'] not in typehelper.hiddenTypesSet]
                  }
        return result
    except Exception,e:
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/manage-fridge-cost-table')
def jsonManageFridgeCostTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        tList = typehelper.getTypeList(db, modelId, 'fridges', fallback=False)
        tList = [t for t in tList if t['Category'] != '-chained-'
                 and t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if 'DisplayName' not in rec \
                or rec['DisplayName'] is None or rec['DisplayName']=='':
                rec['DisplayName'] = rec['Name']
            if 'Category' not in rec \
                or rec['Category'] is None or rec['Category']=='':
                rec['Category'] = _('Uncategorized')
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                            {'category':'Category',
                                                             'name':'Name',
                                                             'displayname':'DisplayName',
                                                             'basecost':'BaseCost',
                                                             'currency':'BaseCostCurCode',
                                                             'basecostyear':'BaseCostYear',
                                                             },
                                                            bottle.request)
        for t in tList:
            for k in ['BaseCost','BaseCostYear','PowerRate']: 
                if t[k] == 0: t[k] = None
            if t['PowerRateUnits'] and energyTranslationDict[t['Energy']][2] and t['PowerRateUnits'].lower() != energyTranslationDict[t['Energy']][2].lower():
                raise RuntimeError("Power units for %s are inconsistent: %s vs. %s"%\
                                   (t['Name'],t['PowerRateUnits'],energyTranslationDict[t['Energy']][2]))
                
        result = {
                  'success':True,
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"name":t['Name'], 
                             "cell":[t['Name'],
                                     t['Category'],
                                     t['DisplayName'],
                                     t['Name'],
                                     t['BaseCost'],
                                     t['BaseCostCur'],
                                     t['BaseCostYear'],
                                     t['PowerRate'],
                                     t['PowerRateUnits'],
                                     energyTranslationDict[t['Energy']][1]]
                             }
                           for t in tList if t['Name'] not in typehelper.hiddenTypesSet]
                  }
        return result
    except Exception,e:
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/manage-fridge-cost-table-new')
def jsonManageFridgeCostTableNew(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        tList = typehelper.getTypeList(db, modelId, 'fridges', fallback=False)
        tList = [t for t in tList if t['Category'] != '-chained-'
                 and t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if 'DisplayName' not in rec \
                or rec['DisplayName'] is None or rec['DisplayName']=='':
                rec['DisplayName'] = rec['Name']
            if 'Category' not in rec \
                or rec['Category'] is None or rec['Category']=='':
                rec['Category'] = _('Uncategorized')
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                            {'category':'Category',
                                                             'name':'Name',
                                                             'displayname':'DisplayName',
                                                             'basecost':'BaseCost',
                                                             'currency':'BaseCostCurCode',
                                                             'basecostyear':'BaseCostYear',
                                                             'energy':'Energy'
                                                             },
                                                            bottle.request)
        for t in tList:
            for k in ['BaseCost','BaseCostYear','PowerRate']: 
                if t[k] == 0: t[k] = None
            if t['PowerRateUnits'] and energyTranslationDict[t['Energy']][2] and t['PowerRateUnits'].lower() != energyTranslationDict[t['Energy']][2].lower():
                raise RuntimeError("Power units for %s are inconsistent: %s vs. %s"%\
                                   (t['Name'],t['PowerRateUnits'],energyTranslationDict[t['Energy']][2]))
                
        result = {
                  'success':True,
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"name":t['Name'], 
                             "cell":[t['Name'],
                                     t['Category'],
                                     t['DisplayName'],
                                     t['Name'],
                                     t['BaseCost'],
                                     t['BaseCostCur'],
                                     t['BaseCostYear'],
                                     t['PowerRate'],
                                     "%s:%s %s"%(t['Energy'],
                                                 energyTranslationDict[t['Energy']][2],
                                                 energyTranslationDict[t['Energy']][1])]
                             }
                           for t in tList if t['Name'] not in typehelper.hiddenTypesSet]
                  }
        return result
    except Exception,e:
        print "hello"
        print t
        _logStacktrace()
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/get-cost-info-fridge')
def jsonGetCostInfoFridge(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        amortYears = int(round(m.getParameterValue('amortizationstorageyears')))
        result = { 
                  'success':True,
                  'amortYears':amortYears
                  }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 

@bottle.route('/edit/edit-cost-fridge', method='POST')
def editCostFridge(db, uiSession):
    try:
        #print [(k,v) for k,v in bottle.request.params.items()]
        if bottle.request.params['oper']=='edit':
            modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            typeName = _getOrThrowError(bottle.request.params, 'id')
            if typeName in m.types:
                tp = m.types[typeName]
                for opt in ['category', 'displayname', 'ongoingunits','ongoingwhat']:
                    if opt in bottle.request.params:
                        raise RuntimeError(_('Editing of {0} is not supported').format(opt))
                if 'basecost' in bottle.request.params:
                    tp.BaseCost = _safeGetReqParam(bottle.request.params, 'basecost', isFloat=True)
                if 'currency' in bottle.request.params:
                    tp.BaseCostCurCode = _safeGetReqParam(bottle.request.params, 'currency')
                if 'basecostyear' in bottle.request.params:
                    tp.BaseCostYear = _safeGetReqParam(bottle.request.params, 'basecostyear', isInt=True)
                if 'ongoing' in bottle.request.params:
                    tp.PowerRate = _safeGetReqParam(bottle.request.params, 'ongoing', isFloat=True)
                return {'success':True}
            else:
                raise RuntimeError(_('Model {0} does not contain type {1}').format(m.name, typeName))
        else: raise RuntimeError(_('Unsupported operation {0}').format(bottle.request.params['oper']))
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        _logStacktrace()
        return {'success':False, 'msg':str(e)}
            
@bottle.route('/edit/edit-cost-fridge-new', method='POST')
def editCostFridgeNew(db, uiSession):
    try:
        print [(k,v) for k,v in bottle.request.params.items()]
        if bottle.request.params['oper']=='edit':
            modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            typeName = _getOrThrowError(bottle.request.params, 'id')
            if typeName in m.types:
                tp = m.types[typeName]
                for opt in ['category', 'displayname', 'ongoingunits','ongoingwhat']:
                    if opt in bottle.request.params:
                        raise RuntimeError(_('Editing of {0} is not supported').format(opt))
                if 'basecost' in bottle.request.params:
                    tp.BaseCost = _safeGetReqParam(bottle.request.params, 'basecost', isFloat=True)
                if 'currency' in bottle.request.params:
                    tp.BaseCostCurCode = _safeGetReqParam(bottle.request.params, 'currency')
                if 'basecostyear' in bottle.request.params:
                    tp.BaseCostYear = _safeGetReqParam(bottle.request.params, 'basecostyear', isInt=True)
                if 'ongoing' in bottle.request.params:
                    tp.PowerRate = _safeGetReqParam(bottle.request.params, 'ongoing', isFloat=True)
                if 'energy' in bottle.request.params:
                    eCode = _safeGetReqParam(bottle.request.params, 'energy').split(':')[0]
                    powerRateUnits = energyTranslationDict[eCode][2]
                    tp.Energy = eCode
                    tp.PowerRateUnits = powerRateUnits
                return {'success':True}
            else:
                raise RuntimeError(_('Model {0} does not contain type {1}').format(m.name, typeName))
        else: raise RuntimeError(_('Unsupported operation {0}').format(bottle.request.params['oper']))
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        _logStacktrace()
        return {'success':False, 'msg':str(e)}
            
@bottle.route('/json/set-fridge-amort-years')
def jsonSetFridgeAmortYears(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        amortYears = _getOrThrowError(bottle.request.params, 'amortYears', isInt=True)
        if amortYears is not None and amortYears!='':
            m.addParm(shadow_network.ShdParameter('amortizationstorageyears', amortYears))
        result = {'success':True, 'amortYears':amortYears}
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e), 
                'amortYears':int(round(m.getParameterValue('amortizationstorageyears')))
                } 

    
