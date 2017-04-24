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

_hermes_svn_id_ = "$Id$"

import types
import bottle
import ipath
import shadow_network_db_api
import shadow_network
import session_support_wrapper as session_support

from widgethooks import getTypeFromRequest, getEnergyFromRequest, getFuelFromRequest, \
    getCurrencyFromRequest

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _safeGetReqParam


inlizer = session_support.inlizer
_ = session_support.translateString

@bottle.route('/factory-top')
def factoryTopPage(db, uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path, _("Factory")))
    return bottle.template("factory_top.tpl", {"breadcrumbPairs": crumbTrack,
                                               "title_slogan": _("Factory"), })

class InvalidFactory(Exception):
    pass
 
@bottle.route('/json/get-factory-data')
def jsonGetFactoryData(db, uiSession):
    ret = {'success': True}
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayReadModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)
        factories = m.factories

        ret['factoryCount'] = len(factories)
        ret['editable'] = True
        
        # make sure we can display this factory
        if len(factories) > 1:
            raise InvalidFactory("Too many factories")
        if len(factories) == 1:
            f = factories.values()[0]
            if f.DemandType not in ("projection", "expectation"):
                raise InvalidFactory("unknown demand type")
            ret['factoryCount'] = 1
            ret['intervalDays'] = f.ProductionIntervalDays
            ret['latency'] = f.StartupLatencyDays
            ret['overstock'] = f.OverstockScale * 100.0
            ret['demandType'] = f.DemandType

    except InvalidFactory, e:
        ret['msg'] = str(e)
        ret['editable'] = False
        
    except Exception, e:
        _logStacktrace()
        ret['success'] = False
        ret['msg'] = str(e)
        ret['editable'] = False
    return ret

        
@bottle.route('/json/set-factory-data')
def jsonSetFactoryData(db, uiSession):
    ret = {'success': True}
    try:
        modelId = _getOrThrowError(bottle.request.params, 'modelId', isInt=True)
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        m = shadow_network_db_api.ShdNetworkDB(db, modelId)

        factoryCount = _getOrThrowError(bottle.request.params, 'factoryCount', isInt=True)
        if factoryCount == 0:
            m.factories = {}
        elif factoryCount == 1:
            m.factories = {}
            fdict = {'idcode': 1,
                     'Name': "factory",
                     'Vaccines': "All" }
            fdict['Targets'] = str(m.trunkStore().idcode)
            fdict['ProductionIntervalDays'] = _getOrThrowError(bottle.request.params, 'intervalDays', isFloat=True)
            fdict['StartupLatencyDays'] = _getOrThrowError(bottle.request.params, 'latency', isFloat=True)
            fdict['OverstockScale'] = _getOrThrowError(bottle.request.params, 'overstock', isFloat=True) / 100.0
            fdict['DemandType'] = _getOrThrowError(bottle.request.params, 'demandType')
            m.addFactory(fdict)
    
        return {"success":True}
    except Exception, e:
        _logStacktrace()
        return {'success': False, 'msg': str(e)}


