import ipath
import ccem_utils as CC
import optparse
import sys,os
import pprint
import shadow_network as shd
from shadow_network_db_api import ShdNetworkDB
import session_support_wrapper as session_support
import db_routines
import typehelper
from transformation import setLatenciesByNetworkPosition


#### This needs to be run with a 32-bit python if you are running a 32 bit access
#### Database.

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
    
    db = db_routines.DbInterface(echo=False)
    session = db.Session()
    
    aM = typehelper._getAllTypesModel(session)
    ### Establish the connection with ACCESS DATABASE
    shdTypes = shd.ShdTypes()
   
    ccemDB = CC.AccessDB(opts.accessDB)
    
    supplyChain = CC.SupplyChain(ccemDB)
    
    ### This is separate as people my want to try other methods
    supplyStructure,routesList = supplyChain.PakistanSpecificDetermineFacilitySimpleHeirarchicalHeirarchical()
    for route in routesList:
        if (route[1],route[0]) in routesList:
            print route
        #print route
    #print len(routesList)
    #print len(set(routesList))
    #print len(supplyChain.facilitiesDict)
    #sys.exit()
    shdTypeClass = shd.ShdTypes.typesMap['fridges']
    
    for id,coldDev in supplyChain.coldDevInv.items():
        newType = shdTypeClass(coldDev.toHERMESRec())
        shdTypes.addType(newType)
    
    ### Add proxy and others
    proxyRec = {
                'Name':'CCEM_Proxy',
                'DisplayName':'CCEM_Proxy',
                'Make':'STB',
                'Model':'STB',
                'Category':'RefigeratorFreezer',
                'cooler':1,
                'freezer':1,
                'Year':2016,
                'Energy':'E',
                'BaseCostCur':'USD',
                'BaseCostYear':'2016',
                'BaseCost':0.0,
                'PowerRate':0.0,
                'roomtemperature':0.0,
                'NoPowerHoldoverDays':0.0,
                'Notes':'From CCEM',
                'AmortYears':8.53,
                }
    newType = shdTypeClass(proxyRec)
    shdTypes.addType(newType)
    
    
    #shdTypeClass = shd.ShdTypes.typesMap['trucks']
    #for id,transDev in supplyChain.transDevInv.items():
    #    newType = shdTypeClass(transDev.toHERMESRec())
    #    shdTypes.addType(newType)
    
    ### Adding generic vehicles, because the data in the CCEM is a mess
    for cb in ['Std_CB_RCW25CF','Std_VC','OUTDOORS']:
        attrRec = {'_inmodel':False, 'modelId':aM.modelId}
        shd._copyAttrsToRec(attrRec,aM.types[cb])
        newTp = shdTypeClass(attrRec.copy())
        shdTypes.addType(newTp)
    
    shdTypeClass = shd.ShdTypes.typesMap['trucks']
    for vehicle in ['Std_DoubleCabTruck','Std_coldtruck','Std_motorbike']:
        attrRec = {'_inmodel':False, 'modelId':aM.modelId}
        shd._copyAttrsToRec(attrRec,aM.types[vehicle])
        newTp = shdTypeClass(attrRec.copy())
        shdTypes.addType(newTp)
    
    count = 0
    peopleTypes = ['Newborn','PW','CBA','0-1Years']
    for people in peopleTypes:
        attrRec = {'Name':people,
                   'DisplayName':people,
                   'SortOrder':count,
                   'Notes':'From CCEM'}
        newTp = shd.ShdTypes.typesMap['people'](attrRec)
        shdTypes.addType(newTp)
    
    shdTypeClass = shd.ShdTypes.typesMap['vaccines']
    vaccineTypes = ['BCG_WHO_Shipping_Guide_20Dose',
                    'OPV_WHO_Shipping_Guide_20Dose',
                    'DTPHepBHib_Crucell_Shingal_3mL_1Dose',
                    'Measles_WHO_Shipping_Guide_10Dose',
                    'PCV10_GSK_10Carton_1Dose',
                    'Tetanus_Toxoid_WHO_Shipping_Guide_20Dose',
                    'IPV_Sanofi_10Dose',
                    'Rotavirus_GSK_50Tube_1Dose']
    for vaccine in vaccineTypes:
        attrRec = {'_inmodel':False, 'modelId':aM.modelId}
        shd._copyAttrsToRec(attrRec,aM.types[vaccine])
        attrRec['Name'] = attrRec['Name'] + "_Pakistan"
        newTp = shdTypeClass(attrRec.copy())
        shdTypes.addType(newTp)
    
    shdNetwork = shd.ShdNetwork(None,None,None,shdTypes,opts.outputname)
    ### Create the Stores Table
    for fac,facData in supplyChain.facilitiesDict.items():
        #print facData.toHERMESRec()
        #if len(facData.inventory) == 0:
        #    print facData.toHERMESRec('CCEM_Proxy')
        #    print "{0}   {1}".format(facData.isVaccinating,facData.isOutreach)
        storeRec = facData.toHERMESRec('CCEM_Proxy')
        if storeRec['CATEGORY'] == 'Federal':
            storeRec['Inventory'] += '+10*Std_coldtruck'
        elif storeRec['CATEGORY'] == 'Province':
            storeRec['Inventory'] += '+10*Std_coldtruck+50*Std_DoubleCabTruck'
        elif storeRec['CATEGORY'] == 'District':
            storeRec['Inventory'] += '+50*Std_DoubleCabTruck'
        
        #store = shd.ShdStore(storeRec,shdNetwork)
        #print "adding store {0}".format(store.idcode)
        shdNetwork.addStore(storeRec)
   
     
    ### set the schedule
    #
    #
    
    ### Make Routes
    ###
    demands = {'BCG_WHO_Shipping_Guide_20Dose':[1,0,0,0],
               'OPV_WHO_Shipping_Guide_20Dose':[1,0,0,3],
                'DTPHepBHib_Crucell_Shingal_3mL_1Dose':[0,0,0,3],
                'Measles_WHO_Shipping_Guide_10Dose':[0,0,0,2],
                'PCV10_GSK_10Carton_1Dose':[0,0,0,3],
                'Tetanus_Toxoid_WHO_Shipping_Guide_20Dose':[0,0,0,0],
                'IPV_Sanofi_10Dose':[0,0,0,0],
                'Rotavirus_GSK_50Tube_1Dose':[0,0,0,0]
                }
    for vac,demand in demands.items():
        for count in demand:
            print '{0}_Pakistan'.format(vac)
            print peopleTypes[demand.index(count)]
            print count
            shdNetwork.addDemand(shd.ShdDemand({'vaccineStr':'{0}_Pakistan'.format(vac),'peopleStr':peopleTypes[demand.index(count)],'count':count,'demandType':'U',"Notes":"from CCEM"}))
    
