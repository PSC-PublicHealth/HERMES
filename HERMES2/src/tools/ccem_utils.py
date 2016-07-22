import pyodbc
import sys, os
from pprint import _id

# ## utility FUNCTIONS

def floatOrZero(value):
    try:
        fValue = float(value)
        return fValue
    except:
        return 0.0

def intOrZero(value):
    try:
        iValue = int(value)
        return iValue
    except:
        return 0.0   
    
def strOrUnknown(value):
    if value is None:
        return "UNKOWN"
    else:
        return value
    

# ## Classes

class AccessDB:
    def __init__(self, _accessFile):
        try:
        # # From https://github.com/mkleehammer/pyodbc/wiki/Connecting-to-Microsoft-Access
            self.conn = pyodbc.connect(r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' + 
                              r'DBQ={0}'.format(_accessFile))
            self.cursor = self.conn.cursor()
        
        except pyodbc.Error, err:
            raise RuntimeError("Problem connecting to the access database: {0}".format(err))
        
    
    def execute(self, SQLStatement):
        try:
            self.cursor.execute(SQLStatement)
            rows = self.cursor.fetchall()
            return rows
        
        except pyodbc.Error, err:
            raise RuntimeError("Problem executing {0} on accessDB: {1}".format(SQLStatement, err))

class SupplyChain:
    def __init__(self, _ccemDB, _name="Supply Chain"):
        self.name = _name
        self.ccemDB = _ccemDB
        self.levels = self._fillAdminLevels()
        self.administriveAreas = self._fillAdminAreas()
        self.facilitiesDict, self.ignoredFacilties = self._populateFacilitiesDict()
        self.facilityTypes = self._fillFacilityTypes()
        self.energySources = self._fillEnergySources()
        self.equipmentTypes = self._fillEquipTypes()
        
        self.coldDevInv, self.ignoredDevs = self._populateColdDevInventoryAndAssignToFacilities()
        # self.transDevInv, self.ignoredTDevs = self._populateTransportDevInventoryAndAssignToFacilities()
        self.transDevInv = {}
        print self.levels
        self.facilityStructure = None
        
    
    def _fillFacilityTypes(self):
        # ## Lets get location types
        SQLString = "SELECT * from TBL_FACILITY_TYPE"
        
        facCodes = {}
        facTypes = self.ccemDB.execute(SQLString)
    
        count = 1
        for fac in facTypes:
            facCodes[count] = fac
            count += 1
        
        return facCodes
    
    def _fillEnergySources(self):
        # ## Power Sources
        SQLString = "SELECT * from TBL_POWER_SOURCE"
        rawData = self.ccemDB.execute(SQLString)
        powerSources = {x.ft_power_source:x for x in rawData}
        
        return powerSources
    
    
    def _fillEquipTypes(self):
        # ## Equipment types    
    
        SQLString = "SELECT * from TBL_EQUIPMENT_TYPE"
        
        rawData = self.ccemDB.execute(SQLString)
        equipTypes = {x.ft_code:x for x in rawData}
        
        # ## We need to figure out what to do with this.
        equipTypes['ColdBox'] = []
        
        return equipTypes
    
    def _fillAdminLevels(self):
        
        SQLString = "SELECT * from TBLSettings_Admin"
        
        rawData = self.ccemDB.execute(SQLString)
        levels = [x.name for x in rawData]
        
        return levels
    
    def _fillAdminAreas(self):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        SQLString = "SELECT * from TBL_ADMIN_AREAS"
        
        rawData = self.ccemDB.execute(SQLString)
        
        numberOfLevels = len(self.levels)
        
        # ## This will be a heirarchical structure
        levelDict = {}
        for n in range(1, numberOfLevels + 1):
            # print n
            levelList = []
            levelListRaw = [[getattr(x, "ft_level{0}".format(y + 1)) for y in range(0, n)] for x in rawData]
            for l in levelListRaw:
                if l not in levelList:
                    levelList.append(l)
            
            # print levelList
            
            if len(levelList) == 1 and len(levelList[0]) == 1:
                # print levelList
                levelDict[levelList[0][0]] = {}
            else:
                # print levelList
                for l in levelList:
                    # print l
                    thisadmin = l[-1]
                    thisDict = levelDict
                    for k in l[:-1]:
                        # print k
                        thisDict = thisDict[k]
                    if len(l) == numberOfLevels - 1:
                        if thisadmin not in thisDict.keys():
                            thisDict[thisadmin] = []
                    elif len(l) == numberOfLevels:
                        if thisadmin not in thisDict:
                            thisDict.append(thisadmin)
                    else:
                        if thisadmin not in thisDict.keys():
                            thisDict[thisadmin] = {}
                  
        return levelDict
                
                    
        
    def _populateFacilitiesDict(self):
    # # Ok, lets try to devise a network from this mess
         
        SQLString = "SELECT * from TBL_FACILITIES"
         
        facilitiesDict = {}
        ignoredFacs = []
        facilities = self.ccemDB.execute(SQLString)
        globalCount = 1
        for fac in facilities:
            if fac.ft_facility_type is not None:
                facilitiesDict[globalCount] = Facility(fac, self,globalCount)
                globalCount += 1
            else:
                ignoredFacs.append(fac)
        
        return facilitiesDict, ignoredFacs
    
    def _populateColdDevInventoryAndAssignToFacilities(self):
        
        # # first cold rooms
        if len(self.facilitiesDict) == 0:
            raise RuntimeError("calling _populateColdDevInventoryAndAssignToFacilities before facilites have been assigned")
        
        coldDevInv = {}
        ignoredDevs = []
        
        SQLString = "SELECT * FROM TBL_INV_COLD_ROOM"
         
        rawData = self.ccemDB.execute(SQLString)
        
        coldRInv = []
        assignmentsHere = []
        for dev in rawData:
            # ## First Determine if this device is already in the inventory
            devList = list(dev)
            ccEntry = [x for x in devList if devList.index(x) != 1 ]
            
            if ccEntry not in coldRInv:
                coldRInv.append(ccEntry)
                assignmentsHere.append([dev.ft_facility_code])
            else:
                assignmentsHere[coldRInv.index(ccEntry)].append(dev.ft_facility_code)
         
     
        # ## Convert to ColdDevs
        for dev in coldRInv:
            ID = dev[0]
            facilities = assignmentsHere[coldRInv.index(dev)]
            count = 1
            while ID in coldDevInv.keys():
                ID = "{0}_{1}".format(dev[0], count)
                count += 1
             
            coldDevInv[ID] = ColdDev(dev, self.equipmentTypes, self.energySources, _coldRoomEntry=True)
            for facID in facilities:
                facility = None
                for fac,facData in self.facilitiesDict.items():
                    if facID == facData.ccemID:
                        facility = self.facilitiesDict[fac]
                        break
                self.facilitiesDict[facility.ID].inventory.append(ID) 
        
