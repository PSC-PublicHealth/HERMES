#! /usr/bin/env python

########################################################################
# Copyright C 2012, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

__doc__=""" shadow_network.py
This is the set of routines to load a simple representation of the hermes 
supply chain network.
"""
_hermes_svn_id_="$Id$"

import types
import collections

import csv_tools
from csv_tools import castValue, castTypes, castColumn, castEntry, CSVDict
import util
from util import listify, logContext, raiseRuntimeError, logWarning
from util import parseInventoryString
import load_networkrecords
import storagetypes
from fridgetypes import energyTranslationDict, fridgeDisplayNameFromRec
import input, HermesInput
import globals as G
from datatypes import *
from curry import curry
from enums import TimeUnitsEnums
import math
import struct
import operator

#import sys
#sys.setrecursionlimit(1500)
import re
import copy
import pickle
try:
    # anything gotten from sqlalchemy should have an equivalent noop below
    from sqlalchemy import Column, Integer, String, ForeignKey, Index
    import sqlalchemy
    saEvent = sqlalchemy.event
    from sqlalchemy.orm import relationship, backref, object_mapper
    from sqlalchemy.orm.properties import RelationshipProperty
    from sqlalchemy.orm.collections import attribute_mapped_collection
    from sqlalchemy.ext.hybrid import hybrid_property

    from db_routines import Base
    
except:
    raise RuntimeError("unable to load sqlalchemy.  This is now fatal!") 

    def emptyFunc(*args, **kwargs):
        return None

    class EmptyClass():
        def __init__(self, *args, **kwargs):
            pass

    Column = Index = ForeignKey = relationship = backref = attribute_mapped_collection = emptyFunc
    Integer = saEvent = Base = EmptyClass

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
    ret['type'] = attr[1]
    if ret['type'] is None:
        ret['cast'] = None
    else:
        ret['cast'] = ret['type'].cast()
    i = 2
    while i < len(attr):
        ret[attr[i]] = attr[i+1]
        i += 2
    return ret
    
def _attrsFromDest(dest, attrs = None):
    if attrs is not None:
        return attrs
    if isinstance(dest, dict):
        return dest['attrs']
    return getattr(dest, 'attrs')

def _moveAttrs(dest, rec, attrs = None, prefix = None, skip = None):
    """
    move the attributes from an input record to a destination dict or class instance
    based on a list of attribute descriptor lists "attrs"

    This will delete from rec any attributes moved
    """
    attrs = _attrsFromDest(dest, attrs)
    attrs = listify(attrs)
    ret = {}
    finishedRelationships = set()
    
    for attr in attrs:
        a = _parseAttr(attr)

        delete = True
        if 'delete' in a:
            delete = a['delete']

        if 'recdecode' in a:
            if 'relationship' in a:
                relName = a['relationship']
            elif a['type'] is None:
                relName = a['name']
            else:
                relName = None
            if relName is not None:
                if relName in finishedRelationships: continue
                else: finishedRelationships.add(relName)
            a['recdecode'](dest, rec, delete=delete)
        elif a['type'] is None:
            continue
        elif 'noInputRec' in a:
            continue
        else:
            name = a['name']
            if skip and name in skip: 
                continue
            names = [a['name']]
            if 'recordName' in a:
                names = [a['recordName']]
            if 'synonym' in a:
                names.extend(listify(a['synonym']))
                
            if prefix:
                names = [prefix + n for n in names]
                
            # question: do I go out and delete anything in any further synonyms?
            for n in names:
                if n in rec and rec[n] != '':
                    val = rec[n]
                    if delete:
                        del(rec[n])
                    break
            else:
                n = None
                val = ''
    
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

def _copyAttrsToRec(rec, src, attrs = None):
    """
    copy attributes from a dict or class instance to an input record.
    
    not as full featured as _moveAttrs()
    """
    finishedRelationships = set()
    attrs = listify(_attrsFromDest(src, attrs))
    for attr in attrs:
        a = _parseAttr(attr)
        
        recName = name = a['name']
        if 'recordName' in a:
            recName = a['recordName']
            
        if 'recencode' in a:
            try:
                if 'relationship' in a:
                    relName = a['relationship']
                elif a['type'] is None:
                    relName = a['name']
                else:
                    relName = None
                if relName is not None:
                    if relName in finishedRelationships: continue
                    else: finishedRelationships.add(relName)
                rec.update(a['recencode'](src))
            except:
                rec[recName] = ''
        elif 'copy' in a:
            continue
        elif 'noInputRec' in a:
            continue
        elif a['type'] is None:
            continue
        else:
            if isinstance(src, dict):
                try:
                    if src[name] is not None:
                        rec[recName] = src[name]
                    else:
                        rec[recName] = ''
                except:
                    rec[recName] = ''
                    pass
            else:
                try:
                    if getattr(src, name) is None:
                        rec[recName] = ''
                    else:
                        rec[recName] = getattr(src, name)
                except Exception,e:
                    rec[recName] = ''
                    pass
            
def _getAttrsRecNamesList(src, attrs=None):
    """
    Return a list containing the names of the associated attrs, as they would
    appear in an input record.

    Be careful using this, as it may or may not include non-standard input recs
    """
    result = []
    attrs = listify(_attrsFromDest(src, attrs))
    for attr in attrs:
        a = _parseAttr(attr)
        if 'noInputRec' in a or a['type'] is None:
            continue

        recName = name = a['name']
        if 'recordName' in a:
            recName = a['recordName']


        if isinstance(src, dict):
            try:
                if src[name] is not None:
                    result.append(recName)
            except:
                pass
        else:
            try:
                if getattr(src, name) is not None:
                    result.append(recName)
            except:
                pass
            
    return result

def _makeColumns(clas, attrs = None):
    attrs = _attrsFromDest(clas, attrs)

    for attr in attrs:
        a = _parseAttr(attr)
        t = a['type']

        if t is not None and t.dbType() is not None:
            #print name
            #print t.dbArgs()
            #print t.dbKwargs()
            if 'hybridName' in a:
                name = a['hybridName']
                dbArgs = [a['name']] + t.dbArgs()
                setattr(clas, name, Column(*dbArgs, **t.dbKwargs()))

            else:
                name = a['name']
                setattr(clas, name, Column(*t.dbArgs(), **t.dbKwargs()))
        

def _initBasic(instance, args, kwargs, startAttr=1):
    """
    Use this for the init function of a simple shadow class

    if __init__() is passed a dictionary it will treat it as a csv record line and extract the
    data from it based on the attribute table.

    otherwise it will treat the attrs as a list of ordered or named arguments, skipping the 
    first (assuming that that is modelId).
    """
    attrs = _attrsFromDest(instance)

    if len(args) > 0:
        if isinstance(args[0], collections.Mapping):
            return _moveAttrs(instance, args[0], attrs)
        
    for i,arg in enumerate(args, start=startAttr):
        a = _parseAttr(attrs[i])
        kwargs[a['name']] = arg

    return _moveAttrs(instance, kwargs, attrs)

def _indPrint(s,recurLvl): print ('    '*recurLvl)+s

class ShdCopyable(object):
    def createRec(self):
        """
        create a CSV record line as though it were just read in from the csv
        """
        rec = CSVDict()
        _copyAttrsToRec(rec, self)
        return rec
    
    def copyAttrsFromRec(self,otherRec,excludeThese=None):
        """
        Fill self with attribute values as specified in the given CSV record.
        """
        oR = otherRec.copy()
        _moveAttrs(self,oR,skip=excludeThese)            
            
    def traverseRelationships(self, lvl=0):
        relDict = {} # known relationships
        afR = set() # already followed relationships
        _indPrint('traversing %s'%type(self).__name__, lvl)
        _indPrint('record is %s'%self.createRec(),lvl)
        myMapper = object_mapper(self)
        _indPrint('relationship keys are %s'%myMapper.relationships.keys(),lvl)
        for a in self.attrs:
            if a[1] is None: 
                # This is purely a relationship
                d = _parseAttr(a)
                relDict[d['name']] = d
                assert 'relationshiptype' in d, 'Relationship attribute %s has no relationshiptype'%d['name']
                
        for relName,rel in myMapper.relationships.items():
            if relName not in relDict:
                _indPrint('!! %s : Relationship with no corresponding attr'%relName, lvl+1)

        for a in self.attrs:
            d = _parseAttr(a)
            nm = d['name']

            if d['type'] is None:
                k = d['name']
            elif d['type'].dbType() is None:
                assert 'relationship' in d, "Attribute %s has no dbType and no relationship"%d['name']
                k = d['relationship']
                if k is None: continue # 'relationship' None can be used to denote rels for which the map is not implemented
            else:
                k = None

            if k is None:
                _indPrint("%s : Simple attribute <%s>"%(nm, getattr(self,nm)), lvl+1)
            else:
                if k in afR:
                    _indPrint('%s : relationship %s, already followed'%(nm,k),lvl+1)
                else:
                    afR.add(k)
                    relType = relDict[k]['relationshiptype']
                    if relType in ['onetomany', 'manytomany']:
                        if hasattr(self,k):
                            rel = getattr(self,k)
                            supportsIteration = hasattr(rel,'__iter__')
                            supportsItems = hasattr(rel,'items')
                        else:
                            raise RuntimeError("relationship '%s' of %s is invisible"%(k,type(self).__name__))
                        _indPrint('%s : relationship %s: iteration %s, items %s, type %s'%\
                                  (nm,k,supportsIteration,supportsItems,relType),lvl+1)
                        assert supportsIteration, 'This %s relationship does not support iteration'%relType
                        if len(rel) == 0: 
                            _indPrint('no children',lvl+2)
                        else: 
                            for target in rel:
                                if isinstance(target,ShdCopyable):
                                    target.traverseRelationships(lvl+2)
                                else:
                                    _indPrint('%s not ShdCopyable'%target,lvl+2)
                    elif relType == 'onetoone':
                        if hasattr(myMapper,'polymorphic_on') and myMapper.polymorphic_on.table.name == k:
                            relClass = myMapper.polymorphic_map[k].class_
                            assert relClass in self.__class__.__bases__ , "%s is not a direct base class of %s"%(relClass.__name__, self.__class__.__name__)
                            _indPrint('%s : from one-to-one polymorphic relationship with class %s'%(nm,relClass.__name__),
                                      lvl+1)
                        else:
                            raise RuntimeError("relationship '%s' of %s is invisible"%(k,type(self).__name__))
                    elif relType == 'manytoone':
                        _indPrint('%s : many-to-one target is %s'%(nm,rel),lvl+2)
                    else:
                        raise RuntimeError('Unknown relationship type %s'%relType)
        

class ShdInventory(Base, ShdCopyable):
    """
    this is derived from an the Storage and Inventory fields of a store record.
    """

    __tablename__ = "inventory"
    inventoryId = Column(Integer, primary_key=True)

    # sourceType enums
    SOURCE_STORE = 1
    SOURCE_STORE_DEMAND = 2
    SOURCE_ROUTE = 3

    attrs = [('modelId',    DataType(INTEGER, foreignKey='models.modelId'),
              'noInputRec', True),
             ('sourceType', INTEGER,
              'noInputRec', True, 'relationship', 'invType'),
             ('idcode',     LONG,  # used when source is a store
              'noInputRec', True, 'relationship', 'invType'),
             ('Name',       STRING, # used when a source is a type
              'noInputRec', True, 'relationship', 'invType'),
             ('invName',    STRING, #   DataType(STRING, foreignKey='types.Name')),
              'relationship', 'invType'),
             ('count',      INTEGER),
             ('invType',    None, 'relationshiptype', 'manytoone')
             ]


    invType = relationship('ShdType',
                           primaryjoin="and_(ShdInventory.modelId==ShdType.modelId, "
                                            "ShdInventory.invName==ShdType.Name)",
                           foreign_keys="[ShdType.modelId,ShdType.Name]",
                           uselist=False)


    def __init__(self, sourceType, source, invType, count):
        """
        invType can be either the type or the name of a type.
        if invType is a string it will not be checked nor will the invType
        field be available until/unless this record is reloaded from a 
        database.
        """
        self.sourceType = sourceType
        if sourceType == self.SOURCE_STORE or sourceType == self.SOURCE_STORE_DEMAND:
            self.idcode = source
            self.Name = None
        else:
            self.Name = source
            self.idcode = None

        if isinstance(invType, types.StringTypes):
            self.invName = invType
        else:
            self.invType = invType
            self.invName = invType.Name
        self.count = count

_makeColumns(ShdInventory)
ShdInventory.__table_args__ = (Index('inventoryIdxId', 'modelId', 'sourceType', 'idcode'),
                               Index('inventoryIdxName', 'modelId', 'sourceType', 'Name'))


class ShdFactory(Base, ShdCopyable):
    """
    Holds the attributes of an indivisual Factory.
     
    """
     
    __tablename__ = 'factories'
    factoryId = Column(Integer, primary_key=True)
    
    attrs = [('modelId', DataType(INTEGER, foreignKey='models.modelId'),
               'noInputRec', True, 
               'relationship', 'net'),
             ('idcode', DataType(LONG, primary_key=True)),
             ('Name', STRING),
             ('Targets', STRING),
             ('Vaccines', STRING),
             ('ProductionIntervalDays', FLOAT),
             ('StartupLatencyDays', FLOAT),
             ('OverstockScale', FLOAT),
             ('DemandType', STRING),
             ('net', None, 'relationshiptype', 'manytoone')
             ]
    
    net = relationship('ShdNetwork',
                       primaryjoin="ShdFactory.modelId==ShdNetwork.modelId",
                       uselist=False)
    
    def __init__(self, rec, net):
        self.net = net
        _moveAttrs(self, rec)
        
        self.rec = rec
        self.targets = []
        self.vaccines = []
        
    def __repr__(self):
        return "<ShdFactory instance %s(%d)>" % (self.Name, self.idcode)
    
    def createRecord(self):
        """
        create a factory file record line as though it were just read in from the csv
        """
        rec = CSVDict()
        _copyAttrsToRec(rec, self)
        
        return rec
    
def factoryLoadListener(factory, context):
    print "Loading factory %s (%d)" % (factory.Name, factory.idcode)

_makeColumns(ShdFactory)
Index('factoryIdx', ShdFactory.modelId, ShdFactory.idcode)

class ShdFactoryWastage(Base):
    __tablename__ = 'factoryWastage'
    factoryWastageId = Column(Integer, primary_key=True)

    attrs = [('modelId',        DataType(INTEGER, foreignKey='models.modelId'), 'noInputRec', True),
             ('FactoryID',      INTEGER),
             ('VaccineName',    STRING),
             ('WastageFraction',FLOAT)
             ]
    
    def __init__(self, *args, **kwargs):
        _initBasic(self, args, kwargs)

    def createRecord(self):
        rec = CSVDict()
        _copyAttrsToRec(rec, self)
        return rec

_makeColumns(ShdFactoryWastage)

class ShdInitialOVW(Base):
    __tablename__ = 'initialOVW'
    initialOVWId = Column(Integer, primary_key=True)

    attrs = [('modelId',       DataType(INTEGER, foreignKey='models.modelId'), 'noInputRec', True),
             ('Name',          STRING),
             ('OVW',           FLOAT),
             ('Notes',         NOTES_STRING)]
    
    def __init__(self, *args, **kwargs):
        _initBasic(self, args, kwargs)

    def createRecord(self):
        rec = CSVDict()
        _copyAttrsToRec(rec, self)
        return rec

_makeColumns(ShdInitialOVW)

class ShdStore(Base, ShdCopyable):
    """
    Holds the attributes of an individual store.

    Besides the attributes in the storeAttrs list, the following attributes are valid:
         inventory: list of inventory and associated counts in the form of ShdInventory instances.
         demand:    list of people types and associated counts in the form of ShdInventory instances.
         reports:   a dictionary of report records that have been attached to this store.
         rpt:       the most recent report record attached to this store or None if none added.

     methods
         clients():   list clients in the form of tuples of (store,route).
         suppliers(): list of suppliers in the form of tuples of (store, route).

    """

    __tablename__ = 'stores'
    storeId = Column(Integer, primary_key=True)

    def copyStorage(self, string):
        "parse and copy an inventory string"
        itemList = parseInventoryString(string)
        newItemList = []
        for (count,name) in itemList:
            try:
                newType = self.net.types[name]
            except:
                raiseRuntimeError("unknown type %s"%name)
            self.addInventory(newType, count)

    def inventoryToRec(self):
        """
        This is a 'recencode' method, which will be used like rec.update(self.demandToRec())
        to convert database information representing this attribute to record form.
        """
        invStr = ""
        plusStr = ""
        for item in self.inventory:
            invStr = invStr + "%s%d*%s"%(plusStr, item.count, item.invName)
            plusStr = "+"
        return {'Inventory':invStr}
    
    def inventoryFromRec(self,rec,delete=True):
        """
        This is a 'recdecode' method, which will be used like self.demandFromRec(rec) to convert
        record information for this attribute to database form.  If delete is True, this method
        must delete the corresponding record items.
        """
        for k in ['Inventory','Storage']:
            if k in rec:
                self.copyStorage(rec[k])
                if delete: del rec[k]
            
    def demandToRec(self):
        """
        This is a 'recencode' method, which will be used like rec.update(self.demandToRec())
        to convert database information representing this attribute to record form.
        """
        rec = {}
        for d in self.demand:
            rec[d.invName] = d.count
        return rec
    
    def demandFromRec(self,rec,delete=True):
        """
        This is a 'recdecode' method, which will be used like self.demandFromRec(rec) to convert
        record information for this attribute to database form.  If delete is True, this method
        must delete the corresponding record items.
        """
        net = self.net
        for key in rec.keys():
            if key in net.types:
                curType = net.types[key]
                curType.setActive()
                castEntry(rec, key, (castTypes.EMPTY_IS_ZERO, castTypes.INT))
                self.addDemand(curType, rec[key])
                if delete: del rec[key]

    attrs = [('modelId',           DataType(INTEGER, foreignKey = 'models.modelId'),
              'noInputRec', True,
              'relationship', 'net'),
             ('CATEGORY',          STRING),
             ('FUNCTION',          STRING),
             ('NAME',              STRING),
             ('idcode',            DataType(LONG, primary_key=True)),
             ('utilizationRate',   FLOAT, 
              'recordName', 'Device Utilization Rate'),
             ('Latitude',          FLOAT_NONE,
              'synonym', ('WHO_Lat', 'Pop_Lat')),
             ('Longitude',         FLOAT_NONE,
              'synonym', ('WHO_Long', 'Pop_Long')),
             ('UseVialsInterval',  FLOAT),
             ('UseVialsLatency',   FLOAT),
             ('Storage',           DataType(STRING_NULL, dbType=None),
              'copy', copyStorage, 
              'relationship', 'inventory',
              'recencode', inventoryToRec, 'recdecode', inventoryFromRec),              
             ('Inventory',         DataType(STRING_NULL, dbType=None),
              'copy', copyStorage,
              'relationship', 'inventory',
              'recencode', inventoryToRec, 'recdecode', inventoryFromRec),
             ('Notes',             NOTES_STRING),
             ('inventory',         None, 'relationshiptype', 'onetomany'),
             ('demand',            None, 'relationshiptype', 'onetomany',
              'recencode', demandToRec,  'recdecode', demandFromRec),
             ('reports',           None, 'relationshiptype', 'onetomany'),
             ('relatedStops',      None, 'relationshiptype', 'onetomany'),
             ('net',               None, 'relationshiptype', 'manytoone')
             ]
    
    # inventory and demand should have cascade delete orphan on them
    inventory = relationship('ShdInventory',
                             primaryjoin="and_("
                                            "and_(ShdStore.modelId==ShdInventory.modelId, "
                                            "ShdStore.idcode==ShdInventory.idcode), "
                                           "ShdInventory.sourceType==1)",
                             foreign_keys="[ShdInventory.modelId,ShdInventory.idcode]")

    demand = relationship('ShdInventory',
                          primaryjoin="and_("
                                         "and_(ShdStore.modelId==ShdInventory.modelId, "
                                             "ShdStore.idcode==ShdInventory.idcode), "
                                         "ShdInventory.sourceType==2)",
                          foreign_keys="[ShdInventory.modelId,ShdInventory.idcode,ShdInventory.sourceType]")

    # the following are so I can build clients() and suppliers()
    relatedStops = relationship('ShdStop',
                                primaryjoin="and_(ShdStop.modelId==ShdStore.modelId, "
                                                 "ShdStop.idcode==ShdStore.idcode)",
                                foreign_keys="[ShdStop.modelId,ShdStop.idcode]",
                                viewonly = True)

    net = relationship('ShdNetwork',
                       primaryjoin="ShdStore.modelId==ShdNetwork.modelId",
                       uselist=False)#,
