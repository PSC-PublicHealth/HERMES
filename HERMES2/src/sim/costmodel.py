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
import microcostmodel
from currencysupport import CurrencyConverter
from costmodelsummary import (
        LegacyCostModelHierarchicalSummary,
        DummyCostModelHierarchicalSummary,
        Micro1CostModelHierarchicalSummary)

def getCostManager(hermesSim, userInput):
    costModelName = userInput['costmodel']
    if costModelName == 'dummy':
        return dummycostmodel.DummyCostManager(hermesSim, hermesSim.model)
    elif costModelName == 'legacy':
        if userInput['pricetable'] is None:
            return dummycostmodel.DummyCostManager(hermesSim, hermesSim.model) # fall back to none
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
                                                 userInput['currencybaseyear'],
                                                 userInput['priceinflation'])
    
            priceTable = legacycostmodel.PriceTable(ptFile, currencyConverter, required=True)
            return legacycostmodel.LegacyCostManager( hermesSim, hermesSim.model,
                                                      priceTable )
    elif costModelName == 'micro1':
        if hermesSim.shdNet:
            ccFile = hermesSim.shdNet.getCurrencyTableRecs()
        else:
            ccFile = userInput['currencyconversionfile']

        #print ccFile
        currencyConverter= CurrencyConverter(ccFile,
                                             userInput['currencybase'],
                                             userInput['currencybaseyear'],
                                             userInput['priceinflation'])

        return microcostmodel.MicroCostManager( hermesSim, hermesSim.model, currencyConverter )
    
    else:
        raise RuntimeError("Unrecognized cost model name %s"%costModelName)
    
def getCostModelVerifier(shdNet):
    costModelName = shdNet.getParameterValue('costmodel')
    if costModelName == 'dummy':
        return dummycostmodel.DummyCostModelVerifier()
    elif costModelName == 'legacy':
        if shdNet.getParameterValue('pricetable') is None:
            return dummycostmodel.DummyCostModelVerifier() # fall back to dummy
        else:
            currencyConverter= CurrencyConverter(shdNet.getCurrencyTableRecs(),
                                                 shdNet.getParameterValue('currencybase'),
                                                 shdNet.getParameterValue('currencybaseyear'),
                                                 shdNet.getParameterValue('priceinflation'))
            priceTable = legacycostmodel.PriceTable( shdNet.getPriceTableRecs(),
                                                     currencyConverter,required=True )
            return legacycostmodel.LegacyCostModelVerifier(priceTable)
    elif costModelName == 'micro1':
        currencyConverter= CurrencyConverter(shdNet.getCurrencyTableRecs(),
                                             shdNet.getParameterValue('currencybase'),
                                             shdNet.getParameterValue('currencybaseyear'),
                                             shdNet.getParameterValue('priceinflation'))

        return microcostmodel.MicroCostModelVerifier( currencyConverter )
    else:
        raise RuntimeError("Unrecognized cost model name <%s>"%costModelName)

def getCostModelSummary(shdNet, result):
    costModelName = shdNet.getParameterValue('costmodel')
    if costModelName == 'dummy':
        return DummyCostModelHierarchicalSummary(result)
    elif costModelName == 'legacy':
        if shdNet.getParameterValue('pricetable') is None:
            # dummycostmodel
            return DummyCostModelHierarchicalSummary(result)
        else:
            # legacycostmodel
            return LegacyCostModelHierarchicalSummary(result)
    elif costModelName == 'micro1':
        return Micro1CostModelHierarchicalSummary(result)
    else:
        raise RuntimeError("Unrecognized cost model name <%s>"%costModelName)
