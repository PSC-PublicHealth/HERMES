#!/usr/bin/env python




__doc__=""" model_niger_generic.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math

import warehouse, vaccinetypes
import model_generic
from collections import deque

def createRunningAverageQue(initialVC):
    return deque([initialVC.copy() 
                  for i in xrange(Model.nRunningAverageShipments)])
    
class MonthlyOrderProcess(warehouse.PeriodicProcess):
    def __init__(self,interval, startupLatency, wh):
        warehouse.PeriodicProcess.__init__(self, wh.sim, "MonthlyOrderProcess_%s"%wh.name,
                                           interval,startupLatency)
        self.wh= wh
        #self.interval = 28.0
        assert(hasattr(self.wh,'shppingDemandModel'))
    def cycle(self,timeNow):
        vialsThisMonth= self.wh.getAccumulatedUsageVC()
        self.wh.clearAccumulatedUsage()
        if self.wh.runningAveQ is None:
            self.wh.runningAveQ= createRunningAverageQue(vialsThisMonth)
            self.wh.runningAveVC= vialsThisMonth*len(self.wh.runningAveQ)
        else:
            self.wh.runningAveVC -= self.wh.runningAveQ.pop() # remove from right end
            self.wh.runningAveVC += vialsThisMonth
            self.wh.runningAveQ.appendleft(vialsThisMonth.copy()) # insert from left
        aveVC= self.wh.runningAveVC*(1.0/len(self.wh.runningAveQ))
        ## Campaign demand
        #vaccT = self.sim.vaccines.getTypeByName("T_Dengue")
        campDosesVC = self.wh.shippingDemandModel.getDemandExpectation(self.wh.getPopServedPC(),
                                                                       self.interval,timeNow=timeNow+28)
        campVialsVC= self.sim.model._scaleDemandByType(campDosesVC)*self.sim.model.campaignFilterVC
        campVialsVC = self.sim.shippables.addPrepSupplies(campVialsVC)
        #print "\nBefore " + str(timeNow) + " WH: " +str(self.wh.idcode) + " has demand of vials: " + str(aveVC)    
        aveVC=aveVC.filter(campVialsVC,self.sim.model.campaignFilterVC)
        #print "\nAt " + str(timeNow) + " WH: " +str(self.wh.idcode) + " has demand of vials: " + str(aveVC)
        self.wh.registerInstantaneousDemandVC(aveVC,self.interval)
        
class Model(model_generic.Model):
    nRunningAverageShipments = 1
    
    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        self.campaignFilterVC = self.sim.vaccines.getCollection([(sim.vaccines.getTypeByName('T_Dengue'),1.0)])
               
    def getModelMonthlyOrderProcess(self):
        return MonthlyOrderProcess
