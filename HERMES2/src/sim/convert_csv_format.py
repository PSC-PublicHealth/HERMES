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

_hermes_svn_id_="$Id$"

import sys,os,os.path,math,getopt,types
import csv_tools

verbose= 0
debug= 0

outputName= "merge"
sortKey= None

#################
# Notes-
#################

def printUsage():
    print "Usage: %s -v -d [--outname OutBaseName] [--sortkey SortKey] csvFile1 [csvFile2 ...]"%\
          os.path.basename(sys.argv[0])
    print ""
    print "     default OutBaseName is 'merge'"
    print "     default is to have no sort key"

def getSortVal(dict):
    if sortKey != None:
        return dict[sortKey]
    else:
        return 0.0

#################
# Main
#################

def main():
    global verbose, debug
    try:
        (opts,pargs) = getopt.getopt(sys.argv[1:],"vd",
                                     ["outname=","sortkey="])
    except:
        print "%s: Invalid command line parameter" % sys.argv[0]
        printUsage();
        sys.exit()

    #Check calling syntax; parse args
    if len(pargs) < 1 :
        printUsage()
        sys.exit(1)

    for a,b in opts:
        if a=="-v":
            verbose=1
        if a=="-d":
            debug=1
        if a=="--outname":
            outputName= b
        if a=="--sortkey":
            sortKey= b

    allKeys= None
    allLineList= []
    for fname in pargs:
        if verbose: print "reading %s"%fname
        f= open(fname,"r")
        keys, lineList= csv_tools.parseCSV(f)
        f.close()
        if allKeys==None:
            allKeys= keys
        else:
            for k in keys:
                if not k in allKeys:
                    allKeys.append(k)
        for lDict in lineList:
            rCode= lDict['Region code']
            if type(rCode)!=types.IntType:
                rCode= 0
            dCode= lDict['District code']
            if type(dCode)!=types.IntType:
                dCode= 0
            cCode= lDict['Clinic code']
            if type(cCode)!=types.IntType:
                cCode= 0
            lDict['idcode']= long("%d%02d%02d%02d"%(1,rCode,dCode,cCode))
            allLineList.append((getSortVal(lDict),lDict))


    #allLineList.sort() # rules for sorting tuples cause sortval to be used

    left= allKeys.index('Region code')
    right= allKeys.index('Clinic code')
    outKeys= allKeys[:left]+['idcode']+allKeys[right+1:]
    if not outputName[-4:]==".csv":
        outputName= "%s.csv"%outputName
    if verbose: print "writing %s"%outputName
    f= open("%s"%outputName,"w")
    csv_tools.writeCSV(f,outKeys,[d for (s,d) in allLineList])
    f.close()

    print "done"

############
# Main hook
############

if __name__=="__main__":
    main()
