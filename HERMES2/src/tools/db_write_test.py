#! /usr/bin/env python

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

__doc__=""" preliminary testing of loading a network and writing it to the db
"""
_hermes_svn_id_="$Id$"

import ipath


import input
import globals
import curry
from main import parseCommandLine
import csv_tools
# more delayed imports below, so that values in globals can be changed before import

class ParserOptionCollector:
    def __init__(self):
        self._optList = []

    def addOpt(self, argName, *posArgs, **kwArgs):
        self._optList.append({'argName':argName, 'posArgs':posArgs, 'kwArgs':kwArgs})

    def optList(self):
        return self._optList

def main():
    unifiedInput = input.UnifiedInput()  # pointers to 'unified' files

    poc = ParserOptionCollector()

    poc.addOpt("report", "--report",
               help="A CSV file like report.csv, from which color info can be drawn")

    userInputList,gblInputs= parseCommandLine(poc.optList())
    reportFile = gblInputs['report']

    # Delayed inputs- we wanted to modify globals before causing these modules to load
    # we don't need hermes or util yet but this is a reminder that when we do need them
    # that we shouldn't load them at the top.
    import shadow_network
    import session_support_wrapper as session_support

    userInput = userInputList[0]
    userInputFile = gblInputs['input_files'][0]
    userInputFile,x1,x2 = userInputFile.partition(":")
    

    shdTypes = shadow_network.ShdTypes()
    shdTypes.loadShdNetworkTypeManagers(userInput, unifiedInput)
    net = shadow_network.loadShdNetwork(userInput, shdTypes)
    net.attachParms(userInputFile)


    
    import db_routines
    iface = db_routines.DbInterface(echo=True)
#    iface = db_routines.DbInterface(dbType='sqlite', name='/home/jim/sqlite_db', echo=True)
    #iface.dropTables(IReallyWantToDoThis=True)
    #return

    iface.createTables()
    #return;

    session = iface.Session()
    session.add(net)
    session.commit()

    cpy = net.copy()
    session.add(cpy)
    session.commit()


    if reportFile is not None:
        resultsGroup = shadow_network.HermesResultsGroup(net, "a name")
        session.add(resultsGroup)
        session.commit()
        rgId = resultsGroup.resultsGroupId

        results = shadow_network.HermesResults(rgId, 0, 'single')
        resId = results.resultsId

        (keys, recs) = csv_tools.parseCSV(reportFile)

        results.addReportRecs(net, recs)
        session.add(results)
        session.commit()
        #net.attachReport(recs)
    
        results = shadow_network.HermesResults(rgId, 1, 'single')
        resId = results.resultsId

        (keys, recs) = csv_tools.parseCSV(reportFile)

        results.addReportRecs(net, recs)
        session.add(results)
        session.commit()
        results = shadow_network.HermesResults(rgId, 2, 'single')
        resId = results.resultsId

        (keys, recs) = csv_tools.parseCSV(reportFile)

        results.addReportRecs(net, recs)
        session.add(results)
        session.commit()


############
# Main hook
############

if __name__=="__main__":
    main()

