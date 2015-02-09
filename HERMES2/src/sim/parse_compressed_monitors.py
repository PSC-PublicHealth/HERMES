_hermes_svn_id_="$Id$"

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

from binary_packing import *
import sys


def parseMonitorsCompressed(data):
    i = [0]
    vaxIn = {}

    while(1):
        wh = decodeString(data, i)
        if 0 == len(wh):
            break
        print "warehouse: %s"%wh

        ts = decodeIntList(data, i)
        ts = diffUnpack(diffUnpack(ts))
        ts = map((lambda t: float(t) / 256), ts)
        print "    time series: %s"%ts
        
        while(1):
            vaxId = signedBerDecode(data, i)
            if 0 == vaxId:
                break
            if vaxId not in vaxIn:
                vaxIn[vaxId] = decodeString(data, i)
            vc = decodeIntList(data,i)
            vc = diffUnpack(vc)
            print "    %s: %s"%(vaxIn[vaxId], vc)
            

def main():
    with open(sys.argv[1], "rb") as f:
        bits = f.read()
    parseMonitorsCompressed(bits)

if __name__=="__main__":
    main()
