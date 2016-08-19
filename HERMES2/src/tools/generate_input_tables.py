#! /usr/bin/env python

"""
This assumes that lat/lon is present the yaml files, and uses Google's distancematrix
API to grab a section of the travel time/ distance matrix.
"""

import sys
import os
import phacsl.utils.formats.csv_tools as csv_tools
import phacsl.utils.formats.kvp_tools as kvp_tools
from gettext import Catalog

modelDir = '/home/welling/git/hermes/HERMES2/master_data/Odisha_Food'
coordFile = 'HERMES_data_organization_2016Aug4_databyloc.csv'
transitFile = 'transitmatrix.csv'
defsFile = 'Orissa_Food.kvp'

storeNameMap = {'CATEGORY': 'CATEGORY',
                'FUNCTION': 'FUNCTION',
                'idcode': 'idcode',
                'NAME': 'NAME',
                "Latitude": 'latitude',
                "Longitude": 'longitude',
                "Notes": 'NOTES'
                }
storeConstants = {'SiteCostCur': 'INR',
                  'SiteCostPerYear': 0.0,
                  'SiteCostBaseYear': 2016,
                  'PowerOutageFrequencyPerYear': 0.0,
                  'PowerOutageDurationDays': 0.0,
                  'PowerOutageDurationSigma': 0.0,
                  'Inventory': '',
                  "Device Utilization Rate": 1.0,
                  "UseVialsLatency": 0.0,
                  "UseVialsInterval": 7.0,
                  'Inventory': 'Std_SingleCabTruck'
                  }

routeCatPairs = [('Farm', 'Trader', 'CLOSEST_SUPPLIER'),
                 ('Trader',  'Storage', 'CLOSEST_CLIENT'),
                 ('Storage', 'Mandi', 'CLOSEST_CLIENT'),
#                  ('Mandi', 'Retailer', 'CLOSEST_SUPPLIER')
                 ]

def getCategoryChainEnds(routeCatPairs):
    linkD = {}
    for fmCat, toCat, policy in routeCatPairs:
        if fmCat in linkD:
            linkD[fmCat] += 1
        else:
            linkD[fmCat] = 1
        if toCat in linkD:
            linkD[toCat] -= 1
        else:
            linkD[toCat] = -1
    firstCat = lastCat = None
    for cat, v in linkD.items():
        if v == 1:
            assert firstCat is None, 'Category chain has two heads'
            firstCat = cat
        elif v == -1:
            assert lastCat is None, 'Category chain has two tails'
            lastCat = cat
    return firstCat, lastCat

def pairByClosestSupplier(fmKeyList, toKeyList, transitDict):
    """
    For each toKey, create a link fmKey -> toKey where fmKey is
    the key of the supplier with the shortest travel time.  This
    may leave some suppliers unused.
    """
    pairs = []
    for toKey in toKeyList:
        bestFmKey = None
        bestTm = None
        bestDist = None
        for fmKey in fmKeyList:
            if fmKey in transitDict and toKey in transitDict[fmKey]:
                tm = transitDict[fmKey][toKey]['Seconds']
                if tm > 0:
                    if not bestTm or tm < bestTm:
                        bestTm = tm
                        bestDist = transitDict[fmKey][toKey]['Meters']
                        bestFmKey = fmKey
            else:
#                     print 'missing %s -> %s' % (fmKey, toKey)
                pass
        pairs.append({'from': bestFmKey, 'to': toKey, 'time': bestTm,
                      'dist': bestDist})
    return pairs
    
def pairByClosestClient(fmKeyList, toKeyList, transitDict):
    """
    For each fmKey, create a link fmKey -> toKey where toKey is
    the key of the client with the shortest travel time.  This
    may leave some clients unused.
    """
    pairs = []
    for fmKey in fmKeyList:
        bestToKey = None
        bestTm = None
        bestDist = None
        for toKey in toKeyList:
            if fmKey in transitDict and toKey in transitDict[fmKey]:
                tm = transitDict[fmKey][toKey]['Seconds']
                if tm > 0:
                    if not bestTm or tm < bestTm:
                        bestTm = tm
                        bestDist = transitDict[fmKey][toKey]['Meters']
                        bestToKey = toKey
            else:
#                     print 'missing %s -> %s' % (fmKey, toKey)
                pass
        pairs.append({'from': fmKey, 'to': bestToKey, 'time': bestTm,
                      'dist': bestDist})
    return pairs
    
