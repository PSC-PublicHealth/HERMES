_hermes_svn_id_="$Id$"

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################

import ipath
from full_import_paths import HermesBaseDir
from util import listify, openDataFullPath
import util
import zipfile
import pickle
from contextlib import closing
import string
from main import parseCommandLine
import os.path

def RevisionInfo():
    return "$Id$"


"""
zipSubFileKeys gives the list of keys specified in a HERMES input .kvp file
which specify auxiliary files if present.  These auxiliary files must thus
be included in any zip file representing the inputs.
"""
zipSubFileKeys = ['calendarfile', 'storesfile', 'factoryfile',
                  'routesfile', 'demandfile', 'initialovw',
                  'customoutput', 'storesoverlayfiles',
                  'vaccinefile', 'truckfile', 'peoplefile',
                  'fridgefile', 'icefile', 'packagefile', 'stafffile',
                  'perdiemfile', 'gapstorefile', 'factorywastagefile',
                  'currencyconversionfile', 'pricetable',
                  'shippingdemandfile', 'consumptiondemandfile',
                  'shippingcalendarfile', 'consumptioncalendarfile']

class GatherInputs:
    def _addfiles(self,fileNames):
        fileNames = listify(fileNames)
        for name in fileNames:
            if name in self.files: return
            #fqName = getDataFullPath(name)
            #with open(fqName, 'rb') as f:
            with openDataFullPath(name) as f:
                self.files[name] = f.read()
            
    def gatherInputs(self, zipfileName, userInputList, gblInputs, unifiedInput, argv):
        self.files = {}
        
        # add argv and the input files
        self.files['argv.pkl'] = pickle.dumps(argv)

        # stats is a very simple structure that can be unpickled without needing to load
        # hermes libraries.  This is to be used by job submission queues and the like.
        stats = {}
        stats['inputCount'] = len(userInputList)
        stats['version'] = getHermesVersion()

        # I'm sure I'll want more stats for job submission stuff later but for now
        # this is sufficient to get something up and running.
        self.files['input_stats'] = pickle.dumps(stats)

        for input in gblInputs['input_files']:
            if input.find(":") != -1:
                inputStrings = string.split(input,":")
                self._addfiles(inputStrings[0])
            else:
                self._addfiles(input)

        # the rest is required to be able to run hermes:
        self.files['userInputList.pkl'] = pickle.dumps(userInputList)
        self.files['gblInputs.pkl'] = pickle.dumps(gblInputs)

        self._addfiles(unifiedInput.vaccineFile)
        self._addfiles(unifiedInput.truckFile)
        self._addfiles(unifiedInput.peopleFile)
        self._addfiles(unifiedInput.fridgeFile)
        self._addfiles(unifiedInput.iceFile)
        self._addfiles(unifiedInput.packageFile)
        self._addfiles(unifiedInput.staffFile)
        self._addfiles(unifiedInput.perDiemFile)

        for uInput in userInputList:
            for field in zipSubFileKeys:
                self._addfiles(uInput[field])

        with closing(zipfile.ZipFile(zipfileName, 'a',zipfile.ZIP_DEFLATED)) as z:
            for name,data in self.files.items():
                z.writestr(name, data)


def gatherInputs(zipfileName, userInputList, gblInputs, unifiedInput, argv):
    """
    gather all of the inputs for this hermes run and save them in <zipfileName>

    this is called after command line and main input file is parsed.  argv
    is saved strictly for documentation/debugging purposes.
    """
    gi = GatherInputs()
    gi.gatherInputs(zipfileName, userInputList, gblInputs, unifiedInput, argv)

def extractInputs(zipfileName):
    util.redirectInput(zipfileName=zipfileName)

#     try:
#         with openDataFullPath('input_stats') as f:
#             stats = pickle.loads(f.read())
#             if stats['version'] != getHermesVersion():
#                 raise RuntimeError("version mismatch between hermes program and zip file")
#     except:
#         raise RuntimeError("version mismatch between hermes program and zip file")

    with openDataFullPath('argv.pkl') as f:
        myArgv = pickle.loads(f.read())
    userInputList,gblInputs = parseCommandLine(cmdLineArgs=myArgv[1:])

    gblInputs['zip_inputs'] = None

    return (userInputList,gblInputs)

#BUG: There is nothing in merge outputs to deal with or discard excessively large output files
# this currently just reads the data into ram and spools it back to another zip file.
def mergeOutputs(finalOutput, ziplist, hdata_name):
    """
    merge a list of outputs in ziplist to one single output file zipfile
    return a list of HermesOutput()s
    """
    ret = []
    if finalOutput is None:
        raise RuntimeError("Can't merge outputs without zip_outputs set")
    if hdata_name is None:
        raise RuntimeError("Can't merge outputs if hdata name is not set")
    hdata_name += '_'
    nameSet = set() # skip any file that's already been saved
    with closing(zipfile.ZipFile(finalOutput,"w", zipfile.ZIP_DEFLATED)) as zo:
        for zip in ziplist:
            with closing(zipfile.ZipFile(zip)) as zi:
                for fileName in zi.namelist():
                    if fileName == 'stderr.main' or fileName == 'stdout.main':
                        continue
                    if fileName in nameSet:
                        continue
                    nameSet.add(fileName)
                    data = zi.read(fileName)
                    zo.writestr(fileName, data)
                    if fileName.startswith(hdata_name):
                        (trash,slot) = fileName.split(hdata_name,1)
                        (slot,trash) = slot.split('.pkl',1)
                        slot = int(slot)
                        if slot >= len(ret):
                            ret.extend([None]*(slot-len(ret) + 1))
                        ret[slot] = pickle.loads(data)

    return ret

           
                        
def smallerOutput(oldOutput, newOutput, hdataPrefix):
    """
    Create an output zipfile from another zipfile without the hdata files
    """
    with closing(zipfile.ZipFile(newOutput, "w", zipfile.ZIP_DEFLATED)) as zo:
        with closing(zipfile.ZipFile(oldOutput)) as zi:
            for fileName in zi.namelist():
                if fileName.startswith(hdataPrefix):
                    continue
                data = zi.read(fileName)
                zo.writestr(fileName, data)


HermesVersionFile = os.path.join("src", "version.txt")
HermesVersionFileFullPath = os.path.join(HermesBaseDir, HermesVersionFile)

def getHermesVersion():
    "get the hermes version out of HermesBaseDir/src/version.txt"
    try:
        with open(HermesVersionFileFullPath) as f:
            while f.readline().strip() != "HERMES":
                continue
            return f.readline().strip()
    except:
        raise RuntimeError("unable to get HERMES version from src/version.txt")

