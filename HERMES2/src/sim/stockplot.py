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

__doc__=""" stockplot.py
Makes stock vs time plots
"""

_hermes_svn_id_="$Id$"

import sys, getopt
from numpy import *
from matplotlib import pyplot,axis
from os.path import isfile

def main():
    try:
        (opts,pargs) = getopt.getopt(sys.argv[1:],"",["outfile=","wh=","prod="])
    except:
        sys.exit("%s: Invalid command line parameter" % sys.argv[0])

    wh2plot=[]
    prod2plot=[]

    for a,b in opts:
        if a=="--reportfile": stockReportFile=b
        if a=="--wh": wh2plot.append(b)
        if a=="--prod": prod2plot.append(b)
    nPlots=len(wh2plot)*len(prod2plot)
    if nPlots == 0: raise RuntimeError("Nothing to plot")

    #############################################################################

    srfBin=stockReportFile + '.npz'
    if isfile(srfBin):
        data=load(srfBin)
        nWH=data['nWH'][()]
        wHDict=data['wHDict'][()]
        nProd=data['nProd'][()]
        prodDict=data['prodDict'][()]
        nt=data['nt'][()]
        t=data['t']
        stock=data['stock']
        del data
    else:
        srf=open(stockReportFile, 'rU');

        # Read in the # products
        buf=(srf.readline()).split()
        if  buf[0]=='':
            raise RuntimeError("#products=0 in file")
        else:
            nProd=int(buf[0])

        #Read in the product names
        prodDict = {}
        for pid in xrange(nProd):
            buf=(srf.readline()).strip()
            if  buf=='':
                raise RuntimeError("Missing product name in file")
            else:
                prodDict[buf] = pid

        #Read in the # warehouses
        srf.readline() #Skip a line
        buf=(srf.readline()).split()
        if buf[0] == '':
            raise RuntimeError("#warehouses=0 in file")
        else:
            nWH=int(buf[0])

        #Read in the warehouse names
        wHDict = {}
        for wid in xrange(nWH):
            buf=(srf.readline()).strip()
            if buf=='':
                raise RuntimeError("Missing warehouse in file")
            else:
                wHDict[buf] = wid

        #Read in the number of timesteps
        srf.readline() #Skip a line
        buf=(srf.readline()).split()
        if buf[0] == '':
            raise RuntimeError("#timesteps=0 in file")
        else:
            nt=int(buf[0])            

        stock=zeros(( nt, nWH, nProd ), dtype=int)
        itStep=0
        t=[]
        srf.readline() #Skip a line
        buf=(srf.readline()).split()
        print buf
        while (len(buf)>0):
            t.append(int(buf[1]))

            for wid in xrange(nWH):
                buf=(srf.readline()).split()
                for pid in xrange(nProd):
                    stock[itStep, wid, pid] = int(buf[pid])

            itStep += 1
            srf.readline() #Skip a line
            buf=(srf.readline()).split()
            print buf
        t=array(t)

        srf.close()

        savez(srfBin,nProd=nProd,prodDict=prodDict,nWH=nWH,wHDict=wHDict,nt=nt,t=t,stock=stock)

    ##########################################################################

    print '#Products = ' + str(nProd)
    print '#Warehouses = ' + str(nWH)
    print '#Timesteps = ' + str(nt)

    iPlot=0
    for kwh2plot in wh2plot:
        for kprod2plot in prod2plot:
            iPlot +=1
            pyplot.subplot(nPlots,1,iPlot);
            pyplot.plot(t,stock[:, wHDict[kwh2plot], prodDict[kprod2plot] ])
            if iPlot < nPlots: pyplot.setp(pyplot.gca(),'xticks',[])
            pyplot.ylabel('Stock')
            pyplot.title( kprod2plot + " : " + kwh2plot)

    pyplot.xlabel('Days')        

    pyplot.show()






############
# Main hook
############

if __name__=="__main__":
    main()
