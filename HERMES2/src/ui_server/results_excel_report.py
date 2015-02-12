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
import shadow_network as shd
import session_support_wrapper as session_support
from HermesServiceException import HermesServiceException
import privs
import htmlgenerator
import typehelper
from costmodel import getCostModelSummary
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError
if 0:
    from xlwt.Workbook import *
    from xlwt.Style import *
    import xlwt
    ezxf = xlwt.easyxf

from openpyxl import Workbook
from openpyxl.compat import range
from openpyxl.cell import get_column_letter
from openpyxl.styles import Style, PatternFill, Border, Side, Alignment, Protection, Font,Color,fills
from openpyxl.worksheet.dimensions import ColumnDimension, RowDimension

import time
from reporthooks import createModelSummaryWSCall
import traceback

from collections import defaultdict

inlizer = session_support.inlizer
_ = session_support.translateString


class XLCell:
    def __init__(self, worksheet, row=1, column=1):
        self.worksheet = worksheet
        self._row = row
        self._column = column
        self._maxRow = row
        self._maxCol = column

    def ws(self):
        return self.worksheet

    def r(self, row = None):
        if row is not None:
            self._row = row
            if self._row > self._maxRow:
                self._maxRow = self._row
        return self._row

    def c(self, column = None):
        if column is not None:
            self._column = column
            if self._column > self._maxCol:
                self._maxCol = self._column
        return self._column

    def maxRow(self, maxRow=None):
        if maxRow is not None:
            self._maxRow = maxRow
        return self._maxRow

    def maxColumn(self, maxColumn=None):
        if maxColumn is not None:
            self_maxCol = maxColumn
        return self._maxCol

    def cell(self, column = None, row = None):
        if column is not None:
            self.c(column)
        if row is not None:
            self.r(row)
        return self.worksheet.cell(row=self._row, column=self._column)

    def right(self, cols=1):
        self.c(self.c() + cols)
        return self.cell()

    def down(self, rows=1):
        self.r(self.r() + rows)
        return self.cell()

    def left(self, cols=1):
        return self.right(-cols)

    def up(self, rows=1):
        return self.down(-rows)

    def set(self, value=None, style=None):
        c = self.cell()
        if value is not None:
            c.value = value
        if style is not None:
            c.style = style
        return c

    def next(self, value = None, style = None):
        c = self.right()
        if value is not None:
            c.value = value
        if style is not None:
            c.style = style
        return c
    
    def postNext(self, value = None, style = None):
        c = self.cell()
        if value is not None:
            c.value = value
        if style is not None:
            c.style = style
        self.right()
        return c
    
    def nextRow(self):
        self._column = 1
        self.down()
        return self.cell()

    def mergeCells(self, columns=1, rows=1):
        self.ws().merge_cells(start_row=self.r(),
                              start_column=self.c(),
                              end_row=self.r() + rows - 1,
                              end_column=self.c() + columns - 1)

    RowHeightCache = {}
    ColumnWidthCache = {}
    def columnWidth(self, width, column=None):
        if column is None:
            column = self.c()
        if width not in self.ColumnWidthCache:
            self.ColumnWidthCache[width] = ColumnDimension(width=width)
        colStr = get_column_letter(column)
        self.ws().column_dimensions[colStr] = self.ColumnWidthCache[width]

    def rowHeight(self, height, row=None):
        if row is None:
            row = self.r()
        if height not in self.RowHeightCache:
            self.RowHeightCache[height] = RowDimension(height=height)
        self.ws().row_dimensions[row] = self.RowHeightCache[height]

medBorder = Border(bottom=Side(style='medium', color='FF000000'), 
                   left=Side(style='medium', color='FF000000'), 
                   right=Side(style='medium', color='FF000000'), 
                   top=Side(style='medium', color='FF000000'))


modelHeadingStyle = Style(font=Font(bold=True, color="FF000000", sz=18.0),
                          fill=PatternFill(patternType=fills.FILL_SOLID,
                                           fgColor=Color('FFFFFFFF')), #fgColor=Color('FF911313')),
                          alignment=Alignment(horizontal='left',
                                              vertical='center',
                                              wrap_text=True),
                          border=Border(bottom=Side(color="FF000000", border_style=None)))

modelHeading2Style = Style(font=Font(bold=True, color="FF000000"),
                          fill=PatternFill(patternType=fills.FILL_SOLID,fgColor=Color('FFFFFFFF')),
                          alignment=Alignment(horizontal='left',
                                              vertical='center',
                                            wrap_text=True),
                          border=Border(bottom=Side(color="FF000000", border_style=None)))