#         ### now the fridges 
#         SQLString = "SELECT * from TBL_LIB_REFRIGERATORS"
#          
#         rawData = self.ccemDB.execute(SQLString)
#      
#         
#         for dev in rawData:
#             coldDevInv[dev.ft_library_id] = ColdDev(dev,self.equipmentTypes,self.energySources,_coldRoomEntry=False)    
        
        # ## Now refrigerators 
        coldRInv = []
        assignmentsHere = []
        SQLString = "SELECT * FROM TBL_INV_REF"
         
        rawData = self.ccemDB.execute(SQLString)
         
        for dev in rawData:
            devList = list(dev)[0:23]
            
            # ## Not working
            if devList[22] == 3:
                ignoredDevs.append((devList[1], "Refrigerator labeled as not working"))
                continue
            
            del devList[0]
            del devList[1]
            del devList[4]
            
            ccEntry = devList
            # ccEntry = [x for x in devList if (devList.index(x) not in [0,2,6])]
            if len(ccEntry) == 0:
                continue
            if ccEntry[0] is None:
                continue
            
            # print ccEntry
            if ccEntry not in coldRInv:
                coldRInv.append(ccEntry)
                assignmentsHere.append([dev.ft_facility_code])
            else:
                assignmentsHere[coldRInv.index(ccEntry)].append(dev.ft_facility_code)
        
        # ## Convert to ColdDevs
        for dev in coldRInv:
            ID = dev[0]
            facilities = assignmentsHere[coldRInv.index(dev)]
            count = 1
            while ID in coldDevInv.keys():
                ID = "{0}_{1}".format(dev[0], count)
                count += 1
            coldDevInv[ID] = ColdDev(dev, self.equipmentTypes, self.energySources, _coldRoomEntry=False)
            for facID in facilities:
                facility = None
                for fac,facData in self.facilitiesDict.items():
                    if facID == facData.ccemID:
                        facility = self.facilitiesDict[fac]
                        break
                if facility is None:
                    ignoredDevs.append((ID, facID, "Facility Code Not Found in Database"))
                else:
                    self.facilitiesDict[facility.ID].inventory.append(ID) 
        
                #if facID not in self.facilitiesDict.keys():
                #    ignoredDevs.append((ID, facID, "Facility Code Not Found in Database"))
                # print "facID = {0} ID = {1}".format(facID,ID)
                #else:
                #    self.facilitiesDict[facID].inventory.append(ID)
        
        
        
