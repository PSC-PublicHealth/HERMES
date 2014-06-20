##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

import pyjd # dummy in pyjs

from pyjamas import Window, DOM
from __pyjamas__ import JS
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.Label import Label
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.ui.ListBox import ListBox
from pyjamas.JSONService import JSONProxy
from pyjamas.JSONParser import JSONParser
from pyjamas.ui.SimplePanel import SimplePanel
from serviceinteractor import ServiceInteractor
from hermesservices import TopLevelService
from toolpanel import ToolPanel
from fireworkspanel import FireworksPanel
from fwsvgpanel import FwSVGPanel
import dynamic

def getTotalOffsetsUpTo(elem,topElem):
    JS("""
    t= l= 0;
    if (elem.offsetParent) {
        do {
            //alert('Comparing ' + elem.innerHTML + ' ####to#### ' + topElem.innerHTML);
            if (elem==topElem) {
                //alert('Terminating!');
                break;
            }
            l += elem.offsetLeft;
            t += elem.offsetTop;
        } while (elem= elem.offsetParent);
    }
    """)
    return t,l

class HyperGraphPanel(ToolPanel):
    
    def onAttach(self):
        ToolPanel.onAttach(self)
        if self.owner.checkJIT(): # may cause dynamic.ajax_import
            dynamic.ajax_import("hypergraphpanel_util.js", names=['hypergraphpanel_init'])
        else:
            Window.alert('Dynamic load of Javascript InfoVis Toolkit failed!')
        json= self.jsonString
        json= self.jsonString
        myId= self.getMyId()
        containerName= 'infovis%d'%myId
        logName= 'log%d'%myId
        detailsName= 'inner-details%d'%myId
        JS("""
           hypergraphpanel_init(containerName,logName,detailsName,eval('('+json+')'));
        """)
    
    def __init__(self,owner,jsonString,name=None):
        ToolPanel.__init__(self, owner, name)
        if name is None:
            self.name= "HyperGraph%d"%self.getMyId()
#        self.owner= owner
        self.jsonString= jsonString
        self.state= {}
        panel = VerticalPanel(Spacing=10,Width="100%")
        controlPanel= HorizontalPanel(Spacing=10,Width="100%")
        controlPanel.add(Label('There are no controls'))
        panel.add(controlPanel)
        workPanel= HorizontalPanel(Spacing=10)
        #workPanel.setSize("100%","500px")
        leftPanel= VerticalPanel(Spacing=10)
        myId= self.getMyId()
        self.infoVisDiv= HTML('<div id="infovis%d"></div>'%myId)
        self.infoVisDiv.setSize("500px","500px")
        leftPanel.add(self.infoVisDiv)
        workPanel.add(leftPanel)
        rightPanel= VerticalPanel(Spacing=10)
        rightPanel.setHeight("100%")
        self.innerDetailsDiv= HTML('<div id="inner-details%d"></div>'%myId)
        rightPanel.add(self.innerDetailsDiv)
        workPanel.add(rightPanel)
        logPanel= VerticalPanel(Spacing=10)
        logPanel.setHeight("100%")
        self.logDiv= HTML('<div id="log%d"></div>'%myId)
        logPanel.add(self.logDiv)
        workPanel.add(logPanel)
        panel.add(workPanel)
        self.add(panel)
        self.saveState()

    def applyState(self,state):
        if state.has_key("jsonString"):
            self.jsonString= state["jsonString"]
        self.state= state.copy()        
    def saveState(self):
        self.state["jsonString"]= self.jsonString
        self.owner.setChildState(self,self.state)
        
class TreePanel(ToolPanel):
    
    def onAttach(self):
        ToolPanel.onAttach(self)        
        if self.owner.checkJIT(): # may cause dynamic.ajax_import
            dynamic.ajax_import("treepanel_util.js", names=['treepanel_init'])
        else:
            Window.alert('Dynamic load of Javascript InfoVis Toolkit failed!')
        json= self.jsonString
        prefix= self.name
        myId= self.getMyId()
        containerName= 'infovis%d'%myId
        logName= 'log%d'%myId
        detailsName= 'inner-details%d'%myId
        JS("""
           treepanel_init(containerName,logName,detailsName,eval('('+json+')'),prefix);
        """)
    
    def __init__(self,owner,jsonString,name=None):
        ToolPanel.__init__(self, owner, name)
        if name is None:
            self.name= "Tree%d"%self.getMyId()
