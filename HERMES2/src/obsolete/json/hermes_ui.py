
notesText= """
<h1>Notes</h1>
<ul>
<li>Why can't I do delete at line 362?
<li>Transaction numbers are getting desynchronized because some server transactions go to ServiceInteractors.
<li>Make sure state gets touched early so that it is protected from deletion.
<li>The scratch directory is getting culled too often, I think.
</ul>
"""

_hermes_svn_id_="$Id$"

import pyjd # dummy in pyjs

from pyjamas import DOM, Window
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui.TextBox import TextBox
from pyjamas.ui.Label import Label
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.JSONService import JSONProxy
from pyjamas.JSONParser import JSONParser
from pyjamas.ui.SimplePanel import SimplePanel
from pyjamas.ui.FormPanel import FormPanel
from pyjamas.ui.NamedFrame import NamedFrame
from pyjamas.ui.Hidden import Hidden
from pyjamas.ui.TabPanel import TabPanel
from pyjamas.ui import HasAlignment
from pyjamas.ui.PopupPanel import PopupPanel
from hermesservices import TopLevelService
from testserviceinteractor import TestServiceInteractor
from echoserviceinteractor import EchoServiceInteractor
#from xkcdserviceinteractor import XKCDServiceInteractor
from guruserviceinteractor import GuruServiceInteractor
from storesinteractor import StoresInteractor
from routesinteractor import RoutesInteractor
from reportinteractor import ReportInteractor
from toolsinteractor import ToolsInteractor
from resourcemanager import ResourceManager
#from testpanel import MyToolPanel,TestPanel

from __pyjamas__ import JS,doc,jsimport
import dynamic

def getTotalOffsets(elem):
    JS("""
    t= l= 0;
    if (elem.offsetParent) {
        do {
            l += elem.offsetLeft;
            t += elem.offsetTop;
        } while (elem= elem.offsetParent);
    }
    """)
    return t,l

class StatusPanel(SimplePanel):
    def __init__(self,owner,name):
        SimplePanel.__init__(self)
        self.name= name
        self.owner= owner
        self.state= {}
        panel = VerticalPanel(Spacing=10)
        self.status=Label()
        self.debugField= Label()
        panel.add(self.status)
        panel.add(self.debugField)
        self.add(panel)
    def setStatus(self,str):
        self.status.setText(str)
        self.saveState()
    def debugMsg(self,str):
        self.debugField.setText( self.debugField.getText() + " " + msg )
        self.saveState()
    def applyState(self,state):
        if state.has_key("debugTxt"): 
            self.debugField.setText(state["debugTxt"])
        if state.has_key("statusTxt"): 
            self.setStatus(state["statusTxt"])
        self.state= state.copy()        
    def saveState(self):
        for k,v in [("debugTxt",self.debugField.getText()),
                    ("statusTxt",self.status.getText())
                    ]:
            self.state[k]= v
        self.owner.setChildState(self,self.state)

