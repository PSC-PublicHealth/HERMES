#! /usr/bin/env python

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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

__doc__=""" main.py
This is a utility for scanning HERMES input spreadsheets for errors.
"""
_hermes_svn_id_="$Id$"

import sys,os,optparse,types,math,string,os.path,base64
from collections import defaultdict
import pygraphviz as pgv

import ipath
import csv_tools, util

showWhat= None
vax= None
layoutAlg= "circo"
outBaseName= "check"
outFormat= "jpg"
verbose= False
debug= False
peopleTypes= ['GenericPeople'] # and supplemented later
_asciiTransTbl= None
referenceFilePath= None

outFormatExtensions= {"jpg":"jpg", "svg":"svg", "dot":"dot", "png":"png"}
#ctbl= ["violet","blue","cyan","green","greenyellow","yellow","orange","orangered","red"]
ctbl= ["%5.3f 1.0 1.0"%(0.8-(0.8/9.0)*i) for i in xrange(10)]

# Where to look in a route list for the supplier entry, by route type
offsetsByRouteType= {'push':0, 'varpush':0, 'pull':0, 'attached':0,
                     'schedfetch':1, 'schedvarfetch':1, 'demandfetch':1,
                     'askingpush':0, 'dropandcollect':0,
                     'persistentdemandfetch':1, 'persistentpull':0}

def colorNameFromFraction(v):
    "This routine provides a sort of a color table"
    vTrunc= max(min(v,0.999),0.0)
    index= int(vTrunc*len(ctbl))
    return ctbl[index]

def addLegend(g,scale=10.0):
    """
    This routine returns a GraphViz node with an HTML label designed to serve
    as a legend for the listed values.
    """
    g.add_node('legend')
    if showWhat == None:
    	labelString= '<tr><td bgcolor="none" border="0">Legend</td></tr>\n'
    elif showWhat == 'fill':
	labelString= '<tr><td bgcolor="none" border="0">Storage</td></tr><tr><td> Utilization Percentage</td></tr>\n'
    elif showWhat == 'supplyratio':
	labelString= '<tr><td bgcolor="none" border="0">Vaccine</td></tr><tr><td>Availability</td></tr>\n'
    vStep= 1.0/len(ctbl)
    for i in xrange(len(ctbl)):
        vMin= i*vStep
        vMax= vMin+vStep
        v= 0.5*(vMin+vMax)
        lbl= "%4.2f - %4.2f"%(vMin,vMax)
        if showWhat=='fill':
            clr= colorNameFromFraction(v)
        else:
            clr= colorNameFromFraction(1.0-v)
        labelString += '<tr><td bgcolor="%s">%s</td></tr>\n'%(clr,lbl)
    labelString= '<table border="0" cellborder="1" cellspacing="0">\n'+labelString+'</table>'
    labelString= '<<font point-size="%f">\n'%scale+labelString+'\n</font>>'
    n = g.get_node('legend')
    n.attr.update({'label': labelString,
                   'pos': "10000,200",
                   'shape': 'plaintext',
                   'color': 'none'})
    return n

def _decomposeId(code):
    #print "decomposeId: %d -> "%code,
    clinicCode= code % 100
    code /= 100
    districtCode= code % 100
    code /= 100
    regionCode= code % 100
    #print "(%d,%d,%d)"%(regionCode,districtCode,clinicCode)
    return (regionCode,districtCode,clinicCode)

def _composeId(regionCode,districtCode,clinicCode):
    result= long("%d%02d%02d%02d"%(1,regionCode,districtCode,clinicCode))
    #print "composeId: (%d %d %d) -> %ld"%(regionCode,districtCode,
    #                                      clinicCode,result)
    return result

def _deadWarehouse(rec):
    return (_getTotalPop(rec)==0 and _getTotalStorage(rec)==0)

def _getDefaultSupplier(rec):
    code= long(rec['idcode'])
    regionCode,districtCode,clinicCode= _decomposeId(code)
    if regionCode==0 and districtCode==0 and clinicCode==0:
        return None # This is the central store
    else:
        if districtCode==0 and clinicCode==0:
            # region; supplier is central store
            return _composeId(0,0,0) 
        elif clinicCode==0:
            # district; supplier is region
            return _composeId(regionCode,0,0) 
        else:
            # clinic; supplier is district
            return _composeId(regionCode,districtCode,0) 


