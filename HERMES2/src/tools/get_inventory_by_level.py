#!/usr/bin/env python
__doc__ = """ consolidate_places_in_level.py
This program takes a stores file, route file and a csv that describes places to be changed, and creates new stores and routes files executing the alterations.
"""


_hermes_svn_id_ = "$Id: consolidate_places_in_level.py 1053 2012-08-16 17:47:26Z stbrown $"

import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
import input
from copy import deepcopy
import sys
import optparse

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-d db_id]
    """)
    parser.add_option("-i", "--inputfile", default=None)
    parser.add_option("-o","--outputfile",default="inventory.csv")
    # parser.add_option("-d","--use_db",type=int,default=None)
    opts, args = parser.parse_args()
    
    return (opts, args)

if __name__ == '__main__':
    import csv_tools
    import math
    
    
    opts, args = parseCommandLine()
        
    userInput = input.UserInput(opts.inputfile, False)
    shdTypes = shadow_network.loadShdTypes(userInput, input.UnifiedInput())
    shdNtwk = shadow_network.loadShdNetwork(userInput, shdTypes, "Bihar_surr")
    
    inventoryDict = {}
    volumeCounts = {}
    for storeId,store in shdNtwk.stores.items():
        if store.CATEGORY not in inventoryDict.keys():
            inventoryDict[store.CATEGORY] = {}
            volumeCounts[store.CATEGORY] = []
        invDict = store.countAllInventory()
        
        for item,count in invDict.items():
            try:
                year = int(item[-4:])
                item = item[:-5]
            except:
                try:
                    year = int(item[-6:-2])
                    item = item[:-7] + item[-2:]
                except:
                    pass
            if item in inventoryDict[store.CATEGORY].keys():
                inventoryDict[store.CATEGORY][item] += count
            else:
                inventoryDict[store.CATEGORY][item] = count
        for item,count in invDict.items():
            if item.invType == "fridges":
                print "Its a boy!"
                
    #print str(inventoryDict)
    with open(opts.outputfile,"wb") as f:
        f.write("Level,Device,Count\n")
        for level in inventoryDict.keys():
            first = True
            if len(inventoryDict[level])== 0:
                f.write("%s,,\n"%level)
            else:
                for item, count in inventoryDict[level].items():
                    if first:
                        f.write("%s,%s,%d\n"%(level,item,count))
                        first = False
                    else:
                        f.write(",%s,%d\n"%(item,count))
    
                
                
            
            
            
            
            
            
