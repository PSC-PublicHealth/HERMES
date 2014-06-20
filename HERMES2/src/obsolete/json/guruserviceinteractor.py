##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

import pyjd # dummy in pyjs

from pyjamas import Window
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui.Label import Label
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.JSONService import JSONProxy
from pyjamas.JSONParser import JSONParser
from pyjamas.ui.SimplePanel import SimplePanel
from pyjamas.ui.Controls import InputControl
from __pyjamas__ import JS
from serviceinteractor import ServiceInteractor
from hermesservices import TopLevelService

class GuruServiceInteractor(ServiceInteractor):
    def __init__(self, owner, name="GuruServiceInteractor"):
        ServiceInteractor.__init__(self,owner,name,TopLevelService())
        
        self.parser= JSONParser()
        
        info = """
        <p>This provides a view behind the scenes.
           </p>"""

        self.clientStateArea = TextArea()
        self.clientStateArea.setCharacterWidth(80)
        self.clientStateArea.setVisibleLines(8)

        self.serverStateArea = TextArea()
        self.serverStateArea.setCharacterWidth(80)
        self.serverStateArea.setVisibleLines(8)

        self.stateButton = Button("Get state",self)
        self.buildButton = Button("Build shared state",self)
        
        panel = VerticalPanel(Spacing=10)
        panel.add(HTML(info))
        panel.add(Label("Client-side State"))
        panel.add(self.clientStateArea)
        panel.add(Label("Server-side State"))
        panel.add(self.serverStateArea)
        buttonPanel= HorizontalPanel(Spacing=10)
        buttonPanel.add(self.stateButton)
        buttonPanel.add(self.buildButton)
        panel.add(buttonPanel)
        self.add(panel)

    def applyState(self,state):
        if state.has_key('ServerStateArea'):
            self.serverStateArea.setText(state['ServerStateArea'])
        if state.has_key('ClientStateArea'):
            self.clientStateArea.setText(state['ClientStateArea'])
        ServiceInteractor.applyState(self,state)
        
    def saveState(self):
        self.state['ServerStateArea']= self.serverStateArea.getText()
        self.state['ClientStateArea']= self.clientStateArea.getText()
        ServiceInteractor.saveState(self)

    def doActionCall(self, sender):
        if sender==self.stateButton:
            try:
                sC= self.owner.stateCache
                JS("val= sC.value;")
                censoredState= self.parser.decode(val)
                censoredState[self.name]['ClientStateArea']= 'censored to avoid infinite regress'
                self.clientStateArea.setText(self.parser.encode(censoredState))
            except Exception,e:
                self.clientStateArea.setText('Could not find client state: %s'%e)
            id= self.remoteService.getServerState(self.state['SessionKey'],self)
            info= ("getServerState",None)
            return id, info
        elif sender==self.buildButton:
            id= self.remoteService.buildSharedState(self.state['SessionKey'],self)
            info= ("buildSharedState",None)
            return id, info
        else:
            return None,None

    def doActionResponse(self, callInfo, response, request_info):
        self.serverStateArea.setText(response)
        return True