#                       post_update=True)


    reports = relationship('StoresRpt',
                           primaryjoin="and_(ShdStore.modelId == StoresRpt.modelId, "
                                            "ShdStore.idcode  == StoresRpt.code)",
                           foreign_keys="[StoresRpt.modelId, StoresRpt.code]",
                           collection_class=attribute_mapped_collection('resultsId'),
                           viewonly=True)


    def __init__(self, rec, net):
        self.inventory = []
        self.demand = []
        self.net = net

        _moveAttrs(self, rec)

        self.rec = rec
        self.reports = {}
        self.rpt = None
        self.relatedStops = []
    
    def __repr__(self):
        return "<ShdStore instance %s(%s)>"%(self.NAME, self.idcode)

    def _invName(self, invType):
        if isinstance(invType, types.StringTypes):
            name = invType
        elif isinstance(invType, ShdType):
            name = invType.Name
        elif isinstance(invType, ShdInventory):
            name = invType.invName
        else:
            raise RuntimeError('unknown form of inventory')
        return name

    def addInventory(self, invType, count, useDemandList=False):
        """
        add to or subtract from inventory/demand for a store
        """
        if count == 0:
            return
        
        if useDemandList:
            invList = self.demand
        else:
            invList = self.inventory

        name = self._invName(invType)
        i, item = self._findInvRec(name, invList)

        if item is None:
            if useDemandList:
                self._addDemandRec(invType, count)
            else:
                self._addInvRec(invType, count)
            return

        if item.count + count == 0:
            invList.pop(i)
            return

        item.count += count

    def updateInventory(self, invType, count, useDemandList=False):
        """
        set inventory or demand level for a specific type in a store
        """
        if useDemandList:
            invList = self.demand
        else:
            invList = self.inventory

        name = self._invName(invType)
        i, item = self._findInvRec(name, invList)

        if item is None:
            if count == 0:
                return

            if useDemandList:
                self._addDemandRec(invType, count)
            else:
                self._addInvRec(invType, count)
            return

        if count == 0:
            invList.pop(i)
            return

        item.count = count

    def countInventory(self, invType, useDemandList=False):
        """
        find how many of a specific inventory/demand type exists for a store
        """
        if useDemandList:
            invList = self.demand
        else:
            invList = self.inventory

        name = self._invName(invType)

        i, item = self._findInvRec(name, invList) # @UnusedVariable

        if item is None:
            return 0
        else:
            return item.count

    def updateDemand(self, demandType, count):
        self.updateInventory(demandType, count, True)

    def addDemand(self, demandType, count):
        self.addInventory(demandType, count, True)

    def countDemand(self, demandType):
        return self.countInventory(demandType, True)

    def _findInvRec(self, name, invList):
        for i,item in enumerate(invList):
            if item.invName == name:
                return i, item

        return -1, None

    def _addInvRec(self, invType, count):
        inv = ShdInventory(ShdInventory.SOURCE_STORE,
                           self.idcode,
                           invType,
                           count)
        self.inventory.append(inv)

    def _addDemandRec(self, demandType, count):
        inv = ShdInventory(ShdInventory.SOURCE_STORE_DEMAND,
                           self.idcode,
                           demandType,
                           count)
        self.demand.append(inv)


    # the rest of these inv/demand low level routines aren't used
    # and will be trashed.
    def _XXXremoveInvRec(self, invType, invList=None):
        if invList is None:
            invList = self.inventory

        if isinstance(invType, types.StringTypes):
            name = invType
        else:
            name = invType.Name

        for i,item in enumerate(invList):
            if item.invName == name:
                invList.pop(i)
                break
        else:
            raise RuntimeError('tried to remove non-existant demand/inventory rec named %s'%name)

    def _XXXremoveDemandRec(self, demandType):
        self._removeInvRec(demandType, self.demands)
        
    def _updateInvRec(self, invType, count, invList=None):
        if invList is None:
            invList = self.inventory

        if isinstance(invType, types.StringTypes):
            name = invType
        else:
            name = invType.Name

        for item in invList:
            if item.invName == name:
                item.count = count
                break
        else:
            raise RuntimeError('tried to update non-existant demand/inventory rec named %s'%name)

    def _XXXupdateDemandRec(self, demandType, count):
        self._updateInvRec(demandType, count, self.demands)


    def createRecord(self):
        """
        create a store file record line as though it were just read in from the csv
        """
        rec = CSVDict()
        _copyAttrsToRec(rec, self)

        return rec

    def clients(self):
        clients = []
        for rStop in self.relatedStops:
            #print rStop
            if rStop.isSupplier is False:
                continue
            #print rStop.route
            route = rStop.route
            supplierStopNum = ShdRoute.routeTypes[route.Type]
            supplierStop = route.stops[supplierStopNum]
            if supplierStop.store is not self:
                continue
            for stop in route.stops:
                if stop.store is self:
                    continue
                client = (stop.store, route)
                if client in clients:
                    continue
                clients.append(client)
        return clients

    def recursiveClients(self):
        clients = self.clients()
        for client, route in list(clients):
            clients.extend(client.recursiveClients())

        return clients

    def clientRoutes(self):
        clientRoutes = []
        for rStop in self.relatedStops:
            if rStop.isSupplier is False:
                continue
            route = rStop.route
            supplierStopNum = ShdRoute.routeTypes[route.Type]
            supplierStop = route.stops[supplierStopNum]
            if supplierStop.store is not self:
                continue
            if route in clientRoutes:
                continue
            clientRoutes.append(route)
        return clientRoutes
        

    def suppliers(self):
        suppliers = []
        for rStop in self.relatedStops:
            route = rStop.route
            supplierStopNum = ShdRoute.routeTypes[route.Type]
            supplierStop = route.stops[supplierStopNum]
            if supplierStop.store is self:
                continue
            supplier = (supplierStop.store, route)
            if supplier in suppliers:
                continue
            suppliers.append(supplier)
                    
        return suppliers

    def supplierRoute(self):
        s = self.suppliers()
        if len(s) == 0:
            return None
        if len(s) == 1:
            return s[0][1]
        raise RuntimeError("only one supplier expected")
    
    def supplierStore(self):
        s = self.suppliers()
        if len(s) == 0:
            return None
        if len(s) == 1:
            return s[0][0]
        raise RuntimeError("only one supplier expected")
            

    def recursiveSuppliers(self):
        suppliers = self.suppliers()
        for supplier, route in list(suppliers):
            suppliers.extend(supplier.recursiveSuppliers())
        
        return suppliers
        

    def addRelatedStop(self, stop):
        if stop in self.relatedStops:
            return
        self.relatedStops.append(stop)

    def removeRelatedStop(self, stop):
        if stop not in self.relatedStops:
            return
        self.relatedStops.remove(stop)


def storeLoadListener(store, context):
    pass
    #print "loading store %s (%d)"%(store.NAME, store.idcode)

_makeColumns(ShdStore)
#the following form _should_ work but doesn't seem to be doing so.
#ShdStore.__table_args__ = (Index('storesIdx', 'modelId', 'idcode'))
Index('storesIdx', ShdStore.modelId, ShdStore.idcode)


#saEvent.listen(ShdStore, 'load', storeLoadListener)

class ShdStop(Base, ShdCopyable):
    """
    ShdStop is a class to hold an individual stop within a ShdRoute
 
    Do not use RouteName, LocName, idcode, or RouteOrder.
    Use route to access the route this stop is attached to.
    Use store to access anything regarding the store to which this stop is attached.
    Use this stops placement in the list of stops to determine route order.
    
    LocName is not copied.
    idcode and RouteOrder should not be used but are maintained for Database usage.
    These will be ignored until overwritten by canonical data sources.

    """

    __tablename__ = 'stops'
    stopId = Column(Integer, primary_key=True)

    attrs =  [('modelId',            DataType(INTEGER, foreignKey = 'models.modelId'),
               'noInputRec', True),
              ('RouteName',          DataType(STRING, foreignkey = 'routes.RouteName')),
              ('LocName',            DataType(STRING, dbType=None), 
               'copy', False, 'relationship', None),
              ('idcode',             LONG),
              ('RouteOrder',         INTEGER_ZERO),
              ('TransitHours',       FLOAT_ZERO),
              ('DistanceKM',         FLOAT_NONE),
              ('PullOrderAmountDays',FLOAT_NONE),
              ('Notes',              NOTES_STRING),
              ('isSupplier',         BOOLEAN, 'noInputRec', True),
              ('store',              None, 'relationshiptype', 'manytoone'),
              ('route',              None, 'relationshiptype', 'manytoone')]

    store = relationship('ShdStore', 
                         uselist=False,
                         primaryjoin="and_(ShdStop.modelId==ShdStore.modelId, "
                                          "ShdStop.idcode==ShdStore.idcode)",
                         foreign_keys="[ShdStore.modelId,ShdStore.idcode]",
                         viewonly=True)

    route = relationship('ShdRoute',
                         uselist=False,
                         primaryjoin="and_(ShdRoute.modelId==ShdStop.modelId, "
                                          "ShdRoute.RouteName==ShdStop.RouteName)",
                         foreign_keys="[ShdRoute.modelId,ShdRoute.RouteName]",
                         viewonly=True)

    def __repr__(self):
        return "<ShdStop instance traveling to %s(%s)>"%(self.store.NAME,self.store.idcode)

    def __init__(self, rec, stores, route):
        nc = _moveAttrs(self, rec)
        self.store = stores[self.idcode]
        self.route = route

    def nextStop(self, loopOk=False):
        """
        return the next stop. 

        if loopOk is False, raises IndexError() if the last stop.  
        otherwise returns 0th stop.

        This depends on stops being ordered by relabelRouteOrder()
        """
        try:
            return self.route.stops[self.RouteOrder + 1]
        except Exception as e:
            if loopOk:
                return self.route.stops[0]
            else:
                raise e


_makeColumns(ShdStop)
Index('stopsIdxId', ShdStop.modelId, ShdStop.idcode)
Index('stopsIdxRn', ShdStop.modelId, ShdStop.RouteName)


class RouteTypeDescriptor():
    def __init__(self, keyword, supplierStop = 0, isScheduled = False, displayName = None,
                 usesPullMeanFrequency = False):
        self._keyword = keyword
        self._supplierStop = supplierStop
        self._isScheduled = isScheduled
        self._usesPullMeanFrequency = usesPullMeanFrequency
        if displayName is None:
            self._displayName = keyword
        else:
            self._displayName = displayName

    def supplierStop(self):
        return self._supplierStop

    def ss(self):
        return self._supplierStop

    def firstClientStop(self):
        if self.ss() == 0:
            return 1
        return 0

    def isScheduled(self):
        return self._isScheduled

    def multiClient(self):
        "returns true if multiple clients are allowed"
        return self._isScheduled
    
    def isAttached(self):
        return self._keyword == 'attached' # In case we create more types of attachment
    
    def usesPullMeanFrequency(self):
        return self._usesPullMeanFrequency

    def display(self):
        return self._displayName

class ShdRoute(Base):
    """
    This holds the data for a single route including the individual stops along the route.

    One can add, remove or change stops on a route but before doing this the route must be 
    unlinked (using unlinkRoute()) from the stores and after your changes have been made 
    the route should be relinked (using linkRoute()).

    Routes are created from lists of dicts holding the route records (one dict per stop)
    or they can be created with a single dict with no stops specified (and are considered
    unlinked).

    Currently when initializing a route, RouteOrder is not used for putting the stops in order.
    The constructor assumes that the stops are in order in the list of records.

    attribrutes include:
        the list of attributes in 'routeAttrs' (copied from the first rec in the route record list).
        stops:  a list of 'ShdStop's stored in route order.
        reports:  a dictionary of report records that have been attached to this route.
        rpt:  the most recent report record attached to this route or None if none added.

    methods:
        supplier() returns the store that supplies the route (or None)
        clients() returns a list of stores that are clients of the route (or None if there is no supplier)
        unlinkRoute()
        linkRoute()

    """

    __tablename__ = 'routes'
    routeId = Column(Integer, primary_key=True)

    attrs = [('modelId',            DataType(INTEGER, foreignKey = 'models.modelId'),
              'noInputRec', True),
             ('RouteName',          STRING, 'delete', False),
             ('Type',               STRING),
             ('TruckType',          STRING_NULL),
             ('ShipIntervalDays',   FLOAT_ZERO),
             ('ShipLatencyDays',    FLOAT_ZERO),
             ('Conditions',         STRING_NULL)]
    
    stops = relationship('ShdStop', 
                         #backref='route', # don't use backref so I can do things with noop'd sqlalchemy
                         cascade='all, delete, delete-orphan', 
                         primaryjoin="and_(ShdRoute.modelId==ShdStop.modelId, "
                                          "ShdRoute.RouteName==ShdStop.RouteName)",
                         foreign_keys="[ShdStop.modelId,ShdStop.RouteName]",
                         order_by="ShdStop.RouteOrder")

    reports = relationship('RoutesRpt',
                           primaryjoin="and_(ShdRoute.modelId == RoutesRpt.modelId, "
                                            "ShdRoute.RouteName == RoutesRpt.RouteName)",
                           foreign_keys="[RoutesRpt.modelId, RoutesRpt.RouteName]",
                           collection_class=attribute_mapped_collection('resultsId'),
                           viewonly = True)

    types = { 'push' : RouteTypeDescriptor('push', isScheduled=True),
              'varpush' : RouteTypeDescriptor('varpush', isScheduled=True),
              'pull' : RouteTypeDescriptor('pull', usesPullMeanFrequency=True),
              'attached' : RouteTypeDescriptor('attached'),
              'schedfetch' : RouteTypeDescriptor('schedfetch', supplierStop=1, isScheduled=True),
              'schedvarfetch' : RouteTypeDescriptor('schedvarfetch', supplierStop=1, 
                                                    isScheduled=True),
              'demandfetch' : RouteTypeDescriptor('demandfetch',
                                                  supplierStop=1,
                                                  usesPullMeanFrequency=True),
              'askingpush' : RouteTypeDescriptor('askingpush', isScheduled=True),
              'dropandcollect' : RouteTypeDescriptor('dropandcollect', isScheduled=True),
              'persistentpull' : RouteTypeDescriptor('persistentpull',
                                                     usesPullMeanFrequency=True),
              'persistentdemandfetch' : RouteTypeDescriptor('persistentdemandfetch', 
                                                            supplierStop=1,
                                                            usesPullMeanFrequency=True) }

    # I'd like routeTypes to be deprecated but there's so much that uses it right now
    # that I'll build it from types
    routeTypes = {}
    for (t,d) in types.items():
        routeTypes[t] = d.ss()

#    routeTypes = {'push':0, 'varpush':0, 'pull':0, 'attached':0,
#                  'schedfetch':1, 'schedvarfetch':1, 'demandfetch':1,
#                  'askingpush':0, 'dropandcollect':0,
#                  'persistentpull':0, 'persistentdemandfetch':1}
    
