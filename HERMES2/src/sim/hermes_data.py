#! /usr/bin/env python



__doc__=""" 
This is a utility for getting data from hermes input and output csv files.
It is primarily intended for use by the gui.
"""
_hermes_svn_id_="$Id$"

import sys,os,optparse,types,math,string,os.path,base64,re
import gv
import dot_parser

from csv_tools import parseCSV, castTypes, castColumn, castFail
from util import getDataFullPath

# BUGS:
#    There is no check/mark for dead warehouses
#    There is no code to create a legend



_asciiTransTbl= None
def ascify(str):
    global _asciiTransTbl
    if _asciiTransTbl is None:
        _asciiTransTbl= bytearray('?'*256)
        for i in string.printable: _asciiTransTbl[ord(i)]= i
        _asciiTransTbl[ord(' ')]= '_'  # since gv seems to have trouble with strings including blanks
    return str.translate(_asciiTransTbl)



ctbl= ["%5.3f 1.0 1.0"%(0.8-(0.8/9.0)*i) for i in xrange(10)]
def colorNameFromFraction(v):
    "This routine provides a sort of a color table"
    vTrunc= max(min(v,0.999),0.0)
    index= int(vTrunc*len(ctbl))
    return ctbl[index]


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

def _getDefaultSupplier(child):
    code= long(child)
    regionCode,districtCode,clinicCode = _decomposeId(code)
    if (0 == regionCode) and (0 == districtCode) and (0 == clinicCode):
        return None # This is the central store

    if (0 == districtCode) and (0 == clinicCode):
        # region; supplier is central store
        return _composeId(0,0,0) 

    if 0 == clinicCode:
        # district; supplier is region
        return _composeId(regionCode,0,0) 

    # clinic; supplier is district
    return _composeId(regionCode,districtCode,0) 


def guessStoresParent(child):
    """
    This routine is the analog of the HERMES Model.getDefaultSupplier() method.
    It uses a really stupid heuristic which happens to work for the current 
    set of models (as of September 2011).
    """
    child = long(child)
    if child > 999999:
        # This is the old 7 digit form
        return _getDefaultSupplier(child)
    else:
        if child > 9999:
            return "%d"%(child % 10000)
        else:
            return None
        

class hermes_data_exception(Exception):
    def __init__(self, exceptString):
        self.exceptString = exceptString
    def __str__(self):
        return "*** hermes_data exception: %s ***"%self.exceptString


