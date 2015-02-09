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



