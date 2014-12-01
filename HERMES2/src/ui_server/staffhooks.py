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
import shadow_network
import session_support_wrapper as session_support
from HermesServiceException import HermesServiceException
from gridtools import orderAndChopPage
import privs
import htmlgenerator
import typehelper

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults

inlizer=session_support.inlizer
_=session_support.translateString

fieldMap = [{'row':1, 'label':_('Name'), 'key':'Name', 'id':'name', 'type':'string'},
            {'row':1, 'label':_('DisplayName'), 'key':'DisplayName', 'id':'displayname', 'type':'string'},
            {'row':2, 'label':_('Base Salary'), 'key':'BaseSalary', 'id':'basesalary', 'type':'price'},  
            {'row':2, 'label':_('Salary Units'), 'key':'BaseSalaryCur', 'id':'basesalarycur', 'type':'currency'},   
            {'row':2, 'label':_('Salary Year'), 'key':'BaseSalaryYear', 'id':'basesalaryyear', 'type':'int'},  
            {'row':3, 'label':_('Fraction EPI'), 'key':'FractionEPI', 'id':'fractionepi', 'type':'float'},  
            {'row':3, 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'type':'string'},
            {'row':3, 'label':_('SortOrder'), 'key':'SortOrder', 'id':'sortorder', 'type':'int'},                 
            ]

@bottle.route('/staff-top')
def staffTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Population")))
    return bottle.template("staff_top.tpl",{"breadcrumbPairs":crumbTrack})

@bottle.route('/staff-edit')
def staffEditPage(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        protoName = _getOrThrowError(bottle.request.params,'protoname')
        protoName = _smartStrip(protoName)
        crumbTracks = uiSession.getCrumbs().push((bottle.request.path,_("Create Modified Version")))
        return bottle.template("staff_edit.tpl",{"breadcrumbPairs":crumbTracks,
                               "protoname":protoName,"modelId":modelId})
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        return bottle.template("error.tpl",{"breadcrumbPairs":uiSession.getCrumbs(),
                               "bugtext":str(e)})

@bottle.route('/edit/edit-staff.json', method='POST')
def editStaff(db,uiSession):    
    if bottle.request.params['oper']=='edit':
        if 'modelId' not in bottle.request.params.keys():
            return {}
        modelId = int(bottle.request.params['modelId'])
        _logMessage("editing modelId: %d"%modelId)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        _logMessage("we have permission")
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        _logMessage("we have a shadow Network")
        name = bottle.request.params['name']
        _logMessage("changed name")
        pT = m.staff[name]
        if 'dispnm' in bottle.request.params:
            _logMessage("Changing Display Name")
            pT.DisplayName = bottle.request.params['dispnm']
            _logMessage("Changed DisplayName")
            
        return {}
    elif bottle.request.params['oper']=='add':
        raise bottle.BottleException(_('unsupported operation'))
    elif bottle.request.params['oper']=='del':
        raise bottle.BottleException(_('unsupported operation'))

@bottle.route('/json/manage-staff-table')
def jsonManageStaffTable(db,uiSession):
    modelId = int(bottle.request.params['modelId'])
    try:
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d'%modelId)
    tList = typehelper.getTypeList(db, modelId, 'staff')
    nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                        {'name':'Name', 'usedin':'modelId', 'dispnm':'DisplayName'},
                                                        bottle.request)
    result = {
              "total":nPages,    # total pages
              "page":thisPageNum,     # which page is this
              "records":totRecs,  # total records
              "rows": [ {"name":t['Name'], 
                         "cell":[t['Name'], t['_inmodel'], t['DisplayName'], t['Name']]}
                       for t in tList ]
              }
    return result
    
@bottle.route('/json/staff-edit-verify-commit')
def jsonStaffEditVerifyCommit(db,uiSession):
    m,attrRec,badParms,badStr = _mergeFormResults(bottle.request, db, uiSession, fieldMap) # @UnusedVariable
    if badStr and badStr!="":
        result = {'success':True, 'value':False, 'msg':badStr}
    else:
        newStaff = shadow_network.ShdStaffType(attrRec.copy()) 
        db.add(newStaff)
        m.types[attrRec['Name']] = newStaff 
        crumbTrack = uiSession.getCrumbs().pop()
        result = {'success':True, 'value':True, 'goto':crumbTrack.currentPath()}
    return result
            
@bottle.route('/json/staff-info')
def jsonStaffInfo(db,uiSession):
    try:
        modelId = int(bottle.request.params['modelId'])
        name = bottle.request.params['name']
        htmlStr, titleStr = htmlgenerator.getStaffInfoHTML(db,uiSession,modelId,name)
        result = {'success':True, "htmlstring":htmlStr, "title":titleStr}
        return result
    except Exception, e:
        result = {'success':False, 'msg':str(e)}
        return result
    
@bottle.route('/json/staff-edit-form')
def jsonStaffEditForm(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId',isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        protoname = _getOrThrowError(bottle.request.params, 'protoname')
        proposedName = typehelper.getSuggestedName(db,modelId,"staff", protoname, excludeATM=True)
        canWrite,typeInstance = typehelper.getTypeWithFallback(db,modelId, protoname) # @UnusedVariable
        attrRec = {}
        shadow_network._copyAttrsToRec(attrRec,typeInstance)
        htmlStr, titleStr = htmlgenerator.getTypeEditHTML(db,uiSession,"staff",modelId,protoname,
                                                          typehelper.elaborateFieldMap(proposedName, attrRec,
                                                                                       fieldMap))
        result = {'success':True, "htmlstring":htmlStr, "title":titleStr}
    except privs.PrivilegeException:
        result = { 'success':False, 'msg':_('User cannot read this model')}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = { 'success':False, 'msg':str(e)}       
    return result