def getWorkingName(baseStr):
    words = baseStr.split(',')
    if 'market' in words[0].lower():
        nm = words[1].strip('"') + ' Market'
    else:
        nm = words[0]
    nm.strip('"')
    if nm.lower().startswith('mandi:'):
        nm = nm[len('mandi: '):] + ' Mandi'
    return nm.strip()

def augmentRec(rec):
    """
    Add some HERMES-specific tags to the record
    """
    newRec = rec.copy()
    newRec['NAME'] = getWorkingName(rec['display name'])
    newRec['idcode'] = rec['location ID']
    if 'mandi' in rec['supply chain level'].lower():
        cat, func = 'Mandi', 'Distribution'
    elif 'cold storage' in rec['supply chain level'].lower():
        cat, func = 'Storage', 'Distribution'
    elif 'village' in rec['supply chain level'].lower():
        if 'daily' in rec['display name'].lower():
            cat, func = 'Trader', 'Distribution'
        else:
            cat, func = 'Trader', 'Distribution'
    elif 'farm' in rec['supply chain level'].lower():
        cat, func = 'Farm', 'Production'
    elif 'retail' in rec['supply chain level'].lower():
        cat, func = 'Retailer', 'Administration'
    else:
        raise RuntimeError('Cannot identify category for input record %s' % rec)
    newRec['CATEGORY'] = cat
    newRec['FUNCTION'] = func
    if rec['notes: re location'] == 0:
        newRec['NOTES'] = ''
    else:
        newRec['NOTES'] = rec['notes: re location']
    
    return newRec

def buildStoreRec(facRec):
    sRec = {}
    for k, v in storeNameMap.items():
        if v in facRec:
            sRec[k] = facRec[v]
    for k, v in storeConstants.items():
        sRec[k] = v
    return sRec

def buildRouteRecList(pairSC, facDict):
    fmKey = pairSC['from']
    toKey = pairSC['to']
    rName = 'r_%s_%s' % (fmKey, toKey)
    tmHours = pairSC['time']/3600.
    distKm = 0.001 * pairSC['dist']
    rRecs = [{'RouteName': rName, 'idcode': fmKey, 'LocName': facDict[fmKey]['NAME'],
              'Type': 'varpush', 'RouteOrder': 0, 'TransitHours': tmHours,
              'DistanceKM': distKm, 'ShipIntervalDays': 7, 'ShipLatencyDays': 0,
              "PickupDelayMagnitude": 0.0, "PickupDelaySigma": 0.0,
              "PickupDelayFrequency": 0.0, 'PullOrderAmountDays': 7,
              "TruckType": "Std_SingleCabTruck"
              },
             {'RouteName': rName, 'idcode': toKey, 'LocName': facDict[toKey]['NAME'],
              'Type': 'varpush', 'RouteOrder': 1, 'TransitHours': tmHours,
              'DistanceKM': distKm, 'ShipIntervalDays': 7, 'ShipLatencyDays': 0,
              "PickupDelayMagnitude": 0.0, "PickupDelaySigma": 0.0,
              "PickupDelayFrequency": 0.0, 'PullOrderAmountDays': 7,
              "TruckType": "Std_SingleCabTruck"
              }
             ]
    return rRecs

kvpParser = kvp_tools.KVPParser()
with open(os.path.join(modelDir, defsFile), 'rU') as f:
    defsDict = kvp_tools.KVPParser().parse(f)
print defsDict

facFName = os.path.join(modelDir, coordFile)
facKeys, facRecs = csv_tools.parseCSV(facFName)
facDict = {r['location ID']: augmentRec(r) for r in facRecs}

facByCategoryDict = {}
for k, r in facDict.items():
    if r['CATEGORY'] not in facByCategoryDict:
        facByCategoryDict[r['CATEGORY']] = []
    facByCategoryDict[r['CATEGORY']].append(k)

transitFName = os.path.join(modelDir, transitFile)
try:
    with open(transitFName, 'rU') as f:
        transitKeys, transitRecs = csv_tools.parseCSV(f)  #
except Exception, e:
    print 'Could not parse input transitmatrix'
    transitKeys = ['From', 'To', 'Seconds', 'Meters']
    transitRecs = []
nInputRecs = len(transitRecs)

transitDict = {}
for r in transitRecs:
    if r['From'] not in transitDict:
        transitDict[r['From']] = {}
    transitDict[r['From']][r['To']] = {'Seconds': r['Seconds'], 'Meters': r['Meters']}
