#! /usr/bin/env python

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

_rhea_svn_id_ = "$Id: map_facilities.py 133 2016-03-07 20:12:44Z welling $"

import signal
import os.path
import optparse
from datetime import datetime
import numpy as np
import ipath
from phacsl.utils.formats.csv_tools import parseCSV

import geomap


def getMarkerInfo(rec):
    if 'mandi' in rec['supply chain level'].lower():
        mrk = '+'
    elif 'cold storage' in rec['supply chain level'].lower():
        mrk = 'o'
    elif 'village' in rec['supply chain level'].lower():
        mrk = '.'
    elif 'farm' in rec['supply chain level'].lower():
        mrk = '*'
    else:
        mrk = None

    if rec['location ID'] > 0:
        name = str(rec['location ID'])
    elif len(rec['village']) > 0:
        name = rec['village']
    elif len(rec['display name']) > 0:
        name = rec['display name']
    elif len(rec['Tehsil']) > 0:
        name = rec['Tehsil']
    else:
        name = None

#     if rec['location ID'] > 2000000:
#         name = ' '
#         mrk = None
    return name, mrk
        


def drawMap(geoDataPath, locRecs):

    sumLon = 0.0
    sumLat = 0.0
    for r in locRecs:
        if len(r['display name']) > 0:
            try:
                sumLon += float(r['longitude'])
                sumLat += float(r['latitude'])
            except Exception, e:
                print 'Got exception %s on %s' % (e, r)
                
    ctrLon = sumLon / len(locRecs)
    ctrLat = sumLat / len(locRecs)

    myMap = geomap.Map(geoDataPath,
                       'Odisha', r'((Khordha)|(Cuttack))',
#                         'Odisha', r'Khordha',
#                         'Odisha', r'Cuttack',
                       ctrLon, ctrLat,
                       annotate=True,
                       nameMap={'STATE': 'NAME_1', 'COUNTY': 'NAME_2',
                                'TRACT': 'NAME_3', 'NAME': 'NAME_3'},
                       regexCodes=True)  # Map of Orange County
    LTRED = '#cc6666'
    RED = '#cc0000'
    LTMAGENTA = '#cc66cc'
    MAGENTA = '#cc00cc'
    LTBLUE = '#6666cc'
    BLUE = '#0000cc'
    LTCYAN = '#66cccc'
    CYAN = '#00cccc'
    LTGREEN = '#66cc66'
    GREEN = '#00cc00'
    LTYELLOW = '#cccc66'
    YELLOW = '#cccc00'

    clrTupleSeq = [(LTRED, RED), (LTMAGENTA, MAGENTA), (LTBLUE, BLUE),
                   (LTCYAN, CYAN), (LTGREEN, GREEN), (LTYELLOW, YELLOW)]
    for idx, tract in enumerate(myMap.tractPolyDict.keys()):
        clr1, clr2 = clrTupleSeq[idx % len(clrTupleSeq)]
        myMap.plotTract(tract, clr1)
        
    for idx, r in enumerate(locRecs):
        name, mrk = getMarkerInfo(r)
        if name:
            clr1, clr2 = clrTupleSeq[idx % len(clrTupleSeq)]
            myMap.plotMarker(float(r['longitude']), float(r['latitude']), mrk, name, 'black')

    myMap.draw()


def main():
    verbose = False
    debug = False
    # Thanks to http://stackoverflow.com/questions/25308847/attaching-a-process-with-pdb for this
    # handy trick to enable attachment of pdb to a running program
    def handle_pdb(sig, frame):
        import pdb
        pdb.Pdb().set_trace(frame)
    signal.signal(signal.SIGUSR1, handle_pdb)

    parser = optparse.OptionParser(usage="""
    %prog [-v][-d] input.csv
    """)
    parser.add_option("-v", "--verbose", action="store_true",
                      help="verbose output")
    parser.add_option("-d", "--debug", action="store_true",
                      help="debugging output")

    opts, args = parser.parse_args()

    if opts.debug:
        debug = True
    elif opts.verbose:
        verbose = True

    if len(args) == 1:
        inputPath = args[0]
    else:
        parser.error("A single CSV file containing coordinate data must be specified.")


    with open(inputPath, 'rU') as f:
        keys, recs = parseCSV(inputPath)
    for k in ['location ID', 'latitude', 'longitude']:
        assert k in keys, "Required CSV column %s is missing" % k
        
    geoDataPath = '/home/welling/geo/India/india.geojson'
    stateCode = '06'
    countyCode = '059'

    drawMap(geoDataPath, recs)

if __name__ == "__main__":
    main()
