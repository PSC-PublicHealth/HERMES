#!/usr/bin/env python

_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types
import bottle
import ipath
import shadow_network_db_api
import shadow_network as s_n
import session_support_wrapper as session_support
from HermesServiceException import HermesServiceException
from gridtools import orderPage, orderAndChopPage
import privs
import htmlgenerator
import typehelper
from costmodel import getCostModelSummary

_gvAvailable = True
try:
    import graph_network_utils
except:
    _gvAvailable = False
import cgi


from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

inlizer=session_support.inlizer
_=session_support.translateString

@bottle.route('/results-top')
def resultsTopPage(db,uiSession):
    #modelId = _safeGetReqParam(bottle.request.path,"modelId");
    modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    print "ModelID 1 {0}".format(modelId) 
    if modelId is None:
        modelId = -1;
    print "FSDFADFAFAEFDSAFAEFADFAFAEFAFSADFASEFAESFASDFAWEFASEF"
    print "ModelID = {0}".format(modelId)
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Results")))
    return bottle.template("results_top.tpl",{"breadcrumbPairs":crumbTrack},modelId=modelId)

@bottle.route('/json/has-results')
def doesModelHaveResult(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId')
        rGps = db.query(s_n.HermesResultsGroup).filter(s_n.HermesResultsGroup.modelId==modelId)
        if rGps is not None:
            return {'success':True,'hasResults':True}
        else:
            return {'success':True,'hasResults':False}
    except Exception as e:
        return {'success':False,'type':'error','msg':str(e)}
    
@bottle.route('/results-fireworks')
def resultsFireworksPage(db, uiSession):
    resultsId = _getOrThrowError(bottle.request.params,'runId',isInt=True)
    hR = db.query(s_n.HermesResults).filter(s_n.HermesResults.resultsId==resultsId).one()
    hRG = hR.resultsGroup
    uiSession.getPrivs().mayReadModelId(db, hRG.modelId)
    m = shadow_network_db_api.ShdNetworkDB(db,hRG.modelId)
    vaccinesInUse = [k for k,v in hR.summaryRecs.items() if isinstance(v, s_n.ShdVaccineSummary)]
    return bottle.template("results_fireworks.tpl",{"breadcrumbPairs":[("top",_("Welcome")),
                                                                  ("results-top",_("Results")),
                                                                  ("results-summary?modelId=%d&resultsId=%d"%(hRG.modelId,resultsId),_("Summary")),
                                                                  ("results-fireworks",_("Fireworks"))],
                                                    "vaccineList":vaccinesInUse,
                                                    "resultsId":resultsId,
                                                    "modelName":m.name,
                                                    "resultsGroupName":hRG.name,
                                                    "runNum":hR.runNumber
                                                    })

@bottle.route('/svg/fireworks')
def resultsSvgFireworks(db, uiSession):
    resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
    hR = db.query(s_n.HermesResults).filter(s_n.HermesResults.resultsId==resultsId).one()
    hRG = hR.resultsGroup
    uiSession.getPrivs().mayReadModelId(db, hRG.modelId)
    net = shadow_network_db_api.ShdNetworkDB(db, hRG.modelId)
    vax = _safeGetReqParam(bottle.request.params, 'vax')
    attrib = {}
    attrib['resultsId'] = resultsId
    if vax:
        attrib['vax'] = vax
        attrib['show'] = 'supplyratio'
    else:
        attrib['show'] = 'fill'
    #attrib['layout'] = gblInputs['layout']
    attrib['removeOrphans'] = False
    #if gblInputs['label'] is not None:
    #   attrib['label'] = gblInputs['label']

    #if gblInputs['root'] is not None:
    #    attrib['root'] = gblInputs['root']

    try:
        ng = graph_network_utils.HermesNetGraph(net, attrib)
    except Exception,e:
            raise RuntimeError(_("GraphView required but not available: ")+str(e))

    return ng.get_gv_render('svg')

@bottle.route('/edit/edit-results.json', method='POST')
@bottle.route('/edit/edit-results.json')
def editResults(db, uiSession):
    if bottle.request.params['oper']=='edit':
        raise bottle.BottleException(_('unsupported operation'))
    elif bottle.request.params['oper']=='add':
        raise bottle.BottleException(_('unsupported operation'))
    elif bottle.request.params['oper']=='del':
        resultsId = _getOrThrowError(bottle.request.params,'id',isInt=True)
        hR = db.query(s_n.HermesResults).filter(s_n.HermesResults.resultsId==resultsId).one()
        hRG = hR.resultsGroup
        uiSession.getPrivs().mayWriteModelId(db, hRG.modelId)
        _logMessage("Deleting resultsId %s"%resultsId)
        db.delete(hR)
        if len(hRG.results) == 0:
            _logMessage("ResultsGroup %s( %d ) is empty; deleting it"%(hRG.name, hRG.resultsGroupId))
            db.delete(hRG)
        return {'success':True}
    else:
        raise bottle.BottleException(_("Bad parameters to {0}").format(bottle.request.path))

def getResultsTreeForModel(mId,db):
    m = shadow_network_db_api.ShdNetworkDB(db,mId)
    resultsJson = {'text':'{0}'.format(m.name),'type':'disabled','id':"m_{0}".format(mId),'children':[]}
    rGPs = db.query(s_n.HermesResultsGroup).filter(s_n.HermesResultsGroup.modelId==mId)
    for rG in rGPs:
        resultsJson['children'].append(getResultsGroupTree(rG,m,db))
    
    return resultsJson
    
def getResultsGroupTree(rG,m,db):
    
    rGDict = {'text':'{0}'.format(rG.name),'state':{'opened':True},
              'id':'rG_{0}_{1}'.format(rG.modelId,rG.resultsGroupId),
              'children':[]}
    ### get the results from this 
    rsltcount=0
    for r in rG.results:
        if r.resultsType != "average":
            rsltcount+=1
    
    for r in rG.results:
        print "Does this have costs? {0}".format(len(r.costSummaryRecs) != 0) 
        if rsltcount == 1:
            if r.resultsType == "average":
                continue
            else:
                pass
        rName = "Run: {0}".format(r.runNumber)
        tText = "Model:{0}, Result:{1}, ".format(m.name,rG.name)
        if r.resultsType == "average":
            rName = "Average Result"
            tText += "Ave"
        else:
            tText += "Run {0}".format(r.runNumber)
        
        #linkName = "<a href={0}results-summary?modelId={1}&resultsId={2}>Open</a>".format("",
        #                                                                                  modelId,
        #                                                                                  r.resultsId)    
        rGDict['children'].append({'text':rName,'tabText':tText,
                                   'id':"r_{0}_{1}".format(rG.modelId,r.resultsId)})
    return rGDict

    
@bottle.route('/json/results-tree-for-all-models')
def resultsTreeForAllModels(db,uiSession):
    ### go from Results Groups, as if there is no results, there is no reason
    try:
        rGrps = db.query(s_n.HermesResultsGroup)
        mIdsParsed = []
        returnJson = []
        for rGp in rGrps:
            if rGp.modelId in mIdsParsed:
                continue
            mIdsParsed.append(rGp.modelId)
            returnJson.append(getResultsTreeForModel(rGp.modelId,db))
    
        return {'success':True,'treeData':returnJson}
    except Exception as e:
        return {'success':False,'type':'error','msg':str(e)}

@bottle.route('/json/results-tree-for-one-model')
def resultsTreeForOneModels(db,uiSession):
    ### go from Results Groups, as if there is no results, there is no reason
    try:
        modelId=_getOrThrowError(bottle.request.params,'modelId',isInt=True)
        
        rGrps = db.query(s_n.HermesResultsGroup).filter(s_n.HermesResultsGroup.modelId==modelId)
        mIdsParsed = []
        returnJson = []
        for rGp in rGrps:
            if rGp.modelId in mIdsParsed:
                continue
            mIdsParsed.append(rGp.modelId)
            returnJson.append(getResultsTreeForModel(rGp.modelId,db))
    
        return {'success':True,'treeData':returnJson}
    except Exception as e:
        return {'success':False,'type':'error','msg':str(e)}

@bottle.route('/json/results-tree-for-model')
def resultsTreeForModel(db,uiSession):
    try:
        modelId=_getOrThrowError(bottle.request.params,'modelId',isInt=True)
#         m = shadow_network_db_api.ShdNetworkDB(db,modelId)
#         ## get Results Group (note s_n is shadow_network)
#         rsltGrps = db.query(s_n.HermesResultsGroup).filter(s_n.HermesResultsGroup.modelId==modelId)
#         resultsJson = []
#         for rG in rsltGrps:
#             resultsJson.append(getResultsGroupTree(rG,m,db))
        
        return {'success':True,'rgnames':getResultsTreeForModel(modelId, db)}
    
    except Exception as e:
        return {'success':False,'type':'error','msg':str(e)}
        
@bottle.route('/json/manage-results-table')
def jsonManageResultsTable(db, uiSession):
    rList = []
    prv = uiSession.getPrivs()
    dbs = db
    for rsltGrp in db.query(s_n.HermesResultsGroup):
        try:
            prv.mayReadModelId(db, rsltGrp.modelId)
            m = shadow_network_db_api.ShdNetworkDB(dbs,rsltGrp.modelId)
            ### Logic to only display average results when there are more than one single run in the resultsgroup
            rsltscount = 0
            for rslt in rsltGrp.results:
                if rslt.resultsType != "average":
                    rsltscount +=1
            for rslt in rsltGrp.results:
                #if rslt.resultsType=='single':
                if rsltscount == 1:
                    if rslt.resultsType == "average":
                        print "average"
                        continue
                    else:
                        pass
                rList.append({'modelId':rsltGrp.modelId, 'modelName':m.name,
                              'runId':rsltGrp.resultsGroupId, 'runName':rsltGrp.name,
                              'resultsId':rslt.resultsId, 'resultsType':rslt.resultsType,
                              'runNumber':rslt.runNumber,
                                  })
        except privs.PrivilegeException:
            pass
    totRecs,rList = orderPage([r for r in rList],
                              {'runname':'runName', 'runid':'runId',
                               'modelname':'modelName', 'modelid':'modelId',
                               'resultsid':'resultsId',
                               'resultstype':'resultsType',
                               'runnum':'runNumber'},
                              bottle.request,
                              defaultSortIndex='runname')
    print "RList = " + str(rList)
    if r['resultsType']=='single': rtLoc = _("Individual")
    else: rtLoc = _("Group Average")
    result = {
              "total":1,    # total pages
              "page":1,     # which page is this
              "records":totRecs,
              'rows':[
                    {
                     "modelname":'Model: ' + r['modelName'],
                     "modelid":r['modelId'],
                     "runname":'Result: ' + r['runName'],
                     "placeholder":" ",
                     "resultsid":r['runId'],
                     "resultstype": _("Individual") if (r['resultsType']=='single') else _("Group Average"),
                     "runid":r['resultsId'],
                     "runnum":r['runNumber']+1, # to make it 1-based rather than 0-based
                     "info":r['resultsId'] #,1,'results'
                     }
                       for r in rList]
              }
    print "-------------------"
    for r in result['rows']: print r
    print '%d rows'%len(result['rows'])
    return result

@bottle.route('/results-summary')
def createResultsSummary(db, uiSession):
    global _gvAvailable
    #modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    resultsId = _safeGetReqParam(bottle.request.params,'resultsId',isInt=True)
    hRG = db.query(s_n.HermesResults).filter(s_n.HermesResults.resultsId==resultsId).one().resultsGroup
    modelId = hRG.modelId
    m = shadow_network_db_api.ShdNetworkDB(db,hRG.modelId)

    if modelId is None:
        raise bottle.BottleException("modelId is missing getting kmlstring")
        return None
    if resultsId is None:
        raise bottle.BottleException("resultsId is missing getting kmlstring")
        return None
	
    return bottle.template("results_summary.tpl",{"breadcrumbPairs":[("top",_("Welcome")),("results-top",_("Results")),("results-summary?modelId=%d&resultsId=%d"%(hRG.modelId,resultsId),_("Summary"))],
                               "pageHelpText":_("This is intended to show page-specific help"),"modelName":m.name,"resultsGroupName":hRG.name},
                               _=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId,
                               gvAvailable=_gvAvailable)

@bottle.route('/json/results-info')
def jsonResultsInfo(db, uiSession):
    try:
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        htmlStr, titleStr = htmlgenerator.getResultsInfoHTML(db,uiSession,resultsId)
        result = {'success':True, "htmlstring":htmlStr, "title":titleStr}
        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/get-results-name')
def jsonGetResultsName(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)

        result = {'name':r.name,
                  'success':True}
        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/results-summary')
def jsonResultsSummary(db, uiSession):
    validResultTypes = ["vaccines",'trucks','fridges']
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        resultType = _getOrThrowError(bottle.request.params,'resultType',isInt=False)
        if resultType not in validResultTypes:
            raise Exception("resultType is not valid")
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)

        typeSummaries = r.summaryRecs

        results = {'total':1,
                   'page':"1",
                   'rows':[]}

        if resultType == "vaccines":
            for v,dataStruct in typeSummaries.items():
                if dataStruct.summaryType == "vaccines":
                    attrRec = {}
                    s_n._copyAttrsToRec(attrRec,dataStruct)
                    attrRec['vaccid'] = v
                    if attrRec['Applied'] > 0.0:
                        results['rows'].append(attrRec)

        elif resultType == "trucks":
            for v,dataStruct in typeSummaries.items():
                if dataStruct.summaryType == "trucks":
                    attrRec = {}
                    s_n._copyAttrsToRec(attrRec,dataStruct)
                    attrRec['truckid'] = v
                    results['rows'].append(attrRec)

        elif resultType == "fridges":
            for v,dataStruct in typeSummaries.items():
                if dataStruct.summaryType == "fridges":
                    attrRec = {}
                    s_n._copyAttrsToRec(attrRec,dataStruct)
                    attrRec['fridgeid'] = v
                    results['rows'].append(attrRec)

        results['success'] = True
        return results

    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

