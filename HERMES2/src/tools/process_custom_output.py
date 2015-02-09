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


import HermesOutput
import sys
import pickle


import util
import noteholder
import hermes


def main():
    if len(sys.argv) < 3 or sys.argv[1][0] == '-':
        print "%s help:"%sys.argv[0]
        print "process a custom output script against a hermes output file"
        print "usage:"
        print "python %s <outputFile> <customOutputCSV>"%sys.argv[0]
        return

    outputFileName = sys.argv[1]
    outputTemplateFile = sys.argv[2]

    with open(outputFileName, 'r') as f:
        ho = pickle.load(f)

    ho.customOutputs = [outputTemplateFile]
    ho.writeOutputs()




if __name__=="__main__":
    main()
