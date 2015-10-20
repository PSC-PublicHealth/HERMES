#! /usr/bin/env python

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

"""
This tool provides test routines for warehouse.share3_calculateOwnerStorageFillRatios
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import ipath

import warehouse

"Provides a few test routines"
import abstractbaseclasses
import globals
import sampler
import typemanager
import storagetypes
import peopletypes
from peopletypes import genericPeopleTypeName
import trackabletypes
import trucktypes
import vaccinetypes
import icetypes
import packagetypes
import fridgetypes
import input
import storagemodel
import packagingmodel
import util
from math import pi
import random

#globals.deterministic = True

warehouse.DEBUG = True


def buildMockTypeManager(userInput, sim, vacList=None, 
                         coldBoxSizes={'freezer':5.0,'cooler':5.0,'roomtemperature':5.0}):
    verbose = debug = False
    typeManager= typemanager.TypeManager([], verbose=verbose, debug=debug, sim=sim)
    trackableTypes = trackabletypes.TrackableTypeManager(typeManager)
    # Import the storage type names and make them active;
    # they are needed in parsing files below.
    for stn in storagetypes.storageTypeNames:
        typeManager.addType({"Name": stn}, storagetypes.StorageType,
                                 verbose, debug)
        typeManager.getTypeByName(stn)
      
    typeManager.addType({"Name": "outdoorDiscard"}, storagetypes.StorageType,
                             verbose, debug)
    storagetypes.OUTDOORS = typeManager.getTypeByName("outdoorDiscard")


    sourceList = [({'Name': peopletypes.genericPeopleTypeName},
                   None, peopletypes.PeopleType),]

    sourceList += [([{"Name":"VAC1","DisplayName":"V1",
                      "Doses per vial":2,
                      "Packed vol/dose(cc) of vaccine":1.23,
                      "Packed vol/dose(cc) of diluent":4.46,
                      "Doses/person":1,"LifetimeFreezerDays":1.23,
                      "LifetimeCoolerDays":672,
                      "LifetimeRoomTempDays":0.02,
                      "LifetimeOpenDays":0.25,
                      "RandomKey":1000},
                     {"Name":"VAC2","DisplayName":"V2",
                      "Doses per vial":2,
                      "Packed vol/dose(cc) of vaccine":1.23,
                      "Packed vol/dose(cc) of diluent":4.46,
                      "Doses/person":1,
                      "LifetimeFreezerDays":200.0,
                      "LifetimeCoolerDays":50,
                      "LifetimeRoomTempDays":0.02,
                      "LifetimeOpenDays":0.25,
                      "RandomKey":1000},
                     {"Name":"VAC3","DisplayName":"V3",
                      "Doses per vial":2,
                      "Packed vol/dose(cc) of vaccine":1.23,
                      "Packed vol/dose(cc) of diluent":4.46,
                      "Doses/person":1,
                      "LifetimeFreezerDays":1.23,
                      "LifetimeCoolerDays":50,
                      "LifetimeRoomTempDays":200,
                      "LifetimeOpenDays":0.25,
                      "RandomKey":1000},], 
                    vaccinetypes.VaccineType,vaccinetypes.DeliverableVaccineType)]
    
    if vacList is not None:
        sourceList += [(vacList, vaccinetypes.VaccineType,vaccinetypes.DeliverableVaccineType)]


    cbs = coldBoxSizes
    sourceList += [([{"Make":"mothernature", "Model": "outdoors", "Year":"U", "Energy":"U",
                      "roomtemperature":1000000000, "Name":"OUTDOORS",
                      "ClassName":"Fridge"},
                     {"Make":"mk", "Model":"mod", "Year":"2000", "Energy":"", 
                      "freezer":cbs['freezer'], 
                      "cooler":cbs['cooler'], 
                      "roomtemperature":cbs['roomtemperature'],
                      "Name":"coldbox_1", "ClassName":"ShippableFridge"},],
                    None, fridgetypes.FridgeType)]

    sourceList += [([{"Name":"truck1", "CoolVolumeCC":0, "Storage":"1*coldbox_1"},],
                    None, trucktypes.TruckType)]


    trackableTypes.importRecords(sourceList,
                                 verbose, debug)

    # dictionary of the individual type managers by subTypeKey
    tms = {c.subTypeKey: c(typeManager)
           for c in util.createSubclassIterator(typemanager.SubTypeManager)}

    # Pull in any package types not mentioned explicitly but contained in
    # package types that are mentioned
    for name in tms['packaging'].getAllValidTypeNames():
        pkgType = tms['packaging'].getTypeByName(name, activateFlag=False)
        tms['shippables'].getTypeByName(pkgType.containsStr,
                                        activateFlag=False).addPackageType(pkgType)

    return typeManager, tms


class _mockSim:
    """
    This is used to mock the sim parameter needed by DemandModels during testing.
    """
    def __init__(self, vacList=None, coldBoxSizes={'freezer':5.0,'cooler':5.0,'roomtemperature':5.0}):
        self.userInput = input.UserInput()
        self.userInput['limitedroomtemp'] = True
        self.typeManager, self.typeManagers = buildMockTypeManager(self.userInput, self, vacList, coldBoxSizes)

        for k,v in self.typeManagers.items():
            setattr(self, k, v)

        self.staticDemand = False
        self.randomRounder = util.RandomRounder(1234)
        self.verbose = False
        self.debug = False
        self.uniqueIdDict = {}
        self.perfect = False

    def buildTypeRecords(self, recList, whatType):
        for rec in recList: self.typeManager.addType(rec, whatType, False, False)

    def getUniqueString(self, base):
        """
        This is used by various components to generate names, primarily for debugging.
        If called with base='foo' (for example), it will return first 'foo0', then 'foo1',
        etc.
        """
        if not self.uniqueIdDict.has_key(base):
            self.uniqueIdDict[base]= 0
        retVal= "%s%d"%(base,self.uniqueIdDict[base])
        self.uniqueIdDict[base] += 1
        return retVal

    def now(self):
        return 1.2345


def stringFromVC(vc):
    if vc is None:
        return "None"
    else:
        l = [(v.name,v) for v in vc.keys()]
        l.sort()
        l = [v for name,v in l]
        s = ""
        for v in l: s += "%s:%s,"%(v.name,vc[v])
        if len(s): s= s[:-1]
        return s


def calcAvailableVolumes(truck, vc):
    incomingStorageBlocks = []
    for v, n in vc.getTupleList():
        if isinstance(v, abstractbaseclasses.CanStoreType):
            assert n == int(n), "Non-integral number of fridges"
            storageCapacityInfo = v.getStorageCapacityInfo()
            for st, vol in storageCapacityInfo:
                for _ in xrange(int(n)):
                    incomingStorageBlocks.append(fridgetypes.Fridge.StorageBlock(truck, st, vol))
    incomingStorageBlocks = truck.filterStorageBlocks(incomingStorageBlocks)

    fAvail = 0.0
    cAvail = 0.0
    wAvail = 0.0
    for sB in truck.getStorageBlocks() + incomingStorageBlocks:
        if sB.volAvail < 100000000:  # avoid discard storage
            if sB.storageType in truck.sim.storage.coolStorageList():
                cAvail += sB.volAvail
            elif sB.storageType == truck.sim.storage.roomtempStorage():
                wAvail += sB.volAvail
            else:
                assert(sB.storageType == truck.sim.storage.frozenStorage())
                fAvail += sB.volAvail

    return fAvail, cAvail, wAvail


def calcStats(truck, vcList, vcReq):
    facRate_score = 0
    for vc, facAttr in zip(vcList, ('freezerFac','coolerFac','roomtempFac')):
        totVol = 0.0
        for v,r in vc.items():
            req = vcReq[v]
            volPerVial = v.dosesPerVial * v.ccPerDose
            vials = r * req
            totVol += volPerVial * vials
        

        for v,r in vc.items():
            req = vcReq[v]
            volPerVial = v.dosesPerVial * v.ccPerDose
            vials = r * req
            vol = volPerVial * vials
            fac = getattr(v, facAttr)

            facRate_score += fac * r

    scores = {'facRate': facRate_score}
    return scores

    


def calcVolumesUsed(truck, sM, fVC, cVC, wVC):
    fTot = 0
    cTot = 0
    wTot = 0
    lifetimes = []
    fShares = []
    fLabels = []
    cShares = []
    cLabels = []
    wShares = []
    wLabels = []
    for v, frac in fVC.items():
        volPerVial = v.dosesPerVial * v.ccPerDose
        if sM.getStoreVaccinesWithDiluent(v):
            volPerVial += v.dosesPerVial * v.ccDiluentPerDose
        deltaV = frac * vc[v] * volPerVial
        fTot += deltaV
        if frac > 0.0:
            lifetimes.append(1.0/v.freezerFac)
            fShares.append(deltaV)
            fLabels.append(v.name)

    for v, frac in cVC.items():
        volPerVial = v.dosesPerVial * v.ccPerDose
        if sM.getStoreVaccinesWithDiluent(v):
            volPerVial += v.dosesPerVial * v.ccDiluentPerDose
        deltaV = frac * vc[v] * volPerVial
        cTot += deltaV
        if frac > 0.0:
            lifetimes.append(1.0/v.coolerFac)
            cShares.append(deltaV)
            cLabels.append(v.name)

    for v, frac in wVC.items():
        volPerVial = v.dosesPerVial * v.ccPerDose
        if sM.getStoreVaccinesWithDiluent(v):
            volPerVial += v.dosesPerVial * v.ccDiluentPerDose
        deltaV = frac * vc[v] * volPerVial
        wTot += deltaV
        if frac > 0.0:
            lifetimes.append(1.0/v.roomtempFac)
            wShares.append(deltaV)
            wLabels.append(v.name)

    return fTot, cTot, wTot, min(lifetimes), fShares, fLabels, cShares, cLabels, wShares, wLabels


def sharesToFracs(shares, totAvail, labels):
    fracs = [s/totAvail for s in shares]
    if sum(fracs) < 0.99999:
        fracs += [1.0 - sum(fracs)]
        labels += ['Empty']
    return fracs, labels

def makeVacRec(name, ltf=200.0, ltc=200.0, ltr=200.0, vol=1.0, dpv=1, other={}):
    vr = {"Name":name,
          "DisplayName":name,
          "LifetimeFreezerDays":ltf,
          "LifetimeCoolerDays":ltc,
          "LifetimeRoomTempDays":ltr,
          "Packed vol/dose(cc) of vaccine":vol,
          "Packed vol/dose(cc) of diluent":vol,
          "Doses per vial":dpv,
          "LifetimeOpenDays":0.25,
          "Doses/person":1,
          "RandomKey":1000}

    for k,v in other.items():
        vr[k] = v

    return vr

def rDur(flags, which):
    "generate a random lifetime or an almost 0 based on a flag"
    if flags & 1<<which:
        return random.uniform(50.0,400.0)
    return 0.04

def rDurs():
    """
    generate a set of three lifetimes for a good, where at least one 
    lifetime is long enough to survive some time in a supply chain
    """
    f = random.randint(1,7)
    return (rDur(f,0), rDur(f,1), rDur(f,2))

def calcVols(vcCt, vcRat):
    vol = 0.0
    for v,r in vcRat.items():
        n = vcCt[v] * r
        volPerVial = v.dosesPerVial * v.ccPerDose
        vol += volPerVial * n
    return vol

def metrics(vc, fVc, cVc, wVc):
    pass


def chartCollection(vcList, vcReq, axList):
    for vc, ax, facAttr in zip(vcList, axList, ('freezerFac','coolerFac','roomtempFac')):
        totVol = 0.0
        for v,r in vc.items():
            req = vcReq[v]
            volPerVial = v.dosesPerVial * v.ccPerDose
            vials = r * req
            totVol += volPerVial * vials
        
        theta = []
        volWid = []
        color = []
        height = []

        for v,r in vc.items():
            color.append(float(v.name[1])/10.0)
            req = vcReq[v]
            volPerVial = v.dosesPerVial * v.ccPerDose
            vials = r * req
            vol = volPerVial * vials
            volWid.append(vol/totVol*2*pi)
            height.append(1/getattr(v, facAttr))
        curT = 0.0
        for vw in volWid:
            theta.append(curT)
            curT += vw
        bars = ax.bar(theta, height, width=volWid, bottom=0.0)
        for c, bar in zip(color, bars):
            bar.set_facecolor(cm.jet(c))
            bar.set_alpha(0.5)
            

def runRandomTestCase(vCt=10):
    """
    run a random test case
    vc is number of vaccines to try to fit
    """
    scores = []
    vRecs = []
    for i in xrange(vCt):
        f,c,r = rDurs()
        vRecs.append(makeVacRec("v%d"%i, f, c, r, random.uniform(0.5, 10.0)))

    cbSizes = {'freezer':random.uniform(0,10.0), 
               'cooler':random.uniform(0,10.0),
               'roomtemperature':random.uniform(0,10.0)}

    sim = _mockSim(vRecs, cbSizes)
    sM = storagemodel.StorageModel(False)
    pM = packagingmodel.SimplePackagingModel()
    
    tM = sim.typeManager
    
    truckType = tM.getTypeByName("truck1", sim=sim)
    truck = truckType.createInstance()
    truck.storageModel = sM
    truck.packagingModel = pM
    
    vax = [tM.getTypeByName("v%d"%i) for i in xrange(vCt)]
    vc = sim.shippables.getCollection()
    for i in xrange(vCt):
        vc += sim.shippables.getCollection([(vax[i], random.randrange(1000))])
    
    print vc
#    fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatiosPreferred(truck, vc, False)
    fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatiosSimple(truck, vc, False)
    print fVC
    print cVC
    print wVC
    print cbSizes
    print calcVols(vc, fVC)
    print calcVols(vc, cVC)
    print calcVols(vc, wVC)
    scores.append(calcStats(truck, (fVC,cVC,wVC), vc))
    

    warehouse.DEBUG = False
    fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatios(truck, vc, False)
    print fVC
    print cVC
    print wVC
    print cbSizes
    print calcVols(vc, fVC)
    print calcVols(vc, cVC)
    print calcVols(vc, wVC)
    if calcVols(vc, fVC) > cbSizes['freezer'] * 1000.1:
        print("freezer alloc too high")
        exit()
    if calcVols(vc, cVC) > cbSizes['cooler'] * 1000.1:
        print("cooler alloc too high")
        exit()
    if calcVols(vc, wVC) > cbSizes['roomtemperature'] * 1000.1:
        print("roomtemperature alloc too high")
        exit()
    scores.append(calcStats(truck, (fVC,cVC,wVC), vc))

    warehouse.DEBUG = False
    fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatiosPreferred(truck, vc, False)
    print fVC
    print cVC
    print wVC
    print cbSizes
    print calcVols(vc, fVC)
    print calcVols(vc, cVC)
    print calcVols(vc, wVC)
    if calcVols(vc, fVC) > cbSizes['freezer'] * 1000.1:
        print("freezer alloc too high")
        exit()
    if calcVols(vc, cVC) > cbSizes['cooler'] * 1000.1:
        print("cooler alloc too high")
        exit()
    if calcVols(vc, wVC) > cbSizes['roomtemperature'] * 1000.1:
        print("roomtemperature alloc too high")
        exit()
    scores.append(calcStats(truck, (fVC,cVC,wVC), vc))

    return scores


def chartRandomTestCase(vCt=10, caseNum=1):
    """
    run a random test case
    vc is number of vaccines to try to fit
    """

    figs, axes = plt.subplots(nrows=3, ncols=3,subplot_kw=dict(polar=True))


    vRecs = []
    for i in xrange(vCt):
        f,c,r = rDurs()
        vRecs.append(makeVacRec("v%d"%i, f, c, r, random.uniform(0.5, 10.0)))

    cbSizes = {'freezer':random.uniform(0,10.0), 
               'cooler':random.uniform(0,10.0),
               'roomtemperature':random.uniform(0,10.0)}

    sim = _mockSim(vRecs, cbSizes)
    sM = storagemodel.StorageModel(False)
    pM = packagingmodel.SimplePackagingModel()
    
    tM = sim.typeManager
    
    truckType = tM.getTypeByName("truck1", sim=sim)
    truck = truckType.createInstance()
    truck.storageModel = sM
    truck.packagingModel = pM
    
    vax = [tM.getTypeByName("v%d"%i) for i in xrange(vCt)]
    vc = sim.shippables.getCollection()
    for i in xrange(vCt):
        vc += sim.shippables.getCollection([(vax[i], random.randrange(1000))])
    
    print vc
#    fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatiosPreferred(truck, vc, False)
    fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatiosSimple(truck, vc, False)
    print fVC
    print cVC
    print wVC
    print cbSizes
    print calcVols(vc, fVC)
    print calcVols(vc, cVC)
    print calcVols(vc, wVC)
    chartCollection((fVC, cVC, wVC), vc, (axes[0,0], axes[0,1], axes[0,2]))
    axes[0,0].set_title('simple freeze')
    axes[0,1].set_title('simple cool')
    axes[0,2].set_title('simple warm')

    warehouse.DEBUG = False
    fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatios(truck, vc, False)
    print fVC
    print cVC
    print wVC
    print cbSizes
    print calcVols(vc, fVC)
    print calcVols(vc, cVC)
    print calcVols(vc, wVC)
    if calcVols(vc, fVC) > cbSizes['freezer'] * 1000.1:
        print("freezer alloc too high")
        exit()
    if calcVols(vc, cVC) > cbSizes['cooler'] * 1000.1:
        print("cooler alloc too high")
        exit()
    if calcVols(vc, wVC) > cbSizes['roomtemperature'] * 1000.1:
        print("roomtemperature alloc too high")
        exit()
 
    chartCollection((fVC, cVC, wVC), vc, (axes[1,0], axes[1,1], axes[1,2]))
    axes[1,0].set_title('l1 freeze')
    axes[1,1].set_title('l1 cool')
    axes[1,2].set_title('l1 warm')

    warehouse.DEBUG = False
    fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatiosPreferred(truck, vc, False)
    print fVC
    print cVC
    print wVC
    print cbSizes
    print calcVols(vc, fVC)
    print calcVols(vc, cVC)
    print calcVols(vc, wVC)
    if calcVols(vc, fVC) > cbSizes['freezer'] * 1000.1:
        print("freezer alloc too high")
        exit()
    if calcVols(vc, cVC) > cbSizes['cooler'] * 1000.1:
        print("cooler alloc too high")
        exit()
    if calcVols(vc, wVC) > cbSizes['roomtemperature'] * 1000.1:
        print("roomtemperature alloc too high")
        exit()
    chartCollection((fVC, cVC, wVC), vc, (axes[2,0], axes[2,1], axes[2,2]))
    axes[2,0].set_title('l2 freeze')
    axes[2,1].set_title('l2 cool')
    axes[2,2].set_title('l2 warm')
    figs.savefig('blah')

          
#chartRandomTestCase()


sumFr10=0
sumFr21=0
sumFr20=0
betterCount = 0
cases = 10000
for i in xrange(cases):
    scores = runRandomTestCase()
    fr0 = scores[0]['facRate']
    fr1 = scores[1]['facRate']
    fr2 = scores[2]['facRate']

    fr10 = fr0 / fr1
    fr21 = fr1 / fr2
    fr20 = fr0 / fr2

    sumFr10 += fr10
    sumFr21 += fr21
    sumFr20 += fr20
    if fr20 > 1.0:
        betterCount += 1
    
    print "facRates"
    print fr0, fr1, fr2
    print "facCompares"
    print fr10, fr21, fr20

print sumFr10 / cases
print sumFr21 / cases
print sumFr20 / cases
print float(betterCount) / cases




exit()

sim = _mockSim()
sM = storagemodel.StorageModel(False)
pM = packagingmodel.SimplePackagingModel()

tM = sim.typeManager

truckType = tM.getTypeByName("truck1", sim=sim)
truck = truckType.createInstance()
truck.storageModel = sM
truck.packagingModel = pM

v1 = tM.getTypeByName('VAC1')
v2 = tM.getTypeByName('VAC2')
v3 = tM.getTypeByName('VAC3')
vc = sim.shippables.getCollection([(v1, 5000), (v2, 3333), (v3, 10555)])
print vc



figs1, axes1 = plt.subplots(nrows=1, ncols=1)
figs2, axes2 = plt.subplots(nrows=2, ncols=3)
xVals = []
yVals = []
areas = []
colors = []

fAvail, cAvail, wAvail = calcAvailableVolumes(truck, vc)

fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatios(truck, vc, False)
print fVC
print cVC
print wVC
fTot, cTot, wTot, minLifetime, fShares, fLabels, cShares, cLabels, wShares, wLabels = \
    calcVolumesUsed(truck, sM, fVC, cVC, wVC)
fFracs, fLabels = sharesToFracs(fShares, fTot, fLabels)
cFracs, cLabels = sharesToFracs(cShares, cTot, cLabels)
wFracs, wLabels = sharesToFracs(wShares, wTot, wLabels)
xVals.append(cTot/cAvail)
yVals.append(wTot/wAvail)
areas.append(100*minLifetime)
colors.append('blue')
axes2[0, 0].pie(fFracs, labels=fLabels, autopct='%1.1f%%', startangle=90)
axes2[0, 0].set_title('Freeze')
axes2[0, 0].set_aspect('equal')
axes2[0, 1].pie(cFracs, labels=cLabels, autopct='%1.1f%%', startangle=90)
axes2[0, 1].set_title('Cold')
axes2[0, 1].set_aspect('equal')
axes2[0, 2].pie(wFracs, labels=wLabels, autopct='%1.1f%%', startangle=90)
axes2[0, 2].set_title('Warm')
axes2[0, 2].set_aspect('equal')

fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatiosPreferred(truck, vc, False)
print fVC
print cVC
print wVC
fTot, cTot, wTot, minLifetime, fShares, fLabels, cShares, cLabels, wShares, wLabels = \
    calcVolumesUsed(truck, sM, fVC, cVC, wVC)
fFracs, fLabels = sharesToFracs(fShares, fTot, fLabels)
cFracs, cLabels = sharesToFracs(cShares, cTot, cLabels)
wFracs, wLabels = sharesToFracs(wShares, wTot, wLabels)
xVals.append(cTot/cAvail)
yVals.append(wTot/wAvail)
areas.append(100*minLifetime)
colors.append('green')
axes2[1, 0].pie(fFracs, labels=fLabels, autopct='%1.1f%%', startangle=90)
axes2[1, 0].set_title('Freeze')
axes2[1, 0].set_aspect('equal')
axes2[1, 1].pie(cFracs, labels=cLabels, autopct='%1.1f%%', startangle=90)
axes2[1, 1].set_title('Cold')
axes2[1, 1].set_aspect('equal')
axes2[1, 2].pie(wFracs, labels=wLabels, autopct='%1.1f%%', startangle=90)
axes2[1, 2].set_title('Warm')
axes2[1, 2].set_aspect('equal')

axes1.scatter(xVals, yVals, s=areas, c=colors, marker='o')
axes1.set_xlim(0.0, max(2.0, max(xVals)))
axes1.set_ylim(0.0, max(2.0, max(yVals)))
axes1.plot([0.0, 1.0, 1.0], [1.0, 1.0, 0.0], '--', color='black')
axes1.set_aspect('equal')

# figs1.tight_layout()
# figs2.tight_layout()
#plt.show()
figs1.savefig('blah1')
figs2.savefig('blah2')
