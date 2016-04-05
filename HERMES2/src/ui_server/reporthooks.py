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
_hermes_svn_id_="$Id: resultshooks.py 1927 2014-09-25 21:45:00Z welling $"

import sys,os,os.path,time,json,math,types
import bottle
import ipath
import shadow_network_db_api
import shadow_network as shdNtwk
import session_support_wrapper as session_support
from HermesServiceException import HermesServiceException
import privs
import htmlgenerator
import typehelper
from costmodel import getCostModelSummary
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

@bottle.route('/json/model-summary-report')
def createModelSummaryWSCall(db, uiSession):
    try:
        modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        
        #returnJson = createModelSummaryJson(m)
        #createModelSummarySerialized(m)
        if m.getModelSummaryJson() is None:
            m.addModelSummaryJson()
        
        returnJson = m.getModelSummaryJson()
        returnJson['success'] = True
        return returnJson
    
    except Exception as e:
        _logStacktrace()
        return {'success':False,'msg':str(e)}
    
def createModelSummarySerialized(m):
    try:
        import json
        return json.dumps(createModelSummaryJson(m))
    except Exception as e:
        _logStacktrace()
        print str(e)
        
def createModelSummaryJson(m):
    from util import longitudeLatitudeSep
    returnJSON = {}
    orderedLevelList= m.getLevelList()
    totalPlaceCount,vaccPlaceCount = getNumberOfLocationsFromModel(m)
    
    levelCount = m.getLevelCount()
    vaccLevelCount = m.getVaccinatingLevelCount()
    returnJSON['name'] = m.name
    ## Level ordering so that one can make this pretty 
    returnJSON['orderedLevelList'] = orderedLevelList
    returnJSON['fixedLocationCount'] = levelCount[1]
    returnJSON['vaccinationLocationCount'] = vaccLevelCount[1]
    returnJSON['fixedLocationCount']['Total'] = totalPlaceCount
    returnJSON['vaccinationLocationCount']['Total'] = vaccPlaceCount
    
    ### Population Information
    peopleByLevelCount = m.getDemandLevelCount()    
    # print peopleByLevelCount
    totalCount = {}
    for level,countDict in peopleByLevelCount.items():
        print level
        for cat in countDict.keys():
            if cat not in totalCount.keys():
                print cat
                totalCount[cat] = {'count':countDict[cat]['count'],'ave':float(countDict[cat]['count']),
                                   'max':countDict[cat]['max'],'min':countDict[cat]['min']}
            else:
                print "S" + cat
                totalCount[cat]['count'] += countDict[cat]['count']
                totalCount[cat]['ave'] += float(countDict[cat]['count'])
                if countDict[cat]['max'] > totalCount[cat]['max']:
                    totalCount[cat]['max'] = countDict[cat]['max']
                if countDict[cat]['min'] < totalCount[cat]['min']:
                    totalCount[cat]['min'] = countDict[cat]['min']
        for cat in countDict.keys():
            totalCount[cat]['ave'] /= float(vaccLevelCount[1][level])
                                            
                
    peopleByLevelCount['Total'] = totalCount
    #print peopleByLevelCount
    returnJSON['populationLevelCount'] = peopleByLevelCount
    returnJSON['inventoryLevelCount'] = m.getInventoryByLevel()
    returnJSON['routeLevelCount'] = m.getRoutesLevelCount()
    
    ### Heirchaical list
    heirIdList = m.getWalkOfClientIdsWithDepth(m.rootStores()[0].idcode)
    heirList= []
    for place,depth in heirIdList:
        thisStore = m.stores[place]
        distKM = -1.0
        if thisStore.hasGIS() and (len(thisStore.suppliers()) > 0 and thisStore.suppliers()[0][0].hasGIS()):
            distKM = longitudeLatitudeSep(thisStore.Longitude,thisStore.Latitude,
                                          thisStore.suppliers()[0][0].Longitude,
                                          thisStore.suppliers()[0][0].Latitude)
        heirList.append({'idcode':thisStore.idcode,'name':thisStore.NAME,
                         'level':thisStore.CATEGORY,'depth':depth,
                         'latitude':thisStore.Latitude,'longitude':thisStore.Longitude,'distKM':distKM})
        
            
        
    returnJSON['heirarchicalStores'] =  heirList
    return returnJSON

@bottle.route('/json/model-vaccine-info-summary')
def createModelVaccineInfoSummary(db,uiSession):
    try:
        modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
        
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        returnJson = {'vaccines':{},'people':[]}
        
        demand = m.unifiedDemands
        
        for v in m.vaccines.values():
            demandDict = {}
            flag = False
            print "For Vaccine {0}".format(v.Name)
            for d in demand:
                if d.peopleStr not in returnJson['people']:
                    returnJson['people'].append(d.peopleStr)
                print "   Demand for {0} {1}".format(d.vaccineStr,d.peopleStr)
                if d.vaccineStr == v.Name:
                    print "       In Demand, Count = {0}".format(d.count)
                    demandDict[d.peopleStr] = d.count
                    if d.count > 0:
                        #demandDict[d.peopleStr] = d.count
                        flag = True
                        break
            if flag:
                returnJson['vaccines'][v.Name] = {'name':m.types[v.Name].getDisplayName(),
                                      'dosesPerVial':v.dosesPerVial,
                                      'volPerDose':v.volPerDose,
                                      'dilVolPerDose':v.diluentVolPerDose,
                                      'abbrev': v.Abbreviation,
                                      'presentation':v.presentation,
                                      'demands':demandDict
                                      }
                
                
                
                
#             returnJson[id]=typeInstance.DisplayName()
        returnJson['success'] = True
        return returnJson
    
    except Exception as e:
        _logStacktrace()
        return {'success':False,'msg':str(e)}
        
    
def getNumberOfLocationsFromModel(model):
    placeCount = 0
    vaccinatingCount = 0
    for storeId,store in model.stores.items():
        if store.isVaccinating():
            vaccinatingCount += 1
        if not store.isAttached():
            placeCount += 1
    return (placeCount,vaccinatingCount)