#!/usr/bin/env python

########################################################################
# Copyright C 2009-2011, Pittsburgh Supercomputing Center (PSC).       #
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

__doc__=""" recorders.py
The classes provided by this module are functionally like Monitors and
Tallies, but with a little more control.
"""

_hermes_svn_id_="$Id$"

import weakref,types
from SimPy.Simulation import *
import pickle
from binary_packing import *
from util import isiterable, openOutputFile
import math
import time

import globals as G
import vaccinetypes

# Color table for curves
_ctbl= ['black','blue','green','red','yellow','cyan','magenta']

class RMonitor(Monitor):
    pass

class RTally(Tally):
    pass

class RecorderGroup:
    """
    Instances of this class represent groups of recorders.
    """
    
    # If graphics are requested, this will become a plot instance
    plt= None

    def __init__(self,sim):
        self.allRecorderWeakRefs= []
        self.sim= sim

    def resetAll(self):
        for rRef in self.allRecorderWeakRefs:
            r= rRef()
            if r is not None:
                r.reset()

    def getFromRecorderType(self,typeName,monitorName,maxCount=100):
        if typeName is None: 
            return None
        elif typeName=="monitor":
            m= RMonitor(monitorName,"vials",sim=self.sim)
            self.allRecorderWeakRefs.append(weakref.ref(m))
            return m
        elif typeName=="tally":
            t= RTally(monitorName,"vials",sim=self.sim)
            t.setHistogram(low=0.0, high=maxCount, nbins= 50)
            self.allRecorderWeakRefs.append(weakref.ref(t))
            return t
        else:
            raise RuntimeError("Unknown recorder type name '%s'"%typeName)

    def buildRecorderObject(self, recorderType, baseName, estUsageVC,
                            recordTheseVaccineNames):
        if recordTheseVaccineNames[0] == 'everyvaccine':
            recordTheseVaccineNames = self.sim.vaccines.getActiveTypeNames()
            recordTheseVaccineNames.append('all')
        if recorderType is None:
            return None
        else:
            if recordTheseVaccineNames is None \
                   or len(recordTheseVaccineNames)==0:
                recorderName= "%s stock of all types"%baseName
                recorder= self.getFromRecorderType(recorderType,
                                                   recorderName,
                                                   maxCount=estUsageVC.totalCount())
                recorder.loc= baseName
                recorder.vax= 'all'
            elif len(recordTheseVaccineNames)==1:
                if recordTheseVaccineNames[0]=='all':
                    recorderName= "%s stock of all types"%baseName
                    recorder= self.getFromRecorderType(recorderType,
                                                       recorderName,
                                                       maxCount=estUsageVC.totalCount())
                    recorder.loc= baseName
                    recorder.vax= 'all'
                else:
                    recorderName= "%s stock of %s"%\
                                  (baseName,recordTheseVaccineNames[0])
                    v= self.sim.vaccines.getTypeByName(recordTheseVaccineNames[0])
                    estMax= estUsageVC[v]
                    recorder= (v,self.getFromRecorderType(recorderType,
                                                          recorderName,
                                                          maxCount=estMax))
                    recorder[1].loc= baseName
                    recorder[1].vax= recordTheseVaccineNames[0]
            else:
                recorder= {}
                for vaxName in recordTheseVaccineNames:
                    if vaxName=="all":
                        key= vaxName
                        recorder[key]= self.buildRecorderObject(recorderType,
                                                                baseName, estUsageVC,
                                                                [vaxName])
                    else:
                        key= self.sim.vaccines.getTypeByName(vaxName)
                        recorder[key]= self.buildRecorderObject(recorderType,
                                                                baseName, estUsageVC,
                                                                [vaxName])[1]
                    recorderName= "(dictionary)" # for debug output below
            if self.sim.debug:
                print "Recorder %s is a %s\n"%(recorderName,recorderType)
            
            return recorder

    def sortByType(self):
        monitorList= []
        tallyList= []
        for rRef in self.allRecorderWeakRefs:
            r= rRef()
            if r is None: continue
            if isinstance(r,types.DictType):
                print "%s is a dict"%r.name
            elif isinstance(r,Monitor):
                monitorList.append(r)
            elif isinstance(r,Tally):
                tallyList.append(r)
            else:
                raise RuntimeError("recorder %s of type %s cannot be handled"%(r.name,type(r)))
        return monitorList,tallyList

    def printHistograms(self,ofile=sys.stdout):
        monitorList,tallyList= self.sortByType()
        if len(tallyList+monitorList)>0:
            for r in tallyList:
                if r.count()>0:
                    ofile.write(r.printHistogram(fmt="%6.4f")+'\n')
                else:
                    ofile.write("Histogram for %s: no counts\n"%r.name)
            for r in monitorList:
                if r.count()>0:
                    high= max(r.yseries())
                    r.setHistogram(low=0.0, high=max(high,1.0), nbins=50)
                    if high>0:
                        ofile.write(r.printHistogram(fmt="%6.4f")+'\n')
                    else:
                        ofile.write("Histogram for %s: %d counts, all zero."%\
                                    (r.name,r.count()))
                else:
                    ofile.write("Histogram for %s: no counts\n"%r.name)
        else:
            ofile.write("No histograms to print\n")

    def plotHistograms(self):
