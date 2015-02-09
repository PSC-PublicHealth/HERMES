#!/usr/bin/env python
__doc__ = """ consolidate_places_in_level.py
This program takes a stores file, route file and a csv that describes places to be changed, and creates new stores and routes files executing the alterations.
"""

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

_hermes_svn_id_ = "$Id: consolidate_places_in_level.py 1053 2012-08-16 17:47:26Z stbrown $"

import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
import input
from copy import deepcopy
import sys
import optparse
import util
import random

    
def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-d db_id]
    """)
    parser.add_option("-i", "--inputfile", default=None)
    parser.add_option("-s", "--levelstart", default=None)
    parser.add_option("-e", "--levelend",default=None)
    parser.add_option("-n", "--numberPerLoop",type="int",default=None)
    parser.add_option("-t", "--trucktype",default="GenericTruck")

    # parser.add_option("-d","--use_db",type=int,default=None)
    opts, args = parser.parse_args()
    
    return (opts, args)

if __name__ == '__main__':
    import csv_tools
    import math
    from transformation import makeLoopsOptimizedByDistanceBetweenLevels,setLatenciesByNetworkPosition
    
    
    opts, args = parseCommandLine()
        
    userInput = input.UserInput(opts.inputfile, False)
    shdTypes = shadow_network.loadShdTypes(userInput, input.UnifiedInput())
    shdNtwk = shadow_network.loadShdNetwork(userInput, shdTypes, "Bihar_loops3")

    makeLoopsOptimizedByDistanceBetweenLevels(shdNtwk,opts.levelstart,opts.levelend,opts.numberPerLoop,vehicleType=opts.trucktype)
    setLatenciesByNetworkPosition(shdNtwk,3,stagger=True)
    shdNtwk.writeCSVRepresentation()
