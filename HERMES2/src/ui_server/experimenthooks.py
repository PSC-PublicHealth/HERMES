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
_hermes_svn_id_="$Id: experimenthooks.py 2262 2015-02-09 14:38:25Z stbrown $"

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
from modelhooks import addCrumb

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults,\
    _safeGetReqParam
from util import listify
 
inlizer=session_support.inlizer
_=session_support.translateString

@bottle.route('/experiment-top')
def openExperimentTopPage(db,uiSession):
    crumbTrack = addCrumb(uiSession,_("Create an Experiment"))
    try:
        modelId = _getOrThrowError(bottle.request.params, "modelId", isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = m.name
        
        return bottle.template('experiment_top.tpl',
                               {'modelId':modelId,
                                'modelName':name,
                                'breadcrumbPairs':crumbTrack})
    except Exception,e:
        _logStacktrace()
        return bottle.template("problem.tpl", {"comment": str(e),  
                                               "breadcrumbPairs":crumbTrack})   
        
@bottle.route('/vaccine_introduction_experiment')
def addAVaccineExptPage(db,uiSession):
    crumbTrack = addCrumb(uiSession, _("Vaccine Introduction Experiment"))
    try:
        modelId = _getOrThrowError(bottle.request.params, "modelId", isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = m.name
        return bottle.template('vaccine_introduction_experiment.tpl',
                               {'modelId':modelId,
                                'name':name,
                                'breadcrumbPairs':crumbTrack})
    except Exception,e:
        _logStacktrace()
        return bottle.template("problem.tpl", {"comment": str(e),  
                                               "breadcrumbPairs":crumbTrack})   
        

