#!/usr/bin/env python

########################################################################
# Copyright C 2011, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__="""powercut.py
This package encapsulates power failure support.
"""
_hermes_svn_id_="$Id$"

from SimPy.Simulation import *
from util import isiterable

def AddPowerCutInfo(sim, wh, userInput, rec):
    fields = ('FrequencyPerYear',
              'DurationDays',
              'DurationSigma',
              'AffectedRatio',
              'ClusterId')
    prefix = 'PowerOutage'

    # first find any suffixes in the record
    suffixes = set()
    # no suffix is always applicable
    suffixes.add('')
    for k in rec.keys():
        if k.startswith(prefix):
            for f in fields:
                if k.startswith(prefix + f):
                    suffixes.add(k[len(prefix)+len(f):])

    # now go through and put together the values
    # be careful, we only want at most one set of all default options
    fullDefaultExists = False
    for suf in suffixes:
        info = {}
        nonDefaultElementExists = False
        for f in fields:
            val = userInput[("%s%s"%(prefix, f)).lower()]
            if rec.has_key("%s%s%s"%(prefix, f, suf)) and rec["%s%s%s"%(prefix, f, suf)]:
                val = rec["%s%s%s"%(prefix, f, suf)]
                nonDefaultElementExists = True
            info[f] = val

        # pitch secondary all default cases
        if not nonDefaultElementExists:
            if fullDefaultExists:
                continue
            fullDefaultExists = True

        # make sure we've got enough information to continue on
        if not (info['FrequencyPerYear'] and info['DurationDays']):
            continue

        
        # make sure we have a clusterId
        if info['ClusterId'] is None:
            info['ClusterId'] = 'A_%s'%rec['idcode']
        else:
            info['ClusterId'] = 'D_%s'%info['ClusterId']
        cid = info['ClusterId']

        # add or update the power cut record to the sim powerCutDict
        if sim.powerCutDict.has_key(cid):
            sim.powerCutDict[cid].addStore(wh)
        else:
            sim.powerCutDict[cid] = PowerCut(sim, wh, info)
        

class PowerCut(Process):
    """
    Simpy process to simulate power failures at one or more clinics
    """

    def __init__(self, sim, stores, frequencyInfo):
        name = "PowerCut_%s"%frequencyInfo['ClusterId']
        Process.__init__(self, name=name, sim=sim)
        self.sim = sim
        if not isiterable(stores):
            stores = [stores]
        self.stores = stores
        self.frequencyInfo = frequencyInfo

    def addStore(self, store):
        self.stores.append(store)

    def run(self):
        dpy = self.sim.model.daysPerYear
        fi = self.frequencyInfo
        rndm = self.sim.rndm
        freq   = float(fi['FrequencyPerYear']) / dpy
        mag    = fi['DurationDays']
        sigma  = fi['DurationSigma']
        group  = fi['AffectedRatio']
        
        
        while True:
            delay = rndm.expovariate(freq)
            yield hold, self, delay

            if group:
                storesAffected = filter(lambda s: rndm.random() < group, self.stores)
                if 0 == len(storesAffected):
                    continue
            else:
                storesAffected = self.stores

            if sigma:
                duration = rndm.normalvariate(mag, sigma)
            else:
                duration = rndm.random() * mag * 2
            if duration < 0:
                continue

            for store in storesAffected:
                store.cutGridPower()
            yield hold, self, duration
            for store in storesAffected:
                store.restoreGridPower()
            
        
