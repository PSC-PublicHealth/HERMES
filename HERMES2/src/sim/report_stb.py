#!/usr/bin/env python

########################################################################
# Copyright C 2009, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__="""reporter_stb.py
"""

_hermes_svn_id_="$Id$"

from SimPy.Simulation import * 
from warehouse import warehouseList,clinicList
from xlwt import Workbook
import globals as G

class Reporter_stb(Process):

    def __init__(self, interval, duration, reportFileName, reportFileType = 'csv',onlyAfterBurnin = True):
        Process.__init__(self)
        self.interval = interval
        self.duration  = duration
        self.reportFileType = reportFileType
        self.excelWorkbook = None
        self.excelWorksheets = dict()
        if reportFileType == "xls":
            self.excelDayCounter = 1
            self.excelWorkbook = Workbook()
            self.reportFileName = reportFileName + ".xls"
        elif reportFileType == "csv":
            self.reportFileName = reportFileName + ".csv"
        else:
            raise RuntimeError("Unsupported File Type in Reporter: Please choose csv or xls")
            
        self.reportFile = None

    def run(self):
        raise RuntimeError("The specific derived method class must"\
                           +"define this method")

    def beginReporting(self):
        if self.reportFileType == "csv":
            try:    
                self.reportFile = open(self.reportFileName,"wb")
            except IOError:
                print "There was a problem opening %s in Reporter_stb"%self.reportFile
        
        self.createTableHeader()
        activate(self,self.run())

    def createTableHeader(self):
        raise RuntimeError("The specific derived method class must"\
                           +"define this method")

    def finalizeReporting(self):
        if self.reportFileType == "csv":
            try:
                self.reportFile.close()
            except IOError:
                print "There was a problem closing %s in Reporter_stb"%self.reportFile
        elif self.reportFileType == "xls":
            self.excelWorkbook.save(self.reportFileName)
        else:
            raise RuntimeError("Unsupported File Type in Reporter: Please choose csv or xls")
        
class ReportDailyStock(Reporter_stb):

    def __init__(self,interval,duration, productNameList,reportFileName='report_daily_stock',reportFileType='csv', onlyAfterBurnin=True):
        Reporter_stb.__init__(self,interval,duration,reportFileName,reportFileType, onlyAfterBurnin)
        self.productNameList = productNameList
        self.totalStocks = dict()
   
    def createTableHeader(self):
        
#   Initialize the total dictionary
        
        if self.reportFileType == 'csv':
            self.reportFile.write(',')
            for refW in warehouseList:
                for pn in self.productNameList:
                    w=refW()
                    self.reportFile.write( w.name + ',')   
            self.reportFile.write('\nDay,')           
            for refW in warehouseList:
                for pn in self.productNameList:
                    self.reportFile.write(pn + ',')
            self.reportFile.write('\n')
        elif self.reportFileType == 'xls':
            for refW in warehouseList:
                w = refW()
                for pn in self.productNameList:
                    self.totalStocks[(w.name,pn)] = 0
            self.excelWorksheets['TotalStocks'] = self.excelWorkbook.add_sheet('TotalStocks')
            self.excelWorksheets['TotalStocks'].write(0,0,'Location')
            i=1
            for pn in self.productNameList:
                    self.excelWorksheets['TotalStocks'].write(0,i,pn)
                    i = i + 1
            for refW in warehouseList:
                w=refW()
                self.excelWorksheets[w.name] = self.excelWorkbook.add_sheet(w.name)
                self.excelWorksheets[w.name].write(0,0,'Days')
                i = 1
                for pn in self.productNameList:
                    self.excelWorksheets[w.name].write(0,i,pn)
                    i = i + 1
                        
    def run(self):
        stocks = {}
        for pn in self.productNameList: stocks[pn] = 0              
        #Write the stock data
        while True: #Present (in active or passive state) till the end of simulation
            if G.burninTriggered is True:
                if self.reportFileType == 'csv':
                    self.reportFile.write("\n%g,"%(now()-G.burninTriggerDay))

                for refW in warehouseList: #weak references to warehouses
                    w= refW()
                    if w is None: continue
                
                    for g in w.theBuffer:
                    # Get item count for each group
                        stocks[g.vaccineType.name] += g.nVials 
# update Total Stock 
                
                    if self.reportFileType == 'csv':
                        for pn in self.productNameList: 
                        #print the stocks to a file
                            self.reportFile.write(str(stocks[pn]) + "," )
                            stocks[pn] = 0
                        self.reportFile.write("\n")
                    elif self.reportFileType == 'xls':
                        for pn in self.productNameList:
                            self.totalStocks[(w.name,pn)] += stocks[pn]
                        i = 1
                        self.excelWorksheets[w.name].write((int(now())+1)-G.burninTriggerDay,0,int(now())-G.burninTriggerDay)
                        for pn in self.productNameList:
                            self.excelWorksheets[w.name].write(int(now())+1-G.burninTriggerDay,i,stocks[pn])
                            i = i + 1
                            stocks[pn]=0

            yield hold,self,self.interval # set up to record at the next interval
            
    def createTotalsSpreadSheet(self):

        if self.reportFileType == 'xls':
            rowNumber = 1
            for refW in warehouseList:
                w = refW()
                self.excelWorksheets['TotalStocks'].write(rowNumber,0,w.name)
                colNumber=1
                for pn in self.productNameList:
                    self.excelWorksheets['TotalStocks'].write(rowNumber,colNumber,self.totalStocks[(w.name,pn)])
                    colNumber = colNumber + 1
                rowNumber = rowNumber + 1
                
        else:
            print "Report Daily Stocks: no totals because not using xls format"
            
class ReportDailyTotalVaccinated(Reporter_stb):
    def __init__(self,interval,duration,productNameList,reportFileName="report_daily_vaccinated",reportFileType='csv', onlyAfterBurnin=True):
        Reporter_stb.__init__(self,interval,duration,reportFileName,reportFileType,onlyAfterBurnin)
        self.productNameList = productNameList
        self.previousVC = VaccineCollection()
        self.totalVaccinated = dict()
                
    def createTableHeader(self):
        if self.reportFileType == 'csv':
            self.reportFile.write('\nDay,')        
            for refW in clinicList:
                for pn in self.productNameList:
                    w=refW()
                    self.reportFile.write( w.name + ',')
            self.reportFile.write('\n')
            for refW in clinicList:
                for pn in self.productNameList:
                    self.reportFile.write(pn + ',')
        elif self.reportFileType == 'xls':
            for refW in warehouseList:
                w = refW()
                for pn in self.productNameList:
                    self.totalVaccinated[(w.name,pn)] = 0
            self.excelWorksheets['TotalVaccinated'] = self.excelWorkbook.add_sheet('TotalVaccinated')
            self.excelWorksheets['TotalVaccinated'].write(0,0,'Location')
            colNumber=1
            for pn in self.productNameList:
                    self.excelWorksheets['TotalVaccinated'].write(0,colNumber,pn)
                    colNumber = colNumber + 1
            for refW in clinicList:
                w=refW()
                self.excelWorksheets[w.name] = self.excelWorkbook.add_sheet(w.name)
                self.excelWorksheets[w.name].write(0,0,'Days')
                colNumber = 1
                for pn in self.productNameList:
                    self.excelWorksheets[w.name].write(0,colNumber,pn)
                    colNumber = colNumber + 1
       
    def run(self):
        vaccinated = dict()
        for pn in self.productNameList: vaccinated[pn]=0
        while True: #Present (in active or passive state) till the end of simulation
            if G.burninTriggered is True:
                if self.reportFileType == 'csv':
                    self.reportFile.write("\n%d,"%(now()-G.burninTriggerDay))
    
                for refW in clinicList: #weak references to warehouses
                    w=refW()
                    if w is None: continue
                    note = w.noteHolder
                    for pn in self.productNameList:
                        if note.d.has_key('inc_'+pn+'_treated'):
                            vaccinated[pn] = note.d['inc_'+pn+'_treated']
                    if self.reportFileType == 'csv':
                        for pn in self.productNameList:                   
                            self.reportFile.write(str(vaccinated[pn]) + ",")
                        vaccinated[pn] = 0 #Reset
                        self.reportFile.write("\n")
                    elif self.reportFileType == 'xls':
                        for pn in self.productNameList:
                            self.totalVaccinated[(w.name,pn)] += vaccinated[pn]
                        
                        rowNumber= int(now())+1-G.burninTriggerDay
                        dayNumber = int(now())+1-G.burninTriggerDay
                        self.excelWorksheets[w.name].write(rowNumber,0,dayNumber)
                        colNumber = 1
                        for pn in self.productNameList:
                            self.excelWorksheets[w.name].write(rowNumber,colNumber,vaccinated[pn])
                            colNumber = colNumber + 1
                            vaccinated[pn] = 0
                    note.clearIncNote()
            
                
            yield hold,self,self.interval # set up to record at the next interval

    def createTotalsSpreadSheet(self):
        if self.reportFileType == 'xls':
            rowNumber = 1
            for refW in clinicList:
                w = refW()
                self.excelWorksheets['TotalVaccinated'].write(rowNumber,0,w.name)
                colNumber=1
                for pn in self.productNameList:
                    self.excelWorksheets['TotalVaccinated'].write(rowNumber,colNumber,self.totalVaccinated[(w.name,pn)])
                    colNumber = colNumber + 1
                rowNumber = rowNumber + 1
                
        else:
            print "Report Daily Stocks: no totals because not using xls format"
        