#    routeIsScheduled = {'push':True, 'varpush':True, 'pull':False, 'attached':False,
#                        'schedfetch':True, 'schedvarfetch':True, 'demandfetch':False,
#                        'askingpush':True, 'dropandcollect':True,
#                        'persistentpull':False, 'persistentdemandfetch':False}
    
    def __repr__(self):
        return "<ShdRoute instance %s>"%(self.RouteName)

    def __init__(self, rrList, stores, noStops=False):
        rrList = listify(rrList)

        rr = rrList[0]
        _moveAttrs(self, rr)

        # pull all of the duplicate stuff out of the subsequent route records 
        for x in rrList[1:]:
            trashrec = {}
            _moveAttrs(trashrec, x, self.attrs)

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

    def relabelRouteOrder(self):
        for i,stop in enumerate(self.stops):
            stop.RouteOrder = i

    def addStop(self, rec, stores, relink = False, order = -1):
        "Add a stop to the route"
        if relink:
            self.unlinkRoute()

        stop = ShdStop(rec, stores, self)

        if order == -1:
            self.stops.append(stop)
        else:
            self.stops.insert(stop, order)
                         
        self.relabelRouteOrder()

        if relink:
            self.linkRoute()

    def removeStop(self, store, relink = False):
        """
        remove a stop from a route.  store should be an actual store (rather than idcode)
        
        It's possible that there are multiple stops to the same store.  Delete all of them.
        """
        if relink:
            self.unlinkRoute()

        found = False
        for stop in self.stops:
            if stop.store is store:
                found = True
                self.stops.remove(stop)
        
        if not found:
            raiseRuntimeError("Tried to remove stop that didn't exist from route")
        
        self.relabelRouteOrder()

        if relink:
            self.linkRoute()


    def linkRoute(self):
        for i,stop in enumerate(self.stops):
            if i == self.routeTypes[self.Type]:
                stop.isSupplier = True
            else:
                stop.isSupplier = False
            
            stop.store.addRelatedStop(stop)
            #print "link: %s %s"%(stop.store, stop.idcode)

        

    def unlinkRoute(self):
        for stop in self.stops:
            #print "unlink: %s %s"%(stop.store, stop.idcode)
            stop.store.removeRelatedStop(stop)
        

    def createRecords(self):
        """
        create a set of routes file record lines as though they were just read in from the csv
        """
        recs = []

        for i,stop in enumerate(self.stops):
            rec = CSVDict()
            #rec = copy.copy(stop.rec)
            #rec['idcode'] = stop.store.idcode
            rec['LocName'] = stop.store.NAME
            #rec['RouteOrder'] = i

            _copyAttrsToRec(rec, stop)
            _copyAttrsToRec(rec, self)
            recs.append(rec)

        return recs

    def supplier(self):
        supplierStopNum = ShdRoute.routeTypes[self.Type]
        try:
            return self.stops[supplierStopNum].store
        except:
            return None

    def clients(self):
        supplier = self.supplier()
        if supplier is None:
            return None

        clients = []
        for stop in self.stops:
            if stop.store is supplier:
                continue
            if stop.store in clients:
                continue
            clients.append(stop.store)

        return clients
        

_makeColumns(ShdRoute)
Index('routesIdxName', ShdRoute.modelId, ShdRoute.RouteName)


class VaxRpt(Base):
    __tablename__ = 'vaxRpt'
    vaxRptId = Column(Integer, primary_key=True)

    attrs = [('storesRptId', DataType(INTEGER, foreignKey = 'storesRpt.storesRptId'),
              'noInputRec', True),
             ('vax',         STRING,  'noInputRec', True),
             ('expired',     FLOAT_ZERO, 'recordName', '_expired'),
             ('outages',     FLOAT_ZERO, 'recordName', '_outages'),
             ('patients',    FLOAT_ZERO, 'recordName', '_patients'),
             ('treated',     FLOAT_ZERO, 'recordName', '_treated'),
             ('vials',       FLOAT_ZERO, 'recordName', '_vials')]

    def __init__(self, vax, rec):
        self.vax = vax
        _moveAttrs(self, rec, self.attrs, prefix = vax)
    
    def __iadd__(self,vaxrpt_):
        if isinstance(vaxrpt_,VaxRpt) is False:
            raiseRuntimeError("can only iadd another VaxRpt with each other")
        if self.vax != vaxrpt_.vax:
            raiseRuntimeError("Cannot add two VaxRpts with different vaccines")
        
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                value = getattr(self,attr) + getattr(vaxrpt_,attr)
                setattr(self,attr,value)               
        return self
    
    def __idiv__(self,factor_):
        facFloat = None
        try:
            facFloat = float(factor_)
        except:
            raiseRuntimeError("Factor must be able to be cast as a float when idiv VaxRpts")
   
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                value = float(getattr(self,attr)/facFloat)
                setattr(self,attr,value)        
        return self
    
    def resetToZero(self):
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                setattr(self,attr,0.0) 
    
    
_makeColumns(VaxRpt)


class StorageRpt(Base):
    __tablename__ = 'storageRpt'
    storageRptId = Column(Integer, primary_key=True)
    
    attrs = [('storesRptId',    DataType(INTEGER, foreignKey = 'storesRpt.storesRptId'),
              'noInputRec', True),
             ('storageType',    STRING,   'noInputRec', True),
             ('fillRatio',      FLOAT_ZERO, 'recordName', ''),
             ('vol',            FLOAT_ZERO, 'recordName', '_vol'),
             ('vol_used',       FLOAT_ZERO, 'recordName', '_vol_used')]

    def __init__(self, storageType, rec):
        self.storageType = storageType
        _moveAttrs(self, rec, self.attrs, prefix = storageType)
    
    def __iadd__(self,storagerpt_):
        if isinstance(storagerpt_,StorageRpt) is False:
            raiseRuntimeError("Can only iadd a StorageRpt with another StorageRpt")
        
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                value = getattr(self,attr) + getattr(storagerpt_,attr)
                setattr(self,attr,value)        
        return self
    
    def __idiv__(self,factor_):
        facFloat = None
        try:
            facFloat = float(factor_)
        except:
            raiseRuntimeError("Factor must be able to be cast as a float when idiv StorageRpt")
        
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                value = getattr(self,attr)/facFloat
                setattr(self,attr,value)    
        return self
    
    def resetToZero(self):
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                setattr(self,attr,0.0)   
 
    def createRecord(self):
        newRec = {}
        srec = {}
        _copyAttrsToRec(srec,self)
        for key,value in srec.items():
            newRec[self.storageType+key] = value
        
        return newRec
_makeColumns(StorageRpt)


class BlobHolder(Base):
    """
    This class adds a layer of abstraction so that Blobs are only accessed when specifically desired
    and don't clutter up table displays or increase DB usage.
    """
    __tablename__ = 'blobHolder'
    blobId = Column(Integer, primary_key=True)
    blob = Column(LargeBinary)

    def __init__(self, blob):
        self.blob = blob


class StoreVialsBlobHolder(Base):
    """
    This class adds a layer of abstraction so that Blobs are only accessed when specifically desired
    and don't clutter up table displays or increase DB usage.
    """
    __tablename__ = 'storeVialsBlobHolder'
    blobId = Column(Integer, primary_key=True)
    blob = Column(LargeBinary)
    
    def __init__(self, blob):
        self.blob = blob
        

class StoresRpt(Base):
    """
    Besides what's in the attrs list, the following attributes are stored with the 
    StoresRpt structure:
      vax:        dictionary keyed by vaccine type each pointing to a VaxRpt
      storage:    dictionary keyed by storage type, each pointing to a StorageRpt
    """
    __tablename__ = 'storesRpt'
    storesRptId = Column(Integer, primary_key=True)

    def copyStorageRatio(self, mv):
        if mv is None or mv == '':
            self.storageRatio_multival   = None
            self.storageRatio_packedMV   = None
            return
        
        if isinstance(mv, util.AccumMultiVal):
            #print 'packing %s'%type(mv)            
            self.storageRatio_packedMV   = BlobHolder(mv.pack())
        else:
            #print 'dropping %s'%type(mv)            
            self.storageRatio_multival   = None
            self.storageRatio_packedMV   = None
    
    def copyStoreVialCount(self, mv):
        if mv is None or mv == '':
            self.storeVialCount_multival = None
            self.storeVialCount_packedMV = None
            return

        if isinstance(mv, util.AccumMultiVal):
            #print 'packing %s'%type(mv)            
            self.storeVialCount_packedMV = StoreVialsBlobHolder(mv.packWKeys())        
        else:
            #print 'dropping %s'%type(mv)            
            self.storeVialCount_multival = None
            self.storeVialCount_packedMV = None
        
    attrs = [('resultsId',      DataType(INTEGER, foreignKey='results.resultsId'),
              'noInputRec',True),
             # I shouldn't _need_ modelId here, but I'm otherwise failing to get what I need
             # out of sqlalchemy
             ('modelId',        DataType(INTEGER, foreignKey='models.modelId'),
              'noInputRec',True),  
             ('code',           LONG),
             ('name',           DataType(STRING, dbType=None),   'copy', False),
             ('category',       STRING),
             ('function',       DataType(STRING, dbType=None),   'copy', False),
             ('one_vaccine_outages', FLOAT_ZERO),
             ('overstock_time', FLOAT_ZERO),
             ('stockout_time',  FLOAT_ZERO),
             ('tot_delivery_vol', FLOAT_ZERO),
             # storageRatio_multival is just a pointer, use storageRatioMV
             ('storageRatio_multival', DataType(INTEGER, foreignKey='blobHolder.blobId'), 
              'copy', copyStorageRatio),
             ('storeVialCount_multival',DataType(INTEGER, foreignKey='storeVialsBlobHolder.blobId'),
              'copy', copyStoreVialCount)]

    storageRatio_packedMV = relationship('BlobHolder', uselist=False)
    storeVialCount_packedMV = relationship('StoreVialsBlobHolder', uselist=False)
    
    storage = relationship('StorageRpt',
                           primaryjoin="StorageRpt.storesRptId == StoresRpt.storesRptId",
                           foreign_keys="[StorageRpt.storesRptId]",
                           collection_class=attribute_mapped_collection('storageType'))
    
    vax = relationship('VaxRpt',
                       primaryjoin="VaxRpt.storesRptId == StoresRpt.storesRptId",
                       foreign_keys="[VaxRpt.storesRptId]",
                       collection_class = attribute_mapped_collection('vax'))

                                 
    def storageRatioMV(self):
        packedMV = self.storageRatio_packedMV
        if packedMV is None:
            return None
        packedMV = packedMV.blob
        
        # should we ever change storage types any previously stored results will _bomb_.
        nameList = copy.copy(storagetypes.storageTypeNames)
        nameList.append('time')
        nameList = tuple(nameList)
        return util.AccumMultiVal.fromPackedString(nameList, packedMV)
    
    def storeVialCountMV(self):
        packedMV = self.storeVialCount_packedMV
        if packedMV is None:
            return None
        packedMV = packedMV.blob
        
        # should we ever change storage types any previously stored results will _bomb_.
        return util.AccumMultiVal.fromPackedStringWHeaders(packedMV)
    
    def __init__(self, rec):
        _moveAttrs(self, rec)

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

    def createRecord(self): 
        newRec = {}
        storeRec = {}
        vaxRec = {}
        _copyAttrsToRec(newRec,self)
        from storagetypes import storageTypeNames
        for storageType in storageTypeNames:
            if self.storage.has_key(storageType):
                _copyAttrsToRec(storeRec,self.storage[storageType])
                for key,value in storeRec.items():
                    newRec[storageType+key] = value
            
        for vaxName in self.vax.keys():
            _copyAttrsToRec(vaxRec,self.vax[vaxName])
            for key,value in vaxRec.items():
                newRec[vaxName+key] = value
        
        return newRec
    
    def __iadd__(self,storerpt_):
        ### Note, this will not add the blobs, that is not supported at the moment
        if isinstance(storerpt_,StoresRpt) is False:
            raiseRuntimeError("can only iadd a StoreRpt with another StoreRpt")

        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                value = getattr(self,attr) + getattr(storerpt_,attr)
                setattr(self,attr,value)
         
        from storagetypes import storageTypeNames
        #print "len store: " + str(len(self.storage))
        if hasattr(storerpt_, 'storage'):
            for storageType in storageTypeNames:
                # ## Is it in self?
                if storageType in self.storage.keys():
                    if storageType in storerpt_.storage.keys():
                        self.storage[storageType] += storerpt_.storage[storageType]
                elif storageType in storerpt_.storage.keys():
                    strrpt = StorageRpt(storageType, storerpt_.storage[storageType].createRecord())
                    self.storage[storageType] = strrpt
        
        if hasattr(storerpt_,'vax'):
            for vName,report in self.vax.items():
                if vName in storerpt_.vax.keys():
                    report += storerpt_.vax[vName]
    
            ### check if the vaccine is in the new storerpt, if so add it 
            for vName,report in storerpt_.vax.items():
                if vName not in self.vax.keys():
                    self.vax[vName] = {}
                    for key,value in report.items():
                        self.vax[vName][key] = value
            
        return self
    
    def __idiv__(self, factor_):
        facFloat = None
        try:
            facFloat = float(factor_)
        except:
            raiseRuntimeError("Factor must be able to be cast as a float when idiv StorageRpt")
        
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                value = getattr(self,attr)/facFloat
                setattr(self,attr,value)

        for key,report in self.storage.items():
            report /= facFloat
        for key,report in self.vax.items():
            report /= facFloat
            
        return self
    
    def resetToZero(self):
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                setattr(self,attr,0.0)
        
        for key,report in self.storage.items():
            report.resetToZero()
        for key,report in self.vax.items():
            report.resetToZero()
        
        ### at this point, we need to delete the blobs
        #self.storageRatio_multival = None
        #self.storeVialCount_multival = None
                
_makeColumns(StoresRpt)

class RoutesRpt(Base):
    """
    The routes report structures is really simple.  Just what's in the attrs list.
    """
    __tablename__ = 'routesRpt'
    routesRptId = Column(Integer, primary_key=True)

    def copyTripTimes(self, tt):
        if tt is None or tt == '':
            self.triptimes_multival = None
            self.triptimes_packedMV = None
            return
        if isinstance(tt,util.AccumMultiVal):
            #print 'packing %s'%type(tt)
            self.triptimes_packedMV = BlobHolder(tt.pack())
        else:
            #print 'dropping %s'%type(tt)
            self.triptimes_multival = None
            self.triptimes_packedMV = None            

    attrs = [('resultsId',        DataType(INTEGER, foreignKey='results.resultsId'),
              'noInputRec', True),
             # again, I shouldn't need modelId
             ('modelId',          DataType(INTEGER, foreignKey='models.modelId'),
              'noInputRec', True),
             ('RouteName',        STRING),
             ('RouteFill',        FLOAT_ZERO),
             ('RouteTrips',       FLOAT_ZERO),
             ('RouteTruckType',   STRING,  'copy', False),
             ('triptimes_multival', DataType(INTEGER, foreignKey='blobHolder.blobId'), 'copy', copyTripTimes)]
    
    def __init__(self, rec):
        _moveAttrs(self, rec)

    triptimes_packedMV = relationship('BlobHolder', uselist=False)

    def tripTimesMV(self):
        packedMV = self.triptimes_packedMV
        if packedMV is None:
            return None
        packedMV = packedMV.blob
        
        nameList = ('distance', 'startTime', 'endTime')
        return util.AccumMultiVal.fromPackedString(nameList, packedMV)
    
    def createRecord(self):
        newRec = {}
        _copyAttrsToRec(newRec,self)
        return newRec
    
    def __iadd__(self,routeRpt_):
        if isinstance(routeRpt_,RoutesRpt) is False:
            raiseRuntimeError("Cannot incrementally add anything but a RouteRpt with a RouteRpt")
        
        
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                value = getattr(self,attr) + getattr(routeRpt_,attr)
                setattr(self,attr,value)
        
        return self
     
    def __idiv__(self,factor_):
        facFloat = None
        try:
            facFloat = float(factor_)
        except:
            raiseRuntimeError("Factor must be able to be cast as a float when idiv RouteRpt")
        
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                value = getattr(self,attr)/facFloat
                setattr(self,attr,value)
        
        return self
    
    def resetToZero(self):
        for attr in self.__dict__.keys():
            if isinstance(getattr(self,attr),float):
                setattr(self,attr,0.0)
        
        return self
    
_makeColumns(RoutesRpt)

