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
_hermes_svn_id_="$Id: truckhooks.py 2262 2015-02-09 14:38:25Z stbrown $"

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
from trucktypes import fuelTranslationDict
import typehooks

from ui_utils import _logMessage, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults

inlizer=session_support.inlizer
_=session_support.translateString

fuelOptions = [(x,y[1],[],[]) for  x,y in fuelTranslationDict.items()]
fieldMap = [{ 'label':_('Data Base ID'), 'key':'Name', 'id':'name', 'info':False, 'edit':True, 'type':'dbkey', 'default':None},
                   { 'label':_('Name'), 'key':'DisplayName', 'id':'displayname', 'info':True, 'edit':True, 'type':'string', 'default':None},
                   { 'label':_('Net Storage at 2-8C (L) '), 'key':'CoolVolumeCC', 'id':'coolvolumecc', 'info':True, 'edit':False, 'type':'custtruckstoresum'},  # Custom Type
                   { 'label':_('Capital Cost'), 'key':'BaseCost', 'id':'baseprice', 'info':True, 'edit':True, 'type':'cost', 'recMap':['BaseCost', 'BaseCostCurCode', 'BaseCostYear']},
                   { 'label':_('Lifetime of Vehicle (KM)'), 'key':'AmortizationKm', 'id':'amortkm', 'info':True, 'edit':True, 'type':'float'},
                   { 'label':_('Fuel Type'), 'key':'Fuel', 'id':'fuel', 'info':True, 'edit':True, 'type':'select','options':fuelOptions},
                   { 'label':_('Fuel Consumption Rate'), 'key':'FuelRate', 'id':'fuelrate', 'info':True, 'edit':True, 
                        'type':'dynamicunit', 'lookup':'Fuel','lookupDict':fuelTranslationDict,'recMap':['FuelRate','FuelRateUnits']},
                   { 'label':_('Requires'), 'key':'Requires', 'id':'requires', 'info':False, 'edit':False, 'type':'string'},
                   { 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'info':True, 'edit':True, 'type':'stringbox'},
                   { 'label':_('Storage'), 'key':'Storage', 'id':'storage', 'info':True, 'edit':False, 'type':'custtruckstoragetable'},
            ]

@bottle.route('/truck-edit')
def truckEditPage(db, uiSession):
    return typehooks.typeEditPage(db, uiSession, 'trucks')

@bottle.route('/edit/edit-truck.json', method='POST')
def editTruck(db,uiSession):  
    return typehooks.editType(db, uiSession, 'trucks')
        

def jsonTruckEditFn(attrRec, m):
# FuelRateUnits is completely determined by energy type
    if attrRec['Fuel']:
        attrRec['FuelRateUnits'] = fuelTranslationDict[attrRec['Fuel'].encode('utf-8')][2]
    else:
        attrRec['FuelRateUnits'] = None
    return attrRec
    
@bottle.route('/json/truck-edit-verify-commit')
def jsonTruckEditVerifyCommit(db, uiSession):
    return typehooks.jsonTypeEditVerifyAndCommit(db, uiSession, 'trucks', fieldMap,
                                                 jsonTruckEditFn)
            
@bottle.route('/json/truck-info')
def jsonTruckInfo(db, uiSession):
    return typehooks.jsonTypeInfo(db, uiSession, htmlgenerator.getTruckInfoHTML)
    
@bottle.route('/json/truck-edit-form')
def jsonTruckEditForm(db, uiSession):
    return typehooks.jsonTypeEditForm(db, uiSession, 'trucks', fieldMap)


@bottle.route('/truck-top')
def truckTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Transport")))
    return bottle.template("truck_top.tpl",{"breadcrumbPairs":crumbTrack},pagehelptag="database")

@bottle.route('/json/manage-truck-table')
def jsonManageTruckTable(db, uiSession):
    modelId = int(bottle.request.params['modelId'])
    try:
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d'%modelId)
    tList = typehelper.getTypeList(db,modelId,'trucks')
    nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                        {'name':'Name', 'usedin':'modelId', 'dispnm':'DisplayName'},
                                                        bottle.request)
    result = {
              "success":True,
              "total":nPages,    # total pages
              "page":thisPageNum,     # which page is this
              "records":totRecs,  # total records
              "rows": [ {"name":t['Name'], 
                         "cell":[t['Name'], t['_inmodel'], t['DisplayName'], t['Name']]}
                       for t in tList ]
              }
    return result
