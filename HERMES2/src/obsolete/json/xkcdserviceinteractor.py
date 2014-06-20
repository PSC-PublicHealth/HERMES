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
from pyjamas.ui.Controls import HorizontalDemoSlider2
from serviceinteractor import ServiceInteractor

class HSliderClass(VerticalPanel):
    def __init__(self, minval,maxval):
        VerticalPanel.__init__(self)

        self.setSpacing(10)
        self.b = HorizontalDemoSlider2(minval, maxval)
        self.add(self.b)

        self.b.setHeight("20px")
        self.b.setWidth("450px")

        self.b.addControlValueListener(self)

        self.label = InputControl(minval,maxval)
        self.add(self.label)
        self.label.setControlPos(self.b.value)
        self.label.setValue(self.b.value)

        self.label.addControlValueListener(self)

        #self.b.setControlPos(int((minval+maxval)/2))
        #self.b.setValue(int((minval+maxval)/2))
        #self.label.setControlPos(int((minval+maxval)/2))
        #self.label.setValue(int((minval+maxval)/2))

    def onControlValueChanged(self, sender, old_value, new_value):
        if sender == self.label:
            self.b.setControlPos(int(new_value))
            self.b.setValue(int(new_value), 0)
        elif sender == self.b:
            self.label.setControlPos(int(new_value))
            self.label.setValue(int(new_value), 0)
            
    def setValue(self,value):
        self.b.setControlPos(int(value))
        self.b.setValue(int(value), 0)
        self.label.setControlPos(int(value))
        self.label.setValue(int(value), 0)

    def getValue(self):
        return self.label.value
    
class XKCDService(JSONProxy):
    def __init__(self):
        JSONProxy.__init__(self,"/bottle_hermes/XKCDService",["fetch"])
    
class XKCDServiceInteractor(ServiceInteractor):
    def __init__(self, owner, name="xkcdServiceInteractor"):
        ServiceInteractor.__init__(self,owner,name,XKCDService())
        
        info = """
        <p>Which strip summary would you like to fetch?
           </p>"""

        self.text_area = TextArea()
        self.text_area.setCharacterWidth(80)
        self.text_area.setVisibleLines(8)

        self.button_xkcd = Button("Fetch XKCD info",self)
        self.stripSlider= HSliderClass(1,852)
        
        panel = VerticalPanel(Spacing=10)
        panel.add(HTML(info))
        panel.add(self.text_area)
        panel.add(self.stripSlider)
        panel.add(self.button_xkcd)
        self.add(panel)

    def applyState(self,state):
        if state.has_key('TextArea'):
            self.text_area.setText(state['TextArea'])
        if state.has_key('WhichStrip'):
            self.stripSlider.setValue(int(state['WhichStrip']))
        ServiceInteractor.applyState(self,state)
        
    def saveState(self):
        self.state['TextArea']= self.text_area.getText()
        self.state['WhichStrip']= int(self.stripSlider.getValue())
        ServiceInteractor.saveState(self)

    def doActionCall(self, sender):
        if sender == self.button_xkcd:
            whichStrip= int(self.stripSlider.getValue())
            id= self.remoteService.fetch(str(whichStrip),self)
            return id,('button_xkcd',None)
        else:
            return None,None

    def doActionResponse(self, callInfo, response,request_info):
        sender,method= callInfo
        if sender=='button_xkcd':
            self.text_area.setText(response['transcript'])
            return True
        else:
            return False

