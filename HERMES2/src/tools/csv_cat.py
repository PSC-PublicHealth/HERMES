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
This is a utility to cat a csv file, keeping the columns aligned.
"""
_hermes_svn_id_="$Id: csv_compare.py 826 2012-02-16 23:14:57Z welling $"

import sys,os,optparse,types
from numbers import Number

import ipath
import csv_tools

###########
# main
###########

def main():
    weakMode= False
    verbose= False
    debug= False
    hideSet= set()
    
    parser= optparse.OptionParser(usage="""
    %%prog fname.csv [--hide ColName1,ColName2,...]
    
    The file is emitted as by 'cat', but respecting columns and applying csv_tools' notions of field types.
    The --hide option suppresses printing of the named columns.
    """)
    parser.add_option("-v","--verbose",action="store_true",help="verbose output")
    parser.add_option("-d","--debug",action="store_true",help="debugging output")
    parser.add_option("--hide",action="append",help="hide the columns in this comma-separated list of names or integers")
 
    opts,args= parser.parse_args()

    if len(args)!=1:
        parser.error("Found %d arguments, expected 1"%len(args))

    # Parse args
    if opts.verbose:
        verbose= True
        csv_tools.verbose= True
    if opts.debug:
        debug= True
        csv_tools.debug= True
    if opts.hide:
        for opStr in opts.hide:
            for word in opStr.split(','):
                hideSet.add(word)

    # Clean up command line parser
    parser.destroy()

    fname= args[0]

    # Ingest the files
    with open(fname,"rU") as f:
        keys,recs= csv_tools.parseCSV(f)

    fieldWidthDict= {}
    for k in keys:
        w= len(str(k))
        for r in recs:
            lenVStr = len(str(r[k]))
            if lenVStr > w: w = lenVStr
        fieldWidthDict[k] = w
        
    obuf= ""
    for n,k in enumerate(keys):
        if k not in hideSet and str(n+1) not in hideSet:
            obuf += "%-*s  "%(fieldWidthDict[k],k)
    obuf= obuf[:-2]
    print obuf
    for r in recs:
        obuf= ""
        for n,k in enumerate(keys):
            if k not in hideSet and str(n+1) not in hideSet:
                if isinstance(r[k],Number):
                    obuf += "%*s  "%(fieldWidthDict[k],r[k])
                else:
                    obuf += "%-*s  "%(fieldWidthDict[k],r[k])
        obuf= obuf[:-2]
        print obuf
        
############
# Main hook
############

if __name__=="__main__":
    main()
