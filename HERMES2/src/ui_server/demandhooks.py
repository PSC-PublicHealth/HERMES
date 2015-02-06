#!/usr/bin/env python

_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types,re
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

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults
from ui_utils import _safeGetReqParam

inlizer=session_support.inlizer
_=session_support.translateString

@bottle.route('/demand-top')
def demandTopPage(uiSession):
    modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Demand For Vaccines")))
    if modelId:
        return bottle.template("demand_top.tpl",{'breadcrumbPairs':crumbTrack},modelId=modelId,pagehelptag="setdemand")
    else:
        return bottle.template("demand_top.tpl",{"breadcrumbPairs":crumbTrack},pagehelptag="setdemand")

def _interpretDemandModelStructure(model):

    m = model
    summary = {}
    
    if 'dayspermonth' in m.parms:
        if m.parms['dayspermonth'].getValue() == 28:
            if 'twentyeightdaymonths' in m.parms:
                if m.parms['twentyeightdaymonths'].getValue():
                    summary['twentyeightDayMonths'] = True;
                else:
                    raise bottle.BottleException(_('model parameter conflict between dayspermonth and twentyeightdaymonths'))
            else:
                summary['twentyeightDayMonths'] = True;
        else:
            if 'twentyeightdaymonths' in m.parms:
                if not m.parms['twentyeightdaymonths'].getValue():
                    summary['twentyeightDayMonths'] = False;
                else:
                    raise bottle.BottleException(_('model parameter conflict between dayspermonth and twentyeightdaymonths'))
            else:
                summary['twentyeightDayMonths'] = False
    elif 'twentyeightdaymonths' in m.parms:
        summary['twentyeightDayMonths'] = m.parms['twentyeightdaymonths'].getValue();
    else:
        summary['twentyeightDayMonths'] = (m.getParameterValue('dayspermonth') == 28)

    summary['allDemandsUnified'] = bool( not (m.consumptionDemands or m.shippingDemands) )
    
    summary['hasPatternCalendar'] = bool(m.getParameterValue('demanddayspattern')
                                     or m.getParameterValue('demanddaysbytypepattern'))
    
    summary['hasCalendar'] = bool(m.unifiedCalendar or m.shippingCalendar or m.consumptionCalendar) \
                                  or summary['hasPatternCalendar']
    
    summary['allCalendarsUnified'] = ( not (m.shippingCalendar or m.consumptionCalendar) )
    
    if summary['hasCalendar']:
        summary['oneYearCalendarCycle'] = (m.getParameterValue('calendarcycle') == (7*4*12)) or summary['hasPatternCalendar']

    summary['supported'] = summary['allDemandsUnified'] 
                
    summary['calSupported'] = (summary['twentyeightDayMonths']
                               and ((not summary['hasCalendar']) or summary['hasPatternCalendar']))
    
    summary['hasScalarScale'] = ((m.getParameterValue('scaledemandactual') is not None)
                                 or (m.getParameterValue('scaledemandexpected') is not None))
    summary['hasVectorScale'] = ((m.getParameterValue('scaledemandbytypeactual') is not None)
                                 or (m.getParameterValue('scaledemandbytypeexpected') is not None))
    
    summary['hasScalarCal'] = (m.getParameterValue('demanddayspattern') is not None)
    summary['hasVectorCal'] = (m.getParameterValue('demanddaysbytypepattern') is not None)

    return summary

def _scaleVecDictToParms(model,scaleDict):
    """
    This actually builds and saves the appropriate scale parameters to the model.
    """

    # We're doing a vector representation, so discard any scalar info
    for k in ['scaledemandactual','scaledemandexpected']:
        if k in model.parms: del model.parms[k]
        
    actualStr = ','.join(["'%s:%s'"%(k,a) for k,(a,b) in scaleDict.items()])
    expectedStr = ','.join(["'%s:%s'"%(k,b) for k,(a,b) in scaleDict.items()])
    model.addParm(shadow_network.ShdParameter('scaledemandbytypeactual', actualStr))
    model.addParm(shadow_network.ShdParameter('scaledemandbytypeexpected', expectedStr))

