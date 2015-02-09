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

_hermes_svn_id_="$Id$"

import csv_tools
import sys,optparse
import vaccinetypes
import trucktypes
import globals as G
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np

class StoreRecord:
    def __init__(self,rec,vacctypes):
        if rec['code'] == "NA":
            self.code = "NA"
            return
        self.code = rec['code']
        self.name = rec['name']
        self.cooler_per = rec['cooler']
        self.cooler_vol = rec['cooler_vol']
        self.cooler = (self.cooler_per * self.cooler_vol)/1000.0
        self.freezer_per = rec['freezer']
        self.freezer_vol = rec['freezer_vol']
        self.freezer = (self.freezer_per*self.freezer_vol)/1000.0
        self.roomtemp = rec['roomtemperature']
        self.roomtemp_vol = rec['roomtemperature_vol']
        self.tot_delivered_vol = rec['tot_delivery_vol']
        self.vaccineDict = {}
        for v in vacctypes.allVaccineTypes:
            vpatstring = v.name + "_patients"
            vtreatstring = v.name + "_treated"
            vvialstring = v.name + "_vials"
            if vpatstring in rec:
                self.vaccineDict[v.name] = {"patients":rec[vpatstring], 
                                       "treated": rec[vtreatstring],
                                       "vials": rec[vvialstring]}
        
class TransportRecord:
    def __init__(self,rec,trucktype):
        if rec['RouteName'] == 'NA':
            self.name = "NA"
            return
        self.name = rec['RouteName']
        self.fill = rec['RouteFill']
        self.fillVol = self.fill * 1000000000000000
        self.trips = rec['RouteTrips']
        self.truckType = trucktypes._truckTypeDict[rec['RouteTruckType']]
        
        
parser= optparse.OptionParser(usage="""
%prog [--report name][--out outputbase]
""")

parser.add_option("--report",help="filename for the report file to be parsed",default="report.csv")
parser.add_option("--out",help="prefix for all output files",default="output")
parser.add_option("--storefile",help="filename of the original storage file to do gap analysis")
parser.add_option("--routefile",help="original routes file")

opts,args = parser.parse_args()

reportFile = opts.report
outputBase = opts.out
storefile = opts.storefile
routefile = opts.routefile

## First get the unified vaccine list
vaccinetypes.initialize(G.vaccinePresentationsFile)
trucktypes.initialize(G.truckTypesFile)

### Need to get the proper Store information
storeDict = {}
with open(storefile,'rU') as f:
    skeyList,srecList = csv_tools.parseCSV(f)

for rec in srecList:
    storeDict[rec["idcode"]] = {"category":rec["CATEGORY"],
                  "name":rec["NAME"],
                  "function":rec["FUNCTION"],
                  "code":rec["idcode"],
                  "cooler":rec["Walk in +(lit)"] + rec["VOL + (lit)"],
                  "freezer":rec["Walk in -(lit)"] + rec["VOL - (lit)"]}

routeDict = {}
with open(routefile,'rU') as f:
    rkeyList,rrecList = csv_tools.parseCSV(f)

for rec in rrecList:
    if rec["RouteOrder"] == 0:
        truckType = trucktypes._truckTypeDict[rec['TruckType']]
        routeDict[rec["RouteName"]] = {"name":rec["RouteName"],
                                       "type":rec["Type"],
                                       "TruckType":truckType}
with open(reportFile,'rU') as f:
    keyList,recList = csv_tools.parseCSV(f)
    
storeRecDict = {}
transportRecDict = {}
for rec in recList:
    store = StoreRecord(rec,vaccinetypes)
    if store.code != "NA":
        storeRecDict[rec['code']]=store
    truck = TransportRecord(rec,trucktypes)
    if truck.name != "NA":
        transportRecDict[rec['RouteName']]=truck

## Ok Time to perform a gap analysis for storage
storegapDict = {}
for store in storeRecDict.keys():
    storePerf = storeRecDict[store]
    storeReal = storeDict[storePerf.code]
    cooler = storePerf.cooler - storeReal["cooler"]
    if cooler < 0.0: cooler = 0.0
    freezer = storePerf.freezer - storeReal["freezer"]
    if freezer < 0.0: freezer = 0.0
    
    storegapDict[storePerf.code] = {"cooler": cooler,
                                "freezer": freezer}
    