def _checkSameAndDel(rec,key,val):
    if val is None:
        val = rec[key]
        del rec[key]
        return val
    else:
        assert rec[key] == val, _("Cost report {0} values do not match").format(key)
        del rec[key]
        return val

@bottle.route('/json/costs-summary')
def jsonCostsSummary(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)


        results = {'total':1,
                   'page':"1",
                   'rows':[]}

        workingRecs = []
        for cSR in r.costSummaryRecs:
            rec = cSR.createRecord()
            if rec['ReportingLevel'] in ['-top-', 'all']:
                workingRecs.append(rec)
        baseYear = baseCur = intervalDays = daysPerYear = recType = None
        for rec in workingRecs:
            baseYear = _checkSameAndDel(rec, 'BaseYear', baseYear)
            baseCur = _checkSameAndDel(rec, 'Currency', baseCur)
            intervalDays = _checkSameAndDel(rec, 'ReportingIntervalDays', intervalDays)
            daysPerYear = _checkSameAndDel(rec, 'DaysPerYear', daysPerYear)
            recType = _checkSameAndDel(rec, 'Type', recType)
            for entry in ['ReportingLevel']:
                del rec[entry]

        if recType == 'micro1':
            # Clip the tags off the cost entries
            newRecs = []
            for rec in workingRecs:
                nRec = {}
                for k, v in rec.items():
                    if k.startswith('m1C_'):
                        k = k[4:]
                    if v != 0.0:
                        nRec[k] = v
                newRecs.append(nRec)
            workingRecs = newRecs

        results['BaseYear'] = baseYear
        results['Type'] = recType
        results['Currency'] = baseCur
        results['ReportingIntervalDays'] = intervalDays
        results['DaysPerYear'] = daysPerYear
        results['rows'] = workingRecs

        results['success'] = True
        return results

    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/results-vaccine-by-place-hist')