def _scaleVecDictFromParms(model):
    """
    This returns a dict with entries vaccineTypeName:(scaleActual,scaleExpected)
    """
    m = model
    actualVal = m.getParameterValue('scaledemandactual')
    expectedVal = m.getParameterValue('scaledemandexpected')

    scaleDict = {dmnd.vaccineStr:(actualVal,expectedVal) for dmnd in m.unifiedDemands}
    sDBTA = m.getParameterValue('scaledemandbytypeactual')
    if sDBTA is not None:
        for word in [ _smartStrip(w) for w in sDBTA]:
            tname,val = word.split(':')
            if tname in scaleDict:
                a,b = scaleDict[tname]
                scaleDict[tname] = float(val)*a,b
            else:
                scaleDict[tname] = float(val)*actualVal,expectedVal
    sDBTE = m.getParameterValue('scaledemandbytypeexpected')
    if sDBTE is not None:
        for word in [ _smartStrip(w) for w in sDBTE]:
            tname,val = word.split(':')
            if tname in scaleDict:
                a,b = scaleDict[tname]
                scaleDict[tname] = a,float(val)*b
            else:
                scaleDict[tname] = actualVal,float(val)*expectedVal
    return scaleDict

def _calVecDictToParms(model,calDict):
    """
    This actually builds and saves the appropriate calendar string to the model.
    """

    # We're doing a vector representation, so discard any scalar info
    if 'demanddayspattern' in model.parms: del model.parms['demanddayspattern']
        
    calStr = ','.join(["'%s:%s'"%(k,v) for k,v in calDict.items()])
    model.addParm(shadow_network.ShdParameter('demanddaysbytypepattern', calStr))

def _calVecDictFromParms(model):
    """
    This returns a dict with entries peopleTypeName:calendarString
    """
    m = model
    if 'demanddaysbytypepattern' in m.parms:
        vacCalStr = m.parms['demanddaysbytypepattern'].getValue()
        words = vacCalStr.split(',')
        words = [_smartStrip(w) for w in words]
        calDict = {a:b for a,b in [w.split(':',1) for w in words]}
        pTypes = [dmnd.peopleStr for dmnd in m.unifiedDemands]
        for pt in pTypes:
            if pt not in calDict: calDict[pt] = '1111111:1111:111111111111'
            
    elif 'demanddayspattern' in m.parms:
        calStr = m.parms['demanddayspattern'].getValue()
        calStr = _smartStrip(calStr)
        calDict = {dmnd.peopleStr:calStr for dmnd in m.unifiedDemands}
    else:
        calDict = {dmnd.peopleStr:'1111111:1111:111111111111' for dmnd in m.unifiedDemands}
        
    return calDict

@bottle.route('/json/manage-demand-vac-table')
def jsonManageDemandVacTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        showWhich = _safeGetReqParam(bottle.request.params,'show')
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        entries = {}
        if showWhich == 'vaccines':
            for vStr in m.vaccines.keys(): entries[vStr] = False
            for dmnd in m.unifiedDemands: entries[dmnd.vaccineStr] = True
        elif showWhich == 'people':
            for pStr in m.people.keys(): entries[pStr] = False
            for dmnd in m.unifiedDemands: entries[dmnd.peopleStr] = True
        else:
            raise bottle.BottleException('Missing or invalid "show" value')
        print "--------------------------------------------------------------"
        
        if showWhich == 'vaccines':
            tList = [{'name':nm, 'usedin':val, 'dname':m.vaccines[nm].DisplayName} for nm,val in entries.items()]
        elif showWhich == 'people':
             tList = [{'name':nm, 'usedin':val, 'dname':m.people[nm].DisplayName} for nm,val in entries.items()]
            
        print tList
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                            {'name':'name', 'usedin':'usedin'},
                                                            bottle.request)
        return {'success':True,
                "total":nPages,    # total pages
                "page":thisPageNum,     # which page is this
                "records":totRecs,  # total records
                "rows": [ {"name":t['name'], 
                           "cell":[t['usedin'], t['name'], t['dname']]}
                         for t in tList ]
                }
    except Exception,e:
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/manage-empty-demand')
def jsonManageEmptyDemand(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
        name = _getOrThrowError(bottle.request.params,'name')
        add = _getOrThrowError(bottle.request.params,'add',isBool=True)
        show = _getOrThrowError(bottle.request.params,'show')
        try:
            uiSession.getPrivs().mayModifyModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException(_('User may not modify model {0}').format(modelId))
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        if show=='vaccines':
            if add:
                if len(m.unifiedDemands)>0:
                    peopleStr = m.unifiedDemands[0].peopleStr
                elif m.people:
                    peopleStr = m.people.keys()[0]
                else:
                    raise bottle.BottleException(_("You must first add a population type to this model"))
                m.unifiedDemands.append(shadow_network.ShdDemand(modelId=modelId,
                                                                 demandType=shadow_network.DemandEnums.TYPE_UNIFIED,
                                                                 vaccineStr=name,
                                                                 peopleStr=peopleStr,
                                                                 count=0))
            else:
                killList = []
                for dmnd in m.unifiedDemands:
                    if dmnd.vaccineStr == name:
                        if dmnd.count==0: killList.append(dmnd)
                        else:
                            raise bottle.BottleException(_('Change the demand for this vaccine to zero first.'))
                for dmnd in killList: m.unifiedDemands.remove(dmnd)
                    
            
        elif show=='people':
            if add:
                if len(m.unifiedDemands)>0:
                    vaccineStr = m.unifiedDemands[0].vaccineStr
                elif m.vaccines:
                    vaccineStr = m.vaccines.keys()[0]
                else:
                    raise bottle.BottleException(_("You must first add a vaccine type to this model"))
                m.unifiedDemands.append(shadow_network.ShdDemand(modelId=modelId,
                                                                 demandType=shadow_network.DemandEnums.TYPE_UNIFIED,
                                                                 vaccineStr=vaccineStr,
                                                                 peopleStr=name,
                                                                 count=0))
            else:
                killList = []
                for dmnd in m.unifiedDemands:
                    if dmnd.peopleStr == name:
                        if dmnd.count==0: killList.append(dmnd)
                        else:
                            raise bottle.BottleException(_('Change the demand for this population type to zero first.'))
                for dmnd in killList: m.unifiedDemands.remove(dmnd)

        else:
            raise bottle.BottleException(_("Invalid value for parameter 'show'"))
        return {"success":True}
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}
    