## OK Time to perform a transport gap analysis
transportgapDict= {}
for transp in transportRecDict.keys():
    transPerf = transportRecDict[transp]
    transReal = routeDict[transPerf.name]
    
    realTruckCap = transReal["TruckType"][1]['CoolVolumeCC']
    print "TraspFill: " + str(transPerf.fillVol) + " " + str(realTruckCap)
    difference = transPerf.fillVol - realTruckCap
    if difference < 0.0: difference = 0.0
    transportgapDict[transp] = difference/1000.0 #In Liters
    
    
## Lets Make some plots!
## Create List of values to histogram
storeList = []
max = 0.0
for store in storegapDict.keys():
    storeList.append((storegapDict[store]['cooler']+ storegapDict[store]['freezer']))

for store in storeList:
#    print "Store = " + str(store)
    if store > max: 
        max = store
        
#print "Maximum Store is " + str(max)
maxCapacity = 300000
bars = []
for i in range(0,maxCapacity,20000):
    bars.append(i)
bars.append(maxCapacity+20000)

strBars = []
for bar in bars:
    strBars.append(str(bar))
barheights = [0 for i in range(0,len(bars))]
for store in storeList:
    if store == 0.0:
        barheights[0] += 1
    else:
        for i in range(1,len(bars)):
            if store >= bars[i-1] and store < bars[i]:
                barheights[i] += 1
                
NRange = np.arange(len(bars)) + 0.5
xlocations = np.array(range(len(bars)))+0.5      
storeGapFileName = outputBase + "_store_gap.png"
fig = Figure(figsize=(20,6))
subpt = fig.add_subplot(111)
subpt.set_title("Extra Storage Capacity Needed\n for Entire Supply Chain")
subpt.set_xlabel("Extra Capacity Needed (L)")
subpt.set_ylabel("Number of Storage Facilities")
width = 0.25
subpt.title.set_fontsize(12)
subpt.bar(NRange,barheights,width = 0.80,align='center')

#subpt.set_xticks(xlocations+width/2., strBars )
subpt.set_xticks(NRange)
subpt.set_xticklabels(strBars)

subpt.axis([0,len(bars),0,45])
canvas = FigureCanvasAgg(fig)

canvas.print_figure(storeGapFileName,dpi=80)

## Lets Make some plots!
## Create List of values to histogram
storeList = []
for store in storegapDict.keys():
    if storeDict[store]['category'] == "Region":
        storeList.append((storegapDict[store]['cooler']+ storegapDict[store]['freezer']))

maxCapacity =130000
bars = []
for i in range(0,maxCapacity,10000):
    bars.append(i)

strBars = []
for bar in bars:
    strBars.append(str(bar))
barheights = [0 for i in range(0,len(bars))]
for store in storeList:
    if store == 0.0:
        barheights[0] += 1
    else:
        for i in range(1,len(bars)):
            if store >= bars[i-1] and store < bars[i]:
                barheights[i] += 1
            
NRange = np.arange(len(bars)) + 0.5
xlocations = np.array(range(len(bars)))+0.5      
storeGapFileName = outputBase + "_store_region_gap.png"
fig = Figure(figsize=(20,6))
subpt = fig.add_subplot(111)
subpt.set_title("Extra Storage Capacity Needed\n for Region Level of Supply Chain")
subpt.set_xlabel("Extra Capacity Needed (L)")
subpt.set_ylabel("Number of Storage Facilities")
width = 0.25
subpt.title.set_fontsize(12)
subpt.bar(NRange,barheights,width = 0.80,align='center')

#subpt.set_xticks(xlocations+width/2., strBars )
subpt.set_xticks(NRange)
subpt.set_xticklabels(strBars)

subpt.axis([0,len(bars),0,6])
canvas = FigureCanvasAgg(fig)

canvas.print_figure(storeGapFileName,dpi=80)

## Lets Make some plots!
## Create List of values to histogram
storeList = []
for store in storegapDict.keys():
    if storeDict[store]['category'] == "District":
        storeList.append((storegapDict[store]['cooler']+ storegapDict[store]['freezer']))

maxCapacity = 1000
bars = []
for i in range(0,maxCapacity,100):
    bars.append(i)

strBars = []
for bar in bars:
    strBars.append(str(bar))
