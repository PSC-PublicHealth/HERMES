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
import os.path
import sys

try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    # also need the directory above
    updir = os.path.join(cwd, '..')
    if updir not in sys.path:
        sys.path.append(updir)
except:
    pass



import math, random
import copy

import hermes_data
import util
import csv_tools



distMemo = {}

def distance(p1, p2):
    m = (p1[0],p1[1],p2[0],p2[1])
    try:
        return distMemo[m]
    except:
        ret = util.longitudeLatitudeSep(*m)
        distMemo[m] = ret
        return ret



class Loop:
    def __init__(self, hub, points, noCalc=False):
        self.copy = self.__copy__
        self.hub = hub
        self.points = points
        if noCalc:
            return
        (self.distance,self.route) = self.bestRoute()
        self.score = self.calcScore()

    def __copy__(self):
        cp = Loop(self.hub, self.points[:], True)
        cp.distance = self.distance
        cp.route = self.route[:]
        cp.score = self.score
        return cp

    def bestRoute(self):
        queue = [(0, [self.hub], self.hub, self.points)]
        newQ = []
        for i in xrange(len(self.points) + 1):
            for entry in queue:
                (dist, route, lastPoint, remainingPoints) = entry
                if (len(remainingPoints) == 0):
                    remainingPoints = [self.hub]
                for n,p in enumerate(remainingPoints):
                    nDist = dist + distance(lastPoint, p)
                    nRoute = route[:] + [p]
                    nRemainingPoints = remainingPoints[:n] + remainingPoints[n+1:]
                    newQ.append([nDist, nRoute, p, nRemainingPoints])
            newQ.sort(key=lambda x: x[0])
            queue = newQ
            queue = queue[:200]
            #print queue
            newQ = []

        (dist, route, lastPoint, remainingPoints) = queue[0]
        return (dist,route)

    def calcScore(self):
        # for the moment just use the distance as our scoring method
        # this is acceptable if stores per loop is constant but could
        # probably be made better.  ie it would be better if half the
        # loops took 2 days and half took 1 day rather than all taking
        # 1.5 days in cases with a per diem.
        return self.distance

        # for more complicated loop generating rules we need better scoring methods
        # this was an attempt from earlier
        baseScore = 200.0     # base cost of having a new loop
        baseScore += self.distance
        baseScore += len(self.points) * 10
        if len(self.points) > 5:
            xp = len(self.points) - 5
            baseScore += xp * xp * xp * 10 
        score = baseScore
        if baseScore > 450:
            score += 100
        if baseScore > 700:
            score += 300
        if baseScore > 950:
            score += baseScore * baseScore
        return score


