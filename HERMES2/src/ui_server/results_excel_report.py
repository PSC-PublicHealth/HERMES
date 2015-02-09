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

from openpyxl.styles import alignment

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_ = "$Id: resultshooks.py 1927 2014-09-25 21:45:00Z welling $"

import sys, os, os.path, time, json, math, types
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
import time
from reporthooks import createModelSummaryWSCall


inlizer = session_support.inlizer
_ = session_support.translateString

@bottle.route('/json/create-xls-summary-openpyxl')
def createExcelSummaryOpenPyXl(db, uiSession):
    try:
        modelJSON = createModelSummaryWSCall(db, uiSession)
        fname = _safeGetReqParam(bottle.request.params, 'filename', isInt=False)
    except Exception as e:
        return {'success':False, 'msg':str(e)}
    
    from openpyxl import Workbook
    from openpyxl.compat import range
    from openpyxl.cell import get_column_letter
    from openpyxl.styles import Style, PatternFill, Border, Side, Alignment, Protection, Font,Color,fills
     
    try:
        wb = Workbook()
        summary_sheet = wb.create_sheet(0)
        summary_sheet.title = "Model Summary"
        
        modelHeadingStyle = Style(font=Font(bold=True, color="FFFFFFFF"),
                                  fill=PatternFill(patternType=fills.FILL_SOLID,fgColor=Color('FF911313')),
                                  alignment=Alignment(horizontal='left',
                                                      vertical='center',
                                                    wrap_text=True),
                                  border=Border(bottom=Side(color="FF000000", border_style=None)))
        
        divider1Style = Style(font=Font(bold=True, color="FFFFFFFF"),
                                  fill=PatternFill(patternType=fills.FILL_SOLID,fgColor=Color('FF3709EF')),
                                  alignment=Alignment(horizontal='left',
                                                      vertical='center',
                                                    wrap_text=True),
                                  border=Border(bottom=Side(color="FF000000", border_style=None)))
        divider2Style = Style(font=Font(bold=True, color="FFFFFFFF"),
                                  fill=PatternFill(patternType=fills.FILL_SOLID,fgColor=Color('FFA0A8EC')),
                                  alignment=Alignment(horizontal='left',
                                                      vertical='center',
                                                      wrap_text=True),
                                  border=Border(bottom=Side(color="FF000000", border_style=None)))                               
        
        plainStyle = Style(font=Font(bold=False),
                           # fill=PatternFill(fill_type=None,start_color='dark_red',end_color='dark_red'),
                           alignment=Alignment(horizontal='right',
                                               vertical='center'))   
        plainCenteredStyle = Style(font=Font(bold=False),
                           # fill=PatternFill(fill_type=None,start_color='dark_red',end_color='dark_red'),
                           alignment=Alignment(horizontal='center',
                                               vertical='center'))   
        plainLabelStyle = Style(font=Font(bold=False),
                           # fill=PatternFill(fill_type=None,start_color='dark_red',end_color='dark_red'),
                                alignment=Alignment(horizontal='left',
                                                    vertical='center'))     
        totalStyle = Style(font=Font(bold=True),
                           # fill=PatternFill(fill_type=None,start_color='dark_red',end_color='dark_red'),
                           alignment=Alignment(horizontal='right',
                                               vertical='center')) 
        totalLabelStyle = Style(font=Font(bold=True),
                           # fill=PatternFill(fill_type=None,start_color='dark_red',end_color='dark_red'),
                           alignment=Alignment(horizontal='left',
                                               vertical='center'))                         
                                            
        
        summary_sheet.merge_cells(start_row=1,start_column=1,end_row=1,end_column=4)
        summary_sheet["A1"] = modelJSON['name']
        summary_sheet["A1"].style = modelHeadingStyle
        
        row=2
        col=1
        summary_sheet.merge_cells(start_row=row,start_column=col,end_row=row,end_column=col+3) 
        summary_sheet.cell(row=row,column=col).value = _("Overall System Statistics")
        summary_sheet.cell(row=row,column=col).style = divider1Style
        
        row+=1
        summary_sheet.merge_cells(start_row=row,start_column=col,end_row=row,end_column=col+3) 
        summary_sheet.cell(row=row,column=col).value = _("Facility Statistics")
        summary_sheet.cell(row=row,column=col).style = divider2Style
        
        row+=1
        levels = modelJSON['orderedLevelList']
        levelCount = modelJSON['fixedLocationCount']
        vaccLevelCount = modelJSON['vaccinationLocationCount']
            
        summary_sheet.cell(row=row,column=1).value   = "Level"
        summary_sheet.cell(row=row,column=col+1).value = "Total"
        summary_sheet.cell(row=row,column=col+2).value = "Vaccinating"
        
        row+=1  
        for level in levels:
            if level in levelCount.keys():
                summary_sheet.cell(row=row,column=1).value = level
                summary_sheet.cell(row=row,column=1).style = plainLabelStyle
                summary_sheet.cell(row=row,column=2).value = levelCount[level]
                summary_sheet.cell(row=row,column=2).style = plainStyle
                if level in vaccLevelCount.keys():
                    summary_sheet.cell(row=row,column=3).value = vaccLevelCount[level]
                else:
                    summary_sheet.cell(row=row,column=3).value = 0
                summary_sheet.cell(row=row,column=3).style = plainStyle
                row += 1
        summary_sheet.cell(row=row,column=1).value = _("All Levels")
        summary_sheet.cell(row=row,column=1).style = totalLabelStyle
        summary_sheet.cell(row=row,column=2).value = levelCount['Total']
        summary_sheet.cell(row=row,column=2).style = totalStyle
        summary_sheet.cell(row=row,column=3).value = vaccLevelCount['Total']
        summary_sheet.cell(row=row,column=3).style = totalStyle
        
        popLevelCount = modelJSON['populationLevelCount']
        numColumns = len(popLevelCount)
        
        summary_sheet.merge_cells(start_row=row,start_column=col,end_row=row,end_column=col+4*numColumns) 
        summary_sheet.cell(row=row,column=col).value = _("Population Statistics")
        summary_sheet.cell(row=row,column=col).style = divider2Style
        row+=1
        
        col=2
        ## Get an ordered list to make all consistent
        popCats = sorted([x for x in popLevelCount['Total'].keys()])
        origRow = row
        for level in levels:
            if level in popLevelCount.keys():
                summary_sheet.merge_cells(start_row=row,start_column=col,end_row=row,end_column=col+3)
                summary_sheet.cell(row=row,column=col).value = level
                summary_sheet.cell(row=row,column=col).style = plainCenteredStyle
                summary_sheet.cell(row=row+1,column=col).value = _("Total")
                summary_sheet.cell(row=row+1,column=col+1).value = _("Average")
                summary_sheet.cell(row=row+1,column=col+2).value = _("Minimum")
                summary_sheet.cell(row=row+1,column=col+3).value = _("Maximum")
                col+=4
        summary_sheet.merge_cells(start_row=row,start_column=col,end_row=row,end_column=col+3)
        summary_sheet.cell(row=row,column=col).value = _("All Levels")
        summary_sheet.cell(row=row,column=col).style = plainCenteredStyle
        summary_sheet.cell(row=row+1,column=col).value = _("Total")
        summary_sheet.cell(row=row+1,column=col+1).value = _("Average")
        summary_sheet.cell(row=row+1,column=col+2).value = _("Minimum")
        summary_sheet.cell(row=row+1,column=col+3).value = _("Maximum")
        row+=2
        for cat in popCats:
            summary_sheet.cell(row=row,column=1).value = cat
            row +=1
        
        col=2
        for level in levels:
            row=origRow+2
            if level in popLevelCount.keys():
                for cat in popCats:
                    if cat in popLevelCount[level].keys():
                        summary_sheet.cell(row=row,column=col).value   = popLevelCount[level][cat]['count']
                        summary_sheet.cell(row=row,column=col+1).value = round(popLevelCount[level][cat]['ave'])
                        summary_sheet.cell(row=row,column=col+2).value = popLevelCount[level][cat]['min']
                        summary_sheet.cell(row=row,column=col+3).value = popLevelCount[level][cat]['max']
                    else:
                        summary_sheet.cell(row=row,column=col).value   = 0
                        summary_sheet.cell(row=row,column=col+1).value = 0#popLevelCount[level][cat]['ave']
                        summary_sheet.cell(row=row,column=col+2).value = 0#popLevelCount[level][cat]['min']
                        summary_sheet.cell(row=row,column=col+3).value = 0#popLevelCount[level][cat]['max']
                    row+= 1
                col+=4
        row=origRow+2
        for cat in popCats:
            summary_sheet.cell(row=row,column=col).value   = popLevelCount["Total"][cat]['count']
            summary_sheet.cell(row=row,column=col+1).value = round(popLevelCount["Total"][cat]['ave'])
            summary_sheet.cell(row=row,column=col+2).value = popLevelCount["Total"][cat]['min']
            summary_sheet.cell(row=row,column=col+3).value = popLevelCount["Total"][cat]['max']
            row+=1
            
        col=1
        summary_sheet.merge_cells(start_row=row,start_column=col,end_row=row,end_column=col+8) 
        summary_sheet.cell(row=row,column=col).value = _("Transport Route Statistics")
        summary_sheet.cell(row=row,column=col).style = divider2Style
        row+=1
        
        ## Get an ordered list to make all consistent
        routeLevelDict = modelJSON['routeLevelCount']
        summary_sheet.merge_cells(start_row=row,start_column=2,end_row=row,end_column=5)
        summary_sheet.cell(row=row,column=2).value = _("Distance (KM)")
        summary_sheet.merge_cells(start_row=row,start_column=6,end_row=row,end_column=7)
        summary_sheet.cell(row=row,column=6).value = _("Route Types")
        summary_sheet.merge_cells(start_row=row,start_column=8,end_row=row,end_column=9)
        summary_sheet.cell(row=row,column=8).value = _("Vehicles")
        row +=1
        summary_sheet.cell(row=row,column=1).value = _("Level")
        summary_sheet.cell(row=row,column=2).value = _("Total")
        summary_sheet.cell(row=row,column=3).value = _("Average")
        summary_sheet.cell(row=row,column=4).value = _("Minimum")
        summary_sheet.cell(row=row,column=5).value = _("Maximum")
        summary_sheet.cell(row=row,column=6).value = _("Type")
        summary_sheet.cell(row=row,column=7).value = _("Count")
        summary_sheet.cell(row=row,column=8).value = _("Type")
        summary_sheet.cell(row=row,column=9).value = _("Count")
        row+=1
        maxRow = row
        for level in levels:
            if level in routeLevelDict.keys():
                summary_sheet.cell(row=row,column=1).value = _(level)
                summary_sheet.cell(row=row,column=2).value = round(routeLevelDict[level]['distance']['total'],2)
                summary_sheet.cell(row=row,column=3).value = round(routeLevelDict[level]['distance']['ave'],2)
                summary_sheet.cell(row=row,column=4).value = round(routeLevelDict[level]['distance']['min'],2)
                summary_sheet.cell(row=row,column=5).value = round(routeLevelDict[level]['distance']['max'],2)
                rowInc = 0
                for rType,count in routeLevelDict[level]['routeTypeCount'].items():
                    summary_sheet.cell(row=row+rowInc,column=6).value = rType
                    summary_sheet.cell(row=row+rowInc,column=7).value = count
                    rowInc += 1
                    if row+rowInc > maxRow:
                        maxRow = row+rowInc
                rowInc=0
                for tType,count in routeLevelDict[level]['vehicleCount'].items():
                    summary_sheet.cell(row=row+rowInc,column=8).value = tType
                    summary_sheet.cell(row=row+rowInc,column=9).value = count
                    rowInc += 1
                    if row+rowInc > maxRow:
                        maxRow = row+rowInc
                row = maxRow
        
        dev_inventory_sheet = wb.create_sheet(1)
        dev_inventory_sheet.title = _("Level-wise Device Inventory")
        
        dev_inventory_sheet.merge_cells(start_row=1,end_row=1,start_column=1,end_column=4)
        dev_inventory_sheet.cell(row=1,column=1).value = _("Device Inventory by Level")
        dev_inventory_sheet.cell(row=1,column=1).style = divider1Style
        
        dev_inventory_sheet.cell(row=2,column=1).value = _("Level")
        dev_inventory_sheet.cell(row=2,column=2).value = _("Device")
        dev_inventory_sheet.cell(row=2,column=3).value = _("Number of Devices")
        
        row=3
        inventoryCount = modelJSON['inventoryLevelCount']
        
        for level in levels:
            if level in inventoryCount.keys():
                dev_inventory_sheet.cell(row=row,column=1).value = level
                for dev,count in inventoryCount[level].items():
                    dev_inventory_sheet.cell(row=row,column=2).value = dev
                    dev_inventory_sheet.cell(row=row,column=3).value = count
                    row+=1
        
                    
                    
        
        heir_sheet = wb.create_sheet(2)
        heir_sheet.title = "Store Locations"
        
        heirInfo = modelJSON['heirarchicalStores']
        row=2
        maxDepth = 0
        for placeDict in heirInfo:
            col = 1+placeDict['depth']
            if placeDict['depth'] > maxDepth: maxDepth = placeDict['depth']
            heir_sheet.cell(row=row,column=col).value = placeDict['name']
            heir_sheet.cell(row=row,column=col+1).value = placeDict['level']
            row+=1
        maxDepth+=1
        heir_sheet.merge_cells(start_row=1,end_row=1,start_column=1,end_column=1+maxDepth)
        heir_sheet.cell(row=1,column=1).value = "Storage Locations"
        heir_sheet.cell(row=1,column=maxDepth+2).value="Latitude"
        heir_sheet.cell(row=1,column=maxDepth+3).value="Longitude"
        
        row=2
        
        for placeDict in heirInfo:
            print "PlaceDict  = " + str(placeDict)
            if placeDict['latitude'] != 0.0 and placeDict['longitude'] != 0.0:
                heir_sheet.cell(row=row,column=maxDepth+2).value = placeDict['latitude']
                heir_sheet.cell(row=row,column=maxDepth+3).value = placeDict['latitude']
                row+=1
        with uiSession.getLockedState() as state:
            (fileKey, fullFileName) = \
                state.fs().makeNewFileInfo(shortName="%s.xlsx" % fname,
                                           fileType='application/vnd.ms-excel',
                                           deleteIfPresent=True)
                
            wb.save(fullFileName)
        return {'success':True, 'xlsfilename':fullFileName}
    
    except Exception as e:
        return {'success':False, 'msg':str(e)}
    
