#! /usr/bin/env python


__doc__=""" 
new graph network

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

import ipath
import input
import globals
import curry
from main import parseCommandLine, loadShadowNetwork
# more delayed imports below, so that values in globals can be changed before import
import csv_tools

import util
import graph_network_utils

class ParserOptionCollector:
    def __init__(self):
        self._optList = []

    def addOpt(self, argName, *posArgs, **kwArgs):
        self._optList.append({'argName':argName, 'posArgs':posArgs, 'kwArgs':kwArgs})

    def optList(self):
        return self._optList

def main():
    unifiedInput = input.UnifiedInput()  # pointers to 'unified' files

    poc = ParserOptionCollector()

    poc.addOpt('outfile', "--outfile", help="filename base for outputs (default is check)", default='check')
    poc.addOpt('layout', "--layout", default='circo',
               help="One of the GraphVis layout engines.  Default is circo; others include dot, neato, and twopi")
    poc.addOpt('type', "--type", default='svg',
               help="Data type for output file.  Default is svg; others include png, jpg, and dot")
    #poc.addOpt("--cluster",action="store_true",
     #          help="Add cluster information to graph.  Only the dot renderer seems to respect this info.")
    poc.addOpt("report", "--report",
               help="A CSV file like report.csv, from which color info can be drawn")
    poc.addOpt('vax', "--vax",
               help="Vaccine for which to calculate the displayed quantity, if applicable")
    poc.addOpt('show', "--show",
               help="One of 'fill','supplyratio'.  Default is 'fill'.",
               default="fill")
    poc.addOpt('label', "--label",
               help="Provide an overall label for the graph")
    poc.addOpt('root', "--root", type="long",
               help="Specify the ID number of the node to place at the center of the graph")
    #poc.addOpt("--legend", action="store_true",
    #           help="Cause a legend to be drawn")
    poc.addOpt('removeOrphans', "--removeOrphans", action="store_true", default=False,
               help="Don't graph stores with no suppliers or clients")


    userInputList,gblInputs= parseCommandLine(poc.optList())
    outFile = gblInputs['outfile']
    outFileType = gblInputs['type']
    useDB = gblInputs['use_dbmodel']
    reportInfo = gblInputs['report']

    net = loadShadowNetwork(userInputList[0], unifiedInput)

    if reportInfo is None:
        resultsId = None
    else:
        if useDB:
            try:
                resultsId = int(reportInfo)
            except:
                raise RuntimeError("With --use_dbmodel, --report should be an integer report id.")
        else:
            from shadow_db_routines import addResultsGroup, commitResultsEntry
            from shadow_network import HermesResults, HermesResultsGroup
            hRG = HermesResultsGroup(net, 'ngn_temp', standAlone=True)
            resultsGroupId = hRG.resultsGroupId
            hR = HermesResults(hRG,0)
            resultsId = hR.resultsId
            (keys, recs) = csv_tools.parseCSV(reportInfo)
            hR.addReportRecs(net,recs)

    #rootStores = net.rootStores()

    #trunkStore = net.trunkStore()

    attrib = {}
    attrib['resultsId'] = resultsId
    attrib['vax'] = gblInputs['vax']
    attrib['show'] = gblInputs['show']
    attrib['layout'] = gblInputs['layout']
    attrib['removeOrphans'] = gblInputs['removeOrphans']
    if gblInputs['label'] is not None:
        attrib['label'] = gblInputs['label']

    if gblInputs['root'] is not None:
        attrib['root'] = gblInputs['root']

    ng = graph_network_utils.HermesNetGraph(net, attrib)

    ng.save_gv_render(gblInputs['type'], gblInputs['outfile'])







############
# Main hook
############

if __name__=="__main__":
    main()

