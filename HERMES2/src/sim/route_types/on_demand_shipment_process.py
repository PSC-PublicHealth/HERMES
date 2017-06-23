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


__doc__=""" on_demand_shipment_process.py
This module contains the shipping processes to implement on demand shipments for ordering when a threshold gets low
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

class OnDemandShipment(Process, abstractbaseclasses.UnicodeSupport):
    def __init__(self,fromWarehouse,toWarehouse,routeName,thresholdFunction,
                 quantityFunction,transitTime,orderPendingLifetime,
                 pullMeanFrequencyDays,shipPriority,startupLatency=0.0,
                 truckType=None,name=None, 
                 minimumDaysBetweenShipments=0.0,
                 delayInfo=None, conditions="normal"):
        """
        thresholdFunction and quantityFunction have the signatures:
        
        vaccineCollection= thresholdFunction(toWarehouse,pullMeanFrequency)
        vaccineCollection= quantityFunction(fromWarehouse,toWarehouse,routeName,
                                            pullMeanFrequencyDays,timeNow)
        
        The first function is used after the shipping network has been built
        to construct a VaccineCollection giving the reorder threshold points 
        for the given warehouse.  The second is used repeatedly to calculate
        the shipment sizes between the given warehouses.

        transitTime may be single scalar time which will apply to both legs
        of the trip, or a tuple (timeOutboundTrip, timeReturnTrip that specify
        separate times for the two halves of the trip.
        """
        if name is None:
            name= "OnDemandShipment_%s_%s"%(fromWarehouse.name,toWarehouse.name)
        Process.__init__(self, name=name, sim=fromWarehouse.sim)
        if startupLatency<0.0:
            raise RuntimeError("OnDemandShipment %s has a negative startup latency"%startupLatency)
        self.fromW= fromWarehouse
        self.toW= toWarehouse
        self.routeName = routeName
        self.thresholdFunc= thresholdFunction
        self.thresholdVC= None
        self.quantityFunction= quantityFunction
        self.transitTime= transitTime
        self.orderPendingLifetime= orderPendingLifetime
        self.pullMeanFrequency= pullMeanFrequencyDays
        self.shipPriority= shipPriority
        if truckType is None:
            self.truckType=self.sim.trucktypes.getTypeByName("default")
        else:
            self.truckType= truckType
        self.conditions= conditions
        #toWarehouse.addSupplier(fromWarehouse,{'Type':'pull',
        #                                       'TruckType':truckType,
        #                                       'Conditions':conditions})
        #fromWarehouse.addClient(toWarehouse)
        self.warningEvent= None
        self.nextAllowedDeparture= startupLatency
        self.minimumDaysBetweenShipments= minimumDaysBetweenShipments
        self.delayInfo = delayInfo
        self.noteHolder= None
        self.packagingModel = packagingmodel.DummyPackagingModel()
        self.storageModel = storagemodel.DummyStorageModel()
        self.first = True
        self.perDiemModel = None
        fromWarehouse.sim.processWeakRefs.append( weakref.ref(self) )

    def setPerDiemModel(self, perDiemModel):
        self.perDiemModel = perDiemModel

    def getPerDiemModel(self):
        return self.perDiemModel

    def finishBuild(self, szFunc):
        """
        This method should be called after the shipping network has been assembled.
        It allows the OnDemandShipment to precalculate quantities that depend on information
        from elsewhere in the network.
        
        szFunc has the signature:
    
          shipSizeVialsVC= szFunc(fromWH,toWH,shipIntervalDays,pullMeanFrequencyDays)

        """
        event= None
        thresholdVC= self.thresholdFunc(self.toW, self.pullMeanFrequency)
        print "ThresholdVC = {0}".format(thresholdVC)
        for v,n in thresholdVC.getTupleList():
            if n>0.0:
                event= self.toW.setLowThresholdAndGetEvent(v,n)
        if event is None:
            raise RuntimeError("%s shipping threshold calculation yielded nothing"%self.bName)
        self.warningEvent= event
        pMMM = packagingmodel.PackagingModelMergerModel(self.sim)
        pMMM.addUpstreamPackagingModel(self.fromW.getPackagingModel())
        pMMM.addDownstreamPackagingModel(self.toW.getPackagingModel())
        self.packagingModel = pMMM.getNetPackagingModel()
        self.storageModel = self.fromW.getStorageModel()
    def setNoteHolder(self,noteHolder):
        self.noteHolder= noteHolder
    def getNoteHolder(self):
        return self.noteHolder
    def run(self):
        self.truck= None
        if self.nextAllowedDeparture>0.0:
            yield hold,self,self.nextAllowedDeparture
        while True:
            # We want to start by doing a shipment, or the downstream
            # warehouse will just sit at 0.

            totalVC= self.quantityFunction(self.fromW, self.toW, self.routeName,
                                           self.pullMeanFrequency,
                                           self.sim.now())
            if totalVC.totalCount()>0:
                # see if our truck is delayed
                if self.delayInfo is not None:
                    delay= self.delayInfo.getPickupDelay()
                    if delay > 0.0:
                        logDebug(self.sim,"%s: shipment is delayed by %f days"%(self.bName, delay))
                        yield hold, self, delay
                        
                        if self.delayInfo.d['PickupDelayReorder']:
                            # this is completely lame but if someone places an order
                            # then the truck is delayed and then when they are asked
                            # what size of an order to make they order nothing we're
                            # going to give them what they originally wanted.  Otherwise
                            # we need to jump through some impressive hoops unless we
                            # wish to go about refactoring this code
                            newTotalVC= self.quantityFunction(self.fromW, self.toW,
                                                              self.routeName,
                                                              self.pullMeanFrequency,
                                                              self.sim.now())
                            if newTotalVC.totalCount > 0:
                                totalVC = newTotalVC

                # We're leaving now; when is the next permitted departure?
                self.nextAllowedDeparture= self.sim.now()+self.minimumDaysBetweenShipments
                
                # Let's cancel the trip if the supplier doesn't have any of what's needed
                if self.fromW.gotAnyOfThese(self.toW.lowStockSet) or self.first == True:
                    self.first = False
                    if isinstance(self.transitTime,types.TupleType):
                        toTime,froTime = self.transitTime
                    else:
                        toTime = froTime = self.transitTime
                        
                    # Make one or more trips.  In normal operation only one trip will be required, but 
                    # additional trips may be executed if the available shipping volume is too low to raise
                    # an otherwise-available shippable above its trigger threshold.
                    stepList = [('load', (self.fromW, self.packagingModel, self.storageModel, totalVC)),
                                ('move',(toTime,self.fromW,self.toW,self.conditions)),
                                ('alldeliver',(self.toW,totalVC,self.pullMeanFrequency)),
                                ('recycle',(self.toW,self.packagingModel, self.storageModel)),
                                ('move',(froTime,self.toW,self.fromW,self.conditions)),
                                ('unload',(self.fromW,)),
                                ('finish',(self.fromW,self.fromW))
                                ]
        
                    travelGen= createTravelGenerator(self.bName, stepList, self.truckType, self.delayInfo, self)
                    # This should maybe be more like the code block from PEP380: 
                    # http://www.python.org/dev/peps/pep-0380/#id13
                    for val in travelGen: yield val
                else:
                    logVerbose(self.sim,u"{0}: supplier has no needed stock at {1}".format(self.name,self.sim.now()))
                    
            else:
                logVerbose(self.sim,u"{0}:quantity to order is zero at {1}".format(self.name,self.sim.now()))

            extraDelay = 0.0
            if self.toW.lowStockSet:
                # Some shippables are below the trigger threshold- run another trip as soon as allowed.
                # By triggering the event and then waiting on it (which returns immediately), we 
                # clear any pending event and continue.
                logDebug(self.sim,u"{0} still triggered at {1}".format(self.name,self.sim.now()))
                if self.minimumDaysBetweenShipments < 1.0:
                    extraDelay = 1.0 # to keep from cycling forever if the supplier has no stock
                self.warningEvent.signal()
                yield waitevent,self,self.warningEvent
            else:
                # The trigger threshold mechanism will initiate a new trip when needed                
                logVerbose(self.sim,u"{0}: enters waitEvent at {1}".format(self.name,self.sim.now()))
                yield waitevent,self,self.warningEvent
                logVerbose(self.sim,u"{0}: received trigger event at {1}".format(self.name,self.sim.now()))
                
            # Short pause to keep shipping events triggered by upstream
            # deliveries acting through attemptRestock() from piling up 
            # at the same 'moment'.  If we've gotten a request before the
            # next allowed departure, wait until then.
            delay= max(self.sim.rndm.gauss(0.1,0.025)+extraDelay, warehouse.Warehouse.shortDelayTime)
            if self.nextAllowedDeparture - self.sim.now() > 0.0:
                delay += self.nextAllowedDeparture-self.sim.now()
            logDebug(self.sim,u"{0} pausing {1} at {2}".format(self.name,delay,self.sim.now()))
            yield hold,self,delay
            logVerbose(self.sim,u"{0} finished waiting; shipping at {1}".format(self.name,self.sim.now()))

    def __repr__(self):
        return u"<OnDemandShipment({0},{1},{2},{3},{4},{5},{6})>".format (self.fromW.name,
                                                                          self.toW.name,
                                                                          self.thresholdVC,self.quantityFunction,self.transitTime,
             self.pullMeanFrequency,self.minimumDaysBetweenShipments)
    def __str__(self): 
        return u"<OnDemandShipment({0},{1})>".format(self.fromW.name,self.toW.name)

class FetchOnDemandShipment(OnDemandShipment):
    def __init__(self,supplierWarehouse,clientWarehouse,routeName,
                 thresholdFunction,
                 quantityFunction,transitTime,orderPendingLifetime,
                 pullMeanFrequencyDays,shipPriority,startupLatency=0.0,
                 truckType=None,name=None, 
                 minimumDaysBetweenShipments=0.0,
                 delayInfo=None, conditions="normal"):
        """
        This shipping pattern is like that of OnDemandShipment, except that
        the truck starts at and returns to clientWarehouse, stopping at supplierWarehouse
        for supplies.
        
        thresholdFunction and quantityFunction have the signatures:
        
        vaccineCollection= thresholdFunction(toWarehouse,pullMeanFrequency)
        vaccineCollection= quantityFunction(fromWarehouse,toWarehouse,routeName,
                                            pullMeanFrequencyDays,timeNow)
        
        The first function is used after the shipping network has been built
        to construct a VaccineCollection giving the reorder threshold points 
        for the given warehouse.  The second is used repeatedly to calculate
        the shipment sizes between the given warehouses.


        transitTime may be single scalar time which will apply to both legs
        of the trip, or a tuple (timeOutboundTrip, timeReturnTrip that specify
        separate times for the two halves of the trip.
        """
        if name is None:
            name= "FetchOnDemandShipment_%s_%s"%(clientWarehouse.name,supplierWarehouse.name)
        OnDemandShipment.__init__(self, supplierWarehouse, clientWarehouse, routeName,
                                  thresholdFunction,
                                  quantityFunction, transitTime, orderPendingLifetime,
                                  pullMeanFrequencyDays, shipPriority, startupLatency,
                                  truckType, name, minimumDaysBetweenShipments,
                                  delayInfo, conditions)
        self.first = True
    def run(self):
        clientW = self.toW
        supplierW = self.fromW
        if self.nextAllowedDeparture>0.0:
            yield hold,self,self.nextAllowedDeparture
        while True:
            # We want to start by doing a shipment, or the downstream
            # warehouse will just sit at 0.
            totalVC= self.quantityFunction(self.fromW, self.toW,
                                           self.routeName,
                                           self.pullMeanFrequency,
                                           self.sim.now())
            if totalVC.totalCount()>0:
                
                # simulate a truck delay
                if self.delayInfo is not None:
                    delay= self.delayInfo.getPickupDelay()
                    if delay > 0.0:
                        logDebug(self.sim,"%s: shipment is delayed by %f days"%(self.bName, delay))

                        yield hold, self, delay
                        if self.delayInfo.d['PickupDelayReorder']:
                            # this is completely lame but if someone places an order
                            # then the truck is delayed and then when they are asked
                            # what size of an order to make they order nothing we're
                            # going to give them what they originally wanted.  Otherwise
                            # we need to jump through some impressive hoops unless we
                            # wish to go about refactoring this code
                            newTotalVC= self.quantityFunction(self.fromW, self.toW,
                                                              self.routeName,
                                                              self.pullMeanFrequency,
                                                              self.sim.now())
                            if newTotalVC.totalCount > 0:
                                totalVC = newTotalVC

                # We're leaving now; when is the next permitted departure?
                self.nextAllowedDeparture= self.sim.now()+self.minimumDaysBetweenShipments

                # Let's cancel the trip if the supplier doesn't have any of what's needed
                if self.fromW.gotAnyOfThese(self.toW.lowStockSet) or self.first == True:
                    self.first = False
                    if isinstance(self.transitTime,types.TupleType):
                        toTime,froTime = self.transitTime
                    else:
                        toTime = froTime = self.transitTime
    
                    # Make one or more trips.  In normal operation only one trip will be required, but 
                    # additional trips may be executed if the available shipping volume is too low to raise
                    # an otherwise-available shippable above its trigger threshold.
                    stepList = [('gettruck', (clientW,)),
                                ('recycle',(clientW,self.packagingModel,self.storageModel)),
                                ('move',(toTime,clientW,supplierW,self.conditions)),
                                ('unload',(supplierW,)),
                                ('loadexistingtruck',(supplierW, self.packagingModel, self.storageModel, totalVC)),
                                ('move',(froTime,supplierW,clientW,self.conditions)),
                                ('alldeliver',(clientW,totalVC,self.pullMeanFrequency)),
                                ('unload',(clientW,)),
                                ('finish',(clientW,clientW))
                                ]
        
                    travelGen= createTravelGenerator(self.bName, stepList, self.truckType, self.delayInfo, self)
                    # This should maybe be more like the code block from PEP380: 
                    # http://www.python.org/dev/peps/pep-0380/#id13
                    for val in travelGen: yield val
                else:
                    logVerbose(self.sim,"%s: supplier has no needed stock at %g"%(self.bName,self.sim.now()))
                
            else:
                logVerbose(self.sim,"%s:quantity to order is zero at %g"%(self.bName,self.sim.now()))

            extraDelay = 0.0
            if self.toW.lowStockSet:
                # Some shippables are below the trigger threshold- run another trip as soon as allowed
                # By triggering the event and then waiting on it (which returns immediately), we 
                # clear any pending event and continue.
                logDebug(self.sim,"%s still triggered at %g"%(self.bName,self.sim.now()))
                if self.minimumDaysBetweenShipments < 1.0:
                    extraDelay = 1.0 # to prevent rapid looping if the supplier is stocked out
                self.warningEvent.signal()
                yield waitevent,self,self.warningEvent                
            else:
                # The trigger threshold mechanism will initiate a new trip when needed                
                logVerbose(self.sim,"%s: enters waitEvent at %g"%(self.bName,self.sim.now()))
                yield waitevent,self,self.warningEvent
                logVerbose(self.sim,"%s: received trigger event at %g"%(self.bName,self.sim.now()))
                
            # Short pause to keep shipping events triggered by upstream
            # deliveries acting through attemptRestock() from piling up 
            # at the same 'moment'.  If we've gotten a request before the
            # next allowed departure, wait until then.
            delay= max(self.sim.rndm.gauss(0.1,0.025)+extraDelay, warehouse.Warehouse.shortDelayTime)
            if self.nextAllowedDeparture - self.sim.now() > 0.0:
                delay += self.nextAllowedDeparture-self.sim.now()
            logDebug(self.sim,"%s pausing %g at %g"%(self.bName,delay,self.sim.now()))
            yield hold,self,delay
            logVerbose(self.sim,"%s finished waiting; shipping at %g"%(self.bName,self.sim.now()))

    def __repr__(self):
        return u"<FetchOnDemandShipment({0},{1},{2},{3},{4},{5},{6})>".format(self.fromW.name,self.toW.name,
             self.thresholdVC,self.quantityFunction,self.transitTime,
             self.pullMeanFrequency,self.minimumDaysBetweenShipments)
    def __str__(self): 
        return "<FetchOnDemandShipment(%s,%s)>"%(self.fromW.name,self.toW.name)

class PersistentFetchOnDemandShipment(OnDemandShipment):
    def __init__(self,supplierWarehouse,clientWarehouse,routeName,
                 thresholdFunction,
                 quantityFunction,transitTime,orderPendingLifetime,
                 pullMeanFrequencyDays,shipPriority,startupLatency=0.0,
                 truckType=None,name=None, 
                 minimumDaysBetweenShipments=0.0,
                 delayInfo=None, conditions="normal"):
        """
        This shipping pattern is like that of PersistentOnDemandShipment, except that
        the truck starts at and returns to clientWarehouse, stopping at supplierWarehouse
        for supplies.
        
        thresholdFunction and quantityFunction have the signatures:
        
        vaccineCollection= thresholdFunction(toWarehouse,pullMeanFrequency)
        vaccineCollection= quantityFunction(fromWarehouse,toWarehouse,routeName,
                                            pullMeanFrequencyDays,timeNow)
        
        The first function is used after the shipping network has been built
        to construct a VaccineCollection giving the reorder threshold points 
        for the given warehouse.  The second is used repeatedly to calculate
        the shipment sizes between the given warehouses.


        transitTime may be single scalar time which will apply to both legs
        of the trip, or a tuple (timeOutboundTrip, timeReturnTrip that specify
        separate times for the two halves of the trip.
        """
        if name is None:
            name= u"PersistentFetchOnDemandShipment_{0}_{1}".format(clientWarehouse.name,supplierWarehouse.name)
        OnDemandShipment.__init__(self, supplierWarehouse, clientWarehouse, routeName,
                                  thresholdFunction,
                                  quantityFunction, transitTime, orderPendingLifetime,
                                  pullMeanFrequencyDays, shipPriority, startupLatency,
                                  truckType, name, minimumDaysBetweenShipments,
                                  delayInfo, conditions)
    def run(self):
        clientW = self.toW
        supplierW = self.fromW
        if self.nextAllowedDeparture>0.0:
            yield hold,self,self.nextAllowedDeparture
        while True:
            # We want to start by doing a shipment, or the downstream
            # warehouse will just sit at 0.
            totalVC= self.quantityFunction(self.fromW, self.toW, self.pullMeanFrequency,
                                           self.sim.now())
            if totalVC.totalCount()>0:
                
                # simulate a truck delay
                if self.delayInfo is not None:
                    delay= self.delayInfo.getPickupDelay()
                    if delay > 0.0:
                        logDebug(self.sim,"%s: shipment is delayed by %f days"%(self.bName, delay))

                        yield hold, self, delay
                        if self.delayInfo.d['PickupDelayReorder']:
                            # this is completely lame but if someone places an order
                            # then the truck is delayed and then when they are asked
                            # what size of an order to make they order nothing we're
                            # going to give them what they originally wanted.  Otherwise
                            # we need to jump through some impressive hoops unless we
                            # wish to go about refactoring this code
                            newTotalVC= self.quantityFunction(self.fromW, self.toW,
                                                              self.routeName,
                                                              self.pullMeanFrequency,
                                                              self.sim.now())
                            if newTotalVC.totalCount > 0:
                                totalVC = newTotalVC

                # We're leaving now; when is the next permitted departure?
                self.nextAllowedDeparture= self.sim.now()+self.minimumDaysBetweenShipments

                if isinstance(self.transitTime,types.TupleType):
                    toTime,froTime = self.transitTime
                else:
                    toTime = froTime = self.transitTime

                while True:
                    # Make one or more trips.  In normal operation only one trip will be required, but 
                    # additional trips may be executed if the available shipping volume is too low to raise
                    # an otherwise-available shippable above its trigger threshold.
                    stepList = [('gettruck', (clientW,)),
                                ('recycle',(clientW,self.packagingModel,self.storageModel)),
                                ('move',(toTime,clientW,supplierW,self.conditions)),
                                ('unload',(supplierW,)),
                                ('loadexistingtruck',(supplierW, self.packagingModel, self.storageModel, totalVC)),
                                ('move',(froTime,supplierW,clientW,self.conditions)),
                                ('alldeliver',(clientW,totalVC,self.pullMeanFrequency)),
                                ('unload',(clientW,)),
                                ('finish',(clientW,clientW))
                                ]
        
                    travelGen= createTravelGenerator(self.bName, stepList, self.truckType, self.delayInfo, self)
                    # This should maybe be more like the code block from PEP380: 
                    # http://www.python.org/dev/peps/pep-0380/#id13
                    for val in travelGen: yield val
                
                    if self.toW.lowStockSet and self.fromW.gotAnyOfThese(self.toW.lowStockSet):
                        totalVC= self.quantityFunction(self.fromW, self.toW, self.routeName,
                                                       self.pullMeanFrequency,
                                                       self.sim.now())
                        # And continue for another loop
                    else:
                        break
                
            else:
                logVerbose(self.sim,"%s:quantity to order is zero at %g"%(self.bName,self.sim.now()))
            logVerbose(self.sim,"%s: enters waitEvent at %f"%(self.bName,self.sim.now()))
            yield waitevent,self,self.warningEvent
            # Short pause to keep shipping events triggered by upstream
            # deliveries acting through attemptRestock() from piling up 
            # at the same 'moment'.  If we've gotten a request before the
            # next allowed departure, wait until then.
            delay= max(self.sim.rndm.gauss(0.1,0.025), warehouse.Warehouse.shortDelayTime)
            if self.nextAllowedDeparture - self.sim.now() > 0.0:
                delay += self.nextAllowedDeparture-self.sim.now()
            logDebug(self.sim,"%s received event at %g, pausing %g"%(self.bName,self.sim.now(),delay))
            yield hold,self,delay
            logVerbose(self.sim,"%s received event and waited; shipping at %g"%(self.bName,self.sim.now()))

    def __repr__(self):
        return u"<PersistentFetchOnDemandShipment({0},{1},{2},{3},{4},{5},{6})>".format(self.fromW.name,self.toW.name,
             self.thresholdVC,self.quantityFunction,self.transitTime,
             self.pullMeanFrequency,self.minimumDaysBetweenShipments)
    def __str__(self): 
        return u"<PersistentFetchOnDemandShipment({0},{1})>".format(self.fromW.name,self.toW.name)

class PersistentOnDemandShipment(OnDemandShipment):
    def __init__(self,supplierWarehouse,clientWarehouse,routeName,
                 thresholdFunction,
                 quantityFunction,transitTime,orderPendingLifetime,
                 pullMeanFrequencyDays,shipPriority,startupLatency=0.0,
                 truckType=None,name=None, 
                 minimumDaysBetweenShipments=0.0,
                 delayInfo=None, conditions="normal"):
        """
        This shipping pattern is like that of OnDemandShipment, except that 
        the shipping cycle 'persists' - it will continue to make shipping trips
        until either all shippables have been brought up above their shipping
        trigger thresholds or the supplier has no more of the needed shippables.
        At that point the process goes back to sleep until a trigger threshold
        is crossed, as with OnDemandShipment.  This is intended as a remedy for
        shipments using undersized trucks.
        
        thresholdFunction and quantityFunction have the signatures:
        
        vaccineCollection= thresholdFunction(toWarehouse,pullMeanFrequency)
        vaccineCollection= quantityFunction(fromWarehouse,toWarehouse,routeName,
                                            pullMeanFrequencyDays,timeNow)
        
        The first function is used after the shipping network has been built
        to construct a VaccineCollection giving the reorder threshold points 
        for the given warehouse.  The second is used repeatedly to calculate
        the shipment sizes between the given warehouses.


        transitTime may be single scalar time which will apply to both legs
        of the trip, or a tuple (timeOutboundTrip, timeReturnTrip that specify
        separate times for the two halves of the trip.
        """
        if name is None:
            name= "PersistentOnDemandShipment_%s_%s"%(clientWarehouse.name,supplierWarehouse.name)
        OnDemandShipment.__init__(self, supplierWarehouse, clientWarehouse, routeName,
                                  thresholdFunction,
                                  quantityFunction, transitTime, orderPendingLifetime,
                                  pullMeanFrequencyDays, shipPriority, startupLatency,
                                  truckType, name, minimumDaysBetweenShipments,
                                  delayInfo, conditions)
    def run(self):
        self.truck= None
        if self.nextAllowedDeparture>0.0:
            yield hold,self,self.nextAllowedDeparture
        while True:
            # We want to start by doing a shipment, or the downstream
            # warehouse will just sit at 0.

            totalVC= self.quantityFunction(self.fromW, self.toW,
                                           self.routeName,
                                           self.pullMeanFrequency,
                                           self.sim.now())
            if totalVC.totalCount()>0:
                # see if our truck is delayed
                if self.delayInfo is not None:
                    delay= self.delayInfo.getPickupDelay()
                    if delay > 0.0:
                        logDebug(self.sim,"%s: shipment is delayed by %f days"%(self.bName, delay))
                        yield hold, self, delay
                        
                        if self.delayInfo.d['PickupDelayReorder']:
                            # this is completely lame but if someone places an order
                            # then the truck is delayed and then when they are asked
                            # what size of an order to make they order nothing we're
                            # going to give them what they originally wanted.  Otherwise
                            # we need to jump through some impressive hoops unless we
                            # wish to go about refactoring this code
                            newTotalVC= self.quantityFunction(self.fromW, self.toW,
                                                              self.routeName,
                                                              self.pullMeanFrequency,
                                                              self.sim.now())
                            if newTotalVC.totalCount > 0:
                                totalVC = newTotalVC

                # We're leaving now; when is the next permitted departure?
                self.nextAllowedDeparture= self.sim.now()+self.minimumDaysBetweenShipments
                
                if isinstance(self.transitTime,types.TupleType):
                    toTime,froTime = self.transitTime
                else:
                    toTime = froTime = self.transitTime
                    
                while True:
                    # Make one or more trips.  In normal operation only one trip will be required, but 
                    # additional trips may be executed if the available shipping volume is too low to raise
                    # an otherwise-available shippable above its trigger threshold.
                    stepList = [('load', (self.fromW, self.packagingModel, self.storageModel, totalVC)),
                                ('move',(toTime,self.fromW,self.toW,self.conditions)),
                                ('alldeliver',(self.toW,totalVC,self.pullMeanFrequency)),
                                ('recycle',(self.toW,self.packagingModel, self.storageModel)),
                                ('move',(froTime,self.toW,self.fromW,self.conditions)),
                                ('unload',(self.fromW,)),
                                ('finish',(self.fromW,self.fromW))
                                ]
        
                    travelGen= createTravelGenerator(self.bName, stepList, self.truckType, self.delayInfo, self)
                    # This should maybe be more like the code block from PEP380: 
                    # http://www.python.org/dev/peps/pep-0380/#id13
                    for val in travelGen: yield val
                    
                    if self.toW.lowStockSet and self.fromW.gotAnyOfThese(self.toW.lowStockSet):
                        totalVC= self.quantityFunction(self.fromW, self.toW,
                                                       self.routeName,
                                                       self.pullMeanFrequency,
                                                       self.sim.now())
                        # And continue for another loop
                    else:
                        break

            else:
                logVerbose(self.sim,"%s:quantity to order is zero at %g"%(self.bName,self.sim.now()))
                
            logVerbose(self.sim,"%s: enters waitEvent at %f"%(self.bName,self.sim.now()))
            yield waitevent,self,self.warningEvent
            # Short pause to keep shipping events triggered by upstream
            # deliveries acting through attemptRestock() from piling up 
            # at the same 'moment'.  If we've gotten a request before the
            # next allowed departure, wait until then.
            delay= max(self.sim.rndm.gauss(0.1,0.025), warehouse.Warehouse.shortDelayTime)
            if self.nextAllowedDeparture - self.sim.now() > 0.0:
                delay += self.nextAllowedDeparture-self.sim.now()
            logDebug(self.sim,"%s received event at %g, pausing %g"%(self.bName,self.sim.now(),delay))
            yield hold,self,delay
            logVerbose(self.sim,"%s received event and waited; shipping at %g"%(self.bName,self.sim.now()))

    def __repr__(self):
        return u"<PersistentOnDemandShipment({0},{1},{2},{3},{4},{5},{6})>".format(self.fromW.name,self.toW.name,
                                                                                  self.thresholdVC,self.quantityFunction,self.transitTime,
                                                                                  self.pullMeanFrequency,self.minimumDaysBetweenShipments)
    def __str__(self): 
        return u"<PersistentOnDemandShipment({0},{1})>"%(self.fromW.name,self.toW.name)

