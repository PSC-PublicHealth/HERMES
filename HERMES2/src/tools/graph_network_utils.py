#! /usr/bin/env python


__doc__=""" 
utility functions for creating graphs of the hermes network
"""
_hermes_svn_id_="$Id$"

import os.path
import sys

try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    # also need the directory above
    updir = os.path.join(cwd, '..')
    if updir not in sys.path:
        sys.path.append(updir)
except:
    pass

import gv
import string
import math
import types
import re

import ipath
from hermes_data import hermes_data_exception

_asciiTransTbl= None
def ascify(s):
    if isinstance(s,types.StringType): s = unicode(s,'utf-8',errors='replace')
    return s.encode('utf-8')
#    global _asciiTransTbl
#    if _asciiTransTbl is None:
#        _asciiTransTbl= bytearray('?'*256)
#        for i in string.printable: _asciiTransTbl[ord(i)]= i
#        _asciiTransTbl[ord(' ')]= '_'  # since gv seems to have trouble with strings including blanks
#    return s.translate(_asciiTransTbl)




ctbl= ["%5.3f 1.0 1.0"%(0.8-(0.8/9.0)*i) for i in xrange(10)]
def colorNameFromFraction(v):
    "This routine provides a sort of a color table"
    vTrunc= max(min(v,0.999),0.0)
    index= int(vTrunc*len(ctbl))
    return ctbl[index]

class HermesNetGraph:
    def __init__(self, net, attrib = None):
        """
        attrib is a dictionary can include the following options:
        show:    Can be 'fill' (default) or 'supplyratio'.
        vax:     Specifies a vaccine or a list of vaccines to calculate
                 supply ratio for.  [] chooses all.  Defaults to [].
        label:   Provide a label for the graph.
        root:    Set root of the graph to <idcode>.  Defaults to first fork
                 (self.trunkStore).  If set to None then does not set root.
        layout:  which graphviz layout type to use (default is circo).
        removeOrphans:
                 don't graph any store with no clients or suppliers if set to
                 True.

        """
        self.net = net
        self.g = None
        if attrib is None:
            attrib = {}

        # specify default attributes
        if not attrib.has_key('show'):
            attrib['show'] = 'fill'

        self.layout = 'circo'
        if attrib.has_key('layout'):
            self.layout = attrib['layout']

        if not attrib.has_key('removeOrphans'):
            attrib['removeOrphans'] = False

        self.attrib = attrib
        self.build_gv_graph()


    def _gv_setNodeColor(self, store, tags):
        # fix this when we get report data
        #if not rec.has_key('report'):
        attrib = self.attrib
        if 'resultsId' not in attrib:
            return 'lightgray'
        if attrib['resultsId'] not in store.reports:
            return 'yellow'
        rpt = store.reports[attrib['resultsId']]
        