#        self.owner= owner
        self.jsonString= jsonString
        self.state= {}
        panel = VerticalPanel(Spacing=10,Width="100%")
        controlPanel= HorizontalPanel(Spacing=10,Width="100%")
        controlPanel.add(Label('There are no controls'))
        panel.add(controlPanel)
        workPanel= HorizontalPanel(Spacing=10)
        #workPanel.setSize("100%","500px")
        leftPanel= VerticalPanel(Spacing=10)
        myId= self.getMyId()
        self.infoVisDiv= HTML('<div id="infovis%d"></div>'%myId)
        self.infoVisDiv.setSize("500px","500px")
        leftPanel.add(self.infoVisDiv)
        workPanel.add(leftPanel)
        rightPanel= VerticalPanel(Spacing=10)
        rightPanel.setHeight("100%")
        self.innerDetailsDiv= HTML('<div id="inner-details%d"></div>'%myId)
        rightPanel.add(self.innerDetailsDiv)
        workPanel.add(rightPanel)
        logPanel= VerticalPanel(Spacing=10)
        logPanel.setHeight("100%")
        self.logDiv= HTML('<div id="log%d"></div>'%myId)
        logPanel.add(self.logDiv)
        workPanel.add(logPanel)
        panel.add(workPanel)
        self.add(panel)
        self.saveState()
    def applyState(self,state):
        if state.has_key("jsonString"):
            self.jsonString= state["jsonString"]
        self.state= state.copy()        
    def saveState(self):
        self.state["jsonString"]= self.jsonString
        self.owner.setChildState(self,self.state)
        
class ThingSelector(HorizontalPanel):
    def __init__(self, owner, thingName, thingTypeName, noneOption=False):
        HorizontalPanel.__init__(self,Spacing=10)
        self.owner= owner
        self.thingName= thingName
        self.thingTypeName= thingTypeName
        self.noneOption = noneOption
        self.add(Label(self.thingName))
        self.file_list = ListBox()
        self.file_list.setVisibleItemCount(0)
        self.fileIndexList= []
        self.file_list.addChangeListener(self.owner.onClick)
        self.add(self.file_list)
        owner.owner.subscribeToResource(thingTypeName,getattr(self,'handleResourceUpdate'))
        
    def setState(self,state):
        if state.has_key('noneOption'):
            self.noneOption = state['noneOption']
        if state.has_key('fileList'):
            self.rebuildList(state['fileList'])
        if state.has_key('FileIndex'):
            self.file_list.setSelectedIndex(state['FileIndex'])

    def getState(self):
        return {'FileIndex':self.file_list.getSelectedIndex(), 'fileList':self.fileIndexList[1:] if self.noneOption else self.fileIndexList, 'noneOption':self.noneOption }
    
    def rebuildList(self,resultList):
        self.file_list.clear()
        self.fileIndexList = []
        if self.noneOption:
            self.file_list.addItem('None')
            self.fileIndexList.append('blah')
        for r in resultList:
            self.file_list.addItem(r['shortName'])
            self.fileIndexList.append(r)
        self.file_list.setSelectedIndex(0)
#        l = len(self.fileIndexList)
#        s = "%s fileIndexList len: %d"%(self.thingName,l)
#        Window.alert(s)
#        for i in range(l):
#            Window.alert("item %d: %s"%(i, self.fileIndexList[i]))


    def handleResourceUpdate(self,name,infoList):
        self.rebuildList(infoList)
        self.file_list.setSelectedIndex(0)
        
    def lateBuild(self):
        pass
    
    def getCurrentUploadKey(self):
        if self.file_list.getItemCount()==0:
            return None
        if self.noneOption:
            if self.file_list.getSelectedIndex() == 0:
                return None
        return self.fileIndexList[self.file_list.getSelectedIndex()]['uploadKey']

