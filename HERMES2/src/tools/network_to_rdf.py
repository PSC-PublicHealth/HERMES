#! /usr/bin/env python

###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################

__doc__=""" network_to_rdf.py
This utility loads the network 'as usual' from .csv files and then saves it as
an RDF file.
"""
_hermes_svn_id_="$Id$"

import sys,os,optparse,types
import rdflib, rdflib.plugin
import input, network


class RDFManager:
    def __init__(self):
        self.storePath = "/usr/tmp/sleepycat2"
        self.ns = {}   
        hermes = rdflib.Namespace("http://hermes.psc.edu/rdf/hermes#")
        hx = rdflib.Namespace("http://hermes.psc.edu/rdf/hermesex#")
        self.ns['hermes'] = hermes
        self.ns['hx'] = hx
        self.store = None             
        self.graph = None

    def openRDFStore(self):
        #self.store = rdflib.plugin.get("Sleepycat",rdflib.plugin.Store)(identifier="rdfstore")        
        self.store = rdflib.plugin.get("IOMemory",rdflib.plugin.Store)(identifier="rdfstore")
        pass
        
    def openRDFGraph(self, create=False):
        if self.store is None: self.openRDFStore()
        self.graph = rdflib.ConjunctiveGraph(store=self.store)
        if create:
            self.graph.open(self.storePath,create=True)
        else:
            rt = self.graph.open(self.storePath,create=False)
            if rt == rdflib.store.NO_STORE: 
                self.graph.open(self.storePath,create=True)
            else:
                assert rt==rdflib.store.VALID_STORE, "The underlying store is corrupt"
        self.graph.bind("hermes",self.ns['hermes'])
        self.graph.bind("hx",self.ns['hx'])
        print "Opening; Existing triples in store: %d"%len(self.graph)
    
    def saveGraphToRDF(self,uri):
        if self.graph is None: self.openRDFGraph(create=True)
        print "Serializing; Existing triples in store: %d"%len(self.graph)
        print self.graph.serialize(uri)
        print 'done'

    def safeAddTriple(self,s,p,o):
        """
        Add the triple to the given graph if it is not already present
        """
        if self.graph is None: self.openRDFGraph(create=True)
        n = 0
        for tuple in self.graph.triples((s,p,o)): n += 1
        if n == 0:
            self.graph.add((s,p,o))
        elif n>1:
            print 'duplicates: %d copies of (%s %s %s)'%(n,s,p,repr(o))

    def fakeAddTriple(self,s,p,o):
        """
        For debugging purposes
        """
        print 'pretending to add %s %s %s'%(s,p,repr(o))

    def createStoreEntity(self, netStore):
        bnode = rdflib.BNode()
        self.safeAddTriple(bnode,rdflib.RDF.type,self.ns['hx']['store'])
        for attr in ['CATEGORY', 'FUNCTION', 'NAME', 
                     'idcode', 'Device Utilization Rate', 'Latitude',
                     'Longitude', 'UseVialsInterval', 'UseVialsLatency'
                     ]:
            v = getattr(netStore, attr)
            if v is None:
                print 'skipping %s %s None'%(netStore.idcode,attr)
            elif (isinstance(v,types.StringTypes) or isinstance(v,types.LongType)
                or isinstance(v,types.FloatType) or isinstance(v,types.IntType)):
                safeAttr = attr.replace(" ","_")
                self.safeAddTriple(bnode, self.ns['hermes'][safeAttr], rdflib.Literal(v)) 
            else:
                safeAttr = attr.replace(" ","_")
                self.safeAddTriple(bnode, self.ns['hermes'][safeAttr], v) 
        for count, item in netStore.inventoryList:
            self.safeAddTriple(bnode,self.ns['hx']['inventory'],
                               self.createInventoryEntry(item, count))
        return bnode

    def getItemTypeEntry(self, item):
        if (self.ns['hermes'][item.name],None,None) not in self.graph:
            self.safeAddTriple(self.ns['hermes'][item.name],
                               self.ns['hx']['category'],self.ns['hermes'][item.typeName])            
        return self.ns['hermes'][item.name]

    def createInventoryEntry(self, item, count):
        bnode = rdflib.BNode()
        self.safeAddTriple(bnode,self.ns['hx']['count'],rdflib.Literal(count))
        self.safeAddTriple(bnode,rdflib.RDF.type,self.getItemTypeEntry(item))
        return bnode

    def createRouteStop(self, stopDict, storeDict):
        stopNode = rdflib.BNode()
        self.safeAddTriple(stopNode,rdflib.RDF.type,self.ns['hx']['stop'])
        self.safeAddTriple(stopNode,self.ns['hermes']['store'],storeDict[stopDict['store'].idcode])
        for attr in ['TransitHours','DistanceKM','PullOrderAmountDays']:
            v = stopDict[attr]
            if v is None:
                print 'skipping %s %s None'%(stopDict['store'].NAME, attr)
            elif (isinstance(v,types.StringTypes) or isinstance(v,types.LongType)
                or isinstance(v,types.FloatType) or isinstance(v,types.IntType)):
                safeAttr = attr.replace(" ","_")
                self.safeAddTriple(stopNode, self.ns['hermes'][safeAttr], rdflib.Literal(v)) 
            else:
                raise RuntimeError("Unexpected attr value %s on route stop %s"%(v,stopDict['store'].NAME))
        return stopNode
                
    def createRouteEntity(self, netRoute, storeDict):
        bnode = rdflib.BNode()
        self.safeAddTriple(bnode,rdflib.RDF.type,self.ns['hx']['route'])
        for attr in ['RouteName', 'Type', 'TruckType', 'ShipIntervalDays', 'ShipLatencyDays',
                     'Conditions']:
            v = getattr(netRoute, attr)
            if v is None:
                print 'skipping %s %s None'%(netStore.idcode,attr)
            elif (isinstance(v,types.StringTypes) or isinstance(v,types.LongType)
                or isinstance(v,types.FloatType) or isinstance(v,types.IntType)):
                safeAttr = attr.replace(" ","_")
                self.safeAddTriple(bnode, self.ns['hermes'][safeAttr], rdflib.Literal(v)) 
            else:
                safeAttr = attr.replace(" ","_")
                self.safeAddTriple(bnode, self.ns['hermes'][safeAttr], v) 
        if len(netRoute.stops) > 0:
            stopList = rdflib.BNode()
            self.safeAddTriple(stopList,rdflib.RDF.type, rdflib.RDF.Seq)
            tail = stopList
            self.safeAddTriple(bnode,self.ns['hx']['stops'],tail)
            for s in netRoute.stops:
                self.safeAddTriple(tail,rdflib.RDF.first,self.createRouteStop(s, storeDict))
                sNode = rdflib.BNode()
                self.safeAddTriple(tail,rdflib.RDF.rest,sNode)
                tail = sNode
            self.safeAddTriple(tail,rdflib.RDF.rest, rdflib.RDF.nil)
        return bnode
        
