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
import typehooks

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults

inlizer=session_support.inlizer
_=session_support.translateString

fieldMap = [{'row':1, 'label':_('Name'), 'key':'Name', 'id':'name', 'type':'string'},
            {'row':1, 'label':_('DisplayName'), 'key':'DisplayName', 'id':'displayname', 'type':'string'},
            {'row':1, 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'type':'string'},
            {'row':1, 'label':_('SortOrder'), 'key':'SortOrder', 'id':'sortorder', 'type':'int'},                 
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
    return bottle.template("people_top.tpl",{"breadcrumbPairs":crumbTrack})


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
    
