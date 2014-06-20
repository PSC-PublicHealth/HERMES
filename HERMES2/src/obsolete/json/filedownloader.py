_hermes_svn_id_="$Id$"

import pyjd # dummy in pyjs

from pyjamas.JSONParser import JSONParser
from pyjamas.ui.SimplePanel import SimplePanel
from pyjamas.ui.FormPanel import FormPanel
from pyjamas.ui.Hidden import Hidden

class FileDownloadSimplePanel(SimplePanel):
    def __init__(self,idString):
        SimplePanel.__init__(self)

        self.idString= idString
        self.owner= owner
        self.parser= JSONParser()
        self.form = FormPanel()
        self.form.setMethod(FormPanel.METHOD_POST)
        self.form.setAction("dummy")
        self.setID(idString)
        self.metadata= Hidden(name="metadata")
        self.form.add(self.metadata)
        self.add(self.form)
        
    def prepAndSubmit(self, downloadKey, metadataDict):
        metadataDict['downloadKey']= downloadKey
        metadataDict['downloaderIDString']= self.idString
        self.metadata.setValue(self.parser.encode(metadataDict))
        self.form.setAction('/bottle_hermes/download/%s'%downloadKey)
        self.form.submit()
        return True

    def getState(self):
        return {}
    
    def setState(self,state):
        pass