#
# Symmetrize the transitDict
#
symTransitDict = transitDict.copy()
now = False
for k1, d1 in transitDict.items():
    for k2, rec in d1.items():
        if k2 not in transitDict:
            if k2 not in symTransitDict:
                symTransitDict[k2] = {}                
        if k1 not in symTransitDict[k2]:
            symTransitDict[k2][k1] = rec
transitDict = symTransitDict
#
# Test symmetrization
#
for k1, d1 in transitDict.items():
    for k2, rec in d1.items():
        assert k2 in transitDict, '%s %s' % (k1, k2)
        assert k1 in transitDict[k2],  '%s %s' % (k1, k2)
        assert transitDict[k2][k1] == rec,  '%s %s' % (k1, k2)

storeKeys = ["CATEGORY", "FUNCTION", "NAME", "idcode",
             "Device Utilization Rate", "UseVialsLatency", "UseVialsInterval",
             "Latitude", "Longitude",
             "PowerOutageFrequencyPerYear", "PowerOutageDurationSigma", 
             "SiteCostCur", "PowerOutageDurationDays", "SiteCostPerYear", "SiteCostBaseYear",
             "Inventory","Notes"]
storeRecs = []
for k, r in facDict.items():
    storeRecs.append((k, buildStoreRec(r)))
storeRecs.sort()
storeRecs = [r for k, r in storeRecs]

with open(os.path.join(modelDir, defsDict['storesfile']), 'w') as f:
    csv_tools.writeCSV(f, storeKeys, storeRecs)
print 'wrote %d store records' % len(storeRecs)

routeKeys = ["RouteName", "idcode", "LocName", "Type", "RouteOrder", "TransitHours",
             "TruckType", "ShipIntervalDays", "ShipLatencyDays", "PullOrderAmountDays",
             "DistanceKM", "Conditions", "Notes",
             "PickupDelayMagnitude", "PickupDelaySigma","PickupDelayFrequency",
             "PerDiemType"]
firstCat, lastCat = getCategoryChainEnds(routeCatPairs)
allCatSet = set([fm for fm, to, policy in routeCatPairs]
                + [to for fm, to, policy in routeCatPairs])
assert allCatSet == set(facByCategoryDict.keys()), \
    "Not all categories are included in route pairings"
noSupplierSet = set([key for key in facDict.keys()
                   if facDict[key]['CATEGORY'] != firstCat])
noClientSet = set([key for key in facDict.keys()
                   if facDict[key]['CATEGORY'] != lastCat])
fullPairSCList = []
for fmCat, toCat, policy in routeCatPairs:
    
    fmKeyList = facByCategoryDict[fmCat] if fmCat in facByCategoryDict else []
    toKeyList = facByCategoryDict[toCat] if toCat in facByCategoryDict else []
    
    if policy == 'CLOSEST_SUPPLIER':
        pairSCList = pairByClosestSupplier(fmKeyList, toKeyList, transitDict)
    elif policy == 'CLOSEST_CLIENT':
        pairSCList = pairByClosestClient(fmKeyList, toKeyList, transitDict)
    else:
        raise RuntimeError('Unknown pairing policy %s' % policy)
    
    for pairSC in pairSCList:
        if pairSC['from'] is not None:
            noSupplierSet.discard(pairSC['to'])
        if pairSC['to'] is not None:
            noClientSet.discard(pairSC['from'])
            
    if toCat == lastCat:
        for key in toKeyList:
            noClientSet.discard(key)
            
    fullPairSCList.extend([p for p in pairSCList if p['from'] and p['to']])
        
noNothingList = list(noSupplierSet.intersection(noClientSet))
noNothingList.sort()
print 'The following unexpectedly have neither clients nor suppliers: %s' % noNothingList
noSupplierList = list(noSupplierSet.difference(noClientSet))
noSupplierList.sort()
print 'The following unexpectedly have no suppliers: %s' % noSupplierList
noClientList = list(noClientSet.difference(noSupplierSet))
noClientList.sort()
print 'The following unexpectedly have no clients: %s' % noClientList

routeRecs = []
for pairSC in fullPairSCList:
    routeRecs.extend(buildRouteRecList(pairSC, facDict))
with open(os.path.join(modelDir, defsDict['routesfile']), 'w') as f:
    csv_tools.writeCSV(f, routeKeys, routeRecs)
print 'wrote %d route records' % len(routeRecs)

