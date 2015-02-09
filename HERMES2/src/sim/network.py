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

__doc__=""" network.py
This is the set of routines to load a simple representation of the hermes 
supply chain network.
"""
_hermes_svn_id_="$Id$"

import csv_tools
import csv_overlays
from csv_tools import castValue, castTypes, castColumn, castEntry
import util
from util import listify, logContext, raiseRuntimeError, logWarning
import model

import re
import copy

def _parseAttr(attr):
    """
    read in an attribute descriptor list

    first two fields are 'name' and 'cast'
    subsequent fields are key value pairs.  Current keys supported are
    'copy':  set to False to not copy or to a callback function that will handle the copying
    'synonym':  set to a list of synonyms for the field
    """
    ret = {}
    ret['name'] = attr[0]
    ret['cast'] = attr[1]
    i = 2
    while i < len(attr):
        ret[attr[i]] = attr[i+1]
        i += 2
    return ret
    
def _moveAttrs(dest, rec, attrs, prefix = None):
    """
    move the attributes from an input record to a destination dict or class instance
    based on a list of attribute descriptor lists "attrs"

    This will delete from rec any attributes moved
    """
    attrs = listify(attrs)
    ret = {}

    for attr in attrs:
        a = _parseAttr(attr)
        name = a['name']
        names = [a['name']]

        if 'recordName' in a:
            names = [a['recordName']]
        if 'synonym' in a:
            names.extend(listify(a['synonym']))
            
        if prefix:
            names = [prefix + n for n in names]

        # question: do I go out and delete anything in any further synonyms?
        for n in names:
            if n in rec:
                val = rec[n]
                del(rec[n])
                break
        else:
            n = None
            val = None

        if 'copy' in a:
            if callable(a['copy']):
                a['copy'](dest, val)
            if a['copy'] is False:
                ret[name] = val
            continue

        cast = a['cast']
        val = castValue(val, cast, name)

        if isinstance(dest, dict):
            dest[name] = val
        else:
            setattr(dest, name, val)

    return ret


def _copyAttrsToRec(rec, src, attrs):
    """
    copy attributes from a dict or class instance to an input record.
    
    not as full featured as _moveAttrs()
    """
    for attr in attrs:
        a = _parseAttr(attr)
        if 'copy' in a:
            continue

        recName = name = a['name']
        if 'recordName' in a:
            recName = a['recordName']


        if isinstance(src, dict):
            try:
                if src[name] is not None:
                    rec[recName] = src[name]
            except:
                pass
        else:
            try:
                if getattr(src, name) is not None:
                    rec[recName] = getattr(src, name)
            except:
                pass