class _MockSim:
    """
    Type construction requires some sort of sim on which to hang intermediate results, but
    it doesn't need any actual functionality.
    """
    def __init__(self, userInput, unifiedInput,perfect):
        self.userInput = userInput
        self.unifiedInput = unifiedInput
        self.perfect = perfect



###########
# main
###########

def main():
    weakMode= False
    verbose= False
    debug= False
    hideSet= set()
    
    parser= optparse.OptionParser(usage="""
    %%prog input.kvp output.rdf
    
    The model specified by the given input file is parsed.  The network is extracted and saved as an RDF file.
    """)
    parser.add_option("-v","--verbose",action="store_true",help="verbose output")
    parser.add_option("-d","--debug",action="store_true",help="debugging output")
    parser.add_option("-D","--define",action="append",help="add/override config info with this definition")

    opts,args= parser.parse_args()

    if len(args)!=2:
        parser.error("Found %d arguments, expected 2"%len(args))

    # Parse args
    if opts.verbose:
        verbose= True
    if opts.debug:
        debug= True

    # Clean up command line parser
    parser.destroy()

    infname= args[0]
    outfname= args[1]

    unifiedInput = input.UnifiedInput()  # pointers to 'unified' files
    userInput = input.UserInput(infname)
            
    if opts.define is not None:
        userInput.addValues(opts.define,replace=True,vtype="kvp")
    if verbose: userInput['verbose'] = True
    if debug: userInput['debug'] = True
    
    sim = _MockSim(userInput, unifiedInput, False)
    sim.typeManager,sim.typeManagers = network.loadTypeManagers(userInput, unifiedInput, sim, verbose, debug)
    # unpack type managers
    for (attr,tm) in sim.typeManagers.items():
        setattr(sim, attr, tm)
    net = network.loadNetwork(userInput, sim.typeManager, sim.typeManagers)
    
    rMan = RDFManager()
    storeDict = {}
    for k,v in net.stores.items():
        storeDict[k] = rMan.createStoreEntity(v)
        
    for k,v in net.routes.items():
        rMan.createRouteEntity(v, storeDict)
        
    rMan.saveGraphToRDF("file:///%s"%outfname)
    """
    Creation of stores will have activated types.  typeManager.getActiveTypes() can get the types.
    
    traverse net.stores (a dict of stores by long int idcode)
    for each store,
      create the store
      traverse its inventory
      traverse its people
    traverse net.routes (a dict of routes by long int idcode)
    
    respond to Jim's comment at network.py:147
    """
    
############
# Main hook
############

if __name__=="__main__":
    main()
