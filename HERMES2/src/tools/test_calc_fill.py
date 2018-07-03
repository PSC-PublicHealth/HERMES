#! /usr/bin/env python

"""
This tool provides test routines for warehouse.share3_calculateOwnerStorageFillRatios
"""

import numpy as np
import matplotlib.pyplot as plt

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
#globals.deterministic = True

warehouse.DEBUG = True


def buildMockTypeManager(userInput, sim):
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


    sourceList += [([{"Make":"mothernature", "Model": "outdoors", "Year":"U", "Energy":"U",
                      "roomtemperature":1000000000, "Name":"OUTDOORS",
                      "ClassName":"Fridge"},
                     {"Make":"mk", "Model":"mod", "Year":"2000", "Energy":"", 
                      "freezer":5.0, "cooler":3.0, "roomtemperature":6.0,
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
    def __init__(self):
        self.userInput = input.UserInput()
        self.userInput['limitedroomtemp'] = True
        self.typeManager, self.typeManagers = buildMockTypeManager(self.userInput, self)

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
plt.show()
