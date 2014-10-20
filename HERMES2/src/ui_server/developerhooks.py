#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types
from StringIO import StringIO
import bottle
import ipath
import site_info
import shadow_network_db_api
import shadow_network
import privs
import htmlgenerator
import typehelper
from sqlalchemy.orm.exc import NoResultFound
from upload import uploadAndStore, makeClientFileInfo
from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _safeGetReqParam, _mergeFormResults
from gridtools import orderAndChopPage
import session_support_wrapper as session_support
from modelhooks import _findCanonicalStores
from demandhooks import _interpretDemandModelStructure
import util
import json
import truckhooks, fridgehooks, vaccinehooks, peoplehooks

inlizer=session_support.inlizer
_=session_support.translateString


@bottle.route('/tabs')
def tabPage(uiSession):
    return bottle.template("tabs.tpl",topLevelTabPairs=[('ajax/page_2',_('Menu Page')),
                                                       ('ajax/page_3',_('Tree Page')),
                                                       ('ajax/page_4',_('Table Page')),
                                                       ('ajax/page_5',_('Upload Page')),
                                                       ('ajax/page_6',_('Test Button')),
                                                       ('ajax/page_7',_('Store Editor')),
                                                       ('ajax/page_8',_('Type Selector')),
                                                       ('ajax/page_9',_('Route Editor')),
                                                       ('ajax/page_10',_('Pop-Up Menu')),
                                                       ('ajax/page_11',_('Data Entry')),
                                                       ('ajax/page_12',_('Type Editor')),
                                                       ('debug-ui',_('Debug'))
                                                       ])

@bottle.route('/debug-ui')
def debugUIPage(uiSession):
    return bottle.template("debugUI.tpl")

@bottle.route('/json/nothing')
def jsonNothing():
    result = {'success':True}
    return result

@bottle.route('/json/echo')
def jsonEcho():
    sio = StringIO()
    sio.write("/json/echo says:\n")
    for k,v in bottle.request.params.items():
        sio.write("%s : %s\n"%(k,v))
    result={'success':True,'value':sio.getvalue()}
    return result
    
@bottle.route('/json/type-edit-form')
def jsonTypeEditForm(db, uiSession):
    try:
        typeName = _getOrThrowError(bottle.request.params,'typename')
        modelId = _getOrThrowError(bottle.request.params,'modelId')
        try:
            uiSession.getPrivs().mayWriteModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        tp = m.types[typeName]
        attrRec = {}
        shadow_network._copyAttrsToRec(attrRec,tp)
        if tp.shdType == 'fridges':
            htmlStr, titleStr = htmlgenerator.getTypeEditHTML(db,uiSession,"fridge",modelId,typeName,
                                                              typehelper.elaborateFieldMap(typeName, attrRec,
                                                                                           fridgehooks.fieldMap))
            result = {"success":True, "htmlstring":htmlStr, "title":titleStr}
        elif tp.shdType == 'trucks':
            htmlStr, titleStr = htmlgenerator.getTypeEditHTML(db,uiSession,"truck",modelId,typeName,
                                                              typehelper.elaborateFieldMap(typeName, attrRec,
                                                                                           truckhooks.fieldMap))
            result = {"success":True, "htmlstring":htmlStr, "title":titleStr}
        elif tp.shdType == 'vaccines':
            htmlStr, titleStr = htmlgenerator.getTypeEditHTML(db,uiSession,"vaccine",modelId,typeName,
                                                              typehelper.elaborateFieldMap(typeName, attrRec,
                                                                                           vaccinehooks.fieldMap))
            result = {"success":True, "htmlstring":htmlStr, "title":titleStr}
        elif tp.shdType == 'people':
            htmlStr, titleStr = htmlgenerator.getTypeEditHTML(db,uiSession,"people",modelId,typeName,
                                                              typehelper.elaborateFieldMap(typeName, attrRec,
                                                                                           peoplehooks.fieldMap))
            result = {"success":True, "htmlstring":htmlStr, "title":titleStr}
        else:
            raise RuntimeError('Unknown shdType %s'%tp.shdType)
        return result
    except Exception,e:
        _logStacktrace()
        return {'success':False, 'msg':unicode(e)}