class HermesResultsGroup(Base):
    """
    This holds 1 or more sets of results from runs of Hermes on a model.

    There is crazy initialization so that this is not necessarily attached to the
    same db session as the model that comes in with it or such that it can be 
    created without a database at all.
    """

    __tablename__ = "resultsGroup"
    resultsGroupId = Column(Integer, primary_key=True)
    
    attrs = [('modelId',     DataType(INTEGER, foreignKey='models.modelId'),
              'noInputRec', True),
             ('name',        STRING)
             # add bookkeeping stuff here, like date, user, etc.
             ]

    parms = relationship('ShdParameter',
                         cascade="all, delete, delete-orphan",
                         primaryjoin = "and_(HermesResultsGroup.modelId==ShdParameter.modelId, HermesResultsGroup.resultsGroupId == ShdParameter.resultsGroupId)",
                         collection_class=attribute_mapped_collection('key'),
                         foreign_keys="ShdParameter.modelId, ShdParameter.resultsGroupId")
    _nextId = 0
    @classmethod
    def _getNextResultsGroupId(cls):
        retVal = cls._nextId
        cls._nextId += 1
        return retVal


    def __init__(self, modelOrId, name, standAlone=False):
        self.name = name
        self.standAlone = standAlone
        self.results = []

        if isinstance(modelOrId, ShdNetwork):
            # working with a model
            model = modelOrId
            if standAlone:
                # this is the one case where we're working without a DB
                # do everything here manually and return
                #print "setting resultsGroupId"
                self.resultsGroupId = self._getNextResultsGroupId()
                model.resultsGroups.append(self)
                return

            # from here on to the end of the function, we're assuming a DB
            modelId = model.modelId
            for x in model.parms:
                print x.key 
        else:
            modelId = modelOrId

            
        self.modelId = modelId
        # at this point this instance must be committed and then it will show 
        # up in model.resultsGroups and resultsGroupId will be set.
        #
        # then, and only then, can this be used.
        return
    

    results = relationship('HermesResults',
                           cascade = "all, delete, delete-orphan",
                           #primaryjoin="and_(HermesResultsGroup.resultsGroupId == HermesResults.resultsGroupId,HermesResults.resultsType == 'single')",
                           backref = "resultsGroup")
       
    def getAverageResult(self):
        returnResult = [x for x in self.results if x.resultsType == 'average']
        if len(returnResult) > 1:
            raiseRuntimeError("Inconsistent Results Group, should only be one Average Result")
        
        return returnResult[0]
    
    def hasAverageResult(self):
        returnResult = [x for x in self.results if x.resultsType == 'average']
        if len(returnResult) > 0:
            averageResult = self.getAverageResult()
            return True
        return False
    
    def isAverageResultFilled(self):
        if self.hasAverageResult() is False:
            return False
        
        averageResult = self.getAverageResult()
        if len(averageResult.storesRpts) == 0 or len(averageResult.routesRpts) == 0:
            return False
        
        return False

    def hasStdevResult(self):
        for result in self.results:
            if result.resultsType == 'stdev':
                return True
        return False
    
    def addParm(self,parm):
        # Add a single ShdParameter entry"
        self.parms[parm.key] = parm
        
    def _mergeResults(self,net):
        
        resultsToParse = [x for x in self.results if x.resultsType == 'single']      
        firstResult = resultsToParse[0]
        aveResult = self.getAverageResult()
        
        if not self.hasAverageResult():
            ### for now, raise runtime error, later, we can catch this exception
            raiseRuntimeError("Cannot Merge Results into an average without and average")
        
        if not self.isAverageResultFilled():
            ### first the storeRpts
            for storeId,storeRpt in firstResult.storesRpts.items():
                aveStrRpt = StoresRpt(storeRpt.createRecord())
                aveStrRpt.modelId = storeRpt.modelId
                aveResult.storesRpts[storeId] = aveStrRpt
            for routeId,routeRpt in firstResult.routesRpts.items():
                aveRtRpt = RoutesRpt(routeRpt.createRecord())
                aveRtRpt.modelId = routeRpt.modelId
                aveResult.routesRpts[routeId] = aveRtRpt
            
            for summaryId,summaryRec in firstResult.summaryRecs.items():
                aveSumRec = ShdTypeSummary.initSummaryFromRec(summaryRec.createRecord())
                aveSumRec.resultsId = aveResult.resultsId
                aveResult.summaryRecs[aveSumRec.Name] = aveSumRec
                #print "Creating %s"%str(aveSumRec)
                
                
            ### Need to zero out what we got
        for storeId,storeRpt in aveResult.storesRpts.items():
            storeRpt.resetToZero()
        for routeId,routeRpt in aveResult.routesRpts.items():
            routeRpt.resetToZero()
        for summaryId,summaryRec in aveResult.summaryRecs.items():
            summaryRec.resetToZero()
        
        ### for now, setting these to the first result, as we really don't have an average for them yet
        for storeId,storeRpt in firstResult.storesRpts.items():
            aveResult.storesRpts[storeId].storeVialCount_multival = storeRpt.storeVialCount_multival
            aveResult.storesRpts[storeId].storageRatio_multival = storeRpt.storageRatio_multival
            
        for routeId,routeRpt in firstResult.routesRpts.items():
            aveResult.routesRpts[routeId].triptimes_multival = routeRpt.triptimes_multival
        
        for storeId,storeRpt in aveResult.storesRpts.items():
            for result in resultsToParse:
                storeRptR = result.storesRpts[storeId]
                storeRpt += storeRptR
        for routeId,routeRpt in aveResult.routesRpts.items():
            for result in resultsToParse:
                routeRptR = result.routesRpts[routeId]
                routeRpt += routeRptR
        for summaryId,summaryRec in aveResult.summaryRecs.items():
            for result in resultsToParse:
                summaryRecR = result.summaryRecs[summaryId]
                summaryRec += summaryRecR
             
        for storeId,storeRpt in aveResult.storesRpts.items():
            storeRpt /= float(len(resultsToParse))
        
        for routeId,routeRpt in aveResult.routesRpts.items():
            routeRpt /= float(len(resultsToParse))
            
        for summaryId,summaryRec in aveResult.summaryRecs.items():
            summaryRec /= float(len(resultsToParse))
            
        aveResult.addHistograms(net)
        
_makeColumns(HermesResultsGroup)

def resultsGroupLoadListener(HermesResultsGroup, context):
    HermesResultsGroup.standAlone = False
saEvent.listen(HermesResultsGroup, 'load', resultsGroupLoadListener)

class VAHistBlobHolder(Base):
    """
    This class adds a layer of abstraction so that Blobs are only accessed when specifically desired
    and don't clutter up table displays or increase DB usage.
    """
    __tablename__ = 'vaHistBlobHolder'
    blobId = Column(Integer, primary_key=True)
    blob = Column(LargeBinary)
    
    def __init__(self, blob):
        self.blob = blob

class TransCapHistBlobHolder(Base):
    """
    This class adds a layer of abstraction so that Blobs are only accessed when specifically desired
    and don't clutter up table displays or increase DB usage.
    """
    __tablename__ = 'transCapHistBlobHolder'
    blobId = Column(Integer, primary_key=True)
    blob = Column(LargeBinary)
    
    def __init__(self, blob):
        self.blob = blob
        
class StoreCapHistBlobHolder(Base):
    """
    This class adds a layer of abstraction so that Blobs are only accessed when specifically desired
    and don't clutter up table displays or increase DB usage.
    """
    __tablename__ = 'storeCapHistBlobHolder'
    blobId = Column(Integer, primary_key=True)
    blob = Column(LargeBinary)
    
    def __init__(self, blob):
        self.blob = blob

class HermesResults(Base):
    """
    This will hold information about a specific time that hermes was run
    including links to any outputs produced.
    """
    __tablename__ = "results"
    resultsId = Column(Integer, primary_key=True)
    
    def copykmlViz(self,tt):
        if tt is None or tt == '':
            self.kmlVizStringRef = None
            return
        self.kmlVizStringRef = BlobHolder(tt)
    
    def copyVAJson(self,tt):
        if tt is None or tt == '':
            self.vaccineAvailJsonRef = None
            return
        self.vaccineAvailJsonRef = VAHistBlobHolder(tt)
        
    def copyTransJson(self,tt):
        if tt is None or tt == '':
            self.kmlVizStingRef = None
            return
        self.transportCapJsonRef = TransCapHistBlobHolder(tt)   
        
    def copyStoreJson(self,tt):
        if tt is None or tt == '':
            self.kmlVizStingRef = None
            return
        self.storeCapJsonRef = StoreCapHistBlobHolder(tt)    
            
    attrs = [('resultsGroupId', 
                              DataType(INTEGER, foreignKey='resultsGroup.resultsGroupId'),
              'noInputRec', True),
             ('runNumber',    INTEGER),
             ('resultsType',  STRING), # 'single', 'average'... 
             ('kmlVizStringRef', DataType(INTEGER, foreignKey='blobHolder.blobId'),'copy', copykmlViz),
             ('vaccineAvailJsonRef',DataType(INTEGER, foreignKey='vaHistBlobHolder.blobId'),'copy', copyVAJson),
             ('tranportCapJsonRef',DataType(INTEGER, foreignKey='transCapHistBlobHolder.blobId'),'copy', copyTransJson),
             ('storeCapJsonRef',DataType(INTEGER, foreignKey='storeCapHistBlobHolder.blobId'),'copy', copyStoreJson)
             ] 
             
              
    routesRpts = relationship('RoutesRpt',
                              backref = 'results',
                              cascade = "all, delete, delete-orphan",
                              collection_class=attribute_mapped_collection('RouteName'))
             
    storesRpts = relationship('StoresRpt',
                              backref = 'results',
                              cascade = "all, delete, delete-orphan",
                              collection_class=attribute_mapped_collection('code'))

    summaryRecs = relationship('ShdTypeSummary',
                               backref = 'results',
                               cascade = "all, delete, delete-orphan",
                               collection_class=attribute_mapped_collection('Name'))
    
    costSummaryRecs = relationship('ShdCostSummary',
                                   backref = 'results',
                                   cascade = "all, delete, delete-orphan")
    
    kmlVizString = relationship('BlobHolder', uselist=False)
    vaAvailJson = relationship('VAHistBlobHolder',uselist=False)
    transCapJson = relationship('TransCapHistBlobHolder',uselist=False)
    storeCapJson = relationship('StoreCapHistBlobHolder',uselist=False)
    
    #                            backref = 'blobHolder',
    #                            primaryjoin = "results.kmlVizStringRef == blobHolder.blobId")
    #vaccineAvailJson = relationship('BlobHolder',uselist=False)
    
    _nextId = 0
    @classmethod
    def _getNextResultsId(cls):
        retVal = cls._nextId
        cls._nextId += 1
        return retVal

    def __init__(self, resultsGroup, *args, **kwargs):
        """init a results set from a hermes run.

        resultsGroup can either be a HermesResultsGroup instance or just the ID.
        """

        _initBasic(self, args, kwargs)

        if isinstance(resultsGroup, HermesResultsGroup):
            resultsGroup.results.append(self)
            self.standAlone = resultsGroup.standAlone
            if self.standAlone:
                self.resultsId = self._getNextResultsId()
                resultsGroup.results.append(self)
                
        else:
            self.resultsGroupId = resultsGroup
            self.standAlone = False
        
        routesRpts = {}
        storesRpts = {}
        summaryRecs = {}
    
    def setKmlVizString(self,vizString):
        if self.kmlVizStringRef is None:       
            self.kmlVizString = BlobHolder(vizString)
        else:
            bh = self.kmlVizString
            bh.blob = vizString
 
    def getKmlVizString(self):
        if self.kmlVizString is None:
            return None
        
        return str(self.kmlVizString.blob)
        
    def getVaccineSummary(self):
        pass
    
    def addReportRecs(self, net, reportRecs):
        """
        Add report recs.

        if the report recs are not going into a db then set linkRecsToNet to True.
        This will add a resultsId self if it is currently None and will set 
        """
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
                    raiseRuntimeError("store code %d was found in the report but not in the Hermes ShdNetwork"%code)
                rpt = StoresRpt(rec)
                rpt.modelId = net.modelId
                self.storesRpts[code] = rpt
                if self.standAlone:
                    rpt.resultsId = self.resultsId
                    if not hasattr(net.stores[code], 'reports'):
                        net.stores[code].reports = {}
                    net.stores[code].reports[self.resultsId] = rpt
                    net.stores[code].rpt = rpt
            elif rtName != 'NA':
                if rtName not in net.routes:
                    # currently we'll call this a warning, but soon we will fully deprecate implied links
                    # and this will go back to being a fatal error.
                    logWarning("route name %s was found in the report but not in the Hermes ShdNetwork"%rtName)
                    continue
                    #raiseRuntimeError("route name %s was found in the report but not in the Hermes ShdNetwork"%rtName)
                rpt = RoutesRpt(rec)
                rpt.modelId = net.modelId
                self.routesRpts[rtName] = rpt
                if self.standAlone:
                    if not hasattr(net.routes[rtName], 'reports'):
                        net.routes[rtName].reports = {}
                    net.routes[rtName].reports[self.resultsId] = rpt
                    net.routes[rtName].rpt = rpt
            else:
                raiseRuntimeError("invalid record in report records")
            
        self.addHistograms(net)
            
            
    def addSummaryRecs(self, net, summaryRecDicts):
        "summaryRecDicts is a list of dicts"
        for recDict in summaryRecDicts:
            rec = ShdTypeSummary.initSummaryFromRec(recDict)
            self.summaryRecs[rec.Name] = rec
            
    def addCostSummaryRecs(self, net, summaryRecDicts):
        "summaryRecDicts is a list of dicts"
        for recDict in summaryRecDicts:
            rec = ShdCostSummary.initSummaryFromRec(recDict)
            self.costSummaryRecs.append(rec)
            
    def addHistograms(self,net):          
        self.addVAHist(net)
        self.addTransCapHist(net)
        self.addStoreCapHist(net)
        
    def addVAHist(self,net):
        
        ### --- add 
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']
        sizeBorders = [100,300,1000]
        histogramData = [[0,0,0,0,0,0,0,0,0,0,0],
                         [0,0,0,0,0,0,0,0,0,0,0],
                         [0,0,0,0,0,0,0,0,0,0,0],
                         [0,0,0,0,0,0,0,0,0,0,0]]
        birthCohortDict = {}
        
        for demand in net.populationDemand:
            if demand.invName == "Newborn" or demand.invName == "Newborns":
                birthCohortDict[demand.idcode] = demand.count
                
        for storeRptId, storeRpt in self.storesRpts.items():         
            patients = 0
            treated = 0
            count = 0
            if birthCohortDict.has_key(storeRpt.code):
                birthC = birthCohortDict[storeRpt.code]
                while count < len(sizeBorders) and birthC >= sizeBorders[count]:
                    count += 1
                for v,n in storeRpt.vax.items():
                    patients += n.patients
                    treated += n.treated
                if patients == 0:
                    continue
                avail = (float(treated) / float(patients)) * 100.0
                index = int(math.floor(avail / 10.0))
                histogramData[count][index] += 1
            
        ### create string
        blobString  = ""
        for dataArray in histogramData:
            for data in dataArray:
                blobString += "%s:"%str(data)
        blobString = blobString[:-1]
        
        if self.vaAvailJson is None:
            self.vaAvailJson = VAHistBlobHolder(blobString)
        else:
            bh = self.vaAvailJson
            bh.blob = blobString

    def addTransCapHist(self,net):
        ##----- Add Transport Hist
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']
        histogramData = {}
        for routeRptId,routeRpt in self.routesRpts.items():
            route = net.routes[routeRptId]
            if route.Type != "attached":
                startLevel = route.stops[0].store.CATEGORY
                if startLevel not in histogramData.keys():
                    histogramData[startLevel] = [0,0,0,0,0,0,0,0,0,0,0]
                util = float(routeRpt.RouteFill)*100.0
                if util > 100.0:
                    util = 100.0
                index = int(math.floor(util/10.0))
                histogramData[startLevel][index] += 1
    
        blobStringList = []
        
        blobStringList.append(struct.pack('i',len(histogramData.keys())))
        for level,dataArr in histogramData.items():
            formatString = "<i" + str(len(level)) + "s"
            s = struct.Struct(formatString)
            packList = [len(level),level.encode('utf-8')]
            blobStringList.append(s.pack(*packList))
            blobStringList.append(struct.pack('i',len(dataArr)))
            for data in dataArr:
                blobStringList.append(struct.pack('i',data))
        
        if self.transCapJson is None:
            self.transCapJson = TransCapHistBlobHolder("".join(blobStringList))
        else:
            bh = self.transCapJson
            bh.blob = "".join(blobStringList)
    
    def addStoreCapHist(self,net):
        categories = ['0-9%','10-19%','20-29%','30-39%',
                      '40-49%','50-59%','60-69%','70-79%',
                      '80-89%','90-99%','100%']
        histogramData = {}
        for storeRptId,storeRpt in self.storesRpts.items():
            if storeRpt.category not in histogramData.keys():
                histogramData[storeRpt.category] = [0,0,0,0,0,0,0,0,0,0,0]
            if storeRpt.storage['cooler'].vol > 0.0:
                util = float(storeRpt.storage['cooler'].fillRatio)*100.0
                index = int(math.floor(util/10.0))
                histogramData[storeRpt.category][index] += 1
        
        blobStringList = []
        blobStringList.append(struct.pack('i',len(histogramData.keys())))
        for level,dataArr in histogramData.items():
            formatString = "<i" + str(len(level)) + "s"
            s = struct.Struct(formatString)
            packList = [len(level),level.encode('utf-8')]
            blobStringList.append(s.pack(*packList))
            blobStringList.append(struct.pack('i',len(dataArr)))
            for data in dataArr:
                blobStringList.append(struct.pack('i',data))
        
        #print "StoreString = " + str(blobString
        if self.storeCapJson is None:
            self.storeCapJson = StoreCapHistBlobHolder(''.join(blobStringList))
        else:
            bh = self.storeCapJson
            bh.blob = ''.join(blobStringList)

    def getVAHistString(self):
        if self.vaAvailJson is None:
            return None
         
        return str(self.vaAvailJson.blob)
    
    def getTransCapHistDict(self):
        if self.transCapJson is None:
            return None
        
        ### unpack the histogram
        histDict = {}
        offInt = struct.calcsize('i')
        packString = str(self.transCapJson.blob)
        count = offInt
        numLevels = struct.unpack_from('i',packString)[0]
        for i in range(0,numLevels):
            sLength = struct.unpack_from('i',packString,count)[0]
            count+= offInt
            formatString = "<"+str(sLength)+"s"
            level = struct.unpack_from(formatString,packString,count)[0]
            histDict[level] = []
            count += struct.calcsize(formatString)
            numVals = struct.unpack_from('i',packString,count)[0]
            count += offInt
            for j in range(0,numVals):
                histDict[level].append(struct.unpack_from('i',packString,count)[0])
                count += offInt
        
        return histDict
    
    def getStoreCapHistDict(self):
        if self.storeCapJson is None:
            return None
        
        ### unpack the histogram
        histDict = {}
        offInt = struct.calcsize('i')
        packString = str(self.storeCapJson.blob)
        count = offInt
        numLevels = struct.unpack_from('i',packString)[0]
        for i in range(0,numLevels):
            sLength = struct.unpack_from('i',packString,count)[0]
            count+= offInt
            formatString = "<"+str(sLength)+"s"
            level = struct.unpack_from(formatString,packString,count)[0]
            histDict[level] = []
            count += struct.calcsize(formatString)
            numVals = struct.unpack_from('i',packString,count)[0]
            count += offInt
            for j in range(0,numVals):
                histDict[level].append(struct.unpack_from('i',packString,count)[0])
                count += offInt
        
        return histDict
         
_makeColumns(HermesResults)

def resultsLoadListener(HermesResults, context):
    HermesResults.standAlone = False