#     shdNetwork.addDemand(shd.ShdDemand({'vaccineStr':'BCG_WHO_Shipping_Guide_20Dose_Pakistan','peopleStr':'Newborn','count':1,'demandType':'U',"Notes":"from CCEM"}))
#     shdNetwork.addDemand(shd.ShdDemand({'vaccineStr':'OPV_WHO_Shipping_Guide_20Dose_Pakistan','peopleStr':'Newborn','count':1,'demandType':'U',"Notes":"from CCEM"}))
#     shdNetwork.addDemand(shd.ShdDemand({'vaccineStr':'OPV_WHO_Shipping_Guide_20Dose_Pakistan','peopleStr':'0-1Years','count':3,'demandType':'U',"Notes":"from CCEM"}))
#     shdNetwork.addDemand(shd.ShdDemand({'vaccineStr':'DTPHepBHib_Crucell_Shingal_3mL_1Dose_Pakistan','peopleStr':'Newborn','count':0,'demandType':'U',"Notes":"from CCEM"}))
#     shdNetwork.addDemand(shd.ShdDemand({'vaccineStr':'DTPHepBHib_Crucell_Shingal_3mL_1Dose_Pakistan','peopleStr':'0-1Years','count':3,'demandType':'U',"Notes":"from CCEM"}))
#     shdNetwork.addDemand(shd.ShdDemand({'vaccineStr':'PCV10_GSK_10Carton_1Dose_Pakistan','peopleStr':'0-1Years','count':3,'demandType':'U',"Notes":"from CCEM"}))
#     
                  #{'vaccineStr':'BCG_WHO_Shipping_Guide_20Dose','peopleStr':'PW','count':0},
                  #{'vaccineStr':'BCG_WHO_Shipping_Guide_20Dose','peopleStr':'CBA','count':0},
                  #{'vaccineStr':'BCG_WHO_Shipping_Guide_20Dose','peopleStr':'0-1Years','count':0}
                   
    frequencies = {('Federal','Province'):60,
                   ('Federal','District'):20,
                   ('Province','District'):20,
                   ('Province','Facility'):10,
                   ('District','Facility'):10
                   }
    
    vehicle = {('Federal','Province'):'Std_coldtruck',
                   ('Federal','District'):'Std_coldtruck',
                   ('Province','District'):'Std_coldtruck',
                   ('Province','Facility'):'Std_DoubleCabTruck',
                   ('District','Facility'):'Std_DoubleCabTruck'
                   }
    structureDict = supplyStructure
