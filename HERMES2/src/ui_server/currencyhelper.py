#!/usr/bin/env python

###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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
import ipath
import shadow_network_db_api
import shadow_network

_currencyInfoTuple = None
_currencyModelId = None

def _maybeScanCurrencyTable(db, modelId):
    global _currencyInfoTuple
    global _currencyModelId
    if modelId == _currencyModelId and _currencyInfoTuple is not None:
        return
    m = shadow_network_db_api.ShdNetworkDB(db, modelId)
    start = True
    minYear = None
    maxYear = None
    currencyDict = {}
    for rec in m.currencyTable:
        if start:
            start = False
            minYear = rec.year
            maxYear = rec.year
            code = rec.code.strip()
            currencyDict[code] = rec.currency.strip()
        else:
            if rec.year < minYear: minYear = rec.year
            elif rec.year > maxYear: maxYear = rec.year
            code = rec.code.strip()
            if code not in currencyDict:
                currencyDict[code] = rec.currency.strip()
    _currencyInfoTuple = (minYear, maxYear, currencyDict)
    _currencyModelId = modelId
            
    

def getCurrencyDict(db, modelId):
    _maybeScanCurrencyTable(db, modelId)
    return _currencyInfoTuple[2]

def getCurrencyMinYear(db, modelId):
    _maybeScanCurrencyTable(db, modelId)
    return _currencyInfoTuple[0]

def getCurrencyMaxYear(db, modelId):
    _maybeScanCurrencyTable(db, modelId)
    return _currencyInfoTuple[1]

