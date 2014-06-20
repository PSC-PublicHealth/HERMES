import os
import sys
import optparse
import pickle

try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    updir = os.path.join(cwd, '..')
    if updir not in sys.path:
        sys.path.append(updir)
except:
    pass

import hermes
import HermesOutput
import util




def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [options] <custom_out_def> <hermes_output> [<hermes_output> [...]]""" )
    parser.add_option("--use_zip", help="Look for the hermes_outputs in the referenced zip file.")
    
    (opts,args) = parser.parse_args()
    cod = args[0] # Custom Output Definition file
    outputs = args[1:]
    
    return (opts,cod, outputs)

def main():
    (opts, cod, outputFileNames) = parseCommandLine()
    
    # we have to be a bit cagey since we want to honor HERMES_DATA_PATH for 
    # the output definition but we want to replace it with our zipfile
    # (if applicable) for the hermes definitions.

    for ofn in outputFileNames:
        oldInput = util.redirectInput(zipfileName = opts.use_zip)
        with util.openDataFullPath(ofn) as of:
            ho = pickle.load(of)
        util.redirectInput(path = oldInput)
        ho.writeCustomCSV(cod, str(ho.runNumber))  # I need to find a decent way of attaching an appropriate suffix here



if __name__ == '__main__':
    main()
