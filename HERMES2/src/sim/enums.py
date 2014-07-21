#! /usr/bin/env python

########################################################################
# Copyright C 2012, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" A place to put enums

Created on Jul 12, 2014

@author: welling

"""
_hermes_svn_id_="$Id$"

class TimeUnitsEnums:
    # enumerations for demand and calendarType
    TYPE_DAY = 'D'
    TYPE_WEEK = 'W'
    TYPE_MONTH = 'M'
    
    eStr = {'D': 'days',
            'W': 'weeks',
            'M': 'months'}

        