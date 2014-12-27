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

import sys, os, types, math
import csv_tools

class CurrencyConverter:
    """
    This class reads a currency conversion table and provides currency conversions.
    """
    def __init__(self, csvFile, currencyBase, currencyBaseYear, inflationRate):
        """
        inflationRate is a scale factor- for example, inflationRate=0.03 implies 3% inflation over 1 year
        """
        self.cb= unicode(currencyBase)
        self.year= int(currencyBaseYear)
        self.inflation= float(inflationRate)
        keys,recs= csv_tools.parseCSV(csvFile)
        yearKeys = {}
        for k in keys:
            try:
                yearKeys[int(k)] = k
            except:
                pass
        if int(currencyBaseYear) in yearKeys:
            self.yearKey = yearKeys[self.year]
        else:
            raise RuntimeError("Requested currency base year %d is not in the currency conversion table"%self.year)
        if 'Currency Code' not in keys:
            raise RuntimeError('The currency table is missing a "Currency Code" column')
        
        for r in recs:
            r['Currency Code'] = unicode(r['Currency Code'].strip()) # avoids problems with trailing blanks
            
        found = False
        for r in recs:
            if r['Currency Code'] == u'USD' and r[yearKeys[self.year]] != '':
                found = True
                if r[yearKeys[self.year]] != 1.0:
                    raise RuntimeError("The currency conversion table does not seem to be written in terms of USD")
                break
        if not found:
            raise RuntimeError("Cannot find an entry for USD in the currency conversion table")
        
        self.fullTable= { yr:{} for yr in yearKeys.keys() }
        for r in recs:
            curCode = r['Currency Code']
            for yr,yrKey in yearKeys.items():
                try:
                    self.fullTable[yr][curCode] = float(r[yrKey])
                except:
                    pass
        #print self.fullTable
                
                    
    def _toJSON(self):
        """
        This makes the user interface's life easier.
        """
        return { 
                'currencyBase':self.cb,
                'currencyBaseYear':self.year,
                'inflation':self.inflation,
                'fullTable':self.fullTable
                }

        
    def convert(self, curCode, val):
        """
        This converts the given value in the given currency to the base currency, 
        assuming the conversion happens in the base year.
        """
        return self.convertTo(val, curCode, self.cb, inflation=0.0)
    
    def convertTo(self, val, curCode, newCurCode, startYear=None, endYear=None, inflation=None):
        """
        val is a value in currency type curCode; it is converted to currency type newCurCode and
        inflated according to the given time interval and inflation rate.  Years may be non-integer.
        For example, if the simulation start time is the beginning of 2011, simulation years have
        336 days, and it is desired to calculate inflation over the interval between day 56 and 
        day 308 of the simulation, startYear = 2011 + 56/336 = 2011.166667 and similarly
        endYear = 2011.916667 .
        """
        if curCode is None:
            raise RuntimeError("Input currency code is not set")
        curCode = unicode(curCode.strip('"').strip("'"))
        if curCode is None:
            raise RuntimeError("Output currency code is not set")
        newCurCode = unicode(newCurCode.strip('"').strip("'"))
        if startYear is None: 
            startYear = float(self.getBaseYear())
            tblYear = self.getBaseYear()
        else: 
            if isinstance(startYear, types.FloatType):
                tblYear = int(math.floor(startYear))
            else:
                tblYear = int(startYear)
                startYear = float(startYear)
        if endYear is None: endYear = float(self.getBaseYear())
        else: endYear = float(endYear)
        if inflation is None: inflation = self.getInflationRate()
        
        if curCode == newCurCode: valNewCurStartYear = val
        else:
            if tblYear in self.fullTable:
                t = self.fullTable[tblYear]
                if curCode in t: v1 = t[curCode]
                else: raise RuntimeError("No conversion table value for %s in %d"%(curCode, tblYear))
                if newCurCode in t: v2 = t[newCurCode]
                else: raise RuntimeError("No conversion table value for %s in %d"%(newCurCode, tblYear))
            else: raise RuntimeError("No conversion table values for the year %d"%tblYear)
            valNewCurStartYear = val*(v2/v1)
            
        if startYear==endYear or inflation==0.0: 
            return valNewCurStartYear
        else:
            delta = endYear-startYear
            return valNewCurStartYear * math.exp(delta*self.inflation)
            
        return valNewCurStartYear
    
    def getBaseCurrency(self):
        return self.cb
    
    def getBaseYear(self):
        return int(self.year)
    
    def getInflationRate(self):
        return self.inflation
    
    def __str__(self): 
        return "<CurrencyConverter(%s, %d)>"%(self.cb, self.year)