barheights = [0 for i in range(0,len(bars))]
for store in storeList:
    if store == 0.0:
        barheights[0] += 1
    else:
        for i in range(1,len(bars)):
            if store >= bars[i-1] and store < bars[i]:
                barheights[i] += 1
            
NRange = np.arange(len(bars)) + 0.5
xlocations = np.array(range(len(bars)))+0.5      
storeGapFileName = outputBase + "_store_district_gap.png"
fig = Figure(figsize=(10,6))
subpt = fig.add_subplot(111)
subpt.set_title("Extra Storage Capacity Needed\n for District Level of Supply Chain")
subpt.set_xlabel("Extra Capacity Needed (L)")
subpt.set_ylabel("Number of Storage Facilities")
width = 0.25
subpt.title.set_fontsize(12)
subpt.bar(NRange,barheights,width = 0.80,align='center')

#subpt.set_xticks(xlocations+width/2., strBars )
subpt.set_xticks(NRange)
subpt.set_xticklabels(strBars)

subpt.axis([0,len(bars),0,10])
canvas = FigureCanvasAgg(fig)

canvas.print_figure(storeGapFileName,dpi=80)

## Lets Make some plots!
## Create List of values to histogram
storeList = []
for store in storegapDict.keys():
    if storeDict[store]['category'] == "Province":
        storeList.append((storegapDict[store]['cooler']+ storegapDict[store]['freezer']))


maxCapacity = 7000
bars = []
for i in range(0,maxCapacity,1000):
    bars.append(i)

strBars = []
for bar in bars:
    strBars.append(str(bar))
barheights = [0 for i in range(0,len(bars))]
for store in storeList:
    if store == 0.0:
        barheights[0] +=1
    else:
        for i in range(1,len(bars)):
            if store >= bars[i-1] and store < bars[i]:
                barheights[i] += 1
            
NRange = np.arange(len(bars)) + 0.5
xlocations = np.array(range(len(bars)))+0.5      
storeGapFileName = outputBase + "_store_province_gap.png"
fig = Figure(figsize=(6,6))
subpt = fig.add_subplot(111)
subpt.set_title("Extra Storage Capacity Needed\n for Province Level of Supply Chain")
subpt.set_xlabel("Extra Capacity Needed (L)")
subpt.set_ylabel("Number of Storage Facilities")
width = 0.25
subpt.title.set_fontsize(12)
subpt.bar(NRange,barheights,width = 0.80,align='center')

#subpt.set_xticks(xlocations+width/2., strBars )
subpt.set_xticks(NRange)
subpt.set_xticklabels(strBars)

subpt.axis([0,7,0,6])
canvas = FigureCanvasAgg(fig)

canvas.print_figure(storeGapFileName,dpi=80)

## Lets Make some plots!
## Create List of values to histogram
truckList = []
for truck in transportgapDict.keys():
    truckList.append(transportgapDict[truck])

maxCapacity = 6000
bars = []
for i in range(0,maxCapacity,500):
    bars.append(i)

strBars = []
for bar in bars:
    strBars.append(str(bar))
barheights = [0 for i in range(0,len(bars))]
for truck in truckList:
    if truck == 0.0:
        barheights[0] +=1
    else:
        for i in range(1,len(bars)):
            print "Truck: " + str(truck)
            if truck > bars[i-1] and truck <= bars[i]:
                barheights[i] += 1
            
NRange = np.arange(len(bars)) + 0.5
xlocations = np.array(range(len(bars)))+0.5      
storeGapFileName = outputBase + "_transport_gap.png"
fig = Figure(figsize=(10,6))
subpt = fig.add_subplot(111)
subpt.set_title("Extra Transport Capacity Needed\n for Entire Supply Chain")
subpt.set_xlabel("Extra Capacity Needed (L)")
subpt.set_ylabel("Number of Storage Facilities")
width = 0.25
subpt.title.set_fontsize(12)
subpt.bar(NRange,barheights,width = 0.80,align='center')

#subpt.set_xticks(xlocations+width/2., strBars )
subpt.set_xticks(NRange)
subpt.set_xticklabels(strBars)

subpt.axis([0,len(bars),0,45])
canvas = FigureCanvasAgg(fig)

canvas.print_figure(storeGapFileName,dpi=80)
