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
from transformation import setLatenciesByNetworkPosition,setUseVialLatenciesAsOffsetOfShipLatencyFromRoute

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
        

@bottle.route('/json/add_storage_experiment_implement')
def addStorageExptImplement(db,uiSession):
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
        exptDataJson = _getOrThrowError(bottle.request.params,'data')
        
        exptData = json.loads(exptDataJson)
        
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        levelToModify = exptData['level']
        option = exptData['option']
        #print "HETER!!!!"
        #print option
        if option == "addstorexpt_addition":
            addDevice = exptData['addDevices']
            deviceCounts = exptData['deviceCounts']
            for storeId,store in m.stores.items():
                if store.CATEGORY == levelToModify and not store.isAttached() and not store.isSurrogate():
                    for dev in addDevice:
                        curCount = store.countInventory(dev)
#                        print "curCount = {0}".format(curCount)
#                        print "deviceCounts = {0}".format(deviceCounts)
                        store.updateInventory(dev,int(curCount) + int(deviceCounts[dev]))
        
        elif option == "addstorexpt_replace":
            addDevice = exptData['addDevices']
            deviceCounts = exptData['deviceCounts']
            
            for storeId,store in m.stores.items():
                if store.CATEGORY == levelToModify and not store.isAttached() and not store.isSurrogate():
                    store.clearStorage()
                    for dev in addDevice:
                        store.updateInventory(dev,int(deviceCounts[dev]))
        
        elif option == "addstorexpt_swap":
            fromDev = exptData['fromDevice']
            print "FRom Dev = {0}".format(fromDev)
            toDev = exptData['toDevice']
            print "to Dev = {0}".format(toDev)
            
            #sList = typehelper.getTypeList(db,modelId,'fridges',fallback=False)
            typehelper.addTypeToModel(db,m,toDev,shadow_network_db_api.ShdNetworkDB(db,1),True,ignore=True)
            for storeId,store in m.stores.items():
                if store.CATEGORY == levelToModify and not store.isAttached() and not store.isSurrogate():
                    fromCount = store.countInventory(fromDev)
                    print "from = {0}".format(fromCount)
                    if fromCount > 0:
                        store.updateInventory(fromDev,0)
                        store.updateInventory(toDev,fromCount)

        db.commit()
        return {'success':True}
    
    except Exception,e:
        return {'success':False,'msg':str(e)}     