#         ### Now Coldboxes
#         
#         coldRInv = []
#         assignmentsHere = []
#         SQLString = "SELECT * from TBL_INV_COLD_BOXES"
#         
#         rawData = self.ccemDB.execute(SQLString)
#         
#         for dev in rawData:
#             devList = list(dev)
#             
#             # Not working 
#             if devList[12] == 3:
#                 self.ignoredDevs.append((devList[1],"ColdBox labeled as not working"))
#                 continue
#             
#             devList[]
            
        return coldDevInv, ignoredDevs    
    
    def _populateTransportDevInventoryAndAssignToFacilities(self, _includeNonWorking=True):
        
        if len(self.facilitiesDict) == 0:
            raise RuntimeError("calling _populateTransportDevInventoryAndAssignToFacilities before facilites have been assigned")
        
        transDevInv = {}
        ignoredDevs = []
        
        SQLString = "SELECT * FROM TBL_INV_TRANSPORT"
         
        rawData = self.ccemDB.execute(SQLString)
        
        transRInv = []
        assignmentsHere = []
        
        for dev in rawData:
            
            devList = list(dev)
            # if devList[0] is None:
            #    print "before {0}".format(devList)
            if dev.ft_facility_code is None:
                ignoredDevs.append((devList, "No facility"))
                continue
            
            if dev.ft_number is None:
                ignoredDevs.append((devList, "Number of Devices missing"))
                continue 
            
            numberOfDevs = intOrZero(dev.ft_number)
            numberOfWDevs = numberOfDevs
            if _includeNonWorking is False:
                numberOfNWDevs = intOrZero(dev.ft_number_nw)
                
                numberOfWDevs = numberOfDevs - numberOfNWDevs
                if numberOfWDevs <= 0:
                    ignoredDevs.append((devList, "Non Working Devices more than working."))
                    continue
                    
            # ## going to assume that vehicles are all working for this purpose at the moment
            
            del devList[6:9]
            del devList[0:2]
            # print "after {0}".format(devList)
            if devList[0] is None:
                ignoredDevs.append((devList, "no data on transport device"))
                continue
            
            if devList not in transRInv:
                transRInv.append(devList)
                assignmentsHere.append([(dev.ft_facility_code, numberOfWDevs)])
            else:
                assignmentsHere[transRInv.index(devList)].append((dev.ft_facility_code, numberOfWDevs))
               
        for dev in transRInv:
            ID = "{0}_{1}".format(dev[2], dev[1])
            facilities = assignmentsHere[transRInv.index(dev)]
            count = 1
            while ID in transDevInv.keys():
                ID = "{0}_{1}_{2}".format(dev[2], dev[1], count)
                count += 1
            transDevInv[ID] = TransportDev(ID, dev)
            
            for facID, count in facilities:
                self.facilitiesDict[facID].transportInv.append((ID, count))
                
            
        return transDevInv, ignoredDevs
                
    def PakistanSpecificDetermineFacilitySimpleHeirarchicalHeirarchical(self):
        # # lets get the table of administrative levels
        # ## find the National Stores
        # ## We have to make some assumptions... not sure how to resolve them yet, but we will see
        
        storeCount = 0
        self.facilitiesStructure = {}
        routes = []
        nationalFacId = None
        # ## first add the National Store
        for fac, facData in self.facilitiesDict.items():
            if facData.facility_type == 1:
                storeCount += 1
                self.facilitiesStructure[fac] = {}
                nationalFacId = fac
         
        # ## now find the 2nd level
        for fac, facData in self.facilitiesDict.items():
            if facData.facility_type == 2:
                storeCount += 1
                self.facilitiesStructure[nationalFacId][fac] = {}
                routes.append((nationalFacId,fac))

        
