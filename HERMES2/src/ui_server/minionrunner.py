#!/usr/bin/env python

_hermes_svn_id_="$Id$"

import sys, os, os.path, time, subprocess, threading
import site_info
import i18n
import gettext

from ui_utils import _logMessage

inlizer = i18n.i18n('locale')
_=inlizer.translateString


#_sI = site_info.SiteInfo()
#_scratchDir= _sI.scratchDir()
#_outTmpDir= _sI.outTmpDir()
#_logFileName= "%s/hermes_service.log"%_scratchDir
#_debug= True
#_uploadChunkSize= 10000

class MinionFactory():
    class MinionProc(subprocess.Popen):
        minionId = 1
        
        def __init__(self,cmdList,env,cwd,nreps=1):
            self.statusString = _("starting")
            self.logFilePath = None
            self.cwd = cwd
            self.mutex = threading.Semaphore()
            self.done = False
            self.id = MinionFactory.MinionProc.minionId
            self.nReps = nreps
            self.currentRep = 0
            MinionFactory.MinionProc.minionId += 1
            self.childHolderThread = threading.Thread(group=None, target=self.childHolder,
                                                      args = (cmdList,env,cwd))
            self.childHolderThread.start()
    
        def childHolder(self, cmdList, env, cwd):
            subprocess.Popen.__init__(self, cmdList, bufsize=1, stdin=None,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                      env=env, cwd=cwd)
            self.stdoutThread= threading.Thread(group=None,target=self.pipeToLog,
                                                args=(self.stdout,))
            self.stdoutThread.start()
            self.stderrThread= threading.Thread(group=None,target=self.pipeToParse,
                                                args=(self.stderr,))
            self.stderrThread.start()
            retcode = self.wait()
            if not self.done:
                self.mutex.acquire()
                self.done = True
                self.statusString = "%s %d %s %s"%(_('failed with retcode'),retcode,_('at'),time.asctime())
                self.mutex.release()
    
        def pipeToLog(self, p):
            while not self.done:
                line = p.readline()
                if len(line)>0:
                    _logMessage('%d says: %s\n'%(self.minionId,line))
                
        def pipeToParse(self, p):
            while not self.done:
                line = p.readline()
                if len(line)>0:
                    sys.stderr.write(line+'\n')
                    if line.find('#finished#')>=0:
                        self.mutex.acquire()
                        self.statusString = "%s %s"%(_('finished at'),time.asctime())
                        self.done = True
                        self.mutex.release()
                        break
                    elif line[0:9]=='#FracDone':
                        frac = float(line.split()[1])
                        self.mutex.acquire()
                        if self.nReps > 1:
                            print "Frac = " + str(frac)
                            if frac == 0.0:
                                self.currentRep += 1
                            self.statusString = '%s: rep: %d %d%% %s'%(_('running'),self.currentRep,int(100*frac),_('complete'))
                        else:
                            self.statusString = '%s: %d%% %s'%(_('running'),int(100*frac),_('complete'))
                        self.mutex.release()
                    elif line[0:12]=='#LogFilePath':
                        path = line[13:].strip()
                        self.mutex.acquire()
                        self.logFilePath = os.path.join(self.cwd,path)
                        self.mutex.release()
                    elif line[0]=='#':
                        self.mutex.acquire()
                        self.statusString = line[1:]
                        self.mutex.release()
                    else:
                        pass
            
        def getStatus(self):
            """
            Returns a status string
            """
            self.mutex.acquire()
            result = self.statusString[:]
            self.mutex.release()
            return result
        
    def __init__(self):
        self.siteInfo = site_info.SiteInfo()
        self.liveRuns = {}
    
    def startRun(self, modelId, runName, cwd, nReps=1, optList=None):
        """
        Returns a MinionProc, which owns a thread which monitors the minion
        """
        env = os.environ.copy()
        env['HERMES_DATA_PATH'] = os.path.join(self.siteInfo.srcDir(),'master_data','unified')
        mainSrc = os.path.join(self.siteInfo.srcDir(),'main.py')
        argList = ['python', '-u', mainSrc, '--minion', '--average', "--out=%s"%runName]
        if optList is not None:
            argList += optList[:] #shallow copy
        argList += ['--use_db', '%d:%d'%(modelId,nReps)]
        sp = MinionFactory.MinionProc( argList, env=env, cwd=cwd, nreps=nReps)
        infoDir = { 'modelId':modelId, 'starttime':time.asctime(), 'runName':runName}
        self.liveRuns[sp.id] = (infoDir,sp)
        return sp.id
    
    