# @bottle.route('/json/create-xls-summary')
# def createExcelSummary(db, uiSession):
#     try:
#         modelJSON = createModelSummary(db, uiSession)
#     except Exception as e:
#         return {'success':False, 'msg':str(e)}
#     
#     try:
#         fname = _safeGetReqParam(bottle.request.params, 'filename', isInt=False)
#         # ## First create a summary page
#         style = XFStyle()
#         wb = Workbook()
#         ws0 = wb.add_sheet('Summary')
#     
#         row = 0
#         col = 1
#         # Define some formatting styles for the spreadsheet.
#         modelHeading_xf = ezxf('font: bold on, height 240; align: wrap on, horiz centre, vert top; borders: bottom thin')
#         divider_1_xf = ezxf('font: bold on, height 222, colour white; align: horiz left; pattern: pattern solid, fore-color dark_red; borders: bottom thin')
#         divider_2_xf = ezxf('font: bold on, height 222, colour white; align: horiz left; pattern: pattern solid, fore-color light_blue; borders: bottom thin')
#         total_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color grey25', num_format_str='0%')
#         total_percent_xf = ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color grey25', num_format_str='0%')
#         total_xf = ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color grey25', num_format_str='#,##0')
#         plain_xf = ezxf('font: bold off, height 222; align: horiz right', num_format_str="#,##0")
#         plain_label_xf = ezxf('font: bold off, height 222; align: horiz left')
#         plain_percent_xf = ezxf('font: bold off, height 222; align: horiz right', num_format_str='0%')
#         doses_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color olive_ega', num_format_str="#,##0")
#         doses_xf = ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color olive_ega', num_format_str="#,##0")
#         final_label_xf = ezxf('font: bold on, height 222; align: horiz left; pattern: pattern solid, fore-color light_green', num_format_str="#,##0")
#         final_xf = ezxf('font: bold on, height 222; align: horiz right; pattern: pattern solid, fore-color light_green', num_format_str="#,##0.00")
#     
#         ws0.row(0).height = 2500
#         # ws0.col(0).width = 6000
#         # ws0.col(1).width = 3000
#         # ws0.col(2).width = 3000
#         ws0.write_merge(0, 0, 0, 4, _("Results Summary for {0}".format(modelJSON['name'])), modelHeading_xf)
#         ws0.write_merge(1, 1, 0, 4, _("Overal System Statistics"), divider_1_xf)
#         ws0.write_merge(2, 2, 0, 4, _("Facility Statistics"), divider_2_xf)
#         ws0.write(3, 0, "Level", plain_label_xf)
#         ws0.write(3, 1, "Total", plain_label_xf)
#         ws0.write(3, 2, "Vaccinating", plain_label_xf)
#         row = 4
#         levels = modelJSON['orderedLevelList']
#         levelCount = modelJSON['fixedLocationCount']
#         vaccLevelCount = modelJSON['vaccinationLocationCount']
#         for level in levels:
#             if level in levelCount.keys():
#                 ws0.write(row, 0, level, plain_label_xf)
#                 ws0.write(row, 1, levelCount[level])
#                 if level in vaccLevelCount.keys():
#                     ws0.write(row, 2, vaccLevelCount[level])
#                 else:
#                     ws0.write(row, 2, 0)
#                 row += 1
#         ws0.write(row, 0, "All Levels", total_label_xf)
#         ws0.write(row, 1, levelCount['Total'], total_xf)
#         ws0.write(row, 2, vaccLevelCount['Total'], total_xf)
#         # ## Fit the column widths
#         # for i in range(4):
#         #    for j in range(row):
#                 
#        
#         
#         
# #         for level,count in m.getLevelList().items():
# #             ws0.write(row,1,level,plain_label_xf)
# #             ws0.write(row,2,count,plain_xf)
# #             row+=1
#         
#         # ws0.write_merge(1,1,0,4,_("Vaccine Results"),divider_1_xf)
#         
#         with uiSession.getLockedState() as state:
#             (fileKey, fullFileName) = \
#                 state.fs().makeNewFileInfo(shortName="%s.xls" % fname,
#                                            fileType='application/vnd.ms-excel',
#                                            deleteIfPresent=True)
#                 
#             wb.save(fullFileName)
#         return {'success':True, 'xlsfilename':fullFileName}
#     except Exception as e:
#         return {'success':False, 'msg':str(e)}
     

