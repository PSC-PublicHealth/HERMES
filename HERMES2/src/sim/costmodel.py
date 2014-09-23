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

__doc__=""" costmodel.py
This module holds classes used in calculating costs associated with simulations.
"""

_hermes_svn_id_="$Id: costmodel.py 879 2012-03-08 16:47:47Z jleonard $"

import sys, os, StringIO, types, unittest
import abstractbaseclasses, warehouse, reportinghierarchy
import csv_tools
import fridgetypes, trucktypes, vaccinetypes
import util
import dummycostmodel
import legacycostmodel
from currencysupport import CurrencyConverter
from costmodelsummary import (
        LegacyCostModelHierarchicalSummary,
        DummyCostModelHierarchicalSummary)

def getCostManager(hermesSim, userInput):
    if userInput['pricetable'] is None:
        return dummycostmodel.DummyCostManager()
    else:
        if hermesSim.shdNet:
            ccFile = hermesSim.shdNet.getCurrencyTableRecs()
            ptFile = hermesSim.shdNet.getPriceTableRecs()
        else:
            ccFile = userInput['currencyconversionfile']
            ptFile = userInput['pricetable']

        #print ccFile
        currencyConverter= CurrencyConverter(ccFile,
                                             userInput['currencybase'],
                                             userInput['currencybaseyear'])

        priceTable = legacycostmodel.PriceTable(ptFile, currencyConverter, required=True)
        costManager= legacycostmodel.LegacyCostManager( hermesSim, hermesSim.model,
                                                        priceTable )
        return costManager
    
def getCostModelVerifier(shdNet):
    if shdNet.getParameterValue('pricetable') is None:
        return dummycostmodel.DummyCostModelVerifier()
    else:
        currencyConverter= CurrencyConverter(shdNet.getCurrencyTableRecs(),
                                             shdNet.getParameterValue('currencybase'),
                                             shdNet.getParameterValue('currencybaseyear'))
        priceTable = legacycostmodel.PriceTable( shdNet.getPriceTableRecs(),
                                                 currencyConverter,required=True )
        return legacycostmodel.LegacyCostModelVerifier(priceTable)

def getCostModelSummary(shdNet, result):
    if shdNet.getParameterValue('pricetable') is None:
        # dummycostmodel
        return DummyCostModelHierarchicalSummary(result)
    else:
        # legacycostmodel
        return LegacyCostModelHierarchicalSummary(result)


