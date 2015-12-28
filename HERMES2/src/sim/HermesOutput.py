_hermes_svn_id_="$Id$"

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

import copy
from csv_tools import *
from util import openDataFullPath,listify,AccumVal, openOutputFile
import util
import types
import pickle
import collections

class HermesOutput():
    """
    This is a set of deep copies of various hermes stats that can be used and kept
    without affecting any of the rest of hermes.
    """

    def __init__(self, sim):
        self.runNumber = sim.runNumber
        self.customOutputs = sim.userInput['customoutput']
#        self.userInput = copy.deepcopy(sim.userInput)

        self.vaxSummaryRecs = \
            [vax.getSummaryDict() for vax in sim.vaccines.getActiveTypes()]
        self.peopleSummaryRecs = \
            [people.getSummaryDict() for people in sim.people.getActiveTypes()]
        self.truckSummaryRecs = \
            [truck.getSummaryDict() for truck in sim.trucks.getActiveTypes()]
        self.fridgeSummaryRecs = \
            [fridge.getSummaryDict() for fridge in sim.fridges.getActiveTypes()]
        self.storageSummaryRecs = \
            [storage.getSummaryDict() for storage in sim.storage.getActiveTypes()]

        self.notes = copy.deepcopy(sim.notes)

        self.stores = {}
        self.routes = {}
        self.other = []
        for note in self.notes.getnotes():
            d = note.getDict()
            if 'code' in d:
                code = d['code']
                self.stores[code] = {'note':note,
                                     'code':code,
                                     'clientRoutes':[],
                                     'suppliers':[]}

            elif 'RouteName' in d:
                route = d['RouteName']
                self.routes[route] = {'note':note}
            else:
                self.other.append(note)
            
        for code,wh in sim.storeDict.items():
            if code not in self.stores:
                #nh = self.notes.createNoteHolder()
                self.stores[code] = {'note':None,  # nh,
                                     'code':code,
                                     'clientRoutes':[],
                                     'suppliers':[]}

        for code,wh in sim.storeDict.items():
            if wh is None:
                continue
            oSt = self.stores[code]  #oSt is output store
            for cr in wh.getClientRoutes():
                if cr['name'] in self.routes:
                    oRt = self.routes[cr['name']]
                    oRt['supplier'] = oSt
                else:
                    oRt = None
                routeClients = []
                for cId in cr['clientIds']:
                    if cId not in self.stores:
                        raise RuntimeError('warehouse %s not in the stores list'%cId)
                    routeClients.append(self.stores[cId])
                    self.stores[cId]['suppliers'].append(oSt)
                tt = cr['truckType']
                if tt is None:
                    tt = "No Transport"
                else:
                    tt = tt.name
                oSt['clientRoutes'].append({'name':cr['name'],
                                            'clients':routeClients,
                                            'type':cr['type'],
                                            'truckType':tt})


        self.rootStores = []
        for id,st in self.stores.items():
            if 0 == len(st['suppliers']):
                self.rootStores.append(st)
        self._addLevels()
        self._sumVaxFields()