@bottle.route('/json/get-demand-table')
def jsonGetDemandTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        summary = _interpretDemandModelStructure(m)
        
        initialScale = 1.0
        initialRelScale = 1.0
        if summary['hasVectorScale']:
            scaleVecDict = _scaleVecDictFromParms(m)
            aa = None
            bb = None
            allMatch = False
            for a,b in scaleVecDict.values():
                if aa is None: aa = a
                elif aa!=a: break
                if bb is None: bb = b
                elif bb!=b: break
            else:
                allMatch = True
            if aa is not None and bb is not None:
                initialScale = aa
                initialRelScale = bb/aa
        elif summary['hasScalarScale']:
            if 'scaledemandactual' in m.parms: a = float(m.parms['scaledemandactual'].getValue())
            else: a = 1.0
            if 'scaledemandexpected' in m.parms: b = float(m.parms['scaledemandexpected'].getValue())
            else: b = 1.0
            initialScale = a
            initialRelScale = b/a
            
        initialCal = '1111111:1111:111111111111'
        if summary['hasVectorCal']:
            calVecDict = _calVecDictFromParms(m)
            allCalMatch = False
            ss = None
            for s in calVecDict.values():
                if ss is None: ss = s
                elif ss!=s: break
            else:
                allCalMatch = True
            if ss is not None: initialCal = ss
        elif summary['hasScalarCal']:
            if 'demanddayspattern' in m.parms:
                initialCal = _smartStrip(m.parms['demanddayspattern'].getValue())
                
        pSet = set()
        for dmnd in m.unifiedDemands:
            pSet.add(dmnd.peopleStr)
        pList = list(pSet)
        result = {
                  "success":True,
                  "supported":summary['supported'],

                  "hasScalarScale":summary['hasScalarScale'],
                  "hasVectorScale":summary['hasVectorScale'],
                  "requireVectorScale":( summary['hasVectorScale'] and not allMatch ),
                  "scalarScaleSetting":initialScale,
                  "scalarRelScaleSetting":initialRelScale,
                  
                  "calSupported":summary['calSupported'],
                  "hasScalarCal":summary['hasScalarCal'],
                  "hasVectorCal":summary['hasVectorCal'],
                  "requireVectorCal":( summary['hasVectorCal'] and not allCalMatch ),
                  "scalarCalSetting":initialCal,

                  "colNames":["",_('Vaccine')] + [pStr for pStr in pList],
                  "colModel":[{'name':'vaccine', 'index':'vaccine', 'hidden':True, 'sorttype':'text','editable':False, 'key':True},
                              {'name':'dvaccine','index':'dname','sorttype':'text','editable':False}] \
                            + [{'name':pStr,'index':pStr, 'sorttype':'text',
                                'editable':True, 'edittype':'text', 'editrules':{'integer':True}} 
                               for pStr in pList],
                  "sortname":"vaccine"
                  }
        return result
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}
 