class LoopSet:
    def __init__(self, hub, points, pointsPerLoop, noCalc=False):
        self.copy = self.__copy__
        if noCalc:
            return
        self.loops = []
        self.hub = hub

        #STB - This needs to be a ceiling, so taht it is big enough for odd number loops always
        loopct= int(math.ceil(float(len(points)) / float(pointsPerLoop)))
        protoLoops = []
        for i in xrange(loopct):
            protoLoops.append([])

        pl = 0
        for p in points:
            protoLoops[pl].append(p)
            pl += 1
            if pl == loopct:
                pl = 0

        

        for prl in protoLoops:
            self.loops.append(Loop(self.hub, prl))
        
        self.score = 0.0
        for l in self.loops:
            self.score += l.score

    def __copy__(self):
        cp = LoopSet(None, None, None, True)
        cp.hub = self.hub
        cp.loops = []
        for l in self.loops:
            cp.loops.append(l.copy())
        cp.score = self.score
        return cp

    def perturb(self, debug = False):
        # we have several options here:
        #   swap two locations between loops
        #   move a location to another loop
        #   split a loop into two
        #   collapse two loops into one
        
        # we should probably weight the different options
        while(1):
            # all of our perturbations can affect up to two loops
            li = [None, None]
            nl = [None, None]


            #option = random.randrange(4)
            option = 0
            
            if option == 0:
                # swap two locations
                if len(self.loops) < 1:
                    print "number of loops is %d"%(len(self.loops))
                    return
                
                # pick two loops
                # Must make a special case when there is only one loop
                if len(self.loops) == 1:
                    l1 = self.loops[0]
                    pts = l1.points[:]
                    pn1 = random.randrange(len(pts))
                    pn2 = random.randrange(len(pts))

                    p1 = pts[pn1]
                    pts[pn1] = pts[pn2]
                    pts[pn2] = p1
                    nl[0] = Loop(l1.hub,pts)
                else:
                    li[0] = random.randrange(len(self.loops))
                    li[1] = random.randrange(len(self.loops))
                    if li[0] == li[1]:
                        continue

                    l1 = self.loops[li[0]]
                    l2 = self.loops[li[1]]
                    if len(l1.points) == 1 and len(l2.points) == 1:
                        continue

                    # grab shallow copies of the points in those loops
                    pts1 = l1.points[:]
                    pts2 = l2.points[:]

                    # pick two points within those two loops
                    pn1 = random.randrange(len(pts1))
                    pn2 = random.randrange(len(pts2))

                    # swap the points and make new loops
                    p1 = pts1[pn1]
                    pts1[pn1] = pts2[pn2]
                    pts2[pn2] = p1
                    nl[0] = Loop(l1.hub, pts1)
                    nl[1] = Loop(l2.hub, pts2)
            elif option == 1:
                # move a location to another loop

                # pick two loops
                li[0] = random.randrange(len(self.loops))
                li[1] = random.randrange(len(self.loops))
                if li[0] == li[1]:
                    continue

                l1 = self.loops[li[0]]
                if len(l1.points) == 1:
                    continue

                l2 = self.loops[li[1]]

                # pick a point within that first loop
                pn1 = random.randrange(len(l1.points))

                # make shallow copies of the lists of points
                pts1 = l1.points[:pn1] + l1.points[pn1+1:]
                pts2 = l2.points[:]

                # add the picked point to pts2
                pts2.append(l1.points[pn1])

                # and make loops
                nl[0] = Loop(l1.hub, pts1)
                nl[1] = Loop(l2.hub, pts2)

            elif option == 2:
                print "option 2"
                # split a loop into two

                # pick a loop
                li[0] = random.randrange(len(self.loops))
                l1 = self.loops[li[0]]
                if len(l1.points) == 1:
                    continue

                # split up the points
                # apparently randrange(1,1) won't work so...
                if len(l1.points) == 2:
                    split = 1
                else:
                    split = random.randrange(1, len(l1.points) - 1)
                pts1 = l1.points[:split]
                pts2 = l1.points[split:]

                # and make loops
                nl[0] = Loop(l1.hub, pts1)
                nl[1] = Loop(l1.hub, pts2)

            elif option == 3:
                print "option 3"
                # collapse two loops into one

                # pick two loops
                li[0] = random.randrange(len(self.loops))
                li[1] = random.randrange(len(self.loops))
                if li[0] == li[1]:
                    continue

                l1 = self.loops[li[0]]
                l2 = self.loops[li[1]]
                
                # take shallow copies of the points
                pts = l1.points[:] + l2.points[:]
                
                # and make a loop
                nl[0] = Loop(l1.hub, pts)


            # now we evaluate our change
            scoreDiff = 0
            for l in li:
                if l is not None:
                    scoreDiff -= self.loops[l].score
            for l in nl:
                if l is not None:
                    scoreDiff += l.score


            # if we've got a better score we keep regardless
            # if we've got a worse score, randomly keep it depending
            # on how bad it is
            #print 'scoreDiff = ' + str(scoreDiff)
            if scoreDiff > 0:
                newScore = self.score + scoreDiff
                r = random.uniform(0.0,1.0)
                fraction = self.score/newScore
                
                if (fraction * fraction * fraction) < r:
                    if debug:
                        print "randomly not choosing to accept this suboptimal perturbation"
                        print "score: %s, newScore: %s, fraction: %s, random: %s"%(self.score,
                                                                                   newScore,
                                                                                   self.score/newScore,
                                                                                   r)
                    return  # we'll call this a perturbation as well...
                else:
                    if debug:
                        print "choosing to take this one anyway!"
                        print "score: %s, newScore: %s, fraction: %s, random: %s"%(self.score,
                                                                                   newScore,
                                                                                   self.score/newScore,
                                                                                   r)
                    pass
            else:
                if debug:
                    print "accepting score diff of %s"%scoreDiff

            for i in xrange(2):
                if li[i] is not None and nl[i] is not None:
                    self.loops[li[i]] = nl[i]
                else:
                    if li[i] is not None:
                        loops = self.loops[:li[i]] + self.loops[li[i]+1:]
                        self.loops = loops
                    if nl[i] is not None:
                        self.loops.append(nl[i])

            self.score += scoreDiff

            # if we've gotten this far then we've made a single perturbation.
            # break out of the while loop (and just leave the function)
            return


