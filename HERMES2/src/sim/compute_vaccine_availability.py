#! /usr/bin/env python
### This is a hack, please do not comment.
### I will build this into the new HERMES run system

_hermes_svn_id_="$Id$"

import csv_tools
import sys,optparse
import vaccinetypes
import trucktypes
import globals as G
import string as str
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
                if rec[vtreatstring] == "NA":
                    self.vaccineDict[v.name] = {"patients":int(0), 
                                                "treated": int(0),
                                                "vials": int(0)}
                else:
                    self.vaccineDict[v.name] = {"patients":int(rec[vpatstring]), 
                                                "treated": int(rec[vtreatstring]),
                                                "vials": int(rec[vvialstring])}
            
parser= optparse.OptionParser(usage="""
%prog [--report name][--out outputbase]
""")

parser.add_option("--report",help="filename for the report file to be parsed",default="report.csv")
parser.add_option("--out",help="prefix for all output files",default="output")
#parser.add_option("--storefile",help="filename of the original storage file to do gap analysis")
#parser.add_option("--routefile",help="original routes file")

opts,args = parser.parse_args()

reportFile = opts.report
outputBase = opts.out
#storefile = opts.storefile
#routefile = opts.routefile

## First get the unified vaccine list
vaccinetypes.initialize(G.vaccinePresentationsFile)
#trucktypes.initialize(G.truckTypesFile)

### Need to get the proper Store information

with open(reportFile,'rU') as f:
    keyList,recList = csv_tools.parseCSV(f)
    
storeRecDict = {}
transportRecDict = {}
for rec in recList:
    store = StoreRecord(rec,vaccinetypes)
    if store.code != "NA":
        storeRecDict[rec['code']]=store
        
### Aggregate the data across the network
patientsDict = {}
for store in storeRecDict.keys():
    for v in storeRecDict[store].vaccineDict.keys():
        if v not in patientsDict.keys():
            patientsDict[v] = (0,0)
        curpat = patientsDict[v][0]
        curtreated = patientsDict[v][1]
        newpat =  curpat + storeRecDict[store].vaccineDict[v]["patients"]
        newtre = curtreated + storeRecDict[store].vaccineDict[v]["treated"]
        patientsDict[v] = (newpat,newtre)
#        treatedDict[v] = newtre
    
        
    
## Lets Make some plots!
## Create List 
totalList = []
for pat in patientsDict.keys():
    if patientsDict[pat][0] != 0:
        totalList.append((pat,float(patientsDict[pat][1])/float(patientsDict[pat][0])))


#for store in storegapDict.keys():
#    storeList.append((storegapDict[store]['cooler']+ storegapDict[store]['freezer']))
#
#for store in storeList:
##    print "Store = " + str(store)
#    if store > max: 
#        max = store
#        
##print "Maximum Store is " + str(max)
#maxCapacity = 300000
bars = []
barheights = []
for tl in totalList:
    bars.append(str.split(tl[0],"_",1)[1])
    barheights.append(tl[1]*100)

width= 0.5          
NRange = np.arange(len(bars))  
storeGapFileName = outputBase + "_vaccine_avail.png"
fig = Figure(figsize=(8,8))
subpt = fig.add_subplot(111,autoscaley_on=True,ymargin=1.0)
subpt.set_title("Vaccine Availability")
subpt.set_xlabel("Vaccine")
subpt.set_ylabel("Percentage Vaccine Available")

subpt.title.set_fontsize(12)
subpt.bar(NRange,barheights, width = width)

#subpt.set_xticks(xlocations+width/2., strBars )
subpt.set_xticks(NRange+width/2)
subpt.set_xticklabels(bars,rotation=30,fontsize=9)

subpt.axis([0,len(bars),0,100])
canvas = FigureCanvasAgg(fig)

canvas.print_figure(storeGapFileName,dpi=80)
