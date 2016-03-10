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

_hermes_svn_id_="$Id: fridgehooks.py 2262 2015-02-09 14:38:25Z stbrown $"

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
from fridgetypes import energyTranslationDict
from currencyhelper import getCurrencyDict
import typehooks

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults

inlizer=session_support.inlizer
_=session_support.translateString

energyOptions = [(x, y[1], [], []) for x,y in energyTranslationDict.items()]
fieldMap = [{ 'label':_('HERMES DB Id'), 'key':'Name', 'id':'name', 'info':False, 'edit':False, 'req':True, 'type':'dbkey'},
            { 'label':_('Name'), 'key':'DisplayName', 'id':'displayname', 'info': True, 'edit':True, 'req':True, 'type':'string'},
            { 'label':_('Make'), 'key':'Make', 'id':'make', 'info': True, 'edit':True, 'req':False, 'type':'string'},
            { 'label':_('Model'), 'key':'Model', 'id':'model', 'info': True, 'edit':True, 'req':False, 'type':'string'},
            { 'label':_('Year'), 'key':'Year', 'id':'year', 'info': True, 'edit':True, 'req':False, 'type':'string'},
            { 'label':_('Net Volume for 2-8C Storage (L)'), 'key':'cooler', 'id':'cooler', 'info': True, 'edit':True, 'req':True, 'canzero':True, 'type':'float'},
            { 'label':_('Net Volume for Below 0C Storage'), 'key':'freezer', 'id':'freezer', 'info': True, 'edit':True, 'req':True, 'canzero':True, 'type':'float'},
            { 'label':_('Net Volume for Room Temperature Storage (L)'), 'key':'roomtemperature', 'id':'roomtemperature',
            'info': True, 'edit':True, 'req':True, 'canzero':True, 'type':'float'},
            { 'label':_('Category of Device'), 'key':'Category', 'id':'category', 'info': True, 'edit':True, 'req':False, 'type':'string'},
            { 'label':_('Type of Technology'), 'key':'Technology', 'id':'technology', 'info': False, 'edit':False, 'req':False, 'type':'string'},
            { 'label':_('Requires'), 'key':'Requires', 'id':'requires', 'info': False, 'edit':False, 'req':False, 'type':'string'},
            { 'label':_('Capital Cost of Device'), 'key':'BaseCost', 'id':'basecost', 'info': True, 'edit':True, 'req':True, 'canzero':True,
             'type':'cost', 'recMap':['BaseCost', 'BaseCostCurCode', 'BaseCostYear']},
            { 'label':_("Usable Lifetime of the Device"), 'key':'AmortYears', 'id':'amortyears', 'info': True, 'edit':True, 'req':True, 'canzero':True, 'type':'float'},
            { 'label':_('Type of Energy Used'), 'key':'Energy', 'id':'energy', 'info': True, 'edit':True, 'req':True, 'type':'select',
             'options':energyOptions,'default':'E'},
            { 'label':_('Rate of Energy Usage'), 'key':'PowerRate', 'id':'powerrate', 'info': True, 'req':True, 'canzero':True, 'type':'dynamicunit',
                'lookup':'Energy', 'lookupDict':energyTranslationDict, 'recMap':['PowerRate', 'PowerRateUnits']},
            { 'label':_('Hold Days with No Power'), 'key':'NoPowerHoldoverDays', 'id':'nopowerholdoverdays', 'info': True, 'edit':False, 'req':False, 'type':'float'},
            { 'label':_('Behavior'), 'key':'ClassName', 'id':'classname', 'info': False, 'edit':False, 'req':False, 'type':'select',
             'options':[('Fridge', _('standard non-portable'), [], ['alarmdays', 'snoozedays', 'coldlifetime']),
                        ('ElectricFridge', _('electric non-portable'), [], ['alarmdays', 'snoozedays', 'coldlifetime']),
                        ('ShippableFridge', _('portable'), [], ['alarmdays', 'snoozedays', 'coldlifetime']),
                        ('IceFridge', _('ice-cooled portable'), ['coldlifetime'], ['alarmdays', 'snoozedays']),
                        ('AlarmedIceFridge', _('ice-cooled with pull support'), ['alarmdays', 'snoozedays', 'coldlifetime'], [])
                        ],'default':'Fridge'},
            { 'label':_('Hold Time of the Device'), 'key':'ColdLifetime', 'id':'coldlifetime', 'info': True, 'edit':False, 'req':False, 'type':'float',
             'default':5.0},
            { 'label':_('AlarmDays'), 'key':'AlarmDays', 'id':'alarmdays', 'info': False, 'edit':False, 'req':False, 'type':'float'},
            { 'label':_('SnoozeDays'), 'key':'SnoozeDays', 'id':'snoozedays', 'info': False, 'edit':False, 'req':False, 'type':'float'},
            { 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'info': True, 'edit':True, 'req':False, 'type':'stringBox'},
            ]

