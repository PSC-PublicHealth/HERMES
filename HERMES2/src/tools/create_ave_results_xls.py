import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
import input
from copy import deepcopy
import sys
import optparse
import session_support_wrapper as session_support
import db_routines
from sqlalchemy import and_
import results_excel_report
from openpyxl import Workbook

def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-i inputfile][-b dbId]
    """)
    parser.add_option("-i", "--dbId", default=None)
    parser.add_option("-n", "--modelName", default =None)
    parser.add_option("-r", "--resultsGroup", default=None)
    parser.add_option("-o", "--outputname",default=None)

    opts,args = parser.parse_args()

    return (opts, args)

def main():

    opts,args = parseCommandLine()

    ## Get DB access
    db = db_routines.DbInterface(echo=False)
    session = db.Session()

    try:
	if opts.modelName:
            mold = session.query(shadow_network.ShdNetwork).filter(shadow_network.ShdNetwork.name==opts.modelName).one()
            print mold.name
            dbId = mold.modelId
        else:
            dbId = opts.dbId
        m = ShdNetworkDB(session,dbId)

    except Exception as e:
        print "Error = {0}".format(e)
        raise RuntimeError("Cannot access modelID = {0} from database".format(dbId))

    try:
        rGs = session.query(shadow_network.HermesResultsGroup).filter(and_(shadow_network.HermesResultsGroup.modelId == dbId,
                                                                     shadow_network.HermesResultsGroup.name == opts.resultsGroup))
        if rGs.count() == 0:
            raise

        rG = rGs[0]
    except Exception as e:
        print "Error = {0}".format(e)
        raise RuntimeError("Cannot find resultsGroup = {0} for modelId = {1} from database".format(opts.resultsGroup,dbId))

    ## Lastly, get the average results from the result Group
    try:
        aveR = None
        for r in rG.results:
            #print r.runNumber
            #print r.resultsType
            if r.resultsType == "average":
                aveR = r

        if aveR is None:
            raise
    except Exception as e:
        print "Error = {0}".format(e)
        raise RuntimeError("Cannot find average Result in resultsGroup = {0} for modelId = {1} from database".format(opts.resultsGroup,dbId))


    wb = results_excel_report.createExcelSummaryOpenPyXLForResult(session, m, aveR)
    wb.save(opts.outputname + ".xlsx")
if __name__ == '__main__':
    main()