def guessSupplierID(rec):
    """
    This routine is the analog of the HERMES Model.getDefaultSupplier() method.
    It uses a really stupid heuristic which happens to work for the current 
    set of models (as of September 2010).
    """
    id= rec['idcode']
    if id>1000000:
        # This is the old 7 digit form
        return _getDefaultSupplier(rec)
    else:
        if id>10000:
            return id % 10000
        else:
            return None
        
def _getTotalPop(rec):
    totPop= 0
    for k in rec.keys():
        if k.find('Population')>=0:
            if type(rec[k])!=types.StringType:
                totPop += rec[k]
    for pt in peopleTypes:
        if rec.has_key(pt) and rec[pt]!='':
            totPop += rec[pt]
    return totPop

def _getTotalStorage(rec):
    totVol= 0.0
    for k in rec.keys():
        if k.find('(lit)')>=0.0 and rec[k]!='':
            totVol += rec[k]
    return totVol

def _copyGVNode(oldNode,newGraph):
    newGraph.add_node(oldNode.name)
    n = newGraph.get_node(oldNode.name)
    n.attr.update(oldNode.attr)
    return n

def _copyGVDigraphWithClusters(oldHead, oldDigraph, newDigraph):
    newHead= _copyGVNode(oldHead,newDigraph)
    for oldEdge in oldDigraph.out_edges_iter([oldHead]):
        oldTarget= oldEdge[1]
        if 'hermes_cluster' in oldTarget.attr and len(oldTarget.attr['hermes_cluster']) > 0:
            clName = oldTarget.attr['hermes_cluster']
            newDigraph.add_subgraph(name=clName)
            subDigraph = newDigraph.get_subgraph(clName)
        else:
            subDigraph= newDigraph
        newTarget= _copyGVDigraphWithClusters(oldTarget,subDigraph)
        newDigraph.add_edge(newHead, newTarget, **oldEdge.attr)
    return newHead

def _copyGVDigraph(oldHead, oldDigraph, newDigraph):
    newHead= _copyGVNode(oldHead,newDigraph)
    for oldEdge in oldDigraph.out_edges_iter([oldHead]):
        if newDigraph.has_node(oldEdge[1]):
            newTarget = newDigraph.get_node(oldEdge[1])
        else:
            newTarget = _copyGVDigraph(oldEdge[1], oldDigraph, newDigraph)
        newDigraph.add_edge(newHead, newTarget)
    return newHead

def _copyGVDigraphBreadthFirst(oldHead, oldDigraph, newDigraph,newHead=None,depth=0,maxDepth=None):
    #print "depth= %d of %s"%(depth, maxDepth)
    if newHead is None:
        newHead= _copyGVNode(oldHead,newDigraph)
    if maxDepth is not None and depth>=maxDepth:
        return
    currentNodes= {}
    for oldEdge in oldDigraph.out_edge_iter([oldHead]):
        oldTarget= oldEdge[1]
        newTarget= _copyGVNode(oldTarget, newDigraph)
        if oldTarget.name not in currentNodes:
            currentNodes[oldTarget.name] = newTarget
        newEdge= newDigraph.add_edge(newHead, newTarget, **oldEdge.attr)
    for oldNode, newNode in currentNodes.items():
        _copyGVDigraphBreadthFirst(oldNode, 
                                   oldDigraph, newDigraph,newNode,depth=depth+1,maxDepth=maxDepth)
    return newHead

def findHeads(digraph):
    edgeL = digraph.edges()
    stepCounter = len(edgeL)
    parentD = defaultdict(list)
    for head, tail in edgeL:
        parentD[tail].append(head)

    headSet = set()
    nodeStack = [edgeL[0][0].name]
    while nodeStack:
        node = nodeStack.pop()
        if parentD[node]:
            print '%s -> %s' % (node, parentD[node])
            nodeStack.extend(parentD[node])
        else:
            headSet.add(node)
        stepCounter -= 1
        if stepCounter < 0:
            raise RuntimeError('Infinite loop seeking the head nodes!')

    return headSet

def findHead(digraph):
    headL = list(findHeads(digraph))
    if len(headL) != 1:
        raise RuntimeError('Cannot find head of the graph!')
    return headL[0]

def copyDigraphEmpty(oldDigraph):
    """Return a new digraph with all the same settings but no nodes or edges"""
    newDigraph= pgv.AGraph(strict=oldDigraph.strict,
                           directed=oldDigraph.directed,
                           name=oldDigraph.name)
    newDigraph.graph_attr.update(oldDigraph.graph_attr)
    newDigraph.node_attr.update(oldDigraph.node_attr)
    newDigraph.edge_attr.update(oldDigraph.edge_attr)
    return newDigraph
    
