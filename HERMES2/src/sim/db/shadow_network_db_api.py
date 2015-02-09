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

import shadow_network as shd


class ShdNetworkDBSimple:
    def __init__(self, dbSession, netId):
        self.dbSession = dbSession;
        self.netId = netId

    def lockNetwork(self):
        "Doesn't work yet!!!"
        return

        self.net = self.dbSession.query(shd.ShdNetwork).\
            filter(shd.ShdNetwork.modelId == self.netId).\
            with_lockmode('update').\
            one()

            

    def getStore(self, storeId):
        "Get a store by ID"
        s = self.dbSession.query(shd.ShdStore).\
            filter(shd.ShdStore.modelId == self.netId).\
            filter(shd.ShdStore.idcode == storeId).\
            one()
        return s

    def getStoreByName(self, storeName):
        "Get a store by Name"
        s = self.dbSession.query(shd.ShdStore).\
            filter(shd.ShdStore.modelId == self.netId).\
            filter(shd.ShdStore.NAME == storeName).\
            one()
        return s

    def getRoute(self, routeName):
        "Get a route by Name"
        r = self.dbSession.query(shd.ShdRoute).\
            filter(shd.ShdRoute.modelId == self.netId).\
            filter(shd.ShdRoute.RouteName == routeName).\
            one()
        return r

    def getStop(self, routeName, stopNum):
        """
        get a stop based on 'RouteName' and 'RouteOrder'
        """
        r = self.dbSession.query(shd.ShdStop).\
            filter(shd.ShdStop.modelId == self.netId).\
            filter(shd.ShdStop.RouteName == routeName).\
            filter(shd.ShdStop.RouteOrder == stopNum).\
            one()
        return r

class ShdNetworkDB(object):
    def __init__(self, dbSession, netId):
        self._dbSession = dbSession
        self._netId = netId
        self._net = ShdNetworkDBSimple(dbSession, netId)
        

    def useShadowNet(self):
        #print "switching to full network!"
        self._net = self._dbSession.query(shd.ShdNetwork).filter(shd.ShdNetwork.modelId==self.netId).one()

    def __getattr__(self, name):
        if not isinstance(self._net, shd.ShdNetwork):
            try:
                return getattr(self._net, name)
            except:
                self.useShadowNet()

        return getattr(self._net, name)

    def __setattr__(self, name,value):
        if name.startswith('_'):
            super(ShdNetworkDB, self).__setattr__(name, value)
        elif isinstance(self._net, shd.ShdNetwork):
            setattr(self._net,name,value)
        else:
            if hasattr(self._net,name): 
                setattr(self._net,name,value)
            else:
                self.useShadowNet()
                setattr(self._net,name,value)

class LockedNet:
    "Use this only in syntax of a context manager to lock a network"
    def __init__(self, session, modelId, expiration=300):
        self.iface = session._hermes_iface
        lockName = "hermes.model_%08d"%modelId
        self.handle = self.iface.advisoryLock(lockName, expiration)
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.iface.advisoryUnlock(self.handle)


class LockedUser:
    "Use this only in syntax of a context manager to lock a user"
    def __init__(self, session, userId, expiration=300):
        self.iface = session._hermes_iface
        lockName = "hermes.user_%08d"%userId
        self.handle = self.iface.advisoryLock(lockName, expiration)
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.iface.advisoryUnlock(self.handle)


