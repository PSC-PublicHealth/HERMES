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

_hermes_svn_id_="$Id: typehooks.py 1989 2014-10-22 22:58:03Z welling $"


import sys,os,os.path,time,json,math,types
import bottle
import ipath

import typehelper
import shadow_network
import shadow_network_db_api
import htmlgenerator
import privs
from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults, b64D

from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
import site_info
import session_support_wrapper as session_support

sI = site_info.SiteInfo()

inlizer=session_support.inlizer
_=session_support.translateString

def typeEditPage(db, uiSession, typeClass):
    try:
        paramList = ['%s:%s'%(str(k),str(v)) for k,v in bottle.request.params.items()]
        _logMessage("Hit type-edit-page; params=%s"%paramList)
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        protoName = _getOrThrowError(bottle.request.params,'protoname')
        protoName = _smartStrip(protoName)
        if 'overwrite' in bottle.request.params:
            overwrite = True
        else:
            overwrite = False
        if 'backURL' in bottle.request.params:
            backURL = b64D(bottle.request.params['backURL'])
        else:
            backURL = 'query'
        crumbTracks = uiSession.getCrumbs().push((bottle.request.path,_("Create Modified Version")))
        return bottle.template("type_edit_dialog.tpl",{"breadcrumbPairs":crumbTracks,
                                                "protoname":protoName,
                                                "modelId":modelId,
                                                "typeClass":typeClass,
                                                "overwrite":overwrite,
                                                "backURL":backURL})
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return bottle.template("error.tpl",{"breadcrumbPairs":uiSession.getCrumbs(),
                               "bugtext":str(e)})


def editType(db, uiSession, typeClass):
    if bottle.request.params['oper']=='edit':
        if 'modelId' not in bottle.request.params.keys():
            return {}
        modelId = int(bottle.request.params['modelId'])
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = bottle.request.params['name']
        _logMessage("Name = %s"%name)
        pT = getattr(m, typeClass)[name]
        if 'dispnm' in bottle.request.params:
            _logMessage("New Display Name = %s"%bottle.request.params['dispnm'])
            pT.DisplayName = bottle.request.params['dispnm']
        return {}
    elif bottle.request.params['oper']=='add':
        raise bottle.BottleException(_('unsupported operation'))
    elif bottle.request.params['oper']=='del':
        raise bottle.BottleException(_('unsupported operation'))

 
    


def jsonTypeEditForm(db, uiSession, typeClass, fieldMap, useInstance=False):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        protoname = _getOrThrowError(bottle.request.params, 'protoname')
        print "in jsonTypeEditform params = {}".format(bottle.request.params)
        if 'overwrite' in bottle.request.params:
            proposedName = protoname
        else:
            proposedName = typehelper.getSuggestedName(db,modelId,typeClass, protoname, excludeATM=True)
        print "protoname = {0}".format(protoname)
        canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, protoname) # @UnusedVariable
        if not useInstance:
            attrRec = {}
            shadow_network._copyAttrsToRec(attrRec,typeInstance)
            print attrRec
        else:
            attrRec = typeInstance
        #print "attrRec = {0}".format(attrRec.presentation)
        htmlStr, titleStr = htmlgenerator.getTypeEditHTML(db,uiSession,
                                                          typeClass,
                                                          modelId,
                                                          protoname, fieldMap)
                                                          #typehelper.
                                                          #elaborateFieldMap(proposedName, 
                                                         #                              attrRec,
                                                          #                             fieldMap))
        result = {"success":True, "htmlstring":htmlStr, "title":titleStr}
    except privs.PrivilegeException:
        result = {'success':False, 'msg':_('User cannot read this model')}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = {'success':False, 'msg':str(e)}
    return result  

def jsonTypeEditVerifyAndCommit(db, uiSession, typeClass, fieldMap, classEditFn=None):
    try:
        anc = False
        if 'overwrite' in bottle.request.params:
            anc = True
        m,attrRec,badParms,badStr = _mergeFormResults(bottle.request, 
                                                      db, 
                                                      uiSession, 
                                                      fieldMap,
                                                      allowNameCollisions=anc)
       # print "AttRec in Type EditVer:"
        #print attrRec
        if badStr and badStr!="":
            result = {'success':True, 'value':False, 'msg':badStr}
        else:
            if classEditFn is not None:
#                 print "setting classEditFn"
#                 print classEditFn
                attrRec = classEditFn(attrRec, m)
                #print "ATTREC after classEdit: {0}".format(attrRec)
#            print "typeClass = {0}".format(typeClass)
            shdTypesClass = shadow_network.ShdTypes.typesMap[typeClass]
            newType = shdTypesClass(attrRec.copy()) 
#           print "newType Presentation = {0}".format(newType.presentation)
            db.add(newType)
            m.types[attrRec['Name']] = newType
            crumbTrack = uiSession.getCrumbs()
            result = {'success':True, 'value':True, 'goto':crumbTrack.getDoneURL()}
        return result
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        _logMessage(str(e))
        _logStacktrace()
        return result

def jsonTypeInfo(db, uiSession, htmlGeneratorFn):
    try:
        modelId = int(bottle.request.params['modelId'])
        name = bottle.request.params['name']
        htmlStr, titleStr = htmlGeneratorFn(db,uiSession,modelId,name)
        result = {'success':True, "htmlstring":htmlStr, "title":titleStr}
        return result
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        _logMessage(str(e))
        _logStacktrace()
        return result

@bottle.route('/json/generic-edit-cancel')
def jsonGenericEditCancel(db,uiSession):
    try:
        crumbTrack = uiSession.getCrumbs()
        return {'success':True, 'value': True, 'goto':crumbTrack.getDoneURL()}
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        _logMessage(str(e))
        _logStacktrace()
        return result    
        
@bottle.route('/json/get-alltypesmodel-id')
def jsonGetAllTypesModelID(db,uiSession):
    try:    
        m = db.query(shadow_network.ShdNetwork).filter(shadow_network.ShdNetwork.name=="AllTypesModel").one()
        return {'success':True,'id':m.modelId}
    except Exception, e:
        result = {'success':False, 'msg':str(e)}

@bottle.route('/json/check-if-type-exists-for-model')
def jsonCheckIfTypeNameExistsForModel(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
        typeName = _getOrThrowError(bottle.request.params,'typename')
        displayName = _getOrThrowError(bottle.request.params,'displayname')
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        result = {}
        displayNames = [typehelper.getTypeWithFallback(db, modelId, x)[1].DisplayName for x in m.types]
        if typeName in m.types:
            result = {'success':True,'exists':True,'which':'type'}
        elif displayName in displayNames:
            result = {'success':True,'exists':True,'which':'disp'}
        else:
            result = {'success':True,'exists':False}
        return result
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        return result
    
    
@bottle.route('/test-inv-grid')
def testInventoryGrid(db,uiSession):
    
    m = int(bottle.request.params['modelId'])
    crumbTrack = uiSession.getCrumbs()
    idcode = 100000
    return bottle.template('inventory_grid_test.tpl',title=_('Test Grid'),_=_,inlizer=inlizer,modelId=m,idcode=idcode)