def cloneWithClusters(oldDigraph):
    """
    Produce a graph equivalent to the input graph (produced by buildHermesNetworkGraph),
    but with clustering information appropriate for the GraphVis 'dot' layout engine.
    """
    headNode= findHead(oldDigraph)

    # Do the cloning operation
    newDigraph = copyDigraphEmpty(oldDigraph)
    newHead= _copyGVDigraphWithClusters(headNode, oldDigraph, newDigraph)
    return newDigraph

def clone(oldDigraph):
    """
    Produce a graph equivalent to the input graph (produced by buildHermesNetworkGraph),
    but with the nodes generated in depth-first order.
    """
    headNode= findHead(oldDigraph)

    # Do the cloning operation
    newDigraph = copyDigraphEmpty(oldDigraph)
    newHead= _copyGVDigraph(headNode, oldDigraph, newDigraph)
    return newDigraph

def cloneBreadthFirst(oldDigraph,maxDepth=None):
    """
    Produce a graph equivalent to the input graph (produced by buildHermesNetworkGraph),
    but with the nodes generated in depth-first order.
    """
    headNode= findHead(oldDigraph)

    # Do the cloning operation
    newDigraph = copyDigraphEmpty(oldDigraph)
    newHead= _copyGVDigraphBreadthFirst(headNode, oldDigraph, newDigraph,maxDepth=maxDepth)
    return newDigraph

def getNodeInfo(rec):
    "Returns a tuple 'color,note' with info to be associated with the node"
    if showWhat=='fill':
        val= rec['cooler']
        if val=='NA':
            clr= "lightgray"
            note= "\ncooler=NA"
        else:
            clr= colorNameFromFraction(val)
            if val>=0.8: note= "\n%s=%f"%('cooler',val)
            else: note= None
    elif showWhat=='supplyratio':
        try:
            treated= rec["%s_treated"%vax]
            patients= rec["%s_patients"%vax]
            if treated=='NA' or patients=='NA':
                clr= "gray"
                note= ""
            elif patients==0:
                clr= "lightgray"
                note= "\nno patients"
            else:
                val= float(treated)/float(patients)
                clr= colorNameFromFraction(1.0-val)
                if val<=0.2: note= "\n%s=%f"%('supply ratio',val)
                else: note= ""
        except:
            print rec
            print "%s_treated"%vax
            print "%s_patients"%vax
            raise RuntimeError("Report file doesn't contain info for requested supply ratio")
    else:
        raise RuntimeError("unknown 'show' option %s"%showWhat)
    return clr,note

def getEdgeInfo(rec):
    "Returns a tuple 'color,note' with info to be associated with the edge"
    if showWhat=='fill' and 'RouteFill' in rec:
        val= rec['RouteFill']
        if val=='NA':
            edgeColor= "lightgray"
            labelTail="\nRouteFill=%s"%val
        else:
            edgeColor= colorNameFromFraction(val)
            if val>=0.8: labelTail="\nRouteFill=%f"%val
            else: labelTail= None
        return edgeColor,labelTail
    else:
        return "black",None

def findMaxDepthBelow(node, graph):
    maxDepth = 1
    for e in graph.out_edge_iter([node]):
        thisD = findMaxDepthBelow(e[1], graph) + 1
        if thisD > maxDepth:
            maxDepth = thisD
    return maxDepth

def getOutEdges(node, graph):
    return graph.out_edges([node])

def _propogateWeights(nodeL, graph, baseWt):
    for n in nodeL:
        graph.get_node(n).attr['hrm_wt'] = float(graph.get_node(n).attr['hrm_wt']) + baseWt
        edgeL = graph.out_edges([n])
        if edgeL:
            _propogateWeights([e[1] for e in edgeL], graph, baseWt/min(len(edgeL), 3))

def _wtToScale(wt, minWt, maxWt):
    #return math.exp(-0.05*((maxWt - wt)/(wt + 0.01 - minWt)))
    return ((wt + 0.01 - minWt)/(maxWt - minWt))