#        import SimPy.SimPlot as sp
#        monitorList,tallyList= self.sortByType()
#        if len(tallyList+monitorList)>0:
#            if RecorderGroup.plt is None:
#                RecorderGroup.plt= sp.SimPlot()
#                f= sp.Frame(RecorderGroup.plt.root)
#                RecorderGroup.plt.root.title("Histogram of vial counts for warehouses, run #%d"%self.sim.runNumber)
#            else:
#                t= sp.Toplevel(RecorderGroup.plt.root)
#                t.title("Histogram of vial counts for warehouses, run #%d"%self.sim.runNumber)
#                f= sp.Frame(t)
#            for r in tallyList:
#                gb= RecorderGroup.plt.makeGraphBase(f,500,100,title=r.name)
#                gb.pack(side=sp.TOP,fill=sp.BOTH,expand=sp.YES)
#                line= RecorderGroup.plt.makeBars(r.getHistogram(),ylab='vials')
#                go= RecorderGroup.plt.makeGraphObjects([line])
#                gb.draw(go)        
#            for r in monitorList:
#                if r.count()>0:
#                    high= max(r.yseries())
#                    r.setHistogram(low=0.0, high=max(high,1.0), nbins=50)
#                    gb= RecorderGroup.plt.makeGraphBase(f,500,100,title=r.name)
#                    gb.pack(side=sp.TOP,fill=sp.BOTH,expand=sp.YES)
#                    line= RecorderGroup.plt.makeBars(r.getHistogram(),ylab='vials')
#                    go= RecorderGroup.plt.makeGraphObjects([line])
#                    gb.draw(go)        
#                else:
#                    print "Histogram of %s: no counts"%r.name
#            f.pack()
#        else:
        print "No histograms to plot"

    def plotCurves(self):
        monitorList,tallyList= self.sortByType()
        if len(monitorList)>0:
            import SimPy.SimPlot as sp
            if RecorderGroup.plt is None:
                RecorderGroup.plt= sp.SimPlot()
                f= sp.Frame(RecorderGroup.plt.root)
                RecorderGroup.plt.root.title("Vial counts vs. time for warehouses, run #%d"%self.sim.runNumber)
            else:
                t= sp.Toplevel(RecorderGroup.plt.root)
                t.title("Vial counts vs. time for warehouses, run #%d"%self.sim.runNumber)
                f= sp.Frame(t)
            groupDict= {}
            keyList= [] # to keep them in order
            for r in monitorList:
                if not groupDict.has_key(r.loc):
                    groupDict[r.loc]= []
                    keyList.append(r.loc)
                groupDict[r.loc].append(r)
            for k in keyList:
                l= groupDict[k]
                gb= RecorderGroup.plt.makeGraphBase(f,500,125,title=k)
                gb.pack(side=sp.TOP,fill=sp.BOTH,expand=sp.YES)
                ymax= -1.0
                for r in l:
                    ymaxNew= max( [y for x,y in r]+[0.0] )
                    if ymaxNew>ymax: ymax= ymaxNew
                if ymax>0.0:
                    goList= []
                    for ind in xrange(len(l)):
                        r= l[ind]
                        clr= _ctbl[ind%len(_ctbl)]
                        if len(r)>0:
                            line= RecorderGroup.plt.makeLine(r,ylab='%s vials'%r.vax,
                                                color=clr)
                        else:
                            line= RecorderGroup.plt.makeLine([(0.0,0.0),(self.sim.now(),0.0)],
                                                ylab='%s vials'%r.vax,
                                                color=clr)
                        goList.append(line)
                    go= RecorderGroup.plt.makeGraphObjects(goList)
                    yrangemax= math.ceil( 1.1*ymax )
                    gb.draw(go, yaxis= (0.0,yrangemax), xaxis = (self.sim.model.burninDays,self.sim.model.burninDays+self.sim.model.runDays) )  
                    #gb.draw(go, yaxis=None)  # this version makes it easier to match times
                else:
                    goList= []
                    for ind in xrange(len(l)):
                        r= l[ind]
                        clr= _ctbl[ind%len(_ctbl)]
                        if len(r)>0:
                            line= RecorderGroup.plt.makeLine(r,ylab='%s vials'%r.vax,
                                                color=clr)
                        else:
                            line= RecorderGroup.plt.makeLine([(0.0,0.0),(self.sim.now(),0.0)],
                                                ylab='%s vials'%r.vax,
                                                color=clr)
                        goList.append(line)
                    go= RecorderGroup.plt.makeGraphObjects(goList)
                    ymax= 1.0
                    yrangemax= 1.1
                    gb.draw(go, yaxis= (0.0,yrangemax))        
            f.pack()
        else:
	    print "No curves to plot"
        
    def showPlots(self):
        if RecorderGroup.plt is None:
            print "No plots to show"
        else:
            RecorderGroup.plt.mainloop()
                   
    def saveMonitors(self,saveAllFile,storeDict):
        """
        saveMonitors() stores both the store curves and the
                       histograms from the monitors.
        """
        monitorList,tallyList= self.sortByType()
        saveAllPKL = saveAllFile + '.pkl'
        saveDict = {}
    
        if len(monitorList)>0:
            for whkey in storeDict:
                wh = storeDict[whkey]
                ### STB - There are some clinics in Niger that don't have demand.
                ### This makes sure they are not accessed here
                if wh is not None:
                    if type(wh.recorder)==types.DictType:
                        recorderIter= iter(wh.recorder.values())
                    else:
                        try:
                            recorderIter= iter(wh.recorder)
                        except TypeError:
                            recorderIter= iter([wh.recorder])
                    for r in recorderIter:
                        if r.count()==0:
                            tseries = [0,0]
                            yseries = [0,0]
                        else:
                            tseries = r.tseries()
                            yseries = r.yseries()
                        saveDict[(wh.idcode,r.vax)] = (wh.name,wh.category,wh.function,tseries,yseries)
        else:
            print "No data to save from Monitors"
    
        print "saving %s Stores data to file %s"%(len(monitorList),saveAllPKL)
        with openOutputFile(saveAllPKL,'wb') as output:
            pickle.dump(saveDict,output)
            
        monitorList,tallyList
        
    def createMatPlotLibStockPlots(self,storeDict,directoryName="stockPlots"):
        """
        createMatPlotLibStockPlots() creates an image with matplotlib
        of all of the stock plots throughout the network
        """
        import os,sys
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        import numpy as np
        import shutil
        
        print "Writing Stockplots to %s"%directoryName
        monitorList,tallyList = self.sortByType()
        
        try:
            os.mkdir(directoryName)
        except:
            shutil.rmtree(directoryName)
            os.mkdir(directoryName)
        os.chdir(directoryName)

        ## ### find max rundays
        ## maxRunDays = -99999
        ## for whkey in storeDict:
        ##     wh=storeDict[whkey]
        ##     if wh is not None:
        ##         if type(wh.recorder)==types.DictType:
        ##             recorderIter= iter(wh.recorder.values())
        ##         else:
        ##             try:
        ##                 recorderIter= iter(wh.recorder)
        ##             except TypeError:
        ##                 recorderIter= iter([wh.recorder])
        ##     for r in recorderIter:
        ##             time1 = time.time()
        ##             vaccine = r.vax
        ##             if vaccine != "all":
        ##                 continue
        ##             fileName = str(idcode) + "_" + vaccine + "_storage_curve.jpg"
                    
        ##             if r.count() == 0:
        ##                 continue
        ##                 #tseries = np.array([0,0])
        ##                 #yseries = np.array([0,0])
        ##             else:
        ##                 tseries = np.array(r.tseries())
        ##                 yseries = np.array(r.yseries())
        ##     if max(yseries) > maxRunDays
            
        timeAll = 0.0
        canvasList = []
        plt.ioff()
        timeA = 0.0
        timeAA = 0.0
        timeB = 0.0
        timeC = 0.0
        timeD = 0.0
        timeE = 0.0
        timeF = 0.0
        timeG = 0.0

        time5 = time.time()
        time1 = time.time()
        fig = Figure(figsize=(10,4))
        subpt = fig.add_subplot(111)
        #subpt.set_title("Number of Vaccine Vials per day for\
        #                %(vaccine,name))
        subpt.set_xlabel('Days')
        subpt.set_ylabel('Vials in Storage')
        subpt.set_autoscale_on(True)
        subpt.autoscale_view(True,True,True)
        l1, = subpt.plot(0,20)
        canvas = FigureCanvasAgg(fig)
        background = canvas.copy_from_bbox(fig.bbox)
        canvas.draw()
        time2 = time.time()

        for whkey in storeDict:
            wh=storeDict[whkey]
            name = wh.name.replace('/','').replace('*','')
            idcode = wh.idcode
            category = wh.category
            function = wh.function
            
            if wh is not None:
                if type(wh.recorder)==types.DictType:
                    recorderIter= iter(wh.recorder.values())
                else:
                    try:
                        recorderIter= iter(wh.recorder)
                    except TypeError:
                        recorderIter= iter([wh.recorder])
 
                timeAA += time2-time1
                for r in recorderIter:
                    time1 = time.time()
                    vaccine = r.vax
                    if vaccine != "all":
                        continue
                    fileName = str(idcode) + "_" + vaccine + "_storage_curve.png"
                    
                    if r.count() == 0:
                        continue
                        #tseries = np.array([0,0])
                        #yseries = np.array([0,0])
                    else:
                        tseries = np.array(r.tseries()) - self.sim.model.burninDays
                        yseries = np.array(r.yseries())

                    ymax = yseries.max()
                    xmax = tseries.max()
                    time2 = time.time()
                    timeA += time2-time1
                    #fig = Figure(figsize=(10,4))
                    #subpt = fig.add_subplot(111)
                    #subpt.set_title("Number of Vaccine Vials per day for %s at %s"\
                    #                %(vaccine,name))
                    #subpt.set_xlabel('Days')
                    #subpt.set_ylabel('Vials in Storage')
                    time1 = time.time()
                    canvas.restore_region(background)
                    time2 = time.time()
                    timeB += time2-time1

                    time1 = time.time()
                    l1.set_data(tseries,yseries)
                    time2 = time.time()
                    timeC += time2-time1
                    
                    #subpt.plot(tseries,yseries)
                    time1 = time.time()
                    subpt.relim()
                    time2 = time.time()
                    timeD += time2-time1

                    time1 = time.time()
                    subpt.set_ybound(0,ymax*1.1)
                    subpt.set_xbound(0,xmax)
                    time2 = time.time()
                    timeE += time2-time1
                    
                    #subpt.autoscale_view(True,True,True)
                    time1 = time.time()
                    #canvas.blit()
                    #subpt.plot(tseries,yseries)
                    time2 = time.time()
                    timeF += time2-time1
                    
                    #subpt.set_xdata(tseries)
                    #subpt.set_ydata(yseries)
                    #canvas = FigureCanvasAgg(fig)
                    time1 =time.time()
                    canvas.draw()
                    canvas.print_figure(fileName,format="png",dpi=40)
                    time2 = time.time()
                    timeG += time2-time1
                    
        time6 = time.time()
        print "Total Time = %g"%(time6-time5)
        print "Times: %g %g %g %g %g %g %g %g"%(timeAA, timeA,timeB,timeC,timeD,timeE,timeF,timeG)
                
        os.chdir('../')
                    
                    
                        
    def serializeMonitorsCompressed(self, storesDict):
        """
        save a compressed version of the monitors with the hope of 
        having something of a sane size to upload to the webserver.
        """
        monitorList,tallyList= self.sortByType()
        saveDict = {}
    
        out = bytearray()
        vaxOut = {}
        nextVaxVal = 1

        if len(monitorList) < 1:
            print "No data to save from Monitors"
            return encodeString("")
        
        for whkey in storesDict:
            wh = storesDict[whkey]
            if type(wh.recorder)==types.DictType:
                recorders= wh.recorder.values()
            else:
                if isiterable(wh.recorder):
                    recorders = wh.recorder
                else:
                    recorders = [wh.recorder]

            # don't bother with a warehouse with no recorders
            if 0 == len(recorders):
                continue

            # get all the time/vial data for a warehouse
            vialCounts = {}
            tseriesBase = None
            for r in recorders:
                if r.count()==0:
                    tseries = [0,0]
                    yseries = [0,0]
                else:
                    tseries = r.tseries()
                    yseries = r.yseries()
                
                print "%s:%s: len t,y: %d, %d"%(wh.idcode, r.vax, len(tseries), len(yseries))
                if tseriesBase is None:
                    tseriesBase = tseries
                else:
                    if tseries != tseriesBase:
                        raise RuntimeError('Time series are inconsistent within a warehouse')
                vialCounts[r.vax] = diffPack(yseries)

            # now see what we can do to shrink it down a bit
            # get rid of any time entries where all of the diffs are equal
            for i in xrange(len(tseriesBase) - 1, -1, -1):
                kill = True
                for vcount in vialCounts.values():
                    if 0 == vcount[i]:
                        kill = False
                        break
                if not kill:
                    continue
                for vcount in vialCounts.values():
                    del vcount[i]
                del tseriesBase[i]
            
            #convert the time series
            ts = map((lambda t: int(t*256)), tseriesBase)
            ts = diffPack(diffPack(ts))
            

            # serialize the data
            # first the warehouse id
            out.extend(encodeString(str(wh.idcode)))
            # next the time series
            out.extend(encodeIntList(ts))
            # now loop through the vial counts
            for vax, vc in vialCounts.items():
                # if this specific vax hasn't been seen before
                # we need to give it a new encoding and define 
                # the encoding in the output stream
                if vax not in vaxOut:
                    vaxOut[vax] = nextVaxVal
                    nextVaxVal += 1
                    out.extend(signedBerEncode(vaxOut[vax]))
                    out.extend(encodeString(vax))
                else:
                    # otherwise just send the encoded value of the vax
                    out.extend(signedBerEncode(vaxOut[vax]))
                # and send the vial counts
                out.extend(encodeIntList(vc))
            # when we're done sending vial counts, send a 0 to say we're done
            out.extend(signedBerEncode(0))


        # now that we've sent all of our warehouses, send a null warehouse id
        out.extend(encodeString(''))
        return out

                    
    def saveMonitorsCompressed(self, saveFile, storesDict):
        saveFile = saveFile + '.vdt'
        with openOutputFile(saveFile, "wb") as out:
            out.write(self.serializeMonitorsCompressed(storesDict))
            
