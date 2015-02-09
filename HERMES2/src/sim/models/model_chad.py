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



__doc__=""" model_niger_generic.py
This is a variant of the Niger model for the vaccine distribution
simulator HERMES
"""

_hermes_svn_id_="$Id$"

import sys,os,getopt,types,math

import warehouse, vaccinetypes
import model_generic
import abstractbaseclasses

class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        if self.daysPerMonth != 28:
            print RuntimeError("The input variable daypermonth must be set to 28 in order to run the Chad Model")
            

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

        if totDays >= 1.0:
            return int(math.ceil(totDays/1.0))
        else:
            return 0