def setScale(nodeL,graph,baseScale):
    for n in graph.nodes():
        n.attr['hrm_wt'] = 0.0
    _propogateWeights(findHeads(graph), graph, 1.0)
    maxWt = max([float(n.attr['hrm_wt']) for n in graph.nodes_iter()])
    minWt = min([float(n.attr['hrm_wt']) for n in graph.nodes_iter()])
    print 'maxWt = %s, minWt= %s' % (maxWt, minWt)
    for n in graph.nodes():
        wt = float(n.attr['hrm_wt'])
        scale = _wtToScale(wt, minWt, maxWt)
        n.attr['fontsize'] = "%6.2f"%(scale * baseScale)
    for e in graph.edges():
        wt = float(graph.get_node(e[1]).attr['hrm_wt'])
        scale = _wtToScale(wt, minWt, maxWt)
        edge = graph.get_edge(*e)
        edge.attr['fontsize'] = "%6.2f"%(0.5*baseScale*scale)
        edge.attr['penwidth'] = "%6.2f"%(0.1*baseScale*scale)
        edge.attr['arrowsize'] = "%6.2f"%(0.02*baseScale*scale)
    
def ascify(str):
    global _asciiTransTbl
    if _asciiTransTbl is None:
        _asciiTransTbl= bytearray('?'*256)
        for i in string.printable: _asciiTransTbl[ord(i)]= i
        _asciiTransTbl[ord(' ')]= '_'  # since gv seems to have trouble with strings including blanks
    return str.translate(_asciiTransTbl)