class hermes_data:

    def _getTotalPop(self, rec):
        totPop= 0
        if 0:  # I think this is not a valid way of looking for population anymore
            for k in rec.keys():
                if k.find('Population')>=0:
                    if type(rec[k])!=types.StringType:
                        totPop += rec[k]
        for pt in self.peopleTypes:
            if rec.has_key(pt) and rec[pt]!='':
                totPop += rec[pt]
        return totPop

    def _getTotalStorage(self, rec):
        totVol= 0.0
        for k in rec.keys():
            try:
                if k.find('(lit)') >= 0:
                    lit = float(rec[k])
                    totVol += lit
            except:
                pass
        return totVol

    def _normalize(self, store):
        """
        Make sure that all stores records have several fields that are either normally
        computed from the csv files or sometimes exist but are otherwise useful to have.
        
        FUNCTION: exists in some csvs, implied from population if doesn't exist
        totPop
        totStorage

        """
        if not store.has_key('totPop'):
            store['totPop'] = self._getTotalPop(store)
        if not store.has_key('totStorage'):
            store['totStorage'] = self._getTotalStorage(store)

        if not store.has_key('FUNCTION'):
            if store['totPop'] != 0:
                store['FUNCTION'] = 'Administration'
            else:
                store['FUNCTION'] = 'Distribution'

    def _readStores(self, storesFile):
        """
        read in the stores file and create self.stores.
        self.stores should be the primary data structure for this whole thing.

        storesFile should either be an open file handle or a full pathname.
        """
        if hasattr(storesFile,"read"):
            self.whKeys, whRecs= parseCSV(storesFile)
        else:
            # don't use getDataFullPath here
            with open(storesFile,"rU") as f:
                self.whKeys, whRecs= parseCSV(f)

        castColumn(whRecs, 'NAME',     castTypes.STRING)
        castColumn(whRecs, 'NewName',     (castTypes.STRING, castTypes.EMPTY))
        castColumn(whRecs, 'idcode',   castTypes.STRING)
        # what other columns should I cast/validate
        castColumn(whRecs, 'Walk in -(lit)', (castTypes.FLOAT, castTypes.EMPTY_IS_ZERO))
        castColumn(whRecs, 'Walk in +(lit)', (castTypes.FLOAT, castTypes.EMPTY_IS_ZERO))
        castColumn(whRecs, 'VOL - (lit)', (castTypes.FLOAT, castTypes.EMPTY_IS_ZERO))
        castColumn(whRecs, 'VOL + (lit)', (castTypes.FLOAT, castTypes.EMPTY_IS_ZERO))
        
        # Now let's reframe the the stores as a dictionary keyed by idcode
        # this is going to be the basis for our main datastore
        self.stores = {}
        for rec in whRecs:
            self.stores[rec['idcode']] = rec

    def _readRoutes(self, routesFile):
        """
        parse the routes file and attach the data to self.stores

        routesFile should either be an open file handle or a full pathname.
        """
        if hasattr(routesFile,"read"):
            self.routeKeys, routeRecs = parseCSV(routesFile)
        else:
            # don't use getDataFullPath here
            with open(routesFile,"rU") as f:
                self.routeKeys, routeRecs= parseCSV(f)
        
        castColumn(routeRecs, 'RouteName',    castTypes.STRING)
        castColumn(routeRecs, 'idcode',       castTypes.STRING)
        castColumn(routeRecs, 'RouteOrder',   castTypes.INT)
        castColumn(routeRecs, 'TransitHours', (castTypes.FLOAT, castTypes.EMPTY_IS_ZERO))
        castColumn(routeRecs, 'TruckType',    (castTypes.STRING, castTypes.EMPTY_IS_NULL_STRING))
        castColumn(routeRecs, 'ShipIntervalDays', (castTypes.FLOAT, castTypes.EMPTY_IS_ZERO))
        castColumn(routeRecs, 'ShipLatencyDays', (castTypes.FLOAT, castTypes.EMPTY_IS_ZERO))

        # Clean up the routes
        self.routes = {}
        backwardRouteTypes = ["demandfetch","schedvarfetch","schedfetch","persistentdemandfetch"]
        
        # first go through and find the lowest RouteOrder route entry
        # for each route.  This is both the "parent" of the route and 
        # assumed to have the core information
        for rec in routeRecs:
            rname = rec['RouteName']
            if not self.routes.has_key(rname):
                self.routes[rname] = rec
            if rec['Type'] in backwardRouteTypes:
                if self.routes[rname]['RouteOrder'] > 1:
                    raise RuntimeError("hermes_data does not support pull route types with more than one stop")
                if rec['RouteOrder'] == 1:
                    self.routes[rname] = rec
            else:
                if self.routes[rname]['RouteOrder'] > rec['RouteOrder']:
                    self.routes[rname] = rec
            self.routes[rname]['stops'] = []

        for rec in routeRecs:
            rname = rec['RouteName']
            stop_rec = (rec['RouteOrder'], 
                        rec['idcode'], 
                        rec['TransitHours'],
                        rec)
            self.routes[rname]['stops'].append(stop_rec)

        for key,route in self.routes.items():
            route['stops'].sort()

    def _readPeopleTypes(self, peopleFile):
        """
        read in the people type file
        peopleFile should either be an open file handle or a full pathname.
        """
        if hasattr(peopleFile,"read"):
            peopleKeys, peopleRecs= parseCSV(peopleFile)
        else:
            # don't use getDataFullPath here
            with open(peopleFile,'rU') as f:
                peopleKeys, peopleRecs= parseCSV(f)

        self.peopleTypes= ['GenericPeople']
        for rec in sorted(peopleRecs, key=lambda rec: rec['SortOrder']):
            if rec['Name'] not in self.peopleTypes:
                self.peopleTypes.append(rec['Name'])


    def _readReports(self, reportsFile):
        """
        read a reports file into memory and validate various fields.

        Since we now need to deal with an average file lots of seemingly integer
        fields can be floats.

        reportsFile should either be an open file handle or a full pathname.
        """
 
        if hasattr(reportsFile,"read"):
            self.reportKeys, reportRecs = parseCSV(reportsFile)
        else:
            # don't use getDataFullPath here
            with open(reportsFile,"rU") as f:
                self.reportKeys, reportRecs= parseCSV(f)

        castColumn(reportRecs, 'code',           (castTypes.NA, castTypes.STRING))
        castColumn(reportRecs, 'name',           (castTypes.NA, castTypes.STRING))
        castColumn(reportRecs, 'cooler',         (castTypes.NA, castTypes.FLOAT))
        castColumn(reportRecs, 'freezer',        (castTypes.NA, castTypes.FLOAT))

        castColumn(reportRecs, 'RouteName',      (castTypes.NA, castTypes.STRING))
        castColumn(reportRecs, 'RouteFill',      (castTypes.NA, castTypes.FLOAT))
        castColumn(reportRecs, 'RouteTrips',     (castTypes.NA, castTypes.FLOAT))
        castColumn(reportRecs, 'RouteTruckType', (castTypes.NA, castTypes.STRING))

        for key in self.reportKeys:
            m = re.match(r"^(.+)_treated$", key)
            if m is not None:
                vax = m.group(1)
                self.vaxList.append(vax)
                castColumn(reportRecs, "%s_patients"%vax,    (castTypes.NA, castTypes.FLOAT))
                castColumn(reportRecs, "%s_treated"%vax,     (castTypes.NA, castTypes.FLOAT))
                castColumn(reportRecs, "%s_vials"%vax,       (castTypes.NA, castTypes.FLOAT))
                castColumn(reportRecs, "%s_outages"%vax,     (castTypes.NA, castTypes.FLOAT))


        # let's attach the report records to the stores and routes
        for r in reportRecs:
            #############
            # ***BUG***
            # need to make output file return 'NA' again in the 'code' field for non-warehouses.
            if not (r['code'] == 'NA' or r['code'] == '0'):
                if r['code'] not in self.stores: continue
                self.stores[r['code']]['report'] = r
            if not r['RouteName'] == 'NA':
                if r['RouteName'] not in self.routes: continue
                self.routes[r['RouteName']]['report'] = r


    def __init__(self, storesFile, 
                 routesFile, 
                 reportsFile=None, 
                 peopleFile='UnifiedPeopleTypeInfo.csv'):
        "Initially just consume the csv's and then build up a graph."
        
        self.vaxList = []  # let's always at least have a stub of a vaxlist
        self.g = None
        self.globals = {}

        # Ingest the files
        self._readStores(storesFile)
        self._readRoutes(routesFile)
        self._readPeopleTypes(peopleFile)
        if reportsFile:
            self._readReports(reportsFile)

        # let's add a few fields to the stores that we're going to use in a bit
        for key,store in self.stores.items():
            store['parent'] = None
            store['parentRoute'] = None
            store['children'] = []
            store['childRoutes'] = []

        # let's attach routes to the stores
        backwardRouteTypes = ["demandfetch","schedvarfetch","schedfetch","persistentdemandfetch"]
        for rname,route in self.routes.items():
            if route['Type'] in backwardRouteTypes:
                if len(route['stops']) > 2:
                    raise RuntimeError("hermes_data does not support pull route types with more than one stop")
                parent = route['idcode']
                self.stores[parent]['childRoutes'].append(rname)
                child = route['stops'][0][1]
                self.stores[child]['parent'] = parent
                self.stores[child]['parentRoute'] = rname
                self.stores[parent]['children'].append(child)
            else:
                parent = route['idcode']
                self.stores[parent]['childRoutes'].append(rname)
                for (order,child,transit,rec) in route['stops'][1:]:
                    self.stores[child]['parent'] = parent
                    self.stores[child]['parentRoute'] = rname
                    self.stores[parent]['children'].append(child)
        # get the orphan stores and find their parents
        for key,store in self.stores.items():
            if None == store['parent']:
                parent = guessStoresParent(key)
                if parent is not None:
                    parent = str(parent)
                    if parent in self.stores:
                        store['parent'] = parent
                        self.stores[parent]['children'].append(key)

        # get our root store and trunk store
        self.rootStores = []
        for key, store in self.stores.items():
            if store['parent'] is None:
                self.rootStores.append(key)
        if len(self.rootStores) == 0:
            raise hermes_data_exception("There is no root node!")

        self.rootStores.sort()
        self.trunkStore = self.rootStores[0]
        while(len(self.stores[self.trunkStore]['children']) == 1):
            self.trunkStore = self.stores[self.trunkStore]['children'][0]
        self.globals['rootStore'] = self.rootStores[0]
        self.globals['rootStores'] = self.rootStores
        self.globals['trunkStore'] = self.trunkStore

        # make sure all of the stores have certain key fields
        for key,store in self.stores.items():
            self._normalize(store)

    def __del__(self):
        if self.g is not None:
            self.destroy_gv_graph()


    def printtree(self, whId, indent):
        indentStr = indent * "  "
        s = self.stores[whId]

        print "%s%s (%s)"%(indentStr, s['idcode'], s['NAME'])
        for child in s['children']:
            self.printtree(child, indent+1)


    def printbasic(self):
        for whId,store in self.stores.items():
            if None == store['parent']:
                self.printtree(whId, 0)



    def _gv_setNodeColor(self, rec, attrib, tags):
        if not rec.has_key('report'):
            color = 'lightgray'
        else:
            report = rec['report']
            if attrib['show'] == 'fill':
                val = report['cooler']
                if val == 'NA':
                    color = 'lightgray'
                    tags.append('cooler=NA')
                else:
                    color = colorNameFromFraction(val)
                    if val >= 0.8:
                        tags.append('cooler=%f'%val)
            elif attrib['show'] == 'supplyratio':
                vax = []
                if not attrib.has_key('vax'):
                    vax = self.vaxList
                elif attrib['vax'] is None:
                    vax = self.vaxList
                elif isinstance(attrib['vax'], types.StringTypes):
                    vax = [attrib['vax']]
                else:
                    vax = attrib['vax']

                try:
                    treated = patients = 0
                    any = 0
                    for vac in vax:
                        if report['%s_treated'%vac] == 'NA' or report['%s_patients'%vac] == 'NA':
                            continue
                        treated += report['%s_treated'%vac]
                        patients += report['%s_patients'%vac]
                        any = 1
                    
                    if any == 0:
                        color = 'gray'
                    elif patients == 0:
                        color = 'lightgray'
                        tags.append("no patients")
                    else:
                        val = float(treated) / float(patients)
                        color = colorNameFromFraction(1.0 - val)
                        if val <= 0.2:
                            tags.append("supply ratio: %f"%val)
                except:
                    raise hermes_data_exception("vaccine info requested not in report")
            else:
                raise hermes_data_exception("invalid coloring request: %s"%attrib['show'])
        return color

    
    def _gv_nodeInfo(self, rec, attrib):
        "Provide color shape and label for the graphical representation of a specific node"
        color = shape = label = None
        tags = []
        showName = True

        # define the shape based on function
        if rec['FUNCTION'] == 'Administration':
            if rec['totStorage'] == 0.0:
                # this should be an attached clinic
                shape = 'diamond'
            else:
                shape = 'ellipse'

        elif rec['FUNCTION'] == 'Distribution':
            shape = 'box'

        elif rec['FUNCTION'] == 'Surrogate':
            shape = 'doublecircle'
            showName = False
        
        else:
            shape = 'octagon'
            color = 'red'
            tags.append('unknown FUNCTION: %s'%rec['FUNCTION'])

        # color based on attributes
        if color is None:
            color = self._gv_setNodeColor(rec, attrib, tags)
            
        if showName:
            label = '%s\n%s'%(ascify(rec['NAME']), rec['idcode'])
        else:
            label = rec['idcode']
        for tag in tags:
            label += '\n%s'%tag

        return (shape, color, label)

    def _gv_edgeInfo(self, route, attrib):
        "provide color, style and label for the graphical representation of an edge"
        color = label = style = None
        tags = []
        
        if route.has_key('TruckType'):
            tags.append(route['TruckType'])
        if route.has_key('Type'):
            tags.append(route['Type'])

        if not route.has_key('report'):
            color = 'black'
        else:
            report = route['report']
            if attrib['show'] == 'fill':
                val = report['RouteFill']
                if val == 'NA':
                    color = 'lightgray'
                    tags.append('RouteFill=NA')
                else:
                    color = colorNameFromFraction(val)
                    if val >= 0.8:
                        tags.append('RouteFill=%f'%val)
            else:
                color = 'black'
        label = route['RouteName']
        for tag in tags:
            label += '\n%s'%tag

        return (style, color, label)

    def _gv_addEdge(self, g, rName, fr, to, attrib, scale, delay=0, constraint=True):
        if delay != 0:
            edgeparms = (g, rName, fr, to, attrib, scale)
            self.delayedEdges.append(edgeparms)
            return

        style = color = label = None
        if rName is None:
            color = 'black'
            label = 'default'
            style = 'dotted'
        else:
            style, color, label = self._gv_edgeInfo(self.routes[rName], attrib)

        edge = gv.edge(fr, to)
        gv.setv(edge, 'color', color)
        gv.setv(edge, 'label', label)
        if style is not None:
            gv.setv(edge, 'style', style)
        gv.setv(edge, 'fontsize', '%6.2f'%(0.5*scale))
        gv.setv(edge, 'penwidth', '%6.2f'%(0.05*scale))
        gv.setv(edge, 'arrowsize', '%6.2f'%(0.02*scale))
        if constraint is False:
            gv.setv(edge, 'constraint', 'false')

    def _gv_addStore(self, g, storeId, attrib, scale, memo):
        """
        Part of build_gv_graph().  
        
        Recursively adds a node, its children and its child edges.
        Returns the top node created so the edge from the top node
        and its parent can be built by the parent caller.
        """
        if storeId in memo:
            return memo[storeId]
        rec = self.stores[storeId]
        shape,color,label = self._gv_nodeInfo(rec, attrib)
        try:
            node = gv.node(g, 'n_%s'%storeId)
        except Exception as e:
            print "Can't create node: for store %s!"%storeId
            raise e
        memo[storeId] = node
        gv.setv(node, 'hermes_id',   storeId)
        gv.setv(node, 'shape',       shape)
        gv.setv(node, 'color',       color)
        gv.setv(node, 'label',       label)
        gv.setv(node, 'fontsize',    "%6.2f"%scale)
        
        # create scaling factor for children and then process them
        if len(self.stores[storeId]['children']):
            sf = math.pow(len(self.stores[storeId]['children']), -0.5)

        processed_children = set()
        
        for route in self.stores[storeId]['childRoutes']:
            last_node = node
            for stop in self.routes[route]['stops'][1:]:
                child = stop[1]
                child_node = self._gv_addStore(g, child, attrib, sf * scale, memo)
                if attrib['stop0IsParent']:
                    self._gv_addEdge(g, route, node, child_node, attrib, scale)
                else:
                    self._gv_addEdge(g, route, last_node, child_node, attrib, scale)
                last_node = child_node
                processed_children.add(child)

        for child in self.stores[storeId]['children']:
            if child not in processed_children:
                child_node = self._gv_addStore(g, child, attrib, sf * scale, memo)
                self._gv_addEdge(g, None, node, child_node, attrib, scale)
                processed_children.add(child)

        return node

    def build_gv_graph(self, attrib = {}, layout='circo'):
        """
        Build a graphvis graph based on the system we've defined and any 
        attributes we've specified.  Call layout but don't render to
        anything yet.

        attrib is a dictionary can include the following options:
        show:    Can be 'fill' (default) or 'supplyratio'.
        vax:     Specifies a vaccine or a list of vaccines to calculate
                 supply ratio for.  [] chooses all.  Defaults to [].
        label:   Provide a label for the graph.
        root:    Set root of the graph to <idcode>.  Defaults to first fork
                 (self.trunkStore).  If set to None then does not set root.
        """

        if self.g is not None:
            gv.rm(self.g)
            self.g = None

        self.delayedEdges = []

        # specify default attributes
        if not attrib.has_key('show'):
            attrib['show'] = 'fill'
        if not attrib.has_key('stop0IsParent'):
            attrib['stop0IsParent'] = False

        g= gv.digraph('g')
        gv.setv(gv.protonode(g),'style','filled')
        gv.setv(gv.protonode(g),'rank','min')
        #gv.setv(g,'overlap','prism')
        gv.setv(g,'mindist','0.1')
        gv.setv(g,'clusterrank','local')
        gv.setv(g,'compound','true')
        gv.setv(g,'fontsize','100.0')
        gv.setv(g,'esep', '5')
        if attrib.has_key('label'):
            gv.setv(g, 'label', attrib['label'])
        
        memo = {}
        for st in self.rootStores:
            self._gv_addStore(g, st, attrib, 100, memo)

        if not attrib.has_key('root'):
            attrib['root'] = self.trunkStore
        if attrib['root'] is not None:
            gv.setv(g, 'root', 'n_%s'%attrib['root'])

        for edge in self.delayedEdges:
            (g, rName, fr, to, attrib, scale) = edge
            self._gv_addEdge(g, rName, fr, to, attrib, scale, 0, False)

        gv.layout(g, layout)

        self.g = g

    def destroy_gv_graph(self):
        if self.g is not None:
            gv.rm(self.g)
        self.g = None

    def get_gv_render(self, format):
        return gv.renderdata(self.g, format)

    def save_gv_render(self, format, filename):
        gv.render(self.g, format, filename + '.' + format)

    def add_gv_locations(self):
        if self.g is None:
            self.build_gv_graph()

        dot = self.get_gv_render('xdot')
        (graph, type) = dot_parser.parse_dot_text(dot)

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


    def routesData(self):
        return self.routes

    def storesData(self):
        return self.stores

    def getVaxList(self):
        return self.vaxList

    def storesList(self):
        ret = []
        for store in self.stores.values():
            ret.append((store['NAME'], store['idcode']))
        return ret

    def getRootStore(self):
        return self.rootStores[0]

    def getGlobals(self):
        return self.globals

    def getPeopleTypes(self):
        return self.peopleTypes

def main():
    parser = optparse.OptionParser()
    parser.add_option("-s", "--stores", help = "stores file")
    parser.add_option("-r", "--routes", help = "routes file")
    parser.add_option("-R", "--report", help = "report file")

    opts, args = parser.parse_args()
    
    storesFile = None
    routesFile = None
    reportFile = None

    if opts.stores:
        storesFile = opts.stores
    if opts.routes:
        routesFile = opts.routes
    if opts.report:
        reportFile = opts.report
    

    system = hermes_data(storesFile, routesFile, reportFile)
    
    system.printbasic()

    print "RootStore: %s"%system.rootStore
    print "TrunkStore: %s"%system.trunkStore

    system.build_gv_graph({'show':'supplyratio', 'label':'this is a label'})
    system.save_gv_render('xdot', 'hermes_data_test.xdot')
    system.add_gv_locations()




############
# Main hook
############

if __name__=="__main__":
    main()


