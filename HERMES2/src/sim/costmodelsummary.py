#!/usr/bin/env python 

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


""" costmodelsummary.py
This module holds classes used to provide hierarchical summaries of
output from supported cost models.
"""

_hermes_svn_id_ = "$Id: costmodelsummary.py 879 2014-09-17 12:47:47Z depasse $"


import types
from abc import ABCMeta
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
            # print 'rec %s'%r
            # if r['ReportingLevel'] == '-top-' or r['ReportingLevel'] == u'-top-':
            #     continue
            for g in groups:
                if g not in d:
                    d[g] = {}
                g_attr = r[g]
                # print 'g_attr: %s'%g_attr
                if g_attr not in d[g]:
                    d[g][g_attr] = {}
                for c in costs:
                    if c not in d[g][g_attr]:
                        d[g][g_attr][c] = 0.0
                    if c in r:
                        c_attr = r[c]
                        if c_attr == '':
                            c_attr = None
                        c_attr = float(c_attr) if c_attr is not None else 0.0
                        d[g][g_attr][c] += c_attr
        # print d
        h = {}
        for g in groups:
            h['name'] = g
            children = []
            for g_attr in d[g]:
                children.append({'name': g_attr,
                                 'children':  [{'name': n, 'size': s}
                                               for n, s in d[g][g_attr].items()]})
            h['children'] = children
        return h

    def _mkSubTree(self, key, localD, treeD, prefixLen):
        """
        This routine converts a treeD to a recursive subTree.  The former has the format:

        {
            '-top-': {
                'all': {'cost1':v, 'cost2':v, ...}
            },
            'all':   {
                'Central':  {'cost1:v, 'cost2:v, ...},
                'Region':   {'cost1:v, 'cost2:v, ...},
                'District': {'cost1:v, 'cost2:v, ...},
                'IHC':      {'cost1:v, 'cost2:v, ...},
            },
            'Central': {
                'loc foo': {'cost1:v, 'cost2:v, ...}
                'rt A': {'cost1:v, 'cost2:v, ...},
                ...
            },
            'Region': {
                'loc bar': {'cost1:v, 'cost2:v, ...},
                'loc baz': {'cost1:v, 'cost2:v, ...},
                'rt B':    {'cost1:v, 'cost2:v, ...},
                ...
            },
            ...
        }

        where v is some scalar value.

        A subTree is truly recursive, and has elements with keys 'name', 'size', and 'children'.
        If 'size' is present it is a leaf node and 'size' is a scalar.  If 'children' is present
        it is a list each entry of which is a subTree.  Every node has a 'name', and either a
        'children' list or a 'size' value.  Calling _mkSubTree('-top-', treeD['-top-'], treeD) on
        the treeD example above produces:

        {
            'name':     '-top-',
            'children': [
                {'name':'all',
                 'children': [
                     {'name': 'Central',
                      'children': [
                          {'name':'loc foo',
                           'children: [
                              {'name':'cost1', 'size':v}, <-- 'cost1' entry from treeD['Central']['loc foo']
                              {'name':'cost2', 'size':v},
                              ...
                            ]},
                          {'name':'rt A',
                           'children: [
                              {'name':'cost1', 'size':v}, <-- 'cost1' entry from treeD['Central']['rt A']
                              {'name':'cost2', 'size':v},
                              ...
                            ]},
                           },
                          {'name':'cost1', 'size':v}, <-- 'cost1' entry from treeD['all']['Central']
                          {'name':'cost2', 'size':v},
                          ...
                      ]},
                {'name':'cost1', 'size':v}, <-- the 'cost1' entry from treeD['-top-']['all']
                {'name':'cost2', 'size':v},
                ...
            ]}
        """
        children = []
        if key in treeD:
            for k, v in treeD[key].items():
                children.append(self._mkSubTree(k, v, treeD, prefixLen))
        leaves = localD.items()
        for lKey, lVal in leaves:
            if lKey not in treeD:
                children.append({'name': lKey[prefixLen:],
                                 'size': lVal
                                 })
        return {'name': key,
                'children': children
                }

    def _printSubTree(self, tree, depth=0):
        """This routine prints a subTree, with indenting."""
        if 'children' in tree:
            print '%s%s:' % ('    '*depth, tree['name'])
            for child in tree['children']:
                self._printSubTree(child, depth+1)
        else:
            if tree:
                print '%s%s: %s' % ('    '*depth, tree['name'], tree['size'])
            else:
                print '%s-empty-' % ('    '*depth)

    def _blankToZero(self, v):
        if v == '' or v == ' ':
            return 0.0
        else:
            return v

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
            treeD[lvl][brch] = {k: self._blankToZero(v) for k, v in r.items() if k in costSet}
        # h = self._mkSubTree('all', treeD['all'], treeD, prefixLen)
        h = self._mkSubTree('-top-', treeD['-top-'], treeD, prefixLen)
        # self._printSubTree(h)
        # return h
        return h['children'][0]

    def _cullTree(self, subTree, testSet):
        """
        This routine removes collective entries from upper levels of the tree, leaving
        only the corresponding entries at the deepest levels.  For example, in the example
        in _mkSubTree, fullTree{children:[{name:'cost1'...}]} and
        fullTree{children:[{name:'Central',children:[{name:cost1...}]}]} would be removed.
        """
        if 'children' in subTree:
            newKids = []
            nKidsWithKids = len([child for child in subTree['children']
                                 if 'children' in child])
            for child in subTree['children']:
                if child['name'] in testSet and nKidsWithKids > 0:
                    pass  # drop this one
                else:
                    newKids.append(child)
                    self._cullTree(child, testSet)
            subTree['children'] = newKids

    def _clipNames(self, treeD, testSet, clipLen=0):
        """
        Remove clipLen characters from names in testSet everywhere in the tree.

        This is used to clip prefixes, for example 'm1C_', from cost entries.
        """
        if 'children' in treeD:
            for child in treeD['children']:
                self._clipNames(child, testSet, clipLen)
        if treeD['name'] in testSet:
            treeD['name'] = treeD['name'][clipLen:]

    def _collectLeaves(self, subTree, labelList, parentInfo=None):
        """
        Walk the tree depth first, collecting a list of dicts.  Each dict in the list
        contains keys and values for all layers encountered in the walk.  Labellist is
        a list of keys for successive labels, such as ['ignore','level','location'] .

        For example, the call self._collectLeaves(subTree, ['ignore','level','location', 'key']) with
        subTree as in the description of _mkSubTree would return:

        [
            {'ignore':'-top-', 'level':'cost1', 'size':v},
            {'ignore':'-top-', 'level':'cost2', 'size':v},
            {'ignore':'-top-', 'level':'all', 'location':'cost1', 'size':v},
            {'ignore':'-top-', 'level':'all', 'location':'cost2', 'size':v},
            {'ignore':'-top-', 'level':'Central', 'location':'loc foo', 'key':'cost1', 'size':v},
            {'ignore':'-top-', 'level':'Central', 'location':'loc foo', 'key':'cost2', 'size':v},
            {'ignore':'-top-', 'level':'Central', 'location':'rt A', 'key':'cost1', 'size':v},
            {'ignore':'-top-', 'level':'Central', 'location':'rt A', 'key':'cost2', 'size':v},
            ...
        ]
        """
        if parentInfo is None:
            parentInfo = {}
        subPI = parentInfo.copy()
        if 'children' in subTree:
            assert labelList, 'we have run out of labels'
            subPI[labelList[0]] = subTree['name']
            kidDicts = []
            for kid in subTree['children']:
                kidDicts.extend(self._collectLeaves(kid, labelList[1:], subPI))
        else:
            d = subPI.copy()
            d.update(subTree)
            assert len(labelList) == 1, "%d labels at leaf" % len(labelList)
            d[labelList[0]] = d['name']
            del d['name']
            kidDicts = [d]
        return kidDicts

    def _listToTreeList(self, keyList, leafList, depth=0):
        """
        Given a list of elaborated leaf nodes 'leafList' as produced by _collectLeaves,
        reconstruct a list of trees with layers determined by the given 'keyList'.  This
        essentially converts a leafList to a list of dicts suitable to be a new subTree's
        'children' list, undoing the work of _collectLeaves.
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

    def _cleanSubTree(self, subTree):
        """Remove all entries which are not 'name', 'children', or 'size'. """
        for k in subTree.keys()[:]:
            if k not in ['children', 'size', 'name']:
                del subTree[k]
        if 'children' in subTree:
            for kid in subTree['children']:
                self._cleanSubTree(kid)

    def _rekeySubTree(self, subTree, oldKey, newKey):
        if oldKey in subTree:
            subTree[newKey] = subTree[oldKey]
            del subTree[oldKey]
        if 'children' in subTree:
            for kid in subTree['children']:
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
            fullTree = self._doByContainer(groups, set(costs))
            self._cullTree(fullTree, set(costs))
            leafDicts = [lD for lD in self._collectLeaves(fullTree,
                                                          ['ignore', 'level', 'location', 'key'])
                         if (lD['size'] != 0.0 and lD['size'] is not None and lD['size'] != '')]
            for l in leafDicts:
                del l['ignore']
            fullTree = {'name': 'all',
                        'children': self._listToTreeList(['level', 'location'],
                                                         leafDicts)}
            self._rekeySubTree(fullTree, 'key', 'name')
            # self._printSubTree(fullTree)
            return fullTree
        else:
            raise RuntimeError("Unrecognized hierarchy format %s" % fmt)


class DummyCostModelHierarchicalSummary(CostModelHierarchicalSummary):

    def dict(self, fmt=None):
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
            subTree = self._doByContainer(groups, self.PrefixFakeSet(tag), 0)
            self._cullTree(subTree, self.PrefixFakeSet(tag))
            self._clipNames(subTree, self.PrefixFakeSet(tag), len(tag))
            if fmt is None:
                kidDicts = [kD for kD in self._collectLeaves(subTree,
                                                             ['ignore', 'level', 'location',
                                                              'key'])
                            if (kD['size'] != 0.0 and kD['size'] is not None and kD['size'] != '')]
                for k in kidDicts:
                    del k['ignore']
                subTree = {'name': 'all',
                           'children': self._listToTreeList(['level', 'location'],
                                                            kidDicts)}
                self._rekeySubTree(subTree, 'key', 'name')
                # self._printSubTree(subTree)
                return subTree
            else:
                lvlList = self._parseFormat(fmt)
                nC = lvlList.count('c')
                nL = lvlList.count('l')
                kidDicts = [kD for kD in self._collectLeaves(subTree,
                                                             ['ignore', 'level', 'location',
                                                              'key'])
                            if (kD['size'] != 0.0 and kD['size'] is not None and kD['size'] != '')]
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

                subTree = {'name': 'all',
                           'children': self._listToTreeList(lvlList[:-1],
                                                            kidDicts)}
                self._rekeySubTree(subTree, lvlList[-1], 'name')
                self._cleanSubTree(subTree)
                # self._printSubTree(subTree)
                return subTree