saEvent.listen(HermesResults, 'load', resultsLoadListener)

             
class ShdCurrencyConversion(Base):
    __tablename__ = "currencyConversion"
    currencyId = Column(Integer, primary_key=True)
    
    attrs = [('modelId',    DataType(INTEGER, foreignKey='models.modelId'), 'noInputRec', True),
             ('country',    STRING),
             ('currency',   STRING),
             ('code',       STRING),
             ('year',       INTEGER),
             ('value',      FLOAT),
             ('Notes',      NOTES_STRING)]

    def __init__(self, *args, **kwargs):
        _initBasic(self, args, kwargs)

    @staticmethod
    def CurrencyConversionFromRec(rec):
        ret = []
        country = str(rec['Country Name'])
        currency = str(rec['Currency Name'])
        code = str(rec['Currency Code'])
        Notes = ''
        if 'Notes' in rec:
            Notes = str(rec['Notes'])

        for (key,val) in rec.items():
            if key in ['Country Name', 'Currency Name', 'Currency Code', 'Notes']:
                continue
            # don't save holes in the table
            if val is None:
                continue
            if val == "":
                continue
            year = castValue(key, INTEGER.cast(), "currency year")
            value = castValue(val, FLOAT.cast(), "currency value")
            ret.append(ShdCurrencyConversion(country,
                                             currency,
                                             code,
                                             year,
                                             value,
                                             Notes))
        return ret


    @staticmethod
    def createRecords(entries):
        dictOfRecs = {}
        keys = ['Country Name', 'Currency Name', 'Currency Code', 'Notes']
        
        for entry in entries:
            key = (entry.code, entry.country, entry.currency)
            if key not in dictOfRecs:
                rec = CSVDict()
                rec['Country Name'] = entry.country
                rec['Currency Name'] = entry.currency
                rec['Currency Code'] = entry.code
                rec['Notes'] = entry.Notes
                dictOfRecs[key] = rec
            else:
                rec = dictOfRecs[key]
                # validate the rest of the data?
                #if (rec['Country Name'] != entry.country) or \
                #        (rec['Currency Name'] != entry.currency):
                #    logWarning("currency conversion records have mismatched data (%s,%s) (%s,%s)"%\
                #                   (rec['Country Name'],entry.country,rec['Currency Name'],entry.currency))

            rec[entry.year] = entry.value
            if entry.year not in keys:
                keys.append(entry.year)

        return keys, dictOfRecs.values()

_makeColumns(ShdCurrencyConversion)


class ShdCosts(Base):
    __tablename__ = 'costs'
    costId = Column(Integer, primary_key=True)

    attrs = [('modelId',    DataType(INTEGER, foreignKey='models.modelId'), 'noInputRec', True),
             ('Name',       STRING),
             ('Currency',   STRING),
             ('PerKm',      FLOAT_NONE),
             ('PerYear',    FLOAT_NONE),
             ('PerTrip',    FLOAT_NONE),
             ('PerTreatmentDay', FLOAT_NONE),
             ('PerDiem',    FLOAT_NONE),
             ('PerVial',    FLOAT_NONE),
             ('Level',      STRING_NONE),
             ('Conditions', STRING_NONE),
             ('Notes',      NOTES_STRING)]

    def __init__(self, *args, **kwargs):
        _initBasic(self, args, kwargs)


    def createRecord(self):
        rec = CSVDict()
        _copyAttrsToRec(rec, self)
        return rec
        
_makeColumns(ShdCosts)

class ShdCostSummary(Base, ShdCopyable):
    __tablename__ = 'costSummary'

    summaryId = Column(Integer, primary_key=True)
    costClass = Column(String(30))
    summaryType = 'undefinedType'
    __mapper_args__ = {'polymorphic_identity': summaryType}
    attrs = [('resultsId',    DataType(INTEGER, foreignKey='results.resultsId'),
              'noInputRec', True),
             ]

    __mapper_args__ = {
        'polymorphic_identity':'costSummary',
        'polymorphic_on':costClass
        }



    def __init__(self, name, type_):
        raiseRuntimeError("Can't create base class of cost summary")
        

    @staticmethod
    def initSummaryFromRec(rec):
#         if 'Name' not in rec:
#             raiseRuntimeError('No "Name" (type name) in summary record to be converted')
        if 'Type' not in rec:
            raise RuntimeError('No "Type" (class type) in cost summary record to be converted')
        t = rec['Type']
        if t not in ShdCostSummary.typesMap:
            raise RuntimeError('Unknown cost summary type %s in summary record to be converted'%t)

        return ShdCostSummary.typesMap[t](rec)

    def __iadd__(self,summary_):
        
        if summary_.typeClass != self.typeClass:
            raiseRuntimeError("no, no, no")
        
        for attr in self.__dict__.keys():
            if attr[-2:] != "Id":
                if isinstance(getattr(self,attr),float) or isinstance(getattr(self,attr),int):
                    value = getattr(self,attr) + getattr(summary_,attr)
                    setattr(self,attr,value)               
        
        return self

    def __idiv__(self,factor_):
        facFloat = None
        try:
            facFloat = float(factor_)
        except:
            raiseRuntimeError("Factor must be able to be cast as a float when idiv RouteRpt")
        
        for attr in self.__dict__.keys():
            if attr[-2:] != "Id":
                if isinstance(getattr(self,attr),float) or isinstance(getattr(self,attr),int):
                    value = getattr(self,attr)/facFloat
                    setattr(self,attr,value)
        
        return self
        
    def resetToZero(self):
        for attr in self.__dict__.keys():
            if attr[-2:] != "Id":
                if isinstance(getattr(self,attr),float) or isinstance(getattr(self,attr),int):
                    #value = getattr(self,attr) + getattr(summary_,attr)
                    setattr(self,attr,0.0) 
        return self
    
    def createRecord(self):
        return self.createRec()

_makeColumns(ShdCostSummary)

class ShdLegacyCostSummary(ShdCostSummary):
    __tablename__ = "legacyCostSummary"
    summaryType = 'legacy'
    __mapper_args__ = {'polymorphic_identity': summaryType}

    legacySummaryId = Column(Integer, ForeignKey('costSummary.summaryId'), primary_key=True)

    # apparently there's nothing in this summary dict!
    attrs = [
             ('ReportingLevel', STRING),
             ('ReportingBranch', STRING),
             ('ReportingIntervalDays', FLOAT_NONE),
             ('DaysPerYear', FLOAT_NONE),
             ('Currency', STRING_NONE),
             ('RouteTrips', INTEGER_NONE),
             ('PerDiemDays', INTEGER_NONE),
             ('CostingTreatmentDays', INTEGER_NONE),
             ('PerDiemCost', FLOAT_NONE),
             ('PerKmCost', FLOAT_NONE),
             ('PerTripCost', FLOAT_NONE),
             ('TransportCost', FLOAT_NONE),
             ('LaborCost', FLOAT_NONE),
             ('StorageCost', FLOAT_NONE),
             ('BuildingCost', FLOAT_NONE)
             ]
    
    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

_makeColumns(ShdLegacyCostSummary)

ShdCostSummary.typesMap = {'legacy':ShdLegacyCostSummary,
                           }
    

###
###
###  Unified and Type files
###
###


def _initShdType(instance, args, kwargs):
    """
    Use this for the init function of the net type classes
    """
    return _initBasic(instance, args, kwargs, 0)

class ShdType(Base):
    __tablename__ = 'types'

    typeId = Column(Integer, primary_key=True)
    typeClass = Column(String(30))
    attrs = [('modelId',    DataType(INTEGER, foreignKey='models.modelId'), 'noInputRec', True),
             ('Name',       STRING)]
    
    __mapper_args__ = {
        'polymorphic_identity':'types',
        'polymorphic_on':typeClass
        }
    
    shdType = 'invalid'
    active = False

    def setActive(self):
        self.active = True

    def createRecord(self):
        "Create a typefile record"
        rec = CSVDict()
        _copyAttrsToRec(rec, self)
        return rec
    
    def copy(self):
        rec = self.createRecord()
        return ShdTypes.typesMap[self.typeClass](rec)

    def getDisplayName(self):
        try:
            if self.DisplayName is not None and self.DisplayName.strip() is not '':
                return self.DisplayName
        except:
            pass
        return self.Name
        
        
_makeColumns(ShdType)
Index('typesIdx', ShdType.modelId, ShdType.Name)

    
class ShdIceType(ShdType):
    __tablename__ = "icetypes"
    shdType = 'ice'
    __mapper_args__ = {'polymorphic_identity':shdType}

    icetypeId = Column(Integer, ForeignKey('types.typeId'), primary_key=True)
    attrs = [('Name',       DataType(STRING, dbType=None)),
             ('DisplayName', STRING_NONE),
             ('VolCC',      FLOAT),
             ('FridgeType', STRING),
             ('RandKey',    INTEGER),
             ('ClassName',  STRING),
             ('Requires',   STRING_NONE),
             ('Notes',      NOTES_STRING)]
     
    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

    def copy(self):
        return ShdIceType(self.createRecord())
    
_makeColumns(ShdIceType)


class ShdPackageType(ShdType):
    __tablename__ = "packagetypes"
    shdType = 'packaging'
    __mapper_args__ = {'polymorphic_identity':shdType}

    packagetypeId = Column(Integer, ForeignKey('types.typeId'), primary_key=True)
    attrs = [('Name',       DataType(STRING, dbType=None)),
             ('DisplayName', STRING_NONE),
             ('Contains',   STRING),
             ('Count',      INTEGER),
             ('Category',   STRING),
             ('Volume',     FLOAT, 'recordName', "Volume(CC)"),
             ('SortOrder',  INTEGER),
             ('Requires',   STRING_NONE),
             ('Notes',      NOTES_STRING)]

    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

    def copy(self):
        return ShdPackageType(self.createRecord())

_makeColumns(ShdPackageType)

class ShdPeopleType(ShdType):
    __tablename__ = "peopletypes"
    shdType = 'people'
    __mapper_args__ = {'polymorphic_identity':shdType}

    peopletypeId = Column(Integer, ForeignKey('types.typeId'), primary_key=True)
    attrs = [('Name',       DataType(STRING, dbType=None)),
             ('DisplayName', STRING_NONE),
             ('SortOrder',  INTEGER),
             ('Requires',   STRING_NONE),
             ('Notes',      NOTES_STRING)]
    
    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

    def copy(self):
        return ShdPeopleType(self.createRecord())
     
_makeColumns(ShdPeopleType)


class ShdStorageType(ShdType, ShdCopyable):
    __tablename__ = "storagetypes"
    shdType = 'fridges'
    __mapper_args__ = {'polymorphic_identity':shdType}

    storagetypeId = Column(Integer, ForeignKey('types.typeId'), primary_key=True)
    attrs = [('Name',       DataType(STRING, dbType=None)),
             ('DisplayName', STRING_NONE, 'hybridName', '_DisplayName'),
             ('Make',       STRING_NONE),
             ('Model',      STRING_NONE),
             ('Year',       STRING_NONE),
             ('Energy',     STRING_NONE),
             ('Category',   STRING_NONE),
             ('Technology', STRING_NONE),
             ('BaseCost',   FLOAT_NONE),
             ('BaseCostCurCode', STRING_NONE, 'recordName', 'BaseCostCur'),
             ('BaseCostYear', INTEGER_NONE),
             ('PowerRate',  FLOAT_NONE),
             ('PowerRateUnits', STRING_NONE),
             ('NoPowerHoldoverDays', FLOAT_ZERO),
             ('freezer',    FLOAT_ZERO),
             ('cooler',     FLOAT_ZERO),
             ('roomtemperature', FLOAT_ZERO),
             ('ClassName',  STRING_NONE),
             ('chain',      STRING_NONE),
             ('ColdLifetime', FLOAT_NONE),
             ('AlarmDays',  FLOAT_NONE),
             ('SnoozeDays', FLOAT_NONE),
             ('Requires',   STRING_NONE),
             ('Notes',      NOTES_STRING)]
    
    @hybrid_property
    def DisplayName(self):
        result = self.getDisplayName()
        return result
    
    @DisplayName.setter
    def setDisplayName(self, value):
        if value != self.getDisplayName():
            self._DisplayName = value

    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)
        
    def copy(self):
        return ShdStorageType(self.createRecord())
    
    def getDisplayName(self):
        s_DN = getattr(self,'_DisplayName')
        if s_DN is not None:
            return s_DN
        else:
            # We can't use utility functions here, because they may end
            # up calling this routine recursively
            rec = {}
            for attr in self.attrs:
                lA = listify(attr)
                if 'hybridName' in lA:
                    rec[lA[0]] = ''
                else:
                    rec[lA[0]] = getattr(self,lA[0])
            result = fridgeDisplayNameFromRec(rec)
            return result
    
_makeColumns(ShdStorageType)


class ShdTruckType(ShdType):
    __tablename__ = "trucktypes"
    shdType = 'trucks'
    __mapper_args__ = {'polymorphic_identity':shdType}

    trucktypeId = Column(Integer, ForeignKey('types.typeId'), primary_key=True)
    attrs = [('Name',       DataType(STRING, dbType=None)),
             ('DisplayName', STRING_NONE),
             ('CoolVolumeCC', FLOAT_ZERO),
             ('Storage',    STRING),
             ('Requires',   STRING_NONE),
             ('Notes',      NOTES_STRING)]

    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)
    
    #def getNetStorageCapacity(self):
    #    returnVolDict = {'cooler':0.0,'freezer':0.0}
    #    returnVolDict['cooler'] += self.CoolVolumeCC
    #    for 
        
    def copy(self):
        return ShdTruckType(self.createRecord())

_makeColumns(ShdTruckType)

class ShdVaccineType(ShdType, ShdCopyable):
    __tablename__ = "vaccinetypes"
    shdType = 'vaccines'
    __mapper_args__ = {'polymorphic_identity':shdType}

    @staticmethod
    def lifetimeToRec(arg,preface):
        """
        This is a 'recencode' method, which will be used like rec.update(thisMethodName(arg))
        to convert database information representing this attribute to record form.
        """
        if isinstance(arg,types.DictType):
            unitsChar = arg[preface.lower()+'LifetimeUnits']
            val = arg[preface.lower()+'Lifetime']
        else:
            unitsChar = getattr(arg,preface.lower()+'LifetimeUnits')
            val = getattr(arg,preface.lower()+'Lifetime')
        key = 'Lifetime'+preface+TimeUnitsEnums.eStr[unitsChar].capitalize()
        rec = {key:val}
        return rec
    
    def lifetimeFromRec(self,rec,preface,delete=True):
        """
        This is a 'recdecode' method, which will be used like self.thisMethodName(rec) to convert
        record information for this attribute to database form.  If delete is True, this method
        must delete the corresponding record items.
        """
        if preface.lower()+'LifetimeUnits' in rec:
            key = preface.lower()+'Lifetime'
            uKey = preface.lower()+'LifetimeUnits'
            assert key in rec, _("Missing or invalid time value in record for {0} lifetime").format(preface)
            tvChar = rec[uKey]
            assert tvChar in TimeUnitsEnums.eStr.keys(), _("Invalid time unit identifier {0} in record for {1} lifetime").format(tvChar,preface)
            setattr(self, uKey, tvChar)
            setattr(self, key, castValue(rec[key], (castTypes.EMPTY_IS_ZERO,castTypes.FLOAT), key))
            if delete: 
                del rec[key]
                del rec[uKey]
        else:
            for k,v in TimeUnitsEnums.eStr.items():
                key = 'Lifetime' +preface + v.capitalize()
                if key in rec.keys():
                    setattr(self, preface.lower()+'LifetimeUnits', k)
                    setattr(self, preface.lower()+'Lifetime', castValue(rec[key], (castTypes.EMPTY_IS_ZERO,castTypes.FLOAT), key))
                    if delete: del rec[key]
                    break
            else:
                raise RuntimeError('No %s lifetime info available in %s'%(preface,rec))
    def frzLifetimeToRec(arg):
        """
        This is a 'recencode' method, which will be used like rec.update(self.demandToRec())
        to convert database information representing this attribute to record form.
        """
        return ShdVaccineType.lifetimeToRec(arg,preface='Freezer')
    
    def frzLifetimeFromRec(self,rec,delete=True):
        """
        This is a 'recdecode' method, which will be used like self.demandFromRec(rec) to convert
        record information for this attribute to database form.  If delete is True, this method
        must delete the corresponding record items.
        """
        return self.lifetimeFromRec(rec,delete=delete,preface='Freezer')
    def coolLifetimeToRec(arg):
        return ShdVaccineType.lifetimeToRec(arg,preface='Cooler')
    def coolLifetimeFromRec(self,rec,delete=True):
        return self.lifetimeFromRec(rec,delete=delete,preface='Cooler')
    def roomtempLifetimeToRec(arg):
        return ShdVaccineType.lifetimeToRec(arg,preface='RoomTemp')
    def roomtempLifetimeFromRec(self,rec,delete=True):
        return self.lifetimeFromRec(rec,delete=delete,preface='RoomTemp')
    def openLifetimeToRec(arg):
        return ShdVaccineType.lifetimeToRec(arg,preface='Open')
    def openLifetimeFromRec(self,rec,delete=True):
        return self.lifetimeFromRec(rec,delete=delete,preface='Open')

    vaccinetypeId = Column(Integer, ForeignKey('types.typeId'), primary_key=True)
    attrs = [('Name',       DataType(STRING, dbType=None),
              'relationship', 'types'),
             ('DisplayName',   STRING_NONE),
             ('Abbreviation',  STRING),
             ('presentation',  STRING_NULL, 'recordName', 'Vaccine presentation'),
             ('administration', STRING_NULL, 'recordName', 'Method of administration'),
             ('Manufacturer', STRING_NULL, 'recordName', 'Manufacturer'),
             ('secondaryPackaging', STRING_NULL,'recordName','Secondary Packaging', 
              'synonym', ['secondaryPackaging']),
             ('dosesPerVial',  INTEGER, 'recordName', 'Doses per vial',
              'synonym', ['dosesPerVial']),
             ('volPerDose',    FLOAT, 'recordName', 'Packed vol/dose(cc) of vaccine',
              'synonym', ['volPerDose']),
             ('diluentVolPerDose', FLOAT_ZERO, 'recordName', 'Packed vol/dose(cc) of diluent',
              'synonym', ['diluentVolPerDose']),
             ('pricePerVial',  FLOAT_NONE, 'recordName', 'Vaccine price/vial',
              'synonym', ['pricePerVial']),
             ('pricePerDose',  FLOAT_NONE, 'recordName', 'Vaccine price/dose',
              'synonym', ['pricePerDose']),
             ('priceUnits',    STRING, 'recordName', 'Price Units',
              'synonym', ['priceUnits']),
             ('dosesPerPerson', INTEGER, 'recordName', 'Doses/person',
              'synonym',['dosesPerPerson']),
             ('freezerLifetime', FLOAT, 
              'recencode', frzLifetimeToRec, 'recdecode', frzLifetimeFromRec),
             ('freezerLifetimeUnits', CHAR, 'noInputRec', True),
             ('coolerLifetime', FLOAT, 
              'recencode', coolLifetimeToRec, 'recdecode', coolLifetimeFromRec),
             ('coolerLifetimeUnits', CHAR, 'noInputRec', True),
             ('roomtempLifetime', FLOAT, 
              'recencode', roomtempLifetimeToRec, 'recdecode', roomtempLifetimeFromRec),
             ('roomtempLifetimeUnits', CHAR, 'noInputRec', True),
             ('openLifetime', FLOAT, 
              'recencode', openLifetimeToRec, 'recdecode', openLifetimeFromRec),
             ('openLifetimeUnits', CHAR, 'noInputRec', True),
             ('RandomKey',     INTEGER_ZERO),
             ('Requires',      STRING_NONE),
             ('Notes',         NOTES_STRING),
             ('types',         None, 'relationshiptype', 'onetoone'),
             ('link',          STRING_NONE,'recordName','link')]
    
    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

    def copy(self):
        return ShdVaccineType(self.createRecord())

