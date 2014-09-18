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
def resultsTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Results")))
    return bottle.template("results_top.tpl",{"breadcrumbPairs":crumbTrack})


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
                                                                  ("results-edit",_("Edit")),
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
    modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    resultsId = _safeGetReqParam(bottle.request.params,'resultsId',isInt=True)

    if modelId is None:
        raise bottle.BottleException("modelId is missing getting kmlstring")
        return None
    if resultsId is None:
        raise bottle.BottleException("resultsId is missing getting kmlstring")
        return None

    return bottle.template("results_summary.tpl",{"breadcrumbPairs":[("top",_("Welcome"))],
                               "pageHelpText":_("This is intended to show page-specific help")},
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

@bottle.route('/json/results-cost-hierarchical')
def jsonResultSummaryCostHierarchical(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,
                'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,
                'resultsId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)

        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)

        #import ipdb
        #ipdb.set_trace()

        try:
            cost_summary = getCostModelSummary(m, r)
            result = {'success': True,
                  'data': cost_summary.dict()}
                  #'data': json.loads(CostHierarchyTestJSON)}
        except:
            result = {'success': False,
                  'data': '{}'}

        print result

        return result

    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        return result










###############################################################################

CostHierarchyTestJSON = '''
{
 "name": "flare",
 "children": [
  {
   "name": "analytics",
   "children": [
    {
     "name": "cluster",
     "children": [
      {"name": "AgglomerativeCluster", "size": 3938},
      {"name": "CommunityStructure", "size": 3812},
      {"name": "HierarchicalCluster", "size": 6714},
      {"name": "MergeEdge", "size": 743}
     ]
    },
    {
     "name": "graph",
     "children": [
      {"name": "BetweennessCentrality", "size": 3534},
      {"name": "LinkDistance", "size": 5731},
      {"name": "MaxFlowMinCut", "size": 7840},
      {"name": "ShortestPaths", "size": 5914},
      {"name": "SpanningTree", "size": 3416}
     ]
    },
    {
     "name": "optimization",
     "children": [
      {"name": "AspectRatioBanker", "size": 7074}
     ]
    }
   ]
  },
  {
   "name": "animate",
   "children": [
    {"name": "Easing", "size": 17010},
    {"name": "FunctionSequence", "size": 5842},
    {
     "name": "interpolate",
     "children": [
      {"name": "ArrayInterpolator", "size": 1983},
      {"name": "ColorInterpolator", "size": 2047},
      {"name": "DateInterpolator", "size": 1375},
      {"name": "Interpolator", "size": 8746},
      {"name": "MatrixInterpolator", "size": 2202},
      {"name": "NumberInterpolator", "size": 1382},
      {"name": "ObjectInterpolator", "size": 1629},
      {"name": "PointInterpolator", "size": 1675},
      {"name": "RectangleInterpolator", "size": 2042}
     ]
    },
    {"name": "ISchedulable", "size": 1041},
    {"name": "Parallel", "size": 5176},
    {"name": "Pause", "size": 449},
    {"name": "Scheduler", "size": 5593},
    {"name": "Sequence", "size": 5534},
    {"name": "Transition", "size": 9201},
    {"name": "Transitioner", "size": 19975},
    {"name": "TransitionEvent", "size": 1116},
    {"name": "Tween", "size": 6006}
   ]
  },
  {
   "name": "data",
   "children": [
    {
     "name": "converters",
     "children": [
      {"name": "Converters", "size": 721},
      {"name": "DelimitedTextConverter", "size": 4294},
      {"name": "GraphMLConverter", "size": 9800},
      {"name": "IDataConverter", "size": 1314},
      {"name": "JSONConverter", "size": 2220}
     ]
    },
    {"name": "DataField", "size": 1759},
    {"name": "DataSchema", "size": 2165},
    {"name": "DataSet", "size": 586},
    {"name": "DataSource", "size": 3331},
    {"name": "DataTable", "size": 772},
    {"name": "DataUtil", "size": 3322}
   ]
  },
  {
   "name": "display",
   "children": [
    {"name": "DirtySprite", "size": 8833},
    {"name": "LineSprite", "size": 1732},
    {"name": "RectSprite", "size": 3623},
    {"name": "TextSprite", "size": 10066}
   ]
  },
  {
   "name": "flex",
   "children": [
    {"name": "FlareVis", "size": 4116}
   ]
  },
  {
   "name": "physics",
   "children": [
    {"name": "DragForce", "size": 1082},
    {"name": "GravityForce", "size": 1336},
    {"name": "IForce", "size": 319},
    {"name": "NBodyForce", "size": 10498},
    {"name": "Particle", "size": 2822},
    {"name": "Simulation", "size": 9983},
    {"name": "Spring", "size": 2213},
    {"name": "SpringForce", "size": 1681}
   ]
  },
  {
   "name": "query",
   "children": [
    {"name": "AggregateExpression", "size": 1616},
    {"name": "And", "size": 1027},
    {"name": "Arithmetic", "size": 3891},
    {"name": "Average", "size": 891},
    {"name": "BinaryExpression", "size": 2893},
    {"name": "Comparison", "size": 5103},
    {"name": "CompositeExpression", "size": 3677},
    {"name": "Count", "size": 781},
    {"name": "DateUtil", "size": 4141},
    {"name": "Distinct", "size": 933},
    {"name": "Expression", "size": 5130},
    {"name": "ExpressionIterator", "size": 3617},
    {"name": "Fn", "size": 3240},
    {"name": "If", "size": 2732},
    {"name": "IsA", "size": 2039},
    {"name": "Literal", "size": 1214},
    {"name": "Match", "size": 3748},
    {"name": "Maximum", "size": 843},
    {
     "name": "methods",
     "children": [
      {"name": "add", "size": 593},
      {"name": "and", "size": 330},
      {"name": "average", "size": 287},
      {"name": "count", "size": 277},
      {"name": "distinct", "size": 292},
      {"name": "div", "size": 595},
      {"name": "eq", "size": 594},
      {"name": "fn", "size": 460},
      {"name": "gt", "size": 603},
      {"name": "gte", "size": 625},
      {"name": "iff", "size": 748},
      {"name": "isa", "size": 461},
      {"name": "lt", "size": 597},
      {"name": "lte", "size": 619},
      {"name": "max", "size": 283},
      {"name": "min", "size": 283},
      {"name": "mod", "size": 591},
      {"name": "mul", "size": 603},
      {"name": "neq", "size": 599},
      {"name": "not", "size": 386},
      {"name": "or", "size": 323},
      {"name": "orderby", "size": 307},
      {"name": "range", "size": 772},
      {"name": "select", "size": 296},
      {"name": "stddev", "size": 363},
      {"name": "sub", "size": 600},
      {"name": "sum", "size": 280},
      {"name": "update", "size": 307},
      {"name": "variance", "size": 335},
      {"name": "where", "size": 299},
      {"name": "xor", "size": 354},
      {"name": "_", "size": 264}
     ]
    },
    {"name": "Minimum", "size": 843},
    {"name": "Not", "size": 1554},
    {"name": "Or", "size": 970},
    {"name": "Query", "size": 13896},
    {"name": "Range", "size": 1594},
    {"name": "StringUtil", "size": 4130},
    {"name": "Sum", "size": 791},
    {"name": "Variable", "size": 1124},
    {"name": "Variance", "size": 1876},
    {"name": "Xor", "size": 1101}
   ]
  },
  {
   "name": "scale",
   "children": [
    {"name": "IScaleMap", "size": 2105},
    {"name": "LinearScale", "size": 1316},
    {"name": "LogScale", "size": 3151},
    {"name": "OrdinalScale", "size": 3770},
    {"name": "QuantileScale", "size": 2435},
    {"name": "QuantitativeScale", "size": 4839},
    {"name": "RootScale", "size": 1756},
    {"name": "Scale", "size": 4268},
    {"name": "ScaleType", "size": 1821},
    {"name": "TimeScale", "size": 5833}
   ]
  },
  {
   "name": "util",
   "children": [
    {"name": "Arrays", "size": 8258},
    {"name": "Colors", "size": 10001},
    {"name": "Dates", "size": 8217},
    {"name": "Displays", "size": 12555},
    {"name": "Filter", "size": 2324},
    {"name": "Geometry", "size": 10993},
    {
     "name": "heap",
     "children": [
      {"name": "FibonacciHeap", "size": 9354},
      {"name": "HeapNode", "size": 1233}
     ]
    },
    {"name": "IEvaluable", "size": 335},
    {"name": "IPredicate", "size": 383},
    {"name": "IValueProxy", "size": 874},
    {
     "name": "math",
     "children": [
      {"name": "DenseMatrix", "size": 3165},
      {"name": "IMatrix", "size": 2815},
      {"name": "SparseMatrix", "size": 3366}
     ]
    },
    {"name": "Maths", "size": 17705},
    {"name": "Orientation", "size": 1486},
    {
     "name": "palette",
     "children": [
      {"name": "ColorPalette", "size": 6367},
      {"name": "Palette", "size": 1229},
      {"name": "ShapePalette", "size": 2059},
      {"name": "SizePalette", "size": 2291}
     ]
    },
    {"name": "Property", "size": 5559},
    {"name": "Shapes", "size": 19118},
    {"name": "Sort", "size": 6887},
    {"name": "Stats", "size": 6557},
    {"name": "Strings", "size": 22026}
   ]
  },
  {
   "name": "vis",
   "children": [
    {
     "name": "axis",
     "children": [
      {"name": "Axes", "size": 1302},
      {"name": "Axis", "size": 24593},
      {"name": "AxisGridLine", "size": 652},
      {"name": "AxisLabel", "size": 636},
      {"name": "CartesianAxes", "size": 6703}
     ]
    },
    {
     "name": "controls",
     "children": [
      {"name": "AnchorControl", "size": 2138},
      {"name": "ClickControl", "size": 3824},
      {"name": "Control", "size": 1353},
      {"name": "ControlList", "size": 4665},
      {"name": "DragControl", "size": 2649},
      {"name": "ExpandControl", "size": 2832},
      {"name": "HoverControl", "size": 4896},
      {"name": "IControl", "size": 763},
      {"name": "PanZoomControl", "size": 5222},
      {"name": "SelectionControl", "size": 7862},
      {"name": "TooltipControl", "size": 8435}
     ]
    },
    {
     "name": "data",
     "children": [
      {"name": "Data", "size": 20544},
      {"name": "DataList", "size": 19788},
      {"name": "DataSprite", "size": 10349},
      {"name": "EdgeSprite", "size": 3301},
      {"name": "NodeSprite", "size": 19382},
      {
       "name": "render",
       "children": [
        {"name": "ArrowType", "size": 698},
        {"name": "EdgeRenderer", "size": 5569},
        {"name": "IRenderer", "size": 353},
        {"name": "ShapeRenderer", "size": 2247}
       ]
      },
      {"name": "ScaleBinding", "size": 11275},
      {"name": "Tree", "size": 7147},
      {"name": "TreeBuilder", "size": 9930}
     ]
    },
    {
     "name": "events",
     "children": [
      {"name": "DataEvent", "size": 2313},
      {"name": "SelectionEvent", "size": 1880},
      {"name": "TooltipEvent", "size": 1701},
      {"name": "VisualizationEvent", "size": 1117}
     ]
    },
    {
     "name": "legend",
     "children": [
      {"name": "Legend", "size": 20859},
      {"name": "LegendItem", "size": 4614},
      {"name": "LegendRange", "size": 10530}
     ]
    },
    {
     "name": "operator",
     "children": [
      {
       "name": "distortion",
       "children": [
        {"name": "BifocalDistortion", "size": 4461},
        {"name": "Distortion", "size": 6314},
        {"name": "FisheyeDistortion", "size": 3444}
       ]
      },
      {
       "name": "encoder",
       "children": [
        {"name": "ColorEncoder", "size": 3179},
        {"name": "Encoder", "size": 4060},
        {"name": "PropertyEncoder", "size": 4138},
        {"name": "ShapeEncoder", "size": 1690},
        {"name": "SizeEncoder", "size": 1830}
       ]
      },
      {
       "name": "filter",
       "children": [
        {"name": "FisheyeTreeFilter", "size": 5219},
        {"name": "GraphDistanceFilter", "size": 3165},
        {"name": "VisibilityFilter", "size": 3509}
       ]
      },
      {"name": "IOperator", "size": 1286},
      {
       "name": "label",
       "children": [
        {"name": "Labeler", "size": 9956},
        {"name": "RadialLabeler", "size": 3899},
        {"name": "StackedAreaLabeler", "size": 3202}
       ]
      },
      {
       "name": "layout",
       "children": [
        {"name": "AxisLayout", "size": 6725},
        {"name": "BundledEdgeRouter", "size": 3727},
        {"name": "CircleLayout", "size": 9317},
        {"name": "CirclePackingLayout", "size": 12003},
        {"name": "DendrogramLayout", "size": 4853},
        {"name": "ForceDirectedLayout", "size": 8411},
        {"name": "IcicleTreeLayout", "size": 4864},
        {"name": "IndentedTreeLayout", "size": 3174},
        {"name": "Layout", "size": 7881},
        {"name": "NodeLinkTreeLayout", "size": 12870},
        {"name": "PieLayout", "size": 2728},
        {"name": "RadialTreeLayout", "size": 12348},
        {"name": "RandomLayout", "size": 870},
        {"name": "StackedAreaLayout", "size": 9121},
        {"name": "TreeMapLayout", "size": 9191}
       ]
      },
      {"name": "Operator", "size": 2490},
      {"name": "OperatorList", "size": 5248},
      {"name": "OperatorSequence", "size": 4190},
      {"name": "OperatorSwitch", "size": 2581},
      {"name": "SortOperator", "size": 2023}
     ]
    },
    {"name": "Visualization", "size": 16540}
   ]
  }
 ]
}
'''



