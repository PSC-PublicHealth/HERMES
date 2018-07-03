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
    
    
    def getScheduledShipmentSize(self, fromW, toW, shipInterval, timeNow, asking=False):
        # The function is called repeatedly, every time a shipment is being set up.
        # The InstantaneousDemand has been set by the MonthlyOrderProcesses of the
        # downstream clinics; it includes any attached clinics but does not include
        # safety stock.
        #demandDownstreamVialsVC= toW.getInstantaneousDemandVC((timeNow,timeNow+shipInterval))
        
        demandDownstreamVialsVC= toW.getProjectedDemandVC((timeNow,timeNow+shipInterval))
        vaccineVialsVC,otherVialsVC= self._separateVaccines(demandDownstreamVialsVC)
        
        # Warehouses try for a buffer stock of 1.25.
        vaccineVialsVC *= 1.25
        # Believe you need a round up here, or the buffer may not get added to the system for small vial counts
        # (e.g. if the number of vials is 3, and then the buffer makes it 3.75, the next set of commands
        # cause it to be 3 rather than 4, which is the right answer.
        vaccineVialsVC.roundUp()
        suppliers = toW.getSuppliers()
        supplierRoute = suppliers[0][1]
        if supplierRoute['Type']=='askingpush':
	#if False:
            lowVC = vaccineVialsVC
        else:
            fVC,cVC,wVC= toW.calculateStorageFillRatios(vaccineVialsVC)
            fillVC= fVC+cVC+wVC
            scaledVaccineVialsVC= vaccineVialsVC*fillVC
            scaledVaccineVialsVC.roundDown()

            onhandVC= self.sim.shippables.getCollectionFromGroupList(\
		[s for s in toW.getStore().theBuffer\
		 if isinstance(s,abstractbaseclasses.Shippable)])
            lowVC= scaledVaccineVialsVC - onhandVC
            lowVC.floorZero()
            
            lowVC.roundUp()
                

        # This must now be scaled by available space so that we don't end up immediately
        # discarding things on delivery.        
        
        return toW.getPackagingModel().applyPackagingRestrictions(lowVC + otherVialsVC)
    
    def getDeliverySize(self, toW, availableVC, shipInterval, timeNow):
        """
        For those rare shipping patterns where the truck may not drop off the full
        size of an order, for example in the VillageReach shipping pattern.  This
        method is called for some particular route types immediately before the
        delivery is actually transferred to toW, and the amount delivered is
        the lesser of the returned VaccineCollection and availableVC.
        """
        #vc = self.getScheduledShipmentSize(None, toW, shipInterval, timeNow)
        demandDownstreamVialsVC= toW.getProjectedDemandVC((timeNow,timeNow+shipInterval))
        vaccineVialsVC,otherVialsVC= self._separateVaccines(demandDownstreamVialsVC)
        
        # Warehouses try for a buffer stock of 1.25.
        vaccineVialsVC *= 1.25
        # Believe you need a round up here, or the buffer may not get added to the system for small vial counts
        # (e.g. if the number of vials is 3, and then the buffer makes it 3.75, the next set of commands
        # cause it to be 3 rather than 4, which is the right answer.
        vaccineVialsVC.roundUp()

        # This must now be scaled by available space so that we don't end up immediately
        # discarding things on delivery.        
        fVC,cVC,wVC= toW.calculateStorageFillRatios(vaccineVialsVC)
        fillVC= fVC+cVC+wVC
        scaledVaccineVialsVC= vaccineVialsVC*fillVC
        scaledVaccineVialsVC.roundDown()

        onhandVC= self.sim.shippables.getCollectionFromGroupList([s for s in toW.getStore().theBuffer
                                                                if isinstance(s,abstractbaseclasses.Shippable)])
        lowVC= scaledVaccineVialsVC - onhandVC
        lowVC.floorZero()
        lowVC.roundUp()
        #print "shipment %s -> %s"%(fromW,toW.name)
        #print "lowVC: %s"%[(v.name,n) for v,n in lowVC.items()]
        #print "otherVialsVC: %s"%[(v.name,n) for v,n in otherVialsVC.items()]
        #print "fillVC: %s"%[(v.name,n) for v,n in fillVC.items()]
        return toW.getPackagingModel().applyPackagingRestrictions(lowVC + otherVialsVC)
        #vc.roundUp()
        #return vc
        
    def getModelMonthlyOrderProcess(self):
        return MonthlyOrderProcess

    def calcPerDiemDays(self, tripJournal, homeWH, truckType = None):
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

        ### NEW RULE if less than one day, give one, else floor of the number of days of travel.
        assert homeWH==tripJournal[-1][4],"Trip journal does not return to home warehouse"
        totDays = 0.0
        totDistKm = 0.0
        totalPerDiems = 0.0
        for tpl in tripJournal:
            if tpl[0] == "move":
                legStart,legEnd,conditions,fromWH,toWH = tpl[1:6]
                if conditions is None:
                    conditions = 'normal'
                totDistKm += fromWH.getKmTo(toWH, homeWH.category, conditions)
            else:
                legStart,legEnd,conditions = tpl[1:4]
            totDays += (legEnd - legStart)
        #print "DAys: " + str(totDays)
        if totDays < 1.0:
            return 1.0
        else:
            return math.floor(totDays)
            #totalPerDiems += math.ceil(totDays)
        #print "PerDiems" + str(totalPerDiems)
        #return totalPerDiems