def printRouteCSV(l):
    RouteName = None

    curLoc = l.route[0]
    for (i, nextLoc) in enumerate(l.route[1:]):
        cl = curLoc[2]
        nl = nextLoc[2]
        if RouteName is None:
            RouteName = "r%s_%s"%(cl['idcode'],nl['idcode'])
        Type = 'varpush'
        LocName = cl['NAME']
        idcode = cl['idcode']
        RouteOrder = '%s'%i
        TransitHours = 0.5 + distance(curLoc, nextLoc) / 50
        TruckType = 'N_4x4_truck'
        ShipIntervalDays = '28'
        ShipLatencyDays = '1'  # this will likely need changing
        PullOrderAmountDays = '0'
        Conditions = ''
        
        print "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%(RouteName,
                                                  Type,
                                                  LocName,
                                                  idcode,
                                                  RouteOrder,
                                                  TransitHours,
                                                  TruckType,
                                                  ShipIntervalDays,
                                                  ShipLatencyDays,
                                                  PullOrderAmountDays,
                                                  Conditions)

        # python loops really need a finally clause
        curLoc = nextLoc

        


def printRoute(l):
    print "Loop: %s (dist:%s)"%(l.score, l.distance)
    lastLoc = [l.route[0][0], l.route[0][1]]
    for p in l.route:
        s = p[2]
        name = s['NAME']
        id = s['idcode']
        loc = [p[0], p[1]]
        dist = distance(loc, lastLoc)

        print "     %s (%s): %s (%s)"%(name, id, loc, dist)

        lastLoc = loc



def printRoutes(ls):
    print ls
    for l in ls.loops:
        printRouteCSV(l)
        print
    print "total score: %s"%ls.score

storesOutputList = []
storesOutputFields = ['idcode', 'Storage']

routesOutputList = []
routesOutputFields = ['RouteName',
                      'Type',
                      'LocName',
                      'idcode',
                      'RouteOrder',
                      'TransitHours',
                      'TruckType',
                      'ShipIntervalDays',
                      'ShipLatencyDays',
                      'PullOrderAmountDays',
                      'Conditions']


def addFields(rec):
    for k in rec.keys():
        if k in ['stops','']:  # don't add these keys
            continue
        if k not in routesOutputFields:
            routesOutputFields.append(k)

def addRec(rec):
    addFields(rec)
    routesOutputList.append(rec)

def saveLegacyRoutes(hd, store):
    for rName in store['childRoutes']:
        r = hd.routes[rName]
        for stop in r['stops']:
            addRec(stop[3])

def saveLoopData(hd, loop, routeName, shipLatency):
    retShipLatency = shipLatency + 1
    l = loop
    curLoc = l.route[0]
    totTransit = 0
    dayTransit = 0
    totDistance = 0

    for i, nextLoc in enumerate(l.route[1:]):
        cl = curLoc[2]
        nl = nextLoc[2]

        d = distance(curLoc, nextLoc)
        totDistance += d
        transitTime = d * g['roadDistanceFactor'] / g['kmph']
        transitTime += g['stopTime']
        
        dayTransit += transitTime
        while 1:
            if dayTransit < g['shipHoursPerDay']:
                break
            transitTime += g['hoursPerDay'] - g['shipHoursPerDay']
            retShipLatency += 1
            dayTransit -= g['shipHoursPerDay']
            
        
        rec = {'RouteName':            routeName,
               'Type':                 g['routeType'],
               'LocName':              cl['NAME'],
               'idcode':               cl['idcode'],
               'RouteOrder':           '%d'%i,
               'TransitHours':         transitTime,
               'TruckType':            g['truckType'],
               'ShipIntervalDays':     g['shipIntervalDays'],
               'ShipLatencyDays':      shipLatency,
               'PullOrderAmountDays':  g['pullOrderAmountDays'],
               'Conditions':           g['conditions'],
               'distance':             d,
               'totDistance':          totDistance
               }

        addRec(rec)

        # python loops really need a finally clause
        curLoc = nextLoc

    return retShipLatency


