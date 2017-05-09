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
_hermes_svn_id_ = "$Id: perdiemhooks.py 2262 2015-02-09 14:38:25Z stbrown $"

import bottle
import ipath
import shadow_network_db_api
import shadow_network
import session_support_wrapper as session_support
from gridtools import orderAndChopPage
import privs
import htmlgenerator
import typehelper
from currencyhelper import getCurrencyDict
import typehooks

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, \
    _mergeFormResults,_safeGetReqParam

inlizer = session_support.inlizer
_ = session_support.translateString

fieldMap = [{ 'label': _('Name'), 'key': 'Name', 'id': 'name', 'info':False, 'edit':False, 'req':True, 'type': 'dbkey'},
            { 'label': _('DisplayName'), 'key': 'DisplayName', 'id': 'displayname', 'info':True, 'edit': True, 'req':True, 'type': 'string'},
            { 'label': _('Base Amount'), 'key': 'BaseAmount', 'id': 'baseamount', 'info':True, 'edit': True, 'req':True, 'canzero':True,
             'type': 'cost', 'recMap':['BaseAmount', 'BaseAmountCurCode', 'BaseAmountYear']},
            { 'label': _('Must Be Overnight'), 'key': 'MustBeOvernight',
             'id': 'mustbeovernight', 'info':True, 'edit':True, 'req':False, 'type': 'bool'},
            { 'label': _('Count First Day'), 'key': 'CountFirstDay',
             'id': 'countfirstday', 'info':True, 'edit': True, 'req':False, 'type': 'bool'},
            { 'label': _('Minimum Km from Home'), 'key': 'MinKmHome', 'id': 'minkmhome',
             'info':True, 'edit': True, 'req':False, 'type': 'float'},
            { 'label': _('Notes'), 'key': 'Notes', 'id': 'notes', 'info':True, 'edit':True, 'req':False, 'type': 'stringbox'},
            { 'label': _('SortOrder'), 'key': 'SortOrder', 'id': 'sortorder',
             'info':False, 'edit':False, 'req':False, 'type': 'int'},
            ]


@bottle.route('/perdiem-top')
def perDiemTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path, _("Per Diems")))
    return bottle.template("perdiem_top.tpl", {"breadcrumbPairs": crumbTrack}, pagehelptag="database")

@bottle.route('/perdiem-edit')
def perDiemEditPage(db, uiSession):
    return typehooks.typeEditPage(db,uiSession,'perdiems')

@bottle.route('/edit/edit-perdiem.json', method='POST')
def editPerDiem(db, uiSession):
    return typehooks.typeEditPage(db,uiSession,'perdiems')

@bottle.route('/json/manage-perdiem-table')
def jsonManagePerDiemTable(db, uiSession):
    modelId = int(bottle.request.params['modelId'])
    try:
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d' % modelId)
    tList = typehelper.getTypeList(db, modelId, 'perdiems')
    nPages, thisPageNum, totRecs, tList = orderAndChopPage(tList,
                                                           {'name': 'Name', 'usedin': 'modelId',
                                                            'dispnm': 'DisplayName'},
                                                           bottle.request)
    result = {"total": nPages,  # total pages
              "page": thisPageNum,  # which page is this
              "records": totRecs,  # total records
              "rows": [{"name": t['Name'],
                        "cell":[t['Name'], t['_inmodel'], t['DisplayName'], t['Name']]}
                       for t in tList]
              }
    return result

def jsonPerDiemEditFn(attrRec, m):
    return attrRec

@bottle.route('/json/perdiem-edit-verify-commit')
def jsonPerDiemEditVerifyCommit(db, uiSession):
    return typehooks.jsonTypeEditVerifyAndCommit(db,uiSession,'perdiems',fieldMap,jsonPerDiemEditFn)


@bottle.route('/json/perdiem-info')
def jsonPerDiemInfo(db, uiSession):
    return typehooks.jsonTypeInfo(db,uiSession,htmlgenerator.getPerDiemInfoHTML)



@bottle.route('/json/perdiem-edit-form')
def jsonPerDiemEditForm(db, uiSession):
    return typehooks.jsonTypeEditForm(db, uiSession, 'perdiems', fieldMap)

@bottle.route('/json/manage-perdiems-explorer',method='POST')
def jsonManagePeopleExplorerTable(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        searchTerm = _safeGetReqParam(bottle.request.params, 'searchterm', default=None)
        #searchTerm = u"{0}".format(searchTermStr)
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException(_('Current User does not have access to model with Id = {0}: from json/manaage-perdiem-explorer'.format(modelId)))
    except ValueError, e:
        print 'Empty parameters supplied to manage-perdiem-explorer'
        print str(e)
        return {'success': 'false'}
    try:
        tList = typehelper.getTypeList(db,modelId,'perdiems')
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
                print "SERACH: {0}".format(row)
                ## does this match name, manufacturer...
                for v in row.values():
                    if v.lower().find(searchTerm.lower()) > -1:
                        rows.append(row)
                        break
            else:
                print row
                rows.append(row)
            
        return {'success':True,
                'total':1,
                'page':1,
                'records':len(rows),
                'rows':rows
                }
    except Exception,e:
        return {'success':False,'msg':'manage-perdiem-explorer: {0}'.format(str(e))}
    