class NetStore:
    """
    Holds the attributes of an individual store.

    Besides the attributes in the storeAttrs list, the following attributes are valid:
         people:    list of people types and associated counts in the form of tuples of (type,count).
         clients:   list clients in the form of tuples of (store,route).
         suppliers: list of suppliers in the form of tuples of (store, route).
         rec:       dictionary of any remaing attributes that weren't copied based on storeAttrs or people types.
         reports:   a dictionary of report records that have been attached to this store.
         rpt:       the most recent report record attached to this store or None if none added.
    """

    def copyStorage(self, string):
        "parse and copy an inventory string"
        if not hasattr(self, 'inventoryList'):
            self.inventoryList = []

        itemList = model.parseInventoryString(string)
        newItemList = []
        for (count,name) in itemList:
            try:
                # while getTypeByName() does not instantiate anything of this type (so not
                # changing any counts), it does make this type "active".  I'm not sure if
                # this is desired.
                newType = self.typeManager.getTypeByName(name, sim=self.typeManager.sim)
            except:
                raiseRuntimeError("unknown type %s"%name)
            newItemList.append((count, newType))
        self.inventoryList += newItemList

    storeAttrs = [('CATEGORY',          castTypes.STRING),
                  ('FUNCTION',          castTypes.STRING),
                  ('NAME',              castTypes.STRING),
                  ('idcode',            castTypes.LONG),
                  ('utilizationRate',   castTypes.FLOAT, 
                   'recordName', 'Device Utilization Rate'),
                  ('Latitude',         (castTypes.EMPTY_IS_NONE, castTypes.FLOAT),
                   'synonym', ('WHO_Lat', 'Pop_Lat')),
                  ('Longitude',        (castTypes.EMPTY_IS_NONE, castTypes.FLOAT),
                   'synonym', ('WHO_Long', 'Pop_Long')),
                  ('UseVialsInterval',  castTypes.FLOAT),
                  ('UseVialsLatency',   castTypes.FLOAT),
                  ('Storage',          (castTypes.EMPTY_IS_NONE, castTypes.STRING),
                   'copy', copyStorage),
                  ('Inventory',        (castTypes.EMPTY_IS_NONE, castTypes.STRING),
                   'copy', copyStorage)]

    def __init__(self, rec, typeManager, types):
        self.typeManager = typeManager
        self.types = types

        _moveAttrs(self, rec, self.storeAttrs)

        self.people = {}
        for key in rec.keys():
            if types['people'].validTypeName(key):
                castEntry(rec, key, (castTypes.EMPTY_IS_ZERO, castTypes.INT))
                self.people[key] = rec[key]
                del rec[key]

        self.rec = rec
        self.clients = []
        self.suppliers = []
        self.reports = {}
        self.rpt = None

    def __repr__(self):
        return "<NetStore instance %s(%s)>"%(self.NAME, self.idcode)

    def createRecord(self):
        """
        create a store file record line as though it were just read in from the csv
        """
        rec = copy.copy(self.rec)
        _copyAttrsToRec(rec, self, self.storeAttrs)

        for pType,pCount in self.people.items():
            rec[pType] = pCount

        invStr = ""
        plusStr = ""
        for (count, newType) in self.inventoryList:
            invStr = invStr + "%s%d*%s"%(plusStr, count, newType.name)
            plusStr = "+"
        rec['Inventory'] = invStr
        return rec


    def addClient(self, store, route):
        self.clients.append((store, route))

    def removeClient(self, store, route):
        self.clients.remove((store, route))

    def addSupplier(self, store, route):
        self.suppliers.append((store, route))

    def removeSupplier(self, store, route):
        self.suppliers.remove((store, route))

