#!/usr/bin/env python

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


__doc__="""delayinfo.py
This package provides classes for implementing shipping delays.
"""

_hermes_svn_id_="$Id: delayinfo.py 948 2012-05-04 01:52:22Z welling $"

import types

from SimPy.Simulation  import *
#from SimPy.SimulationTrace  import *
#from SimPy.SimulationGUIDebug import *

import constants as C
import globals as G
import csv_tools
import warehouse
import storagetypes
import trucktypes
import peopletypes
import util
import random

class DelayInfo:
    def __init__(self, userInput, rec, sim):
        self.d= {}
        for field in ('PickupDelayFrequency',
                      'PickupDelayMagnitude',
                      'PickupDelaySigma',
                      'PickupDelayReorder',
                      'DeliveryDelayFrequency',
                      'DeliveryDelayMagnitude',
                      'DeliveryDelaySigma'):
            val = userInput[field.lower()]
            if rec.has_key(field) and rec[field]:
                val = rec[field]
            self.d[field] = val
        
        # ShippingDelaySeed is special:
        if rec.has_key('ShippingDelaySeed') and rec['ShippingDelaySeed']:
            self.d['ShippingDelayRNG'] = random.Random()
            self.d['ShippingDelayRNG'].seed(rec['ShippingDelaySeed'])
        elif userInput['shippingdelayseed']:
            if not hasattr(sim, 'defaultShippingDelayRNG'):
                sim.defaultShippingDelayRNG = random.Random()
                sim.defaultShippingDelayRNG.seed(userInput['shippingdelayseed'])
            self.d['ShippingDelayRNG'] = sim.defaultShippingDelayRNG
        else:
            self.d['ShippingDelayRNG'] = sim.rndm

    def valid(self):
        return ((self.d['PickupDelayFrequency'] and 
                 self.d['PickupDelayMagnitude']) or
                (self.d['DeliveryDelayFrequency'] and
                 self.d['DeliveryDelayMagnitude']))

    def getPickupDelay(self):
        if self.d['PickupDelayFrequency']:
            freq = self.d['PickupDelayFrequency']
            mag = self.d['PickupDelayMagnitude']
            sigma = self.d['PickupDelaySigma']
            rndm = self.d['ShippingDelayRNG']
            if rndm.random() < freq:
                if sigma:
                    delay = rndm.normalvariate(mag,sigma)
                else:
                    delay = rndm.random() * mag
                if delay < 0:
                    delay = 0.0
                return delay
            else:
                return 0.0
    
    def getDeliveryDelay(self):
        if self.d['DeliveryDelayFrequency']:
            freq = self.d['DeliveryDelayFrequency']
            mag = self.d['DeliveryDelayMagnitude']
            sigma = self.d['DeliveryDelaySigma']
            rndm = self.d['ShippingDelayRNG']
            if rndm.random() < freq:
                if sigma:
                    delay = rndm.normalvariate(mag,sigma)
                else:
                    delay = rndm.random() * mag
                if delay < 0:
                    delay = 0.0
                return delay
            else:
                return 0.0
        