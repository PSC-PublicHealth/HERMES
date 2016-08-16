#! /usr/bin/env python

"""
This assumes that lat/lon is present the yaml files, and uses Google's distancematrix
API to grab a section of the travel time/ distance matrix.
"""

import sys
import os
import urllib
import json
import time
import phacsl.utils.formats.csv_tools as csv_tools
import datetime
import pytz
from util import longitudeLatitudeSep

modelDir = '/home/welling/git/hermes/HERMES2/master_data/Odisha_Food'
coordFile = 'HERMES_data_organization_2016Aug4_databyloc.csv'

class PST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-8)

    def dst(self, dt):
        return datetime.timedelta(0)


class UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=0)

    def dst(self, dt):
        return datetime.timedelta(0)

indiaTZ = pytz.timezone('Asia/Calcutta')
targetDateTime = datetime.datetime(2015, 12, 1, 11, tzinfo=indiaTZ)  # 11AM on 7/11/2015
epochDateTime = datetime.datetime(1970, 1, 1, tzinfo=UTC())  # Unix epoch
targetTimestamp = (targetDateTime - epochDateTime).total_seconds()

nRequestsThisBatch = 52  # Google API permits 100, but this keeps url length down


def augmentRec(rec):
    """
    Add some HERMES-specific tags to the record
    """
    newRec = rec.copy()
    newRec['NAME'] = rec['display name']
    newRec['idcode'] = rec['location ID']
    if 'mandi' in rec['supply chain level'].lower():
        cat, func = 'Mandi', 'Distribution'
    elif 'cold storage' in rec['supply chain level'].lower():
        cat, func = 'Storage', 'Distribution'
    elif 'village' in rec['supply chain level'].lower():
        if 'daily' in rec['display name'].lower():
            cat, func = 'DailyTrader', 'Distribution'
        else:
            cat, func = 'WeeklyTrader', 'Distribution'
    elif 'farm' in rec['supply chain level'].lower():
        cat, func = 'Farm', 'Production'
    elif 'retail' in rec['supply chain level'].lower():
        cat, func = 'Retailer', 'Administration'
    else:
        raise RuntimeError('Cannot identify category for input record %s' % rec)
    newRec['CATEGORY'] = cat
    newRec['FUNCTION'] = func
    
    return newRec


#
# Order of the following pairs is chosen to minimize the numberof geodata queries
#
# pairsToConnectDict = {'Farm': 'WeeklyTrader', 'Storage': 'WeeklyTrader', 'Mandi': 'Storage',
#                       'Retailer': 'Mandi'}
pairsToConnectDict = {'Mandi':'Storage'}

facFName = os.path.join(modelDir, coordFile)
facKeys, facRecs = csv_tools.parseCSV(facFName)
facDict = {r['location ID']: augmentRec(r) for r in facRecs}

facByCategoryDict = {}
for k, r in facDict.items():
    if r['CATEGORY'] not in facByCategoryDict:
        facByCategoryDict[r['CATEGORY']] = []
    facByCategoryDict[r['CATEGORY']].append(k)

transitFName = os.path.join(modelDir, 'transitmatrix.csv')
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

newRecs = []

fromLoc = None
for k, rec in facDict.items():
    if rec['CATEGORY'] not in pairsToConnectDict:
        continue
    if k not in transitDict:
        fromLoc = k
        transitDict[fromLoc] = {}
        break
    elif len(transitDict[k]) < len(facByCategoryDict[pairsToConnectDict[rec['CATEGORY']]]):
        fromLoc = k
        break
if fromLoc is None:
    print "All transit data is already present"
else:
    toLocList = []
    nFetch = 0
    if facDict[fromLoc]['CATEGORY'] in pairsToConnectDict:
        for loc in facByCategoryDict[pairsToConnectDict[facDict[fromLoc]['CATEGORY']]]:
            if loc not in transitDict[fromLoc]:
                toLocList.append(loc)
                nFetch += 1
                if nFetch >= nRequestsThisBatch:
                    break
    print 'Fetching data from %s' % fromLoc
    print '...to %s' % toLocList
    
    for k in ['latitude', 'longitude']:
        assert k in facDict[fromLoc], '%s is missing %s data' % (fromLoc, k)
    
    try:
        query = {'origins': '%f,%f' % (facDict[fromLoc]['latitude'], facDict[fromLoc]['longitude'])}
        dstStr = ""
        for toLoc in toLocList:
            for k in ['latitude', 'longitude']:
                assert k in facDict[toLoc], '%s is missing %s data' % (toLoc, k)
            dstStr += '|%f,%f' % (facDict[toLoc]['latitude'], facDict[toLoc]['longitude'])
        dstStr = dstStr[1:]
        query = {'arrival_time': int(targetTimestamp),
                 'origins': '%f,%f' % (facDict[fromLoc]['latitude'], facDict[fromLoc]['longitude']),
                 'destinations': dstStr}
        url = ('http://maps.googleapis.com/maps/api/distancematrix/json?%s' %
               urllib.urlencode(query))
    except Exception, e:
        print 'bad encode: %s' % e
        print 'query: %s' % query
        print 'url: %s' % url
    
    try:
        data = None
        time.sleep(1.0)
        response = urllib.urlopen(url)
        data = json.loads(response.read())
    except Exception, e:
        print 'bad transaction with googleapis: %s' % e
        print 'returned JSON: %s' % data
        
    if len(data) and len(data['rows']):
        for d, toLoc in zip(data['rows'][0]['elements'], toLocList):
            if d['status'] == 'OK':
                transitDict[fromLoc][toLoc] = {'Seconds': d['duration']['value'],
                                               'Meters': d['distance']['value']}
            else:
                print 'Status = %s for %s -> %s' % (d['status'], fromLoc, toLoc)
                if d['status'] == 'ZERO_RESULTS':
                    transitDict[fromLoc][toLoc] = {'Seconds': -1, 'Meters': -1}
        
        outTransitRecs = []
        for fromLoc, fromDict in transitDict.items():
            for toLoc, d in fromDict.items():
                outRec = {'From': fromLoc, 'To': toLoc}
                outRec.update(d)
                outTransitRecs.append(outRec)
        
        print 'Added %d recs; %d total' % (len(outTransitRecs) - nInputRecs, len(outTransitRecs))
        try:
            os.unlink(os.path.join(modelDir, 'transitmatrix.sav.csv'))
        except:
            pass
        try:
            os.rename(os.path.join(modelDir, 'transitmatrix.csv'),
                      os.path.join(modelDir, 'transitmatrix.sav.csv'))
        except:
            pass
        with open(os.path.join(modelDir, 'transitmatrix.csv'), 'w') as f:
            csv_tools.writeCSV(f, transitKeys, outTransitRecs)
        print 'Wrote %s to %s' % ('transitmatrix.csv', modelDir)
    elif data['status'] == 'OVER_QUERY_LIMIT':
        raise RuntimeError('Over Query Limit! %s' % data['error_message'])
    else:
        raise RuntimeError('No data was returned')
