#! /usr/bin/env python

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

import ipath

import shadow_network
import db_routines

import util

iface = db_routines.DbInterface(echo=True)
session = iface.Session()
m = session.query(shadow_network.ShdNetwork).filter_by(modelId=1).one()
r0 = m.routes['A']
print r0
print "\n\n***************************\n\n"
print r0.stops
print "\n\n***************************\n\n"
print r0.stops[0].store
print "\n\n***************************\n\n"
for item in r0.stops[0].store.inventory:
    invType = item.invType
    print "%d x %s(%s), %s"%(item.count, item.invName, invType.Name, invType.typeClass)
    if invType.typeClass == 'trucks':
        print "volume: %s"%invType.CoolVolumeCC
print r0.stops[0].store.inventory

print "\n\n***************************\n\n"
s = r0.stops[0].store

import types
tf = isinstance(m.stores, types.DictType)
print "\n\n****************"
print tf

print "\n\n****************"

hdo = util.redirectOutput(zipfileName='test_out.zip')
m.writeCSVRepresentation()
util.redirectOutput(path=hdo)

print len(m.stores)

print "\n\n****************"

if len(s.reports) == 0:
    exit()

print s.reports

s = m.stores[60818]
rpt = s.reports.values()[0]
sRMV = rpt.storageRatioMV()
print sRMV
for i in xrange(sRMV.count()):
    print sRMV.getEntryDict(i)

r40309 = m.routes['r40309']
rpt = r40309.reports.values()[0]
sTT = rpt.tripTimesMV()
print sTT
for i in xrange(sTT.count()):
    print sTT.getEntryDict(i)
#print m.fridges

