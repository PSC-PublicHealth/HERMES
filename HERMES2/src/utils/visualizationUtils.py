#!/usr/bin/env python

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

__doc__=""" visualizationUtils.py
This module holds miscellaneous utility functions that do not have
a natural home elsewhere.
"""

_hermes_svn_id_="$Id: visualizationutil.py 1697 2014-04-22 21:03:16Z jleonard $"

import ipath
import math

def circleLonLat(center_x,center_y,radius,resolution):
    points = []
    for i in range(resolution, 0, -1):
        angle = (2 * math.pi / float(resolution)) * float(i)
        #print str(angle) + " " + str(center_x) + " " + str(center_y) + " " + str(radius)
        #print "Angles: " + str(math.sin(angle)) + " " + str(math.cos(angle))
        if i == resolution:
            orgPoint = (float(center_x) + float(radius)* math.sin(angle), float(center_y)+ float(radius) * math.cos(angle))
        points.append((float(center_x) + radius * math.sin(angle), 
                       float(center_y) + radius * math.cos(angle)))
        
    points.append((orgPoint[0],orgPoint[1]))
     
    return points

