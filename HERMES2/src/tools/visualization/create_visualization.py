#!/usr/bin/env python
__doc__=""" consolidate_places_in_level.py
This program takes a stores file, route file and a csv that describes places to be changed, and creates new stores and routes files executing the alterations.
"""

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

_hermes_svn_id_="$Id: consolidate_places_in_level.py 1053 2012-08-16 17:47:26Z stbrown $"

import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
from visualization_shdntwk import *
import kml_shdNtwk as kml
import jOrgChart_shdNtwk as jsOrg
import kml_jquery_shdNtwk as kmlJ

import input
from copy import deepcopy
import sys
import optparse

def hPrint(store,dataDict,level=0,levelToStop=None):
    spaceString = ""
    for i in range(0,level):
        spaceString += ","
    print("%s%s,%10.2f"%(spaceString,store.NAME,dataDict[store.idcode]))
    for cli in store.clients():
        hPrint(cli[0],dataDict,level=level+1)
        
        
routesOutputFields = []
storesOutputFields = []
storesOutputList = []
routesOutputList = []

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-d db_id]
    """)
    parser.add_option("-d","--use_db",type=int,default=None)
    parser.add_option("-r","--result_id",default=None)
    parser.add_option("-n","--run_id",type=int,default=0)
    parser.add_option("-y","--year",type=int,default=2012)
    parser.add_option("-m","--month",type=int,default=1)
    parser.add_option("-j","--day",type=int,default=1)
    parser.add_option("-c","--numbercolors",type=int,default=100)
    parser.add_option("-H","--columnheight",type=int,default=100000)
    parser.add_option("-t","--title",default="Google Earth HERMES Viz")
    parser.add_option("-R","--popradius",type=float,default=0.2)
    parser.add_option("-V","--vacradius",type=float,default=0.05)
    parser.add_option("-T","--type",type="choice",choices=["google","jsOrgChart"],default="google")
    
    opts,args=parser.parse_args()
    
    return (opts,args)

if __name__ == '__main__':

    opts,args = parseCommandLine()
    
    import session_support_wrapper as session_support
    import db_routines
        
    iface = db_routines.DbInterface(echo=False)
    session = iface.Session()
    shdNtwkDB = ShdNetworkDB(session,opts.use_db)
    shdNtwkDB.useShadowNet()
    shdNtwk = shdNtwkDB._net
    
    resultGToProc = shdNtwk.getResultsGroupByName(opts.result_id)
    resultsID = resultGToProc.results[0].resultsId
    
    if opts.type == "google":
        kDate = kmlJ.KMLDate(opts.year,opts.month,opts.day)
        viz = kmlJ.KMLVisualization(shadow_network_db_=shdNtwkDB,
                                    resultsID_=resultsID,    
                                    kmlDate_=kDate,
                                    numberOfColors_=opts.numbercolors,
                                    columnHeight_=opts.columnheight,
                                    populationRadius_=opts.popradius,
                                    vaccineAvailRadius_=opts.vacradius,
                                    title_=opts.title)
    elif opts.type == "jsOrgChart":
        viz = jsOrg.JOrgChartVisualization(shadow_network_=shdNtwk,
                                           resultsID_=resultsID,
                                           title_=opts.title)
            
    viz.build()
    viz.output(removeFiles=False)

    result = shdNtwk.getResultById(resultsID)
    with open("./kmlViz.kml","wb") as f:
        f.write("%s"%result.getKmlVizString())
     