_makeColumns(ShdVaccineType)

class ShdTypes:
    typesMap = {'ice': ShdIceType,
                'packaging': ShdPackageType,
                'people': ShdPeopleType,
                'fridges': ShdStorageType,
                'trucks': ShdTruckType,
                'vaccines': ShdVaccineType}
             
    def __init__(self):
        self.types = {}
        for key in self.typesMap.keys():
            setattr(self, key, {})

    def addType(self, newType):
        name = newType.Name
        self.types[name] = newType
        typeDict = getattr(self, newType.shdType)
        typeDict[name] = newType

    def importRecordsFromFile(self, fileOrHandle, recType):
        (keys, recs) = csv_tools.parseCSV(fileOrHandle)
        for rec in recs:
            newType = self.typesMap[recType](rec)
            typeName = newType.Name
            if typeName in self.types:
                continue
            
            self.addType(newType)

    def loadShdNetworkTypeManagers(self, userInput, unifiedInput):
        typesFiles = [(userInput['peoplefile'],      'people'),
                      (unifiedInput.peopleFile,      'people'),
                      (userInput['packagefile'],     'packaging'),
                      (unifiedInput.packageFile,     'packaging'),
                      (userInput['truckfile'],       'trucks'),
                      (unifiedInput.truckFile,       'trucks'),
                      (userInput['vaccinefile'],     'vaccines'),
                      (unifiedInput.vaccineFile,     'vaccines'),
                      (userInput['icefile'],         'ice'),
                      (unifiedInput.iceFile,         'ice'),
                      (userInput['fridgefile'],      'fridges'),
                      (unifiedInput.fridgeFile,      'fridges')]

        for (f,t) in typesFiles:
            if f is None:
                continue
            with util.logContext("loading types from %s for shadow network"%f):
                self.importRecordsFromFile(f,t)


def _initShdSummary(instance, args, kwargs):
    """
    Use this for the init function of the net summary classes
    """
    return _initBasic(instance, args, kwargs, 0)

class ShdTypeSummary(Base):
    __tablename__ = 'typeSummary'

    summaryId = Column(Integer, primary_key=True)
    typeClass = Column(String(30))
    summaryType = 'undefinedType'
    __mapper_args__ = {'polymorphic_identity': summaryType}
    attrs = [('resultsId',    DataType(INTEGER, foreignKey='results.resultsId'),
              'noInputRec', True),
             ('Name',         STRING),
             ('Type',         STRING)]

    __mapper_args__ = {
        'polymorphic_identity':'typeSummary',
        'polymorphic_on':typeClass
        }



    def __init__(self, name, type_):
        raiseRuntimeError("Can't create base class of summary type")
        

    @staticmethod
    def initSummaryFromRec(rec):
        if 'Name' not in rec:
            raiseRuntimeError('No "Name" (type name) in summary record to be converted')
        if 'Type' not in rec:
            raiseRuntimeError('No "Type" (class type) in summary record to be converted')
        t = rec['Type']
        if t not in ShdTypeSummary.typesMap:
            logWarning("summary record type not in ShdTypeSummary.typesMap")
            return ShdBasicSummary(rec)

        return ShdTypeSummary.typesMap[t](rec)

    def __iadd__(self,summary_):
        
        if summary_.typeClass != self.typeClass:
            raiseRuntimeError("no, no, no")
        
        for attr in self.__dict__.keys():
            if attr[-2:] != "Id":
                if isinstance(getattr(self,attr),float) or isinstance(getattr(self,attr),int):
                    value = getattr(self,attr) + getattr(summary_,attr)
                    setattr(self,attr,value)               
        
        return self

    def __idiv__(self,factor_):
        facFloat = None
        try:
            facFloat = float(factor_)
        except:
            raiseRuntimeError("Factor must be able to be cast as a float when idiv RouteRpt")
        
        for attr in self.__dict__.keys():
            if attr[-2:] != "Id":
                if isinstance(getattr(self,attr),float) or isinstance(getattr(self,attr),int):
                    value = getattr(self,attr)/facFloat
                    setattr(self,attr,value)
        
        return self
        
    def resetToZero(self):
        for attr in self.__dict__.keys():
            if attr[-2:] != "Id":
                if isinstance(getattr(self,attr),float) or isinstance(getattr(self,attr),int):
                    #value = getattr(self,attr) + getattr(summary_,attr)
                    setattr(self,attr,0.0) 
        return self
    
    def createRecord(self):
        newRec = {}
        _copyAttrsToRec(newRec,self)
        return newRec
    
_makeColumns(ShdTypeSummary)

class ShdTruckSummary(ShdTypeSummary):
    __tablename__ = "truckSummary"
    summaryType = 'trucks'
    __mapper_args__ = {'polymorphic_identity': summaryType}

    truckSummaryId = Column(Integer, ForeignKey('typeSummary.summaryId'), primary_key=True)
    
    attrs = [('Name',        DataType(STRING, dbType=None)),
             ('Type',        DataType(STRING, dbType=None)),
             ('TotalTrips',  FLOAT_ZERO),
             ('TotalKm',     FLOAT_ZERO),
             ('TotalTravelDays', FLOAT_ZERO)]
    
    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

_makeColumns(ShdTruckSummary)


class ShdBasicSummary(ShdTypeSummary):
    __tablename__ = "basicSummary"
    summaryType = 'basic'
    __mapper_args__ = {'polymorphic_identity': summaryType}

    basicSummaryId = Column(Integer, ForeignKey('typeSummary.summaryId'), primary_key=True)

    # apparently there's nothing in this summary dict!
    attrs = [('Name',        DataType(STRING, dbType=None)),
             ('Type',        DataType(STRING, dbType=None))]
    
    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

_makeColumns(ShdBasicSummary)


class ShdIceSummary(ShdTypeSummary):
    __tablename__ = "iceSummary"
    summaryType = 'ice'
    __mapper_args__ = {'polymorphic_identity': summaryType}

    iceSummaryId = Column(Integer, ForeignKey('typeSummary.summaryId'), primary_key=True)

    attrs = [('Name',        DataType(STRING, dbType=None)),
             ('Type',        DataType(STRING, dbType=None)),
             ('TotalTrips',  INTEGER),
             ('TotalKm',     FLOAT),
             ('TotalTravelDays', FLOAT),
             ('NBroken',     INTEGER),
             ('NCreated',    INTEGER),
             ('NBrokenAbsolute', INTEGER),
             ('NCreatedAbsolute', INTEGER)]
    
    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

_makeColumns(ShdIceSummary)


class ShdFridgeSummary(ShdTypeSummary):
    __tablename__ = "fridgeSummary"
    summaryType = 'fridges'
    __mapper_args__ = {'polymorphic_identity': summaryType}

    fridgeSummaryId = Column(Integer, ForeignKey('typeSummary.summaryId'), primary_key=True)
    
    attrs = [('Name',             DataType(STRING, dbType=None)),
             ('Type',             DataType(STRING, dbType=None)),
             ('NCreated',         INTEGER),
             ('NCreatedAbsolute', INTEGER),
             ('ShipTimeDays',     FLOAT_ZERO),     # here and below is shippable fridge only
             ('ShipInstanceTimeDays', FLOAT_ZERO),
             ('ShipKm',           FLOAT_ZERO),
             ('ShipInstanceKm',   FLOAT_ZERO),
             ('NBroken',          INTEGER_ZERO),
             ('NBrokenAbsolute',  INTEGER_ZERO)]

    
    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)

_makeColumns(ShdFridgeSummary)

class ShdVaccineSummary(ShdTypeSummary):
    __tablename__ = "vaccineSummary"
    summaryType = 'vaccines'
    __mapper_args__ = {'polymorphic_identity': summaryType}

    vaccineSummaryId = Column(Integer, ForeignKey('typeSummary.summaryId'), primary_key=True)
    attrs = [('Name',         DataType(STRING, dbType=None)),
             ('Type',         DataType(STRING, dbType=None)),
             ('DisplayName',  STRING),
             ('DosesPerVial', INTEGER),
             ('StorageHistoryVialDays', FLOAT_ZERO),      # these don't always exist
             ('roomtemperatureStorageFrac', FLOAT_ZERO),
             ('coolerStorageFrac', FLOAT_ZERO),
             ('freezerStorageFrac', FLOAT_ZERO),
             ('ShipTimeDays', FLOAT),
             ('ShipVialDays', FLOAT),
             ('ShipKm',       FLOAT),
             ('ShipVialKm',   FLOAT),
             ('Applied',      INTEGER),
             ('Treated',      INTEGER),
             ('SupplyRatio',  FLOAT),
             ('OpenVialWasteFrac', FLOAT),
             ('VialsUsed',    INTEGER),
             ('VialsExpired', INTEGER),
             ('VialsBroken',  INTEGER),
             ('VialsCreated', INTEGER),
             ('VialsUsedAbsolute', INTEGER),
             ('VialsExpiredAbsolute', INTEGER),
             ('VialsBrokenAbsolute', INTEGER),
             ('VialsCreatedAbsolute', INTEGER)]

    def __init__(self, *args, **kwargs):
        _initShdType(self, args, kwargs)
    
_makeColumns(ShdVaccineSummary)

ShdTypeSummary.typesMap = {'vaccinetype':ShdVaccineSummary,
                           'trucktypeskeleton':ShdTruckSummary,
                           'trucktype':ShdTruckSummary,
                           'fridgetype':ShdFridgeSummary,
                           'shippablefridgetype':ShdFridgeSummary,
                           'peopletype':ShdBasicSummary,
                           'packagetype':ShdBasicSummary,
                           'storagetype':ShdBasicSummary,
                           'icetype':ShdIceSummary}

class DemandEnums:
    # enumerations for demand and calendarType
    TYPE_UNIFIED = 'U'      # single, unified demand/calendar
    TYPE_CONSUMPTION = 'C'  # consumption demand/calendar
    TYPE_SHIPPING = 'S'     # shipping demand/calendar
    
    eStr = {'U': 'unified',
            'C': 'consumption',
            'S': 'shipping'}

class ShdCalendarEntry(Base):
    __tablename__ = 'calendarEntries'
    calendarEntryId = Column(Integer, primary_key=True)
    
    attrs = [('modelId',        DataType(INTEGER, foreignKey='models.modelId'), 'noInputRec', True),
             ('calendarType',   CHAR),
             ('startDate',      FLOAT),
             ('typeId',         DataType(INTEGER, foreignKey='types.typeId')),
             ('amount',         FLOAT),
             ('notes',          NOTES_STRING)]
    
    pType = relationship('ShdType',
                         primaryjoin="and_(ShdCalendarEntry.modelId == ShdType.modelId, "
                                          "ShdCalendarEntry.typeId == ShdType.typeId)",
                         uselist=False)


    def __init__(self, net, calendarType, startDate, pType, amount, notes):
        if pType not in net.types:
            raiseRuntimeError("Invalid pType %s in calendar entry init"%pType)
        self.calendarType = calendarType
        self.startDate = startDate
        self.pType = net.types[pType]
        #self.typeId = net.types[pType].typeId
        self.amount = amount
        self.notes = notes
        
    
    @staticmethod
    def calendarEntriesFromRecs(net, calendarType, recs):
        recs = util.listify(recs)
        entries = []

        for rec in recs:
            if 'StartDate' not in rec:
                raiseRuntimeError("no 'StartDate' in calendar record")
            startDate = rec['StartDate']
            notes = None
            if 'notes' in rec:
                notes = rec['notes']
            
            for (pType, amount) in rec.items():
                if pType in ('StartDate', 'Notes'):
                    continue
                
                entries.append(ShdCalendarEntry(net, calendarType, startDate, pType, amount, notes))
    
        return entries
    
    @staticmethod
    def createRecords(entries):
        dictOfRecs = {}
        keys = ['StartDate', 'Notes']

        for entry in entries:
            if entry.startDate not in dictOfRecs:
                rec = CSVDict()
                dictOfRecs[entry.startDate] = rec
                rec['StartDate'] = entry.startDate
            else:
                rec = dictOfRecs[entry.startDate]

            if entry.notes is not None:
                rec['Notes'] = entry.notes  # do we check if some of the notes might be different?

            if entry.pType.Name not in keys:
                keys.append(entry.pType.Name)
            rec[entry.pType.Name] = entry.amount


        return keys, dictOfRecs.values()


_makeColumns(ShdCalendarEntry)


class ShdParameter(Base):
    """
    This holds a single element of the input KVP file
    """

    __tablename__ = 'parms'
    
    parmId = Column(Integer, primary_key=True)
    attrs = [('modelId',    DataType(INTEGER, foreignKey='models.modelId'), 'noInputRec', True),
             ('resultsGroupId',DataType(INTEGER, foreignKey='resultsGroup.resultsGroupId'),'noInputRec',True),
             ('key',        STRING),
             ('value',      STRING)]

    def __init__(self, key, value):
        self.key = key
        self.value = value

    @classmethod
    def fromStr(cls, s):
        s = s.strip()
        if s.startswith('#'):
            return None
        (key,sep,val) = s.partition('=')
        if key.strip() is '' and sep is '':
            return None
        if sep != '=':
            raiseRuntimeError("invalid line in kvp parameter file (no '=')")
        return ShdParameter(key.strip(), val.strip())

    def toStr(self):
        return "%s = %s"%(self.key, self.value)

    def parse(self):
        defTokenizer = input.InputDefault()
        return defTokenizer.processKeywordValue(self.key, self.value)
    
_makeColumns(ShdParameter)


class ShdDemand(Base):
    # need to build relationship between vaccineStr and peopleStr with their associated types.
    __tablename__ = "demand"
    demandId = Column(Integer, primary_key=True)

    attrs = [('modelId',       DataType(INTEGER, foreignKey='models.modelId'), 'noInputRec', True),
             ('demandType',    CHAR),
             ('vaccineStr',    STRING),
             ('peopleStr',     STRING),
             ('count',         INTEGER),
             ('Notes',         NOTES_STRING)]

    def __init__(self, *args, **kwargs):
        _initBasic(self, args, kwargs)
        
    @classmethod
    def fromRec(cls, rec, demandType = DemandEnums.TYPE_UNIFIED):
        "Return a list of ShdDemand() instances for a given record"
        vType = Notes = None
        try:
            vType = rec['VaccineType']  # vType needs to succeed but Notes is optional
            Notes = rec['Notes']        # thus order of this is important
        except:
            # let the later validations throw this out
            pass

        ret = []
        for key,val in rec.items():
            if key in ('VaccineType', 'Notes'):
                continue
            if val!=0:
                ret.append(ShdDemand(demandType, vType, key, val, Notes))

        return ret
        

    @classmethod
    def toRecs(cls, demands):
        recs = CSVDict()
        vacSet = set()
        pplSet = set()
        for demand in demands:
            vacSet.add(demand.vaccineStr)
            pplSet.add(demand.peopleStr)
            if demand.vaccineStr not in recs:
                recs[demand.vaccineStr] = {'VaccineType':demand.vaccineStr,
                                           'Notes':demand.Notes}
            recs[demand.vaccineStr][demand.peopleStr] = demand.count
        
        # Fill entry values with explicit zeros so generated tables have no blanks
        for v in vacSet:
            for p in pplSet:
                if p not in recs[v]: recs[v][p] = 0
        
        return recs.values()[:] #defense against python 3?

    @classmethod
    def toKeys(cls, demands):
        keys = ['VaccineType', 'Notes']
        for demand in demands:
            if demand.peopleStr not in keys:
                keys.append(demand.peopleStr)
        return keys

_makeColumns(ShdDemand)