divider1Style = Style(font=Font(bold=True, color="FFFFFFFF"),
                      fill=PatternFill(patternType=fills.FILL_SOLID,
                                       fgColor=Color('FF0000FF')),
                      alignment=Alignment(horizontal='left',
                                          vertical='bottom',
                                          wrap_text=True),
                      border=Border(bottom=Side(color="FF000000", 
                                                border_style=None)))

divider2Style = Style(font=Font(bold=True, color="FFFFFFFF"),
                      fill=PatternFill(patternType=fills.FILL_SOLID,
                                       fgColor=Color('FF3709EF')),
                      alignment=Alignment(horizontal='left',
                                          vertical='bottom',
                                          wrap_text=True),
                      border=Border(bottom=Side(color="FF000000", 
                                                border_style=None)))

labelStyle = Style(font=Font(bold=True, color="FF000000"),
                          fill=PatternFill(patternType=fills.FILL_SOLID,
                                           fgColor=Color('FFA0A8EC')),
                          alignment=Alignment(horizontal='left',
                                              vertical='center',
                                              wrap_text=True),
                          border=Border(bottom=Side(color="FF000000", 
                                                    border_style=None)))

labelStyleCenter = Style(font=Font(bold=True, color="FF000000"),
                         fill=PatternFill(patternType=fills.FILL_SOLID,
                                          fgColor=Color('FFA0A8EC')),
                         alignment=Alignment(horizontal='center',
                                             vertical='center',
                                             wrap_text=True),
                         #border=None
                         )

levelStyle = Style(font=Font(bold=True),
                   # fill=PatternFill(fill_type=None,start_color='dark_red',
                   #  end_color='dark_red'),
                   alignment=Alignment(horizontal='left',
                                       vertical='center'))   

levelTotalStyle = levelStyle
totalStyle = Style(font=Font(bold=True),
                   # fill=PatternFill(fill_type=None,start_color='dark_red',
                   #  end_color='dark_red'),
                   alignment=Alignment(horizontal='right',
                                       vertical='center'))   



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


