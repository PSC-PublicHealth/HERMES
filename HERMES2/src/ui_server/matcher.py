#!/usr/bin/env python

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id$"

import sys,os,os.path
from StringIO import StringIO
import bottle
import ipath
import csv_tools
import site_info
import serverconfig
import typehelper
import privs
import session_support_wrapper as session_support
import shadow_network
from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError, _smartStrip
import clipboard
import developerhooks
import modelhooks
import peoplehooks
import vaccinehooks
import fridgehooks
import truckhooks
import staffhooks
import runhooks
import resultshooks
import pagehelp
import model_edit_hooks
import geographic_visualization
import widgethooks
import demandhooks
import costhooks
import information_dialog_box_hooks
import results_excel_report
import reporthooks

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
sI = site_info.SiteInfo()
#try:
#    cwd = os.path.dirname(__file__)
#    if cwd not in sys.path:
#        sys.path.append(cwd)
#
#    if sI.srcDir() not in sys.path:
#        sys.path.append(sI.srcDir())
#except:
#    pass

inlizer=session_support.inlizer
_=session_support.translateString

_toolTipDict = None

def initializeToolTips():
    """
    This produces a layered dictionary of tooltips of the form d[locale][pagepath][elementId] = tipString
    """
    csvFname = os.path.join( site_info.SiteInfo().srcDir(), '..', 'ui_server', 'ToolTips.csv')
    result = {}
    try:
        with open(csvFname,'rU') as f:
            keys,recs = csv_tools.parseCSV(f)
            localeList = [ k for k in keys if k not in ['Location','Path','Button ID','Notes']]
            for l in localeList:
                if l not in result: result[l] = {}
            for rec in recs:
                url = rec['Path']
                while url[0] == '/': url = url[1:]
                elemId = rec['Button ID']
                for l in localeList:
                    if url not in result[l]: result[l][url] = {}
                    result[l][url][elemId] = rec[l]
    except Exception,e:
        raise RuntimeError("Missing or unparsable ToolTips file %s: %s"%(csvFname,str(e)))
    return result
            
def _getToolTips():
    global _toolTipDict
    if _toolTipDict is None: _toolTipDict = initializeToolTips()
    path = bottle.request.path
    while path[0] == '/': path = path[1:]
    sio = StringIO()
    sio.write('{')
    if inlizer.currentLocaleName in _toolTipDict and path in _toolTipDict[inlizer.currentLocaleName]:
        pD = _toolTipDict[inlizer.currentLocaleName][path].copy()
    else: pD = {}
    if '*' in _toolTipDict[inlizer.currentLocaleName]:
        pD.update(_toolTipDict[inlizer.currentLocaleName]['*'])
    for k,v in pD.items(): 
        vStr = v
        if len(v) > 1:
            if v[0] == '"' and v[len(v)-1] == '"':
                vStr = v[1:-1]        
        sio.write(u'"{0}":"{1}",\n'.format(k,vStr))
    uiSession = session_support.UISession.getFromRequest(bottle.request)
    if 'developerMode' in uiSession and uiSession['developerMode']:
        sio.write("""
            'button,input,select':function(elem) { 
                return 'url: %s id: '+$(elem).attr('id')+' class: '+$(elem).attr('class');
            }
        """%bottle.request.path)
    sio.write('}')
    return sio.getvalue()

def _setupToolTips():
    sio = StringIO()
    sio.write("$(document).hrmWidget({widget:'tooltips',tips:")
    sio.write(_getToolTips())
    sio.write("});\n")
    return sio.getvalue()

bottle.SimpleTemplate.defaults.update({'_':_, 'inlizer':inlizer, 'rootPath':serverconfig.rootPath, 
                                       'getToolTips':_getToolTips, 'setupToolTips':_setupToolTips})

@bottle.route('/static/<filepath:path>')
def server_static(filepath):
    _logMessage("static get of %s"%filepath)
    return bottle.static_file(filepath, root='../ui_www/')

@bottle.route('/%s'%serverconfig.topPath)
def topPage(uiSession):
    createnew = _safeGetReqParam(bottle.request.params,'createnew',isInt=True)
    createPass = -1
    if createnew:
        createPass = createnew

    crumbTrack = uiSession.getCrumbs()  # to trigger automatic features, even if we don't use it here

    return bottle.template("welcome.tpl", title=_('This title is set in matcher'),createnew=createPass)

@bottle.route('/notimpl')
@bottle.view("notimplemented.tpl")
def notimplPage():
    return {}

@bottle.route('/ajax/<path>')
def handleAjax(path):
    _logMessage('Ajax path request for %s'%path)
    try:
        result = bottle.template(path+'.tpl') # No use of request.params to prevent code injection
    except Exception,e:
        _logMessage('template failed: %s'%e)
        raise bottle.HTTPError(body=_('Attempt to build template from {0} failed').format(path)+'.tpl',
                               exception=e)
    _logMessage('Ajax template %s was successful'%path)
    return result