class ToolsInteractor(ServiceInteractor):
    def __init__(self, owner, name="ToolsInteractor"):
        ServiceInteractor.__init__(self,owner,name,TopLevelService())

        self.parser= JSONParser()
        
        info = "<p>A collection of tools for examining HERMES runs. </p>"

        self.treeButton = Button("Tree Explorer",self)
        self.hgButton = Button("HyperGraph Explorer",self)
        # for now we'll leave this button but we won't display it
        # this is currently deprecated in favor of the SVG version
        self.fireworksButton= Button("Fireworks Diagram",self)
        self.fwSVGButton = Button("Fireworks Diagram", self)
        
        panel = VerticalPanel(Spacing=10)
        leftColumn= VerticalPanel(Spacing=3)
        self.resources= [('Stores',ThingSelector(self,"Stores","Stores")),
                         ('Routes',ThingSelector(self,"Routes","Routes")),
                         ('Reports',ThingSelector(self,'Reports','Reports',True))
                        ]
        for name,resource in self.resources:
            leftColumn.add(resource)
        rightColumn= VerticalPanel(Spacing=10)
        columnPair= HorizontalPanel(Spacing=10)
        columnPair.add(leftColumn)
        columnPair.add(rightColumn)
        panel.add(HTML(info))
        panel.add(columnPair)
        rightColumn.add(self.treeButton)
        rightColumn.add(self.hgButton)
#        rightColumn.add(self.fireworksButton)
        rightColumn.add(self.fwSVGButton)
        self.add(panel)

    def lateBuild(self):
        pass

    def applyState(self,state):
        for name,resource in self.resources:
            if state.has_key(name):
                resource.setState(state[name])
        ServiceInteractor.applyState(self,state)
        
    def saveState(self):
        for name,resource in self.resources:
            self.state[name]= resource.getState()
        ServiceInteractor.saveState(self)

    def doActionCall(self, sender):
        if sender==self.hgButton:
            infoList= [(name,ts.getCurrentUploadKey()) for name,ts in self.resources]
            id= self.remoteService.getNetworkGraph(self.state['SessionKey'],infoList,self)
            info= ("hgButton",None)
            return id, info
        elif sender==self.treeButton:
            infoList= [(name,ts.getCurrentUploadKey()) for name,ts in self.resources]
            id= self.remoteService.getNetworkGraph(self.state['SessionKey'],infoList,self)
            info= ("treeButton",None)
            return id, info
        elif sender==self.fireworksButton:
            infoList= [(name,ts.getCurrentUploadKey()) for name,ts in self.resources]
            infoList.append(["GetVaxList","1"])
            id= self.remoteService.getNetworkDotGraph(self.state['SessionKey'],infoList,self)
            info= ("fireworksButton",None)
            return id, info
        elif sender==self.fwSVGButton:
            infoList= [(name,ts.getCurrentUploadKey()) for name,ts in self.resources]
            infoList.append(["Download", "svg"])
            infoList.append(["Size", "100%"])
            infoList.append(["GetVaxList", "1"])
            infoList.append(["GetStoresList", "1"])
            infoList.append(["GetCSVData", "1"])
            id= self.remoteService.getNetworkDotGraph(self.state['SessionKey'],infoList,self)
            info= ("fwSVGButton",None)
            return id, info
        
        else:
            return None,None

    def doActionResponse(self, callInfo, response, request_info):
        sender,method= callInfo
        if sender=="hgButton":
            jsonString= response
            self.owner.addView(HyperGraphPanel(self.owner,jsonString))
        elif sender=="treeButton":
            jsonString= response
            self.owner.addView(TreePanel(self.owner,jsonString))
        elif sender=="fireworksButton":
            response = self.parser.decode(response)
            info = response['InfoList']
            g = response['DotFile']
            vaxList = response['VaxList']
            self.owner.addView(FireworksPanel(self.owner,
                                              g,info=response['InfoList'],
                                              sk=self.state['SessionKey'],
                                              vaxList=response['InfoList']))
        elif sender=="fwSVGButton":
            response = self.parser.decode(response)
            self.owner.addView(FwSVGPanel(self.owner,
                                          sk=self.state['SessionKey'],
                                          data=response))

        return True
