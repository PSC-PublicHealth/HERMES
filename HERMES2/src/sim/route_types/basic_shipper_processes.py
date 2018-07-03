#!/usr/bin/env python


__doc__=""" basic_shipping_processes.py
This module contains the shipping processes to implement a Manifest Shipping Process
"""

import ipath
import weakref
import sys,os,string


from SimPy.Simulation import *

### HERMES imports
import abstractbaseclasses
import packagingmodel
import storagemodel

from util import logDebug, logVerbose

import warehouse
from route_types.create_travel_generator import createTravelGenerator

class ShipperProcess(SimPy.Simulation.Process, abstractbaseclasses.UnicodeSupport):
    def __init__(self,fromWarehouse,transitChain,interval,
                 orderPendingLifetime,shipPriority,startupLatency=0.0,
                 truckType=None,name=None, delayInfo=None):
        """
        format of transitChain is:
        [(triptime,warehouse,conditions), 
         (triptime,warehouse,conditions),
         ...]
         
         where 'conditions' is optional (in which case the tuple has only 2
         elements and the condition "normal" is assumed). The final element of
         the list should be a tuple representing the trip from the last client
         warehouse back to the supplier (fromWarehouse).  As a backward
         compatibility feature, if this last tuple is missing a rather lame
         version is created.
        """
        if name is None: name= "ShipperProcess_%s"%fromWarehouse.name
        Process.__init__(self, name=name, sim=fromWarehouse.sim)
        if interval<1.0:
            raise RuntimeError("ShipperProcess %s has cycle time of less than a day- probably not what you wanted"%\
                               name)
        if startupLatency<0.0:
            raise RuntimeError("ShipperProcess %s has a negative startup latency"%startupLatency)
        self.fromW= fromWarehouse
        self.transitChain= transitChain[:]
        # test whether the return trip is coded in the transit chain, and if not, add one
        # based on the very first leg of the chain
        if self.transitChain[-1][1] != fromWarehouse:
            if len(self.transitChain[0]) == 3:
                self.transitChain += [(self.transitChain[0][0], fromWarehouse, self.transitChain[0][2])]
            else:
                self.transitChain += [(self.transitChain[0][0], fromWarehouse)]                
        self.interval= interval
        self.startupLatency= startupLatency
        self.shipPriority= shipPriority
        self.orderPendingLifetime= orderPendingLifetime
        if truckType is None:
            self.truckType=self.sim.trucktypes.getTypeByName("default")
        else:
            self.truckType= truckType
        self.delayInfo = delayInfo
        self.noteHolder= None
        self.nextWakeTime= startupLatency
        self.packagingModel = packagingmodel.DummyPackagingModel() # to be replaced later
        self.storageModel = storagemodel.DummyStorageModel() # to be replaced later
        self.perDiemModel = None
        fromWarehouse.sim.processWeakRefs.append( weakref.ref(self) )

    def setPerDiemModel(self, perDiemModel):
        self.perDiemModel = perDiemModel

    def getPerDiemModel(self):
        return self.perDiemModel

    def finishBuild(self, szFunc):
        """
        This method should be called after the shipping network has been assembled.
        It allows the ShipperProcess to precalculate quantities that depend on information
        from elsewhere in the network.
        
        szFunc has the signature:
    
          shipSizeVialsVC= szFunc(fromWH,toWH,shipIntervalDays)

        """
        pMMM = packagingmodel.PackagingModelMergerModel(self.sim)
        pMMM.addUpstreamPackagingModel(self.fromW.getPackagingModel())
        for tripTime,wh,conditions in self.transitChain:
            if wh != self.fromW: pMMM.addDownstreamPackagingModel(wh.getPackagingModel())
        self.packagingModel = pMMM.getNetPackagingModel()
        self.storageModel = self.fromW.getStorageModel()
        
    def setNoteHolder(self,noteHolder):
        self.noteHolder= noteHolder
    def getNoteHolder(self):
        return self.noteHolder
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
            for num,tpl in enumerate(self.transitChain):
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
                    if num == len(self.transitChain) - 2:
                        stepList.append(('alldeliver',(w,vc,self.interval)))
                    else:
                        stepList.append(('deliver',(w,vc,self.interval)))
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
        return "<ShipperProcess(%s,%s,%g)>"%\
            (repr(self.fromW),repr(self.transitChain),self.interval)
    def __str__(self):
        return "<ShipperProcess(%s,%s,%s,%g)>"%\
            (self.fromW.name,str(self.transitChain),self.interval)
            