@bottle.route('/json/type-edit-verify-commit')
def jsonTypeEditVerifyAndCommit(db, uiSession):
    try:
        typeName = _getOrThrowError(bottle.request.params,'name')
        modelId = _getOrThrowError(bottle.request.params,'modelId')
        try:
            uiSession.getPrivs().mayWriteModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        tp = m.types[typeName]

        if tp.shdType == 'fridges':
            m,attrRec,badParms,badStr = _mergeFormResults(bottle.request, db, uiSession, fridgehooks.fieldMap,  # @UnusedVariable
                                                          allowNameCollisions=True)
            # PowerRateUnits is completely determined by energy type
            if attrRec['Energy']:
                attrRec['PowerRateUnits'] = fridgehooks.energyTranslationDict[attrRec['Energy'].encode('utf-8')][2]
            else:
                attrRec['PowerRateUnits'] = None
        elif tp.shdType == 'trucks':
            m,attrRec,badParms,badStr = _mergeFormResults(bottle.request, db, uiSession, truckhooks.fieldMap,  # @UnusedVariable
                                                          allowNameCollisions=True)
        elif tp.shdType == 'vaccines':
            m,attrRec,badParms,badStr = _mergeFormResults(bottle.request, db, uiSession, vaccinehooks.fieldMap,  # @UnusedVariable
                                                          allowNameCollisions=True)
        elif tp.shdType == 'people':
            m,attrRec,badParms,badStr = _mergeFormResults(bottle.request, db, uiSession, peoplehooks.fieldMap,  # @UnusedVariable
                                                          allowNameCollisions=True)
        else:
            raise RuntimeError('Unknown shdType %s'%tp.shdType)

        if badStr and badStr!="":
            result = {'success':True, 'value':False, 'msg':badStr}
        else:
            shadow_network._moveAttrs(tp, attrRec)
            result = {'success':True, 'value':True}
        return result
    except Exception, e:
        _logStacktrace()
        result = {'success':False, 'msg':str(e)}
        return result


@bottle.route('/json/data-entry-get-keys')
def jsonDataEntryGetKeys(db, uiSession):
    try:
        if 'dataEntryDict' in uiSession:
            keySet = set(['name'])
            for _,subDict in uiSession['dataEntryDict'].items():
                keySet |= set(subDict.keys())
            return {'success':True, 'keys':list(keySet)}
        else:
            return {'success':True, 'keys':['name']}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {'success':False, 'msg':str(e)}    

@bottle.route('/json/data-entry-enter', method='POST')
def jsonDataEntryEnter(db, uiSession):
    try:
        #d = {k:v for k,v in bottle.request.params.items()}
        d = bottle.request.json
        assert 'name' in d and d['name'] is not None, 'name field is missing'
        nm = d['name']
        if nm=='clearall':
            uiSession['dataEntryDict'] = {}
        else:
            if 'dataEntryDict' not in uiSession:
                uiSession['dataEntryDict'] = {}
            uiSession['dataEntryDict'][nm] = d
        
        # delete any empty entries
        killList = []
        for nm,subDict in uiSession['dataEntryDict'].items():
            if all([(v is None or v=='null') for k,v in subDict.items() if k!='name']):
                killList.append(nm)
        for nm in killList: del uiSession['dataEntryDict'][nm]
        
        uiSession.changed()
        print 'dataEntryDict is %s'%uiSession['dataEntryDict']
        return {'success':True}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {'success':False, 'msg':str(e)}    
    
@bottle.route('/json/data-entry-get-by-name') 
def jsonDataEntryGetByName(db, uiSession):
    try:
        nm = _getOrThrowError(bottle.request.params,'name')
        if 'dataEntryDict' in uiSession:
            keySet = set(['name'])
            for _,subDict in uiSession['dataEntryDict'].items():
                keySet |= set(subDict.keys())
            keyList = list(keySet)
            if nm in uiSession['dataEntryDict']:
                d = uiSession['dataEntryDict'][nm].copy()
            else:
                d = {'name':nm}
            for k in keyList:
                if k not in d: d[k] = None
            return {'success':True, 'value':d}
        else:
            return {'success':True, 'value':{'name':nm}}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {'success':False, 'msg':str(e)}         