#         if not hasattr(store, 'rpt') or store.rpt is None:
#             return 'lightgray'
#         rpt = store.rpt

        if attrib['show'] == 'fill':
            val = rpt.storage['cooler'].fillRatio
            if val == 'NA':
                color = 'lightgray'
                tags.append('cooler=NA')
            else:
                color = colorNameFromFraction(val)
                if val >= 0.8:
                    tags.append('cooler=%f'%val)
            return color

        elif attrib['show'] == 'supplyratio':
            print rpt.vax.keys()
            if not attrib.has_key('vax'):
                vax = list(rpt.vax.keys())
            elif attrib['vax'] is None:
                vax = list(rpt.vax.keys())
            elif isinstance(attrib['vax'], types.StringTypes):
                vax = [attrib['vax']]
            else:
                vax = attrib['vax']

            try:
                treated = patients = 0
                for vac in vax:
                    vaxrpt = rpt.vax[vac]
                    print rpt.resultsId
                    print store.idcode
                    print vaxrpt.treated
                    print vaxrpt.patients
                    treated += vaxrpt.treated
                    patients += vaxrpt.patients

                if patients == 0:
                    color = 'lightgray'
                    tags.append("no patients")
                else:
                    val = float(treated) / float(patients)
                    color = colorNameFromFraction(1.0 - val)
                    if val <= 0.2:
                        tags.append("supply ratio: %f"%val)
            except:
                return 'lightgray'
                #raise hermes_data_exception("vaccine info requested not in report")
        else:
            raise hermes_data_exception("invalid coloring request: %s"%self.attrib['show'])
        return color

    
    def _gv_nodeInfo(self, store):
        "Provide color shape and label for the graphical representation of a specific node"
        color = shape = label = None
        tags = []
        showName = True

        # define the shape based on function
        fn = store.FUNCTION
        if fn == 'Administration':
            # see if it's an attached clinic:
            shape = 'ellipse'
            try:
                (supplier, route) = store.suppliers()[0]
                if route.Type == 'attached':
                    shape = 'diamond'
            except:
                pass

        elif fn == 'Distribution':
            shape = 'box'

        elif fn == 'Surrogate':
            shape = 'doublecircle'
            showName = False
        
        else:
            shape = 'octagon'
            color = 'red'
            tags.append('unknown FUNCTION: %s'%fn)

        # color based on attributes
        if color is None:
            color = self._gv_setNodeColor(store, tags)
            
        if showName:
            label = '%s\n%s'%(ascify(store.NAME), store.idcode)
        else:
            label = '%s'%store.idcode
        for tag in tags:
            label += '\n%s'%tag

        return (shape, color, label)

    def _gv_edgeInfo(self, route):
        "provide color, style and label for the graphical representation of an edge"
        color = label = style = None
        tags = []
        
        if len(route.TruckType):
            tags.append(route.TruckType)
        tags.append(route.Type)

        # when we reattach reports, reset this condition
        if not hasattr(route, 'rpt') or route.rpt is None:
            color = 'black'
        else:
            rpt = route.rpt
            if self.attrib['show'] == 'fill':
                val = rpt.RouteFill
                color = colorNameFromFraction(val)
                if val >= 0.8:
                    tags.append('RouteFill=%f'%val)
            else:
                color = 'black'
        label = route.RouteName
        for tag in tags:
            label += '\n%s'%tag

        return (style, color, label)

    def _gv_addEdge(self, route, fr, to, scale, delay=0, constraint=True):

        if delay != 0:
            edgeparms = (route.name, fr, to, scale)
            self.delayedEdges.append(edgeparms)
            return

        style = color = label = None
        if route is None:
            color = 'black'
            label = 'default'
            style = 'dotted'
        else:
            style, color, label = self._gv_edgeInfo(route)

        edge = gv.edge(fr, to)
        gv.setv(edge, 'color', color)
        aL = str(ascify(label))
        gv.setv(edge, 'label', aL)
        if style is not None:
            gv.setv(edge, 'style', style)
        gv.setv(edge, 'fontsize', '%6.2f'%(0.5*scale))
        gv.setv(edge, 'penwidth', '%6.2f'%(0.05*scale))
        gv.setv(edge, 'arrowsize', '%6.2f'%(0.02*scale))
        if constraint is False:
            gv.setv(edge, 'constraint', 'false')

    def _gv_addStore(self, store, scale, memo):
        """
        Part of build_gv_graph().  
        
        Recursively adds a node, its children and its child edges.
        Returns the top node created so the edge from the top node
        and its parent can be built by the parent caller.
        """
        storeId = str(store.idcode)
        if storeId in memo:
            return memo[storeId]

        shape,color,label = self._gv_nodeInfo(store)
        try:
            node = gv.node(self.g, 'n_%s'%storeId)
        except Exception as e:
            print "Can't create node: for store %s!"%storeId
            raise e
        memo[storeId] = node
        gv.setv(node, 'hermes_id',   storeId)
        gv.setv(node, 'shape',       shape)
        gv.setv(node, 'color',       color)
        aL = str(ascify(label))
        gv.setv(node, 'label',       aL)
        gv.setv(node, 'fontsize',    "%6.2f"%scale)
        #gv.setv(node, 'URL','http://localhost:8080/foo')
        
        # create scaling factor for children and then process them
        clientCount = len(store.clients())
        if clientCount:
            sf = math.pow(clientCount, -0.5)

        processedRoutes = set()
        for (x, route) in store.clients():
            if route in processedRoutes:
                continue

            processedRoutes.add(route)
            lastNode = node
            for stop in route.stops:
                client = stop.store
                if client is store:
                    continue
                clientNode = self._gv_addStore(client, sf * scale, memo)
                self._gv_addEdge(route, lastNode, clientNode, scale)
                lastNode = clientNode

        return node


    def build_gv_graph(self):
        """
        Build a graphvis graph based on the system we've defined and any 
        attributes we've specified.  Call layout but don't render to
        anything yet.

        """

        if self.g is not None:
            gv.rm(self.g)
            self.g = None

        self.delayedEdges = []
        attrib = self.attrib

        g= gv.digraph('g')
        self.g = g

        gv.setv(gv.protonode(g),'style','filled')
        gv.setv(gv.protonode(g),'rank','min')
        #gv.setv(g,'overlap','prism')
        gv.setv(g,'mindist','0.1')
        gv.setv(g,'clusterrank','local')
        gv.setv(g,'compound','true')
        gv.setv(g,'fontsize','100.0')
        gv.setv(g,'charset','utf-8')
        gv.setv(g,'esep', '5')
        if attrib.has_key('label'):
            gv.setv(g, 'label', attrib['label'])
        
        memo = {}
        rootStores = self.net.rootStores()
        for st in rootStores:
            if attrib['removeOrphans']:
                if 0 == len(st.clients()):
                    continue
            self._gv_addStore(st, 100, memo)

        if not attrib.has_key('root'):
            trunkStore = self.net.trunkStore()
            attrib['root'] = trunkStore.idcode
        if attrib['root'] is not None:
            gv.setv(g, 'root', 'n_%s'%attrib['root'])

        for edge in self.delayedEdges:
            (rName, fr, to, scale) = edge
            self._gv_addEdge(rName, fr, to, scale, 0, False)

        gv.layout(g, self.layout)


    def destroy_gv_graph(self):
        if self.g is not None:
            gv.rm(self.g)
        self.g = None

    def get_gv_render(self, format):
        return gv.renderdata(self.g, format)

    def save_gv_render(self, format, filename):
        gv.render(self.g, format, filename + '.' + format)


    # this needs to be rebuilt
    def add_gv_locations(self):
        if self.g is None:
            self.build_gv_graph()

        dot = self.get_gv_render('xdot')
        (graph, tp) = dot_parser.parse_dot_text(dot)

        # get the size or "bounding box" of the graph
        bb = graph['graph']['bb']
        (xmin,ymin,xmax,ymax) = re.split(',', bb)
        if xmin != '0' or ymin != '0':
            raise hermes_data_exception("graphviz is using non-zero based bounding boxes!")
        graphHeight = float(ymax)
        graphWidth = float (xmax)
        self.globals['graphHeight'] = graphHeight
        self.globals['graphWidth'] = graphWidth

        # start attaching locations and sizes
        for key, store in self.stores.items():
            element = graph['n_%s'%key]
            pos = element['pos']
            width = element['width']
            height = element['height']
            (x,y) = re.split(',', pos)

            store['graph_x'] = float(x) / graphWidth
            store['graph_y'] = 1.0 - (float(y) / graphHeight)
            store['graph_w'] = float(width) / graphWidth
            store['graph_h'] = float(height) / graphHeight

        # now let's calculate a nice display box.
        # we just need a min width and height with the store centered
        # for leaf nodes include parent
        # for nodes with children, include the children

        for key, store in self.stores.items():
            locx = store['graph_x']
            locy = store['graph_y']

            disp_w = 0.0
            disp_h = 0.0
            if len(store['children']):
                # parents
                for c in store['children']:
                    disp_w = max(2 * math.fabs(self.stores[c]['graph_x'] - locx) + self.stores[c]['graph_w'],
                                 disp_w)
                    disp_h = max(2 * math.fabs(self.stores[c]['graph_y'] - locy) + self.stores[c]['graph_h'],
                                 disp_h)

            elif store['parent'] is not None:
                # leaves
                disp_w = 2 * math.fabs(self.stores[store['parent']]['graph_x'] - locx)
                disp_w += self.stores[store['parent']]['graph_w']
                disp_h = 2 * math.fabs(self.stores[store['parent']]['graph_y'] - locy)
                disp_h += self.stores[store['parent']]['graph_h']
            else:
                # wtf?  Who makes a graph with only one node
                disp_w = 0.5
                disp_h = 0.5

            store['disp_w'] = disp_w
            store['disp_h'] = disp_h

