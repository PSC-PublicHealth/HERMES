#!/usr/bin/env python


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

