#! /usr/bin/env python

########################################################################
# Copyright C 2009, Pittsburgh Supercomputing Center (PSC).            #
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

_hermes_svn_id_="$Id: output_average.py 826 2012-02-16 23:14:57Z welling $"

import sys, os, optparse
import ipath
from csv_tools import parseCSV
import globals
from input import KeywordTokenDefinition, InputDefault

preamble="""
<html>

<head>

<title>HERMES Input File Keywords</title>
<link rel='stylesheet' href='../dev_docs/hermes_doc.css'>
</head>
<body bgcolor="white">

<h1>HERMES Input File Keywords</h1>
<p>

<table>
<tr><th align="right">Keyword<th align="center">Type<th align="center">Default<th align="left">Description</tr>
"""

postamble="""
</table>
</body>
</html>
"""

def main(substituteArgList=None):
    "Parses the input defaults file to produce an html document containing a table of options"

    parser= optparse.OptionParser(usage="""
    %prog --out outFname [inputFile]
    
    inputFile defaults to """+globals.defaultInputTokenFile)
    parser.add_option("--out", type="string", help="filename for output (required)")
    
    if substituteArgList is None:
        opts,args= parser.parse_args()
    else:
        opts,args= parser.parse_args(args=substituteArgList) 
    
    if not opts.out:
        sys.exit("You must supply an --out argument")

    if len(args)==0:
        inFile= globals.defaultInputTokenFile
    elif len(args)==1:
        inFile= args[0]
    else:
        sys.exit("Only one argument please")

    inputDefault = InputDefault()
    with open(opts.out,'wb') as f:
        f.write(preamble)
    
        kList= inputDefault.keys()
        kList.sort()
        for k in kList:
            info= inputDefault.TokenDict[k]
            f.write('<tr><td align="right">%s<td align="center">%s<td align="center">%s<td align="left">%s</tr>\n'%\
                    (info.name,info.type,info.default,info.description))
        
        f.write(postamble)
        f.close()

    parser.destroy()


############
# Main hook
############

if __name__=="__main__":
    main()