class HermesUI:

    def debugMsg(self,msg):
        Window.alert(msg)
        self.statusPanel.debugMsg(msg)

    def setStatus(self,msg):
        self.statusPanel.setStatus(msg)

    def getChildState(self,child):
        if not self.fullState.has_key(child.name):
            self.fullState[child.name]= {'SessionKey':self.sessionKey}
        return self.fullState[child.name].copy()
    
    def getSessionKey(self):
        return self.sessionKey

    def setChildState(self,child,sDict):
        self.fullState[child.name]= sDict
        self.saveState()

    def saveState(self):
        things= self.fullState.copy()
        for k,v in [("whichTab",self.toolTabs.tabBar.getSelectedTab()),
                    ("whichViewTab",self.viewTabs.tabBar.getSelectedTab())]:
            things[k]= v
        if self.sessionKey is not None:
            things['SessionKey']= self.sessionKey
        sC= self.stateCache
        val= self.parser.encode(things)
        JS("sC.value=val;")
        
    def restoreOrInitializeState(self):
        sC= self.stateCache
        JS("val= sC.value;")
        if len(val)>2: # length 2 is just enough for empty brackets
            things= self.parser.decode(val)
            self.applyState(things)
        else:
            self.applyState(self.initialState)
            
    def applyState(self,things):
        if things.has_key('SessionKey'): self.sessionKey= things['SessionKey']
        if things.has_key('whichTab'): self.toolTabs.selectTab(things['whichTab'])
        if things.has_key('whichViewTab'): 
            if self.viewTabs.getWidgetCount()>things['whichViewTab']:
                self.viewTabs.selectTab(things['whichViewTab'])
        self.fullState= things.copy()
        
    def checkJIT(self):
        if not self.jitLoaded:
            dynamic.ajax_import("myjit.js", names = ['$jit'])
            JS("""
               $jit.document=$doc
               """)
            self.jitLoaded= True
        return True
            
    def buildPage(self):

        # Must set up status display fields before initializing children,
        # because they may try to set status values
        
        self.toolTabs = TabPanel(Width="100%", Height="300px")
        self.viewTabs = TabPanel(Width="100%", Height="600px")
        
        self.resourceManager= ResourceManager(self)
        
        for (nm, itype) in [
                           #("Echo", EchoServiceInteractor),
                           #("XKCD", XKCDServiceInteractor),
                           #("Test", TestServiceInteractor),
                           ("Stores", StoresInteractor),
                           ("Routes", RoutesInteractor),
                           ("Reports", ReportInteractor),
                           ("Tools", ToolsInteractor)
                           ]:
            self.interactors.append( itype(self,nm) )  
                  
        for child in self.interactors:
            self.toolTabs.add(child, child.name)

        self.toolTabs.add(HTML(notesText), "Notes")
        self.toolTabs.add(HTML("This spacer should not be visible!"), None) # None means separator
        self.statusPanel= StatusPanel(self,'Status')
        self.interactors.append(self.statusPanel)
        self.toolTabs.add(self.statusPanel, self.statusPanel.name)
        guruInteractor= GuruServiceInteractor(self,'Guru')
        self.interactors.append( guruInteractor )
        self.toolTabs.add( guruInteractor, guruInteractor.name )
        
        self.toolTabs.selectTab(0)
        self.toolTabs.addTabListener(self)
        
        buttons = HorizontalPanel()
        buttons.setSpacing(8)
        
        info = """<h2>HERMES</h2>"""
        
        panel = VerticalPanel(Spacing=10,Width="100%")
        panel.add(HTML(info))
        panel.add(buttons)
        panel.add(self.toolTabs)
        panel.add(self.viewTabs)

        RootPanel().add(panel)

    def addView(self,viewPanel):
        """
        viewPanel must implement the state management functions, as StatusPanel does.
        """
        if hasattr(viewPanel,'name'):
            name= viewPanel.name
        else:
            name= 'View%d'%self.viewNum
            self.viewNum += 1
        if name in [interactor.name for interactor in self.interactors]:
            Window.alert('The panel name %s is already in use.'%name)
            return False
        if not hasattr(viewPanel,'name'):
            viewPanel.name= name
        newIndex= self.viewTabs.getWidgetCount()
        self.viewTabs.add(viewPanel, viewPanel.name)
        self.viewTabs.selectTab(newIndex)
        self.interactors.append(viewPanel)
        t,l= getTotalOffsets(self.viewTabs.getWidget(newIndex).getElement())
        viewPanel.setOffsetBase(t,l)        
        return True

    def subscribeToResource(self,name,callback):
        """
        name is the name of the resource, e.g. 'Stores'
        Callback signature should be cb(name,[dict,dict,dict...])
        """
        self.resourceManager.addHook(name,callback)
        
    def updateResource(self,name,infoList):
        """
        name is the name of the resource, e.g. 'Stores'
        infoList is a list of dicts
        """
        self.resourceManager.update(name,infoList)

    def onTabSelected(self, sender, tabIndex):
        if sender==self.toolTabs.tabBar:
            self.fullState['whichTab']= tabIndex
        elif sender==self.viewTabs.tabBar:
            self.fullState['whichViewTab']= tabIndex
        self.saveState()

    def onBeforeTabSelected(self, sender, tabIndex):
        return True # any tab can be selected

    def onModuleLoad(self):
        
        self.TEXT_WAITING = "Waiting for response..."
        self.TEXT_READY = "Ready"
        self.TEXT_ERROR = "Server Error"
        self.initialState= {'Status':{'statusTxt':'Status text goes here',
                                      'debugTxt':'Debug text goes here'
                                      },
                            'Uploads':{}
                            # No session key to cause a fresh one to be generated
                            } 
        self.inFlight= {} 
        self.parser= JSONParser()
        self.stateCache= DOM.getElementById("state_cache")
        self.sessionKey= None
        self.fullState= {}
        self.interactors= []
        self.viewNum= 0
        self.jitLoaded= False

        self.remote_topLevel = TopLevelService()

        self.buildPage()

        self.restoreOrInitializeState()
        for child in self.interactors:
            child.applyState(self.getChildState(child))
        if self.sessionKey is None:
            id= self.remote_topLevel.getSessionKey(None,self)
            self.inFlight[id]= ('getSessionKey',None)
            self.setStatus('waiting for getSessionKey')
        
    def onClick(self, sender):
        #self.setStatus(self.TEXT_WAITING)
        Window.alert("Internal error; can't tell what clicked")
        self.setStatus(self.TEXT_READY)

    def onRemoteResponse(self, response, request_info):
        try:
            #Window.alert('Got something; id is '+request_info.id)
            if self.inFlight.has_key(request_info.id):
                sender,method= self.inFlight[request_info.id]
                #Window.alert('got response for '+sender)
                #del self.inFight[request_info.id]
                if sender=='getSessionKey':
                    self.sessionKey= response
                    newId= self.remote_topLevel.getClientStateUpdate(self.sessionKey,self)
                    self.inFlight[newId]= ('getClientStateUpdate',None)
                    self.setStatus('Waiting for getClientStateUpdate')
                elif sender=='getClientStateUpdate':
                    self.applyState(self.parser.decode(response))
                    for child in self.interactors:
                        child.applyState(self.getChildState(child))
                    self.saveState()
                    self.setStatus('State updated')
                    for irtr in self.interactors:
                        if hasattr(irtr,'lateBuild'):
                            irtr.lateBuild()
                else:
                    self.debugMsg("Got unknown response %s,%s"%(str(sender),str(method)))
                    self.setStatus("Fumbled a %s message"%str(sender))
            else:
                self.debugMsg("Missing inFlight info for json message %s"%request_info.id)
                self.setStatus('Fumbled a message')
        except Exception,e:
            self.debugMsg("No request info: %s"%str(e))
            self.setStatus('No request info')

    def onRemoteError(self, code, errobj, request_info):
        # onRemoteError gets the HTTP error code or 0 and
        # errobj is an jsonrpc 2.0 error dict:
        #     {
        #       'code': jsonrpc-error-code (integer) ,
        #       'message': jsonrpc-error-message (string) ,
        #       'data' : extra-error-data
        #     }
        Window.alert('Got an error!')
        message = errobj['message']
        if code != 0:
            self.setStatus("HTTP error %d: %s" % 
                                (code, message))
        else:
            code = errobj['code']
            self.setStatus("JSONRPC Error %s: %s" %
                                (code, message))
        del self.inFlight[request_info.id]
        self.saveState()

if __name__ == '__main__':
    # for pyjd, set up a web server and load the HTML from there:
    # this convinces the browser engine that the AJAX will be loaded
    # from the same URI base as the URL, it's all a bit messy...
    pyjd.setup("./output/hermes_ui.html")
    app = HermesUI()
    app.onModuleLoad()
    pyjd.run()