class ShdNetwork(Base):
    """
    This is the class that holds everything in one place.  Its primary purpose is to have
    a dictionary of stores with routes linking them together in a manner that can easily be
    read and manipulated.

    It has the following attributes:
        stores:  Dictionary of ShdStore's keyed off of their idcode's.
        routes:  Dictionary of ShdRoute's keyed off of their RouteName's.
        types:   Dictionary of ShdType's keyed off 'Name'.
        ice, packaging, people, fridges, trucks, vaccines:
                 Dictionaries of these specific subclasses of types, keyed off 'Name'.
        parms:   list of parameters defining a hermes run
        demands: list of people/vaccine demands.

        fromDb:  True or False depending on whether this network was instantiated from a Database.

    methods:
        rootStores():   list of stores with no supplier
        trunkStore():   Assumes the lowest numbered rootStore is _the_ rootstore.
                        Follows client links until it finds the first store with 
                        more than one (branching) clients.
        addStore():     Add a store to the network (this may either be a ShdStore or a rec)
        removeStore():  Remove a store from the network.
        addRoute():     Add a route to the network.
        removeRoute():  Remove a route from the network.
        createStoreRecs():
                        create a list of records for all of the stores in the network.
        createRouteRecs():
                        create a list of records for all of the routes in the network.
        attachParms():  
        addDemands():
        getDemandRecs(): 
        getDemandTypes():
        getParameterValue(tok): 
                        return the value of the the parameter of the given name, including the
                        default if there is no model-specific value.  The returned value is of
                        the type specified for that name in the parameter definition file.
    """

    __tablename__ = 'models'
    __table_args__ = {'mysql_engine':'InnoDB'}
    modelId = Column(Integer, primary_key=True)
    note = Column(String(4096))
    attrs = [('name',    STRING)]

    factories = relationship('ShdFactory',
                            backref='model',
                            cascade='all, delete, delete-orphan',
                            collection_class=attribute_mapped_collection('idcode'))
    
    stores = relationship('ShdStore', 
                          backref='model', 
                          cascade="all, delete, delete-orphan",
                          collection_class=attribute_mapped_collection('idcode'))
    
    routes = relationship('ShdRoute', 
                          backref='model', 
                          cascade="all, delete, delete-orphan",
                          collection_class=attribute_mapped_collection('RouteName'))

    types = relationship('ShdType',
                         cascade="all, delete, delete-orphan",
                         collection_class=attribute_mapped_collection('Name'))

    # a segregated version of the types is defined just below the class definition
    # since it needed to reference this class to do so.

    parms = relationship('ShdParameter',
                         cascade="all, delete, delete-orphan",
                         primaryjoin = "and_(ShdNetwork.modelId==ShdParameter.modelId,ShdParameter.resultsGroupId == None)",
                         collection_class=attribute_mapped_collection('key'),
                         foreign_keys="[ShdParameter.modelId, ShdParameter.resultsGroupId]")

    initialOVW = relationship('ShdInitialOVW',
                              backref='model',
                              cascade="all, delete, delete-orphan")
    
    factoryWastage = relationship('ShdFactoryWastage',
                              backref='model',
                              cascade="all, delete, delete-orphan")

    unifiedDemands = relationship('ShdDemand',
                                  cascade="all, delete, delete-orphan",
                                  primaryjoin="and_(ShdNetwork.modelId=="
                                                       "ShdDemand.modelId, "
                                                   "ShdDemand.demandType=="
                                                        "'%s')"%DemandEnums.TYPE_UNIFIED,
                                  foreign_keys="[ShdDemand.modelId, ShdDemand.demandType]")

    consumptionDemands = relationship('ShdDemand',
                                  cascade="all, delete, delete-orphan",
                                  primaryjoin="and_(ShdNetwork.modelId=="
                                                       "ShdDemand.modelId, "
                                                   "ShdDemand.demandType=="
                                                        "'%s')"%DemandEnums.TYPE_CONSUMPTION,
                                  foreign_keys="[ShdDemand.modelId, ShdDemand.demandType]")

    shippingDemands = relationship('ShdDemand',
                                  cascade="all, delete, delete-orphan",
                                  primaryjoin="and_(ShdNetwork.modelId=="
                                                       "ShdDemand.modelId, "
                                                   "ShdDemand.demandType=="
                                                        "'%s')"%DemandEnums.TYPE_SHIPPING,
                                  foreign_keys="[ShdDemand.modelId, ShdDemand.demandType]")

    unifiedCalendar = relationship('ShdCalendarEntry',
                            cascade="all, delete, delete-orphan",
                            primaryjoin="and_(ShdNetwork.modelId=="
                                                "ShdCalendarEntry.modelId, "
                                             "ShdCalendarEntry.calendarType=="
                                                "'%s')"%DemandEnums.TYPE_UNIFIED,
                            foreign_keys="[ShdCalendarEntry.modelId, "
                                           "ShdCalendarEntry.calendarType]",
                            order_by="ShdCalendarEntry.startDate")
                            
    consumptionCalendar = relationship('ShdCalendarEntry',
                            cascade="all, delete, delete-orphan",
                            primaryjoin="and_(ShdNetwork.modelId=="
                                                "ShdCalendarEntry.modelId, "
                                             "ShdCalendarEntry.calendarType=="
                                                "'%s')"%DemandEnums.TYPE_CONSUMPTION,
                            foreign_keys="[ShdCalendarEntry.modelId, "
                                           "ShdCalendarEntry.calendarType]",
                            order_by="ShdCalendarEntry.startDate")
                            
    shippingCalendar = relationship('ShdCalendarEntry',
                            cascade="all, delete, delete-orphan",
                            primaryjoin="and_(ShdNetwork.modelId=="
                                                "ShdCalendarEntry.modelId, "
                                             "ShdCalendarEntry.calendarType=="
                                                "'%s')"%DemandEnums.TYPE_SHIPPING,
                            foreign_keys="[ShdCalendarEntry.modelId, "
                                           "ShdCalendarEntry.calendarType]",
                            order_by="ShdCalendarEntry.startDate")
                            
    priceTable = relationship('ShdCosts',
                              cascade="all, delete, delete-orphan")

    currencyTable = relationship('ShdCurrencyConversion',
                                 cascade="all, delete, delete-orphan")

    resultsGroups = relationship('HermesResultsGroup',
                                 backref = 'model',
                                 cascade = "all, delete, delete-orphan")

    populationDemand = relationship('ShdInventory',
                                    cascade="all, delete, delete-orphan",
                                    primaryjoin="and_(ShdNetwork.modelId=="
                                                "ShdInventory.modelId, "
                                                "ShdInventory.sourceType == '2')",
                                    foreign_keys="[ShdInventory.modelId, "
                                                    "ShdInventory.sourceType]"
                                    )


    def __init__(self, storeRecs, routeRecs, factoryRecs, shdTypes, name=None):
        """
        Instantiates a new hermes network based on the 'storeRecs' and 'routeRecs'.
        """
        if name is None: name = "unnamed model"

        self.fromDb = False
        
        self.types = shdTypes.types
        self.factories = {}
        self.routes = {}
        self.stores = {}
        self.parms = {}
        self.name = name
        self.demands = []
        self.resultsGroups = []

        # segregated copy of the types as well
        for key in ShdTypes.typesMap.keys():
            setattr(self, key, getattr(shdTypes, key))

        # parse factory recs
        with logContext("initial parsing of factory records"):
            if factoryRecs:
                for factoryRec in factoryRecs:
                    if 'idcode' not in factoryRec:
                        raiseRuntimeError("found factory record with no idcode")
                    with logContext("initial parsing of factory record %s"%factoryRec['idcode']):
                        self.addFactory(factoryRec)
                        
        # parse store recs
        with logContext("initial parsing of stores records"):
            if storeRecs:
                for storeRec in storeRecs:
                    if 'idcode' not in storeRec:
                        raiseRuntimeError("found stores record with no idcode")
                    with logContext("initial parsing of stores record %s"%storeRec['idcode']):
                        print "Adding " + storeRec['NAME']
                        self.addStore(storeRec)

        # parse route recs and integrate them into the store records
        with logContext("initial parsing of routes records"):
            # do initial casting so that we can presort the records
            if routeRecs:
                for attrs in ShdRoute.attrs + ShdStop.attrs:
                    a = _parseAttr(attrs)
                    if a['name'] in ('RouteName', 'RouteOrder', 'idcode'):
                        castColumn(routeRecs, a['name'], a['cast'])

                rrDict = {}
                for routeRec in routeRecs:
                    name = routeRec['RouteName']
                    if name not in rrDict:
                        rrDict[name] = []
                    rrDict[name].append(routeRec)

                for name,rrList in rrDict.items():
                    rrList.sort(key = lambda r: r['RouteOrder'])
                    self.addRoute(rrList)
   
    def getLevelList(self):
        countDict = {}
        for storeId,store in self.stores.items():
            if store.CATEGORY not in countDict.keys():
                countDict[store.CATEGORY] = 1
            else:
                countDict[store.CATEGORY] += 1        
        sortedcount = [x[0] for x in sorted(countDict.iteritems(),key=operator.itemgetter(1))]
        return sortedcount
        
    # the following group of functions are analogs to the db api
    def getStore(self, storeId):
        return self.stores[storeId]

    def getStoreByName(self, storeName):
        for s in self.stores.values():
            if s.NAME == storeName:
                return s
        raise KeyError()

    def getFactory(self, factoryId):
        return self.factories[factoryId]
    
    def getRoute(self, routeName):
        return self.routes[routeName]

    def getStop(self, routeName, stopNum):
        r = self.routes[routeName]
        for s in r.stops:
            if s.RouteOrder != stopNum:
                continue
            return s
        raise KeyError(stopNum)

    def addFactory(self, factory):
        """
        Add a 'ShdFactory' to the network.
        """
        if isinstance(factory,ShdFactory):
            pass
        elif isinstance(factory, dict):
            factory = ShdFactory(factory,self)
        else:
            raiseRuntimeError("unknown factory type in addFactory")
        
        self.factories[factory.idcode] = factory
        return factory
    
    def removeFactory(self, factory):
        '''
        remove a store from the network, 'factory can either be a 'ShdFactory or 
        an 'idcode'
        '''
        if isinstance(factory, ShdFactory):
            pass
        elif factory in self.factories.keys():
            factory = self.factories[factory]
        else:
            raiseRuntimeError("factory to be removed is unrecognized")
        
        idcode = factory.idcode
        
        del(self.factories[idcode])
        
    def addStore(self, store):
        """
        Add a 'ShdStore' to the network. 'store' can either be a fully formed 
	'ShdStore' or a dictionary of attributes.
        """
        if isinstance(store, ShdStore):
            pass
        elif isinstance(store, dict):
            store = ShdStore(store, self)
        else:
            raiseRuntimeError("unknown store type in addStore")
        
        self.stores[store.idcode] = store
        return store

    def removeStore(self, store):
        """
        remove a store from the network.  'store' can either be a 'ShdStore' or 
        an 'idcode'.

        It is an error to remove a store if there are routes in the network
        that reference it.
        """
        if isinstance(store, ShdStore):
            pass
        elif store in self.stores:
            store = self.stores[store]
        else:
            raiseRuntimeError("store to be removed is unrecognized")

        idcode = store.idcode
        
        if len(store.clients()) or len(store.suppliers()):
            raiseRuntimeError("can't remove store with routes linked to it!")

        if idcode not in self.stores:
            raiseRuntimeError("store to be removed not found")
        del(self.stores[idcode])


    def addRoute(self, recList, noStops = False):
        """
        create and add a route based on a recList.  If noStops is set to True then
        stops will not be created and no stores will be linked.
        """
        r = ShdRoute(recList, self.stores, noStops)
        self.routes[r.RouteName] = r
        return r

    def removeRoute(self, route, unlinked=False):
        """
        remove a route from the network.  'route' can either be a 'ShdRoute' or
        a 'RouteName'.  By default this will unlink the route for you (unless 
        'unlinked' is set to True).
        """
        if isinstance(route, ShdRoute):
            name = route.RouteName
        else:
            name = route
            route = self.routes[name]

        if not unlinked:
            route.unlinkRoute()
        
        del(self.routes[name])

    def createFactoryRecs(self):
        ''' 
        Create a set of factory records (and keys) that can be used to create a new factory file
        '''
        recs = []
        for factory in self.factories.values():
            recs.append(factory.createRecord())
        keys = set()
        for rec in recs:
            keys |= set(rec.keys())
        keys = list(keys)
        return keys,recs
    
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
        "Find the stores with no parents"
        rootStores = []
        for store in self.stores.values():
            routes = {} # dict of route names and whether this store is the supplier
            for stop in store.relatedStops:
                rName = stop.RouteName
                if stop.isSupplier:
                    routes[rName] = True
                else:
                    if rName not in routes:
                        routes[rName] = False

            isRoot = True
            for routeVal in routes.values():
                if routeVal is False:
                    isRoot = False
                    break
            if isRoot:
                rootStores.append(store)

        return rootStores


        # here's the old simpler but less optimized version
        rootStores = []
        for store in self.stores.values():
            if len(store.suppliers()) == 0:
                rootStores.append(store)

        return rootStores

    
    
    def addSortedClients(self,store):
        clientList = [store.idcode]
        tmpClientList = []
        if len(store.clients()) > 0:
            for client in store.clients():
                tmpClientList.append(client[0].idcode)
            tmpClientList = sorted(tmpClientList)
            for client in tmpClientList:
                clientList += self.addSortedClients(self.getStore(client))
        return clientList
    
    #def idSortByNetwork(self):
        ## start at the Root Stores
        
    def getWalkOfSupplierIds(self, idcode):
        ''' This member will walk up from an store through the network 
            and return a list of idcodes for all of the supply chain for
            the store
        '''
        supplierIds = []
        thisStore = self.stores[idcode]
        for supplier in thisStore.suppliers():
            supplierIds.append(supplier[0].idcode)
            supplierIds += self.getWalkOfSupplierIds(supplier[0].idcode)
        
        return supplierIds
    
    def getWalkOfClientIds(self, idcode):
        ''' This member will walk up from an store through the network 
            and return a list of idcodes for all of the client chain for
            the store
        '''
        clientIds = []
        thisStore = self.stores[idcode]
        for client in thisStore.clients():
            clientIds.append(client[0].idcode)
            clientIds += self.getWalkOfClientIds(client[0].idcode)
        
        return clientIds

### STB - Helper function here to creat a json, it was just easier    
    def getWalkOfClientsDictForJson(self,idcode):
        ''' This member will walk up from an store through the network 
            and return a dict for heirarchical reps for all of the client chain for
            the store
        '''
        thisStore = self.stores[idcode]
        #print type(thisStore.NAME)
        levels = self.getLevelList()
        thisLoopList = [x for x in thisStore.clients() if len(x[1].stops) > 2]
        thisClientList = [x for x in thisStore.clients() if (x[1].Type != "attached" and x not in thisLoopList)]
        if len(thisClientList) > 0:
            clientDict = {'name':thisStore.NAME,'level':levels.index(thisStore.CATEGORY),'idcode':thisStore.idcode,'children':[]}
            for client in thisClientList:
                if client[1].Type != "attached":
                    clientDict['children'].append(self.getWalkOfClientsDictForJson(client[0].idcode))
        else:
            clientDict = {'name':thisStore.NAME,'level':levels.index(thisStore.CATEGORY),'idcode':thisStore.idcode}
        ### Handle a Transport Loop
        if len(thisLoopList) > 0:
            if 'children' not in clientDict.keys():
                clientDict['children'] = []
            loopClientDict = {'name':'Transport Loop','level':9999,
                              'idcode':9999,
                              'children':[]}
            for lclient in thisLoopList:
                print lclient[0].NAME
                lClientList = [x for x in thisStore.clients() if (x[1].Type != "attached")]
                loopClientDict['children'].append(self.getWalkOfClientsDictForJson(lclient[0].idcode))
            clientDict['children'].append(loopClientDict)
            
        return clientDict
    
    def createRouteListOrderdByWalkOfClients(self, idcode):
        ''' This member will create a list of routes that are 
            are ordered by a list for all of the client chain
            for the store
        '''
        routeIds = []
        thisStore = self.stores[idcode]
        
        sortedClientRoutes = sorted([x.RouteName for x in thisStore.clientRoutes()])
        for clientRouteName in sortedClientRoutes:
            clientRoute = self.routes[clientRouteName]
            routeIds.append(clientRoute.RouteName)
            for stop in clientRoute.stops:
                if stop.store.idcode != thisStore.idcode:
                    routeIds += self.createRouteListOrderdByWalkOfClients(stop.store.idcode)
        #for client in thisStore.clients():
        #    routeIds += self.createRouteListOrderdByWalkOfClients(client[0].idcode)
        
        return routeIds
            
                
    def trunkStore(self):
        """
        Start with the lowest value root store.  Recursively move to this stores child store if 
        there is only one child store.  Return the final store reached.
        """
        rootStores = self.rootStores()
        if len(rootStores) == 0:
            raiseRuntimeError("no root stores in network")
        rootStores.sort(key=lambda s: s.idcode)
        trunk = rootStores[0]
        while (len(trunk.clients()) == 1):
            trunk = trunk.clients()[0][0]

        return trunk

