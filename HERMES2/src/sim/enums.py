#! /usr/bin/env python


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
