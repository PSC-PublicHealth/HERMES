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
from serviceinteractor import ServiceInteractor
from hermesservices import TopLevelService

class TestServiceInteractor(ServiceInteractor):
    def __init__(self, owner, name="TestServiceInteractor"):
        ServiceInteractor.__init__(self,owner,name,TopLevelService())
        
        info = """
        <p>This runs some random test on the server side.
           </p>"""

        self.text_area = TextArea()
        self.text_area.setCharacterWidth(80)
        self.text_area.setVisibleLines(8)

        self.button = Button("Press Me!",self)
        
        panel = VerticalPanel(Spacing=10)
        panel.add(HTML(info))
        panel.add(self.text_area)
        panel.add(self.button)
        self.add(panel)

    def applyState(self,state):
        if state.has_key('TextArea'):
            self.text_area.setText(state['TextArea'])
        ServiceInteractor.applyState(self,state)
        
    def saveState(self):
        self.state['TextArea']= self.text_area.getText()
        ServiceInteractor.saveState(self)

    def doActionCall(self, sender):
        if sender==self.button:
            id= self.remoteService.test(self.state['SessionKey'],self)
            info= ("button",None)
            return id, info
        else:
            return None,None

    def doActionResponse(self, callInfo, response, request_info):
        self.text_area.setText(response)
        return True
