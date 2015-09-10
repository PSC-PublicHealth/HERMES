#! /usr/bin/env python

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

        

class StorageTypeEnums:
    STORE_WARM = 'roomtemperature'
    STORE_COOL = 'cooler'
    STORE_FREEZE = 'freezer'

    eStr = {'roomtemperature' : 'warm',
            'cooler' : 'cool',
            'freezer' : 'freeze'}

    wcfList = (STORE_WARM, STORE_COOL, STORE_FREEZE)
