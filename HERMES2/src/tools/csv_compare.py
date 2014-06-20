#! /usr/bin/env python

########################################################################
# Copyright C 2010, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

__doc__=""" main.py
This is a utility to compare pairs of csv files.
"""
_hermes_svn_id_="$Id: csv_compare.py 826 2012-02-16 23:14:57Z welling $"

import sys,os,optparse,types

import csv_tools

defaultMatchBy= ["idcode"]
              
###########
# main
###########

def buildMatchKey(rec,matchBy):
    l= []
    for m in matchBy: l.append(rec[m])
    return tuple(l)

def main():
    weakMode= False
    verbose= False
    debug= False
    
    parser= optparse.OptionParser(usage="""
    %%prog fname1.csv fname2.csv
    
    The files are compared record-for-record based on content.  Field order 
    doesn't matter. 
    Records are matched based on a user-supplied field name (default %s).
    """%defaultMatchBy)
    parser.add_option("-v","--verbose",action="store_true",help="verbose output")
    parser.add_option("-d","--debug",action="store_true",help="debugging output")
    parser.add_option("--match",help=("Match based on this field (default %s). Can appear more than once."%defaultMatchBy),
                      action="append")
    parser.add_option("--ignore",help=("Ignore this field when comparing records. Can appear more than once."%defaultMatchBy),
                      action="append",default=[])
    parser.add_option("--weak",action="store_true",
                      help="Compare only to the degree that string reps of numbers agree.  This reduces sensitivity to the low-order bits of floats.")
 
    opts,args= parser.parse_args()

    if len(args)!=2:
        parser.error("Found %d arguments, expected 2"%len(args))

    # Parse args
    if opts.verbose:
        verbose= True
        csv_tools.verbose= True
    if opts.debug:
        debug= True
        csv_tools.debug= True
    if opts.weak:
        weakMode= True
    if opts.match is not None and len(opts.match)>0:
        matchBy= opts.match
    else:
        matchBy= defaultMatchBy
    ignoreThese= opts.ignore

    # Clean up command line parser
    parser.destroy()

    fname1= args[0]
    fname2= args[1]

    # Ingest the files
    with open(fname1,"rU") as f:
        keys1,recs1= csv_tools.parseCSV(f)
    with open(fname2,"rU") as f:
        keys2,recs2= csv_tools.parseCSV(f)
        
    for m in matchBy:
        if m not in keys1:
            exit('%s does not contain matchby key %s'%(fname1,m))
        if m not in keys2:
            exit('%s does not contain matchby key %s'%(fname2,m))
        
    match= True
    
    key1Mismatches= []
    key2Mismatches= []
    fieldKeys= []
    for k in keys1:
        if k in keys2:
            fieldKeys.append(k)
        else:
            key1Mismatches.append(k)
    for k in keys2:
        if not k in keys1:
            key2Mismatches.append(k)
    key1Mismatches= [k for k in key1Mismatches if k not in ignoreThese]
    key2Mismatches= [k for k in key2Mismatches if k not in ignoreThese]
    if len(key1Mismatches) != 0 or len(key2Mismatches)!= 0:
        match= False
        if len(key1Mismatches)!=0:
            print "File 1 has extra keys %s"%key1Mismatches
        if len(key2Mismatches)!=0:
            print "File 2 has extra keys %s"%key2Mismatches
        sys.exit('Key mismatch!')
        
    matchedRecDict= {}
    duplicates1= []
    extras1= []
    duplicates2= []
    extras2= []
    for r in recs1:
        k= buildMatchKey(r,matchBy)
        if matchedRecDict.has_key(k): duplicates1.append(k)
        else: matchedRecDict[k]= (r,None)
    for r in recs2:
        k= buildMatchKey(r,matchBy)
        if matchedRecDict.has_key(k):
            old1,old2= matchedRecDict[k]
            if old2 is not None: duplicates2.append(k)
            else: matchedRecDict[k]= (old1,r)
        else: extras2.append(k)
    for r in recs1:
        k= buildMatchKey(r,matchBy)
        old1,old2= matchedRecDict[k]
        if old2 is None: 
            extras1.append(k)
            del matchedRecDict[k]
        
    for fn,dupList,extraList in [('File1',duplicates1,extras1),('File2',duplicates2,extras2)]:
        if len(dupList)!=0:
            match= False
            print "%s has duplicate records for these %s values: %s"%(fn,matchBy,dupList)
        if len(extraList)!=0:
            match= False
            print "%s has unmatched records for these %s values: %s"%(fn,matchBy,extraList)

    recKeyList= matchedRecDict.keys()
    recKeyList.sort()
    fieldKeys.sort()
    for k in recKeyList:
        r1,r2= matchedRecDict[k]
        deltas= []
        for f in fieldKeys:
            if weakMode:
                if str(r1[f])!=str(r2[f]) and f not in ignoreThese:
                    deltas.append((f,r1[f],r2[f]))
            else:
                if r1[f]!=r2[f] and f not in ignoreThese:
                    deltas.append((f,r1[f],r2[f]))
        if len(deltas)!=0:
            match= False
            print "%s=%s:"%(matchBy,k)
            for f,v1,v2 in deltas:
                if type(v1)==types.StringType and len(v1)==0: v1= '(empty)'
                if type(v2)==types.StringType and len(v2)==0: v2= '(empty)'
                print "     %s: <%s> --> <%s>"%(f,v1,v2)
    
    if match:
        sys.exit(0)
    else:
        sys.exit('Files do not match')
        
############
# Main hook
############

if __name__=="__main__":
    main()