@bottle.route('/json/manage-demand-table')
def jsonManageDemandTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        pSet = set()
        vSet = set()
        counts = {}
        for dmnd in m.unifiedDemands:
            pSet.add(dmnd.peopleStr)
            vSet.add(dmnd.vaccineStr)
            counts[(dmnd.peopleStr,dmnd.vaccineStr)] = dmnd.count
        pList = list(pSet)
        vList = list(vSet)
        tList = []
        for vStr in vList:
            d = {'vaccine':vStr,'dname':m.vaccines[vStr].DisplayName}
            for pStr in pList:
                if (pStr,vStr) in counts: d[pStr] = counts[(pStr,vStr)]
                else: d[pStr] = 0
            tList.append(d)
        transDict = {p:p for p in pList}
        transDict['vaccine']='vaccine'
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList, transDict, bottle.request)
        return {'success':True,
                "total":nPages,    # total pages
                "page":thisPageNum,     # which page is this
                "records":totRecs,  # total records
                "rows": [ {"vaccine":t['vaccine'], 
                           "cell":[t['vaccine'],t['dname']]+[t[p] for p in pList]}
                         for t in tList ]
                }
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}
        
@bottle.route('/edit/edit-demand',method='POST')
def editEditDemand(db, uiSession):
    try:
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in bottle.request.params.items()]
        _logMessage("editEditDemand: paramList is %s"%paramList)
        if bottle.request.params['oper']=='edit':
            modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
            vaccineStr = _getOrThrowError(bottle.request.params,'vaccine')
            vacDemands = { d.peopleStr:d for d in m.unifiedDemands if d.vaccineStr==vaccineStr}
            for k,v in bottle.request.params.items():
                if k in m.people:
                    v = int(v)
                    if k in vacDemands:
                        if vacDemands[k].count != v: vacDemands[k].count = v
                    else:
                        if v!=0:
                            m.unifiedDemands.append(shadow_network.ShdDemand(modelId=modelId,
                                                                             demandType=shadow_network.DemandEnums.TYPE_UNIFIED,
                                                                             vaccineStr=vaccineStr,
                                                                             peopleStr=k,
                                                                             count=v))
        elif bottle.request.params['oper']=='add':
            raise bottle.BottleException(_('unsupported operation'))
        elif bottle.request.params['oper']=='del':
            raise bottle.BottleException(_('unsupported operation'))
        return {'success':True}
    except Exception,e:
        _logStacktrace()
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/manage-demand-scale-table')
def jsonManageDemandScaleTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        scaleDict = _scaleVecDictFromParms(m)
        tList = []
        for k,tpl in scaleDict.items():
            print "k = " +str(k)
            a,b = tpl
            if a==0.0: raise bottle.BottleException(_('actual demand scaled to zero?'))
            else:
                dName = 'All'
                if k in m.vaccines.keys():
                    dName = m.vaccines[k].DisplayName
                tList.append({'vaccine':k, 'dname':dName, 'scale':a, 'relscale':b/a})
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                            {'vaccine':'vaccine','dname':'dname','scale':'scale', 
                                                             'relscale':'relscale'},
                                                            bottle.request)
        return {'success':True,
                "total":nPages,    # total pages
                "page":thisPageNum,     # which page is this
                "records":totRecs,  # total records
                "rows": [ {"vaccine":t['vaccine'], 
                           "cell":[t['vaccine'], t['dname'], t['scale'], t['relscale']]}
                         for t in tList ]
                }
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}
        
@bottle.route('/json/set-demand-scalar-scale')
def jsonSetDemandScalarScale(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayModifyModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not modify model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        val = _getOrThrowError(bottle.request.params,'value',isFloat=True)
        summary = _interpretDemandModelStructure(m)
        if summary['hasVectorScale']:
            scaleDict = _scaleVecDictFromParms(m)
            for k,(a,b) in scaleDict.items(): 
                scaleDict[k] = (val,val*b/a)
            _scaleVecDictToParms(m, scaleDict)
        else:
            if 'scaledemandactual' in m.parms: aVal = float(m.parms['scaledemandactual'].getValue())
            else: aVal = 1.0
            if 'scaledemandexpected' in m.parms: eVal = float(m.parms['scaledemandexpected'].getValue())
            else: eVal = 1.0
            newAVal = val
            newEVal = (eVal/aVal)*val
            m.addParm(shadow_network.ShdParameter('scaledemandactual', str(newAVal)))
            m.addParm(shadow_network.ShdParameter('scaledemandexpected', str(newEVal)))
        return {'success':True}
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}
        