def buildHermesNetworkGraph(whRecs,routeRecs,peopleRecs,reportRecs=None):
    """
    This routine takes 'standard' HERMES input table rows and produces
    a GraphVis graph.  whRecs, routeRecs and peopleRecs are the
    lists of record dictionaries produced by loading the warehouse,
    route, and peopletype definition spreadsheet files.  If reportRecs
    is given, values are taken from the report data to add color to the graph.
    
    The returned graph is a digraph.  Each node contains an attribute 
    'hermes_id' containing the corresponding 'idcode' value as a string.
    Those which form a cluster contain an attribute 'hermes_cluster' 
    containing the cluster name- but note that they are not in a GraphVis
    cluster subgraph.  See cloneWithClusters() to convert the graph to
    an equivalent graph with cluster subgraphs.
    """

    global peopleTypes
    
    # Load people types so we can recognize those columns
    for rec in peopleRecs:
        if rec['Name'] not in peopleTypes:
            peopleTypes.append(rec['Name'])

    # Sort out the routes
    routeDict= {}
    for rec in routeRecs:
        rname= rec['RouteName']
        if not routeDict.has_key(rname):
            routeDict[rname]= []
        routeDict[rname].append((int(rec['RouteOrder']),rec))
    for k in routeDict.keys():
        l= routeDict[k]
        l.sort()
        routeDict[k]= [rec for junk,rec in l]
        
    # Sort out the report records, if given
    routeReportDict= {}
    whReportDict= {}
    if reportRecs is not None:
        for r in reportRecs:
            if r.has_key('code'):
                whReportDict[r['code']]= r
            if r.has_key('RouteName'):
                routeReportDict[r['RouteName']]= r
    
    # Build the graph
    g= pgv.AGraph(strict=False, directed=True)
    g.node_attr['style'] = 'filled'
    g.node_attr['rank'] = 'min'
    g.node_attr['fixedsize'] = 'false'
    g.graph_attr['mindist'] = '0.1'
    g.graph_attr['clusterrank'] = 'local'
    g.graph_attr['compound'] = 'true'
    nodeDict= {}
    nodeRecDict= {}
    for rec in whRecs:
        id= int(rec['idcode'])
        g.add_node('n%d'%id)
        n= g.get_node('n%d'%id)
        nName= rec['NAME']
        nodeDict[id] = n
        n.attr['hermes_id'] = '%d'%id
        labelTail= ""
        if whReportDict.has_key(id):
            clr,labelTail= getNodeInfo(whReportDict[id])
            if labelTail is None: labelTail= ""
            n.attr['color'] = clr
        else: 
            n.attr['color'] = 'lightgray'
        if rec.has_key('FUNCTION'):
            if rec['FUNCTION']=='Administration':
                if _getTotalStorage(rec)==0.0:
                    n.attr['shape'] = 'diamond' # these should be 'attached' clinics
                    n.attr['label'] = "%s\n%s%s"%(ascify(nName), id,labelTail)
                else:
                    n.attr['label'] = '%s\n%s%s'%(ascify(nName),id,labelTail)
                    n.attr['shape'] = 'ellipse'
            elif rec['FUNCTION']=='Distribution':
                n.attr['label'] = '%s\n%s%s'%(ascify(nName),id,labelTail)
                n.attr['shape'] = 'box'
            elif rec['FUNCTION']=='Outreach':
                n.attr['label'] = '%s\n%s%s'%(ascify(nName),id,labelTail)
                n.attr['shape'] = 'house'
            elif rec['FUNCTION']=='Surrogate':
                n.attr['shape'] = 'doublecircle' # these should be 'attached' clinics
                n.attr['label'] = "%s%s"%(id,labelTail)
            else:
                n.attr['shape'] = 'octagon'
                n.attr['color'] = 'red'
                n.attr['label'] = '%s\n%s\n%s%s'%(ascify(nName),id,rec['FUNCTION'],labelTail)
        else:
            totPop= _getTotalPop(rec)
            if totPop !=0:
                if _getTotalStorage(rec)==0.0:
                    n.attr['label'] = 'label','%s\n%s%s'%(ascify(nName),id,labelTail)
                    n.attr['shape'] = 'diamond' # these should be 'attached' clinics
                else:
                    n.attr['label'] = '%s\n%s%s'%(ascify(nName),id,labelTail)
                    n.attr['shape'] = 'ellipse'
            else:
                n.attr['label'] = '%s\n%s%s'%(ascify(nName),id,labelTail)
                n.attr['shape'] = 'box'
        nodeRecDict[id]= rec
    for routeName in routeDict.keys():
        edgeList= []
        stops= routeDict[routeName]
        supplierOffset = offsetsByRouteType[stops[0]['Type']]
        if supplierOffset == 0:
            fromRec= stops[0]
            stops= stops[1:]
        elif supplierOffset == 1:
            fromRec= stops[1]
            if len(stops) > 2:
                stops= stops[0:1] + stops[2:]
            else:
                stops= stops[0:1]
        else:
            raise RuntimeError("Confused by unknown route type %s"%stops[0]['Type'])
        if routeReportDict.has_key(routeName):
            edgeColor, labelTail= getEdgeInfo(routeReportDict[routeName])
            if labelTail==None: labelTail= ""
        else:
            edgeColor= "black"
            labelTail= ""
        stopsSeenIDs = set()
        for rec in stops:
            fromID= int(fromRec['idcode'])
            toID= rec['idcode']
            if toID not in stopsSeenIDs: # Avoid two-visit loops like dropandretrieve
                stopsSeenIDs.add(toID)
                g.add_edge(nodeDict[fromID],nodeDict[toID])
                edge = g.get_edge(nodeDict[fromID],nodeDict[toID])
                edge.attr['color'] = edgeColor
                if rec.has_key('TruckType'):
                    edge.attr['label'] = "%s\n%s\n%s%s" % (routeName,
                                                           rec['TruckType'],
                                                           rec['Type'],
                                                           ascify(labelTail))
                else:
                    edge.attr['label'] = "%s\n%s%s"%(routeName,rec['Type'],ascify(labelTail))
                edgeList.append(edge)
            fromRec= rec
            
    # Scan for loose nodes, and try to attach them
    for id,node in nodeDict.items():
        nLinks= 0
        if len(g.edges([node.name])) == 0:
            rec= nodeRecDict[id]
            if _deadWarehouse(rec):
                node.attr['style'] = 'dashed'
            else:
                supplierID= guessSupplierID(rec)
                if supplierID is None:
                    node.attr['color'] = 'red'
                else:
                    g.add_edge(nodeDict[supplierID].name, node.name)
                    edge = g.get_edge(nodeDict[supplierID].name, node.name)
                    edge.attr['label'] = 'default'
                    edge.attr['style'] = 'dotted'

    # Scan for clusters, and add cluster information
    for id,node in nodeDict.items():
        edgeL = g.edges([node.name])
        numInEdges = len([edge for edge in edgeL if edge[1] == node.name])
        numOutEdges = len([edge for edge in edgeL if edge[0] == node.name])
        if numInEdges==1 and numOutEdges>3:
            nodeRec= nodeRecDict[id]
            node.attr['hermes_cluster'] = ascify(nodeRec['NAME'])
    g.graph_attr['fontsize'] = '100.0'
    #setScale(findHead(g),g,100.0)
    setScale(findHeads(g),g,100.0)
    
    return g
                           
###########
# main
###########