def jsonResultSummaryVaccineByPlace(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']
        histogramData = [0,0,0,0,0,0,0,0,0,0,0]
        for storeRptId,storeRpt in r.storesRpts.items():
            patients = 0
            treated = 0
            for v,n in storeRpt.vax.items():
                patients += n.patients
                treated  += n.treated
            if patients == 0:
                continue
            avail = (float(treated) / float(patients))*100.0
            index = int(math.floor(avail/10.0))
            #_logMessage("Avail = " + str(avail) + " index = " + str(index))
            histogramData[index] += 1

        result = {'success':True,
                  'categories':categories,
                  'data':histogramData}
        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/results-vaccine-by-place-by-size-hist')
def jsonResultSummaryVaccineByPlaceBySize(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']
        sizeBorders = [100,300,1000]
        histogramDataString = r.getVAHistString()
        histDataSplit = histogramDataString.split(":")
        #print "Lenght = " + str(len(histDataSplit))
        print "String = " + str(histogramDataString)
        histogramData = []
        for i in range(0,4):
            histogramData.append([])
            for j in range(0,11):
                #print str(11*i+j)
                histogramData[i].append(int(histDataSplit[11*i+j]))
        histogramJSON = [{'name':'<100','data':histogramData[0]},
                         {'name':'100-299','data':histogramData[1]},
                         {'name':'300-999','data':histogramData[2]},
                         {'name':'>1000','data':histogramData[3]}]
        result = {'success':True,
                  'categories':categories,
                  'datas':histogramJSON}
        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/result-storage-utilization-by-place-hist')
def jsonResultsSummaryStorageUtiliztionByPlace(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']
        histogramData = [0,0,0,0,0,0,0,0,0,0,0]
        for storeRptId,storeRpt in r.storesRpts.items():
            if storeRpt.storage['cooler'].vol > 0.0:
                util = float(storeRpt.storage['cooler'].fillRatio)*100.0
                index = int(math.floor(util/10.0))
                histogramData[index] += 1

        result = {'success':True,
                  'categories':categories,
                  'data':histogramData}

        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/result-storage-utilization-by-place-by-levelhist')
def jsonResultsSummaryStorageUtiliztionByPlaceByLevel(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']
        histogramDataDict = r.getStoreCapHistDict()
        histogramJSON = []
        
        levels = m.getLevelList()
        
        for level in levels:
            if level in histogramDataDict.keys():
                histData = histogramDataDict[level]
        #for histKey,histData in histogramDataDict.items():
                histogramJSON.append({'name':level,'data':histData})

        result = {'success':True,
                  'categories':categories,
                  'datas':histogramJSON}

        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/result-transport-utilization-by-route-hist')
def jsonResultsSummaryTransportUtiliztionByRoute(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']
        histogramData = [0,0,0,0,0,0,0,0,0,0,0]
        for routeId,route in m.routes.items():
            if route.Type != "attached":
                if route.reports.has_key(resultsId):
                    routeReport = route.reports[resultsId]
                    util = float(routeReport.RouteFill)*100.0
                    if util > 100.0:
                        util = 100.0
                    index = int(math.floor(util/10.0))
                    histogramData[index] += 1

        result = {'success':True,
                  'categories':categories,
                  'data':histogramData}

        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/result-transport-utilization-by-route-by-level-hist')
def jsonResultsSummaryTransportUtiliztionByRouteByLevel(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']

        histogramDataDict = r.getTransCapHistDict()
        levels = m.getLevelList()
        
        histogramJSON = []
        for level in levels:
            if level in histogramDataDict.keys():
                histData = histogramDataDict[level]
#        for histKey,histData in histogramDataDict.items():
                histogramJSON.append({'name':level,'data':histData})

        result = {'success':True,
                  'categories':categories,
                  'datas':histogramJSON}

        return result
    except Exception,e:
        print str(e)
        result = {'success':False, 'msg':str(e)}
        return result

def _convert_key(_item, _from, _to):
    """ recurse through supplied dict converting all _from keys to _to keys

    This is necessary becuse d3.treemap expects "value" while
    d3.hierarchical-barchart expects "
    """
    if _to == 'size':
        return _item
    if isinstance(_item, dict):
        return {_to if k==_from else k: _convert_key(v, _from, _to) \
                for k,v in _item.items()}
    elif isinstance(_item, list):
        return [_convert_key(v, _from, _to) for v in _item]
    else:
        return _item

@bottle.route('/json/results-cost-hierarchical-mixed')
def jsonResultSummaryCostHierarchicalMixed(db, uiSession, value_format='size'):
    try:
        modelId = _getOrThrowError(bottle.request.params,
                'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,
                'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)

        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)

        base = m.getParameterValue('currencybase')
        year = m.getParameterValue('currencybaseyear')
        _from = 'size'
        if value_format == 'value':
            _to = 'value'
        else:
            _to = 'size'

        try:
            cost_summary = getCostModelSummary(m, r)
            result = {
                    'success': True,
                    'data': {
                      'cost_summary': _convert_key(cost_summary.dict(fmt='mixed'), _from, _to),
                      'currency_base': base,
                      'currency_year': year
                    }
                }
        except:
            _logStacktrace()
            result = {'success': False,
                      'data': '{}'}

        return result

    except Exception, e:
        _logStacktrace()
        result = {'success': False, 'msg': str(e)}
        return result


@bottle.route('/json/results-cost-hierarchical-mixed-value')
def jsonResultSummaryCostHierarchicalMixedValue(db, uiSession):
    return jsonResultSummaryCostHierarchicalMixed(db, uiSession, value_format='value')


@bottle.route('/json/results-cost-hierarchical')
def jsonResultSummaryCostHierarchical(db, uiSession, value_format='size', fmt=None):
    try:
        modelId = _getOrThrowError(bottle.request.params,
                                   'modelId', isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,
                                     'resultsId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)

        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        r = m.getResultById(resultsId)

        base = m.getParameterValue('currencybase')
        year = m.getParameterValue('currencybaseyear')
        _from = 'size'
        if value_format == 'value':
            _to = 'value'
        else:
            _to = 'size'

        try:
            cost_summary = getCostModelSummary(m, r)
            result = {'success': True,
                      'data': {'cost_summary': _convert_key(cost_summary.dict(fmt=fmt),
                                                            _from, _to),
                               'currency_base': base,
                               'currency_year': year
                               }
                      }
        except Exception, e:
            _logStacktrace()
            result = {'success': False,
                      'data': '{}',
                      'msg': str(e)}

        return result

    except Exception, e:
        _logStacktrace()
        result = {'success': False, 'msg': str(e)}
        return result


@bottle.route('/json/results-cost-hierarchical-value')
def jsonResultSummaryCostHierarchicalValue(db, uiSession):
    return jsonResultSummaryCostHierarchical(db, uiSession, value_format='value',
                                             fmt='cllc')
