#!/usr/bin/env python

###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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



__doc__=""" model_tinytest.py
This is a modification of the generic model which un-disables some things
so that more backward compatibility situations can be tested.
"""

_hermes_svn_id_="$Id: model_tinytest.py 826 2012-02-16 23:14:57Z welling $"

import sys,os,getopt,types,math

import warehouse, vaccinetypes
import model_generic

class Model(model_generic.Model):

    def __init__(self,sim):
        model_generic.Model.__init__(self,sim)
        self.defaultShipStartupLatency= 7.0

    @staticmethod
    def decomposeId(code):
        #print "decomposeId: %d -> "%code,
        clinicCode= code % 100
        code /= 100
        districtCode= code % 100
        code /= 100
        regionCode= code % 100
        #print "(%d,%d,%d)"%(regionCode,districtCode,clinicCode)
        return (regionCode,districtCode,clinicCode)

    @staticmethod
    def composeId(regionCode,districtCode,clinicCode):
        result= long("%d%02d%02d%02d"%(1,regionCode,districtCode,clinicCode))
        #print "composeId: (%d %d %d) -> %ld"%(regionCode,districtCode,
        #                                      clinicCode,result)
        return result

    def getDefaultSupplier(self,storeDict,code):
        regionCode,districtCode,clinicCode= self.decomposeId(code)
        if regionCode==0 and districtCode==0 and clinicCode==0:
            return None # This is the central store
        else:
            wh= storeDict[code]
            if wh.getPopServedPC().totalCount()==0 and len(wh.getClients())==0:
                # deactivated warehouse
                return None
            elif districtCode==0 and clinicCode==0:
                # region; supplier is central store
                return self.composeId(0,0,0) 
            elif clinicCode==0:
                # district; supplier is region
                return self.composeId(regionCode,0,0) 
            else:
                # clinic; supplier is district
                return self.composeId(regionCode,districtCode,0) 

    def getDefaultTruckTypeName(self,fromW,toW):
        return "N_vaccine_carrier_WHO_PQS"
