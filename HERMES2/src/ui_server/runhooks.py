#!/usr/bin/env python


_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types
import bottle
import ipath
from serverconfig import rootPath
import minionrunner
import privs
import input
import shadow_network_db_api
import shadow_db_routines
import shadow_network
#import shadow_network as shd
import session_support_wrapper as session_support
from HermesServiceException import HermesServiceException
from gridtools import orderAndChopPage
import htmlgenerator
import time
import crumbtracks
import costmodel
import psutil
import socket
import time

from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError, _getAttrDict

_minionFactory = None # lazy initialization

inlizer=session_support.inlizer
_=session_support.translateString

def addCrumb(uiSession, label, noInlize=False):
    if not noInlize:
        label = _(label)
    if uiSession.getCrumbs().currentLabel() == label:
        return uiSession.getCrumbs()
    url = bottle.request.path + '?' + bottle.request.query_string
    crumb = (url, label)
    crumbTrack = uiSession.getCrumbs().push(crumb)
    return crumbTrack

@bottle.route('/run-top')
def runTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Run")))
    return bottle.template("run_top.tpl",{"breadcrumbPairs":crumbTrack})

def generateInitialSeedTable(nInst,seeds):
    s = '<table><tr><th>%s</th><th>%s</th></tr>'%(_("Run"),_("Seed"));
    for i in xrange(nInst):
        s += '<tr><td>';
        s += str(i+1)
        idStr = 'seed_%d'%i;
        if len(seeds)>i and seeds[i] is not None:
            assert isinstance(seeds[i],(types.IntType,types.LongType)), _("A seed field has an inappropriate type")
            valStr = 'value=%s'%seeds[i]
        else:
            valStr = ''
        s += '</td><td><input type="number" id="%s" %s></td></tr>'%(idStr,valStr)
    s += '</table>'
    return s

@bottle.route('/model-run')
def newModelRunPage(db,uiSession):
    crumbTrack = addCrumb(uiSession,'Run Simulation')
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        developer = False
        if 'developerMode' in uiSession and uiSession['developerMode']:
            developer = True
        return bottle.template("run_model.tpl",
                               breadcrumbPairs=crumbTrack,
                               modelId=modelId,
                               developer=developer,
                               runName="sim " + time.strftime("%Y-%m-%d_%H:%M"))

    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        crumbTrack = addCrumbTrack(uiSession,"Problem Report")
        return bottle.template("problem.tpl",
                                breadcrumbPairs=crumbTrack,
                                comment=_("An error occurred while initiating the run: {0}".format(str(e))))


@bottle.route('/json/run-start',method="post")
def jsonRunStart(db, uiSession):
    global _minionFactory
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        uiSession.getPrivs().mayWriteModelId(db, modelId)
        runName = _getOrThrowError(bottle.request.params,'runName')
        deterministic = _safeGetReqParam(bottle.request.params,'deterministic',isBool=True)
        perfect = _safeGetReqParam(bottle.request.params,'perfect',isBool=True)
        nInstances =  _getOrThrowError(bottle.request.params,'nInstances',isInt=True)
        setSeed = _safeGetReqParam(bottle.request.params,'setseeds',isBool=True)
        
        optList = []
        if deterministic: optList.append('--deterministic')
        if perfect: optList.append('--perfect')
        
        if setSeed:
            foundAny = False
            seedStr = ''
            for i in range(nInstances):
                seed = _safeGetReqParam(bottle.require.params,'seed_{0}'.format(i))
                if seed:
                    foundAny = True
                    seedStr += "{0},".format(seed)
                else:
                    seedStr += ','
            
            if len(seedStr) > 0:
                seedStr = seedStr[:-1]
            
            if foundAny:
                optList.append("-Dseed={0}".format(seedStr))
             
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        
        runParamsString = _safeGetReqParam(bottle.request.params,'run_params')
        runParams = json.loads(runParamsString)
        badParms,deltas = _parseRunParms(db, uiSession, m, runParams)
 
        resultsGroupId = shadow_db_routines.addResultsGroup(modelId, runName, db)
        resultsGroup = m.getResultsGroupById(resultsGroupId)
        if deltas:
            for k,tp,val in deltas:   
                resultsGroup.addParm(shadow_network.ShdParameter(k,val))
                optList.append("-D{0}={1}".format(k,val))
        if _minionFactory is None:
            _minionFactory = minionrunner.MinionFactory()    
    
        with uiSession.getLockedState() as state:
            print "runName = {0}".format(runName)
            runId = _minionFactory.startRun(modelId,resultsGroupId, runName,
                                            #"%s_%d"%(runName,resultsGroup.resultsGroupId), 
                                            state.fs().workDir, 
                                            nReps=nInstances,
                                            optList=optList)
        _minionFactory.liveRuns[runId][0]['note'] = 'no note'
        _minionFactory.liveRuns[runId][0]['modelName'] = m.name
        _minionFactory.liveRuns[runId][0]['nReps'] = nInstances
        return { 'success':True, 'value':True }
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception, e:
        _logMessage(str(e))
        _logStacktrace()
        return { 'success':False, 'msg':str(e)}  

