##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

import pyjd # dummy in pyjs

from pyjamas import Window
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.ui.ListBox import ListBox
from pyjamas.JSONService import JSONProxy
from pyjamas.JSONParser import JSONParser
from pyjamas.ui.SimplePanel import SimplePanel
from serviceinteractor import ServiceInteractor

class EchoServicePython(JSONProxy):
    def __init__(self):
        JSONProxy.__init__(self, "/bottle_hermes/EchoService",
                           ["echo", "reverse", "uppercase", "lowercase",
                            "nonexistant"])
        
class EchoServiceInteractor(ServiceInteractor):
    def __init__(self, owner, name="echoServiceInteractor"):
        ServiceInteractor.__init__(self,owner,name,EchoServicePython())
        self.METHOD_ECHO = "Echo"
        self.METHOD_REVERSE = "Reverse"
        self.METHOD_UPPERCASE = "UPPERCASE"
        self.METHOD_LOWERCASE = "lowercase"
        self.METHOD_NONEXISTANT = "Non existant"
        self.methods = [self.METHOD_ECHO, self.METHOD_REVERSE, 
                        self.METHOD_UPPERCASE, self.METHOD_LOWERCASE, 
                        self.METHOD_NONEXISTANT]

        info = """
        <p>Enter some text below, and press a button to send the text
           to an Echo service on your server. An echo service simply sends the exact same text back that it receives.
           </p>"""

        self.text_area = TextArea()
        self.text_area.setCharacterWidth(80)
        self.text_area.setVisibleLines(8)
        
        self.method_list = ListBox()
        self.method_list.setVisibleItemCount(1)
        for method in self.methods:
            self.method_list.addItem(method)
        self.method_list.setSelectedIndex(0)
    
        method_panel = HorizontalPanel()
        method_panel.add(HTML("Remote string method to call: "))
        method_panel.add(self.method_list)
        method_panel.setSpacing(8)

        self.button_py = Button("Send to Python Service", self)

        panel = VerticalPanel(Spacing=10)
        panel.add(HTML(info))
        panel.add(self.text_area)
        panel.add(method_panel)
        panel.add(self.button_py)
        self.add(panel)

    def applyState(self,state):
        if state.has_key('TextArea'):
            self.text_area.setText(state['TextArea'])
        if state.has_key('Method'):
            self.method_list.setSelectedIndex(state['Method'])
        ServiceInteractor.applyState(self,state)
        
    def saveState(self):
        self.state['TextArea']= self.text_area.getText()
        self.state['Method']= self.method_list.getSelectedIndex()
        ServiceInteractor.saveState(self)

    def doActionCall(self, sender):
        if sender == self.button_py:
            method = self.methods[self.method_list.getSelectedIndex()]
            text = self.text_area.getText()
            if method == self.METHOD_ECHO:
                id = self.remoteService.echo(text, self)
            elif method == self.METHOD_REVERSE:
                id = self.remoteService.reverse(text, self)
            elif method == self.METHOD_UPPERCASE:
                id = self.remoteService.uppercase(text, self)
            elif method == self.METHOD_LOWERCASE:
                id = self.remoteService.lowercase(text, self)
            elif method == self.METHOD_NONEXISTANT:
                id = self.remoteService.nonexistant(text, self)
            return id, ('button_py',method)
        else:
            return None,None

    def doActionResponse(self, callInfo, response,request_info):
        sender,method= callInfo
        if sender=='button_py':
            self.text_area.setText(response)
            return True
        else:
            return False

