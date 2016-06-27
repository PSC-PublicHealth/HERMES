import pyodbc
import optparse
import sys,os
import pprint


#### This needs to be run with a 32-bit python if you are running a 32 bit access
#### Database.
def floatOrZero(value):
    try:
        fValue = float(value)
        return fValue
    except:
        return 0.0
    
def strOrUnknown(value):
    if value is None:
        return "UNKOWN"
    else:
        return value

class ColdDev:
    def __init__(self,_ccEntry,_eTypes,_pTypes,_coldRoomEntry=False):
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
            self.ID = _ccEntry.ft_library_id
            self.name = strOrUnknown(_ccEntry.ft_model_name),
            self.manufacturer = strOrUnknown(_ccEntry.ft_manufacturer_name)
            self.gross_C_volume_L = floatOrZero(_ccEntry.fn_gross_volume_4deg)
            self.net_C_volume_L = floatOrZero(_ccEntry.fn_net_volume_4deg)
            self.gross_F_volume_L = floatOrZero(_ccEntry.fn_gross_volume_20deg)
            self.net_C_volme_L = floatOrZero(_ccEntry.fn_net_volume_20deg)
            self.capitalPrice_USD = floatOrZero(_ccEntry.fi_prod_price)
            self.year_purchased = strOrUnknown(_ccEntry.fi_intro_date)
            self.type = _ccEntry.ft_item_type
            self.energyType = _ccEntry.ft_power_sources
            
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
        
            
        
class AccessDB:
    def __init__(self,_accessFile):
        try:
        ## From https://github.com/mkleehammer/pyodbc/wiki/Connecting-to-Microsoft-Access
            self.conn = pyodbc.connect(r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' +
                              r'DBQ={0}'.format(_accessFile))
            self.cursor = self.conn.cursor()
        
        except pyodbc.Error, err:
            raise RuntimeError("Problem connecting to the access database: {0}".format(err))
        
    
    def execute(self,SQLStatement):
        try:
            self.cursor.execute(SQLStatement)
            rows = self.cursor.fetchall()
            return rows
        
        except pyodbc.Error, err:
            raise RuntimeError("Problem executing {0} on accessDB: {1}".format(SQLStatement, err))


def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-i inputfile][-b dbId]
    """)
    parser.add_option("-a","--accessDB",default=None,
                      help="The location of the CCEM access database")
    parser.add_option("-o", "--outputname",default=None)

    opts,args = parser.parse_args()

    return (opts, args)

def main():
    opts,args = parseCommandLine()
    pp = pprint.PrettyPrinter(indent=4)
    
    ### Establish the connection with ACCESS DATABASE
    
    ccemDB = AccessDB(opts.accessDB)
    
    ### Lets get location types
    
    SQLString = "SELECT * from TBL_FACILITY_TYPE"
    
    facCodes = []
    facTypes = ccemDB.execute(SQLString)

    for fac in facTypes:
        facCodes.append(fac)
        
    ### Equipment types    
    
    SQLString = "SELECT * from TBL_EQUIPMENT_TYPE"
    
    rawData = ccemDB.execute(SQLString)
    equipTypes = {x.ft_code:x for x in rawData}
    
    ### Power Sources
    
    SQLString = "SELECT * from TBL_POWER_SOURCE"
    rawData = ccemDB.execute(SQLString)
    powerSources = {x.ft_power_source:x for x in rawData}
    
    ### lets create a master list of equipment
    
    coldRInv = []
    ## first cold rooms
    SQLString = "SELECT * FROM TBL_INV_COLD_ROOM"
    
    rawData = ccemDB.execute(SQLString)
    
    for dev in rawData:
        ### First Determine if this device is already in the inventory
        devList = list(dev)
        ccEntry = [x for x in devList if devList.index(x) != 1 ]
        if ccEntry not in coldRInv:
            coldRInv.append(ccEntry)
    

    ### Convert to ColdDevs
    coldDevInv = {}
    for dev in coldRInv:
        ID = dev[0]
        count = 1
        while ID in coldDevInv.keys():
            ID = dev[0] + "_{0}".format(count)
            count+=1
        
        coldDevInv[ID] = ColdDev(dev,equipTypes,powerSources,_coldRoomEntry=True)
        
    ### now the fridges 
    SQLString = "SELECT * from TBL_LIB_REFRIGERATORS"
    
    rawData = ccemDB.execute(SQLString)

    for dev in rawData:
        coldDevInv[dev.ft_library_id] = ColdDev(dev,equipTypes,powerSources,_coldRoomEntry=False)
    
    sys.exit()
    
    ### Ok, lets try to devise a network from this mess
    
    SQLString = "SELECT * from TBL_FACILITIES"
    
    facilitiesDict = {}
    ignoredFacs = []
    facilities = ccemDB.execute(SQLString)
    
    for fac in facilities:
        if fac.ft_facility_type is not None:
            distanceKM = -1.0
            if fac.fn_distance is not None:
                distanceKM = float(fac.fn_distance)
            facilitiesDict[fac.ft_facility_code] = {'name':u'{0}'.format(fac.ft_facility_name),
                                                    'admin_code':fac.fi_admin_code,
                                                    'admin_struct':(fac.ft_level2,fac.ft_level3,fac.ft_level4,fac.ft_level5),
                                                    'facility_type':facTypes[int(fac.ft_facility_type)-1],
                                                    'populations':{'newborns':int(fac.fi_target_births),
                                                                   'pregnantWomen':int(fac.fi_target_pw),
                                                                   'cba':int(fac.fi_cba),
                                                                   'total':int(fac.fi_tot_pop)},
                                                    'distanceToSupplier_KM':distanceKM,
                                                    
                                                    }
        else:
            ignoredFacs.append(fac)
    
    
    ### find the National Stores
    ### We have to make some assumptions... not sure how to resolve them yet, but we will see
    facilitiesStructure = {}
    nationalFacId = None
    ### first add the National Store
    for fac,facData in facilitiesDict.items():
        if facCodes.index(facData['facility_type']) == 0:
            facilitiesStructure[fac] = {}
            nationalFacId = fac
    
    ### now find the 2nd level
    for fac,facData in facilitiesDict.items():
        if facCodes.index(facData['facility_type']) == 1:
            facilitiesStructure[nationalFacId][fac] = {}
    
    ### now the third level
    for fac,facData in facilitiesDict.items():
        if facCodes.index(facData['facility_type']) == 2:
            for prov in facilitiesStructure[nationalFacId].keys():
                provEntry = facilitiesDict[prov] 
                if facData['admin_struct'][0] == provEntry['admin_struct'][0]:
                    facilitiesStructure[nationalFacId][prov][fac] = []
             
     
     
    for fac,facData in facilitiesDict.items():
        if facCodes.index(facData['facility_type']) > 2:
            for prov,provData in facilitiesStructure[nationalFacId].items():
                for dist in provData.keys():
                    distEntry = facilitiesDict[dist]
                    if distEntry['admin_struct'][0]==facData['admin_struct'][0] \
                        and distEntry['admin_struct'][1] == facData['admin_struct'][1]:
                        facilitiesStructure[nationalFacId][prov][dist].append(fac)
                        
    pp.pprint(facilitiesStructure)
    
if __name__ == '__main__':
    main()

