#! /usr/bin/env python

########################################################################
# Copyright C 2012, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" loadnetwork.py
This is a main routine that can minimally load the simple representation of
the hermes supply chain network from a hermes kvp file.

Currently this is more of a template than anything else.
"""
_hermes_svn_id_="$Id$"

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



############
# Main hook
############

if __name__=="__main__":
    main()