@bottle.route('/json/data-entry-download')
def jsonDataEntryDownload(db, uiSession):
    zipFileName = "data-entry.zip"
    with uiSession.getLockedState() as state:
        (fileKey, fullZipFileName) = \
            state.fs().makeNewFileInfo(shortName = zipFileName,
                                       fileType = 'application/zip',
                                       deleteIfPresent = True)

    oldHDO = util.redirectOutput(fullZipFileName)
    if 'dataEntryDict' in uiSession: dataEntryDict = uiSession['dataEntryDict']
    else: dataEntryDict = {}
    with util.openOutputFile("data-entry.json") as f:
        f.write(json.dumps(dataEntryDict))
    util.redirectOutput(None,oldHDO)
    
    return bottle.static_file(zipFileName,os.path.dirname(fullZipFileName),
                              mimetype='application/zip',download=zipFileName)
    

@bottle.route('/json/throw-error')
def jsonThrowError():
    raise bottle.BottleException("/json/throw-error was called")

@bottle.route('/json/test-button')
def jsonTestButton(db, uiSession):
    try:
        for modelId in [2,6,4,8,3,7,9]:
            try:
                uiSession.getPrivs().mayReadModelId(db, modelId)
            except privs.PrivilegeException:
                raise bottle.BottleException('User may not read model %d'%modelId)
            m = shadow_network_db_api.ShdNetworkDB(db, modelId)
            print _interpretDemandModelStructure(m)
#        m = shadow_network_db_api.ShdNetworkDB(db, 9)
#         s2 = m.getStore(5)
#         s2.copyAttrsFromInstance(s1,excludeThese=['idcode','modelId','NAME'])
#         #s2.copyAttrsFromRec(s1.createRecord(),excludeThese=['idcode','modelId','NAME'])
        return {'success':True}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return {'success':False, 'msg':str(e)}

@bottle.route('/json/toggle-devel-mode')
def jsonToggleDevelMode(uiSession):
    if 'developerMode' in uiSession and uiSession['developerMode']:
        uiSession['developerMode'] = False
    else:
        uiSession['developerMode'] = True
    result = {'success':True}
    return result

@bottle.route('/json/become-system')
def jsonBecomeSystem(uiSession):
    uiSession.becomeSystem()
    result = {}
    return result

@bottle.route('/json/become-anyone')
def jsonBecomeAnyone(uiSession):
    uiSession.becomeAnyone()
    result = {}
    return result

@bottle.route('/json/show-dict')
def jsonShowDict(uiSession):
    reqDict = {}
    for k in bottle.request.params.keys():
        reqDict[k] = bottle.request.params[k]
    result = {              
              "sessionDict":uiSession.getDictSummary(),
              "path":bottle.request.path,
              "requestparams":reqDict
              }
    return result

@bottle.route('/json/clear-session-data')
def jsonClearSessionData(uiSession):
    uiSession.clearSessionData();
    _logMessage('sessionDict cleared')
    result = {}
    return result

@bottle.route('/json/clear-notes-data')
def jsonClearNotesData(uiSession):
    uiSession['notes'] = 'cleared'
    _logMessage('notes cleared')
    result = {}
    return result
    
@bottle.route('/json/clear-fs-metadata')
def jsonClearFSMetadata(uiSession):
    with uiSession.getLockedState() as state:
        state.fs().clearAllInfo()
    _logMessage('fs metadata cleared')
    result = {}
    return result
    
@bottle.route('/json/show-menu')
def jsonShowMenu(db, uiSession):
    models = db.query(shadow_network.ShdNetwork)
    menuItems = []
    prv = uiSession.getPrivs()
    for m in models: 
        try:
            prv.mayReadModelId(db, m.modelId)
            menuItems.append({"text":m.name, "href":'#%d'%m.modelId})
        except privs.PrivilegeException:
            pass
    result = { "other":"this doesn't pertain to the menu",
                "menu": {"notcontent":"might be class info",
                         "stillnotcontent":"and whatever else",
                         "content":{"notthiseither":"but who cares",
                                    "menuitem":menuItems
                                    }
                         }
              }
    return result
        



