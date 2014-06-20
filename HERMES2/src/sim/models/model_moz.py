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
                if toWH != homeWH:
                    endWH = toWH
            else:
                legStart,legEnd,conditions = tpl[1:4]
            totDays += (legEnd - legStart)

        if totDistKm == 0.0:
            return 0

        if (homeWH.category == "Province" and endWH.category == "District") or \
            (homeWH.category == "District" and endWH.category == "Province"):
            if (homeWH,endWH) not in self.whCounter:
                self.whCounter[(homeWH,endWH)] = 0
    
            if self.whCounter[(homeWH,endWH)] == 0:
                self.whCounter[(homeWH,endWH)] = 1
                return 1
            else:
                self.whCounter[(homeWH,endWH)] = 0
                return 0.86
        return 1
