##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

from pyjamas import Window

class _ResourceHook:
    def __init__(self, owner, cb):
        self.cb= cb
        self.owner= owner
    def update(self,name,infoList):
        self.cb(name,infoList)

class ResourceManager:
    def __init__(self, owner):
        self.owner= owner
        self.resourceDict= {}
        
    def addHook(self,name,callback):
        if not self.resourceDict.has_key(name):
            self.resourceDict[name]= []
        newHook= _ResourceHook(self,callback)
        self.resourceDict[name].append(newHook)

    def update(self,name,infoList):
        #Window.alert('update on %s has %d elements'%(name,len(self.resourceDict[name])))
        if self.resourceDict.has_key(name):
            for client in self.resourceDict[name]:
                client.update(name,infoList)