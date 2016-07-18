import ipath
import ccem_utils as CC
import optparse
import sys,os
import pprint
import shadow_network as shd
import typehelper


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
    
    ### Establish the connection with ACCESS DATABASE
    shdTypes = shd.ShdTypes()
   
    ccemDB = CC.AccessDB(opts.accessDB)
    
    supplyChain = CC.SupplyChain(ccemDB)
    
    ### This is separate as people my want to try other methods
    supplyStructure = supplyChain.PakistanSpecificDetermineFacilitySimpleHeirarchicalHeirarchical()
    shdTypeClass = shd.ShdTypes.typesMap['fridges']
    
    for id,coldDev in supplyChain.coldDevInv.items():
        if id == "E003010_41":
            print coldDev.toHERMESRec()
        newType = shdTypeClass(coldDev.toHERMESRec())
        shdTypes.addType(newType)
    
    shdTypeClass = shd.ShdTypes.typesMap['trucks']
    for id,transDev in supplyChain.transDevInv.items():
        newType = shdTypeClass(transDev.toHERMESRec())
        shdTypes.addType(newType)
    
    shdNetwork = shd.ShdNetwork(None,None,None,shdTypes,opts.outputname)
    ### Create the Stores Table
    for fac,facData in supplyChain.facilitiesDict.items():
        print facData.toHERMESRec()
        store = shd.ShdStore(facData.toHERMESRec(),shdNetwork)
        shdNetwork.addStore(store)
    aM = typehelper._getAllTypesModel()
                        
if __name__ == '__main__':
    main()

