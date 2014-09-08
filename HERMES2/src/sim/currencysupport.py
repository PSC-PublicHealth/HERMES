#!/usr/bin/env python 

########################################################################
# Copyright C 2010, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" currencysupport.py
This module provides currency conversion support.
"""

_hermes_svn_id_="$Id$"

import sys, os, types
import csv_tools

class CurrencyConverter:
    """
    This class reads a currency conversion table and provides currency conversions.
    """
    def __init__(self, csvFile, currencyBase, currencyBaseYear):
        self.cb= currencyBase
        self.year= int(currencyBaseYear)
        keys,recs= csv_tools.parseCSV(csvFile)
        if currencyBaseYear in keys:
            self.yearKey = currencyBaseYear
        elif str(currencyBaseYear) in keys:
            self.yearKey = str(currencyBaseYear)
        else:
            raise RuntimeError("Requested currency base year %d is not in the currency conversion table"%self.year)
        if 'Currency Code' not in keys:
            raise RuntimeError('The currency table is missing a "Currency Code" column')
        
        for r in recs:
            r['Currency Code'] = r['Currency Code'].strip() # avoids problems with trailing blanks
            
        found = False
        for r in recs:
            if r['Currency Code'] == 'USD' and r[self.yearKey] != '':
                found = True
                if r[self.yearKey] != 1.0:
                    raise RuntimeError("The currency conversion table does not seem to be written in terms of USD")
                break
        if not found:
            raise RuntimeError("Cannot find an entry for USD in the currency conversion table")
        
        baseRecList = [r for r in recs if r['Currency Code']=='USD']
        if len(baseRecList) == 0:
            raise RuntimeError("The currency table record for %s is missing"%self.cb)
        baseFac = None
        for r in baseRecList:
            if type(r[self.yearKey]) == types.FloatType:
                baseFac = r[self.yearKey]
                break
        if baseFac is None:
            raise RuntimeError("Failed to find a valid base currency value for the base year")
        if baseFac <= 0.0:
            raise RuntimeError("Currency table contains a nonsense value for the base currency at base year")
        
        self.table= {}
        for r in recs:
            curCode = r['Currency Code']
            if self.yearKey in r:
                v = r[self.yearKey]
                if v is not None and v != '' and v > 0.0:
                    self.table[curCode] = baseFac/v
                    
    def _toJSON(self):
        """
        This makes the user interface's life easier.
        """
        return { 
                'currencyBase':self.cb,
                'currencyBaseYear':self.year,
                'table':self.table
                }

        
    def convert(self, curCode, val):
        if curCode in self.table:
            return self.table[curCode] * val
        raise RuntimeError("No conversion factor to take %s to %s"%(curCode,self.cb))
    
    def convertTo(self, curCode, val, newCurCode):
        if curCode in self.table and newCurCode in self.table:
            return (self.table[curCode] * val)/self.table[newCurCode]
        raise RuntimeError("No conversion factor to take %s to %s"%(curCode,newCurCode))
    
    def getBaseCurrency(self):
        return self.cb
    
    def getBaseYear(self):
        return int(self.year)
    
    def __str__(self): 
        return "<CurrencyConverter(%s, %d)>"%(self.cb, self.year)


