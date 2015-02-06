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
import typehooks

from ui_utils import _logMessage, _logStacktrace, _getOrThrowError, _smartStrip, _getAttrDict, _mergeFormResults
from util import listify
 
inlizer=session_support.inlizer
_=session_support.translateString

fieldMap = [{'row':1, 'label':_('Name'), 'key':'Name', 'id':'name', 'type':'string'},
            {'row':1, 'label':_('DisplayName'), 'key':'DisplayName', 'id':'displayname', 'type':'string'},
            {'row':1, 'label':_('Abbreviation'), 'key':'Abbreviation', 'id':'abbreviation', 'type':'string'},  
            {'row':1, 'label':_('Doses per vial'), 'key':'dosesPerVial', 'id':'dosespervial', 'type':'int'},  
            {'row':2, 'label':_('Method of administration'), 'key':'administration', 
             'id':'methodofadministration', 'type':'select',
             'options':[('IM',_('intramuscular (IM)'),[],[]),
                        ('ID',_('intradermal (ID)'),[],[]),
                        ('SC',_('subcutaneous (SC)'),[],[]),
                        ('Oral',_('oral'),[],[])
                        ]},  
            {'row':2, 'label':_('Vaccine presentation'), 'key':'presentation', 'id':'vaccinepresentation', 
             'type':'select',
             'options':[('Liquid',_('Liquid'),[],[]),
                        ('Freeze Dried',_('Freeze Dried'),[],[]),
                        ('Lyophilized',_('Lyophilized'),[],[]),
                        ('Liquid + Lyophilized',_('Liquid + Lyophilized'),[],[]),
                        ]},
            {'row':3, 'label':_('Lifetime After Opening'), 'key':'openLifetime', 'id':'lifetimeopendays', 'type':'lifetime'},
            {'row':3, 'label':_('Lifetime Warm'), 'key':'roomtempLifetime', 'id':'lifetimeroomtempdays', 'type':'lifetime'},
            {'row':3, 'label':_('Lifetime In Cooler'), 'key':'coolerLifetime', 'id':'lifetimecoolerdays', 'type':'lifetime'},
            {'row':3, 'label':_('Lifetime In Freezer'), 'key':'freezerLifetime', 'id':'lifetimefreezerdays', 'type':'lifetime'},         
            {'row':4, 'label':_('Packed vol/dose(cc) of vaccine'), 'key':'volPerDose', 'id':'volperdosevac', 'type':'float'},  
            {'row':4, 'label':_('Packed vol/dose(cc) of diluent'), 'key':'diluentVolPerDose', 'id':'volperdosedil', 'type':'float'},
            {'row':5, 'label':_('Vaccine price/dose'), 'key':'pricePerDose', 'id':'priceperdose', 'type':'hide'},  
            {'row':5, 'label':_('Vaccine price/vial'), 'key':'pricePerVial', 'id':'pricepervial', 'type':'price'},  
            {'row':5, 'label':_('Price Units'), 'key':'priceUnits', 'id':'priceunits', 'type':'currency'},   
            {'row':5, 'label':_('Price Year'), 'key':'priceYear', 'id':'priceyear', 'type':'int'},  
            {'row':6, 'label':_('Requires'), 'key':'Requires', 'id':'requires', 'type':'string'},  
            {'row':6, 'label':_('Notes'), 'key':'Notes', 'id':'notes', 'type':'string'},
            {'row':6, 'label':_('RandomKey'), 'key':'RandomKey', 'id':'randomkey', 'type':'int'},
            {'row':6, 'label':_('SortOrder'), 'key':'SortOrder', 'id':'sortorder', 'type':'int'},              
            {'row':6, 'label':_('Doses/person'), 'key':'dosesPerPerson', 'id':'dosesperperson', 'type':'hide', 'default':1},              
            ]

@bottle.route('/vaccine-edit')
def vaccineEditPage(db, uiSession):
    return typehooks.typeEditPage(db, uiSession, 'vaccines')

@bottle.route('/edit/edit-vaccine.json', method='POST')
def editVaccine(db, uiSession):    
    return typehooks.editType(db, uiSession, 'vaccines')

def jsonVaccineEditFn(attrRec, m):
    if attrRec['pricePerVial'] is None or attrRec['dosesPerVial'] is None:
        attrRec['pricePerDose'] = None
    else:
        attrRec['pricePerDose'] = float(attrRec['pricePerVial'])/float(attrRec['dosesPerVial'])
    # We must now make our return field rec look like a CSV record.
    filtAttr = {}
    for k,v in attrRec.items():
        if isinstance(v,types.TupleType):
            a,b = v
            filtAttr[k] = a
            filtAttr[k+'Units'] = b
        else:
            filtAttr[k] = v
    return filtAttr

@bottle.route('/json/vaccine-edit-verify-commit')
def jsonVaccineEditVerifyCommit(db, uiSession):
    return typehooks.jsonTypeEditVerifyAndCommit(db, uiSession, 'vaccines', fieldMap,
                                                 jsonVaccineEditFn)
            
@bottle.route('/json/vaccine-info')
def jsonVaccineInfo(db, uiSession):
    return typehooks.jsonTypeInfo(db, uiSession, htmlgenerator.getVaccineInfoHTML)
    
