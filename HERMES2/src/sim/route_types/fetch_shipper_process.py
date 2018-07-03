#!/usr/bin/env python


__doc__=""" fetch_shipping_processes.py
This module contains the shipping processes to implement a route where the vehicle starts at the client
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

class FetchShipperProcess(ShipperProcess):
    def __init__(self,fromWarehouse,transitChain,interval,
                 orderPendingLifetime,shipPriority,startupLatency=0.0,
                 truckType=None,name=None, delayInfo=None):
        """
        A FetchShipperProcess is like a ShipperProcess, except that the trip starts at 
        the first client warehouse and then travels to the supplier as the first leg.
        
        fromWarehouse is the first client warehouse, not the supplier; it is there that
        the trip starts.  The format of transitChain is:
        
            [(triptime,warehouse,conditions), 
             (triptime,warehouse,conditions),
             ...]
         
        where in this case the warehouse specified in the first record will be the supplier
        and the warehouse specified in the last record will be fromWarehouse, the first client.
        Typically these routes will have only one client and thus be two-
        leg trips, but inserting additional clients is supported.  
         
        In transitChain, 'conditions' is optional (in which case the tuple has only 2
        elements and the condition "normal" is assumed).
        """
        if name is None: name= "FetchShipperProcess_%s"%fromWarehouse.name
        ShipperProcess.__init__(self, fromWarehouse, transitChain, interval,
                                orderPendingLifetime, shipPriority, startupLatency,
                                truckType, name, delayInfo)

        # un-do mods to the transit chain performed by ShipperProcess.__init__()
        self.transitChain= transitChain[:]
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

            supplierW= self.transitChain[0][1]
            totalVC= self.sim.shippables.getCollection()
            stepList = [('gettruck', (self.fromW,)),
                        ('recycle',(self.fromW,self.packagingModel,self.storageModel)),
                        ]
            if len(self.transitChain[0]) == 3:
                transitTime, supplierW, conditions = self.transitChain[0]
            else:
                transitTime, supplierW = self.transitChain[0]
                conditions = 'normal'
            stepList += [('move',(transitTime,self.fromW,supplierW,conditions)),
                         ('unload',(supplierW,)),
                         ('loadexistingtruck',(supplierW, self.packagingModel, self.storageModel, totalVC))]
            prevW = supplierW
            for tpl in self.transitChain[1:-1]:
                if len(tpl) == 3:
                    t,w,conditions = tpl
                else:
                    t,w = tpl
                    conditions = 'normal'
                stepList.append(('move',(t,prevW,w,conditions)))
                vc= supplierW.getAndForgetPendingShipment(w)
                totalVC += vc
                stepList.append(('deliver',(w,vc,self.interval)))
                stepList.append( ('recycle', (w,self.packagingModel,self.storageModel)) )
                prevW = w
            if len(self.transitChain[-1]) == 3:
                transitTime, finalW, conditions = self.transitChain[-1]
            else:
                transitTime, finalW = self.transitChain[-1]
                conditions = 'normal'
            assert finalW==self.fromW, "Internal error: %s is not a loop"%self.name
            vc= supplierW.getAndForgetPendingShipment(finalW)
            totalVC += vc
            stepList += [('move',(transitTime,prevW,finalW,conditions)),
                         ('alldeliver',(finalW,vc,self.interval)),
                         ('unload',(finalW,)),
                         ('finish',(finalW,self.fromW))
                         ]
                      
            if totalVC.totalCount()>0:
                travelGen= createTravelGenerator(self.bName, stepList, self.truckType, self.delayInfo, self)
                # This should maybe be more like the code block from PEP380: 
                # http://www.python.org/dev/peps/pep-0380/#id13
                for val in travelGen: yield val
            else:
                logVerbose(self.sim,"%s: no order to ship at %f"%(self.bName,self.sim.now()))
            while self.nextWakeTime <= self.sim.now(): self.nextWakeTime += self.interval
            yield hold,self,self.nextWakeTime-self.sim.now()
                
    def __repr__(self):
        return "<FetchShipperProcess(%s,%s,%g)>"%\
            (repr(self.fromW),repr(self.transitChain),self.interval)
    def __str__(self):
        return "<FetchShipperProcess(%s,%s,%s,%g)>"%\
            (self.fromW.name,str(self.transitChain),self.interval)