@bottle.route('/edit/edit-runs.json')
def editRuns():
    return {}


def runningStatus(stp):
    """
    returns a tuple to determine if the process defined in stp (shadow tick process)
    is local (position 0) and currently running on this machine (position 1) along with a printed status (position 2)
    """
    host = socket.gethostname()

    if stp.hostName != host:
        return (False, False, stp.status)

    if not psutil.pid_exists(stp.processId):
        if stp.status == "finished":
            return (True, False, "finished")

        if stp.status == "initial setup":
            if time.time() - stp.lastUpdate < 600:
                return (True, False, "initial setup")
        
        return (True, False, "process stopped at " + stp.status)

    #don't trust the process id if the tick process hasn't updated in the last ten minutes
    if time.time() - stp.lastUpdate > 600:
        if stp.status == "finished":
            return (True, False, "finished")
        return (True, False, "process stopped at " + stp.status)

    # we could put other checks against the command line or similar but for now we'll call this good enough.
    return (True, True, stp.status)
    
    

@bottle.route('/json/manage-runs-table')
def jsonManageRunsTable(db, uiSession):
#    global _minionFactory
#    if _minionFactory is None:
#        _minionFactory = minionrunner.MinionFactory()
#    rList = _minionFactory.liveRuns.values()

    rList = db.query(shadow_network.ShdTickProcess).all()

    rList = rList[:]
    
    #print rList

    pidStatusList = [runningStatus(r) for r in rList]
        
    nPages,thisPageNum,totRecs,rList = orderAndChopPage([{'runId':r.tickId,'status':ps[2],
                                                          'runName':r.runName,
                                                          'rundispname':r.runDisplayName,
                                                          'modelName':r.modelName, 'modelId':r.modelId,
                                                          'submitted':r.starttime,
                                                          'note':r.note, 'local':ps[0],
                                                          'running':ps[1] } for r,ps in zip(rList, pidStatusList)],
                                                        {'runname':'runName', 'runid':'runId',
                                                         'modelname':'modelName', 'modelid':'modelId',
                                                         'submitted':'submitted','status':'status','note':'note'},
                                                        bottle.request)
    
    result = {
              "total":nPages,    # total pages
              "page":thisPageNum,     # which page is this
              "records":totRecs,  # total records
              "rows": [ {"runid":r['runId'],
                         "cell":[r['runName'], r['rundispname'],r['runId'], r['modelName'], r['modelId'], r['submitted'],
                                 r['status'], r['runId'], r['runId'], 
                                 #(not _minionFactory.liveRuns[r['runId']][1].done)]}
                                 r['running'] ]}
                       for r in rList]
              }
    #print result
    return result