@bottle.route('/json/vaccine-edit-form')
def jsonVaccineEditForm(db, uiSession):
    return typehooks.jsonTypeEditForm(db, uiSession, 'vaccines', fieldMap, useInstance=True)

@bottle.route('/vaccines-top')
def vaccineTopPage(uiSession):
    crumbTrack = uiSession.getCrumbs().push((bottle.request.path,_("Vaccines")))
    return bottle.template("vaccine_top.tpl",{"breadcrumbPairs":crumbTrack},pagehelptag="database")

@bottle.route('/list/select-subkey')
def listSubkey(db, uiSession):
    ''' Returns a json string that can be used to initialize a select box with
    subgrid grouping fields.
    '''
    try:
        modelId = int(bottle.request.params['modelId'])
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d'%modelId)
    except ValueError, e:
        print 'Empty parameters supplied to select-subkey'
        print str(e)
        return {'success': 'false'}
    tList = typehelper.getTypeList(db,modelId,'vaccines')
    assert(len(tList) > 0)

    allowed_subkeys = set(
            ('Abbreviation', 'Manufacturer', 'Vaccine presentation',))
    default_subkey = 'Abbreviation' 

    from itertools import product
    for k, t in product(allowed_subkeys, tList):
        if k not in t:
            allowed_subkeys.remove(k)

    assert(default_subkey in allowed_subkeys)

    pairs = list()
    menustr_list = list() 
    default_subkey_index = None

    for k, i in zip(allowed_subkeys, range(1,1+len(allowed_subkeys))):
        if k == default_subkey:
            default_subkey_index = i
            s = ' selected'
        else:
            s = ''
        pairs.append([i,k])
        menustr_list.append('<option value=%d%s>%s</option>' % (i,s,k))

    result = {'pairs': pairs, 'menustr': '\n'.join(menustr_list),
            'selid': default_subkey_index, 'selname': default_subkey}

    return result

    
    


@bottle.route('/json/manage-vaccine-table')
def jsonManageVaccineTable(db, uiSession):
    modelId = int(bottle.request.params['modelId'])
    try:
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d'%modelId)
    tList = typehelper.getTypeList(db,modelId,'vaccines')
    
    nPages,thisPageNum,totRecs,tList = orderAndChopPage(tList,
                                                        {'dispnm':'DisplayName','usedin':'modelId','name':'Name'},
                                                        bottle.request)
    print type(tList)
    result = {
              "total":nPages,    # total pages
              "page":thisPageNum,     # which page is this
              "records":totRecs,  # total records
              "rows": [ {"name":t['Name'], 
                         "cell": [ t['Name'], t['_inmodel'], t['DisplayName'], t['Name']]}
                       for t in tList ]
              }
    return result


@bottle.route('/json/manage-vaccine-table-groupings')
def jsonManageVaccineTableGroupings(db, uiSession):
    try:
        modelId = int(bottle.request.params['modelId'])
        subkey = str(bottle.request.params['subkey'])
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d'%modelId)
    except ValueError, e:
        print 'Empty parameters supplied to manage-vaccine-table-groupings'
        print str(e)
        return {'success': 'false'}
    tList = typehelper.getTypeList(db,modelId,'vaccines')

    from collections import defaultdict
    groupings = defaultdict(int) 

    for t in tList:
        groupings[t[subkey]] += 1

    thisPageNum = int(bottle.request.params['page'])
    rowsPerPage = int(bottle.request.params['rows'])

    rows = list()
    r = 0
    for subval, count in sorted(groupings.items(),
            key=lambda key_value_pair: key_value_pair[0].upper()):
        if r/rowsPerPage >= thisPageNum - 1:
            subvalHEX = subval.encode('utf-8').encode('hex')
            rows.append({"name": subval, "cell": [subvalHEX, subval, count]})
        r += 1
    
    from math import ceil

    result = {
            "total": int(ceil(len(groupings)/rowsPerPage)), 
            "page": thisPageNum,
            "records": len(groupings),
            "rows": rows
            }

    return result

@bottle.route('/json/manage-vaccine-sub-table')
def jsonManageVaccineSubTable(db, uiSession):
    """ Used to populate subGridRowExpanded in manage_vaccine_grid; see:
    vaccine_top.tpl
    """
    modelId = int(bottle.request.params['modelId'])
    subkey = str(bottle.request.params['subkey'])
    subval = str(bottle.request.params['subval'])
    print subval
    subval = subval.decode('hex').decode('utf-8')
    print subval
    try:
        uiSession.getPrivs().mayReadModelId(db, modelId)
    except privs.PrivilegeException:
        raise bottle.BottleException('User may not read model %d'%modelId)
    tList = typehelper.getTypeList(db,modelId,'vaccines')
    nPages,thisPageNum,totRecs,tList = orderAndChopPage(
            tList,
            {'dispnm':'DisplayName','usedin':'modelId','name':'Name'},
            bottle.request)

    rows = []
    for t in tList:
        if t[subkey] == subval:
            if t.viewkeys() >= {'Name', '_inmodel', 'DisplayName'}:
                rows.append({"name":t['Name'], "cell": [ t['Name'], t['_inmodel'],
                      t['DisplayName'], t['Name']]})
    result = {
              "total":1,    # total pages
              "page":1,     # which page is this
              "records":len(rows),  # total records
              "rows":rows
              }
    return result

