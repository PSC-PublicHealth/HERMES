#!/usr/bin/env python




__doc__=""" model_niger_generic.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id: model_chad.py 1019 2012-06-15 11:29:36Z stbrown $"

import sys,os,getopt,types,math

import warehouse, vaccinetypes
import model_generic
import abstractbaseclasses
import constants as C

class MonthlyOrderProcess(warehouse.PeriodicProcess):
    def __init__(self,interval, startupLatency, wh):
        warehouse.PeriodicProcess.__init__(self, wh.sim, "MonthlyOrderProcess_%s"%wh.name,
                                           interval,startupLatency)
        #self.wh= wh
        #self.interval = 28.0
        #assert(hasattr(self.wh,'shppingDemandModel'))
    def cycle(self,timeNow):
        pass
        #print "Using this Monthly Order Process"
    
class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        if self.daysPerMonth != 20:
            print RuntimeError("The input variable daypermonth must be set to 20 in order to run the Benin Model")
    
    def getModelMonthlyOrderProcess(self):
        return MonthlyOrderProcess

    def calcPerDiemDays(self, tripJournal, homeWH):
        """
        This function is called once at the end of each full round trip for any
        shipping process to calculate the number of days of per diem pay the
        driver is to receive, based on the details of the just- completed trip.
        
        tripJournal is a list of tuples describing the steps of the just-completed trip.
        tripJournal entries all start with (stepname, legStartTime, legEndTime, legConditions...);
        see the description of warehouse.createTravelGenerator for additional details.

        homeWH is the warehouse which is the driver's 'home'; that is, where the driver
        might be expected to sleep for free. Typically legEndTime for one leg
        will equal legStartTime for the next.
        
        The return value of this function is expected to be a number.
        

        """
        assert homeWH==tripJournal[-1][4],"Trip journal does not return to home warehouse"
        totDays = 0.0
        totDistKm = 0.0
        for tpl in tripJournal:
            if tpl[0] == "move":
                legStart,legEnd,conditions,fromWH,toWH = tpl[1:6]
                if conditions is None:
                    conditions = 'normal'
                totDistKm += fromWH.getKmTo(toWH, homeWH.category, conditions)
            else:
                legStart,legEnd,conditions = tpl[1:4]
            totDays += (legEnd - legStart)

        totalPerDiems = 0
        if totDistKm > 100.0:
            totalPerDiems += 1

        totalPerDiems += math.floor(totDays)

        return totalPerDiems


