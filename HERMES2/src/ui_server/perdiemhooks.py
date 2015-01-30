#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_ = "$Id$"

import bottle
import ipath
import shadow_network_db_api
import shadow_network
import session_support_wrapper as session_support
from gridtools import orderAndChopPage
import privs
import htmlgenerator
import typehelper

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, \
    _mergeFormResults

inlizer = session_support.inlizer
_ = session_support.translateString

fieldMap = [{'row': 1, 'label': _('Name'), 'key': 'Name', 'id': 'name', 'type': 'string'},
            {'row': 1, 'label': _('DisplayName'), 'key': 'DisplayName',
             'id': 'displayname', 'type': 'string'},
            {'row': 2, 'label': _('Base Amount'), 'key': 'BaseAmount',
             'id': 'baseamount', 'type': 'price'},
            {'row': 2, 'label': _('Amount Units'), 'key': 'BaseAmountCur', 'id': 'baseamountcur',
             'type': 'currency'},
            {'row': 2, 'label': _('Amount Year'), 'key': 'BaseAmountYear',
             'id': 'baseamountyear', 'type': 'int'},
            {'row': 3, 'label': _('Must Be Overnight'), 'key': 'MustBeOvernight',
             'id': 'mustbeovernight', 'type': 'bool'},
            {'row': 3, 'label': _('Count First Day'), 'key': 'CountFirstDay',
             'id': 'countfirstday', 'type': 'bool'},
            {'row': 3, 'label': _('Minimum Km from Home'), 'key': 'MinKmHome', 'id': 'minkmhome',
             'type': 'float'},
            {'row': 4, 'label': _('Notes'), 'key': 'Notes', 'id': 'notes', 'type': 'string'},
            {'row': 4, 'label': _('SortOrder'), 'key': 'SortOrder', 'id': 'sortorder',
             'type': 'int'},
            ]


@bottle.route('/perdiem-top')
def perDiemTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path, _("PerDiems")))
    return bottle.template("perdiem_top.tpl", {"breadcrumbPairs": crumbTrack})


@bottle.route('/perdiem-edit')
def perDiemEditPage(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        protoName = _getOrThrowError(bottle.request.params, 'protoname')
        protoName = _smartStrip(protoName)
        crumbTracks = uiSession.getCrumbs().push((bottle.request.path,
                                                  _("Create Modified Version")))
        return bottle.template("perdiem_edit.tpl", {"breadcrumbPairs": crumbTracks,
                               "protoname": protoName, "modelId": modelId})
    except Exception, e:
        _logMessage(str(e))
        _logStacktrace()
        return bottle.template("error.tpl", {"breadcrumbPairs": uiSession.getCrumbs(),
                               "bugtext": str(e)})


@bottle.route('/edit/edit-perdiem.json', method='POST')
def editPerDiem(db, uiSession):
    if bottle.request.params['oper'] == 'edit':
        if 'modelId' not in bottle.request.params.keys():
            return {}
        modelId = int(bottle.request.params['modelId'])
        _logMessage("editing modelId: %d" % modelId)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        name = bottle.request.params['name']
        _logMessage("changed name")
        pT = m.perdiems[name]
        if 'dispnm' in bottle.request.params:
            _logMessage("Changing Display Name")
            pT.DisplayName = bottle.request.params['dispnm']
            _logMessage("Changed DisplayName")
        return {}
    elif bottle.request.params['oper'] == 'add':
        raise bottle.BottleException(_('unsupported operation'))
    elif bottle.request.params['oper'] == 'del':
        raise bottle.BottleException(_('unsupported operation'))


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
    result = {"total": nPages,    # total pages
              "page": thisPageNum,     # which page is this
              "records": totRecs,  # total records
              "rows": [{"name": t['Name'],
                        "cell":[t['Name'], t['_inmodel'], t['DisplayName'], t['Name']]}
                       for t in tList]
              }
    return result


@bottle.route('/json/perdiem-edit-verify-commit')
def jsonPerDiemEditVerifyCommit(db, uiSession):
    m, attrRec, badParms, badStr = _mergeFormResults(bottle.request,  # @UnusedVariable
                                                     db, uiSession, fieldMap)
    if badStr and badStr != "":
        result = {'success': True, 'value': False, 'msg': badStr}
    else:
        newPerDiem = shadow_network.ShdPerDiemType(attrRec.copy())
        db.add(newPerDiem)
        m.types[attrRec['Name']] = newPerDiem
        crumbTrack = uiSession.getCrumbs()
        result = {'success': True, 'value': True, 'goto': crumbTrack.getDoneURL()}
    return result


@bottle.route('/json/perdiem-info')
def jsonPerDiemInfo(db, uiSession):
    try:
        modelId = int(bottle.request.params['modelId'])
        name = bottle.request.params['name']
        htmlStr, titleStr = htmlgenerator.getPerDiemInfoHTML(db, uiSession, modelId, name)
        result = {'success': True, "htmlstring": htmlStr, "title": titleStr}
        return result
    except Exception, e:
        result = {'success': False, 'msg': str(e)}
        return result


@bottle.route('/json/perdiem-edit-form')
def jsonPerDiemEditForm(db, uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        protoname = _getOrThrowError(bottle.request.params, 'protoname')
        proposedName = typehelper.getSuggestedName(db, modelId, "perdiems", protoname,
                                                   excludeATM=True)
        canWrite, typeInstance = typehelper.getTypeWithFallback(db, modelId,  # @UnusedVariable
                                                                protoname)
        attrRec = {}
        shadow_network._copyAttrsToRec(attrRec, typeInstance)
        elabMap = typehelper.elaborateFieldMap(proposedName, attrRec, fieldMap)
        htmlStr, titleStr = htmlgenerator.getTypeEditHTML(db, uiSession, "perdiems",
                                                          modelId, protoname, elabMap)
        result = {'success': True, "htmlstring": htmlStr, "title": titleStr}
    except privs.PrivilegeException:
        result = {'success': False, 'msg': _('User cannot read this model')}
    except Exception, e:
        _logMessage(str(e))
        _logStacktrace()
        result = {'success': False, 'msg': str(e)}
    return result