@bottle.route('/json/route_by_level_experiment_implement')
def modifyRouteExptImplement(db,uiSession):
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
        exptDataJson = _getOrThrowError(bottle.request.params,'data')
        
        exptData = json.loads(exptDataJson)
        
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        levelOpt = exptData['levelOpt']
        
        changeFreq = exptData['changeFreq']
        changeVehicle = exptData['changeVehicle']
        
        routesToChange = []
        
        if levelOpt == "modrouteexpt_level_between":
            levelBetween = exptData['levelBetween']
            if levelBetween[:4] == "loop":
                fromLevel = levelBetween.split("_")[1]
                toLevels = levelBetween.split("_")[2:]
                
                for routeId,route in m.routes.items():
                    stopCats = []
                    if len(route.stops) > 2 and route.Type != "attached":
                        if route.stops[0].store.CATEGORY == fromLevel:
                            for stop in route.stops[1:]:
                                stopCats.append(stop.store.CATEGORY)
                    
                    hitCount = 0
                    for l in toLevels:
                        if l in stopCats:
                            hitCount+=1
                            break
                    
                    if hitCount == len(toLevels):
                        routesToChange.append(routeId)
            else:
                fromLevel = levelBetween.split("_")[0]
                toLevel = levelBetween.split("_")[1]
             
                for routeId,route in m.routes.items():
                    if len(route.stops) == 2 and route.Type != "attached":
                        if route.stops[0].store.CATEGORY == fromLevel and route.stops[1].store.CATEGORY == toLevel:
                            routesToChange.append(routeId)
        
        elif levelOpt == "modrouteexpt_level_orig":
            levelOrig = exptData['levelOrig']
            
            for routeId,route in m.routes.items():
                if route.stops[0].store.CATEGORY == levelOrig and route.Type != "attached":
                    routesToChange.append(routeId)
        
        else:
            raise RuntimeError("in route_by_level_experiment_implement, unrecognized levelOpt")
        
        
        ### Now perform the transformation on the selected routes
        
        if changeFreq:
            transDict ={'modrouteexpt_freq_half':0.5,
                        'modrouteexpt_freq_double':2,
                        'modrouteexpt_freq_quadruple':4} 
            
            freqOpt = exptData['freqOpt']
            if freqOpt == "modrouteexpt_freq_needed":
                for routeId in routesToChange:
                    route = m.routes[routeId]
                    routeDesc = shadow_network.ShdRoute.types[route.Type]
                    #print "Route Type = {0}".format(shadow_network.ShdRoute.types[route.Type].isScheduled())
                    if route.Type == "attached":
                        continue
                    
                    if len(route.stops) > 2:
                        pass
                        #route.ShipIntervalDays = 1
                    else:
                        newRouteType = "persistentdemandfetch"
                        if routeDesc.supplierStop == 0:
                            newRouteType = "persistentpull"
                            
                        route.Type = newRouteType
                        for stop in route.stops:
                            stop.PullOrderAmountDays = 1
                        route.ShipIntervalDays = 1
                        
                        
            else:
                factor = float(transDict[freqOpt])
                for routeId in routesToChange:
                    route = m.routes[routeId]
                    routeDesc = shadow_network.ShdRoute.types[route.Type]
                    #if route.Type in ['varpush','schedvarfetch','schedfetch','push','askingpush','dropandcollect']:
                    if routeDesc.isScheduled():
                        route.ShipIntervalDays = int(route.ShipIntervalDays / factor)
                    else:
                        for stop in route.stops:
                            stop.PullOrderAmountDays = (int(stop.PullOrderAmountDays / factor))
        
        print routesToChange  
        if changeVehicle:
            vehicleToChange = exptData['vehicleChange']
            oldTrucks = {}
            for routeId in routesToChange:
                route = m.routes[routeId]
                routeDesc = shadow_network.ShdRoute.types[route.Type]
                
                oldTrucks[routeId] = route.TruckType
                
                route.TruckType = vehicleToChange
                
        ### ok this becomes a little tricky as I don't want to remove a vehicle if it is being used for another route that hasn't changed
            for routeId in routesToChange:
                route = m.routes[routeId]
                store = route.stops[0].store
                needOld = False
                if store.supplierRoute() is not None:
                    if store.supplierRoute().TruckType == oldTrucks[routeId]:
                        needOld = True
                
                if store.clientRoutes is not None:
                    for clientRoute in store.clientRoutes():
                        if clientRoute.TruckType == oldTrucks[routeId]:
                            needOld = True
                
                oldCount = store.countInventory(oldTrucks[routeId])      
                if not needOld:
                    store.updateInventory(oldTrucks[routeId],0)
                
                store.addInventory(vehicleToChange,oldCount)
                
        # Done with transformation, commit
        db.commit() 
              
        return {'success':True,'routes':routesToChange} 
    except Exception,e:
        return {'success':False,'msg':str(e)}             
            