@bottle.route('/json/show-tree')
def jsonShowTree():
    try:
        nodeId = int(bottle.request.params['id'])
        if nodeId == -1: 
            result = {
                      "success":True,
                      "kidList":[{
                                  "data" : _("A node"),
                                  "metadata" : "can I find this string?", # This gets associated with the <a> node, I think
                                  "attr" : { "id" : 7 }, # The <li> for the tree node gets this ID
                                  "state" : "closed"
                                  #"children" : [ "Child 1", "A Child 2" ]
                                  }]
                }
        else:
            result = {
                      "success":True,
                      "kidList": [{
                                   "data" : {"title":_("First Child")},
                                   "attr" : { "id" : nodeId + 10 },
                                   "children" : [ _("Child 1"), 
                                                 {"data" : _("Closed child"),
                                                  "attr" : { "id" : nodeId + 15 },
                                                  "state" : "closed",
                                                  "metadata" : "can I find this string?", 
                                                  }
                                                 ],
                                   "state": "open"
                                   },
                                   {
                                   "data" : {"title":_("Leafy Second Child")},
                                   "attr" : { "id" : nodeId + 11 },
                                   },
                                   {
                                   "data" : {"title":_("Third Child")},
                                   "attr" : { "id" : nodeId + 12 },
                                   "children" : [ _("Child 1"), 
                                                 {"data" : _("Closed child"),
                                                  "attr" : { "id" : nodeId + 16 },
                                                  "state" : "closed",
                                                  "metadata" : "can I find this string?", 
                                                  }
                                                 ],
                                   "state": "closed"
                                   },
                                   ]
                      }
        return result
    except Exception,e:
        return { "success":False, "msg":str(e) }
    
@bottle.route('/json/show-table')
def jsonShowTable():
    result = {
              "total":7,
              "page":3,
              "records":117,
              "rows": [
                     { "id" : 1, "cell": ["one" , "row one"]},
                     { "id" : 2, "cell": ["two" , "row two"]},
                     { "id" : 3, "cell": ["three" , "row three"]},
                     { "id" : 4, "cell": ["four" , "<b>Will this be bold?</b>"]},
                     { "id" : 5, "cell": ["five" , "<a href='http://google.com'>a link</a>"]},
                     { "id" : 6, "cell": ["six" , "row six"]},
                     ]
              }
    return result

@bottle.post('/upload')
def uploadTest(db,uiSession):
    _logMessage('File upload is happening')
    #uiSession['notes'] += ', upload request'
    fileKey = None
    try:
        info = uploadAndStore(bottle.request, uiSession)
        clientData= makeClientFileInfo(info)
        clientData['code']= 0
        clientData['message']= ""
#        clientData['files'] = [{
#                                "name": info['shortName'],
#                                "size": os.path.getsize(info['serverSideName']),
#                                "url": "http:\/\/example.org\/files\/picture1.jpg",
#                                "thumbnail_url": "http:\/\/example.org\/files\/thumbnail\/picture1.jpg",
#                                "delete_url": "http:\/\/example.org\/files\/picture1.jpg",
#                                "delete_type": "DELETE"
#        }]
        clientData['files'] = [{
                                "name": info['shortName'],
                                "size": os.path.getsize(info['serverSideName'])
        }]
        return json.dumps(clientData)
    except Exception,e:
        _logMessage("\nException: %s"%e)
        _logStacktrace()
        # We could return text which would go into a browser window set as the 'target'
        # for this upload, but there doesn't seem to be much point.
        mdata = { 'code': 1, 'message': str(e) }
        if fileKey:
            try:
                with uiSession.getLockedState() as state:
                    state.fs().removeFileInfo(fileKey)
            except:
                pass
            
        return json.dumps(mdata)

@bottle.route('/test')
def test(uiSession):
    if 'test' in uiSession:
        uiSession['test'] += 1
    else:
        uiSession['test'] = 1
    return 'Test counter: %d' % uiSession['test']

@bottle.route('/json/clean-resultsgroup-table')
def jsonCleanResultsGroupTable(db, uiSession):
    try:
        count = 0
        for gp in db.query(shadow_network.HermesResultsGroup):
            if len(gp.results)>0: continue
            try:
                uiSession.getPrivs().mayModifyModelId(db, gp.modelId)
                db.delete(gp)
                count += 1
            except privs.PrivilegeException:
                pass
        return {'success':True, 'value':count}
    except Exception,e:
        return {'success':False, 'msg':str(e)}

        
            
            
            
            
            
