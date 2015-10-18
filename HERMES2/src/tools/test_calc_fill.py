import ipath

import warehouse




"Provides a few test routines"
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

fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatios(truck, vc, False)
print fVC
print cVC
print wVC
fVC, cVC, wVC = warehouse.share3_calculateOwnerStorageFillRatiosPreferred(truck, vc, False)
print fVC
print cVC
print wVC