#         for route in routes:
#             print "{0} to {1}".format(self.facilitiesDict[route[0]].name,self.facilitiesDict[route[1]].name)
#         sys.exit()
        # ## now the third level
        
        for fac, facData in self.facilitiesDict.items():
            if facData.facility_type == 3:
                storeCount += 1
                if facData.admin_structure[0] in ["ISLAMABAD","AJK"]:
                    self.facilitiesStructure[nationalFacId][fac] = []
                    routes.append((nationalFacId, fac))
                    
                else:
                    for prov in self.facilitiesStructure[nationalFacId].keys():
                        provEntry = self.facilitiesDict[prov] 
                        if facData.admin_structure[0] == provEntry.admin_structure[0]:
                            self.facilitiesStructure[nationalFacId][prov][fac] = []
                            routes.append((prov, fac))
                            break
        # Now we must fill the remaining levels with a recursive approach based on 
        # The number of levels
        for fac, facData in self.facilitiesDict.items():
            if facData.facility_type > 3:
                storeCount += 1
                if facData.admin_structure[0] in ["ISLAMABAD","AJK"]:
                    for dist in self.facilitiesStructure[nationalFacId].keys():
                        distEntry = self.facilitiesDict[dist]
                        if distEntry.admin_structure[1] == facData.admin_structure[1]:
                            self.facilitiesStructure[nationalFacId][dist].append(fac)
                            routes.append((dist, fac))
                            break
                else:
                    for prov, provData in self.facilitiesStructure[nationalFacId].items():
                        if self.facilitiesDict[prov].admin_structure[0] in ["ISLAMABAD","AJK"]:
                            continue
                        for dist in provData.keys():
                            provFlag = False
                            distEntry = self.facilitiesDict[dist]
                            if distEntry.admin_structure[0] == facData.admin_structure[0]:
                                if distEntry.admin_structure[1] == facData.admin_structure[1]:
                                    self.facilitiesStructure[nationalFacId][prov][dist].append(fac)
                                    routes.append((dist, fac))
                                    provFlag = True
                                    break
                                    #self.facilitiesStructure[nationalFacId][prov].
                        if not provFlag:
                            if distEntry.admin_structure[0] == facData.admin_structure[0]:
                                routes.append((prov,fac))
                                break
        #print storeCount
        return self.facilitiesStructure, routes
                               
class ColdDev:
    def __init__(self, _ccEntry, _eTypes, _pTypes, _coldRoomEntry=False):
        if _coldRoomEntry:
            self.ID = _ccEntry[0]
            self.name = _ccEntry[2]
            self.manufacturer = strOrUnknown(_ccEntry[3])
            self.gross_C_volume_L = floatOrZero(_ccEntry[11])
            self.net_C_volume_L = floatOrZero(_ccEntry[12])
            self.gross_F_volume_L = floatOrZero(_ccEntry[16])
            self.net_F_volume_L = floatOrZero(_ccEntry[17])
            self.year_purchased = strOrUnknown(_ccEntry[18])
            self.capitalPrice_USD = 0.0
            self.operating_condtion = _ccEntry[20]
            self.type = 'ColdRoom'
            if _ccEntry is not None or int(_ccEntry[28]) > 0:
                self.energyType = 'EG'
            else:
                self.energyType = 'E'
        else:
            self.ID = _ccEntry[0]
            self.name = _ccEntry[1]
            self.manufacturer = strOrUnknown(_ccEntry[3])
            self.type = strOrUnknown(_ccEntry[2])
            if _ccEntry[5] is None:
                self.energyType = 'E'
            else:
                self.energyType = _ccEntry[5]
            
            self.gross_C_volume_L = floatOrZero(_ccEntry[10])
            self.net_C_volume_L = floatOrZero(_ccEntry[11])
            if self.net_C_volume_L == 0.0:
                self.net_C_volume_L = 0.0001
            self.gross_F_volume_L = floatOrZero(_ccEntry[15])
            self.net_F_volume_L = floatOrZero(_ccEntry[16])
            
            self.year_purchased = strOrUnknown(_ccEntry[17])
            # self.working_status = intOrZero(_ccEntry[21])
            self.capitalPrice_USD = 0.0
            
