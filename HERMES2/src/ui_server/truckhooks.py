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
from trucktypes import fuelTranslationDict
import typehooks

from ui_utils import _logMessage, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults

inlizer=session_support.inlizer
_=session_support.translateString

fieldMap = [{'row':1, 'label':_('Name'), 'key':'Name', 'id':'name', 'type':'string'},
            {'row':1, 'label':_('DisplayName'), 'key':'DisplayName', 'id':'displayname', 'type':'string'},
            {'row':1, 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'type':'string'},
            {'row':2, 'label':_('Storage'), 'key':'Storage', 'id':'storage', 'type':'string'},  
            {'row':2, 'label':_('CoolVolume (cc)'), 'key':'CoolVolumeCC', 'id':'coolvolumecc', 'type':'float'},
            {'row':2, 'label':_('Requires'), 'key':'Requires', 'id':'requires', 'type':'string'},
            {'row':3, 'label':_('Base Price'), 'key':'BaseCost', 'id':'baseprice', 'type':'price'},  
            {'row':3, 'label':_('Price Units'), 'key':'BaseCostCur', 'id':'basecostcur', 'type':'currency'},   
            {'row':3, 'label':_('Price Year'), 'key':'BaseCostYear', 'id':'basecostyear', 'type':'int'},  
            {'row':4, 'label':_('Km To Amortize'), 'key':'AmortizationKm', 'id':'amortkm', 'type':'float'},
            {'row':4, 'label':_('Fuel'), 'key':'Fuel', 'id':'fuel', 'type':'fuel'},
            {'row':4, 'label':_('Fuel Consumption'), 'key':'FuelRate', 'id':'fuelrate', 'type':'float'},
            {'row':4, 'label':_('Units'), 'key':'FuelRateUnits', 'id':'fuelunits', 'type':'hide'},
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
    return bottle.template("truck_top.tpl",{"breadcrumbPairs":crumbTrack})

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
