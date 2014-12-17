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
from trucktypes import fuelTranslationDict
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

@bottle.route('/cost-edit-fuel')
def costEditFuel(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Fuel")))
    return bottle.template("cost_edit_fuel.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Fuel Costs")})

@bottle.route('/cost-edit-fridge')
def costEditFridge(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Storage")))
    return bottle.template("cost_edit_fridge.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Storage Device Costs")})

@bottle.route('/cost-edit-vaccine')
def costEditVaccine(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Vaccines")))
    return bottle.template("cost_edit_vaccines.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Vaccine Costs")})

@bottle.route('/cost-edit-truck')
def costEditTrucks(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Vehicles")))
    return bottle.template("cost_edit_trucks.tpl",{"breadcrumbPairs":crumbTrack, "title_slogan":_("Vehicle Costs")})


@bottle.route('/cost-edit-salary')
def costEditSalary(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path, _("Salaries")))
    return bottle.template("cost_edit_salary.tpl", {"breadcrumbPairs":crumbTrack,
                                                    "title_slogan":_("Staff Costs")})


@bottle.route('/cost-edit-perdiem')
def costEditPerDiem(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path, _("Per Diem Rates")))
    return bottle.template("cost_edit_perdiem.tpl", {"breadcrumbPairs": crumbTrack,
                                                     "title_slogan": _("Per Diem Rates")})


