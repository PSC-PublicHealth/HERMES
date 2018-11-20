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


__doc__=""" ask_on_delivery_shipping_processes.py
This module contains the shipping processes to implement a "topping off" route
"""

import ipath
import weakref
import sys,os,string

from SimPy.Simulation import *

### HERMES imports
from util import logDebug, logVerbose

import warehouse
from route_types.basic_shipper_processes import ShipperProcess
from route_types.create_travel_generator import createTravelGenerator

class AskOnDeliveryShipperProcess(ShipperProcess):
    def __init__(self,fromWarehouse,transitChain,interval,
                 orderPendingLifetime,shipPriority,startupLatency=0.0,
                 truckType=None,name=None, delayInfo=None):
        """
        This is very much like a normal ShipperProcess, but the delivery size is
        checked at each client via Model.getDeliverySize(), and any leftovers are
        returned to the supplier.
        """
        if name is None: name= "AskOnDeliveryShipperProcess_%s"%fromWarehouse.name
        ShipperProcess.__init__(self,fromWarehouse,transitChain,interval,
                                orderPendingLifetime,shipPriority,startupLatency=startupLatency,
                                truckType=truckType, name=name, delayInfo=delayInfo)
    def run(self):
        if self.startupLatency>0.0:
            yield hold,self,self.startupLatency
        logVerbose(self.sim,"%s: latency %f, interval %f; my transit chain is %s"%(self.bName,self.startupLatency,self.interval,self.transitChain))
        while True:
            self.nextWakeTime += self.interval

            # simulate a truck delay
            if self.delayInfo is not None:
                delay= self.delayInfo.getPickupDelay()
                if delay > 0.0:
                    logDebug(self.sim,"%s: shipment is delayed by %f days"%(self.bName, delay))
                    yield hold, self, delay

            logDebug(self.sim,"%s: my transit chain is %s"%(self.bName,self.transitChain))   
                      
            totalVC= self.sim.shippables.getCollection()
            upstreamW = self.fromW
            stepList = [('load', (self.fromW, self.packagingModel, self.storageModel, totalVC))]
            for tpl in self.transitChain:
                if len(tpl) == 3:
                    t,w,conditions = tpl
                else:
                    t,w = tpl
                    conditions = 'normal'
                if w == self.fromW:
                    # last step of the trip
                    stepList += [('move',(t,upstreamW,w,conditions)),
                                 ('unload',(w,)),
                                 ('finish',(w,self.fromW))]
                else:
                    stepList.append(('move',(t,upstreamW,w,conditions)))
                    vc= self.fromW.getAndForgetPendingShipment(w)
                    #print "%s: %s requests %s"%(self.bName,w.bName,[(v.bName,n) for v,n in vc.items() if n>0.0])
                    totalVC += vc
                    stepList.append(('askanddeliver',(w,vc,self.interval)))
                    stepList.append( ('recycle', (w,self.packagingModel,self.storageModel)) )
                upstreamW = w
                      
            if totalVC.totalCount()>0:
                travelGen= createTravelGenerator(self.bName, stepList, self.truckType, 
                                                 self.delayInfo, self)
                # This should maybe be more like the code block from PEP380: 
                # http://www.python.org/dev/peps/pep-0380/#id13
                for val in travelGen: yield val
            else:
                logVerbose(self.sim,"%s: no order to ship at %f"%(self.bName,self.sim.now()))
            while self.nextWakeTime <= self.sim.now(): self.nextWakeTime += self.interval
            yield hold,self,self.nextWakeTime-self.sim.now()
                
    def __repr__(self):
        return "<AskOnDeliveryShipperProcess(%s,%s,%g)>"%\
            (repr(self.fromW),repr(self.transitChain),self.interval)
    def __str__(self):
        return "<AskOnDeliveryShipperProcess(%s,%s,%s,%g)>"%\
            (self.fromW.name,str(self.transitChain),self.interval)
