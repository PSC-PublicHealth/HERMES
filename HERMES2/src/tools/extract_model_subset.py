import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
import input
from copy import deepcopy
import sys
import optparse
from transformation import convertToSurrogate,convertLoopToSurrogate

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
    print "RoutesToKeep = {0}".format(routesToKeep)
    print "Roots = {0}".format(shdNtwk.rootStores())
    rootStore = shdNtwk.rootStores()[0]
    count = 0
    while True:
        ### Make the other clients of this store a Surrogate
        #for clientStore,clientRoute in supplierStore.clients():
        for clientRoute in supplierStore.clientRoutes():
            ### If the client Route is a loop, must be handled differently
            if len(clientRoute.stops) > 2:
                ### must Determine if this loop has our store in it
                if storeToPivot in [x.store for x in clientRoute.stops]:
                    raise RuntimeError("Can't handle this case yet")
                else:
                    convertLoopToSurrogate(shdNtwk, clientRoute.RouteName)
            else:
                clientStore = clientRoute.stops[0].store
                if clientStore == supplierStore:
                    clientStore = clientRoute.stops[1].store
                print "Client = {0} Supplier = {1}".format(clientStore.idcode,supplierStore.idcode)
                if clientRoute not in routesToKeep:
                    print "blowing away {0}".format(clientRoute.RouteName)
                    if(len(clientStore.clients())>0):
                        convertToSurrogate(shdNtwk,clientStore.idcode)
                print "Root Here = {0}".format(shdNtwk.rootStores())   
        if supplierStore == rootStore:
            break
        routesToKeep.append(supplierStore.supplierRoute())
        supplierStore = supplierStore.suppliers()[0][0]
    
    #print "Routes Left= {0}".format(shdNtwk.routes)
    print "Roots Should be {0}".format(shdNtwk.rootStores())
    shdNtwk.writeCSVRepresentation()
    
    
    
if __name__ == '__main__':
    main()
