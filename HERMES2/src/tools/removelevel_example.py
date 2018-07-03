#! /usr/bin/env python


__doc__=""" removelevel_example.py
This is a main routine that can minimally load the simple representation of
the hermes supply chain network from a hermes kvp file and then remove the 
'Region' level 

Currently this is more of a template than anything else.
"""
_hermes_svn_id_="$Id$"

import os.path
import sys

try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    # also need the directory above
    updir = os.path.join(cwd, '..')
    if updir not in sys.path:
        sys.path.append(updir)
except:
    pass


import input
import globals
import curry
from main import parseCommandLine
# more delayed imports below, so that values in globals can be changed before import

class FakeSim():
    """
    To use the typemanager you need a sim.  it needs to be a class.  But it doesn't
    need much of anything.  But the different types expect to be able to read
    directly off of the sim.
    """
    def __init__(self, userInput, perfect=False):
        self.userInput = userInput
        self.perfect = perfect


import util
def calcTransitHours(supplier, client, order, template):
    if supplier.Latitude is None:
        return 5
    if client.Latitude is None:
        return 5
    if supplier.Longitude is None:
        return 5
    if client.Longitude is None:
        return 5

    dist = util.longitudeLatitudeSep(supplier.Longitude,supplier.Latitude,
                                     client.Longitude, client.Latitude)
    time = dist / 40.0 + 1.0
    return time

def main():
    unifiedInput = input.UnifiedInput()  # pointers to 'unified' files
    userInputList,gblInputs= parseCommandLine()

    globals.deterministic= gblInputs['deterministic']

    # Delayed inputs- we wanted to modify globals before causing these modules to load
    # we don't need hermes or util yet but this is a reminder that when we do need them
    # that we shouldn't load them at the top.
    #import hermes
    #import util
    import network
    import load_typemanagers

    userInput = userInputList[0]
    sim = FakeSim(userInput)

    (sim.typeManager, sim.typeManagers) = \
        load_typemanagers.loadTypeManagers(userInput, unifiedInput, sim, False, False)

    # unpack type managers
    for (attr,tm) in sim.typeManagers.items():
        setattr(sim, attr, tm)

    net = network.loadNetwork(userInput, sim.typeManager, sim.typeManagers)

    



    stKeys, stRecs = net.createStoreRecs()
    rtKeys, rtRecs = net.createRouteRecs()

    import removelevel
    template = {'Type': 'pull',
                'TruckType': 'N_cold_truck',
                'ShipIntervalDays': 14,
                'ShipLatencyDays': 3,
                'TransitHours':calcTransitHours,
                'PullOrderAmountDays':28}

    removelevel.removeLevelWithDefaults(net, 'Region', template)
    stKeys, stRecs = net.createStoreRecs()
    rtKeys, rtRecs = net.createRouteRecs()
 
    import csv_tools
    with open("new_stores.csv", "w") as f:
        csv_tools.writeCSV(f, stKeys, stRecs)
    with open("new_routes.csv", "w") as f:
        csv_tools.writeCSV(f, rtKeys, rtRecs)





############
# Main hook
############

if __name__=="__main__":
    main()