#     for id,locs in structureDict.items():
#         if type(locs) == 'list':
#             continue
#         for loc in locs.keys():
    for route in routesList:
        #print "route"
        fromFac = supplyChain.facilitiesDict[route[0]]
        toFac = supplyChain.facilitiesDict[route[1]]
        #if (fromFac.level,toFac.level) == ('Federal','Facility'):
        #    print fromFac.name + " to " + toFac.name
        frequency = frequencies[(fromFac.level,toFac.level)]
        newRoute = [
                    {
                    'RouteName':u"r_{0}_to_{1}".format(fromFac.ID,toFac.ID),
                    'Type':'varpush',
                    'LocName':u'{0}'.format(fromFac.name),
                    'idcode':fromFac.ID,
                    'RouteOrder':0,
                    'TransitHours':5.0,
                    'ShipIntervalDays':frequency,
                    'ShipLatencyDays':2,
                    'PullOrderAmountDays':'',
                    'Notes':'Automatically Generated',
                    'Conditions':'',
                    'TruckType':vehicle[(fromFac.level,toFac.level)],
                    'DistanceKM':100.0,
                    'PickupDelayMagnitude':0,
                    'PickupDelaySigma':0,
                    'PickupDelayFrequency':0
                    },
                    {
                    'RouteName':u"r_{0}_to_{1}".format(fromFac.ID,toFac.ID),
                    'Type':'varpush',
                    'LocName':u'{0}'.format(toFac.name),
                    'idcode':toFac.ID,
                    'RouteOrder':1,
                    'TransitHours':5.0,
                    'ShipIntervalDays':frequency,
                    'ShipLatencyDays':2,
                    'PullOrderAmountDays':'',
                    'Notes':'Automatically Generated',
                    'Conditions':'',
                    'TruckType':vehicle[(fromFac.level,toFac.level)],
                    'DistanceKM':100.0,
                    'PickupDelayMagnitude':0,
                    'PickupDelaySigma':0,
                    'PickupDelayFrequency':0
                     },
                    ]
        
        route = shdNetwork.addRoute(newRoute)
        route.linkRoute()
    
            ### District to Facility Level
            #routeRec = {'RouteName':'r_{0}_to_{1}'.format()}
    #for routeId,route in shdNetwork.routes.items():
    #    print routeId
    #for storeId,store in shdNetwork.stores.items():
    #    print storeId
    #print shdNetwork.rootStores()
    setLatenciesByNetworkPosition(shdNetwork,1,stagger=True)
    shdNetwork.writeCSVRepresentation()   
    #aM = typehelper._getAllTypesModel(db)
                        
if __name__ == '__main__':
    main()

