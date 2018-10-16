#!/usr/bin/env python



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

outdoorsLotsOfSpace = 1000000000000

daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
daysPerMonth = 28
secondsInDay = 86400.0
secondsInHour = 3600.0
minutesInHour =  60.0
epsilon = 1.0E-8

timeUnitToString = {'s':'Second',
                    'm':'Minute',
                    'D':'Day',
                    'M':'Month',
                    'Y':'Year'}



