#!/usr/bin/env python 

########################################################################
# Copyright C 2010, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" costmodelsummary.py
This module holds classes used to provide hierarchical summaries of
output from supported cost models.
"""

_hermes_svn_id_="$Id: costmodelsummary.py 879 2014-09-17 12:47:47Z depasse $"


import json, types
from itertools import product
from abc import ABCMeta, abstractproperty
from collections import defaultdict
import ipath
from util import logWarning

class CostModelHierarchicalSummary(object):
    __metaclass__ = ABCMeta
    def __init__(self, result):
        self.result = result

    def _do(self, groups, costs):
        recs = [r.createRecord() for r in self.result.getCostSummaryRecs()]
        d = {}
        for r in recs:
            #print 'rec %s'%r
#             if r['ReportingLevel'] == '-top-' or r['ReportingLevel'] == u'-top-':
#                 continue
            for g in groups:
                if g not in d:
                    d[g] = {}
                g_attr = r[g]
                #print 'g_attr: %s'%g_attr
                if g_attr not in d[g]:
                    d[g][g_attr] = {}
                for c in costs:
                    if c not in d[g][g_attr]:
                        d[g][g_attr][c] = 0.0
                    if c in r:
                        c_attr = r[c]
                        if c_attr=='': c_attr = None
                        c_attr = float(c_attr) if c_attr is not None else 0.0
                        d[g][g_attr][c] += c_attr
        # print d
        h = {} 
        for g in groups:
            h['name'] = g
            children = []
            for g_attr in d[g]:
                children.append(
                        {'name':g_attr,
                         'children': [{
                             'name':n, 'size':s
                             } for n, s in d[g][g_attr].items()]})
            h['children'] = children
        return h

    def _mkSubTree(self, key, localD, treeD, prefixLen):
        children = []
        if key in treeD:
            for k,v in treeD[key].items():
                children.append(self._mkSubTree(k,v,treeD, prefixLen))
        leaves = localD.items()
        for lKey,lVal in leaves:
            if lKey not in treeD:
                children.append({
                                 'name':lKey[prefixLen:],
                                 'size':lVal
                                 })
        return {'name': key,
                'children': children
                }

    def _printSubTree(self, tree, depth=0):
        if 'children' in tree:
            print '%s%s:' % ('    '*depth, tree['name'])
            for child in tree['children']:
                self._printSubTree(child, depth+1)
        else:
            if tree:
                print '%s%s: %s' % ('    '*depth, tree['name'], tree['size'])
            else:
                print '%s-empty-' % ('    '*depth)

    def _doByContainer(self, groups, inSet, prefixLen=0):
        """
        groups is a sequence type or iterator
        inSet must implement at least '__contains__'
        prefixLen is an integer giving the length of the substring to clip from the front of
            each name
        """
        recs = [r.createRecord() for r in self.result.getCostSummaryRecs()]
        costSet = set()
        for r in recs:
            costSet.update([k for k in r.keys() if k in inSet])
        treeD = {}
        for r in recs:
            lvl = r['ReportingLevel']
            brch = r['ReportingBranch']
            if lvl not in treeD:
                treeD[lvl] = {}
            assert brch not in treeD[lvl], \
                ("Hierarchical cost summary has redundant entry for level %s branch %s"
                 % (lvl, brch))
            treeD[lvl][brch] = {k: v for k, v in r.items() if k in costSet}
        # h = self._mkSubTree('all', treeD['all'], treeD, prefixLen)
        h = self._mkSubTree('-top-', treeD['-top-'], treeD, prefixLen)
        # self._printSubTree(h)
        # return h
        return h['children'][0]

    def _cullTree(self, treeD, testSet):
        if 'children' in treeD:
            newKids = []
            nGrandKids = len([child for child in treeD['children']
                             if 'children' in child])
            for child in treeD['children']:
                if child['name'] in testSet and nGrandKids > 0:
                    pass  # drop this one
                else:
                    newKids.append(child)
                    self._cullTree(child, testSet)
            treeD['children'] = newKids

    def _clipNames(self, treeD, testSet, clipLen=0):
        if 'children' in treeD:
            for child in treeD['children']:
                self._clipNames(child, testSet, clipLen)
        if treeD['name'] in testSet:
            treeD['name'] = treeD['name'][clipLen:]

    def _collectLeaves(self, treeD, labelList, parentInfo=None):
        """Walk the tree depth first, collecting a list of dicts.  Each dict in the list
        contains keys and values for all layers encountered in the walk.  Labellist is
        a list of keys for successive labels, such as ['ignore','level','location']
        """
        if parentInfo is None:
            parentInfo = {}
        subPI = parentInfo.copy()
        if 'children' in treeD:
            assert labelList, 'we have run out of labels'
            subPI[labelList[0]] = treeD['name']
            kidDicts = []
            for kid in treeD['children']:
                kidDicts.extend(self._collectLeaves(kid, labelList[1:], subPI))
        else:
            d = subPI.copy()
            d.update(treeD)
            assert len(labelList) == 1, "ran out of labels at leaf"
            d[labelList[0]] = d['name']
            del d['name']
            kidDicts = [d]
        return kidDicts

    def _listToTreeList(self, keyList, leafList, depth=0):
        """Given a list of elaborated leaf nodes 'leafList' as produced by _collectLeaves,
        reconstruct a list of trees with layers determined by the given 'keyList'.
        """
        if keyList:
            myKey = keyList[0]
            myDict = {}
            for l in leafList:
                if myKey in l:
                    k = l[myKey]
                    if k not in myDict:
                        myDict[k] = []
                    subL = l.copy()
                    del subL[myKey]
                    myDict[k].append(subL)
            return [{'name': k, 'children': self._listToTreeList(keyList[1:], v, depth+1)}
                    for k, v in myDict.items()]
        else:
            # print '%sleaf returning %s' % ('    '*depth, leafList)
            return leafList

    def _cleanSubTree(self, treeD):
        for k in treeD.keys()[:]:
            if k not in ['children', 'size', 'name']:
                del treeD[k]
        if 'children' in treeD:
            for kid in treeD['children']:
                self._cleanSubTree(kid)

    def _rekeySubTree(self, treeD, oldKey, newKey):
        if oldKey in treeD:
            treeD[newKey] = treeD[oldKey]
            del treeD[oldKey]
        if 'children' in treeD:
            for kid in treeD['children']:
                self._rekeySubTree(kid, oldKey, newKey)


class LegacyCostModelHierarchicalSummary(CostModelHierarchicalSummary):

    def dict(self, fmt=None):
        """
        Return a tree of costs.  'fmt' must be 'mixed' or None.
        """
        groups = ('ReportingLevel',)
        costs = (
                # 'PerDiemCost', 'PerKmCost', 'PerTripCost',
                'LaborCost', 'BuildingCost', 'StorageCost', 'TransportCost'
                )
        if fmt not in ['mixed', None]:
            logWarning('invalid legacy cost hierarchy format %s ignored' % fmt)
            fmt = None
        if fmt == 'mixed':
            return self._doByContainer(groups, set(costs))
        elif fmt is None:
            treeD = self._doByContainer(groups, set(costs))
            self._cullTree(treeD, set(costs))
            # self._printSubTree(treeD)
            return treeD
        else:
            raise RuntimeError("Unrecognized hierarchy format %s" % fmt)


class DummyCostModelHierarchicalSummary(CostModelHierarchicalSummary):

    def dict(self):
        return {}


class Micro1CostModelHierarchicalSummary(CostModelHierarchicalSummary):
    costGroups = {'solar': 'fuel/power',
                  'electric': 'fuel/power',
                  'diesel': 'fuel/power',
                  'gasoline': 'fuel/power',
                  'kerosene': 'fuel/power',
                  'petrol': 'fuel/power',
                  'ice': 'fuel/power',
                  'propane': 'fuel/power',
                  'StaffSalary': 'staff',
                  'PerDiem': 'staff',
                  'TransitFareCost': 'staff',
                  'Vaccines': 'cargo',
                  'BuildingCost': 'equipment',
                  'FridgeAmort': 'equipment',
                  'TruckAmort': 'equipment',
                  'TruckMaint': 'equipment',
                  'FridgeMaint': 'equipment',
                  'SolarMaint': 'equipment'
                  }

    class PrefixFakeSet(object):
        def __init__(self, prefix):
            self.prefix = prefix

        def __contains__(self, arg):
            return isinstance(arg, types.StringTypes) and arg.startswith(self.prefix)

    def _parseFormat(self, fmtStr):
        assert isinstance(fmtStr, types.StringTypes) and fmtStr != 'mixed', \
            "Cannot parse the hierarchy format %s" % fmtStr
        charList = list(fmtStr.lower())
        assert all([(c == 'l' or c == 'c') for c in charList]), \
            "Invalid hierarchy format %s - must be c's or l's" % fmtStr
        assert len(charList) <= 4, "Maximum hierarchy format length is 4 so %s is invalid" % fmtStr
        assert len(charList) > 0, "Minimum hierarchy format length is 1 so empty string is invalid"
        return charList

    def dict(self, fmt=None):
        """
        Return a tree of costs.  'fmt' must be None, 'mixed', or a string between 1 and 4
        characters long containing up to two 'c' characters and up to two 'l' characters.
        The rightmost 'c' if present denotes cost item name; the next left 'c' if present
        denotes cost item category.  The rightmost 'l' if present denotes location; the
        next left 'l' if present denotes network level.  The root of the tree is the
        leftmost character.
        """
        groups = ('ReportingLevel',)
        tag = u'm1C_'
        if fmt == 'mixed':
            return self._doByContainer(groups, self.PrefixFakeSet(tag), len(tag))
        else:
            treeD = self._doByContainer(groups, self.PrefixFakeSet(tag), 0)
            self._cullTree(treeD, self.PrefixFakeSet(tag))
            self._clipNames(treeD, self.PrefixFakeSet(tag), len(tag))
            if fmt is None:
                return treeD
            else:
                lvlList = self._parseFormat(fmt)
                nC = lvlList.count('c')
                nL = lvlList.count('l')
                kidDicts = self._collectLeaves(treeD, ['ignore', 'level', 'location', 'key'])
                for k in kidDicts:
                    del k['ignore']
                    if k['key'] in self.costGroups:
                        k['category'] = self.costGroups[k['key']]
                    else:
                        if 'size' not in k or k['size'] != 0.0:
                            raise RuntimeError('Unexpected leaf dictionary %s' % k)

                if nC == 0:
                    pass
                elif nC == 1:
                    lvlList[lvlList.index('c')] = 'key'
                elif nC == 2:
                    lvlList[lvlList.index('c')] = 'category'
                    lvlList[lvlList.index('c')] = 'key'
                else:
                    raise RuntimeError("invalid format %s - only 2 c's allowed" % fmt)

                if nL == 0:
                    pass
                elif nL == 1:
                    lvlList[lvlList.index('l')] = 'location'
                elif nL == 2:
                    lvlList[lvlList.index('l')] = 'level'
                    lvlList[lvlList.index('l')] = 'location'
                else:
                    raise RuntimeError("invalid format %s - only 2 l's allowed" % fmt)

                treeD = {'name': 'all',
                         'children': self._listToTreeList(lvlList[:-1],
                                                          kidDicts)}
                self._rekeySubTree(treeD, lvlList[-1], 'name')
                self._cleanSubTree(treeD)
                # self._printSubTree(treeD)
                return treeD
