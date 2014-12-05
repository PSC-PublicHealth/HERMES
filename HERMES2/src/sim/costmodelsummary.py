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
        #print d
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
        # print costSet
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


class LegacyCostModelHierarchicalSummary(CostModelHierarchicalSummary):

    def dict(self, mixed=False):
        groups = ('ReportingLevel',)
        costs = (
                # 'PerDiemCost', 'PerKmCost', 'PerTripCost',
                'LaborCost', 'BuildingCost', 'StorageCost', 'TransportCost'
                )
        if mixed:
            return self._doByContainer(groups, set(costs))
        else:
            treeD = self._doByContainer(groups, set(costs))
            self._cullTree(treeD, set(costs))
            self._printSubTree(treeD)
            return treeD


class DummyCostModelHierarchicalSummary(CostModelHierarchicalSummary):

    def dict(self):
        return {}


class Micro1CostModelHierarchicalSummary(CostModelHierarchicalSummary):
    class PrefixFakeSet(object):
        def __init__(self, prefix):
            self.prefix = prefix

        def __contains__(self, arg):
            return isinstance(arg, types.StringTypes) and arg.startswith(self.prefix)

    def dict(self, mixed=False):
        groups = ('ReportingLevel',)
        tag = u'm1C_'
        if mixed:
            return self._doByContainer(groups, self.PrefixFakeSet(tag), len(tag))
        else:
            treeD = self._doByContainer(groups, self.PrefixFakeSet(tag), 0)
            self._cullTree(treeD, self.PrefixFakeSet(tag))
            self._clipNames(treeD, self.PrefixFakeSet(tag), len(tag))
            # self._printSubTree(treeD)
            return treeD
