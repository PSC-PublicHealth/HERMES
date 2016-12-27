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


__doc__=""" manifest_shipping_processes.py
This module contains the shipping processes to implement a Manifest Shipping Process
"""

import ipath
import weakref
import sys,os,string
import operator

from SimPy.Simulation import *

### HERMES imports

import abstractbaseclasses
import packagingmodel
import storagemodel

from util import logDebug, logVerbose

import warehouse
from route_types.create_travel_generator import createTravelGenerator

class ManifestPushShipperUtilities():
    """
    This method takes a transit chain and separates the transitChain into multple none overlapping routes
    """
    
    @staticmethod
    def separateTransitChainIntoMultipleProcesses(transitChain):
        bins = {}
        i=0
        while i < len(transitChain):
            bins[i] = []
            thisTC = transitChain[i]
            thisTCId = i
            startT = thisTC[0]
            endT = thisTC[1]
            i+=1
            for tc2 in transitChain[i:]:
                if tc2[0] <= endT:
                    bins[thisTCId].append(i)
                    i+=1
                else:
                    break
        
        routes = {"_man1":[]}
        for b,ts in bins.items():
            routes["_man1"].append(transitChain[b])
            rNum = 2
            for b2 in ts:
                routeName = "_man{0}".format(rNum)
                if not routes.has_key(routeName):
                    routes[routeName] = []
                routes[routeName].append(transitChain[b2])
                rNum += 1
        
        for route,tcs in routes.items():
            tcs.sort(key=operator.itemgetter(0,1))
    
        return len(routes.keys()),routes
            
    
class ManifestPushShipperProcess(Process, abstractbaseclasses.UnicodeSupport):
    def __init__(self,fromWarehouse,transitChain,orderPendingLifetime, 
                 shipPriority,startupLatency=0.0,
                 truckType=None,name=None, delayInfo=None):
        
        """
        This one gets complicated, this is a route that allows for one to specify
        explicitly when shipments occur, what products are shipped along the route,
        and in what ammount. It quite different than the others and is not using periodicity at all
        """
        
        if name is None: name = "ManifestPushShipperProcess_{0}".format(fromWarehouse.name)
        
        Process.__init__(self,name=name,sim=fromWarehouse.sim)
        
        self.fromW = fromWarehouse
        self.transitChain = transitChain
        self.orderPendingLifetime = orderPendingLifetime
        if startupLatency > 0.0:
            raise RuntimeError("ManifestPushShipperProcess must have a startupLatency of 0 for route {0}".format(name))
        
        self.startupLatency = transitChain[0][0] ## Start this bitch up on the first shipment
        self.shipPriority = shipPriority
        
        if truckType is None:
            self.truckType=self.sim.trucktypes.getTypeByName("default")
        else:
            self.truckType= truckType
            
            
        self.delayInfo = delayInfo
        self.noteHolder = None
        self.nextWakeTime = startupLatency
        
        self.packageModel = packagingmodel.DummyPackagingModel()
        self.storageModel = storagemodel.DummyStorageModel()
        self.perDiemModel = None
        self.currentShipment = 0
        
        fromWarehouse.sim.processWeakRefs.append( weakref.ref(self) )
        
    def setPerDiemModel(self, perDiemModel):
        self.perDiemModel = perDiemModel
        
    def getPerDiemModel(self):
        return self.perDiemModel
    
    def finishBuild(self, szFunc):
        """
        this method should be called after the shipping network has been assempled
        It allows the ManifestPushShipping Process to precalculate quantities 
        and other information
        
        szFunc in this case will just look up the tripManifest... it is the ultimate push
        """
        
        pMMM = packagingmodel.PackagingModelMergerModel(self.sim)
        pMMM.addUpstreamPackagingModel(self.fromW.getPackagingModel())
        
        for startT,endT,wh,conditions,amount in self.transitChain:
            if wh != self.fromW: pMMM.addDownstreamPackagingModel(wh.getPackagingModel())
        
        self.packagingModel = pMMM.getNetPackagingModel()
        self.storageModel = self.fromW.getStorageModel()
        
    def setNoteHolder(self,noteHolder):
        self.noteHolder = noteHolder
    
    def getNoteHolder(self):
        return self.noteHolder
    
    def run(self):   
        if self.startupLatency > 0.0:
            yield hold,self,self.startupLatency
            
        logVerbose(self.sim,"{0}: latency: {1}, manifest route; my transit chain is {2}".format(self.bName,self.startupLatency,self.transitChain))
        
        while True:
            
            ### Set the next wake up time to the next time we ship
            if self.currentShipment + 1 < len(self.transitChain):
                self.nextWakeTime = self.transitChain[self.currentShipment+1][0]
            else:
                self.currentShipment = self.currentShipment-1
                self.nextWakeTime = 999999
                
            # simulate a truck delay (PLACE HOLDER)
            #if self.delayInfo is not None:
            #    delay= self.delayInfo.getPickupDelay()
            #    if delay > 0.0:
            #        logDebug(self.sim,"%s: shipment is delayed by %f days"%(self.bName, delay))
            #        yield hold, self, delay
            
            logDebug(self.sim,"{0}: my transit chain for shipment {1} is {2}".format(self.bName,
                                                                                     self.currentShipment,
                                                                                     self.transitChain[self.currentShipment]))
            
            
            ### Obtain the amount to ship from the transit Chain
            toW = self.transitChain[self.currentShipment][2]
            totalVC = self.fromW.getAndForgetPendingShipment(toW)
           
            transitTime = self.transitChain[self.currentShipment][1]-self.transitChain[self.currentShipment][0]
            
            stepList = [('load',(self.fromW,self.packagingModel, self.storageModel, totalVC)),
                        ('move',(transitTime,self.fromW,toW,'normal')),
                        ('alldeliver',(toW,totalVC,-1.0)),
                        ('recycle', (toW,self.packagingModel,self.storageModel)),
                        ('move',(transitTime,toW,self.fromW,'normal')),
                        ('unload',(self.fromW,)),
                        ('finish',(self.fromW,self.fromW))]
            
            if totalVC.totalCount() > 0:
                
                travelGen= createTravelGenerator(self.bName,
                                                 stepList,
                                                 self.truckType,
                                                 self.delayInfo,
                                                 self)
        
                for val in travelGen: yield val
            else:
                logVerbose(self.sim,"{0}: no order to ship at {1}".format(self.bName,self.sim.now()))
            
            
            self.currentShipment += 1
            yield hold,self,self.nextWakeTime-self.sim.now()
            
    def __repr__(self):
        print self.currentShipment
        print "{0}".format(self.transitChain[self.currentShipment])
        return "<ManifestPushShipperProcess({0},{1})>".format(repr(self.fromW),
                                                               '{0}'.format(self.transitChain[self.currentShipment]))
    def __str__(self):
        return "<ManifestShipperProcess({0})>".format(self.fromW.bName)          


