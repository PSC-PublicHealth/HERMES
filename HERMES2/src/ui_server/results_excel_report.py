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

inlizer=session_support.inlizer
_=session_support.translateString

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
        # Define some formatting styles for the spreadsheet.
        modelHeading_xf = ezxf('font: bold on, height 240; align: wrap on, horiz centre, vert top; borders: bottom thin')
        divider_1_xf = ezxf('font: bold on, height 222, colour white; align: horiz left; pattern: pattern solid, fore-color dark_red; borders: bottom thin')
        total_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color grey25',num_format_str='0%')
        total_percent_xf =  ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color grey25',num_format_str='0%')
        total_xf =  ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color grey25',num_format_str='#,##0')
        plain_xf = ezxf('font: bold off, height 222; align: horiz right',num_format_str="#,##0")
        plain_label_xf = ezxf('font: bold off, height 222; align: horiz left')
        plain_percent_xf =  ezxf('font: bold off, height 222; align: horiz right',num_format_str='0%')
        doses_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color olive_ega',num_format_str="#,##0")
        doses_xf = ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color olive_ega',num_format_str="#,##0")
        final_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color light_green',num_format_str="#,##0")
        final_xf = ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color light_green',num_format_str="#,##0.00")
    
        ws0.row(0).height = 2500
        ws0.col(0).width = 6000
        ws0.write_merge(0,0,0,4,_("Results Summary for {0}".format(m.name)),modelHeading_xf)
        ws0.write_merge(1,1,0,4,_("System Statistics"),divider_1_xf)
        ws0.write_merge(2,2,0,1,"Total Number of Locations",plain_label_xf)
        ws0.write(2,2,getNumberOfLocationsFromModel(m),plain_xf)
        row = 3
        levelCount = m.getLevelCount()
        for level in levelCount[0]:
            ws0.write(row,1,level,plain_label_xf)
            ws0.write(row,2,levelCount[1][level])
            row+=1
#         for level,count in m.getLevelList().items():
#             ws0.write(row,1,level,plain_label_xf)
#             ws0.write(row,2,count,plain_xf)
#             row+=1
        
        #ws0.write_merge(1,1,0,4,_("Vaccine Results"),divider_1_xf)
        
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
    
def getNumberOfLocationsFromModel(model):
    
    placeCount = 0
    for storeId,stores in model.stores.items():
        if not stores.isAttached():
            placeCount += 1
    return placeCount

def getNumberOfLocationsByLevel(model):
    return model.getLevelCount()
    
        
    