#             self.ID = _ccEntry.ft_library_id
#             self.name = strOrUnknown(_ccEntry.ft_model_name),
#             self.manufacturer = strOrUnknown(_ccEntry.ft_manufacturer_name)
#             self.gross_C_volume_L = floatOrZero(_ccEntry.fn_gross_volume_4deg)
#             self.net_C_volume_L = floatOrZero(_ccEntry.fn_net_volume_4deg)
#             self.gross_F_volume_L = floatOrZero(_ccEntry.fn_gross_volume_20deg)
#             self.net_C_volme_L = floatOrZero(_ccEntry.fn_net_volume_20deg)
#             self.capitalPrice_USD = floatOrZero(_ccEntry.fi_prod_price)
#             self.year_purchased = strOrUnknown(_ccEntry.fi_intro_date)
#             self.type = _ccEntry.ft_item_type
#             self.energyType = _ccEntry.ft_power_sources
            
    def toHERMESRec(self):
        fType = "RefigeratorFreezer"
        if self.type == 'ColdRoom':
            fType = "ColdRoom"
        
        return {'Name':self.ID,
                'DisplayName':self.name,
                'Make':self.manufacturer,
                'Model':self.name,
                'Category':fType,
                'cooler':self.net_C_volume_L,
                'freezer':self.net_F_volume_L,
                'Year':self.year_purchased,
                'Energy':self.energyType,
                'BaseCostCur':'USD',
                'BaseCostYear':'2016',
                'BaseCost':self.capitalPrice_USD,
                'PowerRate':'',
                'roomtemperature':0.0,
                'NoPowerHoldoverDays':0.0,
                'Notes':'From CCEM',
                'AmortYears':8.53,
                }

transportDevTypes = ["motorbike",
                     "truck",
                     "other"]
class TransportDev:
    def __init__(self, _ID, _tEntry):
        self.ID = _ID
        self.make = strOrUnknown(_tEntry[2])
        self.model = strOrUnknown(_tEntry[1])
        self.type = int(_tEntry[0])
        self.year = strOrUnknown(_tEntry[3])
        self.fuel_type = intOrZero(_tEntry[4])
    
    
    def getType(self):
        if self.type > len(transportDevTypes) - 1:
            return "Other"
        else:
            return transportDevTypes[self.type - 1]
        
    def toHERMESRec(self):
        return {'Name':self.ID,
                'DisplayName':"{0} {1} {2}".format(self.make, self.model, self.getType()),
                'FuelRate':'',
                'CoolVolumeCC':0.0,
                'Storage':'',
                'FuelRateUnits':'',
                'BaseCostCur':'',
                'BaseCost':'',
                'BaseCostYear':'',
                'Fuel':'',
                'Notes':'From CCEM'
                }    
       