class ManifestScheduledShipment(Process, abstractbaseclasses.UnicodeSupport):
    def __init__(self,fromWarehouse, toWarehouse, transitChain,
                 startupLatency = 0.0, name=None):
        """
        This process uses a manifest to place pending orders
        
        """
        
        if name is None:
            name = u"ManifestScheduledShipment_{0}_{1}".format(fromWarehouse.name,toWarehouse.name)
        Process.__init__(self, name=name,sim=fromWarehouse.sim)
        
        self.fromW = fromWarehouse
        self.toW = toWarehouse
        self.orderManifest = [(x[0],x[4]) for x in transitChain] # the start Day and the amounts
        
        ### Note, this is set in networkbuilder, which is a bit ass, because it is hidden.
        ### It is normally set to the startup latency of its matching process - a short delay
        ### see _buildManifestPushRoute and _innerBuildManifestPushRoute in networkbuilder.py for the code
        
        self.startupLatency = startupLatency #self.orderManifest[0][0] # wake this bitch up on the first shipment day
        self.currentShipment = 0
        
        fromWarehouse.sim.processWeakRefs.append( weakref.ref(self) )
    
    def finishBuild(self,szFunc):
        pass
    
    def run(self):
        if self.startupLatency>0.0:
            yield hold,self,self.startupLatency
        while True:
            ## Create a Vaccine Collection for the order
            shipVC = self.sim.shippables.getCollection()
            for v,n in self.orderManifest[self.currentShipment][1].items():
                vacc = self.sim.vaccines.getTypeByName(v)
                shipVC[vacc] = n
            shipVC.floorZero()
            shipVC.roundDown()
            self.fromW.addPendingShipment(self.toW,shipVC)
            
            previousShipmentDay = self.orderManifest[self.currentShipment][0]
            self.currentShipment += 1
            if self.currentShipment == len(self.orderManifest):
                interval = 9999999 #finished
            else:
                interval = self.orderManifest[self.currentShipment][0] - previousShipmentDay
            
            yield hold,self,interval
    
            
    def __repr__(self):
        return u"<ManifestScheduledShipment({0},{1})>".format(self.fromW.name,self.toW.name)
    def __str__(self): 
        return u"<ManifestScheduledShipment({0},{1})>".format(self.fromW.name,self.toW.name)
    

def main():
    
    testChain = [(0,2),(3,5),(4,6),(5,7),(40,45),(50,60)]
    nRoutes, Routes = \
        ManifestPushShipperUtilities.separateTransitChainIntoMultipleProcesses(testChain)
    
    print "Transit Chain: {0}".format(testChain)
    print "Results: {0},{1}".format(nRoutes, Routes)
    
############
# Main hook
############

if __name__=="__main__":
    main()

    