#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id: resultshooks.py 1927 2014-09-25 21:45:00Z welling $"

import sys,os,os.path,time,json,math,types
import bottle
import ipath
import shadow_network_db_api
import shadow_network as shdNtwk
import session_support_wrapper as session_support
from HermesServiceException import HermesServiceException
import privs
import htmlgenerator
import typehelper
from costmodel import getCostModelSummary
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError
from xlwt.Workbook import *
from xlwt.Style import *
import xlwt
ezxf = xlwt.easyxf

@bottle.route('/json/create-xls-summary')
def createExcelSummary(db, uiSession):
    try:
        modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
        resultsId = _safeGetReqParam(bottle.request.params,'resultsId',isInt=True)
        fname = _safeGetReqParam(bottle.request.params,'filename',isInt=False)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
    
        ### First create a summary page
        style = XFStyle()
        wb = Workbook()
        ws0 = wb.add_sheet('Summary')
    
        row = 0
        col = 1
        modelHeading_xf = ezxf('font: bold on, height 240; align: wrap on, horiz centre, vert top; borders: bottom thin')
    
        ws0.write(0,0,u'Model: %s'%m.name)
     
        with uiSession.getLockedState() as state:
            (fileKey,fullFileName) = \
                state.fs().makeNewFileInfo(shortName = "%s.xls"%fname,
                                           fileType = 'application/vnd.ms-excel',
                                           deleteIfPresent = True)
                
            wb.save(fullFileName)
        return {'success':True,'xlsfilename':fullFileName}
    except Exception as e:
        return {'success':False,'msg':str(e)}
     

@bottle.route('/downloadXLS')
def downloadXLS(db,uiSession):
    shortname = _safeGetReqParam(bottle.request.params,'shortname',isInt=False)
    xlsName = "%s.xls"%shortname
    with uiSession.getLockedState() as state:
        fullname = "%s/%s.xls"%(state.fs().workDir,shortname)
    return bottle.static_file(xlsName,os.path.dirname(fullname),
                              mimetype='application/vnd.ms-excel',download=xlsName)
    