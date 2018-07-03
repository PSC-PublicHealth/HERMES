#!/usr/bin/env python


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

