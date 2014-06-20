#! /usr/bin/env python

_hermes_svn_id_="$Id$"

import pickle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np
import os,sys,optparse
import shutil

class Store_Data:
    def __init__(self,rec,rec_tup):
        self.id = rec_tup[0]
        self.name = rec[0].replace('/','').replace('*','')
        self.category = rec[1]
        self.function = rec[2]
        self.vaccine = rec_tup[1]
        self.tseries = np.array(rec[3])
        self.yseries = np.array(rec[4])
        for i in range(0,len(self.yseries)):
            if self.yseries[i] is None:
                self.yseries[i] = 0
        self.header = self.name + "_" + str(self.id) + "_" + self.vaccine

def create_store_curve_plot(storedata):
    ## First define the file name that will will calling this
    filename = storedata.header + "_storage_curve.png"
    fig = Figure(figsize=(10,4))
    subpt = fig.add_subplot(111)
    subpt.set_title("Vaccine Storage Level per day for %s at %s"%(storedata.vaccine,storedata.name))
    subpt.set_xlabel('Days')
    subpt.set_ylabel('Vials in Storage')
    subpt.plot(storedata.tseries,storedata.yseries)

    canvas = FigureCanvasAgg(fig)
    print "Filename = " + filename
    sys.stdout.flush()
    
    canvas.print_figure(filename, dpi=80)
    ## try:
    ##     plt.savefig(filename)
    ## except IOError:
    ##     print "Cannot create store curve %s"%filename
    ## plt.clf()
    

def find_maximum_storage(storeDict):
    max = 0.0
    for sdk in storeDict.keys():
        sd = storeDict[sdk]
        max_here = np.max(sd.yseries)
        if(max_here > max): max = max_here
    return max

def find_maximum_days(storeDict):
    max = 0.0
    for sdk in storeDict.keys():
        sd = storeDict[sdk]
        max_here = np.max(sd.tseries)
        if(max_here > max): max = max_here
    return max

def main():
    ## Parse command line options
    parser = optparse.OptionParser(usage="""
    %prog [--help][--pklfile fname][--outdir dirname][--vax vaccine name]
    """)
    parser.add_option("-d","--debug",action="store_true",help="Turn debugging on")
    parser.add_option("--pklfile",type="string",
                      help="Input file from a completed HERMES run")
    parser.add_option("--outdir",type="string",
                      help="Output directory for graphs (warning, this will be overwritten",
                      default="hermes.out")
    parser.add_option("--vax",type="string",
                      help="Name of vaccine if you only that vaccine's plots (all for the total plots)")

    opts,args=parser.parse_args()
    debug = False
    if opts.debug:
        debug = True

    infile=opts.pklfile
    if infile is None :
        print "Need to specify an input file with --pklfile"
        sys.exit("No Input File")

    outdir=opts.outdir

    vax=opts.vax
    
    if debug: print "Input file is: %s \nOutput directory is: %s"%(infile,outdir)

## Read in the data file from disk
    try:
        pkl_file = open(infile,'rb')
    except IOError:
        print "Input file %s specified by --pklfile will not open"%infile

    mydict2 = dict()

    try:
        mydict2 = pickle.load(pkl_file)
    except IOError:
        print "Trouble loading %s file"%infile

    pkl_file.close()

    storeDict = {}
    for ds in mydict2.keys():
        if vax == None or vax == ds[1]:
            storeDict[ds] = Store_Data(mydict2[ds],ds)
    
    if len(storeDict) == 0:
        raise RuntimeError("There are no plots for vacceine %s, Please check your command line option vax"%vax)

## Create a directory to hold the plots
    try:
        os.mkdir(outdir)
    except:
        shutil.rmtree(outdir)
        os.mkdir(outdir)
    os.chdir(outdir)
## create Storage Curves for all records
    for sdk in storeDict.keys():
            create_store_curve_plot(storeDict[sdk])

###########
# Main Hook
###########

if __name__=="__main__":
    main()
        