@bottle.route('/model-run/json/run-parms-edit-form')
def jsonRunParmsEditForm(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        inputDefault = input.InputDefault()
        maxLevel = _safeGetReqParam(bottle.request.params, 'maxlevel', isInt=True) # may be None, which is OK
        fieldMap = []
        for t in inputDefault.orderedTokenListByLevel(level=maxLevel, allBelow=True):
            ### build field map entry
            fieldMapEntry = {'key': t.name, 'label':t.displayName}
            ### get info for this entry for Default
            
            ### convert the field types from default file
            if t.type in ['int','intOrNone','long','longOfNone']:
                fieldMapEntry['type'] = 'int'
            elif t.type in ['float','floatOrNone','probability']:
                fieldMapEntry['type'] = 'float'
            elif t.type in ['string','stringOrNone','filename','filenameOrNone']:
                fieldMapEntry['type'] = 'string'
            elif t.type in ['TF']:
                fieldMapEntry['type'] = 'bool'
            else:
                print t.name
                fieldMapEntry['type'] = 'string'
            
            #fieldMapEntry['order'] = int(t.order)-1
            ### Current value?
            if t.type == "TF":
                if t.default:
                    fieldMapEntry['value'] = 'true'
                else:
                    fieldMapEntry['value'] = 'false'
            else:
                fieldMapEntry['value'] = t.default
                
            tKey = fieldMapEntry['key']
            
            value = m.getParameterValue(tKey)
            if t.type in ['int_list','float_list','long_list','string_list']:
                if isinstance(value,list):
                    valueStr = ''
                    for v in value:
                        valueStr += "'{0}',".format(v)
                    value = valueStr[:-1]
                elif value is not None:
                    value = value.strip("[").strip("]")
            fieldMapEntry['value'] = value
            fieldMap.append(fieldMapEntry)

        fieldMapDict = {e['key']:e for e in fieldMap}
                
#         ### go through and figure out if there are any deltas from the uiSession              
#         if 'runInfo' in uiSession and 'deltas' in uiSession['runInfo']:
#             for k,tp,val in uiSession['runInfo']['deltas']: # @UnusedVariable
#                 if k in fieldMapDict:
#                     fieldMapDict[k]['value'] = val
        #htmlStr, titleStr = htmlgenerator.getRunParmsEditHTML(db,uiSession,modelId,eFM.values())
        htmlStr = htmlgenerator._buildRunParmEditFieldTableNew(fieldMap)
        titleStr = _("Run Parameters for model {0}".format(m.name))
        result = {"success":True, "htmlstring":htmlStr, "title":titleStr,"fieldMap":fieldMap}
    except bottle.HTTPResponse, e:
        _logMessage(str(e))
        _logStacktrace()
        raise # bottle will handle this
    except privs.PrivilegeException, e:
        _logMessage(str(e))
        _logStacktrace()
        result = { 'success':False, 'msg':_('User cannot read this model')}
    except Exception as e:
        _logMessage(str(e))
        _logStacktrace()
        result = { 'success':False, 'msg':"jsonRunParamsEditForm "+str(e)}
    return result    

@bottle.route('/json/run-validate-report')
def jsonValidateRun(db, uiSession):
    from validate_model import Validator
    
    try:
        modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        validator = Validator(m)
        validator.registerTest("all")
        validator.runAvailableTests()
        
        costModelVerifier = costmodel.getCostModelVerifier(m)
        costMessages = costModelVerifier.getProblemList(m)
        print costMessages
        report = [x for x in validator.getMessageList() if x['messtype'] == 'Fatal Errors']
        report += [{'test':None,'messtype':'Costing Errors','message':u'{0}'.format(p)} for p in costMessages]
        report += [x for x in validator.getMessageList() if x['messtype'] == 'Warnings']
        
        if len(report) == 0:
            report = [{'test':"All",
                       'messtype':'Success',
                       'message':_('There were no warnings or errors in the model, please proceed to press the Run Simulation button below')}]
        print "Report = {0}".format(report)
        return {'success':True,'report':report}
                
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except privs.PrivilegeException:
        result = { 'success':False, 'msg':_('User cannot read this model')}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = { 'success':False, 'msg':str(e)}
    return result
        
    
@bottle.route('/json/run-info')
def jsonRunInfo(db, uiSession):

#    global _minionFactory
#    if _minionFactory is None:
#        _minionFactory = minionrunner.MinionFactory()
    try:
        runId = _getOrThrowError(bottle.request.params, 'runId', isInt=True)
        processInfo = db.query(shadow_network.ShdTickProcess).filter_by(tickId=runId).one()

        htmlStr, titleStr = htmlgenerator.getRunInfoHTML(db,uiSession,processInfo)
        result = {"success":True, "htmlstring":htmlStr, "title":titleStr,
                  "running": False}  #(not runMinion.done)}
        return result
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/run-logs')
def jsonRunInfo(db, uiSession):

#    global _minionFactory
#    if _minionFactory is None:
#        _minionFactory = minionrunner.MinionFactory()
    try:
        runId = _getOrThrowError(bottle.request.params, 'runId', isInt=True)
        processInfo = db.query(shadow_network.ShdTickProcess).filter_by(tickId=runId).one()
        logs = processInfo.crashLogs
        strings = "<pre>\n"
        for l in logs:
            strings += l.blob
            strings += "\n"
        strings += "</pre>"
        
        htmlStr, titleStr = htmlgenerator.getRunInfoHTML(db,uiSession,processInfo)
        result = {"success":True, "htmlstring":strings, "title":"logs",
                  "running": False}  #(not runMinion.done)}
        return result
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/run-terminate')
def jsonRunTerminate(db, uiSession):
    try:
        runId = _getOrThrowError(bottle.request.params, 'runId', isInt=True)
        processInfo = db.query(shadow_network.ShdTickProcess).filter_by(tickId=runId).one()
        
        uiSession.getPrivs().mayWriteModelId(db,processInfo.modelId)
        p = psutil.Process(processInfo.processId)
        p.kill()
        result = {'success':True, 'id':runId}
        return result
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

@bottle.route('/json/run-clear')
def jsonRunClear(db, uiSession):
    try:
        runId = _getOrThrowError(bottle.request.params, 'runId', isInt=True)
        processInfo = db.query(shadow_network.ShdTickProcess).filter_by(tickId=runId).one()
        
        uiSession.getPrivs().mayWriteModelId(db,processInfo.modelId)
        db.delete(processInfo)
        result = {'success':True, 'id':runId}
        return result
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

def _parseRunParms(db, uiSession, model, postParms = None):
    """
    returns badParms, deltas where:
       badParms is a list of parameters the formats of which are invalid
       deltas is a list of triples (key, typeString, value)
    """
    inputDefault = input.InputDefault()

#     if postParms is None:
#         postParms = bottle.request.params

    eFM = {}
    for pKey,p in model.parms.items():
        if inputDefault.getTokenType(pKey) == 'TF':
            val = (p.value.lower()=='true')
        else:
            print p.value
            val = p.value
        if pKey in eFM: 
            eFM[pKey]['value'] = val
        else: 
            eFM[pKey] = {'key':pKey, 'value':val}
            
    badParms = [] # list of inputs with invalid types
    deltas = [] # list of (key,typeString,value) tuples
    for k in inputDefault.iterkeys():
        if k in postParms:
            v = postParms[k]#_safeGetReqParam(postParms,k)
            if k in eFM: 
                oldV = eFM[k]['value']
            else:
                oldV = inputDefault[k]
            tp = inputDefault.getTokenType(k)
            #print '%s: %s <%s> <%s>'%(k,tp,v,oldV)
            try:
                if tp in ['filename', 'filename_list', 'filenameOrNone']:
                    pass
                    #raise HermesServiceException(_("Unexpectedly found type {0} in parms request").format(tp))
                elif tp =='string':
                    if k == "model":
                        print type(v)
                        print type(oldV)
                        print v
                        print oldV
                    # 'string' values should never be None
                    if v!=oldV:
                        deltas.append((k,tp,v))
                elif tp =='string_list':
                    # 'string_list' values can be None
                    if oldV is None:
                        if v != '': deltas.append((k,tp,v))
                    elif v!=oldV:
                        deltas.append((k,tp,v))
                elif tp == 'stringOrNone':
                    if v=='': v = None
                    if v!=oldV:
                        deltas.append((k,tp,v))
                elif tp == 'TF':
                    v = (v.lower() =='true')
                    if v!=oldV:
                        deltas.append((k,tp,v))                    
                elif tp in ['int', 'long']:
                    oldV = int(oldV)
                    v = int(v)
                    if v!=oldV:
                        deltas.append((k,tp,v))                    
                elif tp in ['intOrNone', 'longOrNone']:
                    if oldV is None:
                        if v is not None and v != '':
                            v = int(v)
                            deltas.append((k,tp,v))                    
                    else:
                        oldV = int(oldV)
                        v = int(v)
                        if v!=oldV:
                            deltas.append((k,tp,v))                    
                elif tp == 'float':
                    oldV = float(oldV)
                    v = float(v)
                    if v!=oldV:
                        deltas.append((k,tp,v))                    
                elif tp == 'floatOrNone':
                    #print "Old V for %s is %s and new is %s cond = %s"%(k,str(oldV),str(v),str(v == ''))
                    if oldV is None:
                        if v is not None and v != '':
                            v = float(v)
                            deltas.append((k,tp,v))                    
                    else:
                        oldV = float(oldV)
                        v = float(v)
                        if v!=oldV:
                            deltas.append((k,tp,v))
                elif tp == 'probability':
                    oldV = float(oldV)
                    v = float(v)
                    if v!=oldV:
                        if v < 0.0 or v > 1.0:
                            raise ValueError
                        deltas.append((k,tp,v))
                elif tp == 'string_list':
                    # list values can be None
                    
                    ## we need to preparse the string
                    if v == '':
                        if oldV is not None and oldV!='': 
                            deltas.append((k,tp,v))
                    else:
                        # Test parsability; throw exception if appropriate
                        l = [seg for seg in v.strip('[').strip(']').split(',')] # @UnusedVariable
                        if v != oldV:
                            deltas.append((k,tp,v))
                elif tp == 'int_list':
                    # list values can be None
                    if v == '':
                        if oldV is not None and oldV!='': 
                            deltas.append((k,tp,v))
                    else:
                        # Test parsability; throw exception if appropriate
                        l = [int(seg) for seg in v.strip('[').strip(']').split(',')] # @UnusedVariable
                        if v != oldV:
                            deltas.append((k,tp,v))
                elif tp == 'long_list':
                    # list values can be None
                    if v == '':
                        if oldV is not None and oldV != '': 
                            deltas.append((k,tp,v))
                    else:
                        # Test parsability; throw exception if appropriate
                        l = [long(seg) for seg in v.strip('[').strip(']').split(',')] # @UnusedVariable
                        if v != oldV:
                            deltas.append((k,tp,v))
                elif tp == 'float_list':
                    # list values can be None
                    if v == '':
                        if oldV is not None and oldV != '': 
                            deltas.append((k,tp,v))
                    else:
                        # Test parsability; throw exception if appropriate
                        l = [float(seg) for seg in v.strip('[').strip(']').split(',')] # @UnusedVariable
                        if l != oldV:
                            deltas.append((k,tp,l))
                else:
                    raise HermesServiceException(_("Unrecognized parm type {0}").format(tp))
            
            except ValueError:
                badParms.append(k)
        
    #print 'badParms: %s'%badParms
    #print 'deltas: %s'%deltas
    return badParms,deltas

@bottle.route('/json/run-parms-levels-to-show')
@bottle.route('/model-run/json/run-parms-levels-to-show')
def jsonRunParmsLevelsToShow(db, uiSession):
    level = _getOrThrowError(bottle.request.params, 'level', isInt=True)
    
    try:
        inputDefault = input.InputDefault()
        
        paramListForLevel = inputDefault.orderedTokenListByLevel(level,True)
        result = {'success':True,'keyList':[x.name for x in paramListForLevel]}
        return result
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = {'success':False, 'msg':str(e)}
        return result
    

### Deprecated Functions  
# @bottle.route('/model-run-old')
# @bottle.route('/model-run-old/<step>')
# def modelRunPage(db,uiSession,step="unknown"):
# 
#     formVals = { 'breadcrumbPairs':uiSession.getCrumbs() }
#     try:
#         crumbTrack = uiSession.getCrumbs()
#         stepPairs = [('specify',_('Start')),
#                      #('realitycheck',_('Verify')),
#                      ('specifics',_('Details')),
#                      ('run',_('Go!')),
#                      ]
#         namedStepList = [a for a,b in stepPairs] # @UnusedVariable
#         screen = None
#         if 'runInfo' in uiSession and 'modelId' in uiSession['runInfo']:
#             # beware of the case where runInfo survives but the model is gone
#             try:
#                 uiSession.getPrivs().mayReadModelId(db, uiSession['runInfo']['modelId'])
#             except Exception,e:
#                 uiSession['runInfo'] = {}
#                 if 'runCrumbTrack' in uiSession:
#                     del uiSession['runCrumbTrack']
#         else:
#             uiSession['runInfo'] = {}
#         if "runCrumbTrack" in uiSession:
#             runCrumbTrack = uiSession['runCrumbTrack']
#             if crumbTrack.trail[-1] != runCrumbTrack:
#                 crumbTrack.push(runCrumbTrack)
#         else:
#             runCrumbTrack = None
#         if step=="unknown" or runCrumbTrack is None:
#             runCrumbTrack = crumbtracks.TrackCrumbTrail(bottle.request.path, _("Run Model"))
#             for a,b in stepPairs: runCrumbTrack.append((a,b))
#             uiSession['runCrumbTrack'] = runCrumbTrack
#             crumbTrack.push(runCrumbTrack)
#             step = screen = runCrumbTrack.current()
#         elif step=='next':
#             screen = runCrumbTrack.next()
#             if screen is None:
#                 # We just finished the track
#                 del uiSession['runCrumbTrack']
#                 crumbTrack.pop()
#                 screen = 'run-top'
#         elif step=='back':
#             screen = runCrumbTrack.back()
#             if screen is None:
#                 # We just backed off the start of the track
#                 crumbTrack.pop()
#                 screen = 'run-top'
#         elif step=='edit-parms':
#             screen = 'edit-parms'
#             crumbTrack.push((bottle.request.path,_("Edit Run Parameters")))
#         else:
#             if not crumbTrack.jump(step):
#                 raise bottle.BottleException("Invalid step %s in run model"%step)
#             screen = crumbTrack.current()
#     
#         paramList = ['%s:%s'%(str(k),str(v)) for k,v in bottle.request.params.items()]
#         _logMessage("Hit model-run; step=%s, params=%s"%(step,paramList))
#         runInfo = uiSession['runInfo']
# 
#         reqParams = bottle.request.params
#         _checkDefAndInvalidate(reqParams, runInfo, 'runName', 'runName', None)
#         _intCheckDefAndInvalidate(reqParams, runInfo, 'modelId', 'modelId', None)
#         _intCheckDefAndInvalidate(reqParams, runInfo, 'nInstances', 'nInstances', None)
#         _intCheckAscendingListAndInvalidate(reqParams, runInfo, 'seed_%d', 'seeds',
#                                             invalidateName=None, baseCount=0)
#         _boolCheckDefAndInvalidate(reqParams, runInfo, 'deterministic', 'deterministic', None)
#         _boolCheckDefAndInvalidate(reqParams, runInfo, 'perfect','perfect',None)
#         _boolCheckDefAndInvalidate(reqParams, runInfo, 'setseeds', 'setseeds', None)
#         if 'modelId' in reqParams: uiSession['selectedModelId'] = int(runInfo['modelId'])
#         uiSession.changed() # maybe the _checkDefs changed it; be safe.
#             
#         if 'modelId' in runInfo:
#             uiSession.getPrivs().mayReadModelId(db, runInfo['modelId'])
#             m = shadow_network_db_api.ShdNetworkDB(db, runInfo['modelId'])
#             runInfo['modelName'] = m.name
#         formVals = {"breadcrumbPairs":crumbTrack,
#                     'generateInitialSeedTable':generateInitialSeedTable}
#         for k in ['runName','modelId','modelName','nInstances','seeds','deterministic','perfect','setseeds']:
#             if k in runInfo: formVals[k] = runInfo[k]
#         if screen=="specify":
#             developer = False
#             if 'developerMode' in uiSession and uiSession['developerMode']:
#                 developer = True
#             return bottle.template("run_specify.tpl",formVals,developer=developer)
#         elif screen=="realitycheck":
#             return bottle.template("run_realitycheck.tpl",formVals)
#         elif screen=="specifics":
#             developer = False
#             if 'developerMode' in uiSession and uiSession['developerMode']:
#                 developer = True
#             return bottle.template("run_specifics.tpl",formVals,developer=developer)
#         elif screen=="run":
#             return bottle.template("run_run.tpl",formVals)
#         elif screen=="run-top":
#             bottle.redirect("%srun-top"%rootPath)
#         elif screen=="edit-parms":
#             return bottle.template("run_edit_parms.tpl",formVals)
#         else:
#             formVals["comment"] = _("We have somehow forgotten which step we are on in running your model.")
#             return bottle.template("problem.tpl",formVals)
#     except bottle.HTTPResponse:
#         raise # bottle will handle this
#     except Exception,e:
#         _logMessage(str(e))
#         _logStacktrace()
#         formVals['comment'] = _("An error occurred while initiating the run: {0}".format(str(e)))
#         return bottle.template("problem.tpl",formVals)
# 
# @bottle.route('/json/run-start-old')
# def jsonRunStart(db, uiSession):
#     global _minionFactory
#     try:
#         modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
#         uiSession.getPrivs().mayWriteModelId(db, modelId)
#         runName = _safeGetReqParam(bottle.request.params,'runName')
#         if 'runInfo' not in uiSession:
#             raise bottle.BottleException('Unexpectedly cannot find details for this run')
#         runInfo = uiSession['runInfo']
#         optList = []
#         if 'deterministic' in runInfo and runInfo['deterministic']:
#             optList.append('--deterministic')
#         if 'perfect' in runInfo and runInfo['perfect']:
#             optList.append('--perfect')
#         if 'seeds' in runInfo and runInfo['seeds']:
#             foundAny = False
#             seedStr = ''
#             for s in runInfo['seeds']:
#                 if s:
#                     foundAny = True
#                     seedStr += '%s,'%s
#                 else:
#                     seedStr += ','
#             if len(runInfo['seeds']): seedStr = seedStr[:-1] # drop trailing comma
#             if foundAny:
#                 optList.append('-Dseed=%s'%seedStr)
#         if 'deltas' in runInfo:
#             for k,tp,val in runInfo['deltas']:
#                 optList.append('-D%s=%s'%(k,val))
#         
#         model = shadow_network_db_api.ShdNetworkDB(db, modelId)
#         
#         costModelVerifier = costmodel.getCostModelVerifier(model)
#         if not costModelVerifier.checkReady(model):
#             raise RuntimeError('cost model is incomplete')
#         
#         resultsGroupId = shadow_db_routines.addResultsGroup(modelId, runName, db)
#         resultsGroup = model.getResultsGroupById(resultsGroupId)
#         #shadow_network.HermesResultsGroup(modelId,runName)
#         if 'deltas' in runInfo:
#             for k,tp,val in runInfo['deltas']:   
#                 resultsGroup.addParm(shadow_network.ShdParameter(k,val))
#         
#         if _minionFactory is None:
#             _minionFactory = minionrunner.MinionFactory()       
#         with uiSession.getLockedState() as state:
#             runId = _minionFactory.startRun(modelId,resultsGroupId,
#                                             #"%s_%d"%(runName,resultsGroup.resultsGroupId), 
#                                             state.fs().workDir, 
#                                             nReps=runInfo['nInstances'],
#                                             optList=optList)
#         _minionFactory.liveRuns[runId][0]['note'] = 'no note'
#         _minionFactory.liveRuns[runId][0]['modelName'] = model.name
#         _minionFactory.liveRuns[runId][0]['nReps'] = runInfo['nInstances']
#         uiSession['runInfo'] = {}
#         return { 'success':True, 'value':True }
#     except bottle.HTTPResponse:
#         raise # bottle will handle this
#     except Exception, e:
#         _logMessage(str(e))
#         _logStacktrace()
#         return { 'success':False, 'msg':str(e)}  
# def _checkDefAndInvalidate(reqParams,defDict,name1,name2,invalidateName=None):
#     #print '###### check and invalidate <%s> <%s> <%s>'%(name1,name2,invalidateName)
#     if name1 in reqParams:
#         if name2 in defDict:
#             if reqParams[name1]!=defDict[name2]:
#                 defDict[name2] = reqParams[name1]
#                 if invalidateName is not None and invalidateName in defDict:
#                     del defDict[invalidateName]
#         else:
#             defDict[name2] = reqParams[name1]
#             if invalidateName is not None and invalidateName in defDict:
#                 del defDict[invalidateName]
# 
# def _intCheckDefAndInvalidate(reqParams,defDict,name1,name2,invalidateName=None):
#     #print '###### int check and invalidate <%s> <%s> <%s>'%(name1,name2,invalidateName)
#     if name1 in reqParams:
#         if name2 in defDict:
#             if int(reqParams[name1])!=defDict[name2]:
#                 defDict[name2] = int(reqParams[name1])
#                 if invalidateName is not None and invalidateName in defDict:
#                     del defDict[invalidateName]
#         else:
#             defDict[name2] = int(reqParams[name1])
#             if invalidateName is not None and invalidateName in defDict:
#                 del defDict[invalidateName]
# 
# def _boolCheckDefAndInvalidate(reqParams,defDict,name1,name2,invalidateName=None):
#     #print '###### int check and invalidate <%s> <%s> <%s>'%(name1,name2,invalidateName)
#     if name1 in reqParams:
#         flag = (reqParams[name1]=="true")
#         if name2 in defDict:
#             if isinstance(defDict[name2],types.BooleanType): oldFlag = defDict[name2]
#             else: oldFlag = (defDict[name2]=="true")
#             if flag!=oldFlag:
#                 defDict[name2] = flag
#                 if invalidateName is not None and invalidateName in defDict:
#                     del defDict[invalidateName]
#         else:
#             defDict[name2] = flag
#             if invalidateName is not None and invalidateName in defDict:
#                 del defDict[invalidateName]
# 
# def _getAscendingList(reqParams,baseName,baseCount=1):
#     l = []
#     for _ in xrange(baseCount-1): l.append(())
#     i = baseCount
#     while True:
#         s = baseName%i
#         if s in reqParams:
#             l.append(reqParams[s])
#             i += 1
#         else:
#             break
#     return l
#         
# def _checkAscendingListAndInvalidate(reqParams,defDict,baseName,name2,invalidateName=None,baseCount=1):
#     newList = _getAscendingList(reqParams,baseName,baseCount)
#     if newList != [] and newList != [()]:
#         if name2 in defDict:
#             if newList != defDict[name2]:
#                 defDict[name2] = newList
#                 if invalidateName is not None and invalidateName in defDict:
#                     del defDict[invalidateName]
#         else:
#             defDict[name2] = newList
#             if invalidateName is not None and invalidateName in defDict:
#                 del defDict[invalidateName]
#                 
# def _intCheckAscendingListAndInvalidate(reqParams,defDict,baseName,name2,invalidateName=None,baseCount=1):
#     newList = _getAscendingList(reqParams,baseName,baseCount)
#     if newList != [] and newList != [()]:
#         l = []
#         for term in newList:
#             if isinstance(term,types.StringTypes): 
#                 if len(term)==0: l.append(None)
#                 else: l.append(int(term))
#             else: l.append(term)
#         newList = l
#         if name2 in defDict:
#             if newList != defDict[name2]:
#                 defDict[name2] = newList
#                 if invalidateName is not None and invalidateName in defDict:
#                     del defDict[invalidateName]
#         else:
#             defDict[name2] = newList
#             if invalidateName is not None and invalidateName in defDict:
#                 del defDict[invalidateName]

# @bottle.route('/json/run-parms-edit')
# @bottle.route('/json/run-parms-edit', method='POST')
# def jsonRunParmsEdit(db, uiSession):
#     modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
#     uiSession.getPrivs().mayReadModelId(db, modelId)
#     m = shadow_network_db_api.ShdNetworkDB(db,modelId)
# 
#     badParms,deltas = _parseRunParms(db, uiSession, m)
#                 
#     badStr = None
#     if badParms:
#         badStr = _("The following parameters are invalid: ")
#         for p in badParms: badStr += "%s, "%p
#         badStr = badStr[:-2] # trim trailing comma
#     if badStr:
#         result = {'success':True, 'value':False, 'msg':badStr}
#     else:
#         if 'runInfo' not in uiSession:
#             uiSession['runInfo'] = {}
#         uiSession['runInfo']['deltas'] = deltas
#         uiSession.changed()
#         ### change the values that are deltas
#         #if 'runInfo' in uiSession and 'deltas' in uiSession['runInfo']:
#         #    for k,tp,val in uiSession['runInfo']['deltas']: # @UnusedVariable
#         #        #"Print updating param %s in deltas with value %s"%(k,str(val))
#         #        m.parms[k].setValue(val)
#         result = {'success':True, 'value':True}
#     return result
