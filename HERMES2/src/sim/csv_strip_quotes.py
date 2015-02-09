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


__doc__=""" main.py
This is a utility to strip quotes from around strings in .csv files,
in an attempt to overcome incompatibilities between Microsoft Excel and
OpenOffice .csv formats.
"""
_hermes_svn_id_="$Id$"

import sys,os,optparse,types

import csv_tools
              
###########
# main
###########

def main():

    verbose= False
    debug= False
    
    parser= optparse.OptionParser(usage="""
    %prog fname.csv
    
    Original file is saved as fname.sav.csv and rewritten without quoted strings.
    The file is scanned first for commas embedded within strings.
    """)
    parser.add_option("-v","--verbose",action="store_true",help="verbose output")
    parser.add_option("-d","--debug",action="store_true",help="debugging output")
 
    opts,args= parser.parse_args()

    if len(args)!=1:
        parser.error("Found %d arguments, expected 2"%len(args))

    # Parse args
    if opts.verbose:
        verbose= True
        csv_tools.verbose= True
    if opts.debug:
        debug= True
        csv_tools.debug= True

    # Clean up command line parser
    parser.destroy()

    fname= args[0]

    # Ingest the files
    with open(fname,"rU") as f:
        keys,recs= csv_tools.parseCSV(f)

    # Scan for embedded commas; quit if we find one.
    nCommasFound= 0
    recNum= 0
    for r in recs:
        recNum += 1
        for k,v in r.items():
            if type(v) in types.StringTypes and v.find(',')>=0:
                print 'Check %s in record %d'%(k,recNum)
                nCommasFound += 1
    if nCommasFound>0:
        sys.exit("You need to remove %d embedded commas from %s"%(nCommasFound,args[0]))
        
    # Move the old file aside
    if fname[-4:]=='.csv':
        newname= "%s.sav.csv"%(fname[:-4])
    else:
        newname= "%s.sav.csv"%fname
    os.rename(fname,newname)
    
    # Write without quotes
    with open(fname,"w") as f:
        csv_tools.writeCSV(f,keys,recs,delim=',',quoteStrings=False)

############
# Main hook
############

if __name__=="__main__":
    main()
