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


import json
from itertools import product
from abc import ABCMeta, abstractproperty
from collections import defaultdict

class CostModelHierarchicalSummary(object):
    __metaclass__ = ABCMeta
    def __init__(self, result):
        self.result = result

    def _do(self, groups, costs):
        recs = self.result.getCostSummaryRecs()
        d = {}
        for r in recs:
            if r.ReportingLevel == '-top-' or r.ReportingLevel == u'-top-':
                continue
            for g in groups:
                #print g
                if g not in d:
                    d[g] = {}
                g_attr = getattr(r, g)
                #print g_attr
                if g_attr not in d[g]:
                    d[g][g_attr] = {}
                for c in costs:
                    #print c
                    if c not in d[g][g_attr]:
                        d[g][g_attr][c] = 0.0
                    c_attr = getattr(r, c)
                    c_attr = float(c_attr) if c_attr is not None else 0.0
                    #print c_attr
                    d[g][g_attr][c] += c_attr
        #print d
        h = {} 
        for g in groups:
            #print g
            h['name'] = g
            children = []
            for g_attr in d[g]:
                #print g_attr
                children.append(
                        {'name':g_attr,
                         'children': [{
                             'name':n, 'size':s
                             } for n, s in d[g][g_attr].items()]})
                #print children
            h['children'] = children
        #print h
        return h


class LegacyCostModelHierarchicalSummary(CostModelHierarchicalSummary):

    def dict(self):
        groups = ('ReportingLevel',)
        costs = (
                #'PerDiemCost','PerKmCost','PerTripCost',
                'LaborCost','BuildingCost','StorageCost','TransportCost'
                )
        return self._do(groups, costs)

class DummyCostModelHierarchicalSummary(CostModelHierarchicalSummary):

    def dict(self):
        return {}