@bottle.route('/json/create-xls-summary-openpyxl')
def createExcelSummaryOpenPyXl(db, uiSession):
    print "I got here!"
    try:
        modelJSON = createModelSummaryWSCall(db, uiSession)
        fname = _safeGetReqParam(bottle.request.params, 'filename', isInt=False)
        modelId = _safeGetReqParam(bottle.request.params, 'modelId', isInt=False)
        resultsId = _safeGetReqParam(bottle.request.params, 'resultsId', isInt=False)
        hr = db.query(shd.HermesResults).filter(shd.HermesResults.resultsId==resultsId).one()

        levelSummary = summarizeByLevel(hr)

    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()
        return {'success':False, 'msg':str(e)}
    
    try:
        wb = Workbook()
        summary_sheet = wb.create_sheet(0)
        summary_sheet.title = "Model Summary"
        #summary_sheet.row_dimensions[1] = RowDimension(height=22.0)
        #summary_sheet.row_dimensions[4] = RowDimension(height=30.0)

        ss = XLCell(summary_sheet)

        ss.mergeCells(5)
        ss.rowHeight(22)
        ss.postNext(modelJSON['name'], modelHeadingStyle)

        ss.nextRow()
        ss.mergeCells(5)
        ss.postNext(_("Overall System Statistics"), modelHeading2Style)
        
        ss.nextRow()
        ss.mergeCells(5)
        ss.postNext(_("Facility Statistics"), divider1Style)
        
        ss.nextRow()

        levels = modelJSON['orderedLevelList']
        levelCount = modelJSON['fixedLocationCount']
        vaccLevelCount = modelJSON['vaccinationLocationCount']
        
        ss.rowHeight(30)
        headers = ["Level", "Total", "Vaccinating", "Average Peak Storage", "Total Volume"]
        for header in headers:
            ss.postNext(header, labelStyle)

        ss.nextRow()
        
        for level in levels:
            if level in levelCount.keys():
                ss.postNext(level, levelStyle)
                ss.postNext(levelCount[level], plainStyle)
                if level in vaccLevelCount.keys():
                    ss.postNext(vaccLevelCount[level], plainStyle)
                else:
                    ss.postNext(0, plainStyle)
                ss.nextRow()

        ss.postNext(_("All Levels"), levelTotalStyle)
        ss.postNext(levelCount['Total'], totalStyle)
        ss.postNext(vaccLevelCount['Total'], totalStyle)
        
        vCols = [(_("Vaccine"), "Name"),
                 (_("Availability"), "SupplyRatio"),
                 (_("Doses Needed"), "Applied"),
                 (_("Doses Received"), "Treated"),
                 (_("Open Vial Waste"), "OpenVialWasteFrac"),
                 (_("Vials Opened"), "VialsUsed"),
                 (_("Vials Procured"), "VialsCreated"),
                 (_("Vials Spoiled"), "VialsExpired"),
                 #(_("Vials Broken"), "VialsBroken"),
                 (_("% Stored 2 to 8 C"), "coolerStorageFrac"),
                 (_("% Stored Below 2 C"), "freezerStorageFrac")]
        ss.nextRow()
        ss.nextRow()
        ss.mergeCells(len(vCols))
        ss.set(_("Vaccine Statistics"), divider1Style)
        ss.nextRow()
        ss.rowHeight(30)
        for header, attr in vCols:
            ss.postNext(header, labelStyle)
        ss.nextRow()
            
        for rec in hr.summaryRecs.values():
            if not isinstance(rec, shd.ShdVaccineSummary):
                continue
            for header, attr in vCols:
                ss.postNext(getattr(rec, attr), plainStyle)
            ss.nextRow()



        popLevelCount = modelJSON['populationLevelCount']
        numColumns = len(popLevelCount)
        
        ss.nextRow()
        ss.mergeCells(1 + 4*numColumns)
        ss.postNext(_("Population Statistics"), divider1Style)

        ss.nextRow()

        ## Get an ordered list to make all consistent
        popCats = sorted([x for x in popLevelCount['Total'].keys()])

        levelList = []
        for level in levels:
            if level in popLevelCount.keys():
                levelList.append((level,level))
        levelList.append((_("All Levels"), "Total"))

        statList = ((_("Total"), 'count'),
                    (_("Average"), 'ave'),
                    (_("Minimum"), 'min'),
                    (_("Maximum"), 'max'))

        ss.set(style=labelStyleCenter)
        ss.down()
        ss.set(style=labelStyleCenter)
        ss.up()
        ss.right()
        for title, level in levelList:
            ss.mergeCells(len(statList))
            ss.set(title, labelStyleCenter)
            ss.down()
            for statLabel, stat in statList:
                ss.postNext(statLabel, labelStyle)
            ss.up()
        
        ss.nextRow()
        ss.nextRow()

        for cat in popCats:
            ss.postNext(cat, levelStyle)
            for title, level in levelList:
                for statLabel, stat in statList:
                    if cat in popLevelCount[level].keys():
                        val = round(popLevelCount[level][cat][stat])
                    else:
                        val = 0
                    ss.postNext(val, plainStyle)
            ss.nextRow()


        ss.nextRow()
        row = ss.r()
        col=1
        ss.mergeCells(9)
        ss.set(_("Transport Route Statistics"), divider2Style)
        ss.nextRow()
        row+=1
        
        ## Get an ordered list to make all consistent
        routeLevelDict = modelJSON['routeLevelCount']
        ss.postNext(style=labelStyleCenter)
        ss.mergeCells(4)
        ss.set(_("Distance (KM)"), labelStyleCenter)
        ss.right(4)
        ss.mergeCells(2)
        ss.set(_("Route Types"), labelStyleCenter)
        ss.right(2)
        ss.mergeCells(2)
        ss.set(_("Vehicles"), labelStyleCenter)
        ss.nextRow()

        for label in (_("Level"), 
                      _("Total"), _("Average"), _("Minimum"), _("Maximum"),
                      _("Type"), _("Count"),
                      _("Type"), _("Count")):
            ss.postNext(label, labelStyle)

        ss.nextRow()

        for level in levels:
            if level not in routeLevelDict.keys():
                continue
            ss.postNext(level, levelStyle)
            for stat in ('total', 'ave', 'min', 'max'):
                ss.postNext(round(routeLevelDict[level]['distance'][stat], 2), plainStyle)
            
            rTypeCounts = routeLevelDict[level]['routeTypeCount']
            tTypeCounts = routeLevelDict[level]['vehicleCount']
            for (routeItem, truckItem) in map(None,
                                              rTypeCounts.items(),
                                              tTypeCounts.items()):
                if routeItem is not None:
                    ss.postNext(routeItem[0])
                    ss.postNext(routeItem[1])
                else:
                    ss.right(2)
                if truckItem is not None:
                    ss.postNext(truckItem[0])
                    ss.postNext(truckItem[1])
                else:
                    ss.right(2)
                ss.left(4)
                ss.down()

            ss.cell(column=1)

        ss.nextRow()
        
        if len(hr.costSummaryRecs) > 0:
            if isinstance(hr.costSummaryRecs[0], shd.ShdMicro1CostSummaryGrp):
                summarizeMicroCostLevels(hr, levels, ss)

            elif isinstance(hr.costSummaryRecs[0], shd.ShdLegacyCostSummary):
                ss.set("legacycostsummary")
            else:
                ss.set("unknown cost summary")
            
            ss.nextRow()


        ss.columnWidth(20, column=1)
        for i in xrange(2, ss.maxColumn()):
            ss.columnWidth(15, column=i)



        dev_inventory_sheet = wb.create_sheet(1)
        dev_inventory_sheet.title = _("Level-wise Device Inventory")

        dis = XLCell(dev_inventory_sheet)
        dis.columnWidth(20, column=1)
        dis.columnWidth(30, column=2)
        dis.columnWidth(15, column=3)


        dis.mergeCells(3)
        dis.set(_("Device Inventory by Level"), divider1Style)
        dis.nextRow()
        dis.rowHeight(30)
        for label in (_("Level"), _("Device"), _("Number of Devices")):
            dis.postNext(label, labelStyle)
        
        dis.nextRow()
        
        inventoryCount = modelJSON['inventoryLevelCount']
        
        for level in levels:
            if level in inventoryCount.keys():
                dis.set(level, levelStyle)
                for dev,count in inventoryCount[level].items():
                    dis.next(dev, plainLabelStyle)
                    dis.next(count, plainStyle)
                    dis.nextRow()
        
                    
                    
        
        heir_sheet = wb.create_sheet(2)
        heir_sheet.title = "Store Locations"

        hs = XLCell(heir_sheet)

        heirInfo = modelJSON['heirarchicalStores']
        hs.nextRow()

        for placeDict in heirInfo:
            hs.right(placeDict['depth'])
            hs.postNext(placeDict['name'], plainLabelStyle)
            hs.nextRow()

        levCol = hs.maxColumn() + 1


        hs.r(1)
        hs.mergeCells(levCol - 1)
        hs.set("Storage Locations", divider1Style)
        hs.c(levCol)
        hs.postNext("Level", divider1Style)
        hs.postNext("Latitude", divider1Style)
        hs.postNext("Longitude", divider1Style)
        hs.nextRow()
        for placeDict in heirInfo:
            dep = placeDict['depth']
            if dep > 1:
                hs.mergeCells(dep)
            hs.right(dep)
            hs.mergeCells(levCol- dep - 1)
            hs.c(levCol)
            hs.postNext(placeDict['level'], plainLabelStyle)
            if placeDict['latitude'] != 0.0 and placeDict['longitude'] != 0.0:
                hs.postNext(placeDict['latitude'], plainLabelStyle)
                hs.postNext(placeDict['longitude'], plainLabelStyle)
            hs.nextRow()

        for i in xrange(1,levCol-1):
            hs.columnWidth(6, column=i)
        hs.columnWidth(20, column=levCol-1)
        hs.columnWidth(20, column=levCol)
        hs.columnWidth(15, column=levCol+1)
        hs.columnWidth(15, column=levCol+2)


        with uiSession.getLockedState() as state:
            (fileKey, fullFileName) = \
                state.fs().makeNewFileInfo(shortName="%s.xlsx" % fname,
                                           fileType='application/vnd.ms-excel',
                                           deleteIfPresent=True)
                
            wb.save(fullFileName)
        return {'success':True, 'xlsfilename':fullFileName}
    
    except Exception as e:
        print 'Exception: %s'%e
        traceback.print_exc()

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