class NetStop:
    """
    NetStop is a class to hold an individual stop within a NetRoute

    LocName, idcode, and RouteOrder are not copied.
    the attribute "store" is used instead which is a link to the appropriate store.
    RouteOrder is merely implied and is dropped from the structure (so that it is harder
        to create an invalid structure).
    """
    stopAttrs =  [('LocName',            castTypes.STRING,  'copy', False),
                  ('idcode',             castTypes.LONG,    'copy', False),
                  ('RouteOrder',         castTypes.INT,     'copy', False),
                  ('TransitHours',       (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                  ('DistanceKM',         (castTypes.EMPTY_IS_NONE, castTypes.FLOAT)),
                  ('PullOrderAmountDays',(castTypes.EMPTY_IS_NONE, castTypes.FLOAT)),
                  ('Notes',              (castTypes.EMPTY_IS_NULL_STRING, castTypes.STRING))]

    def __repr__(self):
        return "<NetStop instance traveling to %s(%s)>"%(self.store.LocName,self.store.idcode)

    def __init__(self, rec, stores):
        nc = _moveAttrs(self, rec, self.stopAttrs)
        store = stores[nc['idcode']]
        self.store = store
        self.rec = rec



class NetRoute:
    """
    This holds the data for a single route including the individual stops along the route.

    One can add, remove or change stops on a route but before doing this the route must be 
    'unlink()'d from the stores and after your changes have been made the route should be
    'relink()'d.

    Routes are created from lists of dicts holding the route records (one dict per stop)
    or they can be created with a single dict with no stops specified (and are considered
    unlink()'d).

    Currently when initializing a route, RouteOrder is not used for putting the stops in order.
    The constructor assumes that the stops are in order in the list of records.

    attribrutes include:
    the list of attributes in 'routeAttrs' (copied from the first rec in the route record list).
    stops:  a list of 'NetStop's stored in route order.
    supplier:  link to the 'NetStore' that is the supplier for the route (based on routeTypes).
    clients:  a list of the 'NetStore's that are clients for the route (based on routeTypes).
    reports:  a dictionary of report records that have been attached to this route.
    rpt:  the most recent report record attached to this route or None if none added.

    any additional attributes that are not defined in 'routeAttrs' or in 'stopAttrs' will be
    copied over to the 'rec' attribute in each stop.
    """

    routeAttrs = [('RouteName',          castTypes.STRING),
                  ('Type',               castTypes.STRING),
                  ('TruckType',          (castTypes.EMPTY_IS_NULL_STRING, castTypes.STRING)),
                  ('ShipIntervalDays',   (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                  ('ShipLatencyDays',    (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                  ('PullOrderAmountDays',(castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                  ('Conditions',         (castTypes.EMPTY_IS_NULL_STRING, castTypes.STRING))]

    routeTypes = {'push':0, 'varpush':0, 'pull':0, 'attached':0,
                  'schedfetch':1, 'schedvarfetch':1, 'demandfetch':1,
                  'askingpush':0, 'dropandcollect':0,
                  'persistentpull':0, 'persistentdemandfetch':1}
    
    def __repr__(self):
        return "<NetRoute instance %s>"%(self.RouteName)

    def __init__(self, rrList, stores, typeManager, noStops=False):
        
        self.typeManager = typeManager
        
        rrList = listify(rrList)

        rr = rrList[0]
        _moveAttrs(self, rr, self.routeAttrs)

        # pull all of the duplicate stuff out of the subsequent route records 
        for x in rrList[1:]:
            trashrec = {}
            _moveAttrs(trashrec, x, self.routeAttrs)

        if self.Type not in self.routeTypes:
            raiseRuntimeError("invalid routetype %s on route %s"%(self.Type, self.RouteName))
            
        self.rpt = None
        self.reports = {}
        
        self.stops = []

        if noStops:
            return

        for i, rr in enumerate(rrList):
            # I really don't know if I should require that route order be defined as 0, 1, 2,...
            # for now I won't require it.
            #if i != rr['RouteOrder']:
            #    raise RuntimeError("invalid or missing RouteOrder numbers on route %s"%(self.RouteName))
            self.addStop(rr, stores)

        self.linkRoute()
        self.transportTypes = [] # eventually facilitates multiple transport types per route
        #for transportName in self.TruckType:
        #    print transportName
        if self.TruckType != "":
            self.transportTypes.append(self.typeManager.getTypeByName(self.TruckType,sim=self.typeManager.sim))

    def addStop(self, rec, stores, relink = False, order = -1):
        "Add a stop to the route"
        if relink:
            self.unlinkRoute()

        stop = NetStop(rec, stores)

        if order == -1:
            self.stops.append(stop)
        else:
            self.stops.insert(stop, order)

        if relink:
            self.linkRoute()

    def removeStop(self, store, relink = False):
        " remove a stop from a route.  store should be an actual store (rather than idcode)"
        if relink:
            self.unlinkRoute()

        found = False
        for stop in self.stops:
            if stop.store is store:
                found = True
                self.stops.remove(stop)
                break
        
        if not found:
            raiseRuntimeError("Tried to remove stop that didn't exist from route")
        
        if relink:
            self.linkRoute()


    def linkRoute(self):
        try:
            self.supplier = self.stops[self.routeTypes[self.Type]].store
        except:
            raiseRuntimeError("missing supplier stop from route %s"%self.RouteName)

        self.clients = []
        for i,stop in enumerate(self.stops):
            if i == self.routeTypes[self.Type]:
                continue
            self.clients.append(stop.store)
            stop.store.addSupplier(self.supplier, self)
            self.supplier.addClient(stop.store, self)
        

    def unlinkRoute(self):
        for i,stop in enumerate(self.stops):
            if i == self.routeTypes[self.Type]:
                continue

            stop.store.removeSupplier(self.supplier, self)

            self.supplier.removeClient(stop.store, self)    
    
        
    
    def createRecords(self):
        """
        create a set of routes file record lines as though they were just read in from the csv
        """
        recs = []

        for i,stop in enumerate(self.stops):
            rec = copy.copy(stop.rec)
            rec['idcode'] = stop.store.idcode
            rec['LocName'] = stop.store.NAME
            rec['RouteOrder'] = i

            _copyAttrsToRec(rec, stop, stop.stopAttrs)
            _copyAttrsToRec(rec, self, self.routeAttrs)
            recs.append(rec)

        return recs





class Network:
    """
    This is the class that holds everything in one place.  Its primary purpose is to have
    a dictionary of stores with routes linking them together in a manner that can easily be
    read and manipulated.

    It has the following attributes:
        stores:  This is a dictionary of 'NetStore's keyed off of their 'idcode's.
        routes:  This is a dictionary of 'NetRoute's keyed off of their 'RouteName's.
        typeManager:
                 Core TypeManager that was passed in.
        types:   Dictionary of sub-typemanagers.
    """

    def __init__(self, storeRecs, routeRecs, typeManager, types):
        """
        Instantiates a new hermes network based on the 'storeRecs' and 'routeRecs'.
	The typemanager (along with its sub-typemanagers are required).  'typeManager' and
	'types' are best acquired as the outputs of load_typemanagers.loadTypeManagers().
        """
        self.typeManager = typeManager
        self.types = types

        # parse store recs
        with logContext("initial parsing of stores records"):
            self.stores = {}
            for storeRec in storeRecs:
                if 'idcode' not in storeRec:
                    raiseRuntimeError("found stores record with no idcode")
                with logContext("initial parsing of stores record %s"%storeRec['idcode']):
                    self.addStore(storeRec)

        # parse route recs and integrate them into the store records
        with logContext("initial parsing of routes records"):
            # do initial casting so that we can presort the records
            for attrs in NetRoute.routeAttrs + NetStop.stopAttrs:
                a = _parseAttr(attrs)
                castColumn(routeRecs, a['name'], a['cast'])

            rrDict = {}
            for routeRec in routeRecs:
                name = routeRec['RouteName']
                if name not in rrDict:
                    rrDict[name] = []
                rrDict[name].append(routeRec)

            self.routes = {}

            for name,rrList in rrDict.items():
                rrList.sort(key = lambda r: r['RouteOrder'])
                self.addRoute(rrList)

    def addStore(self, store):
        """
        Add a 'NetStore' to the network. 'store' can either be a fully formed 
	'NetStore' or a dictionary of attributes.
        """
        if isinstance(store, NetStore):
            pass
        elif isinstance(store, dict):
            store = NetStore(store, self.typeManager, self.types)
        else:
            raiseRuntimeError("unknown store type in addStore")
        
        self.stores[store.idcode] = store
        return store

    def removeStore(self, store):
        """
        remove a store from the network.  'store' can either be a 'NetStore' or 
        an 'idcode'.

        It is an error to remove a store if there are routes in the network
        that reference it.
        """
        if isinstance(store, NetStore):
            pass
        elif store in self.stores:
            store = self.stores[store]
        else:
            raiseRuntimeError("store to be removed is unrecognized")

        idcode = store.idcode
        
        if len(store.clients) or len(store.suppliers):
            raiseRuntimeError("can't remove store with routes linked to it!")

        if idcode not in self.stores:
            raiseRuntimeError("store to be removed not found")
        del(self.stores[idcode])


    def addRoute(self, recList, noStops = False):
        """
        create and add a route based on a recList.  If noStops is set to True then
        stops will not be created and no stores will be linked.
        """
        r = NetRoute(recList, self.stores, self.typeManager, noStops)
        self.routes[r.RouteName] = r
        return r

    def removeRoute(self, route, unlinked=False):
        """
        remove a route from the network.  'route' can either be a 'NetRoute' or
        a 'RouteName'.  By default this will unlink the route for you (unless 
        'unlinked' is set to True).
        """
        if isinstance(route, NetRoute):
            name = route.RouteName
        else:
            name = route
            route = self.routes[name]

        if not unlinked:
            route.unlinkRoute()
        del(self.routes[name])

    def createStoreRecs(self):
        """
        Create a set of stores records (and keys) that can be used to create a new stores file.
        """
        recs = []
        for store in self.stores.values():
            recs.append(store.createRecord())
        keys = set()
        for rec in recs:
            keys |= set(rec.keys())
        keys = list(keys)
        return keys,recs


    def createRouteRecs(self):
        """
        Create a set of routes records (and keys) that can be used to create a new routes file.
        """
        recs = []
        keys = []
        for route in self.routes.values():
            recs.extend(route.createRecords())
        keys = set()
        for rec in recs:
            keys |= set(rec.keys())
        keys = list(keys)
        return keys,recs

    
    def rootStores(self):
        rootStores = []
        for store in self.stores.values():
            if len(store.suppliers) == 0:
                rootStores.append(store)

        return rootStores


    def trunkStore(self):
        rootStores = self.rootStores()
        if len(rootStores) == 0:
            raiseRuntimeError("no root stores in network")
        rootStores.sort(key=lambda s: s.idcode)
        trunk = rootStores[0]
        while (len(trunk.clients) == 1):
            trunk = trunk.clients[0][0]

        return trunk

    def attachReport(self, reportRecs, reportIndex = 0):
        attachReport(self, reportRecs, reportIndex)

def readNetworkRecords(userInput):
    """
    read in any stores and routes csv files based on the userInput structure.

    returns (storeKeys, storeRecList, routeKeys, routeRecList)
    """
    with util.logContext("reading routes CSV"):
        with util.openDataFullPath(userInput['routesfile'],"rb") as RoutesFileHandle:
            routeKeys, routeRecList= csv_tools.parseCSV(RoutesFileHandle)
        if userInput['routesoverlayfiles'] is not None:
            (routeKeys, routeRecList) = \
                csv_overlays.parseOverlayCSV(routeKeys,
                                             routeRecList,
                                             ('RouteName','RouteOrder'),
                                             userInput['routesoverlayfiles'])
                # I don't know of anything to use for secondary keys


    with util.logContext("reading stores CSV"):
        with util.openDataFullPath(userInput['storesfile'],"rb") as StoresFileHandle:
            storeKeys, storeRecList= csv_tools.parseCSV(StoresFileHandle)
        if userInput['storesoverlayfiles'] is not None:
            (storeKeys, storeRecList) = \
                csv_overlays.parseOverlayCSV(storeKeys, 
                                             storeRecList, 
                                             'idcode', 
                                             userInput['storesoverlayfiles'],
                                             'CATEGORY')

    return (storeKeys, storeRecList, routeKeys, routeRecList)


def loadNetwork(userInput, typeManager, typeManagers):
    """
    loads the stores and routes files and populates and then returns a Network class Instance.
    """

    (storeKeys, storeRecList, routeKeys, routeRecList) = \
        readNetworkRecords(userInput)

    net = Network(storeRecList, routeRecList, typeManager, typeManagers)
    return net


class VaxRpt:
    vaxAttrs = [('expired',     (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT), 'recordName', '_expired'),
                ('outages',     (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT), 'recordName', '_outages'),
                ('patients',    (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT), 'recordName', '_patients'),
                ('treated',     (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT), 'recordName', '_treated'),
                ('vials',       (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT), 'recordName', '_vials')]

    def __init__(self, vax, rec):
        self.vax = vax
        _moveAttrs(self, rec, self.vaxAttrs, prefix = vax)

class StorageRpt:
    storageRptAttrs = [('fillRatio', (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT), 'recordName', ''),
                       ('vol',       (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT), 'recordName', '_vol'),
                       ('vol_used',  (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT), 'recordName', '_vol_used')]

    def __init__(self, storageType, rec):
        self.storageType = storageType
        _moveAttrs(self, rec, self.storageRptAttrs, prefix = storageType)
      
class StoresRpt:
    """
    Besides what's in the attrs list, the following attributes are stored with the 
    StoresRpt structure:
      vax:        dictionary keyed by vaccine type each pointing to a VaxRpt
      storage:    dictionary keyed by storage type, each pointing to a StorageRpt
      rec:        everything else in the input record.
    """
    storesRptAttrs = [('code',           castTypes.LONG,     'copy', False),
                      ('name',           castTypes.STRING,   'copy', False),
                      ('category',       castTypes.STRING,   'copy', False),
                      ('function',       castTypes.STRING,   'copy', False),
                      ('one_vaccine_outages', 
                                         (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                      ('overstock_time', (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                      ('stockout_time',  (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                      ('tot_delivery_vol',
                                         (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT))]

    def __init__(self, rec):
        _moveAttrs(self, rec, self.storesRptAttrs)

        from storagetypes import storageTypeNames
        self.storage = {}
        for storageType in storageTypeNames:
            self.storage[storageType] = StorageRpt(storageType, rec)
        
        vaxList = []
        for key in rec.keys():
            m = re.match(r"^(.+)_treated$", key)
            if m is not None:
                vaccine = m.group(1)
                vaxList.append(vaccine)

        self.vax = {}
        for vaccine in vaxList:
            self.vax[vaccine] = VaxRpt(vaccine, rec)
        
        self.rec = rec

class RoutesReport:
    """
    The routes report structures is really simple.  Just what's in the attrs list and rec holds
    anything not copied.
    """
    routesRptAttrs = [('RouteName',        castTypes.STRING,   'copy', False),
                      ('RouteFill',        (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                      ('RouteTrips',       (castTypes.EMPTY_IS_ZERO, castTypes.FLOAT)),
                      ('RouteTruckType',   (castTypes.STRING,  'copy', False))]
    
    def __init__(self, rec):
        _moveAttrs(self, rec, self.routesRptAttrs)
        self.rec = rec

def attachReport(net, reportRecs, reportIndex = 0):
    with logContext("attaching report records to ghost network"):
        for rec in reportRecs:
            code = 0
            try:
                code = int(rec['code'])
            except:
                pass

            rtName = 'NA'
            try:
                rtName = rec['RouteName']
                if rtName == '':
                    rtName = 'NA'
            except:
                pass

            if code > 0:
                if code not in net.stores:
                    raiseRuntimeError("store code %d was found in the report but not in the Hermes Network"%code)
                rpt = StoresRpt(rec)
                net.stores[code].reports[reportIndex] = rpt
                net.stores[code].rpt = rpt
            elif rtName != 'NA':
                if rtName not in net.routes:
                    # currently we'll call this a warning, but soon we will fully deprecate implied links
                    # and this will go back to being a fatal error.
                    logWarning("route name %s was found in the report but not in the Hermes Network"%rtName)
                    continue
                    #raiseRuntimeError("route name %s was found in the report but not in the Hermes Network"%rtName)
                rpt = RoutesReport(rec)
                net.routes[rtName].reports[reportIndex] = rpt
                net.routes[rtName].rpt = rpt
            else:
                raiseRuntimeError("invalid record in report records")
                
                    
                
