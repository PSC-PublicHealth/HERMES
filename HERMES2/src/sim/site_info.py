#! /usr/bin/env python

########################################################################
# Copyright C 2013, Pittsburgh Supercomputing Center (PSC).            #
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

_hermes_svn_id_="$Id$"

import os, os.path, platform
import kvp_tools
import ipath
from full_import_paths import HermesBaseDir

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
