#!/usr/bin/env python




__doc__=""" model_niger_generic.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id: model_kenya.py 1124 2012-11-15 06:50:49Z welling $"

import sys,os,getopt,types,math

import warehouse, vaccinetypes
import model_generic
import abstractbaseclasses
import constants as C

class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        self.whCounter = {}
        if self.daysPerMonth != 20:
            print RuntimeError("The input variable daypermonth must be set to 20 in order to run the Mozembique Model")

#     def getScheduledShipmentSize(self, fromW, toW, shipInterval, timeNow):
#         # The function is called repeatedly, every time a shipment is being set up.
#         # The InstantaneousDemand has been set by the MonthlyOrderProcesses of the
#         # downstream clinics; it includes any attached clinics but does not include
#         # safety stock.
#         
#         #demandDownstreamVialsVC= toW.getInstantaneousDemandVC((timeNow,timeNow+shipInterval))            
#         demandDownstreamVialsVC= toW.getProjectedDemandVCMasked((timeNow,timeNow+shipInterval),mask="M_Drone")
#         #print demandDownstreamVialsVC
#         #if toW.idcode == 120000:
#         #    print "buggers"
#         ### We need to develop a mask for the duplicates
#         
#         #for client in toW.clients():
#             
#         #if fromW.idcode == 1:
#         #    print "Demand: " + str(demandDownstreamVialsVC)
#         vaccineVialsVC,otherVialsVC= self._separateVaccines(demandDownstreamVialsVC)
# 
#         # Warehouses try for a buffer stock of 1.25.
#         vaccineVialsVC *= 1.25
#         # Believe you need a round up here, or the buffer may not get added to the system for small vial counts
#         # (e.g. if the number of vials is 3, and then the buffer makes it 3.75, the next set of commands
#         # cause it to be 3 rather than 4, which is the right answer.
#         vaccineVialsVC.roundUp()
# 
#         # This must now be scaled by available space so that we don't end up immediately
#         # discarding things on delivery.  Outreach clinics are presumed to have no storage
#         # except at the time of treatment (the PVSD arrives with the drugs), so in that case
#         # we do not scale by available storage.
# #        if isinstance(toW,Model.OutreachClinic):
# #            scaledVaccineVialsVC = vaccineVialsVC
# #        else:
#         fVC,cVC,wVC= toW.calculateStorageFillRatios(vaccineVialsVC)
#         fillVC= fVC+cVC+wVC
#         scaledVaccineVialsVC= vaccineVialsVC*fillVC
#         scaledVaccineVialsVC.roundDown()
# 
#         onhandVC= self.sim.shippables.getCollectionFromGroupList([s for s in toW.getStore().theBuffer
#                                                                 if isinstance(s,abstractbaseclasses.Shippable)])
#         lowVC= scaledVaccineVialsVC - onhandVC
#         lowVC.floorZero()
#         lowVC.roundUp()
#         #if fromW.idcode == 1:
#         #    print "lowVC = " + str(lowVC)
#         #print "shipment %s -> %s"%(fromW,toW.name)
#         #print "lowVC: %s"%[(v.name,n) for v,n in lowVC.items()]
#         #print "otherVialsVC: %s"%[(v.name,n) for v,n in otherVialsVC.items()]
#         #print "fillVC: %s"%[(v.name,n) for v,n in fillVC.items()]
#         return toW.getPackagingModel().applyPackagingRestrictions(lowVC + otherVialsVC)
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
        
        ### Rule is every trip gets one 
        assert homeWH==tripJournal[-1][4],"Trip journal does not return to home warehouse"
        totDays = 0.0
        totDistKm = 0.0
        #print "Truck = %s"%(truckType)
        #print type(truckType)
        for tpl in tripJournal:
            if tpl[0] == "move":
                legStart,legEnd,conditions,fromWH,toWH = tpl[1:6]
                if conditions is None:
                    conditions = 'normal'
                totDistKm += fromWH.getKmTo(toWH, homeWH.category, conditions)
                if toWH != homeWH:
                    endWH = toWH
            else:
                legStart,legEnd,conditions = tpl[1:4]
            totDays += (legEnd - legStart)

        if totDistKm == 0.0:
            return 0
        
#         if endWH.getSuppliers()[0][1]['TruckType'] == "M_UAV1" or \
#             endWH.getSuppliers()[0][1]['TruckType'] == "M_UAV2":
#                 return 0
        
            
#         if (homeWH.category == "Province" and endWH.category == "District") or \
#             (homeWH.category == "District" and endWH.category == "Province"):
#             if (homeWH,endWH) not in self.whCounter:
#                 self.whCounter[(homeWH,endWH)] = 0
#     
#             if self.whCounter[(homeWH,endWH)] == 0:
#                 self.whCounter[(homeWH,endWH)] = 1
#                 return 1
#             else:
#                 self.whCounter[(homeWH,endWH)] = 0
#                 return 0.86
        return 1