@bottle.route('/route_by_level_experiment')
def modifyRouteExptPage(db,uiSession):
    crumbTrack = addCrumb(uiSession, _("Modify Routes by Level Experiment"))
    try:
        modelId = _getOrThrowError(bottle.request.params, "modelId", isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = m.name
        return bottle.template('route_by_level_experiment.tpl',
                               {'modelId':modelId,
                                'name':name,
                                'breadcrumbPairs':crumbTrack})
    except Exception,e:
        _logStacktrace()
        return bottle.template("problem.tpl", {"comment": str(e),  
                                               "breadcrumbPairs":crumbTrack})   

@bottle.route('/add_loops_experiment')
def addLoopsExptPage(db,uiSession):
    crumbTrack = addCrumb(uiSession, _("Add Transport Loops Experiment"))
    try:
        modelId = _getOrThrowError(bottle.request.params, "modelId", isInt=True)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        name = m.name
        return bottle.template('add_loops_experiment.tpl',
                               {'modelId':modelId,
                                'name':name,
                                'breadcrumbPairs':crumbTrack})
    except Exception,e:
        _logStacktrace()
        return bottle.template("problem.tpl", {"comment": str(e),  
                                               "breadcrumbPairs":crumbTrack})   
        

@bottle.route('/json/add_loops_summary')
def addLoopsSummary(db,uiSession):
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
        exptDataJson = _getOrThrowError(bottle.request.params,'data')
        
        exptData = json.loads(exptDataJson)
        tList = typehelper.getTypeList(db,modelId,'trucks',fallback=False)
        
        htmlArray = []
        htmlArray.append("<div class='hermes_expt_summary_table_div'>")
        htmlArray.append( "<table class='hermes_expt_summary_table'>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_lead_row'>")
        htmlArray.append( "<td colspan=3 class='hermes_expt_summary_table_lead_col'>")
        endValue = ''
        if exptData['levelEnd'] == 'all':
            endValue = _('You have decided to create transport loops starting at the {0} for locations at all of the locations below.'.format(exptData['levelStart']))
        else:
            endValue = _('You have decided to create transport loops starting at the {0} for locations at {1} supply chain level.'.format(exptData['levelStart'],exptData['levelEnd']))
        htmlArray.append(endValue)
        htmlArray.append("</td></tr>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_lead_row'>")
        htmlArray.append( "<td colspan=3 class='hermes_expt_summary_table_lead_col'>")
        htmlArray.append(_('With the following options: '))
        htmlArray.append("</td></tr>")
        
        htmlArray.append("<tr class='hermes_expt_summary_table_row'>")
        htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
        htmlArray.append("<td class='hermes_expt_summary_table_shorter_col'>")
        htmlArray.append(_("The number of locations per transport loop is:"))
        htmlArray.append("</td>")
        htmlArray.append("<td class='hermes_expt_summary_table_col'>")
        htmlArray.append("{0}".format(exptData['maximumLocations']))
        htmlArray.append("</td></tr>")
        
        htmlArray.append("<tr class='hermes_expt_summary_table_row'>")
        htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
        htmlArray.append("<td class='hermes_expt_summary_table_shorter_col'>")
        dev = [x for x in tList if x['Name']==exptData['vehicleToUse']]
        htmlArray.append(_("With the mode of transport:"))
        htmlArray.append("</td>")
        htmlArray.append("<td class='hermes_expt_summary_table_col'>")
        htmlArray.append("{0}".format(dev[0]['DisplayName']))
        htmlArray.append("</td></tr>")
       
        htmlArray.append("</table>")
        htmlArray.append("</div>")

        # New vaccines Grid Data
        return {'success':True,'html':"\n".join(htmlArray)} 
     
    except Exception,e:
        return {'success':False,'msg':str(e)}           
        
        
@bottle.route('/json/route_by_level_summary')
def modifyRouteSummary(db,uiSession):
    try:
        import json
        modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
        exptDataJson = _getOrThrowError(bottle.request.params,'data')
        
        exptData = json.loads(exptDataJson)
        tList = typehelper.getTypeList(db,modelId,'trucks',fallback=False)
        
        htmlArray = []
        htmlArray.append("<div class='hermes_expt_summary_table_div'>")
        htmlArray.append( "<table class='hermes_expt_summary_table'>")
        htmlArray.append( "<tr class='hermes_expt_summary_table_lead_row'>")
        htmlArray.append( "<td colspan=2 class='hermes_expt_summary_table_lead_col'>")
        if exptData['levelOpt'] == 'modrouteexpt_level_orig':
            htmlArray.append(_("You have chosen to modify all of the shipping routes originating at the {0} supply chain level.".format(exptData['levelOrig'])))
        else:
            htmlArray.append(_("You have chosen to modify all of the shipping routes that are {0}".format(exptData['levelBetweenParsed'])))
        
        htmlArray.append("</td>")
        htmlArray.append("</tr>")
        
        htmlArray.append( "<tr class='hermes_expt_summary_table_lead_row'>")
        htmlArray.append( "<td colspan=2 class='hermes_expt_summary_table_lead_col'>")
        if exptData['changeFreq'] and exptData['changeVehicle']:
            htmlArray.append(_('The modifications to be made are: '))
        else:
            htmlArray.append(_('The modification to be made is: '))
        htmlArray.append("</td>")
        htmlArray.append("</tr>")
        
        if exptData['changeFreq']:
            transDict = {'modrouteexpt_freq_half':_('Reduce the frequency of shipping by half.'),
                         'modrouteexpt_freq_double':_('Increasing the frequency of shipping by double.'),
                         'modrouteexpt_freq_quadruple':_('Increasing the frequency of shipping by quadruple'),
                         'modrouteexpt_freq_needed':_('Increasing the frequency of shipping to occur as often as needed to satisfy demand.')}
            
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>")
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append(transDict[exptData['freqOpt']])
            htmlArray.append("</td>")
            htmlArray.append("</tr>")
        
        if exptData['changeVehicle'] and exptData['vehicleChange']:
            dev = [x for x in tList if x['Name']==exptData['vehicleChange']]
            htmlArray.append("<tr class='hermes_expt_summary_table_row'>")
            htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
            htmlArray.append("<td class='hermes_expt_summary_table_col'>")
            htmlArray.append("Changing the transport mode to {0}.".format(dev[0]['DisplayName']))
            htmlArray.append("</td>")
            htmlArray.append("</tr>")
        
        htmlArray.append("</table>")
        htmlArray.append("</div>")

        # New vaccines Grid Data
        return {'success':True,'html':"\n".join(htmlArray)} 
         
    except Exception,e:
        return {'success':False,'msg':str(e)}   
        
            
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
        htmlArray.append("<tr class='hermes_expt_summary_table_row'>")
        htmlArray.append("<td class='hermes_expt_summary_table_placeholder_col'></td>")
        htmlArray.append("<td class='hermes_expt_summary_table_col'>")
        htmlArray.append(_("The following modifications are being made:"))
        htmlArray.append("</td>")
        htmlArray.append("</tr>")
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
            fromD = [x for x in dList if x['Name']==exptData['fromDevice']]
            #print "FromD= {0}".format(fromD)
            #print "{0}".format(exptData['toDevice'])
            toD = [x for x in daList if x['Name']==exptData['toDevice']]
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
                originationText = _("With Transportation Vehicles Residing and Originating at the Supplier")
            else:
                originationText = _("With Transportation Vehicles Residing and Originating at the Clients")
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
         
        
        
@bottle.route('/json/level_removal_experiment_implement')
def levelRemovalExptImplementation(db,uiSession):
        import copy
        
        try:
            import json
            modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
            exptDataJson = _getOrThrowError(bottle.request.params,'data')
            
            exptData = json.loads(exptDataJson)
            
            uiSession.getPrivs().mayReadModelId(db,modelId)
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
            
            levelToRemove = exptData['level']
            routeOption = exptData['option']
            
            storesToRemove = []
            
            warningMessage = ""
            
            ### Gather up the stores that we would like to "remove" from the level
            ### for removing a level, we will only remove locations that are at the head of a loop
            ### so if their supplier route has more than 2 stops, then they will not be included
            ### client routes are fine.
            for storeId, store in m.stores.items():
                if not store.isAttached() and not store.isSurrogate():
                    if store.CATEGORY == levelToRemove:
                        if len(store.supplierRoute().stops) == 2:
                            storesToRemove.append(storeId)
            
            ### Tabulate the stores that we have to check vehicles for
            newSupplierStoresToSetVehicles = set()
            newClientStoresToSetVehicles = set()
            
            for storeId in storesToRemove:
                #if storeId != 109010000:
                #    continue
                print "Removing store = {0}".format(storeId)
                store = m.stores[storeId]
                routeTemplate = None
                routeDesc = None
                oldSupplierRoute = store.supplierRoute()
                
                #print oldSupplierRoute.RouteName
                #### First we will need to move all of the client routes this stores supplier
                #count = 0
                for oldClientRoute in store.clientRoutes():
                    if oldClientRoute.Type == "attached":
                        continue
                    
                    oldClientRouteDesc = shadow_network.ShdRoute.types[oldClientRoute.Type]
                    oldClientStore = oldClientRoute.stops[oldClientRouteDesc.firstClientStop()].store
                    #if oldClientRoute.Type != 'schedvarfetch':
                    #    continue
                    newSupplierStore = store.supplierStore()
                    #newSupplierStores.add(newSupplierStores.idcode)
                    oldSupplierRoute = store.supplierRoute()
                    
                    
                    if routeOption == "remlevexpt_fromabove":
                        routeTemplate = copy.copy(store.supplierRoute())
                        routeDesc = shadow_network.ShdRoute.types[routeTemplate.Type]
                        #routeDesc = shadow_network.ShdRoute.types[routeTemplate.Type]
                        isLoop = len(oldClientRoute.stops) > 2
                    
                        if isLoop and not routeDesc.multiClient():
                            warningMessage = _("There were transport loops involved in the level removal experiment. Given the restrictions on some route policies with transport, HERMES may have had to deviate from your specified input. It is recommended that you confirm in the <a href='{0}model-edit-structure?id={1}'>HERMES Advanced Editor</a> to ensure that the model has been altered to your desire.".format(rootPath,modelId))    
                            routeTemplate = copy.copy(oldClientRoute)
                            routeDesc = shadow_network.ShdRoute.types[routeTemplate.Type]
                        
                        
                        newRouteType = routeTemplate.Type
                        newRouteConditions = routeTemplate.Conditions
                        newRoutePerDiem = routeTemplate.PerDiemType
                        newPUDFreq = routeTemplate.PickupDelayFrequency
                        newPUDSigma = routeTemplate.PickupDelaySigma
                        newPUDMag   = routeTemplate.PickupDelayMagnitude
                        newTruckType = routeTemplate.TruckType
                        newSID = routeTemplate.ShipIntervalDays
                        newSLD = routeTemplate.ShipLatencyDays
                        newPOD = routeTemplate.stops[0].PullOrderAmountDays
                           
                    elif routeOption == "remlevexpt_frombelow":
                        routeTemplate = copy.copy(oldClientRoute)
                        routeDesc = shadow_network.ShdRoute.types[routeTemplate.Type]
                        newRouteType = routeTemplate.Type
                        newRouteConditions = routeTemplate.Conditions
                        newRoutePerDiem = routeTemplate.PerDiemType
                        newPUDFreq = routeTemplate.PickupDelayFrequency
                        newPUDSigma = routeTemplate.PickupDelaySigma
                        newPUDMag   = routeTemplate.PickupDelayMagnitude
                        newTruckType = routeTemplate.TruckType
                        newSID = routeTemplate.ShipIntervalDays
                        newSLD = routeTemplate.ShipLatencyDays
                        newPOD = routeTemplate.stops[0].PullOrderAmountDays
                        
                    elif routeOption == "remlevexpt_custom":
                        newRouteData = exptData['newRoute']
                        routeDesc = shadow_network.ShdRoute.types[newRouteData['routeType']]
                        newRouteType = newRouteData['routeType']
                        SIDTimeString = newRouteData['shipInterval']
                        
                        isLoop = len(oldClientRoute.stops) > 2
                    
#                         print "routeName = {0}".format(oldClientRoute.RouteName)
#                         print "routeType from Custom = {0}".format(newRouteType)
#                         print "can it be multiclient = {0}".format(routeDesc.multiClient()) 
#                         print "oldClientType = {0}".format(oldClientRoute.Type)
#                         print "Is this a loop: {0}".format(isLoop)
                        
                        if isLoop and not routeDesc.multiClient():
                            warningMessage = _("There were transport loops involved in the level removal experiment. Given the restrictions on some route policies with transport, HERMES may have had to deviate from your specified input. It is recommended that you confirm in the <a href='{0}model-edit-structure?id={1}'>HERMES Advanced Editor</a> to ensure that the model has been altered to your desire.".format(rootPath,modelId))    
                            newRouteType = oldClientRoute.Type
                            SIDTimeString = "{0}:D".format(oldClientRoute.ShipIntervalDays)
                            routeDesc = shadow_network.ShdRoute.types[newRouteData['routeType']]
                            
                        
                        newRouteConditions = ''
                        newRoutePerDiem = ''
                        newPUDFreq = 0
                        newPUDSigma = 0
                        newPUDMag   = 0
                        newTruckType = newRouteData['truckType']
                        SIDTime = SIDTimeString.split(':')
                        newSID = float(SIDTime[0])
                        if SIDTime[1] == 'M':
                            newSID = float(SIDTime[0])*C.daysPerMonth
                        elif SIDTime[1] == 'Y':
                            newSID = float(SIDTime[0])*C.daysPerMonth*C.monthsPerYear
                        
                        PODTime = newRouteData['pullInterval'].split(":")
                        if PODTime[1] == 'M':
                            newPOD = float(PODTime[0])*C.daysPerMonth
                        elif PODTime[1] == 'Y':
                            newPOD = float(PODTime[0])*C.daysPerMonth*C.monthsPerYear
                        newSLD = 0
                    
                    #print "RouteDesc sup stop = {0}".format(routeDesc.supplierStop())
                    if routeDesc.supplierStop() == 0:
                    #    print "supposedly putting this here"
                        newSupplierStoresToSetVehicles.add(newSupplierStore.idcode)
                    else:
                        newClientStoresToSetVehicles.add(oldClientStore.idcode)
                       
                    
                    
                    ### create a new route
                    
                    if len(oldClientRoute.stops) > 2:
                        ### if this is a loop, we know it is push, so this can be simplified
                        newRoute = [
                                    {
                                     'RouteName':'level_loop_remove_{0}_{1}'.format(newSupplierStore.idcode,oldClientStore.idcode),
                                     'Type':newRouteType,
                                     'LocName':newSupplierStore.NAME,
                                     'idcode':newSupplierStore.idcode,
                                     'RouteOrder':0,
                                     'ShipIntervalDays':newSID,
                                     'ShipLatencyDays':newSLD,
                                     'Conditions': newRouteConditions,
                                     'PerDiemType': newRoutePerDiem,
                                     'TruckType': newTruckType,
                                     'PickupDelayFrequency':newPUDFreq,
                                     'PickupDelayMagnitude':newPUDMag,
                                     'PickupDelaySigma':newPUDSigma,
                                     'PullOrderAmountDays':newPOD,#routeTemplate.stops[0].PullOrderAmountDays,
                                     'TransitHours':(oldClientRoute.stops[0].TransitHours + oldSupplierRoute.stops[0].TransitHours),
                                     'DistanceKM':(oldClientRoute.stops[0].DistanceKM + oldSupplierRoute.stops[0].DistanceKM)
                                     }
                                    ]
                        ### now do all of the stops below the supplier
                        for stop in oldClientRoute.stops[1:-1]:
                            newRoute.append(
                                {
                                 'RouteName':'level_loop_remove_{0}_{1}'.format(newSupplierStore.idcode,oldClientStore.idcode),
                                 'Type':newRouteType,
                                 'LocName':stop.store.NAME,
                                 'idcode':stop.store.idcode,
                                 'RouteOrder':oldClientRoute.stops.index(stop),
                                 'ShipIntervalDays':newSID,
                                 'ShipLatencyDays':newSLD,
                                 'Conditions': newRouteConditions,
                                 'PerDiemType': newRoutePerDiem,
                                 'TruckType': newTruckType,
                                 'PickupDelayFrequency':newPUDFreq,
                                 'PickupDelayMagnitude':newPUDMag,
                                 'PickupDelaySigma':newPUDSigma,
                                 'PullOrderAmountDays':newPOD,
                                 'TransitHours':stop.TransitHours,
                                 'DistanceKM':stop.DistanceKM
                                }
                            )
                        ### now the last stop
                        newRoute.append(
                                {
                                'RouteName':'level_loop_remove_{0}_{1}'.format(newSupplierStore.idcode,oldClientStore.idcode),
                                'Type':newRouteType,
                                'LocName':oldClientRoute.stops[-1].store.NAME,
                                'idcode':oldClientRoute.stops[-1].store.idcode,
                                'RouteOrder':len(oldClientRoute.stops)-1,
                                'ShipIntervalDays':newSID,
                                'ShipLatencyDays':newSLD,
                                'Conditions': newRouteConditions,
                                'PerDiemType': newRoutePerDiem,
                                'TruckType': newTruckType,
                                'PickupDelayFrequency':newPUDFreq,
                                'PickupDelayMagnitude':newPUDMag,
                                'PickupDelaySigma':newPUDSigma,
                                'PullOrderAmountDays':newPOD,
                                ### This is definitely approximate, but without internet, or guaranteed geocoordinates, it ain't bad
                                'TransitHours':(oldClientRoute.stops[-1].TransitHours + oldSupplierRoute.stops[0].TransitHours),
                                'DistanceKM':(oldClientRoute.stops[-1].DistanceKM + oldSupplierRoute.stops[0].DistanceKM)
                                 }
                            )
                        #for stop in newRoute:
                        #    print "newRoute {0}: {1}".format(newRoute.index(stop),stop)
                    else:
                        newRoute = []
                        routeClient = {'RouteName':'level_remove_{0}_{1}'.format(newSupplierStore.idcode,oldClientStore.idcode),
                                     'Type':newRouteType,
                                     'LocName':oldClientStore.NAME,
                                     'idcode':oldClientStore.idcode,
                                     'RouteOrder':routeDesc.firstClientStop(),
                                     'ShipIntervalDays':newSID,
                                     'ShipLatencyDays':newSLD,
                                     'Conditions': newRouteConditions,
                                     'PerDiemType': newRoutePerDiem,
                                     'TruckType': newTruckType,
                                     'PickupDelayFrequency':newPUDFreq,
                                     'PickupDelayMagnitude':newPUDMag,
                                     'PickupDelaySigma':newPUDSigma,
                                     'PullOrderAmountDays':newPOD,
                                     'TransitHours':(oldClientRoute.stops[0].TransitHours + oldSupplierRoute.stops[0].TransitHours),
                                     'DistanceKM':(oldClientRoute.stops[0].DistanceKM + oldSupplierRoute.stops[0].DistanceKM)}
                        routeSup = {'RouteName':'level_remove_{0}_{1}'.format(newSupplierStore.idcode,oldClientStore.idcode),
                                     'Type':newRouteType,
                                     'LocName':newSupplierStore.NAME,
                                     'idcode':newSupplierStore.idcode,
                                     'RouteOrder':routeDesc.supplierStop(),
                                     'ShipIntervalDays':newSID,
                                     'ShipLatencyDays':newSLD,
                                     'Conditions': newRouteConditions,
                                     'PerDiemType': newRoutePerDiem,
                                     'TruckType': newTruckType,
                                     'PickupDelayFrequency':newPUDFreq,
                                     'PickupDelayMagnitude':newPUDMag,
                                     'PickupDelaySigma':newPUDSigma,
                                     'PullOrderAmountDays':newPOD,#routeTemplate.stops[0].PullOrderAmountDays,
                                     'TransitHours':(oldClientRoute.stops[0].TransitHours + oldSupplierRoute.stops[0].TransitHours),
                                     'DistanceKM':(oldClientRoute.stops[0].DistanceKM + oldSupplierRoute.stops[0].DistanceKM)}
                        #print "Sup = {0}".format(routeDesc.supplierStop())
                        if routeDesc.supplierStop() == 0:
                            newRoute = [routeSup,routeClient]
                        else:
                            newRoute = [routeClient,routeSup]     
                        #print "New Route0 = {0}".format(newRoute[0])
                        #print "NewRoute1 = {0}".format(newRoute[1])      
                                    
                        
                    #print "Removing Route = {0}".format(oldClientRoute.RouteName)
                    m.removeRoute(oldClientRoute)
                    
                    m.addRoute(newRoute)
                        
                ### Still need to figure out what to do with the original store
                
                if not store.isVaccinating():
#                     ### We should keep it
                    #print "Removing {0}".format(oldSupplierRoute.RouteName)
                    m.removeRoute(oldSupplierRoute)
                    #print "Removing {0}".format(store.idcode)
                    m.removeStore(store)
            
            for storeId in newSupplierStoresToSetVehicles:
                store = m.stores[storeId]
                
                truckCount = store.getRouteTruckCount()
                #print "Truck Count for {0}:{1}".format(store.idcode,truckCount)
                
                ## First eliminate vehicles we no longer need
                
                currentTruckCount = store.countTransport()
                #print "CurrentTruckCount = {0}".format(currentTruckCount)
                for t,c in currentTruckCount.items():
                    if t not in truckCount['total'].keys():
                        store.updateInventory(t,0)
                 
                for truck,count in truckCount['total'].items():
                    thisTruckCount = store.countInventory(truck)
                    neededTrucks = math.ceil(float(count)/2.0/C.daysPerMonth)
                    #print "have: {0} needed: {1}".format(thisTruckCount,neededTrucks)
                    if thisTruckCount == 0:
                        store.addInventory(truck,neededTrucks)
                    else:
                        store.updateInventory(truck,neededTrucks)
                 
                 
            for storeId in newClientStoresToSetVehicles:
                store = m.stores[storeId]
                ### only need to make sure that we have a vehicle for the supplier Route
                truckCount = store.getRouteTruckCount()
                
                ### elminate vehicles that are no longer needed
                currentTruckCount = store.countTransport()
                
                for t,c in currentTruckCount.items():
                    if t not in truckCount['total'].keys():
                        store.updateInventory(t,0)
                
                for truck,count in truckCount['supplierRoutes'].items(): # will only be on
                    thisTruckCount = store.countInventory(truck)
                    if thisTruckCount == 0:
                        store.addInventory(truck,1)
            
            ### Need to set new Shipping Network Latencies
            setLatenciesByNetworkPosition(m,2,limitDays=C.daysPerMonth,stagger=True)
            #print "Set Latencies"
            setUseVialLatenciesAsOffsetOfShipLatencyFromRoute(m,offset=1.0)
            #print "Set V Latencies"
            
            #print "newSup = {0}".format(newSupplierStoresToSetVehicles)
            #print "newClient = {0}".format(newClientStoresToSetVehicles)
            ## Approximate the new vehicle count by having one vehicle
            
                        
            db.commit()
            return {'success':True,'warnings':warningMessage} 
        except Exception,e:
            return {'success':False,'msg':str(e)}                                     
                    
@bottle.route('/json/add_loops_experiment_implement')
def addLoopsExptImplementation(db,uiSession):
        import copy
        from transformation import makeLoopsOptimizedByDistanceBetweenLevels
        try:
            import json
            modelId = _getOrThrowError(bottle.request.params,'modelId', isInt=True)
            exptDataJson = _getOrThrowError(bottle.request.params,'data')
             
            exptData = json.loads(exptDataJson)
             
            uiSession.getPrivs().mayReadModelId(db,modelId)
            m = shadow_network_db_api.ShdNetworkDB(db,modelId)
            
            
            levelStart = exptData['levelStart']
            levelEnd = exptData['levelEnd']
            
            maxLocations = int(exptData['maximumLocations'])
            vehicleToUse = exptData['vehicleToUse']
            
            makeLoopsOptimizedByDistanceBetweenLevels(m,levelStart,levelEnd,maxLocations, iterations=100, vehicleType=vehicleToUse)
            print "setting Latencies"
            setLatenciesByNetworkPosition(m,5,limitDays=C.daysPerMonth,stagger=True)
            print "Set Latencies"
            setUseVialLatenciesAsOffsetOfShipLatencyFromRoute(m,offset=1.0)
            db.commit()
            return {'success':True,'warnings':''}
        
        except Exception,e:
            return {'success':False,'msg':str(e)}  
