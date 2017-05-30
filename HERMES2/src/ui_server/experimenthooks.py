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
from serverconfig import rootPath

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
        
@bottle.route('/json/vaccine_introduction_summary')
def addAVaccineExptSummary(db,uiSession):
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
        print "Model Id = {0}".format(modelId)
        #vacDataJson= _getOrThrowError(bottle.request.params,'newvaccjson')
        #print "vaccData = {0}".format(vacDataJson)
        vacDoseJson = _getOrThrowError(bottle.request.params,'newvaccdosejson')
        
        #newTypes = json.loads(vacDataJson)
        vacDoses = json.loads(vacDoseJson)
        for p in vacDoses:
            for k,v in p.items():
                print "p = {0},{1}".format(k,v)
        htmlString = "<div class='hermes_expt_summary_table_div'>"
        htmlString += "<table class='hermes_expt_summary_table'>"
        htmlString += "<tr class='hermes_expt_summary_table_lead_row'>"
        htmlString += "<td colspan=4 class='hermes_expt_summary_table_lead_col'>"
        htmlString += _('The vaccine introduction experiment that you have specified includes adding these vaccines: ')
        htmlString += "</td>"
        htmlString += "</tr>"
        
        tList = typehelper.getTypeList(db,modelId,'vaccines',fallback=False)
        pList = typehelper.getTypeList(db,modelId,'people',fallback=False)
        
        for v in vacDoses:
        #for v in
            #if v['Name'] in newTypes:
                
#                 vDG = None
#                 for vD in vacDoses:
#                     if vD['vId'] == v['Name']:
#                         vDG = vD
#                         break
#                 if vDG is None:
#                     raise RuntimeError(_("in vaccine_introduction_summary: No doses schedule for vaccine {0}".format(v['Name'])))
                
            htmlString +="<tr class='hermes_expt_summary_table_row'>"
            htmlString +="<td class='hermes_expt_summary_table_placeholder_col'></td>"
            htmlString +="<td colspan=3 class='hermes_expt_summary_table_col'>"
            htmlString +="{0}".format(v['vName'])
            htmlString += "</td>"
            htmlString += "</tr>"
            htmlString += "<tr class='hermes_expt_summary_table_row'>"
            htmlString += "<td class='hermes_expt_summary_table_placeholder_col'></td>"
            htmlString += "<td class='hermes_expt_summary_table_placeholder_col'></td>"
            htmlString += "<td colspan=2 class='hermes_expt_summary_table_col'>"
            ### Order this!!!!!!
            htmlString += _("With a Dosage Schedule of: ")
            htmlString += "</td>"
            htmlString += "</tr>"
            for k,c in v.items():
                if k != 'vId' and k != 'vName':
                    if int(c) > 0:
                        htmlString += "<tr class='hermes_expt_summary_table_row'>"
                        htmlString += "<td class='hermes_expt_summary_table_placeholder_col'></td>"
                        htmlString += "<td class='hermes_expt_summary_table_placeholder_col'></td>"
                        htmlString += "<td class='hermes_expt_summary_table_placeholder_col'></td>"
                        htmlString += "<td class='hermes_expt_summary_table_col'>"
                        p = [x for x in pList if x['Name'] == k]
                        doseString = "Dose"
                        if int(c) > 1:
                            doseString = "Doses"
                        htmlString += "{0} {1} to {2}".format(c,doseString,p[0]['DisplayName'])
                        htmlString += "</td>"
                        htmlString += "</tr>"
        htmlString += "<tr class='hermes_expt_summary_table_placeholder_row'><td colspan=4></td></tr>"
        htmlString += "<tr class='hermes_expt_summary_table_sub_row'>"
        htmlString += "<td class='hermes_expt_summary_table_sub_col' colspan=4>"
        htmlString += _("If you would like to continue to edit the experiment, here are a few options: ")
        htmlString += "</td>"
        htmlString += "</tr>"
        
        htmlString += "<tr class='hermes_expt_summary_table_row'>"
        htmlString += "<td class='hermes_expt_summary_table_placeholder_col'></td>"
        htmlString += "<td class='hermes_expt_summary_table_col' colspan=3>"
        htmlString += "<a href='{0}model-add-types?modelId={1}'>".format(rootPath,modelId)
        htmlString += _("Add New Types of Vaccines and Populations to the Model ")
        htmlString += "</a>"
        htmlString += "</td>"
        htmlString += "</tr>"
        
        htmlString += "<tr class='hermes_expt_summary_table_row'>"
        htmlString += "<td class='hermes_expt_summary_table_placeholder_col'></td>"
        htmlString += "<td class='hermes_expt_summary_table_col' colspan=3>"
        htmlString += "<a href='{0}model-edit-population-tabular?modelId={1}'>".format(rootPath,modelId)
        htmlString += _("Update the Number of People Served by Each Supply Chain Location")
        htmlString += "</a>"
        htmlString += "</td>"
        htmlString += "</tr>"
        
        htmlString += "<tr class='hermes_expt_summary_table_row'>"
        htmlString += "<td class='hermes_expt_summary_table_placeholder_col'></td>"
        htmlString += "<td class='hermes_expt_summary_table_col' colspan=3>"
        htmlString += "<a href='{0}demand-top?modelId={1}'>".format(rootPath,modelId)
        htmlString += _("Edit the Vaccine Dose Schedule ")
        htmlString += "</a>"
        htmlString += "</td>"
        htmlString += "</tr>"
        
        htmlString += "</table>"
        print "htmlString = {0}".format(htmlString)
        print "htmlJson = {0}".format(json.dumps(htmlString))
        # New vaccines Grid Data
        return {'success':True,'html':htmlString} 
         
    except Exception,e:
        return {'success':False,'msg':str(e)}      
         
        
        
         