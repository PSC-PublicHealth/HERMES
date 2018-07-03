#! /usr/bin/env python


_hermes_svn_id_="$Id$"

import os, os.path, platform
import ipath
from full_import_paths import HermesBaseDir
import kvp_tools

class SiteInfo:
    def __init__(self,configFilePath=None):
        s = platform.system()
        defaultUser = 'hermes'
        defaultPword = 'hermes'
        defaultDB = 'hermes'
        defaultHost = '127.0.0.1'
        
        if s == 'Linux' or s=='Darwin':
            homeDir = os.environ['HOME']
            defaultScratchDir = '/tmp'
            defaultOutTmpDir = '/tmp'
            defaultDbLoc = os.path.join(HermesBaseDir, 'hermes.db')
            defaultAlembicIniPath = HermesBaseDir
            
        elif s == 'Windows':
            homeDir = os.path.join(os.environ['APPDATA'], 'HERMES')
            defaultScratchDir = defaultOutTmpDir = homeDir
            if not os.path.exists(defaultScratchDir):
                os.makedirs(defaultScratchDir)
            defaultDbLoc = os.path.join(defaultScratchDir, 'hermes.db')
            defaultAlembicIniPath = HermesBaseDir
            
        else:
            raise RuntimeError("Cannot determine site-specific information for a %s system!"%s)
        
        self.d = {'srcdir':os.path.split(os.path.abspath(__file__))[0],
                  'baseDir':HermesBaseDir,
                  'scratchdir':defaultScratchDir,
                  'outtmpdir':defaultOutTmpDir,
                  'dbtype':'sqlite',
                  'dbloc':defaultDbLoc,
                  'dbuser':defaultUser,
                  'dbpword':defaultPword,
                  'dbname':defaultDB,
                  'dbhost':defaultHost,
                  'alembicPath':defaultAlembicIniPath }
        
        ### look for a user specified hermes_conf, then look for a system wide one
        userconfigFile = os.path.join(homeDir,'hermes_conf.kvp')
        sysconfigFile = os.path.join(HermesBaseDir,'hermes_conf.kvp')
        
        ### If system conf exists, set
        if os.path.exists(sysconfigFile):
            parser = kvp_tools.KVPParser()
            confDict = parser.parse(sysconfigFile)
            badKeys = []
            for k,v in confDict.items():
                if k in self.d: self.d[k] = v
                else: badKeys.append(k)
            if badKeys != []:
                raise RuntimeError('Problem with the System-Level HERMES Config File: {0}, These Entries are incorrect {1}'.format(sysconfigFile,badKeys))
        
        if os.path.exists(userconfigFile):
            parser = kvp_tools.KVPParser()
            confDict = parser.parse(userconfigFile)
            badKeys = []
            for k,v in confDict.items():
                if k in self.d: self.d[k] = v
                else: badKeys.append(k)
            if badKeys != []:
                raise RuntimeError('Problem with the User-Level HERMES Config File: {0}, These Entries are incorrect {1}'.format(userconfigFile,badKeys))
        
        ### If specified on creations, use this one.
        if configFilePath is not None:
            if os.path.exists(configFilePath):
                configFile = os.path.join(configFilePath,'hermes_conf.kvp')
                if os.path.exists(configFile):
                    parser = kvp_tools.KVPParser()
                    confDict = parser.parse(configFile)
                    badKeys = []
                    for k,v in confDict.items():
                        if k in self.d: self.d[k] = v
                        else: badKeys.append(k)
                    if badKeys != []:
                        raise RuntimeError('The following keys are invalid in your hermes_conf.kvp file (typos?): %s'%badKeys)
        
            
    def srcDir(self):
        return self.d['srcdir']
    def baseDir(self):
        return self.d['baseDir']
    def scratchDir(self):
        return self.d['scratchdir']
    def outTmpDir(self):
        return self.d['outtmpdir']
    def dbType(self):
        return self.d['dbtype']
    def dbLoc(self):
        return self.d['dbloc']
    def dbUser(self):
        return self.d['dbuser']
    def dbPword(self):
        return self.d['dbpword']
    def dbName(self):
        return self.d['dbname']
    def dbHost(self):
        return self.d['dbhost']
    def alembicPath(self):
        return self.d['alembicPath']
    
    def __str__(self):
        returnString = "HERMES Site Configuration: \n"
        returnString += "    Source Directory:\t\t{0}\n".format(self.srcDir())
        returnString += "    Base HERMES Directory:\t{0}\n".format(self.baseDir())
        returnString += "    Scratch Directory:\t\t{0}\n".format(self.scratchDir())
        returnString += "    Output Directory:\t\t{0}\n".format(self.outTmpDir())
        returnString += "    Database Type:\t\t{0}\n".format(self.dbType())
        returnString += "    Database Location:\t\t{0}\n".format(self.dbLoc())
        returnString += "    Database User:\t\t{0}\n".format(self.dbUser())
        returnString += "    Database Password:\t\t{0}\n".format(self.dbPword())
        returnString += "    Database Name:\t\t{0}\n".format(self.dbName())
        returnString += "    Database Host:\t\t{0}\n".format(self.dbHost())
        returnString += "    Alembic Ini File:\t\t{0}\n".format(self.alembicPath())
        
        return returnString
    
def main():
    "This is a simple test routine"
    
    s = SiteInfo()
    print "{0}".format(str(s))
    #for m in ['scratchDir', 'outTmpDir', 'srcDir', 'dbType']:
    #    print "%s : %s"%(m, getattr(s,m)())

############
# Main hook
############

if __name__=="__main__":
    main()
