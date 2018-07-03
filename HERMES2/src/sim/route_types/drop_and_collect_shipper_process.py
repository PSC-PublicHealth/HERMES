#!/usr/bin/env python


__doc__=""" basic_shipping_processes.py
This module contains the shipping processes to implement a Manifest Shipping Process
"""

import ipath
import sys,os,string

from SimPy.Simulation import *

### HERMES imports
import abstractbaseclasses

from util import logDebug, logVerbose

import warehouse
from route_types.basic_shipper_processes import ShipperProcess
from route_types.create_travel_generator import createTravelGenerator

class DropAndCollectShipperProcess(ShipperProcess, abstractbaseclasses.UnicodeSupport):
    def __init__(self,fromWarehouse,transitChain,interval,
                 orderPendingLifetime,shipPriority,startupLatency=0.0,
                 truckType=None,name=None, delayInfo=None):
        """
        This differs from a normal ShipperProcess in that each client is visited twice-
        once to drop off and once to pick up recycling.  The transit chain must include
        both visits explicitly (because timing and order need to be specified), and is
        checked to verify that each client is visited exactly twice.  The first visit is
        a delivery only; no recycling is picked up.  The second visit is recycling only;
        no delivery is made.  The truck is assumed to start at the supplier warehouse.
        """
        if name is None: name= "DropAndCollectShipperProcess_%s"%fromWarehouse.name
        if name is None: name= "AskOnDeliveryShipperProcess_%s"%fromWarehouse.name
        # Verify that all locations but the last is visited twice, and the last (the supplier) is
        # visited once.
        visitCounts = {}
        for tripTime,cl,conditions in transitChain[:-1]:
            if cl in visitCounts:
                visitCounts[cl] += 1
            else:
                visitCounts[cl] = 1
        for cl, visits in visitCounts.items():
            if visits != 2: 
                raise RuntimeError("%s (and possibly others) is visited only once in drop-and-collect route %s"%\
                                   (cl.name,name))
        tripTime,cl,conditions = transitChain[-1]
        if cl != fromWarehouse: 
            raise RuntimeError("drop-and-collect route %s should end at its supplier warehouse %s"%\
                               (bName,fromWarehouse.name))
        if cl in visitCounts:
            raise RuntimeError("drop-and-collect route %s visits its supplier %s"%(bName,cl.name))
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
            visited = set()
            stepList = [('load', (self.fromW, self.packagingModel, self.storageModel, totalVC))]
            nClients = (len(self.transitChain)-1)/2
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
                elif w in visited:
                    # Second visit; pick up recycling
                    stepList.append(('move',(t,upstreamW,w,conditions)))
                    stepList.append( ('recycle', (w,self.packagingModel,self.storageModel)) )
                else:
                    # First visit; drop off
                    visited.add(w)
                    stepList.append(('move',(t,upstreamW,w,conditions)))
                    vc= self.fromW.getAndForgetPendingShipment(w)
                    #print "%s: %s requests %s"%(self.bName,w.bName,[(v.bName,n) for v,n in vc.items() if n>0.0])
                    totalVC += vc
                    if len(visited) == nClients:
                        # Last client
                        stepList.append(('allmarkanddeliver',(w,vc,self.interval)))
                    else:
                        stepList.append(('markanddeliver',(w,vc,self.interval)))
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
