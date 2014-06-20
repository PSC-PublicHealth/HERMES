#!/usr/bin/env python
_hermes_svn_id_="$Id$"

import sys, os, types, optparse
import csv_tools

def decomposeId(code):
        print "decomposeId: %d -> "%code,
        clinicCode= code % 100
        code /= 100
        districtCode= code % 100
        code /= 100
        regionCode= code % 100
        print "(%d,%d,%d)"%(regionCode,districtCode,clinicCode)
        return (regionCode,districtCode,clinicCode)
    
def getLevelFromCode(code):
    (rc,dc,cc) = decomposeId(code)
    if rc == 0 and dc == 0 and cc == 0:
        return "Central"
    elif dc == 0 and cc == 0:
        return "Region"
    elif cc == 0:
        return "District"
    else:
        return "Clinic"
    return None

def main():
    storeKeyList = []
    storeRecList = []
    
    routesKeyList = []
    routesRecList = []
    
    reportKeyList = []
    reportRecList = []
    
    summaryKeyList = []
    summaryRecList = []
    
    parser= optparse.OptionParser(usage = """
        %prog --store StoreFile --route RouteFile --report ReportFile 
        """)
    
    parser.add_option("--store",  type="string")
    parser.add_option("--route",  type="string")
    parser.add_option("--report", type="string")
    
    opts,args= parser.parse_args()
    
    if not opts.store or not opts.report:
        sys.exit("You must supply both --store and --report arguments")
        
    report_ave_file = opts.report + ".ave.csv"
    report_ave_summary_file = opts.report + ".ave_summary.csv"
    
    with open(opts.store,"rU") as f:
        storeKeyList,storeRecList = csv_tools.parseCSV(f)
    
    with open(opts.route,"rU") as f:
        routesKeyList,routesRecList = csv_tools.parseCSV(f)
        
    with open(report_ave_file,"rU") as f:
        reportKeyList,reportRecList = csv_tools.parseCSV(f)
        
    with open(report_ave_summary_file,"rU") as f:
        summaryKeyList,summaryRecList = csv_tools.parseCSV(f)
        
    parser.destroy()  
    
    ### Get the Supply Ratios
    sum_supply = 0.0
    count = 0.0
    vials_broken = 0
    sum_OVW = 0.0
    vials_used_tot = 0.0
    vials_expired_tot = 0.0
    for rowDict in summaryRecList[1:]:
        if rowDict['SupplyRatio_ave'] > 0.0:
            #print "supply = " + str(rowDict["SupplyRatio_ave"])
            sum_supply += float(rowDict['SupplyRatio_ave'])
            vials_broken += int(rowDict['VialsBroken_ave'])
            sum_OVW += float(rowDict['OpenVialWasteFrac_ave'])*float(rowDict['VialsUsed_ave'])
            vials_used_tot += float(rowDict['VialsUsed_ave'])
            vials_expired_tot += int(rowDict['VialsExpired_ave'])
            count += 1.0
        
    average_supply = (sum_supply/count)*100.0
    total_OVW = (sum_OVW/vials_used_tot)*100.0
    
    print "\n\n"
    print "Average Supply Ratio = \t%10.2f%%"%average_supply
    print "Vials Broken = \t\t%10d"%vials_broken
    print "Total Vials Used = \t%10d"%vials_used_tot
    print "Open Vial Wastage = \t%10.2f%%"%total_OVW
    print "Vials Expired = \t%10d"%vials_expired_tot
    
    ### Now lets get the storage and transport utilization by level
    
    categoryDict = {}
    storeCatDict = {}
    ## get all categories
    
    for rec in storeRecList:
        level = None
        if "CATEGORY" not in storeKeyList:
            level = getLevelFromCode(rec['idcode'])
        else:
            if rec['FUNCTION'] != 'Surrogate':
                level = rec['CATEGORY']
        if level is not None: 
            storeCatDict[rec['idcode']] = level
                
            if level not in categoryDict.keys():
                categoryDict[level] = {'number':0.0,'storecool':0.0,'storefrez':0.0}
            categoryDict[level]['number'] += 1.0
            
    for rec in reportRecList:
        if rec['code'] != 0:
            categoryDict[storeCatDict[rec['code']]]['storecool'] += float(rec['cooler_ave'])
            categoryDict[storeCatDict[rec['code']]]['storefrez'] += float(rec['freezer_ave'])
    
    for cat in categoryDict.keys():
        categoryDict[cat]['storecool'] /= categoryDict[cat]['number']
        categoryDict[cat]['storecool'] *= 100.0
        categoryDict[cat]['storefrez'] /= categoryDict[cat]['number']
        categoryDict[cat]['storefrez'] *= 100.0
    
    print "\n\n"
    print "Average Storage Capacity Utilization by Level"
    print "-----------------------------------------------------------"
    for cat in categoryDict.keys():
        if "catch" not in cat:
            print "%40s%10.2f%% in cooler %10.2f%% in freezer"%(cat+": ",categoryDict[cat]['storecool'],categoryDict[cat]['storefrez'])
    print "\n\n" 
        
    
    #### To do transport, we need to determine what level going to what level
    #### This right now if a shipping loop spans multiple levels, this won't work
    #### Stole this shit directly from graph_network.py
    
    routeDict= {}
    for rec in routesRecList:
        rname= rec['RouteName']
        if not routeDict.has_key(rname):
            routeDict[rname]= []
        routeDict[rname].append((int(rec['RouteOrder']),rec))
    for k in routeDict.keys():
        l= routeDict[k]
        l.sort()
        routeDict[k]= [rec for junk,rec in l]
        
    routeCategoryDict = {}
    routeCatDict = {}    
    for k in routeDict.keys():
        supplier = routeDict[k][0]['idcode']
        reciever = routeDict[k][1]['idcode']
        level1 = storeCatDict[supplier]
        level2 = storeCatDict[reciever]
        
        level_moniker = level1 + "_" + level2
        routeCatDict[k] = level_moniker
        if level_moniker not in routeCategoryDict.keys():
            routeCategoryDict[level_moniker] = {'number':0.0,'cap':0.0,'trips':0.0}
        routeCategoryDict[level_moniker]['number'] += 1.0
        
    for rec in reportRecList[1:]:
        if str(rec['RouteName']) != 'NA':
            routeCategoryDict[routeCatDict[rec['RouteName']]]['cap'] += float(rec['RouteFill_ave'])
            routeCategoryDict[routeCatDict[rec['RouteName']]]['trips'] += float(rec['RouteTrips_ave'])
        
    for cat in routeCategoryDict.keys():
        routeCategoryDict[cat]['cap'] /= routeCategoryDict[cat]['number']
        routeCategoryDict[cat]['cap'] *= 100.0
        routeCategoryDict[cat]['trips'] /= routeCategoryDict[cat]['number']
    
    print "\n\n"
    print "Average Transport Capacity Utilization by Level"
    print "-----------------------------------------------------------"
    for cat in routeCategoryDict.keys():
        print "%40s%10.2f%% Ave Trips: %10.0f"%(cat +": ",routeCategoryDict[cat]['cap'],routeCategoryDict[cat]['trips'])

        
    
############
# Main hook
############

if __name__=="__main__":
    main()


