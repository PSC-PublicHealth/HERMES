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

__doc__="""reporter.py
The reporter wakes up every given interval and collects data from
warehouses and dumps into a file
"""

# I (AJ) have tried to avoid as far as possible any reference to
# vaccines in this piece of code ( except nVials; suggested alternative :
# just n , or nItems, or count) We should try to avoid references to
# vaccines specific terms in the general structure of HERMES

_hermes_svn_id_="$Id$"

from SimPy.Simulation import *
from util import openOutputFile

class Reporter(Process):

    def __init__(self, sim, interval, duration, reportFileName,productNameList):
        Process.__init__(self, sim=sim)
        self.reportingInterval= interval

        self.reportingDuration= duration
        
        self.reportFile = openOutputFile(reportFileName, 'w')

        self.productNameList = productNameList

        self.reportFileType = (reportFileName.split('.'))[1]
        

    def run(self):

        stocks = {}
        for pn in self.productNameList: stocks[pn] = 0

        #Write the header
        #================
        
        warehouseList= self.sim.warehouseWeakRefs

        if self.reportFileType == 'csv':

            self.reportFile.write(',')
            
            for refW in warehouseList:
                for pn in self.productNameList:
                    self.reportFile.write(pn + ',')

            self.reportFile.write('\nDay,')        

            for refW in warehouseList:
                for pn in self.productNameList:
                    w=refW()
                    self.reportFile.write( w.name + ',')

            self.reportFile.write('\n')        
                

        else: #if the filename extension is non-csv
            self.reportFile.write("%d #Vaccines\n" % len(self.productNameList))
            for pn in self.productNameList:
                self.reportFile.write(pn + '\n')

            self.reportFile.write("\n%d #Warehouses\n" % len(warehouseList) )
            for refW in warehouseList: #weak references to warehouses
                w= refW()
                if w is None: continue
                self.reportFile.write(w.name + '\n')

            self.reportFile.write("\n%d #Days\n" % (self.reportingDuration+1) )
            

        #Write the stock data

        while True: #Present (in active or passive state) till the end of simulation
            if self.reportFileType == 'csv':
                self.reportFile.write("\n%g,"%now())
            else:
                self.reportFile.write("\nDay %g\n"%now())
            
            for refW in warehouseList: #weak references to warehouses
                w= refW()
                if w is None: continue

                for g in w.theBuffer:
                    # Get item count for each group
                    stocks[g.vaccineType.name] += g.nVials 

                for pn in self.productNameList:
                    #print the stocks to a file
                    if self.reportFileType == 'csv':
                        self.reportFile.write(str(stocks[pn]) + "," )
                    else:
                        self.reportFile.write(str(stocks[pn]) + " " ) 

                    stocks[pn] = 0 #Reset

                if self.reportFileType != 'csv':
                    self.reportFile.write("\n")

            yield hold,self,self.reportingInterval

        self.reportFile.close()
            

#In the future, think about ways for the user to specify what to collect
# More efficient file writes? (buffers, binary files etc)
#Plotter