@bottle.route('/downloadXLS')
def downloadXLS(db, uiSession):
    shortname = _safeGetReqParam(bottle.request.params, 'shortname', isInt=False)
    xlsName = "%s.xlsx" % shortname
    with uiSession.getLockedState() as state:
        fullname = "%s/%s.xlsx" % (state.fs().workDir, shortname)
    return bottle.static_file(xlsName, os.path.dirname(fullname),
                              mimetype='application/vnd.ms-excel', download=xlsName)
    
@bottle.route('/json/downloadSVG',method='post')
def downloadSVG(db,uiSession):
    try:
        import json
        from xml.dom import minidom
        data = json.load(bottle.request.body)
        print '1243135315214234325124351341324554513431514513546514452465135315'
        print "Data = " + str(data)
        #print type(data.data)
        #svgXML = minidom.parse(str(data['data']))
        print "Trying to save this fucking file!!!!!"
        with uiSession.getLockedState() as state:
            #fullname = "{0}/test.svg".format(state.fs().workDir)
            fullname = "test.svg"
        with open(fullname,"wb") as f:
            f.write(data['data'])
        return {'success':True}
    
    except bottle.HTTPResponse:
        raise # bottle will handle this
    except Exception,e:
        result = {'success':False, 'type':'error', 'msg':_("Problem saving SVG XML: ") + str(e)}
        return result  
    
    
def getNumberOfLocationsFromModel(model):
    placeCount = 0
    vaccinatingCount = 0
    for storeId, store in model.stores.items():
        if store.isVaccinating():
            vaccinatingCount += 1
        if not store.isAttached():
            placeCount += 1
    return (placeCount, vaccinatingCount)

def getNumberOfLocationsByLevel(model):
    return model.getLevelCount()
    

