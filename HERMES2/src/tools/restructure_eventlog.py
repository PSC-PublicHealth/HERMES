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

__doc__=""" main.py
This is a utility to cat a csv file, keeping the columns aligned.
"""
_hermes_svn_id_="$Id: restructure_eventlog.py 826 2012-02-16 23:14:57Z welling $"

import sys,os,optparse,types,re

verbose = False
debug = False

#termRegex = re.compile(r'(([^"]+)|("[^"]+")):(([^"]+)|("[^"]+"))')
termRegex = re.compile(r'((?P<key1>[^"]+)|("(?P<key2>[^"]+)")):((?P<val1>[^",]+)|("(?P<val2>[^"]+)")),+\s*')

def _parseAsNum(s):
    try:
        k = int(s)
    except ValueError,e:
        try:
            k = float(s)
        except ValueError,e:
            k = s
    return k

def parseRec(rec):
    """
    Return a dict from a record consisting of a series of entries like:
    
    key1:val1,key2:val2,

    Keys and values which represent strings will be quoted.
    """
    rec = rec.strip()
    rec += ','
    result = {}
    for m in termRegex.finditer(rec):
        if m.group('key1'):
            k = _parseAsNum(m.group('key1'))
        else:
            k = m.group('key2')
            assert k is not None, "Encountered bad pair %s"%m.group(0)
        if m.group('val1'):
            v = _parseAsNum(m.group('val1'))
        else:
            v = m.group('val2')
            assert v is not None, "Encountered bad pair %s"%m.group(0)
        result[k] = v

    if debug: print result
    return result

def _quoteStrings(x):
    if isinstance(x,types.StringTypes) and len(x)>0: return '"%s"'%x
    else: return x


###########
# main
###########

def main():
    global verbose, debug
    verbose= False
    debug= False
    
    parser= optparse.OptionParser(usage="""
    %%prog [-v][-d] fname.csv outname.csv

    The input file fname.csv is a loosely-structured CSV file with
    an irregular number of columns, in the format of a raw HERMES
    event log.  The output file has a fixed number of columns with
    appropriate column names.
    """)
    parser.add_option("-v","--verbose",action="store_true",help="verbose output")
    parser.add_option("-d","--debug",action="store_true",help="debugging output")
    opts,args= parser.parse_args()

    if len(args)!=2:
        parser.error("Found %d arguments, expected 2"%len(args))

    # Parse args
    if opts.verbose:
        verbose= True
    if opts.debug:
        debug= True

    # Clean up command line parser
    parser.destroy()

    infname = args[0]
    outfname = args[1]

    # We want to do this without ever holding the whole file in memory,
    # because event logs can get very large.
    
    # Scan for column names
    keySet = set()
    with open(infname,'rU') as f:
        for rec in f:
            recDict = parseRec(rec)
            for k in recDict.keys(): keySet.add(k)

    keys = [k for k in keySet]
    keys.sort()

    #
    #  Shift some keys to the left (rightmost in list ends up leftmost)
    #
    for k in ['client','supplier','tripID','route','event','time']:
        if k in keys:
            keys.remove(k)
            keys = [k]+keys

    if debug or verbose: print keys

    with open(outfname,'w') as ofile:
        headerline = ''.join(["%s, "%_quoteStrings(k) for k in keys])
        ofile.write("%s\n"%headerline[:-2])

        with open(infname,'rU') as f:
            for rec in f:
                recDict = parseRec(rec)
                for k in keys:
                    if k not in recDict: recDict[k] = ''
                line = ''.join(["%s, "%_quoteStrings(recDict[k]) for k in keys])
                ofile.write("%s\n"%line[:-2])
        
############
# Main hook
############

if __name__=="__main__":
    main()
