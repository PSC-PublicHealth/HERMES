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
import constants as C

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
        
@bottle.route('/level_removal_experiment')
def levelRemExptPage(db,uiSession):
    crumbTrack = addCrumb(uiSession, _("Remove Level Experiment"))
    try:
        modelId = _getOrThrowError(bottle.request.params, "modelId", isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = m.name
        return bottle.template('level_removal_experiment.tpl',
                               {'modelId':modelId,
                                'name':name,
                                'breadcrumbPairs':crumbTrack})
    except Exception,e:
        _logStacktrace()
        return bottle.template("problem.tpl", {"comment": str(e),  
                                               "breadcrumbPairs":crumbTrack})   
        
@bottle.route('/add_storage_experiment')
def addStorageExptPage(db,uiSession):
    crumbTrack = addCrumb(uiSession, _("Add/Modify Storage By Level Experiment"))
    try:
        modelId = _getOrThrowError(bottle.request.params, "modelId", isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = m.name
        return bottle.template('add_modify_storage_experiment.tpl',
                               {'modelId':modelId,
                                'name':name,
                                'breadcrumbPairs':crumbTrack})
    except Exception,e:
        _logStacktrace()
        return bottle.template("problem.tpl", {"comment": str(e),  
                                               "breadcrumbPairs":crumbTrack})   
        

@bottle.route('/json/add_storage_summary')
def addStorageExptSummary(db,uiSession):
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
        exptDataJson = _getOrThrowError(bottle.request.params,'data')
        
        exptData = json.loads(exptDataJson)
        dList = typehelper.getTypeList(db,modelId,'fridges',fallback=False)
        daList = typehelper.getTypeList(db,1,'fridges',fallback=False)
        #print "{0}".format(daList)
        #print "exptData option = {0}".format(exptData['option'])
        htmlArray = []
        htmlArray.append("<div class='hermes_expt_summary_table_div'>")
        htmlArray.append( "<table class='hermes_expt_summary_table'>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_lead_row'>")
        htmlArray.append( "<td colspan=3 class='hermes_expt_summary_table_lead_col'>")
        if exptData['option'] == 'addstorexpt_replace':
            htmlArray.append(_('You have chosen to replace all of the storage in the <span style="font-weight:bold;">{0} supply chain level with:'.format(exptData['level'])))
        elif exptData['option'] == 'addstorexpt_addition':
            htmlArray.append(_('You have chosen to add storage devices to all locations in the <span style="font-weight:bold;">{0} supply chain level with:'.format(exptData['level'])))
        elif exptData['option'] == 'addstorextp_swap':
            htmlArray.append(_('You have chosen to swap storage devices at all location in the <span style="font-weight:bold;">{0} supply chain level: '.format(exptData['level'])))
        htmlArray.append( _(' '))
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        if exptData['option'] in ['addstorexpt_replace','addstorexpt_addition']:
            for d in exptData['addDevices']:
                htmlArray.append("<tr class='hermes_expt_summary_table_row'>")
                htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
                htmlArray.append("<td class='hermes_expt_summary_table_col'>")
                if d in exptData['deviceCounts'].keys():
                    if int(exptData['deviceCounts'][d]) > 1:
                        dev = [x for x in dList if x['Name']==d]
                        htmlArray.append("{0} {1}s".format(exptData['deviceCounts'][d],dev[0]['DisplayName']))
                    else:
                        dev = [x for x in dList if x['Name']==d]
                        htmlArray.append("{0} {1}".format(exptData['deviceCounts'][d],dev[0]['DisplayName']))
                    
                else:
                    dev = [x for x in dList if x['Name']==d]
                    htmlArray.append("1 {0}".format(dev[0]['DisplayName']))
                
                htmlArray.append("</td>")
                htmlArray.append("</tr>")
        else:
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>");
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            fromD = [x for x in dList if x['Name']==exptData['fromDevice'][0]]
            #print "FromD= {0}".format(fromD)
            #print "{0}".format(exptData['toDevice'])
            toD = [x for x in daList if x['Name']==exptData['toDevice'][0]]
            #print "HERE: {0}".format(toD)
            htmlArray.append(_("Replace: {0}".format(fromD[0]['DisplayName'])))
            htmlArray.append("</td></tr>")
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>");
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append("With: {0}".format(toD[0]['DisplayName']))
            htmlArray.append("</td></tr>")
                             
        htmlArray.append( "</table>")
        htmlArray.append("</div>")
#        print "htmlString = {0}".format(htmlString)
#        print "htmlJson = {0}".format(json.dumps(htmlString))
        # New vaccines Grid Data
        return {'success':True,'html':"\n".join(htmlArray)} 
         
    except Exception,e:
        return {'success':False,'msg':str(e)}   

@bottle.route('/json/level_removal_summary')
def levelRemovalExptSummary(db,uiSession):
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        exptDataJson = _getOrThrowError(bottle.request.params,'data')
        
        exptData = json.loads(exptDataJson)
        
        htmlArray = []
        htmlArray.append("<div class='hermes_expt_summary_table_div'>")
        htmlArray.append( "<table class='hermes_expt_summary_table'>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_lead_row'>")
        htmlArray.append( "<td colspan=3 class='hermes_expt_summary_table_lead_col'>")
        htmlArray.append(_('You have chosen to create a new system with the <span style="font-weight:bold;">{0}</span> supply chain level removed and replace the existing routes '.format(exptData['level'])))
        if exptData['option'] == 'remlevexpt_fromabove':
            htmlArray.append(_(' with routes that currently originate at the supplier.'))
            htmlArray.append("</td></tr>")
        elif exptData['option'] == 'remlevexpt_frombelow':
            htmlArray.append(_(' with routes that currently originate at the clients.'))
            htmlArray.append("</td></tr>")
        elif exptData['option'] == 'remlevexpt_custom':
            routeTypeText = "It is a route"
            originationText = "Starting in Kansas"
            frequencyText = "frequency is groovy, man"
            freqNumText = "hello"
            timeString = ""
            tList = typehelper.getTypeList(db,modelId,'trucks',fallback=False)
            newRouteData = exptData['newRoute']
            if newRouteData['routeType'] in ['varpush',"schedvarfetch"]:
                routeTypeText = _("Fixed Shipping Schedule / Variable Amount Ordered Based on Frequency")
                frequencyText = "With a Fixed Shipping Frequency of"
                timeString = newRouteData['shipInterval']
            elif newRouteData['routeType'] in ["push","schedfetch"]:
                routeTypeText = _("Fixed Shipping Schedule / Fixed Amount Delivered")
                frequencyText = "With a Fixed Shipping Frequency of"
                timeString = newRouteData['shipInterval']
            elif newRouteData['routeType'] in ['pull','demandfetch']:
                routeTypeText = _("Variable Schedule and Amount Ordered (As Needed with Minimum Wait Time Between Shipments, When Stock Falls Below Threshold)")
                frequencyText = "With a Frequency of Up to"
                timeString = newRouteData['pullInterval']
            
            if newRouteData['routeType'] in ['varpush','push','pull']:
                orignationText = _("With Transportation Vehicles Residing and Originating at the Supplier")
            else:
                orginationText = _("With Transportation Vehicles Residing and Originating at the Clients")
            timeSplit = timeString.split(':')
            freqNumText = "{0} {1}{2}".format(timeSplit[0],C.timeUnitToString[timeSplit[1]],"s" if float(timeSplit[0]) > 1 else "")
            print "HERE"
            htmlArray.append(_(' with newly created routes with the following characteristics:'))
            htmlArray.append("</td></tr>")
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>");
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append(_('Route Policy'))
            htmlArray.append("</td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append(routeTypeText)
            htmlArray.append("</td></tr>")
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>");
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append(_('Route Direction'))
            htmlArray.append("</td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append(originationText)
            htmlArray.append("</td></tr>")
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>");
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append(frequencyText)
            htmlArray.append("</td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append(freqNumText)
            htmlArray.append("</td></tr>")
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>");
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append(_('With the Transportation Mode of'))
            htmlArray.append("</td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            trck = [x for x in tList if x['Name']==newRouteData['truckType']]
            print "TRC = {0}".format(trck)
            htmlArray.append(trck[0]['DisplayName'])
            htmlArray.append("</td></tr>")
            
        htmlArray.append( "</table>")
        htmlArray.append("</div>")
#        print "htmlString = {0}".format(htmlString)
#        print "htmlJson = {0}".format(json.dumps(htmlString))
        # New vaccines Grid Data
        return {'success':True,'html':"\n".join(htmlArray)} 
         
    except Exception,e:
        return {'success':False,'msg':str(e)}   
                     
            
                
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
        htmlArray = []
        htmlArray.append("<div class='hermes_expt_summary_table_div'>")
        htmlArray.append( "<table class='hermes_expt_summary_table'>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_lead_row'>")
        htmlArray.append( "<td colspan=4 class='hermes_expt_summary_table_lead_col'>")
        htmlArray.append( _('The vaccine introduction experiment that you have specified includes adding these vaccines: '))
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        tList = typehelper.getTypeList(db,modelId,'vaccines',fallback=False)
        pList = typehelper.getTypeList(db,modelId,'people',fallback=False)
        
        for v in vacDoses:
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>")
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td colspan=3 class='hermes_expt_summary_table_col'>")
            htmlArray.append("{0}".format(v['vName']))
            htmlArray.append( "</td>")
            htmlArray.append( "</tr>")
            htmlArray.append( "<tr class='hermes_expt_summary_table_row'>")
            htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append( "<td colspan=2 class='hermes_expt_summary_table_col'>")
            ### Order this!!!!!!
            htmlArray.append( _("With a Dosage Schedule of: "))
            htmlArray.append( "</td>")
            htmlArray.append( "</tr>")
            for k,c in v.items():
                if k != 'vId' and k != 'vName':
                    if int(c) > 0:
                        htmlArray.append( "<tr class='hermes_expt_summary_table_row'>")
                        htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
                        htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
                        htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
                        htmlArray.append( "<td class='hermes_expt_summary_table_col'>")
                        p = [x for x in pList if x['Name'] == k]
                        doseString = "Dose"
                        if int(c) > 1:
                            doseString = "Doses"
                        htmlArray.append( "{0} {1} to {2}".format(c,doseString,p[0]['DisplayName']))
                        htmlArray.append( "</td>")
                        htmlArray.append( "</tr>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_placeholder_row'><td colspan=4></td></tr>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_sub_row'>")
        htmlArray.append( "<td class='hermes_expt_summary_table_sub_col' colspan=4>")
        htmlArray.append( _("If you would like to continue to edit the experiment, here are a few options: "))
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        htmlArray.append( "<tr class='hermes_expt_summary_table_row'>")
        htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
        htmlArray.append( "<td class='hermes_expt_summary_table_col' colspan=3>")
        htmlArray.append( "<a href='{0}model-add-types?modelId={1}&startClass=vaccines'>".format(rootPath,modelId))
        htmlArray.append( _("Add New Types of Vaccines to the Model "))
        htmlArray.append( "</a>")
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        htmlArray.append( "<tr class='hermes_expt_summary_table_row'>")
        htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
        htmlArray.append( "<td class='hermes_expt_summary_table_col' colspan=3>")
        htmlArray.append( "<a href='{0}model-add-types?modelId={1}&startClass=people'>".format(rootPath,modelId))
        htmlArray.append( _("Add New Types of People to the Model "))
        htmlArray.append( "</a>")
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        htmlArray.append( "<tr class='hermes_expt_summary_table_row'>")
        htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
        htmlArray.append( "<td class='hermes_expt_summary_table_col' colspan=3>")
        htmlArray.append( "<a href='{0}model-edit-population-tabular?modelId={1}'>".format(rootPath,modelId))
        htmlArray.append( _("Update the Number of People Served by Each Supply Chain Location"))
        htmlArray.append( "</a>")
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        htmlArray.append( "<tr class='hermes_expt_summary_table_row'>")
        htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
        htmlArray.append( "<td class='hermes_expt_summary_table_col' colspan=3>")
        htmlArray.append( "<a href='{0}demand-top?modelId={1}'>".format(rootPath,modelId))
        htmlArray.append( _("Edit the Vaccine Dose Schedule"))
        htmlArray.append( "</a>")
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        htmlArray.append( "<tr class='hermes_expt_summary_table_placeholder_row'><td colspan=4></td></tr>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_sub_row'>")
        htmlArray.append( "<td class='hermes_expt_summary_table_sub_col' colspan=4>")
        htmlArray.append( _("Or if you are finished creating this experiment "))
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        htmlArray.append( "<tr class='hermes_expt_summary_table_row'>")
        htmlArray.append( "<td class='hermes_expt_summary_table_placeholder_col'></td>")
        htmlArray.append( "<td class='hermes_expt_summary_table_col' colspan=3>")
        htmlArray.append( "<a href='{0}model-run?modelId={1}'>".format(rootPath,modelId))
        htmlArray.append( _("Run Simulations of this Model"))
        htmlArray.append( "</a>")
        htmlArray.append( "</td>")
        htmlArray.append( "</tr>")
        
        htmlArray.append( "</table>")
        htmlArray.append("</div>")
#        print "htmlString = {0}".format(htmlString)
#        print "htmlJson = {0}".format(json.dumps(htmlString))
        # New vaccines Grid Data
        return {'success':True,'html':"\n".join(htmlArray)} 
         
    except Exception,e:
        return {'success':False,'msg':str(e)}      
         
        
        
         