@bottle.route('/json/set-demand-scalar-relscale')
def jsonSetDemandScalarRelScale(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayModifyModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not modify model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        val = _getOrThrowError(bottle.request.params,'value',isFloat=True)
        summary = _interpretDemandModelStructure(m)
        if summary['hasVectorScale']:
            scaleDict = _scaleVecDictFromParms(m)
            for k,(a,b) in scaleDict.items(): 
                scaleDict[k] = (a,val*a)
            _scaleVecDictToParms(m, scaleDict)
        else:
            if 'scaledemandactual' in m.parms: aVal = float(m.parms['scaledemandactual'].getValue())
            else: aVal = 1.0
            if 'scaledemandexpected' in m.parms: eVal = float(m.parms['scaledemandexpected'].getValue())
            else: eVal = 1.0
            newAVal = aVal
            newEVal = val*aVal
            m.addParm(shadow_network.ShdParameter('scaledemandactual', str(newAVal)))
            m.addParm(shadow_network.ShdParameter('scaledemandexpected', str(newEVal)))
        return {'success':True}
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}
        
    
@bottle.route('/edit/edit-demand-scale',method='POST')
def editEditDemandScale(db, uiSession):
    try:
        if bottle.request.params['oper']=='edit':
            modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
            uiSession.getPrivs().mayModifyModelId(db, modelId)
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
            vaccineStr = _getOrThrowError(bottle.request.params,'vaccine')
            scale = _getOrThrowError(bottle.request.params,'scale',isFloat=True)
            relScale = _getOrThrowError(bottle.request.params,'relscale',isFloat=True)
            scaleDict = _scaleVecDictFromParms(m)
            scaleDict[vaccineStr] = (scale, relScale*scale)
            _scaleVecDictToParms(m, scaleDict)
            aa = None
            bb = None
            allMatch = False
            for a,b in scaleDict.values():
                if aa is None: aa = a
                elif aa!=a: break
                if bb is None: bb = b
                elif bb!=b: break
            else:
                allMatch = True
            if aa is None: 
                scaleVal = relScaleVal = 1.0
            else: 
                scaleVal = aa
                relScaleVal = bb/aa
            return {'success':True,
                    'requireVectorScale':(not allMatch),
                    'scaleVal':scaleVal,
                    'relScaleVal':relScaleVal 
                    }
        elif bottle.request.params['oper']=='add':
            raise bottle.BottleException(_('unsupported operation'))
        elif bottle.request.params['oper']=='del':
            raise bottle.BottleException(_('unsupported operation'))
    except Exception,e:
        _logStacktrace()
        return {'success':False, 'msg':str(e)}
    
@bottle.route('/json/manage-demand-calendar-table')
def jsonManageDemandCalendarTable(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        calendarStringDict = _calVecDictFromParms(m)
        tList = [{'people':k, 'calpattern':v} for k,v in calendarStringDict.items()]
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                            {'people':'people', 'calpattern':'calpattern'},
                                                            bottle.request)
        return {'success':True,
                "total":nPages,    # total pages
                "page":thisPageNum,     # which page is this
                "records":totRecs,  # total records
                "rows": [ {"name":t['people'], 
                           "cell":[t['people'], t['calpattern']]}
                         for t in tList ]
                }
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}
        
@bottle.route('/json/set-demand-scalar-cal')
def jsonSetDemandScalarCal(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        try:
            uiSession.getPrivs().mayModifyModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not modify model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        cal = _getOrThrowError(bottle.request.params,'calendar')
        summary = _interpretDemandModelStructure(m)
        if summary['hasVectorCal']:
            calDict = _calVecDictFromParms(m)
            calDict = { k:cal for k in calDict.keys() }
            _calVecDictToParms(m, calDict)
        else:
            m.addParm(shadow_network.ShdParameter('demanddayspattern', "'%s'"%cal))
        return {'success':True}
    except Exception,e:
        _logStacktrace()
        return {"success":False, "msg":str(e)}
    
@bottle.route('/edit/edit-demand-calendar')
def editEditDemandCalendar(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        peopleStr = _getOrThrowError(bottle.request.params,'people')
        calStr = _getOrThrowError(bottle.request.params,'calendar')

        calDict = _calVecDictFromParms(m)
        calDict[peopleStr] = calStr
        _calVecDictToParms(m, calDict)
        ss = None
        allMatch = False
        #print calDict
        for s in calDict.values():
            if ss is None: ss = s
            elif ss!=s: break
        else:
            allMatch = True
        if ss is None:
            calVal = '1111111:1111:111111111111'
        else: 
            calVal = ss
        result = {'success':True,
                  'requireVectorCal':(not allMatch),
                  'calVal':calVal
                  }
        #print result
        return result
    except Exception,e:
        _logStacktrace()
        return {'success':False, 'msg':str(e)}
    

