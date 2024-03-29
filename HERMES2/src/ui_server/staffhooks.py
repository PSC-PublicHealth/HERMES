#!/usr/bin/env python


####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id: staffhooks.py 2262 2015-02-09 14:38:25Z stbrown $"

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
from currencyhelper import getCurrencyDict
import typehooks


from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults,_safeGetReqParam

inlizer=session_support.inlizer
_=session_support.translateString

fieldMap = [{ 'label':_('HERMES DB Id'), 'key':'Name', 'id':'name', 'info':False, 'edit':False, 'req':True, 'type':'dbkey'},
            { 'label':_('Name'), 'key':'DisplayName', 'id':'displayname', 'info':True, 'edit':True, 'req':True, 'type':'string'},
            { 'label':_('Yearly Salary'), 'key':'BaseSalary', 'id':'basesalary', 'info':True, 'edit':True, 'req':True, 'canzero':True, 
             'type':'cost', 'recMap':['BaseSalary', 'BaseSalaryCurCode', 'BaseSalaryYear']},
            { 'label':_('Fraction of Effort Dedicated to Supply Chain Logistics'), 'key':'FractionEPI', 'id':'fractionepi', 
             'info':True, 'edit':True, 'req':True, 'canzero':True, 'type':'float'},
            { 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'info':True, 'edit': True, 'req':False, 'type':'stringbox'},
            { 'label':_('SortOrder'), 'key':'SortOrder', 'id':'sortorder', 'info':False, 'edit':False,'req':False, 'type':'int'},
            ]

@bottle.route('/staff-top')
def staffTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Staff")))
    return bottle.template("staff_top.tpl",{"breadcrumbPairs":crumbTrack},pagehelptag="database")

@bottle.route('/staff-edit')
def staffEditPage(db, uiSession):
    return typehooks.typeEditPage(db,uiSession, 'staff')

@bottle.route('/edit/edit-staff.json', method='POST')
def editStaff(db,uiSession):
    return typehooks.typeEditPage(db,uiSession, 'staff')


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

def jsonStaffEditFn(attrRec, m):
    return attrRec
    
@bottle.route('/json/staff-edit-verify-commit')
def jsonStaffEditVerifyCommit(db,uiSession):
    return typehooks.jsonTypeEditVerifyAndCommit(db, uiSession, 'staff', fieldMap, jsonStaffEditFn)

            
@bottle.route('/json/staff-info')
def jsonStaffInfo(db,uiSession):
    return typehooks.jsonTypeInfo(db,uiSession,htmlgenerator.getStaffInfoHTML)
    
@bottle.route('/json/staff-edit-form')
def jsonStaffEditForm(db, uiSession):
    return typehooks.jsonTypeEditForm(db,uiSession,'staff',fieldMap)

@bottle.route('/json/manage-staff-explorer',method='POST')
def jsonManagePeopleExplorerTable(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        searchTerm = _safeGetReqParam(bottle.request.params, 'searchterm', default=None)
        #searchTerm = u"{0}".format(searchTermStr)
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException(_('Current User does not have access to model with Id = {0}: from json/manaage-staff-explorer'.format(modelId)))
    except ValueError, e:
        print 'Empty parameters supplied to manage-staff-explorer'
        print str(e)
        return {'success': 'false'}
    try:
        tList = typehelper.getTypeList(db,modelId,'staff',fallback=False)
        #print tList
        rows = []
        for v in tList:
            dispName = v['DisplayName'];
            if dispName == "":
                dispName = v['Name']
            row = {'id':v['Name'],
                       'name':v['DisplayName'],
                       'details':v['Name']
                       }
            if searchTerm:
                ## does this match name, manufacturer...
                for v in row.values():
                    if v.lower().find(searchTerm.lower()) > -1:
                        rows.append(row)
                        break
            else:
                rows.append(row)
            #rows.append(row)
            
        return {'success':True,
                'total':1,
                'page':1,
                'records':len(rows),
                'rows':rows
                }
    except Exception,e:
        return {'success':False,'msg':'manage-staff-explorer: {0}'.format(str(e))}
    
