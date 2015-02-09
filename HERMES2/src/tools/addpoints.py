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

import random
import math

import csv_tools

def isiterable(c):
    "simple test for iterability"
    if hasattr(c, '__iter__') and callable(c.__iter__):
        return True
    return False

def listify(v, keepNone = False):
    """
    make something iterable if it isn't already
    """
    if keepNone:
        if v is None:
            return None
    if v is None: 
        return []
    if isiterable(v):
        return v
    return [v]


def distance(p1, p2):
    x = p1[0] - p2[0]
    y = p1[1] - p2[1]
    return math.sqrt(x * x + y * y)

def distance_sq(p1, p2):
    x = p1[0] - p2[0]
    y = p1[1] - p2[1]
    return x * x + y * y


class PointCloud:
    def __init__(self, fixedPoints = None):
        self.fixedPoints = listify(fixedPoints)
        self.edgePoints = []
        self.addedPoints = []

        self.center = self.findCenter(self.fixedPoints)
        self.acnd = self.averageClosestNeighborDistance(self.fixedPoints)
        self.gcnd = self.greatestClosestNeighborDistance(self.fixedPoints)
        self.mdfc = self.maxDistanceFromCenter(self.fixedPoints)

        

    @staticmethod
    def findCenter(points):
        pc = len(points)
        if 0 == pc:
            return [0,0]

        xsum = float(0.0)
        ysum = float(0.0)
        for p in points:
            xsum += p[0]
            ysum += p[1]
        return [xsum / pc, ysum / pc]


    @staticmethod
    def closestNeighborDistance(p, points, ignore=None):
        """
        find the distance to the closest neighbor to p from the set points.  
        Ignore p in points.  Also ignore the point ignore if set
        """
        minD = 0
        for np in points:
            if np == p:
                continue
            if np == ignore:
                continue
            d = distance_sq(p, np)
            if minD == 0 or d < minD:
                minD = d

        minD = math.sqrt(minD)
        #print minD
        return minD

    @staticmethod
    def averageClosestNeighborDistance(points):
        if len(points) <= 1:
            return 0
        s = 0
        for p in points:
            s += PointCloud.closestNeighborDistance(p, points)
        return s / len(points)

    @staticmethod
    def greatestClosestNeighborDistance(points):
        if len(points) <= 1:
            return 0
        m = 0.0
        for p in points:
            cnd = PointCloud.closestNeighborDistance(p, points)
            if cnd > m:
                m = cnd
        return m
        

    def maxDistanceFromCenter(self, points):
        m = 0.0
        for p in points:
            d = distance(p, self.center)
            if d > m:
                m = d

        return m

    def addEdgePoint(self, minDist = None):
        if minDist is None:
            minDist = self.gcnd/3.0
        while(1):
            angle = random.uniform(0,math.pi * 2)
            radius = random.uniform(self.mdfc*2, self.mdfc*4)
            #print "angle: %s, radius: %s"%(angle, radius)

            p = [math.sin(angle) * radius + self.center[0], 
                 math.cos(angle) * radius + self.center[1]]
            #print "point: %s"%p
            if len(self.edgePoints) > 0:
                if self.closestNeighborDistance(p, self.edgePoints) < minDist:
                    continue
            break
        self.edgePoints.append(p)

    def scoreEdgePoint(self, p, oldP, minSepEdge, minSepFixed):
        if self.closestNeighborDistance(p, self.edgePoints, oldP) < minSepEdge:
            return -2.0
        if self.closestNeighborDistance(p, self.fixedPoints, oldP) < minSepFixed:
            return -2.0
        score = 0.0
        for fp in self.fixedPoints:
            score += 1.0 / distance_sq(p, fp)
        return score
        

    def moveEdgePoint(self, p, minSepEdge, minSepFixed, step):
        bestScore = 0
        bestMove = p

        for i in xrange(10):
            angle = random.uniform(0, math.pi * 2)
            radius = random.uniform(0, step)
            move = [math.sin(angle) * radius + p[0],
                    math.cos(angle) * radius + p[1]]
            s = self.scoreEdgePoint(move, p, minSepEdge, minSepFixed)
            if s > bestScore:
                bestScore = s
                bestMove = move

        return bestMove
                
    def moveEdgePoints(self, minSepEdge = None, minSepFixed = None, step = None):
        if minSepEdge is None:
            minSepEdge = self.gcnd / 3.0
        if minSepFixed is None:
            minSepFixed = self.gcnd
        if step is None:
            step = minSepEdge / 2.0

        for i,p in enumerate(self.edgePoints):
            self.edgePoints[i] = self.moveEdgePoint(p, minSepEdge, minSepFixed, step)


    def scoreAddedPoint(self, p, oldP, minSepEdge):
        if self.closestNeighborDistance(p, self.edgePoints) < minSepEdge:
            return -2.0

        score = 0.0
        for fp in self.fixedPoints:
            if oldP == fp:
                continue
            score += 1.0 / distance_sq(p, fp)
        for mp in self.addedPoints:
            if oldP == mp:
                continue
            score += 1.0 / distance_sq(p, mp)
        return score

        
    def moveAddedPoint(self, p, minSepEdge, step):
        bestScore = 0
        bestMove = p

        for i in xrange(10):
            angle = random.uniform(0, math.pi * 2)
            radius = random.uniform(0, step)
            move = [math.sin(angle) * radius + p[0],
                    math.cos(angle) * radius + p[1]]
            s = self.scoreAddedPoint(move, p, minSepEdge)
            if s == -2.0:
                continue
            if bestScore == 0:
                bestScore = s
                bestMove = move
                continue

            if s < bestScore:
                bestScore = s
                bestMove = move

        return bestMove
                
    def moveAddedPoints(self, minSepEdge = None, step = None):
        if minSepEdge is None:
            minSepEdge = self.gcnd * 0.8
        if step is None:
            step = minSepEdge / 5.0

        for i,p in enumerate(self.addedPoints):
            self.addedPoints[i] = self.moveAddedPoint(p, minSepEdge, step)

    def addAddedPoint(self, minSepEdge = None, step = None):
        if minSepEdge is None:
            minSepEdge = self.gcnd * 0.8
        if step is None:
            step = minSepEdge / 5.0

        bestLoc = 0
        bestScore = 0
        for i in xrange(4):
            r = random.randrange(len(self.fixedPoints))
            p = self.fixedPoints[r][:]
            if bestLoc == 0:
                bestLoc = p
            s = self.scoreAddedPoint(p, p, minSepEdge)
            if s == -2.0:
                continue
            if bestScore == 0:
                bestScore = s
                bestLoc = p
                continue

            if s < bestScore:
                bestScore = s
                bestLoc = p

        p = bestLoc
        for i in xrange(40):
            p = self.moveAddedPoint(p, minSepEdge, step)

        self.addedPoints.append(p)