class Facility:
    def __init__(self, _fEntry, _SC,_globalCount):
        self._supplyChain = _SC
        self.ID = _globalCount
        _globalCount += 1 #int(_fEntry.ft_facility_code.strip('-').strip('.'))
        self.ccemID = _fEntry.ft_facility_code
        self.name = u'{0}'.format(_fEntry.ft_facility_name)
        self.admin_structure = (_fEntry.ft_level2, _fEntry.ft_level3, _fEntry.ft_level4, _fEntry.ft_level5)
        self.facility_type = _fEntry.ft_facility_type
        self.population = {'newborns':floatOrZero(_fEntry.fi_target_births),
                           'pregnantWomen':floatOrZero(_fEntry.fi_target_pw),
                           'cba':floatOrZero(_fEntry.fi_cba),
                           'total':floatOrZero(_fEntry.fi_tot_pop)}
        
        self.distanceToSupplier_KM = floatOrZero(_fEntry.fn_distance)
        self.resupply_interval = intOrZero(_fEntry.fi_resupp_interval)
        self.reserve_stock = intOrZero(_fEntry.fi_reserve_stock)
        self.isVaccinating = False
        if _fEntry.fi_cc_delivery == -1:  # or _fEntry.fi_cc_outreach == -1:
            self.isVaccinating = True
        self.isOutreach = False
        if _fEntry.fi_cc_outreach == -1:
            self.isOutreach = True 
        self.inventory = []
        self.transportInv = []
        
        self.level = None
        if self.facility_type < 4:
            self.level = _SC.levels[self.facility_type - 1]
        else:
            self.level = u"Facility"
    def inventoryToHERMESString(self, proxyName):
        inventoryString = u""
        if len(self.inventory) == 0:
            inventoryString += u"{0},".format(proxyName)
        else:
            for inv in self.inventory:
                inventoryString += u'{0}+'.format(self._supplyChain.coldDevInv[inv].ID)
        for trans, count in self.transportInv:
            inventoryString += u'{0}*{1}+'.format(count, self._supplyChain.transDevInv[trans].ID)
        
        return inventoryString[:-1]
            
    def toHERMESRec(self, _proxyName):
        functionString = "Distribution"
        if self.isVaccinating:
            functionString = "Administration"
            
        return {'NAME':self.name,
                'CATEGORY':self.level,
                'FUNCTION':'Administration' if self.level == 'Facility' or self.name == 'KHANEWAL' else 'Distribution',
                #(self.isVaccinating or self.isOutreach or self.level == 'Facility') else 'Distribution',
                'idcode':self.ID,
                'Inventory':self.inventoryToHERMESString(_proxyName),
                'Device Utilization Rate':1.0,
                'UseVialsInterval':1,
                'UseVialsLatency':1,
                'Newborn':self.population['newborns'] if self.level == 'Facility' or self.name == 'KHANEWAL' else '',
                'PW':self.population['pregnantWomen'] if self.level == 'Facility' or self.name == 'KHANEWAL' else '',
                'CBA': self.population['cba'] if self.level == 'Facility' or self.name == 'KHANEWAL' else '',
                '0-1Years':self.population['newborns'] if self.level == 'Facility' or self.name == 'KHANEWAL' else '',
                #'Newborn':self.population['newborns'] if (self.isVaccinating or self.isOutreach or self.level == 'Facility') and (self.level == 'Facility') else '',
                #'PW':self.population['pregnantWomen'] if (self.isVaccinating or self.isOutreach or self.level == 'Facility') else '',
                #'CBA': self.population['cba'] if (self.isVaccinating or self.isOutreach or self.level == 'Facility') else '',
                #'0-1Years':self.population['newborns'] if (self.isVaccinating or self.isOutreach or self.level == 'Facility') else '',
                'Latitude':'',
                'Longitude':'',
                }
#         if self.facility_type == 1:
#             self.level = self._supplyChain.levels[0]
#         elif self.facility_type == 2:
#             print self.find_level()
        # if self.level == u'Union Council':
        #    print self.level
        
    
#     def find_level(self):
#         print "Beginning admin = {0}".format(self.admin_structure)
#         print self._supplyChain.administriveAreas['Federal'].keys()
#         numberOfLevels = len(self._supplyChain.levels)
#         thisLevel = self._supplyChain.levels[0]
#         dictHere = self._supplyChain.administriveAreas[thisLevel]
#         for i in range(1,numberOfLevels+1):
#             #print dictHere.keys()
#             print type(dictHere)
#             thisAdmin = self.admin_structure[i-1]
#             if i != numberOfLevels:
#                 print i
#                 if thisAdmin not in dictHere.keys():
#                     return thisLevel
#             else:
#                 if u'{0}'.format(thisAdmin) in dictHere:
#                     return thisLevel   
#                 else:
#                     return None 
#             dictHere = dictHere[thisAdmin]
#             thisLevel = self._supplyChain.levels[i]
#          
#         print thisLevel
#         sys.exit()
            
        
        
