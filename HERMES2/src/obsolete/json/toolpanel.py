##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

import pyjd # dummy in pyjs

from serviceinteractor import ServiceInteractor
from hermesservices import TopLevelService

class ToolPanel(ServiceInteractor):
    instanceCount= 0
    def __init__(self, owner, name):
        ServiceInteractor.__init__(self, owner, name, TopLevelService())
        self.id= ToolPanel.instanceCount
        ToolPanel.instanceCount += 1
    def getMyId(self):
        return self.id

    def setOffsetBase(self,top,left):
        pass
    

