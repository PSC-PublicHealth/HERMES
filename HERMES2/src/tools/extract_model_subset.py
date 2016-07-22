import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
import input
from copy import deepcopy
import sys
import optparse
from transformation import convertToSurrogate

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-d db_id]
    """)
    parser.add_option("-i", "--inputfile", default=None)
    parser.add_option("-p", "--pivotlocation", default=None)
    parser.add_option("-o","--output",default=None)
    # parser.add_option("-d","--use_db",type=int,default=None)
    opts, args = parser.parse_args()
    
    return (opts, args)

def main():
    
    opts, args = parseCommandLine()
        
    userInput = input.UserInput(opts.inputfile, False)
    shdTypes = shadow_network.loadShdTypes(userInput, input.UnifiedInput())
    shdNtwk = shadow_network.loadShdNetwork(userInput, shdTypes, opts.output)
    
    
    storeToPivot = shdNtwk.stores[int(opts.pivotlocation)]
    
    routesToKeep = []
    ### get the supplierRoutes
    routesToKeep.append(storeToPivot.supplierRoute())
    ### Walk up the supplier to make sure we get to the root
    supplierStore = storeToPivot.suppliers()[0][0]
    
    while True:
        ### Make the other clients of this store a Surrogate
        for clientStore,clientRoute in supplierStore.clients():
            if clientRoute not in routesToKeep:
                convertToSurrogate(shdNtwk,clientStore.idcode)
        if supplierStore == shdNtwk.rootStores()[0]:
            break
        routesToKeep.append(supplierStore.supplierRoute())
        supplierStore = supplierStore.suppliers()[0][0]
    
    
    shdNtwk.writeCSVRepresentation()
    
    
    
if __name__ == '__main__':
    main()