def main():
    global outBaseName, verbose, debug, peopleTypes, layoutAlg, outFormat, showWhat, vax, referenceFilePath

    parser= optparse.OptionParser(usage="""
    %prog [-v][-d][--help][--out outbasename][--layout gvname][--type type]
        [--report reportFile] [--show whatToShow] [--vax vaxName] [--label someText]
        [--refpath referenceFilePath] warehouseFile routeFile
    """)
    parser.add_option("-v","--verbose",action="store_true",help="verbose output")
    parser.add_option("-d","--debug",action="store_true",help="debugging output")
    parser.add_option("--out",help="filename base for outputs")
    parser.add_option("--layout",
                      help="One of the GraphVis layout engines.  Default is circo; others include dot, neato, and twopi")
    parser.add_option("--type",
                      help="Data type for output file.  Default is jpg; others include png, svg, and dot")
    parser.add_option("--cluster",action="store_true",
                      help="Add cluster cluster information to graph.  Only the dot renderer seems to respect this info.")
    parser.add_option("--report",
                      help="A CSV file like report.csv, from which color info can be drawn")
    parser.add_option("--vax",
                      help="Vaccine for which to calculate the displayed quantity, if applicable")
    parser.add_option("--show",
                      help="One of 'fill','supplyratio'.  Default is 'fill'.",
                      default="fill")
    parser.add_option("--label",
                      help="Provide an overall label for the graph")
    parser.add_option("--b64label",
                      help="label text encoded in base64")
    parser.add_option("--root", type="long",
                      help="Specify the ID number of the node to place at the center of the graph")
    parser.add_option("--legend", action="store_true",
                      help="Cause a legend to be drawn")
    parser.add_option("--refpath",help="Specify the directory in which to find reference files like UnifiedPeopleTypeInfo")
    parser.add_option("--override",action="store_true",default=False,
                      help="override the deprecation warning")
    
    opts,args= parser.parse_args()

    print "This is deprecated.  Try using tools/ngn.py."
    if opts.override is False:
        return

    if len(args)!=2:
        parser.error("Found %d arguments, expected 2"%len(args))

    reportFile= None
    reportRecs= None
    label= None
    rootID= None
    
    # Parse args
    if opts.verbose:
        verbose= True
        csv_tools.verbose= True
    if opts.debug:
        debug= True
        csv_tools.debug= True
    if opts.out:
        outBaseName= opts.out
    if opts.layout:
        layoutAlg= opts.layout
    if opts.type:
        outFormat= opts.type
    addClusterInfo= opts.cluster
    if opts.report:
        reportFile= opts.report
    if opts.refpath:
        referenceFilePath= opts.refpath
    if opts.show:
        showWhat= opts.show
        if opts.show=="supplyratio" and opts.vax is None:
            raise RuntimeError("For --show supplyratio you must specify a vaccine name via --vax")
    if opts.vax:
        vax= opts.vax
    if opts.label:
        label= opts.label
    if opts.b64label:
        label = base64.b64decode(opts.b64label)
    if opts.root:
        rootID= int(opts.root)

    # Clean up command line parser
    parser.destroy()

    # Ingest the files
    with open(util.getDataFullPath(args[0]),"rU") as f:
        whKeys,whRecs= csv_tools.parseCSV(f)
    with open(util.getDataFullPath(args[1]),"rU") as f:
        routeKeys, routeRecs= csv_tools.parseCSV(f)
    if referenceFilePath is None:
        with open(util.getDataFullPath('UnifiedPeopleTypeInfo.csv'),'rU') as f:
            peopleKeys, peopleRecs= csv_tools.parseCSV(f)
    else:
        with open(os.path.join(referenceFilePath,'UnifiedPeopleTypeInfo.csv'),'rU') as f:
            peopleKeys, peopleRecs= csv_tools.parseCSV(f)
    if reportFile:
        with open(util.getDataFullPath(reportFile),"rU") as f:
            reportKeys, reportRecs= csv_tools.parseCSV(f)

    # Build the raw graph
    g= buildHermesNetworkGraph(whRecs,routeRecs,peopleRecs,reportRecs)
    if rootID:
        g.graph_attr['root'] = 'n%ld'%rootID

    if addClusterInfo:
        g= cloneWithClusters(g)
    else:
        #g= cloneBreadthFirst(g,maxDepth=None) # recreating in depth-first order helps layout
        pass

    if label is not None:
        g.graph_attr['label'] = label
        
    if opts.legend:
        addLegend(g,scale=30.0)

    g.layout(prog=layoutAlg)
    if outFormatExtensions.has_key(outFormat):
        outExtension= outFormatExtensions[outFormat]
    else:
        outExtension= outFormat
        
    g.draw('%s.%s'%(outBaseName,outExtension))

############
# Main hook
############

if __name__=="__main__":
    main()
