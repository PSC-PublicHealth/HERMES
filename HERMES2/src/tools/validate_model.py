# Copyright C 2010, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

_hermes_svn_id_="$Id: validatee_model.py 1053 2012-08-16 17:47:26Z stbrown $"

import ipath
import shadow_network as shd
from shadow_network_db_api import ShdNetworkDB
import input
from copy import copy,deepcopy

import sys,string
import optparse

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][--storefile][--routefile][--replacementfile][--consolidatestorage]
    """)
    parser.add_option("-d","--use_db",type=int,default=None)
    parser.add_option("-i","--input",default=None)

    opts, args=parser.parse_args()

    return {'usedb':opts.use_db,
            'input':opts.input}

class CurrentTest:
    currentTest = None

    def __init__(self, testString):
        self.oldCurrentTest = CurrentTest.currentTest
        currentTest = testString

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        CurrentTest.currentTest = self.oldCurrentTest

class VMC:
    "validate model constants"
    STORE = 'W'
    ROUTE = 'R'
    GLOBAL = 'G'
    
def descNode(node):
    "return a descriptor for a node"
    if isinstance(node, shd.ShdStore):
        return (VMC.STORE, node.idcode, 'store %s (%s)'%(node.NAME, node.idcode))
    if isinstance(node, shd.ShdRoute):
        return (VMC.ROUTE, node.RouteName, 'route %s'%node.RouteName)
    return (VMC.GLOBAL, node, node)


class Validator:
    availableTests = ["checkStorage","checkUseVials",
                      "checkDemands","checkStoreVehicles",
                      "checkRouteDistances"]
    def __init__(self,_shdNtwk):
        self.warnings = []
        self.fatals = []
        self.tests = []
        self.invalidTests = []
        self._shdNtwk = _shdNtwk

    def registerTest(self,testStr):
        invalidTests = []
        if testStr == "all":
            for testStr in self.availableTests:
                self.tests.append(testStr)
        else:
            if testStr in self.availableTests:
                self.tests.append(testStr)
            else:
                invalidTests.append(testStr)


    def printAvailableTestsMessage(self):
        if len(self.invalidTests) > 0:
            print "Tests: "
            for testStr in self.invalidTests:
                print "    %s"%testStr

            print " "
            print "The Tests Available Through the Validator are:"
            for testStr in self.availableTests:
                print "%s"%testStr

            print " "
            if len(self.tests) > 0:
                print "Will proceed with the valid specified tests"

            else:
                raise RuntimeError("No valid tests have been specified.")
        print "Performing the following tests"
        for testStr in self.tests:
            print "%s"%testStr

    def warning(self, node, message):
        (nType, nId, nText) = descNode(node)
        self.warnings.append((nType, nId, nText, CurrentTest.currentTest, message))

    def fatal(self, node, message):
        (nType, nId, nText) = descNode(node)
        self.fatals.append((nType, nId, nText, CurrentTest.currentTest, message))

    def XXXregisterWarning(self,testStr,message):
        self.warnings.append((testStr,message))

    def XXXregisterFatals(self,testStr,message):
        self.fatals.append((testStr,message))


    def runAvailableTests(self):
        import time

        self.printAvailableTestsMessage()

        for testStr in self.tests:
            if testStr not in self.availableTests:
                continue
            with CurrentTest(testStr):
                fn = getattr(self, testStr)
                time1 = time.time()
                fn()
                time2 = time.time()
                print "%s took %10.2f seconds"%(testStr, time2-time1)


    def getMessageList(self):
        messList = []

        if len(self.warnings) == 0:
            messList.append({'testname':'All','messtype':'Warnings','message':'None'})
        else:
            for nType, nId, nText, topic,message in self.warnings:
                messList.append({'testname':topic,'messtype':'Warnings','message':"%s: %s"%(nText, message)})

        if len(self.fatals) == 0:
            messList.append({'testname':'All','messtype':'Fatal Errors','message':'None'})
        else:
            for nType, nId, nText, topic,message in self.fatals:
                messList.append({'test':topic,'messtype':'Fatal Errors','message':"%s: %s"%(nText, message)})

        return messList

    def printReport(self):
        print "Validation Report: "
        print "--------------------------------------------------------------------------"
        print "  Warnings"
        print "--------------------------------------------------------------------------"
        if len(self.warnings) == 0:
            print "   There are no Warnings from this model."
        else:
            print "Category                 Message"
            for (nType, nId, nText, topic, message) in self.warnings:
                print "%-20s%s: %s"%(topic, nText, message)
        print "--------------------------------------------------------------------------"
        print "  Fatal Errors"
        print "--------------------------------------------------------------------------"
        if len(self.fatals) == 0:
            print "   There are no Fatals from this model."
        else:
            print "Category                 Message"
            for (nType, nId, nText, topic, message) in self.fatals:
                print "%-20s%s: %s"%(topic, nText, message)

    def checkStorage(self):
        for storeId,store in self._shdNtwk.stores.items():
            ### getStorageDevices
            hasStorage = False
            hasCoolerStorage = False
            totalStorage = {"cooler":0.0,"freezer":0.0}
            for device in store.inventory:
                if type(device.invType) != shd.ShdStorageType and\
                    type(device.invType) != shd.ShdTruckType:
                    self.fatal(store, "contains an invalid Storage Device %s"%device.invName)
                if type(device.invType)== shd.ShdStorageType:
                    hasStorage = True
                    totalStorage["cooler"] += device.invType.cooler
                    if device.invType.cooler > 0.0:
                        hasCoolerStorage = True
                    totalStorage["freezer"] += device.invType.freezer

            ### Do some consistency Checks
            if store.FUNCTION == "Distribution":
                if hasStorage is False:
                    self.fatal(store, "has a FUNCTION of Distribution, but no storage")
                if hasCoolerStorage is False:
                    self.fatal(store, "has a FUNCTION of Distribution, but no 2-8 C storage")
            if store.FUNCTION == "Administration":
                if hasStorage is True and hasCoolerStorage is False:
                    self.fatal(store, "has a FUNCTION of Administration, but no 2-8 C storage")

                if hasStorage is False:
                    if len(store.clients()) > 0:
                        self.fatal(store, "has no storage, and has clients, this is an invalid configuration implying an AttachedClinic entered incorrectly.")
                    elif len(store.suppliers()) > 1:
                        self.fatal(store, "has no storage and more than one supplier, which is invalid")
                    elif len(store.suppliers()) == 0:
                        self.warning(store, "is an implied AttachedClinic, which is deprecated")
                    elif  store.suppliers()[0][1].Type != "attached":
                        self.fatal(store, "has no storage but is not an AttachedClinic")

    def checkUseVials(self):
        for storeId,store in self._shdNtwk.stores.items():
            if store.FUNCTION == "Administration":
                if store.UseVialsInterval == 0:
                    self.warning(store, "has FUNCTION of Administration, but a UseVialInterval set to 0")
 
    def checkDemands(self):
        peopleTypeExclusionList = ["Service1"]
        for storeId,store in self._shdNtwk.stores.items():
                ### There should be no demand
            hasDemand = False
            for demand in store.demand:
                if demand.invName not in peopleTypeExclusionList:
                    if demand.count > 0:
                        hasDemand = True
            if store.FUNCTION == "Distribution" and hasDemand:
                self.warning(store, "has a FUNCTION of Distribution, but has population to serve")

            if store.FUNCTION == "Administration" and hasDemand is False:
                self.fatal(store, "has a FUNCTION of Administration, but has no population to serve")

    def checkStoreVehicles(self):
        for storeId,store in self._shdNtwk.stores.items():
            ## Check to see if this store is an origin of a supply route
            for supplierStore,supplierRoute in store.suppliers():
                hasThisVehicle = False
                if supplierRoute.stops[0].store.idcode == storeId:
                    # This is the origin of this route, see what vehicle is used
                    vehicle = supplierRoute.TruckType
                    # see if this vehicle exists at the store
                    hasThisVehicle = False
                    for device in store.inventory:
                        if device.invName == vehicle:
                            hasThisVehicle = True

                    if hasThisVehicle is False:
                        self.fatal(store, "is the origin of supply Route %s with vehicle %s, but does not have this vehicle in its inventory"\
                                       %(supplierRoute.RouteName,vehicle))

            for clientRoute in store.clientRoutes():
                hasThisVehicle = False
                if clientRoute.stops[0].store.idcode == storeId and clientRoute.Type != "attached":
                    # This is the origin of this route, see what vehicle is used
                    vehicle = clientRoute.TruckType
                    # see if this vehicle exists at the store
                    hasThisVehicle = False
                    for device in store.inventory:
                        if device.invName == vehicle:
                            hasThisVehicle = True
                    if hasThisVehicle is False:
                        self.fatal(store, "is the origin of client Route %s with vehicle %s, but does not have this vehicle in its inventory"\
                                       %(clientRoute.RouteName,vehicle))

    def checkRouteDistances(self):
        for routeId,route in self._shdNtwk.routes.items():
            if route.Type != "attached":
                for stop in route.stops[1:]:
                    if stop.TransitHours == 0:
                        self.warning(route, "stop %d has 0 hours for TransitTime"%route.stops.index(stop))

                for stop in route.stops:
                    dist = stop.DistanceKM
                    if dist is None or dist == 0:
                        self.warning(route, "stop %d has no DistanceKM associated with it"%route.stops.index(stop))

                    #if stop.TransitHours != 0 and stop.DistanceKM != 0 and stop.DistanceKM /stop.TransitHours > 80:
                    #    self.registerWarning("checkRouteDistances","Route %s stop %d has a vehicle that will travel greater than 80 KM/Hour"%(route.RouteName,route.stops.index(stop)))
if __name__ == '__main__':

    inputDict = parseCommandLine()

    if inputDict['usedb']:
        import session_support_wrapper as session_support
        import db_routines

        iface = db_routines.DbInterface(echo=False)
        session = iface.Session()
        shdNtwkDB = ShdNetworkDB(session,inputDict['usedb'])
        shdNtwkDB.useShadowNet()
        shdNtwk = shdNtwkDB._net
    else:
        userInput= input.UserInput(inputDict['input'],False)
        shdTypes = shd.loadShdTypes(userInput,input.UnifiedInput())
        shdNtwk = shd.loadShdNetwork(userInput, shdTypes, "Bihar")

    validator = Validator(shdNtwk)
    validator.registerTest("all")
    validator.runAvailableTests()
    validator.printReport()

