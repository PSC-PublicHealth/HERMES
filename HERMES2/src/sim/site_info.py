#! /usr/bin/env python

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

_hermes_svn_id_="$Id$"

import os, os.path, platform
import ipath
from full_import_paths import HermesBaseDir
import kvp_tools


class SiteInfo:
    def __init__(self):
        s = platform.system()
        if s == 'Linux' or s=='Darwin':
            homeDir = os.environ['HOME']
            defaultScratchDir = '/tmp'
            defaultOutTmpDir = '/tmp'
            defaultDbLoc = os.path.join(HermesBaseDir, 'hermes.db')
            
        elif s == 'Windows':
            homeDir = os.path.join(os.environ['APPDATA'], 'HERMES')
            defaultScratchDir = defaultOutTmpDir = homeDir
            if not os.path.exists(defaultScratchDir):
                os.makedirs(defaultScratchDir)
            defaultDbLoc = os.path.join(defaultScratchDir, 'hermes.db')
            

        else:
            raise RuntimeError("Cannot determine site-specific information for a %s system!"%s)
        
        self.d = {'srcdir':os.path.split(os.path.abspath(__file__))[0],
                  'scratchdir':defaultScratchDir,
                  'outtmpdir':defaultOutTmpDir,
                  'dbtype':'sqlite',
                  'dbloc':defaultDbLoc }
        configFile = os.path.join(homeDir,'hermes_conf.kvp')
        if os.path.exists(configFile):
            parser = kvp_tools.KVPParser()
            confDict = parser.parse(configFile)
            badKeys = []
            for k,v in confDict.items():
                if k in self.d: self.d[k] = v
                else: badKeys.append(k)
            if badKeys != []:
                raise RuntimeError('The following keys are invalid in your hermes_conf.kvp file (typos?): %s'%badKeys)
    def scratchDir(self):
        return self.d['scratchdir']
    def outTmpDir(self):
        return self.d['outtmpdir']
    def srcDir(self):
        return self.d['srcdir']
    def dbType(self):
        return self.d['dbtype']
    def dbLoc(self):
        return self.d['dbloc']
    
def main():
    "This is a simple test routine"
    
    s = SiteInfo()
    for m in ['scratchDir', 'outTmpDir', 'srcDir', 'dbType']:
        print "%s : %s"%(m, getattr(s,m)())

############
# Main hook
############

if __name__=="__main__":
    main()
