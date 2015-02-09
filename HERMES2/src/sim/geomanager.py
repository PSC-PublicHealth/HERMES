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


__doc__=""" geomanager.py
This module is intended to encapsulate information about travel distance
and time.
"""

_hermes_svn_id_="$Id: geomanager.py  $"

import sys,math,types
import warehouse
from util import longitudeLatitudeSep
import constants as C

class GeoManager:
    """
    Encapsulates geographical data in a simulation-specific way.  If required is True, an attempt
    to get a distance for which no data is available will raise an exception; if false, the same
    request will return 0.0.
    """
    def __init__(self, required=True):
        self.kmDict = {}
        self.required = required
    def __repr__(self):
        return "GeoManager()"
    def __str__(self):
        return "GeoManager"
    def setKmBetween(self,wh1,wh2,val,level,conditions):
        """
        level and conditions are currently ignored.  If necessary,
        """
        #print "Setting km between %s and %s to %f for level=%s conditions=%s"%\
        #      (wh1.name,wh2.name,val,level,conditions)
        if wh1<wh2:
            keyTuple = (wh1,wh2)
        else:
            keyTuple = (wh2,wh1)
        if keyTuple in self.kmDict:
            oldVal = self.kmDict[keyTuple]
            if oldVal != val:
                raise RuntimeError("Inconsistent distances given for travel between %s and %s: %s km. vs. %s km."%\
                                   (wh1.name,wh2.name,oldVal,val))
        else:
            self.kmDict[keyTuple] = val
        
    def getKmBetween(self,wh1,wh2,level,conditions):
        """
        level and conditions are currently ignored.  If necessary,
        """
        if wh1 == wh2: return 0.0
        elif wh1<wh2:
            keyTuple = (wh1,wh2)
        else:
            keyTuple = (wh2,wh1)
        if keyTuple in self.kmDict:
            #print "Hit known entry %s %s"%(keyTuple[0].name,keyTuple[1].name)
            return self.kmDict[keyTuple]
        else:
            lon1,lat1= wh1.getLonLat()
            lon2,lat2= wh2.getLonLat()
            if (lon1 == 0.0 and lat1 == 0.0) or (lon2 == 0.0 and lat2 == 0.0):
                if self.required:
                    raise RuntimeError("Not enough information is available to calculate travel between %s and %s"%\
                                       (wh1.name,wh2.name))
                else:
                    return 0.0
            return longitudeLatitudeSep(lon1, lat1, lon2, lat2)
            
