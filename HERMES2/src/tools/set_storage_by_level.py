import ipath
import shadow_network
from shadow_network_db_api import ShdNetworkDB
import input
from copy import deepcopy
import sys
import optparse
from transformation import setStorageForEntireLevel

def get_comma_sep_args(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))
    
def parseCommandLine():
    parser = optparse.OptionParser(usage="""
    %prog [-v][-i inputfile][-b dbId]
    """)
    parser.add_option("-i", "--inputfile", default=None)
    parser.add_option("-o", "--outputname", default=None)
    parser.add_option("-c","--devicename", default=None)
    parser.add_option("-l","--levels", 
                      type='string',
                      action='callback',
                      callback=get_comma_sep_args)
                      #dest= levels_list)
    # parser.add_option("-d","--use_db",type=int,default=None)
    opts, args = parser.parse_args()
    
    return (opts, args)

def main():
    
    opts, args = parseCommandLine()
        
    userInput = input.UserInput(opts.inputfile, False)
    shdTypes = shadow_network.loadShdTypes(userInput, input.UnifiedInput())
    shdNtwk = shadow_network.loadShdNetwork(userInput, shdTypes, opts.outputname)
    
    stbFridgeRec = {
                    'Name':'stb_Fridge',
                    'DisplayName':'STB Fridge',
                    'Make':'STB',
                    'Model':'STB',
                    'Year':2012,
                    'Energy':'E',
                    'Category':'ElectricFridge',
                    'Technology':'',
                    'BaseCost':980.0,
                    'BaseCostCurCode':'USD',
                    'BaseCostYear':2012,
                    'AmortYears':8.53,
                    'PowerRate':2.02,
                    'PowerRateUnits':'kWh/day',
                    'NoPowerHoldoverDays':0.333,
                    'freezer':0.0,
                    'cooler':6.0,
                    'roomtemperature':0.0,
                    'Notes':'Made By Shawn T. Brown'
                    }
    #print opts.levels
    setStorageForEntireLevel(shdNtwk, shdTypes, opts.levels, opts.devicename, None) #"B_RCW50EK_2001_EK"
                             #storageDeviceRec=stbFridgeRec,
                             #daysPerMonth=20,powerCost=1.0)
    #for n,t in shdNtwk.types.items():
    #    print n
    shdNtwk.writeCSVRepresentation()

if __name__ == '__main__':
    main()
    