class ScheduledShipment(Process, abstractbaseclasses.UnicodeSupport):
    def __init__(self,fromWarehouse,toWarehouse,interval,shipVC,
                 startupLatency=0.0,name=None):
        """
        The shipping interval and startupLatency are in days.
        shipVC should be a VaccineCollection giving the quantity to ship,
         or None, in which case the quantity is calculated after network
         assembly by finishBuild().
        """
        if name is None: 
            name="ScheduledShipment_%s_%s"%(fromWarehouse.name,toWarehouse.name)
        Process.__init__(self, name=name, sim=fromWarehouse.sim)
        if interval<1.0:
            raise RuntimeError("ScheduledShipment %s has cycle time of less than a day- probably not what you wanted"%\
                               name)
        if startupLatency<0.0:
            raise RuntimeError("ScheduledShipment %s has a negative startup latency"%startupLatency)
        self.fromW= fromWarehouse
        self.toW= toWarehouse
        self.interval= interval
        self.shipVC= shipVC
        self.startupLatency= startupLatency
        #toWarehouse.addSupplier(fromWarehouse,{"Type":"push"})
        #fromWarehouse.addClient(toWarehouse)
        fromWarehouse.sim.processWeakRefs.append( weakref.ref(self) )

    def finishBuild(self,szFunc):
        """
        This method should be called after the shipping network has been assembled.
        It allows the ScheduledShipment to precalculate quantities that depend on information
        from elsewhere in the network.
        
        szFunc has the signature:
    
          shipSizeVialsVC= szFunc(fromWH,toWH,shipIntervalDays,timeNow)
          
        As used by this class, szFunc is called once with timeNow= 0.0 at the beginning of simulation.

        """
        if self.shipVC is None and szFunc is not None:
            totalShipVC= szFunc(self.fromW,self.toW,self.interval,self.sim.now())
            fVC,cVC,wVC= self.toW.calculateStorageFillRatios(totalShipVC, assumeEmpty=False)
            fillVC= fVC+cVC+wVC
            scaledShipVC= totalShipVC*fillVC
            scaledShipVC.roundDown()
            self.shipVC= scaledShipVC

    def run(self):
        if self.startupLatency>0.0:
            yield hold,self,self.startupLatency
        while True:
            if self.shipVC is None:
                raise RuntimeError("ScheduledShipment %s to %s: time to ship but shipVC has not been set",
                                   (self.fromW.name,self.toW.name))
            else:
                self.fromW.addPendingShipment(self.toW, self.shipVC)
                logVerbose(self.sim,"%s requesting %s at %g"%(self.bName,self.shipVC,self.sim.now()))
            yield hold,self,self.interval
    def setShipVC(self,shipVC):
        self.shipVC= shipVC
    def __repr__(self):
        return "<ScheduledShipment(%s,%s,%f,%s)>"%\
            (self.fromW.name,self.toW.name,self.interval,repr(self.shipVC))
    def __str__(self): 
        return "<ScheduledShipment(%s,%s)>"%(self.fromW.name,self.toW.name)

class ScheduledVariableSizeShipment(Process,abstractbaseclasses.UnicodeSupport):
    def __init__(self,fromWarehouse,toWarehouse,interval,quantityFunction,
                 startupLatency=0.0,name=None):
        """
        quantityFunction is called every 'interval' days and produces a
        VaccineCollection giving the size of the order.  Its signature is:

          vaccineCollection quantityFunction(fromWarehouse, toWarehouse, shipInterval, timeNow)
            
        szFunc has the signature:
    
          shipSizeVialsVC= szFunc(fromWH,toWH,shipIntervalDays,timeNow)

        szFunc must impose limits due to available storage space, since the shipment
        size will depend on supplies already on hand and this class doesn't have
        that information.
        """
        if name is None:
            name= "ScheduledVariableSizeShipment_%s_%s"%(fromWarehouse.name,toWarehouse.name)
        Process.__init__(self,name=name, sim=fromWarehouse.sim)
        if interval<1.0:
            raise RuntimeError("ScheduledVariableSizeShipment %s has cycle time of less than a day- probably not what you wanted"%\
                               name)
        if startupLatency<0.0:
            raise RuntimeError("ScheduledVariableSizeShipment %s has a negative startup latency"%startupLatency)
        self.fromW= fromWarehouse
        self.toW= toWarehouse
        self.interval= interval
        self.quantityFunction= quantityFunction
        self.startupLatency= startupLatency
        #toWarehouse.addSupplier(fromWarehouse)
        #fromWarehouse.addClient(toWarehouse)
        fromWarehouse.sim.processWeakRefs.append( weakref.ref(self) )
    def finishBuild(self, szFunc):
        """
        This method should be called after the shipping network has been assembled.
        It allows the ScheduledVariableSizeShipment to precalculate quantities that 
        depend on information from elsewhere in the network.
        
        szFunc has the signature:
    
          shipSizeVialsVC= szFunc(fromWH,toWH,shipIntervalDays,timeNow)
        """
        if self.quantityFunction is None:
            self.quantityFunction= szFunc
    def run(self):
        if self.startupLatency>0.0:
            yield hold,self,self.startupLatency
        while True:
            shipVC= self.quantityFunction(self.fromW,self.toW,self.interval,self.sim.now())
            shipVC.floorZero()
            shipVC.roundDown()
            fullVC = shipVC
            self.fromW.addPendingShipment(self.toW,fullVC)
            logVerbose(self.sim,"%s requesting %s at %g"%(self.bName,fullVC,self.sim.now()))
            yield hold,self,self.interval
    def __repr__(self):
        return "<ScheduledVariableSizeShipment(%s,%s,%f)>"%(self.fromW.name,self.toW.name,self.interval)
    def __str__(self): 
        return "<ScheduledVariableSizeShipment(%s,%s)>"%(self.fromW.name,self.toW.name)