#        self.notes.writeNotesAsCSV("NewNotes.csv")

        # create a structure that can be better used for making custom output files
        self.recs = {'vax': self.vaxSummaryRecs,
                     'people': self.peopleSummaryRecs,
                     'truck': self.truckSummaryRecs,
                     'fridge': self.fridgeSummaryRecs,
                     'storage': self.storageSummaryRecs,
                     'stores': [],    # fill in stores and routes in just a minute...
                     'routes': [] }

        for store in self.stores.itervalues():
            if store['note'] is not None:
                self.recs['stores'].append(store['note'].getDict())
        for route in self.routes.itervalues():
            if route['note'] is not None:
                self.recs['routes'].append(route['note'].getDict())


        

    def _addLevels(self, store = None, level = 0, memo = None):
        if store is None:
            for st in self.rootStores:
                self._addLevels(st, 1, memo = {})
            return

        code = store['code']
        if code in memo:
            if memo[code] <= level:
                print "store: %s has previously been reached"%code
                return

        memo[store['code']] = level
        if store['note'] is not None:
            store['note'].addNote({'level':level})
        store['level'] = level
        for rt in store['clientRoutes']:
            for client in rt['clients']:
                self._addLevels(client, level+1, memo)

    #BUG: outputName should probably incorporate the value from the --out runtime flag
    def writeCustomCSV(self, formatFile, output_suffix = ""):
        # since this modifies notes, make a copy and then
        # use this instead! 
        # after the copy don't use "self" anymore and use "scp".
        scp = copy.deepcopy(self)

        with openDataFullPath(formatFile) as f:
            keys,lines = parseCSV(f)
        castColumn(lines, 'function', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'field', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'field2', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'name', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'val', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'hide', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        castColumn(lines, 'format', (castTypes.EMPTY_IS_NONE, castTypes.STRING))
        
        outputName = "custom_out" + output_suffix + ".csv"

        scp.rows = []
        scp.cell = [0,0]
        scp.cellCache = {}
        scp.recGroup = scp.recs['stores']
        scp.NA = ""
        
        for lineCount, line in enumerate(lines):
            fn = line['function']
            hide = line['hide']
            field = line['field']
            field2 = line['field2']
            name = line['name']
            val = line['val']
            fmt = line['format']

#            print "fn: %s, hide: %s, field: %s, name:%s"%(fn,hide,field,name)

            if fn is None:
                continue

            if fn == 'outputName':
                outputName = field + output_suffix + ".csv"
                continue

            if fn == 'setNA':
                if field is None:
                    scp.NA = ""
                else:
                    scp.NA = field
                continue

            if fn == 'use':
                if field not in scp.recs:
                    raise RuntimeError("error on line %d.  No such group %s"%(lineCount, field))
                scp.recGroup = scp.recs[field]
                continue

            if fn == 'require':
                scp._require(field, val)
                continue

            if fn == 'goto':
                try:
                    if field in scp.cellCache:
                        field = scp.cellCache[field]
                    if field2 in scp.cellCache:
                        field2 = scp.cellCache[field2]
                    field = int(field)
                    field2 = int(field2)
                    if field2 < 0:
                        field2 = len(scp.rows) + field2 + 1 #(-1 being the first unused row)
                    assert(field >= 0)
                    assert(field2 >= 0)
                except:
                    raise RuntimeError("error on line %d, invalid cell for goto"%lineCount)
                scp.cell = [field,field2]
                continue

            if fn == 'skip':
                try:
                    xSkip = 1
                    ySkip = 0
                    if field2 is not None:
                        xSkip = 0
                    if field is not None:
                        xSkip = int(field)
                        assert(scp.cell[0] + xSkip >= 0)
                    if field2 is not None:
                        ySkip = int(field2)
                        assert(scp.cell[1] + ySkip >= 0)
                except:
                    raise RuntimeError("error on line %d, skip field and field2 must either be empty or an integer"%lineCount)
                scp.cell[0] += xSkip
                scp.cell[1] += ySkip
                continue

            if fn == 'saveCell':
                scp.cellCache[field] = scp.cell[0]
                scp.cellCache[field2] = scp.cell[1]
                continue
            
            if fn == 'label':
                scp._placeCell(name)

            elif fn in ('display', 'sumClientRoutes', 'sumClients', 'averageClients', 'addFields', 'divFields', 
                        'sumClientTree', 'textColumn', 'runNumColumn'):
                if fn == 'display':
                    if name is None:
                        name = field
                elif fn == 'addFields':
                    name = scp._addFields(field, field2, name)
                elif fn == 'divFields':
                    name = scp._divFields(field, field2, name)

                # the following assume we're working on a set of stores.  I'm not requiring it here though!
                elif fn == 'sumClientRoutes':
                    name = scp._sumClientRoutes(field,name)
                elif fn == 'sumClients':
                    name = scp._sumClients(field,name)
                elif fn == 'averageClients':
                    name = scp._averageClients(field,name)
                elif fn == 'sumClientTree':
                    name = scp._sumClientTree(field, name)

                elif fn == 'textColumn':
                    name = field
                    field = None
                elif fn == 'runNumColumn':
                    name = output_suffix
                    try:
                        if name[0] == '_':
                            name = name[1:]
                    except:
                        pass
                    field = None

                scp._placeColumn(field, name, hide=hide, fmt=fmt)

            elif fn in ('statSumField', 'statSumFieldForField2Val', 'statAverageField', 'statAverageFieldForField2Val'):
                if fn == 'statSumField':
                    (name,value) = scp._statSumField(field, name)
                elif fn == 'statSumFieldForField2Val':
                    (name,value) = scp._statSumFieldForField2Val(field, name, field2, val)
                elif fn == 'statAverageField':
                    (name,value) = scp._statAverageField(field, name)
                elif fn == 'statAverageFieldForField2Val':
                    (name,value) = scp._statAverageFieldForField2Val(field, name, field2, val)

                if hide is None:
                    scp._placeCell(name,fmt='string')
                scp._placeCell(value,fmt=fmt)
            
            elif fn in ('aggregateValues', 'aggregateSum', 'aggregateAverage'):
                if fn == 'aggregateValues':
                    (name,d) = scp._aggregateValues(field, name)
                    hide = True
                elif fn == 'aggregateSum':
                    (name,d) = scp._aggregateSum(field,field2,name)
                elif fn == 'aggregateAverage':
                    (name,d) = scp._aggregateAverage(field,field2,name)
                
                items = d.items()
                items.sort()
                recList = [{'key':key, 'val':val} for (key,val) in items]
                
                scp._placeColumn('key', field, recList, hide=hide, fmt='string')
                scp._placeColumn('val', name, recList, fmt=fmt)

            else:
                raise RuntimeError("invalid custom output fn (%s) on line %d"%(fn,lineCount))

        with openOutputFile(outputName) as f:
            for row in scp.rows:
                fmtd = ""
                for i,val in enumerate(row):
                    if i > 0: fmtd += ','
                    fmtd += str(val)
                fmtd += '\n'
                f.write(fmtd)


    # _placeColumn and _placeCell will move cell one space to the right when done
    def _placeColumn(self, field, label, recs=None, hide=None, fmt=None):
        if not (hide is None or hide == 'header'):
            return
        if recs == None:
            recs = self.recGroup
        cell = copy.deepcopy(self.cell)
        if hide != 'header':
            self._xPlaceCell(cell, label, fmt)
        for rec in recs:
            cell[1] += 1
            if field is None:
                self._xPlaceCell(cell, label, fmt)
            elif field in rec:
                self._xPlaceCell(cell, rec[field], fmt)
            else:
                self._xPlaceCell(cell, self.NA, fmt)
        self.cell[0] += 1

    def _placeCell(self, val,fmt=None):
        self._xPlaceCell(self.cell, val, fmt)
        self.cell[0] += 1

    # _xPlaceCell is intended as a lower level call used by the functions above.
    def _xPlaceCell(self, cell, val, fmt=None):
        while len(self.rows) <= cell[1]:
            self.rows.append([])
        row = self.rows[cell[1]]
        while len(row) <= cell[0]:
            row.append('')
        try:
            v = self.NA
            if fmt != "num":
                v = unicode(val)
            if fmt != "string":
                v = float(val)
            if fmt == "int":
                v = long(val)
        except:
            pass

        row[cell[0]] = v


    # hmm, I may wish to break the special noteholder types
    # in these routines...
    # actually, now I'm sure I do... created fields are now floats

    def _sumVaxFields(self):
        """
        create sums of all of the vaxfields
        also create '_availability' fields (_treated / _patients)
        """
        vaxNames = [vax['Name'] for vax in self.vaxSummaryRecs]
        fields = ['_outages', '_patients', '_treated', '_vials', '_expired']
        for code,store in self.stores.items():
            if store['note'] is None:
                continue
            note = store['note']
            d = note.getDict()
            sum_p = sum_t = 0.0
            create_allvax_avail = False
            for name in vaxNames:
                for field in fields:
                    if name+field in d:
                        note.addNote({"allvax"+field : float(d[name+field])})
                if name + "_patients" not in d:
                    continue
                create_allvax_avail = True
                p = float(d[name + "_patients"])
                sum_p += p
                if name + "_treated" not in d:
                    t = 0
                else:
                    t = float(d[name + "_treated"])
                sum_t += t
                if p > 0:  avail = t / p
                else:      avail = 0.0
                note.addNote({name + "_availability" : avail})

            if not create_allvax_avail:
                continue
            if sum_p > 0:   avail = sum_t / sum_p
            else:           avail = 0.0
            note.addNote({"allvax_availability" : avail})

    def _require(self, field, val):
        newGroup = []
        for d in self.recGroup:
            keep = False
            if field not in d:
                continue
            try:
                if isinstance(d[field], types.StringTypes):
                    if val is not None:
                        if d[field] == val:
                            keep = True
                        else:
                            continue
                    else:
                        keep = True
                else:
                    test = float(d[field])
                    if val is not None:
                        if "%s"%test == "%s"%val:
                            keep = True
                        else:
                            continue
                    else:
                        if test == 0.0:
                            continue
                        else:
                            keep = True
            except:
                pass
            if not keep:
                continue
            newGroup.append(d)
        self.recGroup = newGroup

    def _addFields(self, field, field2, name):
        if field is None:
            return
        if field2 is None:
            return
        if name is None:
            name = "sum_" + field + "_" + field2
        
        for d in self.recGroup:
            s = 0.0
            if field not in d:
                if field2 not in d:
                    continue
            if field in d:
                try: s += float(d[field])
                except: pass

            if field2 in d:
                try: s += float(d[field2])
                except: pass
            d[name] = s
    
    def _divFields(self, field, field2, name):
        if field is None:
            return
        if field2 is None:
            return
        if name is None:
            name = "ratio_" + field + "_" + field2
        for d in self.recGroup:
            try: d[name] = float(d[field]) / float(d[field2])
            except: pass
        return name

    def _sumClientRoutes(self, field, name):
        if name is None:
            name = "sumClientRoutes_" + field
        for code,store in self.stores.items():
            if store['note'] is None:
                continue
            note = store['note']
            for cr in store['clientRoutes']:
                if cr['name'] not in self.routes:
                    continue
                routeNotes = self.routes[cr['name']]['note']
                if routeNotes is None:
                    continue
                d = routeNotes.getDict()
                if field not in d:
                    continue
                try: note.addNote({name : float(d[field])})
                except: pass
        return name
                    
    def _averageClients(self, field, name):
        if name is None:
            name = "averageClients_" + field
        for code, store in self.stores.items():
            if store['note'] is None:
                continue
            note = store['note']
            sum = 0.0
            count = 0
            for cr in store['clientRoutes']:
                for client in cr['clients']:
                    count += 1
                    try:
                        d = client['note'].getDict()
                        sum += float(d[field])
                    except:
                        pass
            if count > 0:
                note.addNote({name : sum / count})

        return name

    def _sumClients(self, field, name):
        if name is None:
            name = "sumClients_" + field
        for code, store in self.stores.items():
            if store['note'] is None:
                continue
            note = store['note']
            for cr in store['clientRoutes']:
                for client in cr['clients']:
                    try:
                        d = client['note'].getDict()
                        if field in d:
                            note.addNote({name : float(d[field])})
                    except:
                        pass
        return name

    def _sumClientTree(self, field, name, store = None):
        """
        Get the sum of field for the full tree of clients.
        This does not include the value in this row.  If this is 
        desired the value for this row can be added with an 'addFields'
        """
        if name is None:
            name = "sumClientTree_" + field
        if store is None:
            for st in self.rootStores:
                self.sumClientTree(field, name, st)
            return name

        s = 0.0
        for rt in store['clientRoutes']:
            for client in rt['clients']:
                s += self.sumClientTree(field, name, client)

        note = store['note']
        if note is not None:
            note.addNote({name: s})
            d = note.getDict()
            if field in d:
                try: s += float(d[field])
                except: pass
        return s

    def _statSumField(self, field, name):
        if name is None:
            name = "sum_" + field
        s = 0.0
        for d in self.recGroup:
            if field in d:
                try: s += float(d[field])
                except: pass

        return (name, s)

    def _statSumFieldForField2Val(self, field, name, field2, val):
        if name is None:
            name = "sum_" + field + "_for_" + field2 + "_is_" + val
        s = 0.0
        for d in self.recGroup:
            if field not in d:
                continue
            if field2 not in d:
                continue
            if "%s"%d[field2] != "%s"%val:
                continue
            try: s += float(d[field])
            except: pass
            
        return (name,s)

    def _statAverageField(self, field, name):
        if name is None:
            name = "mean_" + field
        s = 0.0
        for d in self.recGroup:
            if field in d:
                try: s += float(d[field])
                except: pass
        av = 0.0
        try: av = s / len(self.recGroup)
        except: pass
        return (name, av)

    def _statAverageFieldForField2Val(self, field, name, field2, val):
        if name is None:
            name = "mean_" + field + "_for_" + field2 + "_is_" + val
        s = 0.0
        ct = 0
        for d in self.recGroup:
            if field2 not in d:
                continue
            if "%s"%d[field2] != "%s"%val:
                continue
            ct += 1
            if field not in d:
                continue
            try: s += float(d[field])
            except: pass
        if ct == 0:
            return (name, 0)
        return (name,s/ct)

    def _aggregateValues(self, field, name):
        if name is None:
            name = 'values_%s'%field
        vals = {}
        for d in self.recGroup:
            f = None
            if field in d:
                f = d[field]
            vals[f] = f
        return name,vals

    def _aggregateSum(self, field, field2, name):
        if name is None:
            name = 'sum_%s_by_%s'%(field, field2)
        sums = collections.defaultdict(lambda: 0.0)
        for d in self.recGroup:
            f2 = None
            if field2 in d:
                f2 = d[field2]
            # touch the sum for this value so that even if 
            # field doesn't exist on this row, the sum will.
            # in this manner our rows will line up.
            cur = sums[f2]
            if field in d:
                try: sums[f2] += float(d[field])
                except: pass
        return name,sums


    def _aggregateAverage(self, field, field2, name):
        # nonexistant <field> is treated as a 0.0
        if name is None:
            name = 'mean_%s_by_%s'%(field, field2)
        sums = collections.defaultdict(lambda: [0.0,0])

        for d in self.recGroup:
            f2 = None
            if field2 in d:
                f2 = d[field2]

            sums[f2][1] += 1
            if field in d:
                try: sums[f2][0] += float(d[field])
                except: pass

        for k in sums.keys():
            (num,den) = sums[k]
            sums[k] = num/den  # impossible for denominator to be 0
                
        return name,sums

                
    def writeOutputs(self):
        if self.customOutputs is None:
            return
        for output in self.customOutputs:
            print "working on output %s"%output
            self.writeCustomCSV(output, "_%s"%self.runNumber)

    def strengthenRefs(self):
        "do this before you pickle an output"
        self.notes.strengthenRefs()


    def save(self, fileName):
        self.strengthenRefs()
        fileName += '_%s.pkl'%self.runNumber
        with openOutputFile(fileName) as f:
            f.write(pickle.dumps(self, 0))


class HermesOutputMerged(HermesOutput):
    """
    Take one or more HermesOutput()s and combine their notes into one structure.

    This is subclassed from HermesOutput so that any of the HermesOutput functions
    can be called on it especially WriteCustomCSV

    stores and routes notes are stored as AccumVals.  By default when you read
    any of the notes they return the mean for that value.  The default function can be 
    overridden with setNoteFn() to any of the AccumVal stat outputs (or any other
    function that can handle an AccumVal).
    """
    def __init__(self, outputList):
        outputList = listify(outputList)
        # since various attributes are linked make a deepcopy and move links from
        # there as needed.
        cpy = copy.deepcopy(outputList[0])

        self.runNumber = "average"
        self.customOutputs = cpy.customOutputs

        self.notes = cpy.notes
        self.stores = cpy.stores
        self.routes = cpy.routes
        self.other = []
        self.rootStores = cpy.rootStores

        self.noteFn = [util.meanAccumVal]
        self.mergeCount = len(outputList)

        for id,store in self.stores.items():
            note = store['note']
            if note is None:
                continue
            # first find all of the keys
            keys = set()
            for o in outputList:
                try:
                    od = o.stores[id]['note'].getDict()
                    keys.update(od.keys())
                except:
                    pass

            # now replace all of the numeric notes in our new notes structure.
            # we're going to assume that all string notes are going to be constant between runs.
            d = note.getDict()

            for key in keys:
                if key in ['code']:
                    continue
                try:
                    if isinstance(d[key], types.StringTypes):
                        continue
                except:
                    pass
                

                for i,o in enumerate(outputList):
                    try:
                        od = o.stores[id]['note'].getDict()
                        v = od[key]
                    except:
                        v = 0.0

                    if i == 0:
                        note.replaceNote({key:AccumVal(float(v), self.noteFn, self.noteFn)})
                    else:
                        note.addNote({key:float(v)})


        for id,route in self.routes.items():
            note = route['note']
            if note is None:
                continue
            # first find all of the keys
            keys = set()
            for o in outputList:
                try:
                    od = o.routes[id]['note'].getDict()
                    keys.update(od.keys())
                except:
                    pass

            # now replace all of the numeric notes in our new notes structure.
            # we're going to assume that all string notes are going to be constant between runs.
            d = note.getDict()

            for key in keys:
                if key in ['RouteName']:
                    continue
                try:
                    if isinstance(d[key], types.StringTypes):
                        continue
                except:
                    pass
                
                for i,o in enumerate(outputList):
                    try:
                        od = o.routes[id]['note'].getDict()
                        v = od[key]
                    except:
                        v = 0.0

                    if i == 0:
                        note.replaceNote({key:AccumVal(float(v), self.noteFn, self.noteFn)})
                    else:
                        note.addNote({key:float(v)})


        r = [output.vaxSummaryRecs for output in outputList]
        self.vaxSummaryRecs = self._mergeSummaryRecs(r) 
        r = [output.peopleSummaryRecs for output in outputList]
        self.peopleSummaryRecs = self._mergeSummaryRecs(r) 
        r = [output.truckSummaryRecs for output in outputList]
        self.truckSummaryRecs = self._mergeSummaryRecs(r) 
        r = [output.fridgeSummaryRecs for output in outputList]
        self.fridgeSummaryRecs = self._mergeSummaryRecs(r) 
        r = [output.storageSummaryRecs for output in outputList]
        self.storageSummaryRecs = self._mergeSummaryRecs(r) 

        self.recs = {'vax': self.vaxSummaryRecs,
                     'people': self.peopleSummaryRecs,
                     'truck': self.truckSummaryRecs,
                     'fridge': self.fridgeSummaryRecs,
                     'storage': self.storageSummaryRecs,
                     'stores': [],    # fill in stores and routes in just a minute...
                     'routes': [] }

        for store in self.stores.itervalues():
            if store['note'] is not None:
                self.recs['stores'].append(store['note'].getDict())
        for route in self.routes.itervalues():
            if route['note'] is not None:
                self.recs['routes'].append(route['note'].getDict())


    def setNoteFn(self, fn = util.meanAccumVal):
        self.noteFn[0] = fn

    def _mergeSummaryRecs(self, recListList):
        out = {}
        for recList in recListList:
            for rec in recList:
                if 'Name' not in rec:
                    #um... I don't know how to merge it if it doesn't have a Name
                    continue
                
                name = rec['Name']
                if name not in out:
                    out[name] = {}
                outRec = out[name]
                for key,val in rec.items():
                    if isinstance(val, types.StringTypes):
                        outRec[key] = val
                    else:
                        if key in outRec:
                            outRec[key] += float(val)
                        else:
                            outRec[key] = AccumVal(float(val), self.noteFn, self.noteFn)
        return [val for key,val in sorted(out.items())]


    
    def _mergeNote(self, note, newNote, exemptKeys):
        """
        merge all of the notes from newNote into note.  This should work even if newNote is None
        """
        noteDict = note.getDict()
        try:
            hod = newNote.getDict()
        except:
            pass

        # first find all of the keys
        keys = set()
        keys.update(noteDict.keys())
        try:
            # find new keys that are in the new output.
            # We will presume that they are numeric and add an appropriate
            # amount of zeros to the stats in self
            for key in hod.keys():
                if key in keys:
                    continue
                for i in xrange(self.mergeCount):
                    note.addNote({key:AccumVal(0.0, self.noteFn, self.noteFn)})
            keys.update(hod.keys())
        except:
            pass

        #update all of the numeric keys.  We assume that string keys are constant between runs.
        for key in keys:
            if key in exemptKeys:  # some keys are special
                continue

            # now that we've added all of the extra keys, this shouldn't fail
            if isinstance(noteDict[key], types.StringTypes):
                continue

            try:
                v = hod[key]
            except:
                v = 0.0

            note.addNote({key:float(v)})
        

    def mergeNewOutput(self, ho):
        for id,store in self.stores.items():
            note = store['note']
            if note is None:
                continue
            try:
                newNote = ho.stores[id]['note']
            except:
                newNote = None

            self._mergeNote(note, newNote, ['code'])


        for id,route in self.routes.items():
            note = route['note']
            if note is None:
                continue
            try:
                newNote = ho.routes[id]['note']
            except:
                newNote = None

            self._mergeNote(note, newNote, ['RouteName'])

        self.vaxSummaryRecs = self._mergeNewSummaryRecList(self.vaxSummaryRecs, ho.vaxSummaryRecs)
        self.peopleSummaryRecs = self._mergeNewSummaryRecList(self.peopleSummaryRecs, ho.peopleSummaryRecs)
        self.truckSummaryRecs = self._mergeNewSummaryRecList(self.truckSummaryRecs, ho.truckSummaryRecs)
        self.fridgeSummaryRecs = self._mergeNewSummaryRecList(self.fridgeSummaryRecs, ho.fridgeSummaryRecs)
        self.storageSummaryRecs = self._mergeNewSummaryRecList(self.storageSummaryRecs, ho.storageSummaryRecs)

        self.recs = {'vax': self.vaxSummaryRecs,
                     'people': self.peopleSummaryRecs,
                     'truck': self.truckSummaryRecs,
                     'fridge': self.fridgeSummaryRecs,
                     'storage': self.storageSummaryRecs,
                     'stores': [],    # fill in stores and routes in just a minute...
                     'routes': [] }

        for store in self.stores.itervalues():
            if store['note'] is not None:
                self.recs['stores'].append(store['note'].getDict())
        for route in self.routes.itervalues():
            if route['note'] is not None:
                self.recs['routes'].append(route['note'].getDict())

        self.mergeCount += 1



    def _mergeNewSummaryRecList(self, recList, newRecList):
        # first break out the old recList into a dict
        out = {}
        for rec in recList:
            if 'Name' not in rec:
                # we need a name
                continue
            name = rec['Name']
            out[name] = rec

        for rec in newRecList:
            if 'Name' not in rec:
                continue
            mRec = out[rec['Name']]
            for key,val in rec.items():
                if key in ['Name']: # ignored keys
                    continue
                if isinstance(val, types.StringTypes):  # just set or overwrite strings
                    mRec[key] = val
                    continue
                if key not in mRec:
                    mRec[key] = AccumVal(0.0, self.noteFn, self.noteFn)
                    for i in xrange(self.mergeCount - 1):
                        mRec[key] += AccumVal(0.0, self.noteFn, self.noteFn)
                mRec[key] += AccumVal(float(val), self.noteFn, self.noteFn)
        return [val for key,val in sorted(out.items())]
                    
