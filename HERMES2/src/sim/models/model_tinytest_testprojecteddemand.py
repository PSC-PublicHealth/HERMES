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


__doc__=""" model_tinytest.py
This is a modification of the generic model which un-disables some things
so that more backward compatibility situations can be tested.
"""

_hermes_svn_id_="$Id: model_tinytest.py 826 2012-02-16 23:14:57Z welling $"

import sys,os,getopt,types,math

import warehouse, vaccinetypes, abstractbaseclasses
import model_generic

class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        self.defaultShipStartupLatency= 7.0

    @staticmethod
    def decomposeId(code):
        #print "decomposeId: %d -> "%code,
        clinicCode= code % 100
        code /= 100
        districtCode= code % 100
        code /= 100
        regionCode= code % 100
        #print "(%d,%d,%d)"%(regionCode,districtCode,clinicCode)
        return (regionCode,districtCode,clinicCode)

    @staticmethod
    def composeId(regionCode,districtCode,clinicCode):
        result= long("%d%02d%02d%02d"%(1,regionCode,districtCode,clinicCode))
        #print "composeId: (%d %d %d) -> %ld"%(regionCode,districtCode,
        #                                      clinicCode,result)
        return result

    def getDefaultSupplier(self,storeDict,code):
        regionCode,districtCode,clinicCode= self.decomposeId(code)
        if regionCode==0 and districtCode==0 and clinicCode==0:
            return None # This is the central store
        else:
            wh= storeDict[code]
            if wh.getPopServedPC().totalCount()==0 and len(wh.getClients())==0:
                # deactivated warehouse
                return None
            elif districtCode==0 and clinicCode==0:
                # region; supplier is central store
                return self.composeId(0,0,0) 
            elif clinicCode==0:
                # district; supplier is region
                return self.composeId(regionCode,0,0) 
            else:
                # clinic; supplier is district
                return self.composeId(regionCode,districtCode,0) 

    def getDefaultTruckTypeName(self,fromW,toW):
        return "N_vaccine_carrier_WHO_PQS"

    def warehouseShipQuantityFunc(self, fromW, toW, routeName, pullMeanFrequencyDays, timeNow):
        # These are 'pull' shipments.  This function may be
        # called at start-up time, this functions is now using the InstantaneousDemand
        # to get the vial counts below correct.  This means that MonthlyOrder process must
        # be running in order for this to be correct.
        #vC = self._scaleDemandByType(toW.getProjectedDemandVC(routeName,
        #                                                      (timeNow,timeNow+pullMeanFrequencyDays)))
        vC = toW.getProjectedDemandVC(routeName, (timeNow,timeNow+pullMeanFrequencyDays))
        vaccineVialsVC,otherVialsVC= self._separateVaccines(vC)
        
        vaccineVialsVC *= 1.25
        fVC,cVC,wVC= toW.calculateStorageFillRatios(vaccineVialsVC+otherVialsVC)
        fillVC= fVC+cVC+wVC
        #print "%s: %s"%(toW.name,fillVC)
        scaledVaccineVialsVC= vaccineVialsVC*fillVC
        scaledVaccineVialsVC.roundDown()
        lowVC= (scaledVaccineVialsVC+otherVialsVC) \
               - self.sim.vaccines.getCollectionFromGroupList([s for s in toW.theBuffer
                                                               if isinstance(s,abstractbaseclasses.Shippable)])
        lowVC.floorZero()
        return lowVC

    def getScheduledShipmentSize(self, toW, routeName, shipInterval, timeNow):
        # The function is called repeatedly, every time a shipment is being set up.
        # The InstantaneousDemand has been set by the MonthlyOrderProcesses of the
        # downstream clinics; it includes any attached clinics but does not include
        # safety stock.

        #demandDownstreamVialsVC=self._scaleDemandByType(toW.getProjectedDemandVC(routeName,
        #                                                                        (timeNow,timeNow+shipInterval)))
        
        demandDownstreamVialsVC= toW.getProjectedDemandVC(routeName, (timeNow,timeNow+shipInterval))
        vaccineVialsVC,otherVialsVC= self._separateVaccines(demandDownstreamVialsVC)
        
        # Warehouses try for a buffer stock of 1.25.
        vaccineVialsVC *= 1.25
        # This must now be scaled by available space so that we don't end up immediately
        # discarding things on delivery.
        fVC,cVC,wVC= toW.calculateStorageFillRatios(vaccineVialsVC)
        fillVC= fVC+cVC+wVC
        scaledVaccineVialsVC= vaccineVialsVC*fillVC
        scaledVaccineVialsVC.roundDown()

        onhandVC= self.sim.vaccines.getCollectionFromGroupList([s for s in toW.getStore().theBuffer
                                                                if isinstance(s,abstractbaseclasses.Shippable)])
        lowVC= scaledVaccineVialsVC - onhandVC
        lowVC.floorZero()
        lowVC.roundUp()
        return lowVC+otherVialsVC

    def _getFactoryProductionVC(self, factory, daysSinceLastShipment, timeNow,
                                daysUntilNextShipment):
        #demandDownstreamVialsVC= self._scaleDemandByType(factory.targetStore.getProjectedDemandVC(factory.name,
        #                                                                                          (timeNow,timeNow+daysUntilNextShipment)))
        demandDownstreamVialsVC= factory.targetStore.getProjectedDemandVC(factory.name, (timeNow,timeNow+daysUntilNextShipment))
        vaccineVialsVC,otherVialsVC= self._separateVaccines(demandDownstreamVialsVC)
        vaccineVialsVC *= self.factoryOverstockScale
        fVC,cVC,wVC= factory.targetStore.calculateStorageFillRatios(vaccineVialsVC)
        fillVC= fVC+cVC+wVC
        scaledVaccineVialsVC= vaccineVialsVC*fillVC
        scaledVaccineVialsVC.roundDown()
        onhandVC= self.sim.vaccines.getCollectionFromGroupList([s for s in factory.targetStore.getStore().theBuffer
                                                                if isinstance(s,abstractbaseclasses.Shippable)])
        #print "On Hand: " + str(onhandVC)
        lowVC= scaledVaccineVialsVC - onhandVC
        lowVC.floorZero()
        lowVC.roundUp()
        #print "Actual amount: " + str(lowVC)
        return lowVC