def summarizeByLevel(hr):
    deliveryVol = defaultdict(lambda : 0)
    levelCount = defaultdict(lambda : 0)

    for sr in hr.storesRpts.values():
        deliveryVol[sr.category] += sr.tot_delivery_vol
        levelCount[sr.category] += 1

    ret = {}
    ret['deliveryVol'] = deliveryVol
    ret['levelCount'] = levelCount

    return ret

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
    
#class Micro1CostModelHierarchicalSummary(CostModelHierarchicalSummary):
#    costGroups = {'so
def summarizeMicroCostLevels(hr, levels, ss):
    costGroups = {'solar': ('s_energy', 's_total', 'total'), #'fuel/power',
                  'electric': ('s_energy', 's_total', 'total'), #'fuel/power',
                  'diesel': ('s_energy', 's_total', 'total'), #'fuel/power',
                  'gasoline': ('t_fuel', 't_total', 'total'), #'fuel/power',
                  'kerosene': ('s_energy', 's_total', 'total'), #'fuel/power',
                  'petrol': ('s_energy', 's_total', 'total'), #'fuel/power',
                  'ice': ('s_energy', 's_total', 'total'), #'fuel/power',
                  'propane': ('s_energy', 's_total', 'total'), #'fuel/power',
                  'StaffSalary': ('personnel', 'total'), # 'staff',
                  'PerDiem': ('t_perdiem', 't_total', 'total'), #'staff',
                  'TransitFareCost': ('t_fare', 't_total', 'total'), #'staff',
                  'Vaccines': ('vax', 'total'), #'cargo',
                  'BuildingCost': ('building', 'total'), #'equipment',
                  'FridgeAmort': ('s_amort', 's_total', 'total'), #'equipment',
                  'TruckAmort': ('t_amort', 't_total', 'total'), #'equipment',
                  'TruckMaint': ('t_maint', 't_total', 'total'), #'equipment',
                  'FridgeMaint': ('s_maint', 's_total', 'total'), #'equipment',
                  'SolarMaint': ('s_maint', 's_total', 'total'), #'equipment'
                  # other things I've found:
                  'LaborCost':  ('personnel', 'total'),
                  'Storage': ('s_maint', 's_total', 'total'),
                  'Transport': ('t_maint', 't_total', 'total'),
                  }

    columns = (
        (_("Storage"), ((_("Energy Usage"), 's_energy'),
                        (_("Equipment Maintenance"), 's_maint'),
                        (_("Equipment Amortization"), 's_amort'),
                        (_("Total"), 's_total'))),
        (_("Transport"), ((_("Fuel Usage"), 't_fuel'),
                          (_("Vehicle Maintenance"), 't_maint'),
                          (_("Vehicle Amortization"), 't_amort'),
                          (_("Fixed Fares"), 't_fare'),
                          (_("Per Diems"), 't_perdiem'),
                          (_("Total"), 't_total'))),
        (_("Personnel"), ((_("Total"), "personnel"),)),
        (_("Building"), ((_("Total"), "building"),)),
        (_("Vaccine Procurement"), ((_("Total"), "vax"),)),
#        (_("Logistics"), # We don't have anything under this heading
        (_("Total Costs"), ((_("Including Procurement"), 'total'),)),
        )

    columnCount = 1 # include the row header (level)
    for h,c in columns:
        columnCount += len(c)

    ss.mergeCells(columnCount)
    ss.set(_("Costs By Level"), divider1Style)
    ss.nextRow()
    
    ss.rowHeight(30)
    ss.postNext("", labelStyleCenter)
    for h,c in columns:
        ss.mergeCells(len(c))
        ss.set(h, labelStyleCenter)
        ss.right(len(c))

    ss.nextRow()
    ss.rowHeight(30)
    ss.postNext("Level", labelStyle)
    for h, cList in columns:
        for cHead,data in cList:
            ss.postNext(cHead, labelStyle)
 
    ss.nextRow()

    levelCsrs = {}
    for csr in hr.costSummaryRecs:
        if csr.ReportingBranch in levels:
            levelCsrs[csr.ReportingBranch] = csr  # make it so I can find this later

    for level in levels:
        if level not in levelCsrs:
            continue
        levelInfo = defaultdict(lambda : 0)
        unknownCategories = []
        csr = levelCsrs[level]
        for ce in csr.costEntries:
            cc = ce.costCategory
            if cc.startswith('m1C_'):
                cc = cc[4:]
            if cc not in costGroups:
                unknownCategories.append(cc)
                continue
            for grouping in costGroups[cc]:
                levelInfo[grouping] += ce.cost
        
        ss.postNext(level, levelStyle)
        for h, cList in columns:
            for cHead, data in cList:
                ss.postNext(round(levelInfo[data], 2), plainStyle)
        if len(unknownCategories) > 0:
            ss.set("unknown categories: %s"%unknownCategories)
        ss.nextRow()