@bottle.route('/check-unique')
def handleCheckUnique(db,uiSession):
    _logMessage('/check-unique with params %s'%[(k,v) for k,v in bottle.request.params.items()])
    modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
    uiSession.getPrivs().mayReadModelId(db, modelId)
    if 'runName' in bottle.request.params:
        target = 'runName'
        proposedName = bottle.request.params[target]
        nMatches = db.query(shadow_network.HermesResultsGroup) \
            .filter_by(modelId=modelId).filter_by(name=proposedName).count()
    elif 'typeName' in bottle.request.params:
        target = 'typeName'
        proposedName = bottle.request.params[target]
        nMatches = db.query(shadow_network.ShdType) \
            .filter_by(modelId=modelId).filter_by(name=proposedName).count()
    else:
        raise HermesServiceException('check-unique: no checkable parameters')
    result = {'modelId':modelId, target:proposedName, 'matches':nMatches}
    _logMessage("Returning %s"%result)
    return result

@bottle.route('/check-unique-hint')
def handleCheckUniqueWithHint(db,uiSession):
    try:
        _logMessage('/check-unique-hint with params %s'%[(k,v) for k,v in bottle.request.params.items()])
        modelId = _safeGetReqParam(bottle.request.params, 'modelId',isInt=True)
        if modelId is None:
            raise HermesServiceException('check-unique requires modelId')
        uiSession.getPrivs().mayReadModelId(db, modelId)
        if 'runName' in bottle.request.params:
            target = 'runName'
        elif 'typeName' in bottle.request.params:
            target = 'typeName'
        else:
            raise HermesServiceException('check-unique-hint: no checkable parameters')
        proposedName = bottle.request.params[target]
        
        currentName = typehelper.getSuggestedName(db,modelId, target, proposedName)
        if currentName == proposedName:
            result = {'success':True, 'value':True, 'modelId':modelId, 'typeName':proposedName }
        else:
            result = {'success':True, 'value':False, 'modelId':modelId, 'typeName':proposedName,
                      'hint':currentName }
    except privs.PrivilegeException:
        result = { 'success':False, 'msg':_('User cannot read this model')}
    except Exception,e:
        result = { 'success':False, 'msg':str(e)}        
    _logMessage("Returning %s"%result)
    return result

@bottle.route('/check-may-modify')
def handleCheckMayModify(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        try:
            uiSession.getPrivs().mayModifyModelId(db, modelId)
        except privs.MayModifyPrivilegeException,e:
            return {'success':True, 'value':False}
        return { 'success':True, 'value':True }
    except Exception,e:
        return {'success':False, 'msg':str(e)}

@bottle.route('/show-help')
def helpPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Help")))
    return bottle.template('info.tpl', {'breadcrumbPairs':crumbTrack})

@bottle.route('/json/change-language')
def jsonChangeLanguage(db, uiSession):
    try:
        _logMessage('/json/change-language with params %s'%[(k,v) for k,v in bottle.request.params.items()])
        newLang = bottle.request.params['lang']
        inlizer.selectLocale(newLang)
        uiSession['locale'] = newLang
        result = { 'success':True }
    except Exception,e:
        result = { 'success':False, 'msg':str(e)}        
    _logMessage("Returning %s"%result)
    return result

@bottle.route('/json/translate',method='post')
def jsonTranslatePhrase(db, uiSession):
    try:
        phrasesDict = bottle.request.params
        phrases = [phrasesDict[str(x)] for x in range(0,len(phrasesDict))]
        print phrases
        transDict = []
        for phrase in phrases:
            transDict.append(_(phrase))
        print transDict
        return { 'success':True,
                 'translated_phrases':transDict
                 }
    except Exception,e:
        result = { 'success':False, 'msg':str(e)}        
        return result
    
@bottle.route('/json/generic-pop')
def jsonGenericPop(db, uiSession):
    try:
        crumbTrack = uiSession.getCrumbs()
        oldPath = crumbTrack.currentPath()
        crumbTrack.pop()
        newPath = crumbTrack.currentPath()
        _logMessage('/json/generic-pop: %s -> %s'%(oldPath, newPath))
        result = { 'success':True, 'goto':newPath}
    except Exception,e:
        result = { 'success':False, 'msg':str(e)}        
    return result

@bottle.route('/json/no-op')
@bottle.route('/json/no-op',method='POST')
def jsonNoOp(db, uiSession):
    if 'developerMode' in uiSession and uiSession['developerMode']:
        _logMessage('no-op with params %s'%[(k,v) for k,v in bottle.request.params.items()])
    return {'success':True}

@bottle.route('/tutorial')
def tutorialPage(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path + '?' + bottle.request.query_string, _("Tutorial")))
    return bottle.template('tutorial.tpl',{'breadcrumbPairs':crumbTrack},_=_,inlizer=inlizer)

application= session_support.wrapBottleApp(bottle.app())
