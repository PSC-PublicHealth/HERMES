#!/usr/bin/env python

########################################################################
# Copyright C 2009, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################


__doc__=""" model_niger_generic.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math

import warehouse, vaccinetypes
import model_generic

class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        if self.daysPerMonth != 28:
            print RuntimeError("The input variable daypermonth must be set to 28 in order to run the Niger Model")
            
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
        
        Niger rules: 
        -For any trip, sum the total travel distance
        -if this total is zero, the return value is zero.
        -otherwise, return 1 + floor(totalTransitTimeInDays)
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

        if totDistKm > 0.001:
            return 1+int(math.floor(totDays))
        else:
            return 0