def saveLoopSetData(hd, loopSet):
    hubId = loopSet.hub[2]['idcode']
    hubStorage = ''
    try:
        hubStorage = loopSet.hub[2]['Storage']
    except:
        pass

    nameBase = 'r%s_'%hubId
    
    shipLatency = g['shipLatencyDays']
    trucksNeeded = 1

    for i,l in enumerate(loopSet.loops):
        shipLatency = saveLoopData(hd, l, '%s%d'%(nameBase,i), shipLatency)
        if shipLatency > g['shipLatencyDays'] + g['shippingDaysPerInterval']:
            shipLatency = g['shipLatencyDays']
            trucksNeeded += 1
            print "need another truck"

    storageLine = hubStorage
    if len(hubStorage) > 0:
        storageLine += '+'
    storageLine += '%d*%s'%(trucksNeeded,g['truckType'])
    sRec = {'idcode':hubId,
            'Storage':storageLine}
    storesOutputList.append(sRec)
            

g = {'storesFile':"/Users/stbrown/Simulations/Benin_5days_loops/BeninStoreInfo_2012_wo.csv",
      'routesFile':"/Users/stbrown/Simulations/Benin_5days_loops/BeninRoutes.bcg.wo.csv",
      'peopleFile':"/Users/stbrown/Programs/HERMES2/master_data/unified/UnifiedPeopleTypeInfo.csv",
      'routesOutputFile':'newroutes.csv',
      'storesOutputFile':'newstores.csv',
      'category':'Commune',
      'routeType':'varPush',
      'truckType':'B_generic_4x4_commune_truck',
      'destsPerLoop':3,
      'roadDistanceFactor':1.36,
      'kmph':40,
      'stopTime':0.5,
      'shipHoursPerDay':8.0,
      'hoursPerDay':24.0,
      'shipIntervalDays':20,
      'shippingDaysPerInterval':20,
      'shipLatencyDays':1,
      'pullOrderAmountDays':0,
      'conditions':'',
      'iterationsPerLoopSet':10000,
      }

def main():

    hd = hermes_data.hermes_data(g['storesFile'], g['routesFile'], None, g['peopleFile'])

    for id,s in hd.stores.items():
        if s['CATEGORY'] != g['category']:
            saveLegacyRoutes(hd, s)
            continue

        hubLoc = [s['Longitude'], s['Latitude'], s]
        print "working on %s"%s['NAME']
        locList = []

        for cId in s['children']:
            c = hd.stores[cId]
            locList.append([c['Longitude'], c['Latitude'], c])
            print "adding %s"%c['NAME']


        print "starting"
        distMemo = {}  # reset the distMemo since we're not using any previous points
        ls = LoopSet(hubLoc, locList, g['destsPerLoop'])
        
        best_ls = ls.copy()
        best_score = ls.score
        #print best_score
        #printRoutes(best_ls)
        for i in xrange(g['iterationsPerLoopSet']):
            ls.perturb()
            if ls.score < best_score:
                best_ls = ls.copy()
                best_score = ls.score

        saveLoopSetData(hd, best_ls)


    with open(g['routesOutputFile'], "w") as f:
        csv_tools.writeCSV(f, routesOutputFields, routesOutputList)

    with open(g['storesOutputFile'], "w") as f:
        csv_tools.writeCSV(f, storesOutputFields, storesOutputList)









    

        
if __name__=="__main__":
    main()
