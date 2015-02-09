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
from copy import deepcopy
import sys
import util
import random
import math

def fixTimesByMaxTripLength(times,maxTimePerTrip):
    actualTimes = []
    leftoverTime = 0.0
    for timeLength in times:
        withLeft = leftoverTime+timeLength
        maxTimeTrips = math.floor((withLeft)/maxTimePerTrip)
        thisTime = maxTimeTrips*24.0 + (timeLength - maxTimeTrips*maxTimePerTrip)
        leftoverTime = withLeft - maxTimeTrips*maxTimePerTrip
        
        actualTimes.append(thisTime)

    return actualTimes
        
            
def chunks(l,n):
    for i in xrange(0,len(l),n):
        yield l[i:i+n] 
              
def findBestLoops(hubLoc,locList,pointsPerLoop,nIterations = 10):
    numLoops = int(math.ceil(float(len(locList))/float(pointsPerLoop)))
    
    origIndex = [x for x in range(0,len(locList))]
    
    bestConnections = []
    bestDistance = 9999999999
    currrentConnections = []
    
    ### Begin Iteration
    for i in range(0,nIterations):
        ### first create current connections
        newIndex = deepcopy(origIndex)
        random.shuffle(newIndex)
        #print "newIndex = " + str(newIndex)
        # make this a set of x loops
        currentConnections = list(chunks(newIndex,pointsPerLoop))
        #print "Cur = " + str(currentConnections)
        
        ### Calculate the total distance travelled with these loops
        totalDistance = 0.0
        for loop in currentConnections:
            # first Leg
            #print "%s"%str(loop)
            #print "%d"%loop[0]
            totalDistance += util.longitudeLatitudeSep(hubLoc[0],hubLoc[1],
                                                       locList[loop[0]][0],locList[loop[0]][1])
            # last Leg
            totalDistance += util.longitudeLatitudeSep(hubLoc[0],hubLoc[1],
                                                       locList[loop[len(loop)-1]][0],locList[loop[len(loop)-1]][1])
            # All the shit in between
            for stop in xrange(0,len(loop)-2):
                start = locList[loop[stop]]
                end = locList[loop[stop+1]]
                
                totalDistance += util.longitudeLatitudeSep(start[0],start[1],end[0],end[1])
            
        
        #print "Total Distance = %10.10f"%totalDistance
        if totalDistance < bestDistance:
            ### set this as the best so far
            bestConnections = currentConnections
            bestDistance = totalDistance

    return (bestDistance,bestConnections)
                
    