@bottle.route('/fridge-edit')
def fridgeEditPage(db, uiSession):
    return typehooks.typeEditPage(db, uiSession, 'fridges')

@bottle.route('/edit/edit-fridge.json', method='POST')
def editFridge(db, uiSession):
    return typehooks.typeEditPage(db, uiSession, 'fridges')

    
def jsonFridgeEditFn(attrRec, m):
    # PowerRateUnits is completely determined by energy type
    if attrRec['Energy']:
        attrRec['PowerRateUnits'] = energyTranslationDict[attrRec['Energy'].encode('utf-8')][2]
    else:
        attrRec['PowerRateUnits'] = None
    return attrRec


@bottle.route('/json/fridge-edit-verify-commit')
def jsonFridgeEditVerifyAndCommit(db, uiSession):
    return typehooks.jsonTypeEditVerifyAndCommit(db, uiSession, 'fridges', fieldMap,
                                                 jsonFridgeEditFn)
            
@bottle.route('/json/fridge-info')
def jsonFridgeInfo(db, uiSession):
    return typehooks.jsonTypeInfo(db, uiSession, htmlgenerator.getFridgeInfoHTML)
            
@bottle.route('/json/fridge-edit-form')
def jsonFridgeEditForm(db, uiSession):
    return typehooks.jsonTypeEditForm(db, uiSession, 'fridges', fieldMap)


@bottle.route('/fridge-top')
def fridgeTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Cold Storage")))
    return bottle.template("fridge_top.tpl",{"breadcrumbPairs":crumbTrack},pagehelptag="database")

@bottle.route('/json/manage-fridge-table')
def jsonManageFridgeTable(db, uiSession):
    try:
        modelId = int(bottle.request.params['modelId'])
        try:
            uiSession.getPrivs().mayReadModelId(db, modelId)
        except privs.PrivilegeException:
            raise bottle.BottleException('User may not read model %d'%modelId)
        tList = typehelper.getTypeList(db,modelId,'fridges')
        tList = [t for t in tList if t['Category'] != '-chained-'
                 and t['Name'] not in typehelper.hiddenTypesSet]
        for rec in tList:
            if 'DisplayName' not in rec \
                or rec['DisplayName'] is None or rec['DisplayName']=='':
                rec['DisplayName'] = rec['Name']
            if 'Category' not in rec \
                or rec['Category'] is None or rec['Category']=='':
                rec['Category'] = _('Uncategorized')
        nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                            {'category':'Category',
                                                             'name':'Name', 
                                                             'usedin':'modelId', 
                                                             'dispnm':'DisplayName'},
                                                            bottle.request)
        result = {
                  "total":nPages,    # total pages
                  "page":thisPageNum,     # which page is this
                  "records":totRecs,  # total records
                  "rows": [ {"name":t['Name'], 
                             "cell":[t['Category'],
                                     t['Name'], t['_inmodel'], t['DisplayName'], t['Name']]}
                           for t in tList]
                  }
        return result
    except Exception,e:
        return {'success':False, 'msg':str(e)}
        