@bottle.route('/cost-edit-building')
def costEditBuilding(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path, _("Building Costs")))
    return bottle.template("cost_edit_buildings.tpl", {"breadcrumbPairs": crumbTrack,
                                                       "title_slogan": _("Building Costs")})


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
        m = None  # in case of exception
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        baseYear = _getOrThrowError(bottle.request.params, 'baseYear', isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        m.addParm(shadow_network.ShdParameter('currencybaseyear',str(baseYear)))
        result = { 'baseYear':baseYear, 'success':True }
        return result
    except Exception,e:
        _logStacktrace()
        if m:
            return {"success":False, "msg":str(e), "value": m.getParameterValue('currencybaseyear')} 
        else:
            return {"success":False, "msg":str(e)} 

def setModelParamPercent(db, uiSession, key, paramName):
    try:
        m = None  # in case of exception
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        inflation = _getOrThrowError(bottle.request.params, key, isInt=True)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        m.addParm(shadow_network.ShdParameter(paramName, str(0.01 * inflation)))
        result = {key: inflation, 'success': True}
        return result
    except Exception, e:
        _logStacktrace()
        if m:
            return {"success": False, "msg": str(e),
                    "value": int(round(100.0*m.getParameterValue(paramName)))}
        else:
            return {"success": False, "msg": str(e)}


@bottle.route('/json/set-cost-inflation-percent')
def jsonSetCostInflationPercent(db, uiSession):
    return setModelParamPercent(db, uiSession, 'inflation', 'priceinflation')


@bottle.route('/json/set-cost-storage-maint-percent')
def jsonSetCostStorageMaintPercent(db, uiSession):
    return setModelParamPercent(db, uiSession, 'storage_maint', 'storagemaintcostfraction')


@bottle.route('/json/set-cost-vehicle-maint-percent')
def jsonSetCostVehicleMaintPercent(db, uiSession):
    return setModelParamPercent(db, uiSession, 'vehicle_maint', 'vehiclemaintcostfraction')


@bottle.route('/json/get-currency-info')
def jsonGetCurrencyInfo(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        baseCurrencyId = m.getParameterValue('currencybase')
        currencyBaseYear = m.getParameterValue('currencybaseyear')
        priceInflation = int(round(100*m.getParameterValue('priceinflation')))
        storagemaint = int(round(100*m.getParameterValue('storagemaintcostfraction')))
        truckmaint = int(round(100*m.getParameterValue('vehiclemaintcostfraction')))
        microCostingEnabled = (m.getParameterValue('costmodel') == 'micro1')
        vaccineCostsEnabled = m.getParameterValue('vaccinecostsincluded')

        result = {'success': True,
                  'baseCurrencyId': baseCurrencyId,
                  'baseYear': currencyBaseYear,
                  'inflation': priceInflation,
                  'storage_maint': storagemaint,
                  'vehicle_maint': truckmaint,
                  'microCostingEnabled': microCostingEnabled,
                  'vaccineCostsEnabled': vaccineCostsEnabled,
                  'fuelLabel': getFuelButtonLabel(db, uiSession, m),
                  'truckLabel': getTruckButtonLabel(db, uiSession, m),
                  'fridgeLabel': getFridgeButtonLabel(db, uiSession, m),
                  'vaccineLabel': getVaccineButtonLabel(db, uiSession, m),
                  'salaryLabel': getSalaryButtonLabel(db, uiSession, m),
                  'perdiemLabel': getPerDiemButtonLabel(db, uiSession, m),
                  'buildingLabel': getBuildingButtonLabel(db, uiSession, m)
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {"success": False, "msg": str(e)}


@bottle.route('/json/get-default-currency')
def jsonGetDefaultCurrency(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        if 'defaultCurrencyId' in uiSession:
            currencyId = uiSession['defaultCurrencyId']
            result = {'id':currencyId,
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
        enableFlag = _getOrThrowError(bottle.request.params, 'microCostingEnabled', isBool=True)
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


@bottle.route('/json/set-vaccine-costs-included')
def jsonSetVaccineCostsIncluded(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        enableFlag = _getOrThrowError(bottle.request.params, 'vaccineCostsIncluded', isBool=True)
        if enableFlag:
            m.addParm(shadow_network.ShdParameter('vaccinecostsincluded', True))
        else:
            m.addParm(shadow_network.ShdParameter('vaccinecostsincluded', False))
        return {'success': True,
                'vaccineCostsIncluded': m.getParameterValue('vaccinecostsincluded')
                }
    except Exception, e:
        _logStacktrace()
        return {"success": False, "msg": str(e)}


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
        return {"success": False, "msg": str(e)} 


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
        if val is None:  # free fuel
            pass
        elif isinstance(val, types.TupleType):
            vList += list(val)
        else:
            vList.append(val)
    nSet = sum([v is not None and v != '' and v != 0.0
                for v in [m.getParameterValue(vv) for vv in vList if vv is not None]])
    if nSet == 0:
        return _("Begin")
    elif nSet == len(vList):
        return _("Revisit")
    else:
        return _("Continue")


def getTypeButtonLabel(db, uiSession, m, tpCategory, keyList):
    count = 0
    possible = 0
    tList = typehelper.getTypeList(db, m.modelId, tpCategory, fallback=False)
    for t in tList:
        for fld in keyList:
            v = t[fld]
            possible += 1
            if not(v is None or v == '' or v < 0):
                count += 1
    if count == 0:
        return _("Begin")
    elif count == possible:
        return _("Revisit")
    else:
        return _("Continue")


def getFridgeButtonLabel(db, uiSession, m):
    return getTypeButtonLabel(db, uiSession, m, 'fridges', ['BaseCost', 'BaseCostCur',
                                                            'BaseCostYear', 'PowerRate',
                                                            'AmortYears'])


def getTruckButtonLabel(db, uiSession, m):
    return getTypeButtonLabel(db, uiSession, m, 'trucks', ['BaseCost', 'BaseCostCur',
                                                           'BaseCostYear', 'AmortizationKm',
                                                           'FuelRate'])


def getVaccineButtonLabel(db, uiSession, m):
    return getTypeButtonLabel(db, uiSession, m, 'vaccines', ['Vaccine price/vial', 'Price Units',
                                                             'Price Year'])


def getSalaryButtonLabel(db, uiSession, m):
    return getTypeButtonLabel(db, uiSession, m, 'staff', ['BaseSalary', 'BaseSalaryCur',
                                                          'BaseSalaryYear', 'FractionEPI'])


def getPerDiemButtonLabel(db, uiSession, m):
    return getTypeButtonLabel(db, uiSession, m, 'perdiems', ['BaseAmount', 'BaseAmountCur',
                                                             'BaseAmountYear', 'MinKmHome',
                                                             'MustBeOvernight', 'CountFirstDay'])


def getBuildingButtonLabel(db, uiSession, m):
    count = 0
    possible = 0
    keyList = ['SiteCost', 'SiteCostCurCode', 'SiteCostYear']
    for s in m.stores.values():
        for k in keyList:
            possible += 1
            val = getattr(s, k)
            if val is not None and val != '':
                count += 1
    if count == 0:
        return _("Begin")
    elif count == possible:
        return _("Revisit")
    else:
        return _("Continue")


def _getCurrencyConverter(db, uiSession, m):
    currencyBase = m.getParameterValue('currencybase')
    currencyBaseYear = m.getParameterValue('currencybaseyear')
    inflationRate = m.getParameterValue('priceinflation')
    if ('currencyConverter' not in uiSession or 'currencyConverterModelId' not in uiSession
            or uiSession['currencyConverterModelId'] != m.modelId
            or uiSession['currencyConverter'].getBaseCurrency() != currencyBase
            or uiSession['currencyConverter'].getBaseYear() != currencyBaseYear
            or uiSession['currencyConverter'].getInflationRate() != inflationRate):
        uiSession['currencyConverter'] = costmodel.CurrencyConverter(m.getCurrencyTableRecs(),
                                                                     currencyBase,
                                                                     currencyBaseYear,
                                                                     inflationRate)
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
            if fuelParamName is None: continue  # this fuel is free
            fuelCurString = '%sCurrency'%fuel
            fuelValueString = '%sValue'%fuel
            if fuelCurString not in uiSession:
                uiSession[fuelCurString] = currencyBase
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
            fuelCurString = '%sCurrency' % fuelName
            uiSession[fuelCurString] = currencyId
            result = {'success':True, 'price':price, 'id':currencyId}
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)} 


@bottle.route('/json/manage-fridge-cost-table')
def jsonManageFridgeCostTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d' % modelId)
        tList = typehelper.getTypeList(db, modelId, 'fridges', fallback=False)
        tList = [t for t in tList if t['Category'] != '-chained-'
                 and t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if 'DisplayName' not in rec \
                    or rec['DisplayName'] is None or rec['DisplayName'] == '':
                rec['DisplayName'] = rec['Name']
            if 'Category' not in rec \
                    or rec['Category'] is None or rec['Category'] == '':
                rec['Category'] = _('Uncategorized')
        nPages, thisPageNum, totRecs, tList = orderAndChopPage(tList,  # @UnusedVariable
                                                               {'category': 'Category',
                                                                'name': 'Name',
                                                                'displayname': 'DisplayName',
                                                                'basecost': 'BaseCost',
                                                                'currency': 'BaseCostCurCode',
                                                                'basecostyear': 'BaseCostYear',
                                                                'amortyears': 'AmortYears',
                                                                'ongoing': 'PowerRate',
                                                                'ongoingunits': 'PowerRateUnits'
                                                                },
                                                               bottle.request)
        for t in tList:
            for k in ['BaseCost', 'BaseCostYear', 'PowerRate', 'AmortYears']:
                if t[k] == 0:
                    t[k] = None
            if (t['PowerRateUnits'] and energyTranslationDict[t['Energy']][2]
                    and t['PowerRateUnits'].lower() != energyTranslationDict[t['Energy']][2].lower()):
                raise RuntimeError("Power units for %s are inconsistent: %s vs. %s" %
                                   (t['Name'], t['PowerRateUnits'],
                                    energyTranslationDict[t['Energy']][2]))

        result = {'success': True,
                  "total": 1,    # total pages
                  "page": 1,     # which page is this
                  "records": totRecs,  # total records
                  "rows": [{"name": t['Name'],
                            "category": t['Category'],
                            "displayname": t['DisplayName'],
                            "detail": t['Name'],
                            "basecost": t['BaseCost'],
                            "currency": t['BaseCostCur'],
                            "basecostyear": t['BaseCostYear'],
                            'amortyears': t['AmortYears'],
                            "powerrate": t['PowerRate'],
                            "powerrateunits":t['PowerRateUnits'],
                            "energy":energyTranslationDict[t['Energy']][1]
                            }
                           for t in tList if t['Name'] not in typehelper.hiddenTypesSet]
                  }
        return result
    except Exception, e:
        return {'success': False, 'msg': str(e)}


@bottle.route('/json/get-cost-info-fridge')
def jsonGetCostInfoFridge(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        # m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        result = {'success': True  # currently nothing need be sent
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {"success": False, "msg": str(e)}


@bottle.route('/edit/edit-cost-fridge', method='POST')
def editCostFridge(db, uiSession):
    try:
        # print [(k,v) for k,v in bottle.request.params.items()]
        if bottle.request.params['oper'] == 'edit':
            modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            typeName = _getOrThrowError(bottle.request.params, 'id')
            if typeName in m.types:
                tp = m.types[typeName]
                for opt in ['category', 'displayname', 'ongoingunits', 'ongoingwhat']:
                    if opt in bottle.request.params:
                        raise RuntimeError(_('Editing of {0} is not supported').format(opt))
                if 'basecost' in bottle.request.params:
                    tp.BaseCost = _safeGetReqParam(bottle.request.params, 'basecost', isFloat=True)
                if 'currency' in bottle.request.params:
                    tp.BaseCostCurCode = _safeGetReqParam(bottle.request.params, 'currency')
                if 'basecostyear' in bottle.request.params:
                    tp.BaseCostYear = _safeGetReqParam(bottle.request.params, 'basecostyear',
                                                       isInt=True)
                if 'ongoing' in bottle.request.params:
                    tp.PowerRate = _safeGetReqParam(bottle.request.params, 'ongoing', isFloat=True)
                if 'amortyears' in bottle.request.params:
                    tp.AmortYears = _safeGetReqParam(bottle.request.params, 'amortyears',
                                                     isFloat=True)
                return {'success': True}
            else:
                raise RuntimeError(_('Model {0} does not contain type {1}')
                                   .format(m.name, typeName))
        else:
            raise RuntimeError(_('Unsupported operation {0}')
                               .format(bottle.request.params['oper']))
    except bottle.HTTPResponse:
        raise  # bottle will handle this
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/json/get-cost-info-vaccine')
def jsonGetCostInfoVaccine(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        # m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        result = {'success': True,
                  # I am sure we will want to pass something in here!
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {"success": False, "msg": str(e)}


@bottle.route('/json/manage-vaccine-cost-table')
def jsonManageVaccineCostTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d' % modelId)
        tList = typehelper.getTypeList(db, modelId, 'vaccines', fallback=False)
        tList = [t for t in tList if t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if ('DisplayName' not in rec
                    or rec['DisplayName'] is None or rec['DisplayName'] == ''):
                rec['DisplayName'] = rec['Name']
            if ('Abbreviation' not in rec
                    or rec['Abbreviation'] is None or rec['Abbreviation'] == ''):
                rec['Abbreviation'] = _('Uncategorized')
        nPages, thisPageNum, totRecs, tList = orderAndChopPage(tList,  # @UnusedVariable
                                                               {'category': 'Abbreviation',
                                                                'name': 'Name',
                                                                'displayname': 'DisplayName',
                                                                'basecost': 'Vaccine price/vial',
                                                                'currency': 'Price Units',
                                                                'basecostyear': 'Price Year'
                                                                },
                                                               bottle.request)
        for t in tList:
            for k in ['Vaccine price/vial']:
                if t[k] == 0:
                    t[k] = None

        result = {'success': True,
                  "total": 1,    # total pages
                  "page": 1,     # which page is this
                  "records": totRecs,  # total records
                  "rows": [{"name": t['Name'],
                            "category": t['Abbreviation'],
                            "displayname": t['DisplayName'],
                            "detail": t['Name'],
                            "basecost": t['Vaccine price/vial'],
                            "currency": t['Price Units'],
                            "basecostyear": t['Price Year'],
                            }
                           for t in tList if t['Name'] not in typehelper.hiddenTypesSet]
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/edit/edit-cost-vaccine', method='POST')
def editCostVaccine(db, uiSession):
    try:
        # print [(k,v) for k,v in bottle.request.params.items()]
        if bottle.request.params['oper'] == 'edit':
            modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            typeName = _getOrThrowError(bottle.request.params, 'id')
            if typeName in m.types:
                tp = m.types[typeName]
                assert isinstance(tp, shadow_network.ShdVaccineType), \
                    "Type %s is not a vaccine" % typeName
                for opt in ['category', 'displayname']:
                    if opt in bottle.request.params:
                        raise RuntimeError(_('Editing of {0} is not supported').format(opt))
                if 'basecost' in bottle.request.params:
                    tp.pricePerVial = _safeGetReqParam(bottle.request.params, 'basecost',
                                                       isFloat=True)
                if 'currency' in bottle.request.params:
                    tp.priceUnits = _safeGetReqParam(bottle.request.params, 'currency')
                if 'basecostyear' in bottle.request.params:
                    tp.priceBaseYear = _safeGetReqParam(bottle.request.params, 'basecostyear',
                                                        isInt=True)
                return {'success': True}
            else:
                raise RuntimeError(_('Model {0} does not contain type {1}').format(m.name,
                                                                                   typeName))
        else:
            raise RuntimeError(_('Unsupported operation {0}')
                               .format(bottle.request.params['oper']))
    except bottle.HTTPResponse:
        raise  # bottle will handle this
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/json/get-cost-info-truck')
def jsonGetCostInfoTruck(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        result = {'success': True,
                  # I am sure we will want to pass something in here!
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {"success": False, "msg": str(e)}


@bottle.route('/json/manage-truck-cost-table')
def jsonManageTruckCostTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d' % modelId)
        tList = typehelper.getTypeList(db, modelId, 'trucks', fallback=False)
        tList = [t for t in tList if t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if ('DisplayName' not in rec
                    or rec['DisplayName'] is None or rec['DisplayName'] == ''):
                rec['DisplayName'] = rec['Name']
        nPages, thisPageNum, totRecs, tList = orderAndChopPage(tList,  # @UnusedVariable
                                                               {'name': 'Name',
                                                                'displayname': 'DisplayName',
                                                                'basecost': 'BaseCost',
                                                                'currency': 'BaseCostCur',
                                                                'basecostyear': 'BaseCostYear',
                                                                'fuel': 'Fuel',
                                                                'fuelrate': 'FuelRate',
                                                                'fuelrateunits': 'FuelRateUnits'
                                                                },
                                                               bottle.request)
        for t in tList:
            for k in ['BaseCost']:
                if t[k] == 0:
                    t[k] = None
            if (t['FuelRateUnits'] and fuelTranslationDict[t['Fuel']][2]
                    and t['FuelRateUnits'].lower() != fuelTranslationDict[t['Fuel']][2].lower()):
                raise RuntimeError("Fuel units for %s are inconsistent: %s vs. %s" %
                                   (t['Name'], t['FuelRateUnits'],
                                    fuelTranslationDict[t['Fuel']][2]))

        result = {'success': True,
                  "total": 1,    # total pages
                  "page": 1,     # which page is this
                  "records": totRecs,  # total records
                  "rows": [{"name": t['Name'],
                            "displayname": t['DisplayName'],
                            "detail": t['Name'],
                            "basecost": t['BaseCost'],
                            "currency": t['BaseCostCur'],
                            "basecostyear": t['BaseCostYear'],
                            "fuelrate": t['FuelRate'],
                            "fuelrateunits": t['FuelRateUnits'],
                            "fuel": fuelTranslationDict[t['Fuel']][1],
                            "amortizationkm": t['AmortizationKm']
                            }
                           for t in tList if t['Name'] not in typehelper.hiddenTypesSet]
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/edit/edit-cost-truck', method='POST')
def editCostTruck(db, uiSession):
    try:
        # print [(k,v) for k,v in bottle.request.params.items()]
        if bottle.request.params['oper'] == 'edit':
            modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            typeName = _getOrThrowError(bottle.request.params, 'id')
            if typeName in m.types:
                tp = m.types[typeName]
                assert isinstance(tp, shadow_network.ShdTruckType), \
                    "Type %s is not a truck" % typeName
                for opt in ['name', 'displayname', 'fuel', 'fuelrateunits']:
                    if opt in bottle.request.params:
                        raise RuntimeError(_('Editing of {0} is not supported').format(opt))
                if 'basecost' in bottle.request.params:
                    tp.BaseCost = _safeGetReqParam(bottle.request.params, 'basecost', isFloat=True)
                if 'currency' in bottle.request.params:
                    tp.BaseCostCurCode = _safeGetReqParam(bottle.request.params, 'currency')
                if 'basecostyear' in bottle.request.params:
                    tp.BaseCostYear = _safeGetReqParam(bottle.request.params, 'basecostyear',
                                                       isInt=True)
                if 'amortkm' in bottle.request.params:
                    tp.AmortizationKm = _safeGetReqParam(bottle.request.params, 'amortkm',
                                                         isFloat=True)
                if 'fuelrate' in bottle.request.params:
                    tp.FuelRate = _safeGetReqParam(bottle.request.params, 'fuelrate', isFloat=True)
                return {'success': True}
            else:
                raise RuntimeError(_('Model {0} does not contain type {1}')
                                   .format(m.name, typeName))
        else:
            raise RuntimeError(_('Unsupported operation {0}')
                               .format(bottle.request.params['oper']))
    except bottle.HTTPResponse:
        raise  # bottle will handle this
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/json/get-cost-info-salary')
def jsonGetCostInfoSalary(db, uiSession):
    try:
        # We will surely have real info to pass back soon enough
        modelId = _getOrThrowError(bottle.request.params, 'modelId',
                                   isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        # m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        result = {'success': True,
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {"success": False, "msg": str(e)}


@bottle.route('/json/manage-staff-cost-table')
def jsonManageStaffCostTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',
                                   isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d' %
                                         modelId)
        tList = typehelper.getTypeList(db, modelId, 'staff', fallback=False)
        tList = [t for t in tList
                 if t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if 'DisplayName' not in rec or rec['DisplayName'] is None \
                    or rec['DisplayName'] == '':
                rec['DisplayName'] = rec['Name']
        nPages, thisPageNum, totRecs, tList = (  # @UnusedVariable
            orderAndChopPage(tList,
                             {'name': 'Name',
                              'displayname': 'DisplayName',
                              'basesalary': 'BaseSalary',
                              'currency': 'BaseSalaryCur',
                              'basesalaryyear': 'BaseSalaryYear',
                              'fractionepi': 'FractionEPI'
                              },
                             bottle.request))
        for t in tList:
            for k in ['BaseSalary']:
                if t[k] == 0:
                    t[k] = None

        result = {'success': True,
                  "total": 1,    # total pages
                  "page": 1,     # which page is this
                  "records": totRecs,  # total records
                  "rows": [{"name": t['Name'],
                            "displayname": t['DisplayName'],
                            "detail": t['Name'],
                            "basesalary": t['BaseSalary'],
                            "currency": t['BaseSalaryCur'],
                            "basesalaryyear": t['BaseSalaryYear'],
                            "fractionepi": t['FractionEPI']
                            }
                           for t in tList
                           if t['Name'] not in typehelper.hiddenTypesSet]
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/edit/edit-cost-staff', method='POST')
def editCostStaff(db, uiSession):
    try:
        # print [(k,v) for k,v in bottle.request.params.items()]
        bRQ = bottle.request.params
        if bRQ['oper'] == 'edit':
            modelId = _getOrThrowError(bRQ, 'modelId',
                                       isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            typeName = _getOrThrowError(bRQ, 'id')
            if typeName in m.types:
                tp = m.types[typeName]
                assert isinstance(tp, shadow_network.ShdStaffType), \
                    _("Type %s is not a staff type").format(typeName)
                for opt in ['name', 'displayname']:
                    if opt in bRQ:
                        raise RuntimeError(_('Editing of {0} is not supported').format(opt))
                if 'basesalary' in bRQ:
                    tp.BaseSalary = _safeGetReqParam(bRQ, 'basesalary',
                                                     isFloat=True)
                if 'currency' in bRQ:
                    tp.BaseSalaryCurCode = _safeGetReqParam(bRQ, 'currency')
                if 'basesalaryyear' in bRQ:
                    tp.BaseSalaryYear = _safeGetReqParam(bRQ, 'basesalaryyear',
                                                         isInt=True)
                if 'fractionepi' in bRQ:
                    tp.FractionEPI = _safeGetReqParam(bRQ, 'fractionepi',
                                                      isFloat=True)
                return {'success': True}
            else:
                raise RuntimeError(_('Model {0} does not contain type {1}').
                                   format(m.name, typeName))
        else:
            raise RuntimeError(_('Unsupported operation {0}').
                               format(bRQ['oper']))
    except bottle.HTTPResponse:
        raise  # bottle will handle this
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/json/get-cost-info-perdiem')
def jsonGetCostInfoPerDiem(db, uiSession):
    try:
        # We will surely have real info to pass back soon enough
        modelId = _getOrThrowError(bottle.request.params, 'modelId',
                                   isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        # m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        result = {'success': True,
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {"success": False, "msg": str(e)}


@bottle.route('/json/manage-perdiem-cost-table')
def jsonManagePerDiemCostTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',
                                   isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d' %
                                         modelId)
        tList = typehelper.getTypeList(db, modelId, 'perdiems', fallback=False)
        tList = [t for t in tList
                 if t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if 'DisplayName' not in rec or rec['DisplayName'] is None \
                    or rec['DisplayName'] == '':
                rec['DisplayName'] = rec['Name']
        nPages, thisPageNum, totRecs, tList = (  # @UnusedVariable
            orderAndChopPage(tList,
                             {'name': 'Name',
                              'displayname': 'DisplayName',
                              'baseamount': 'BaseAmount',
                              'currency': 'BaseAmountCur',
                              'baseamountyear': 'BaseAmountYear',
                              'minkmhome': 'MinKmHome',
                              'mustbeovernight': 'MustBeOvernight',
                              'countfirstday': 'CountFirstDay'
                              },
                             bottle.request))

        result = {'success': True,
                  "total": 1,    # total pages
                  "page": 1,     # which page is this
                  "records": totRecs,  # total records
                  "rows": [{"name": t['Name'],
                            "displayname": t['DisplayName'],
                            "detail": t['Name'],
                            "baseamount": t['BaseAmount'],
                            "currency": t['BaseAmountCur'],
                            "baseamountyear": t['BaseAmountYear'],
                            "minkmhome": t['MinKmHome'],
                            'mustbeovernight': t['MustBeOvernight'],
                            'countfirstday': t['CountFirstDay']
                            }
                           for t in tList
                           if t['Name'] not in typehelper.hiddenTypesSet]
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/edit/edit-cost-perdiem', method='POST')
def editCostPerDiem(db, uiSession):
    try:
        # print [(k, v) for k, v in bottle.request.params.items()]
        bRQ = bottle.request.params
        if bRQ['oper'] == 'edit':
            modelId = _getOrThrowError(bRQ, 'modelId', isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            typeName = _getOrThrowError(bRQ, 'id')
            if typeName in m.types:
                tp = m.types[typeName]
                assert isinstance(tp, shadow_network.ShdPerDiemType), \
                    _("Type {0} is not a PerDiem rule").format(typeName)
                for opt in ['name', 'displayname']:
                    if opt in bRQ:
                        raise RuntimeError(_('Editing of {0} is not supported').format(opt))
                if 'baseamount' in bRQ:
                    tp.BaseSalary = _safeGetReqParam(bRQ, 'baseamount', isFloat=True)
                if 'currency' in bRQ:
                    tp.BaseAmountCurCode = _safeGetReqParam(bRQ, 'currency')
                if 'baseamountyear' in bRQ:
                    tp.BaseAmountYear = _safeGetReqParam(bRQ, 'baseamountyear', isInt=True)
                if 'minkmhome' in bRQ:
                    tp.MinKmHome = _safeGetReqParam(bRQ, 'minkmhome', isFloat=True)
                if 'mustbeovernight' in bRQ:
                    v = _safeGetReqParam(bRQ, 'mustbeovernight')
                    tp.MustBeOvernight = (v is not None and isinstance(v, types.StringTypes)
                                          and v.lower() in ['on', 't', 'true'])
                if 'countfirstday' in bRQ:
                    v = _safeGetReqParam(bRQ, 'countfirstday')
                    tp.CountFirstDay = (v is not None and isinstance(v, types.StringTypes)
                                        and v.lower() in ['on', 't', 'true'])
                return {'success': True}
            else:
                raise RuntimeError(_('Model {0} does not contain type {1}').
                                   format(m.name, typeName))
        else:
            raise RuntimeError(_('Unsupported operation {0}').
                               format(bRQ['oper']))
    except bottle.HTTPResponse:
        raise  # bottle will handle this
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/json/manage-route-perdiem-table')
def jsonManageRoutePerDiemTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',
                                   isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d' %
                                         modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        tList = []
        for rt in [r for r in m.routes.values() if r.Type != 'attached']:
            tList.append({'routename': rt.RouteName,
                          'pdtype': rt.PerDiemType,
                          'supplier': rt.supplier().NAME,
                          'level': rt.supplier().CATEGORY})
        nPages, thisPageNum, totRecs, tList = (  # @UnusedVariable
            orderAndChopPage(tList,
                             {'routename': 'routename',
                              'pdtype': 'pdtype',
                              'supplier': 'supplier',
                              'level': 'level'
                              },
                             bottle.request))

        result = {'success': True,
                  "total": 1,    # total pages
                  "page": 1,     # which page is this
                  "records": totRecs,  # total records
                  "rows": [{"routename": t['routename'],
                            "pdtype": t['pdtype'],
                            "supplier": t['supplier'],
                            "level": t['level'],
                            "detail": t['routename']
                            }
                           for t in tList]
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/edit/edit-cost-route-perdiem', method='POST')
def editCostRoutePerDiem(db, uiSession):
    try:
        # print [(k, v) for k, v in bottle.request.params.items()]
        bRQ = bottle.request.params
        if bRQ['oper'] == 'edit':
            modelId = _getOrThrowError(bRQ, 'modelId', isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            pdTypeName = _getOrThrowError(bRQ, 'pdtype')
            routeName = _getOrThrowError(bRQ, 'id')
            assert pdTypeName in m.types, _("This model has no type {0}").format(pdTypeName)
            assert routeName in m.routes, _("This model has no route {0}").format(routeName)
            tp = m.types[pdTypeName]
            assert isinstance(tp, shadow_network.ShdPerDiemType), \
                _("Type {0} is not a PerDiem rule").format(pdTypeName)
            for opt in ['routename', 'level', 'supplier', 'info']:
                if opt in bRQ:
                    raise RuntimeError(_('Editing of {0} is not supported').format(opt))
            rt = m.routes[routeName]
            rt.PerDiemType = pdTypeName
            return {'success': True}
        else:
            raise RuntimeError(_('Unsupported operation {0}').
                               format(bRQ['oper']))
    except bottle.HTTPResponse:
        raise  # bottle will handle this
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/json/get-cost-info-buildings')
def jsonGetCostInfoBuildings(db, uiSession):
    try:
        # We will surely have real info to pass back soon enough
        modelId = _getOrThrowError(bottle.request.params, 'modelId',
                                   isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        # m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        result = {'success': True,
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {"success": False, "msg": str(e)}


@bottle.route('/json/manage-cost-buildings-table')
def jsonManageCostBuildingsTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',
                                   isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d' %
                                         modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        tList = []
        for s in m.stores.values():
            tList.append({'id': s.idcode,
                          'name': s.NAME,
                          'level': s.CATEGORY,
                          'cost': s.SiteCost,
                          'costcur': s.SiteCostCurCode,
                          'costyear': s.SiteCostYear
                          })
        nPages, thisPageNum, totRecs, tList = (  # @UnusedVariable
            orderAndChopPage(tList,
                             {'id': 'id',
                              'name': 'name',
                              'level': 'level',
                              'cost': 'cost',
                              'costcur': 'costcur',
                              'costyear': 'costyear'
                              },
                             bottle.request))

        result = {'success': True,
                  "total": 1,    # total pages
                  "page": 1,     # which page is this
                  "records": totRecs,  # total records
                  "rows": [{"id": t['id'],
                            "name": t['name'],
                            "level": t['level'],
                            "cost": t['cost'],
                            "costcur": t['costcur'],
                            "costyear": t['costyear'],
                            "detail": t['id']
                            }
                           for t in tList]
                  }
        return result
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


@bottle.route('/edit/edit-cost-buildings', method='POST')
def editCostBuildings(db, uiSession):
    try:
        print [(k, v) for k, v in bottle.request.params.items()]
        bRQ = bottle.request.params
        if bRQ['oper'] == 'edit':
            modelId = _getOrThrowError(bRQ, 'modelId', isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            idcode = long(_getOrThrowError(bRQ, 'id'))
            assert idcode in m.stores, _("This model has no store with id code {0}").format(idcode)
            for opt in ['name', 'level', 'detail', 'info']:
                if opt in bRQ:
                    raise RuntimeError(_('Editing of {0} is not supported').format(opt))
            s = m.stores[idcode]
            s.SiteCost = _getOrThrowError(bRQ, 'cost', isFloat=True)
            s.SiteCostCurCode = _getOrThrowError(bRQ, 'costcur')
            s.SiteCostYear = _getOrThrowError(bRQ, 'costyear')
            return {'success': True}
        else:
            raise RuntimeError(_('Unsupported operation {0}').
                               format(bRQ['oper']))
    except bottle.HTTPResponse:
        raise  # bottle will handle this
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}
