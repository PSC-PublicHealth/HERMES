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

import sys, os, types, optparse
import csv_tools, input, util

def create_merged_CSV(outFileName, inputFnameList, desiredTags, forbiddenKeys, sortKey=None ):
    outRecList= []
    outKeyList= []
    unhandledKeySet= set()
    tagMethodList= []
    
    if '_ave' in desiredTags: tagMethodList.append(('_ave',util.AccumVal.mean))
    if '_stdv' in desiredTags: tagMethodList.append(('_stdv',util.AccumVal.stdv))
    if '_min' in desiredTags: tagMethodList.append(('_min',util.AccumVal.min))
    if '_max' in desiredTags: tagMethodList.append(('_max',util.AccumVal.max))
    if '_median' in desiredTags: tagMethodList.append(('_median',util.AccumVal.median))
    if '_count' in desiredTags: tagMethodList.append(('_count',util.AccumVal.count))

    with util.openOutputFileForRead(inputFnameList[0],"rU") as f:
        keyList, recList= csv_tools.parseCSV(f)
        rowDict= recList[0]
        outRowDict= util.TagAwareDict(util.AccumVal, tagMethodList)
        for k,v in rowDict.items():
            if k in forbiddenKeys: 
                outRowDict[k]= v
                outKeyList.append(k)
            elif type(v) in [types.IntType, types.LongType, types.FloatType]:
                outRowDict[k]= util.AccumVal(v)
                for suffix in desiredTags: outKeyList.append(k+suffix)
            elif v=='NA':
                outRowDict[k]= 'NA'
                unhandledKeySet.add(k)
            else:
                raise RuntimeError("Can't cope with non-numerical value %s for key %s in %s"%
                                   (v,k,inputFnameList[0]))
        outRecList.append(outRowDict)
        for rowDict in recList[1:]:
            outRowDict= util.TagAwareDict(util.AccumVal, tagMethodList)
            for k,v in rowDict.items():
                if k in forbiddenKeys: 
                    outRowDict[k]= v
                elif type(v) in [types.IntType, types.LongType, types.FloatType]:
                    outRowDict[k]= util.AccumVal(v)
                    if k in unhandledKeySet:
                        for suffix in desiredTags: outKeyList.append(k+suffix)
                        unhandledKeySet.discard(k)
                elif v=='NA':
                    outRowDict[k]= 'NA'
                else:
                    raise RuntimeError("Can't cope with non-numerical value %s for key %s in %s"%
                                       (v,k,inputFnameList[0]))
            outRecList.append(outRowDict)
    for fname in inputFnameList[1:]:
        with util.openOutputFileForRead(fname,"rU") as f:
            keyList, recList= csv_tools.parseCSV(f)
            for rowDict, outRowDict in zip(recList,outRecList):
                for k, v in rowDict.items():
                    if k in forbiddenKeys:
                        pass
                        #if v != outRowDict[k]:
                         #   raise RuntimeError('Mis-matched %s value: %s vs. %s in %s and %s'%
                          #                     (v,outRowDict[k],fname,inputFnameList[0]))
                    elif type(v) in [types.IntType, types.LongType, types.FloatType]:
                        if k not in outRowDict or outRowDict[k] == 'NA':
                            outRowDict[k]= util.AccumVal(v)
                            if k in unhandledKeySet:
                                for suffix in desiredTags: outKeyList.append(k+suffix)
                                unhandledKeySet.discard(k)
                        else:
                            outRowDict[k] += v
                    elif v=='NA':
                        pass
                    else:
                        raise RuntimeError("Can't cope with non-numerical value %s for key %s in %s"%
                                           (v,k,inputFnameList[0]))
    
    for k in unhandledKeySet:
        outKeyList.append(k)

    for k in forbiddenKeys:
        if k in outKeyList:
            outKeyList.remove(k)
        else:
            forbiddenKeys.remove(k)

    outKeyList.sort()

    outKeyList.reverse()
    while len(forbiddenKeys) > 0:
        outKeyList.append(forbiddenKeys.pop())
    outKeyList.reverse()

                                
    with util.openOutputFile(outFileName,"wb") as f:
        csv_tools.writeCSV(f,outKeyList,outRecList,sortColumn=sortKey)


def create_average_summary_CSV(outFileName,inputList,desiredTags=['_ave','_stdv','_count']):
    forbiddenKeys = [ "code", "name", "DisplayName","Name", "DosesPerVial","Type","roomtemperatureStorageFrac"]
    inputFnameList= ["./" + userInput['outputfile'] + "." + str(runNumber) + "_summary.csv" 
                     for runNumber,userInput in enumerate(inputList)]
    create_merged_CSV(outFileName, inputFnameList, desiredTags, forbiddenKeys)
        
def create_average_report_CSV(outFileName, inputList, desiredTags=['_ave','_stdv','_count']):
    forbiddenKeys = [ "code", "name", "RouteName","RouteTruckType","roomtemperatureStorageFrac",
                      "function", "category" ]
    inputFnameList= ["./" + userInput['outputfile'] + "." + str(runNumber) + ".csv" 
                     for runNumber,userInput in enumerate(inputList)]
    create_merged_CSV(outFileName, inputFnameList, desiredTags, forbiddenKeys,sortKey="code")

def create_average_cost_CSV(outFileName, inputList, desiredTags=['_ave']):
    forbiddenKeys = ["ReportingLevel","ReportingBranch","ReportingIntervalDays","DaysPerYear","Currency"]
    inputFnameList= ["./" + userInput['outputfile'] + "." + str(runNumber) + "_costs.csv" 
                     for runNumber,userInput in enumerate(inputList)]
    create_merged_CSV(outFileName, inputFnameList, desiredTags, forbiddenKeys,sortKey="ReportingLevel")
                     
def main():
    "Provides a simple command line interface"

    parser= optparse.OptionParser(usage="""
    %prog --out outRoot [--stdv] [--min] [--max] [--median] [--count] inputFile1 inputFile2 ...
    
    Input files are standard HERMES .csv or .kvp files; they are parsed
    to learn where to find the simulation results.
    """)
    parser.add_option("--out", type="string", help="filename root for output (required)")
    parser.add_option("--stdv", action="store_true", help="include standard deviation")
    parser.add_option("--min", action="store_true", help="include minimum")
    parser.add_option("--max", action="store_true", help="include maximum")
    parser.add_option("--median", action="store_true", help="include median")
    parser.add_option("--count", action="store_true", help="include count")
    
    opts,args= parser.parse_args()
    
    if not opts.out:
        sys.exit("You must supply an --out argument")

    inputList= [input.UserInput(fName) for fName in args]
    
    desiredTags= ['_ave']
    for flag,val in [(opts.stdv,'_stdv'), (opts.min,'_min'), (opts.max,'_max'), (opts.median,'_median'),
                     (opts.count,'_count')]:
        if flag: desiredTags.append(val)
    
    create_average_report_CSV("./" + opts.out + ".ave.csv", inputList, desiredTags)
    create_average_summary_CSV("./" + opts.out + ".ave_summary.csv", inputList, desiredTags)
    parser.destroy()


############
# Main hook
############

if __name__=="__main__":
    main()