#    def attachReport(self, reportRecs, reportIndex = 0):
#        #attachReport(self, reportRecs, reportIndex)
#        pass

    def addParm(self, parm):
        "Add a single ShdParameter entry"
        self.parms[parm.key] = parm

    def attachParms(self, kvpFile):
        """
        Convert a kvp file/string to ShdParameter entries and add them to the network.
        """
        with util.openFileOrHandle(kvpFile) as f:
            lines = f.readlines()
        for i,line in enumerate(lines,start=1):
            with logContext('parsing reading line %d of input kvp file'%i):
                parm = ShdParameter.fromStr(line)
                if parm is None:
                    continue
                self.addParm(parm)

    def getParameterValue(self,token):
        """
        Get the value of the specified parameter, using the default if no such parameter is 
        specified for the model.  The returned value is of the parameter's specific type,
        as specified in the parameters definition file.
        """
        if token in self.parms.keys():
            return self.parms[token].parse()
        else:
            defTokenizer = input.InputDefault()
            return defTokenizer.processKeywordValue(token,None)
        

    def addInitialOVWEntry(self, ovw):
        "Add a single ShdFactoryOVW entry"
        self.initialOVW.append(ovw)

    def attachInitialOVW(self, ovwRecs):
        "Create and add one or more ShdFactoryOVW entries from one or more recs"
        ovwRecs = util.listify(ovwRecs)
        for rec in ovwRecs:
            self.addInitialOVWEntry(ShdInitialOVW(rec))

    def getInitialOVWRecs(self):
        "convert the list of FactoryOVW entries to recs and return them"
        recs = []
        for ovwRec in self.initialOVW:
            recs.append(ovwRec.createRecord())
        keys = ['Name', 'OVW', 'Notes']
        return keys, recs
    
    def addFactoryWastageEntry(self, ovw):
        "Add a single ShdFactoryOVW entry"
        self.factoryWastage.append(ovw)

    def attachFactoryWastage(self, ovwRecs):
        "Create and add one or more ShdFactoryOVW entries from one or more recs"
        ovwRecs = util.listify(ovwRecs)
        for rec in ovwRecs:
            self.addFactoryWastageEntry(ShdFactoryWastage(rec))

    def getFactoryWastageRecs(self):
        "convert the list of FactoryOVW entries to recs and return them"
        recs = []
        for ovwRec in self.factoryWastage:
            recs.append(ovwRec.createRecord())
        keys = ['FactoryID','VaccineName','WastageFraction']
        return keys, recs

    def addDemand(self, demand):
        "add a single ShdDemand entry to the appropriate demand list"
        demandAttr = DemandEnums.eStr[demand.demandType] + 'Demands'
        getattr(self, demandAttr).append(demand)

    def addDemands(self, demandRecs, demandType = DemandEnums.TYPE_UNIFIED):
        """
        convert one or more demand recs to ShdDemand s and add them to the appropriate 
        demand list based on demandType (defaulting to unified demands)
        """
        demandRecs = util.listify(demandRecs)
        demandAttr = DemandEnums.eStr[demandType] + 'Demands'
        for rec in demandRecs:
            getattr(self, demandAttr).extend(ShdDemand.fromRec(rec, demandType))

    def addConsumptionDemands(self, demandRecs):
        "shortcut for addDemands(demandRecs, DemandEnums.TYPE_CONSUMPTION)"
        self.addDemands(demandRecs, DemandEnums.TYPE_CONSUMPTION)

    def addShippingDemands(self, demandRecs):
        "shortcut for addDemands(demandRecs, DemandEnums.TYPE_SHIPPING)"
        self.addDemands(demandRecs, DemandEnums.TYPE_SHIPPING)

    def getDemandRecs(self, demandType=DemandEnums.TYPE_UNIFIED):
        """
        convert one list of the demand entries (defaulting to unified)
        to demand recs.  returns keys,recs
        """
        demandAttr = DemandEnums.eStr[demandType] + 'Demands'
        recs = ShdDemand.toRecs(getattr(self, demandAttr))
        keys = ShdDemand.toKeys(getattr(self, demandAttr))
        #keys = set()
        #for rec in recs:
        #    keys |= set(rec.keys())
        #keys = list(keys)
        return keys,recs

    def getConsumptionDemandRecs(self):
        "shortcut to get the consumption demand recs"
        return self.getDemandRecs(DemandEnums.TYPE_CONSUMPTION)

    def getShippingDemandRecs(self):
        "shortcut to get the shipping demand recs"
        return self.getDemandRecs(DemandEnums.TYPE_SHIPPING)

    def getDemandTypes(self):
        return ShdDemand.toKeys(self.demands)

    def addCalendarEntry(self, calendarEntry):
        "add an individual calendar entry to the appropriate list of entries"
        calAttr = DemandEnums.eStr[calendarEntry.calendarType] + 'Calendar'
        getattr(self, calAttr).append(calendarEntry)
        

    def addCalendar(self, calendarRecs, calType=DemandEnums.TYPE_UNIFIED):
        """
        convert one or more calendar records to calendar entries and insert them
        into the requested calendar type (default unified)
        """
        calendarRecs = util.listify(calendarRecs)
        calAttr = DemandEnums.eStr[calType] + 'Calendar'
        getattr(self, calAttr).extend(ShdCalendarEntry.calendarEntriesFromRecs(self, 
                                                                               calType,
                                                                               calendarRecs))


    def addConsumptionCalendar(self, calendarRecs):
        "shortcut to add consumption calendar recs"
        self.addCalendar(calendarRecs, DemandEnums.TYPE_CONSUMPTION)

    def addShippingCalendar(self, calendarRecs):
        "shortcut to add shipping calendar recs"
        self.addCalendar(calendarRecs, DemandEnums.TYPE_SHIPPING)

    def getCalendarRecs(self, calType=DemandEnums.TYPE_UNIFIED):
        """
        convert the calendar entries of a specific type (default unified) to recs
        returns keys,recs
        """
        calAttr = DemandEnums.eStr[calType] + 'Calendar'
        return ShdCalendarEntry.createRecords(getattr(self, calAttr))
    
    def getConsumptionCalendarRecs(self):
        "shortcut to get consumption calendar recs"
        return self.getCalendarRecs(DemandEnums.TYPE_CONSUMPTION)
    
    def getShippingCalendarRecs(self):
        "shortcut to get shipping calendar recs"
        return self.getCalendarRecs(DemandEnums.TYPE_SHIPPING)

    def addPriceEntry(self, priceEntry):
        "add a single price table entry"
        self.priceTable.append(priceEntry)

    def addPriceTable(self, priceRecs):
        "add one or more pricetable entries from recs"
        priceRecs = util.listify(priceRecs)
        for rec in priceRecs:
            self.addPriceEntry(ShdCosts(rec))

    def getPriceTableRecs(self):
        "get the price table entries as recs"
        priceRecs = []
        keys = _getAttrsRecNamesList(ShdCosts)
        for rec in self.priceTable:
            priceRecs.append(rec.createRecord())
        return (keys, priceRecs)

    def addCurrencyEntry(self, currencyEntry):
        "add a single currency conversion entry"
        self.currencyTable.append(currencyEntry)

    def addCurrencyTable(self, currencyRecs):
        "convert one or more currency recs into currency table entries and add them"
        currencyRecs = util.listify(currencyRecs)
        for rec in currencyRecs:
            self.currencyTable.extend(ShdCurrencyConversion.CurrencyConversionFromRec(rec))

    def getCurrencyTableRecs(self):
        "convert the currency conversion entries into recs.  returns keys,recs"
        return ShdCurrencyConversion.createRecords(self.currencyTable)

    def getResultsGroupNames(self):
        returnList = [g.name for g in self.resultsGroups]
        if len(returnList) == 0:
            return None
        return returnList
    
    def getResultsGroupByName(self, name):
        for resultG in self.resultsGroups:
            if name == resultG.name:
                return resultG
            
        return None
    
    def getResultsGroupById(self,Id):
        #print 'starting; modelId=%s, id= %s'%(self.modelId,Id)
        for resultG in self.resultsGroups:
            #print 'ping %s'%resultG.resultsGroupId
            if resultG.resultsGroupId == Id:
                return resultG
        return None
    
    def getResultById(self,Id):
        for resultG in self.resultsGroups:
            for result in resultG.results:
                if result.resultsId == Id:
                    return result
                
        return None
            
    def writeCSVRepresentation(self):
        """
        This routine recreates the files which presumably were read by loadShdNetwork to create
        this network in the first place.  It uses util.openOutputFile, and so will respect the
        os.environ['HERMES_DATA_OUTPUT protocol'] for creating files within zip files.
        """

        fakeParms = {}
        storesKeyOrder = ["CATEGORY","FUNCTION","NAME","idcode","Device Utilization Rate",
                          "UseVialsLatency","UseVialsInterval","Latitude","Longitude"]
        storesKeyLast = ["Inventory","Storage","Notes"]
        routesKeyOrder = ["RouteName","idcode","LocName","CATEGORY","Type",
                          "RouteOrder","TransitHours","TruckType",
                          "ShipIntervalDays","ShipLatencyDays",
                          "PullOrderAmountDays","DistanceKM","Conditions","Notes"]
        
        
        filesToZip = {'fridgefile':(self.fridges,),
                      'icefile':(self.ice,),
                      'packagefile':(self.packaging,),
                      'peoplefile':(self.people,),
                      'truckfile':(self.trucks,),
                      'vaccinefile':(self.vaccines,),
                      'initialovw':(self.initialOVW, self.getInitialOVWRecs),
                      'factorywastagefile':(self.factoryWastage,self.getFactoryWastageRecs()),
                      'calendarfile':(self.unifiedCalendar, self.getCalendarRecs),
                      'catchupfile':None,
                      'consumptioncalendarfile':(self.consumptionCalendar, self.getConsumptionCalendarRecs),
                      'consumptiondemandfile':(self.consumptionDemands, self.getConsumptionDemandRecs),
                      'currencyconversionfile':(self.currencyTable, self.getCurrencyTableRecs),
                      'gapstorefile':None,
                      'pricetable':(self.priceTable, self.getPriceTableRecs),
                      'shippingcalendarfile':(self.shippingCalendar, self.getShippingCalendarRecs),
                      'shippingdemandfile':(self.shippingDemands, self.getShippingDemandRecs),
                      'customoutput':({},), # does this matter for UI work?  I guess it probably should exist
                      'storesoverlayfiles':({},), # not a property of the model
                      'routesfile':(self.routes, self.createRouteRecs),
                      'storesfile':(self.stores, self.createStoreRecs),
                      'factoryfile':(self.factories, self.createFactoryRecs),
                      'demandfile':(self.unifiedDemands, self.getDemandRecs)
                      }

        uI = input.UnifiedInput()
        filesToFake = {'fridgefile':(uI.fridgeFile,ShdStorageType),
                       'truckfile':(uI.truckFile,ShdTruckType),
                       'peoplefile':(uI.peopleFile,ShdPeopleType),
                       'icefile':(uI.iceFile,ShdIceType),
                       'packagefile':(uI.packageFile,ShdPackageType),
                       'vaccinefile':(uI.vaccineFile,ShdVaccineType)
                       }
        
        # A quick reality check
        missingKeys = []
        for k in HermesInput.zipSubFileKeys:
            if k not in filesToZip: missingKeys.append(k)
        if missingKeys != []:
            raise RuntimeError("Internal error: shadow_network.writeCSVRepresentation is missing the following keys: %s"%missingKeys)

        # go through the files to be
        for pName,val in filesToZip.items():
#            if val is None:
#                print "pName: %s, val: None"%pName
#            elif len(val)>1:
#                print "pName: %s, val: (%s , %s )"%(pName,type(val[0]),type(val[1]))
#            else:
#                print "pName: %s, val: %s"%(pName, type(val[0]))
            if val is None:
                logWarning('No file to play the role of %s in exported %s'%(pName,self.name))
                continue
            data = val[0]
            convMethod = None
            if len(val) > 1:
                convMethod = val[1]
            
            if pName in filesToFake:
                unifiedFileName,cls = filesToFake[pName]
                keys = _getAttrsRecNamesList(cls)
#                print '%s: %s %s'%(pName,unifiedFileName,keys)
                with util.openOutputFile(unifiedFileName) as f:
                    csv_tools.writeCSV(f, keys, [], quoteStrings=True, emptyVal='')

            # do nothing further if there's no records to write
            if len(data) == 0:
#                print "length of first element is 0; continuing"
                continue
            # set up the filename in parms
            if pName in self.parms:
                fname = self.parms[pName].value
                fname = fname.strip("'")
            else:
                fname = "%s_%s.csv"%(self.name,pName)
                fakeParms[pName] = fname
                
                
            # convert the data to something that csv_utils likes
            if convMethod:
                keys, recs = convMethod()
            else:
                recs = [s.createRecord() for s in data.values()]

                kSet = set()
                for r in recs: kSet.update(r.keys())
                keys = list(kSet)

#            print 'keys: %s'%keys
#            print "%d recs"%len(recs)
            
            # Sort Stores File Keys 
            if pName == "storesfile":
                oldkeys = [x for x in keys]
                notInSort = [x for x in oldkeys if x not in storesKeyOrder and x not in storesKeyLast]
                keys = [x for x in storesKeyOrder if x in oldkeys]
                keys += notInSort
                keys += [x for x in storesKeyLast if x in oldkeys]
            
            ## Get newtork sort
                sortedList = self.addSortedClients(self.rootStores()[0])
                newRecList = []
                for ID in sortedList:
                    for rec in recs:
                        if rec['idcode'] == ID:
                            newRecList.append(rec)
            elif pName == "routesfile":
                oldkeys = [x for x in keys]
                notInSort = [x for x in oldkeys if x not in routesKeyOrder]
                keys = [x for x in routesKeyOrder if x in oldkeys]
                keys += notInSort
                 
                ### Get the network sort
                sortedList = self.createRouteListOrderdByWalkOfClients(self.rootStores()[0].idcode)
                newRecList = []
                for ID in sortedList:
                    for rec in recs:
                        if rec['RouteName'] == ID:
                            newRecList.append(rec)
            else:
                newRecList = recs
            
            with util.openOutputFile(fname) as f:
                csv_tools.writeCSV(f, keys, newRecList, quoteStrings=True, emptyVal='')

        kvpFileName = '%s.kvp'%self.name
        with util.openOutputFile(kvpFileName) as f:
            for k,v in self.parms.items():
                if k in filesToZip and filesToZip[k] is None:
                    logWarning('%s export blocked pending database support for that functionality'%k)
                else:
                    f.write("%s = %s\n"%(k,v.value))
            for k,v in fakeParms.items():
                f.write("%s = '%s'\n"%(k,v))

        fakeCmdLine = ['main.py',kvpFileName]
        with util.openOutputFile('argv.pkl') as f:
            pickle.dump(fakeCmdLine, f)


    def copy(self, name=None):
        """
        copy a model so it can be inserted new into the DB.

        This only copies the model and the inputs.  It does not copy the results groups
        """
        if name is None:
            name = self.name + "_copy"

        typesCopy = ShdTypes()
        for t in self.types.values():
            c = t.copy()
            typesCopy.addType(t.copy())

        storeKeys, storeRecs = self.createStoreRecs()
        routeKeys, routeRecs = self.createRouteRecs()
        factoryKeys, factoryRecs = self.createFactoryRecs()

        newNet = ShdNetwork(storeRecs, routeRecs, factoryRecs, typesCopy, name)

        # parms are simple, just copy them simply
        for parm in self.parms.values():
            newNet.addParm(ShdParameter(parm.key, parm.value))

        #factory ovw is almost as simple
        for ovw in self.initialOVW:
            newNet.addInitialOVWEntry(ShdInitialOVW(ovw.Name, ovw.OVW, ovw.Notes))

        for wastage in self.factoryWastage:
            newNet.addFactoryWastageEntry(ShdFactoryWastage(wastage.FactoryID,wastage.VaccineName,
                                                            wastage.WastageFraction))
            
        # demands are much simpler than their recs... just copy them but use our export functions.
        for demandType in DemandEnums.eStr.values():
            demandList = getattr(self, demandType + 'Demands')
            for demand in demandList:
                d = CSVDict()
                _copyAttrsToRec(d, demand)
                newDemand = ShdDemand(d)
                newNet.addDemand(newDemand)

        # same with calendars
        for demandType in DemandEnums.eStr.values():
            calList = getattr(self, demandType + 'Calendar')
            for cal in calList:
                d = CSVDict()
                _copyAttrsToRec(d, cal)
                newCal = ShdCalendarEntry(d)
                newNet.addCalendarEntry(newCal)
                
        # ShdCosts is simple but has lots of fields...
        # lets just export/import
        for price in self.priceTable:
            newNet.addPriceTable(price.createRecord())

        # currency conversion DB entries are also simpler than their recs
        # but there are more fields in this one.  At least they're all simple.
        for cur in self.currencyTable:
            d = CSVDict()
            _copyAttrsToRec(d, cur)
            newCur = ShdCurrencyConversion(d)
            newNet.addCurrencyEntry(newCur)


        # things left to copy:
        return newNet







# bring in a segregated version of the types
# this is import time code, don't indent
for (typeName,typeClass) in ShdTypes.typesMap.items():
    setattr(ShdNetwork, typeName,
            relationship(typeClass,
                         cascade="all, delete, delete-orphan",
                         collection_class=attribute_mapped_collection('Name')))


_makeColumns(ShdNetwork)

def networkLoadListener(net, context):
    net.fromDb = True

saEvent.listen(ShdNetwork, 'load', networkLoadListener)






def loadShdTypes(userInput, unifiedInput):
    shdTypes = ShdTypes()
    shdTypes.loadShdNetworkTypeManagers(userInput, unifiedInput)
    return shdTypes

def loadShdNetwork(userInput, shdTypes, name=None):
    """
    loads the stores and routes files and populates and then returns a ShdNetwork class Instance.
    """

    (storeKeys, storeRecList, routeKeys, routeRecList, factoryKeys, factoryRecList) = \
        load_networkrecords.readNetworkRecords(userInput)
        
    net = ShdNetwork(storeRecList, routeRecList, factoryRecList, shdTypes, name=name)

    if userInput['demandfile'] is not None:
        (keys, demandRecs) = csv_tools.parseCSV(userInput['demandfile'])
        net.addDemands(demandRecs, DemandEnums.TYPE_UNIFIED)
                                                
    if userInput['consumptiondemandfile'] is not None:
        (keys, demandRecs) = csv_tools.parseCSV(userInput['consumptiondemandfile'])
        net.addDemands(demandRecs, DemandEnums.TYPE_CONSUMPTION)
                                                
    if userInput['shippingdemandfile'] is not None:
        (keys, demandRecs) = csv_tools.parseCSV(userInput['shippingdemandfile'])
        net.addDemands(demandRecs, DemandEnums.TYPE_SHIPPING)
                                                
    if userInput['initialovw'] is not None:
        (keys, recs) = csv_tools.parseCSV(userInput['initialovw'])
        net.attachInitialOVW(recs)
        
    if userInput['factorywastagefile'] is not None:
        (keys, recs) = csv_tools.parseCSV(userInput['factorywastagefile'])
        net.attachFactoryWastage(recs)

    if userInput['calendarfile'] is not None:
        (keys, recs) = csv_tools.parseCSV(userInput['calendarfile'])
        net.addCalendar(recs)

    if userInput['consumptioncalendarfile'] is not None:
        (keys, recs) = csv_tools.parseCSV(userInput['consumptioncalendarfile'])
        net.addConsumptionCalendar(recs)

    if userInput['shippingcalendarfile'] is not None:
        (keys, recs) = csv_tools.parseCSV(userInput['shippingcalendarfile'])
        net.addShippingCalendar(recs)

    if userInput['pricetable'] is not None:
        (keys, recs) = csv_tools.parseCSV(userInput['pricetable'])
        net.addPriceTable(recs)

    if userInput['currencyconversionfile'] is not None:
        (keys, recs) = csv_tools.parseCSV(userInput['currencyconversionfile'])
        net.addCurrencyTable(recs)



    return net
