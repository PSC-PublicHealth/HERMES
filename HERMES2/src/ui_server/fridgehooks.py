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
from fridgetypes import energyTranslationDict
from currencyhelper import getCurrencyDict
import typehooks

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults

inlizer=session_support.inlizer
_=session_support.translateString

fieldMap = [{'row':1, 'label':_('Name'), 'key':'Name', 'id':'name', 'type':'string'},
            {'row':1, 'label':_('DisplayName'), 'key':'DisplayName', 'id':'displayname', 'type':'string'},
            {'row':1, 'label':_('Make'), 'key':'Make', 'id':'make', 'type':'string'},  
            {'row':1, 'label':_('Model'), 'key':'Model', 'id':'model', 'type':'string'},  
            {'row':2, 'label':_('Year'), 'key':'Year', 'id':'year', 'type':'string'},  
            {'row':2, 'label':_('Cooler Volume (L)'), 'key':'cooler', 'id':'cooler', 'type':'float'},
            {'row':2, 'label':_('Freezer Volume (L)'), 'key':'freezer', 'id':'freezer', 'type':'float'},
            {'row':2, 'label':_('Room Temperature Volume (L)'), 'key':'roomtemperature', 'id':'roomtemperature', 
             'type':'float'},
            {'row':3, 'label':_('Category'), 'key':'Category', 'id':'category', 'type':'string'},  
            {'row':3, 'label':_('Technology'), 'key':'Technology', 'id':'technology', 'type':'string'},  
            {'row':3, 'label':_('Requires'), 'key':'Requires', 'id':'requires', 'type':'string'},  
            {'row':4, 'label':_('Base Cost'), 'key':'BaseCost', 'id':'basecost', 'type':'price'},  
            {'row':4, 'label':_('Base Cost Year'), 'key':'BaseCostYear', 'id':'basecostyear', 'type':'int'},  
            {'row':4, 'label':_('Currency'), 'key':'BaseCostCur', 'id':'basecostcur', 'type':'currency',
             'price':'basecost','year':'basecostyear'},
            {'row':4, 'label':_("Years To Amortize"), 'key':'AmortYears', 'id':'amortyears', 'type':'float'},
            {'row':5, 'label':_('Energy'), 'key':'Energy', 'id':'energy', 'type':'energy'},
            {'row':5, 'label':_('Power Rate'), 'key':'PowerRate', 'id':'powerrate', 'type':'float'},  
            {'row':5, 'label':_('Power Rate Units'), 'key':'PowerRateUnits', 'id':'powerrateunits', 'type':'hide'},  
            {'row':5, 'label':_('Holdover Days'), 'key':'NoPowerHoldoverDays', 'id':'nopowerholdoverdays', 'type':'float'},  
            {'row':5, 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'type':'string'},
            {'row':6, 'label':_('Behavior'), 'key':'ClassName', 'id':'classname', 'type':'select',
             'options':[('Fridge',_('standard non-portable'),[],['alarmdays','snoozedays','coldlifetime']),
                        ('ElectricFridge',_('electric non-portable'),[],['alarmdays','snoozedays','coldlifetime']),
                        ('ShippableFridge',_('portable'),[],['alarmdays','snoozedays','coldlifetime']),
                        ('IceFridge',_('ice-cooled portable'),['coldlifetime'],['alarmdays','snoozedays']),
                        ('AlarmedIceFridge',_('ice-cooled with pull support'),['alarmdays','snoozedays','coldlifetime'],[])
                        ]},  
            {'row':6, 'label':_('ColdLifetime'), 'key':'ColdLifetime', 'id':'coldlifetime', 'type':'float',
             'default':5.0},
            {'row':6, 'label':_('AlarmDays'), 'key':'AlarmDays', 'id':'alarmdays', 'type':'float'},
            {'row':6, 'label':_('SnoozeDays'), 'key':'SnoozeDays', 'id':'snoozedays', 'type':'float'},
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
        
