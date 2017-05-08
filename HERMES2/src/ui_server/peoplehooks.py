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
_hermes_svn_id_="$Id: peoplehooks.py 2262 2015-02-09 14:38:25Z stbrown $"

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
import typehooks

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults,_safeGetReqParam

inlizer=session_support.inlizer
_=session_support.translateString

fieldMap = [{'label':_('HERMES DB ID'), 'key':'Name', 'id':'name', 'info':False,'edit':False,'req':True,'type':'dbkey'},
                        {'label':_('Name'), 'key':'DisplayName', 'id':'displayname', 'info':True,'edit':True,'req':True,'type':'string'},
                        {'label':_('SortOrder'), 'key':'SortOrder', 'id':'sortorder','info':False, 'edit':False, 'req':False,'type':'int'},         
                        {'label':_('Notes'), 'key':'Notes', 'id':'notes','info':True, 'edit':True, 'req':False,'type':'stringbox'},        
                        ]

@bottle.route('/people-edit')
def peopleEditPage(db, uiSession):
    return typehooks.typeEditPage(db, uiSession, 'people')

@bottle.route('/edit/edit-people.json', method='POST')
def editPeople(db,uiSession):    
    return typehooks.editType(db, uiSession, 'people')

@bottle.route('/json/people-edit-verify-commit')
def jsonPeopleEditVerifyCommit(db,uiSession):
    return typehooks.jsonTypeEditVerifyAndCommit(db, uiSession, 'people', fieldMap)
            
@bottle.route('/json/people-info')
def jsonPeopleInfo(db,uiSession):
    return typehooks.jsonTypeInfo(db, uiSession, htmlgenerator.getPeopleInfoHTML)
    
@bottle.route('/json/people-edit-form')
def jsonPeopleEditForm(db, uiSession):
    return typehooks.jsonTypeEditForm(db, uiSession, 'people', fieldMap)

@bottle.route('/people-top')
def peopleTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Population")))
    return bottle.template("people_top.tpl",{"breadcrumbPairs":crumbTrack},pagehelptag="database")


@bottle.route('/json/manage-people-table')
def jsonManagePeopleTable(db,uiSession):
    modelId = int(bottle.request.params['modelId'])
    try:
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d'%modelId)
    tList = typehelper.getTypeList(db, modelId, 'people')
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

@bottle.route('/json/manage-people-explorer',method='POST')
def jsonManagePeopleExplorerTable(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        searchTerm = _safeGetReqParam(bottle.request.params, 'searchterm', default=None)
        #searchTerm = u"{0}".format(searchTermStr)
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException(_('Current User does not have access to model with Id = {0}: from json/manaage-truck-explorer'.format(modelId)))
    except ValueError, e:
        print 'Empty parameters supplied to manage-truck-explorer'
        print str(e)
        return {'success': 'false'}
    try:
        tList = typehelper.getTypeList(db,modelId,'people')
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
        return {'success':False,'msg':'manage-people-explorer: {0}'.format(str(e))}
    
