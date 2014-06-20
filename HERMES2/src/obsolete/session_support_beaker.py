#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
# -Other session's files could be downloaded the same way.
####################################
_hermes_svn_id_="$Id$"

import sys,os.path,thread,time
import bottle
import site_info
from beaker.middleware import SessionMiddleware

# If executing under mod_wsgi, we need to add the path to the source
# directory of this script.
_sI = site_info.SiteInfo()
try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    if _sI.srcDir() not in sys.path:
        sys.path.append(_sI.srcDir())
except:
    pass

import db_routines, privs
from user_fs import HermesUserFS


class LockedState:
    """
    This should really be an inner class of UISession, but I don't know if that
    would confuse SQLAlchemy
    """
    def __init__(self, uiSession):
        self.uiSession = uiSession
        self._lock()
        pass
    def _lock(self):
        pass
    def _unlock(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, tp, value, traceback):
        self._unlock()
    def __del__(self):
        self._unlock()
    def fs(self):
        """
        Return the session filesystem, creating it if necessary
        """
        return HermesUserFS(self.uiSession)

class UISession:
    
    def __init__(self, beakerSession):
        self.beakerSession = beakerSession
        if 'notes' not in self.beakerSession:
            self.beakerSession["notes"] = "just created"

    def __len__(self):
        return len(self.beakerSession)
    
    def __getitem__(self, key):
        return self.beakerSession[key]
    
    def __setitem__(self, key, value):
        self.beakerSession[key] = value
    
    def __delitem__(self, key):
        return self.beakerSession.__delitem__(key)
    
    def __iter__(self):
        return self.beakerSession.iterkeys()
    
    def __contains__(self, item):
        return item in self.beakerSession
        
    def clearSessionData(self):
        with self.getLockedState() as state:
            state.fs().clearAllInfo()
        for k in self.beakerSession:
            if not k[0] == '_': # Ignore system fields
                del self.beakerSession[k]
        self.beakerSession["notes"] = "just cleared"
        self.beakerSession["models"] = []

    def __str__(self):
        return "WrappedBeakerSession"
    def __repr__(self):
        return "<WrappedBeakerSession(%s)>"%repr(self.beakerSession)
    
    def getLockedState(self):
        return LockedState(self)

    def getUserID(self):
        return 2
    
    def getDefaultReadGroupID(self):
        return 2
    
    def getDefaultWriteGroupID(self):
        return 2
    
    def getScratchDir(self):
        global _sI
        scratchDir = os.path.join(_sI.scratchDir(),"%d"%self.getUserID())
        if not os.path.lexists(scratchDir):
            os.makedirs(scratchDir)
        return scratchDir
    
    def getPrivs(self):
        """
        Returns an object bearing privilege info
        """
        return privs.Privileges(self.getUserID())
    
    def getDictSummary(self):
        d = {}
        for k,v in self.beakerSession.items():
            if isinstance(v,HermesUserFS):
                d[k] = v.getJSONSafeSummary()
            else:
                d[k] = v
        return d

    def save(self):
        self.beakerSession.save()

    @classmethod
    def getFromRequest(cls,bottleRequest):
        return UISession(bottleRequest.environ['beaker.session'])
    
    @classmethod
    def wrapBottleApp(cls, bottleApp):
        global _sI
        session_opts = {
                        'session.type':'ext:database',
                        'session.url':db_routines.DbInterface(echo=True, dbType=_sI.dbType()).getURI(),
                        'session.lock_dir':'/tmp'
                        }
        return SessionMiddleware(bottle.app(), session_opts)
