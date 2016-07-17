import ipath
import ccem_utils as CC
import optparse
import sys,os
import pprint


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
    
    ccemDB = CC.AccessDB(opts.accessDB)
    
    supplyChain = CC.SupplyChain(ccemDB)
    
    ### This is separate as people my want to try other methods
    supplyChain.determineFacilitySimpleHeirarchicalHeirarchical()
    #supplyChain.assignColdChainEquipmentToFacilities()
    
    
                        
if __name__ == '__main__':
    main()

