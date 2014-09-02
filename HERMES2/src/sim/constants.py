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

_hermes_svn_id_="$Id$"

__doc__=""" constants.py
This module is a convenient place for constants, things that
do not depend on the particular simulation.  This includes
both physical constants and things like event priority information.
"""

hoursPerDay= 24
monthsPerYear = 12

maxPriority= 10
janitorPriority= 1
useVialPriority= 9
shipPriority= 4
requestShipPriority= 3
ccPerLiter= 1000

storageLotsOfSpace = 1232123234342.0 
transportLotsOfSpace = 1232123214432.0 

daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
secondsInDay = 86400.0
secondsInHour = 3600.0
minutesInHour =  60.0
epsilon = 1.0E-8