def printGraph(pc):
    scale = 3.0
    zero = -15.0

    size = int(80) + 1

    graph = []
    for y in xrange(size):
        graph.append([])
        for x in xrange(size):
            graph[y].append(' ')

    for p in pc.fixedPoints:
        x = int(p[0]*scale + zero)
        y = int(p[1]*scale + zero)
        graph[y][x] = 'X'

    for p in pc.addedPoints:
        x = int(p[0]*scale + zero)
        y = int(p[1]*scale + zero)
        graph[y][x] = '+'

    for p in pc.edgePoints:
        x = int(p[0]*scale + zero)
        y = int(p[1]*scale + zero)
        graph[y][x] = '.'


    for row in graph:
        s = ''
        for glyph in row:
            s = s + glyph
        print s



def processPoints(fixedPoints, numAdd):
    pc = PointCloud(fixedPoints)
    print "average nearest neighbor distance: %s"%pc.acnd
    print "center: %s"%pc.center
    print "gcnd: %s"%pc.gcnd
    print "mdfc: %s"%pc.mdfc

    #printGraph(pc)
    
    for i in xrange(150):
        pc.addEdgePoint()
    #print pc.edgePoints
    for i in xrange(600):
        pc.moveEdgePoints()
    #print pc.edgePoints
    #printGraph(pc)

    for i in xrange(numAdd):
        pc.addAddedPoint()

    for i in xrange(400):
        pc.moveAddedPoints()
    #printGraph(pc)
    print "finished District, added %d points"%numAdd
    return pc.addedPoints

        

def setLatLon(s, lat=None, lon=None):
    if lat is None:
        lat = s['Latitude']
    if lon is None:
        lon = s['Longitude']

    s['Latitude'] = lat
    s['Longitude'] = lon

    return s

def processStores(stores):
    if 0 == len(stores):
        return []

    unknownCount = 0
    unknownStores = []
    fixedPoints = []
    for s in stores:
        setLatLon(s)
        lat = s['Latitude']
        lon = s['Longitude']
        if lat == '' or lon == '':
            unknownCount += 1
            unknownStores.append(s)
        else:
            fixedPoints.append([lat,lon])

    if len(fixedPoints) > 2 and unknownCount > 0:
        points = processPoints(fixedPoints, unknownCount)

        for (i,s) in enumerate(unknownStores):
            setLatLon(s, points[i][0], points[i][1])

    return stores

        

def main():
#    fixedPoints = [[0,0], [1,2], [2,5], [4,1], [4,4], [3,3], [6,6]]
#    fixedPoints = []
#    for i in xrange(15):
#        p = [random.uniform(-7,7), random.uniform(-4,4)]
#        fixedPoints.append(p)

    #processPoints(fixedPoints, 10)


#    with open("/home/jim/hermes_dav/user/Jim/Chad_Stores_Info_Current_2015_rnd_loc_6.csv", "r") as f:
    with open("/home/jim/hermes_dav/user/Jim/Kenya_geocoordinates_final_rnd_loc_v7.csv", "r") as f:
        (keys,stores) = csv_tools.parseCSV(f)
    csv_tools.castColumn(stores, 'Latitude', (csv_tools.castTypes.EMPTY_IS_NULL_STRING,
                                              csv_tools.castTypes.FLOAT))
    csv_tools.castColumn(stores, 'Longitude', (csv_tools.castTypes.EMPTY_IS_NULL_STRING,
                                              csv_tools.castTypes.FLOAT))

    newStores = []
    needsProcessed = []
    for s in stores:
        cat = s['Function']
        if cat == 'Central' or cat == 'Central Store' or cat == 'Region' or cat == 'District':
            newStores.extend(processStores(needsProcessed))
            #print newStores
            needsProcessed = []
            with open("/home/jim/hermes_dav/user/Jim/Kenya_geocoordinates_final_rnd_loc_v8.csv", "w") as f:
                csv_tools.writeCSV(f, keys, newStores)
        if cat == 'Central' or cat == 'Central Store' or cat == 'Region':
            newStores.append(setLatLon(s))
            continue
        needsProcessed.append(s)

    newStores.extend(processStores(needsProcessed))


    with open("/home/jim/hermes_dav/user/Jim/Kenya_geocoordinates_final_rnd_loc_v8.csv", "w") as f:
        csv_tools.writeCSV(f, keys, newStores)

            


if __name__=="__main__":
    main()
