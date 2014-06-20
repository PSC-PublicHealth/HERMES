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
from pyjamas.ui.TextBox import TextBox
from toolpanel import ToolPanel
from canviz import Canviz
from filedownloader import FileDownloadSimplePanel
from serviceinteractor import ServiceInteractor
from pyjamas.JSONParser import JSONParser
#from hermes_ui import HermesUI

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

class FireworksPanel(ToolPanel):
    def setOffsetBase(self,top,left):
        "Caller is providing the browser coordinates of the top left corner"
        tCanvas,lCanvas= getTotalOffsetsUpTo(self.infoVisDiv.getElement(),self.getElement().offsetParent)
        h= DOM.getOffsetHeight(self.controlPanel.getElement())
        #Window.alert('fireworkstool.setOffsetBase: top= %s, tCanvas= %s, h= %s'%(top,tCanvas,h))
        if self.canviz is not None:
            self.canviz.setOffsetBase(tCanvas+top,lCanvas+left)
            self.redraw()
            
    def zoomIn(self):
        if self.canviz is not None:
            self.canviz.centeredScale(1.3)
            self.redraw()
    def zoomOut(self):
        if self.canviz is not None:
            self.canviz.centeredScale(1.0/1.3)
            self.redraw()
    def zoomReset(self):
        if self.canviz is not None:
            self.canviz.restoreCtx() # Restore to state saved after first draw
            self.canviz.saveCtx() # And save a new copy
            self.canviz.recenter() # The context doesn't know about our center shifts
            self.redraw()
    def download(self):
        Window.alert('internal error! download shouldn\'t be wired here')
    def redraw(self):
        if self.canviz is not None:
            if self.newDotString:
                self.canviz.parse(self.dotString)
                self.newDotString= False
                self.canviz.saveCtx() # So we can restore to initial state
            else:
                self.canviz.draw()    

    def rebuildGraph(self):
        Window.alert("not implemented yet!")

    def onAttach(self):
        ToolPanel.onAttach(self)
        myId= self.getMyId()
        self.canviz= Canviz(self.infoVisDiv,None,500,500,'log%d'%myId)
        self.redraw()
                
    def __init__(self,owner,dotString,name=None,info=None,sk=None,vaxList=None):
        ToolPanel.__init__(self, owner, name)
        self.state= {'SessionKey':sk}
        if name is None:
            self.name= "Fireworks%d"%self.getMyId()
        self.info = info
#        self.owner= owner
        self.dotString= dotString
        self.vaxList = vaxList
        panel = VerticalPanel(Spacing=10,Width="100%")

        self.controlPanel= HorizontalPanel(Spacing=10,Width="100%")
        self.optionsTextBox = TextBox(VisibleLength=30)
        self.controlPanel.add(self.optionsTextBox)
        self.layoutTypeBox = ListBox()
        self.layoutTypeBox.setVisibleItemCount(0)
        # sfdp doesn't seem to exist as a layout
        # twopi creates something that fails the layout engine
        for item in ("circo","dot","neato","fdp"):
            self.layoutTypeBox.addItem(item)
        self.controlPanel.add(self.layoutTypeBox)
        
        self.vaxListBox = ListBox()
        self.vaxListBox.setVisibleItemCount(0)
        self.vaxListBox.addItem("All Vaccines")
        if len(self.vaxList):
            for vax in self.vaxList:
                self.vaxListBox.addItem(vax)
        self.controlPanel.add(self.vaxListBox)
        
        self.rebuildGraphButton = Button("Rebuild Graph", self)
        self.controlPanel.add(self.rebuildGraphButton)
        self.downloadButton= Button("Download", self)
        self.controlPanel.add(self.downloadButton)
        panel.add(self.controlPanel)

        self.downloadPanel= FileDownloadSimplePanel("FireworksDownloader")
        panel.add(self.downloadPanel)

        workPanel= HorizontalPanel(Spacing=10)
        #workPanel.setSize("100%","500px")
        leftPanel= VerticalPanel(Spacing=10,BorderWidth=1)

        self.miniControlPanel= HorizontalPanel(Spacing=10,Width="100%")
        self.miniControlPanel.add(Button("Zoom In", getattr(self,"zoomIn")))
        self.miniControlPanel.add(Button("Zoom Out", getattr(self,"zoomOut")))
        self.miniControlPanel.add(Button("Zoom Reset", getattr(self,"zoomReset")))
        leftPanel.add(self.miniControlPanel)

        #leftPanel.setHeight('100%')
        #leftPanel.setWidth('70%')
        #DOM.setStyleAttribute(leftPanel.getElement(),"backgroundColor","lightblue")
        myId= self.getMyId()
        # does this next line actually do anything?  I need to test removing it at some point.
        # or at least the specific line of html seems to do nothing.
        self.infoVisDiv= HTML('<div id="infovis%d" style="width:500px,height:500px"></div>'%myId)
        self.infoVisDiv.setSize("500px","500px")
        DOM.setStyleAttribute(self.infoVisDiv.getElement(),"backgroundColor","lightgreen")
        leftPanel.add(self.infoVisDiv)
        workPanel.add(leftPanel)
        self.infoVisDiv.addMouseListener(self)
        rightPanel= VerticalPanel(Spacing=10,BorderWidth=1)
        rightPanel.setHeight("100%")
        #rightPanel.setWidth("20%")
        #DOM.setStyleAttribute(rightPanel.getElement(),"backgroundColor","lightblue")
        self.innerDetailsDiv= HTML('<div id="inner-details%d">Details</div>'%myId)
        self.innerDetailsDiv.setSize('300px','500px')
        #self.innerDetailsDiv.setHeight('500px')
        DOM.setStyleAttribute(self.innerDetailsDiv.getElement(),"backgroundColor","lightgreen")
        rightPanel.add(self.innerDetailsDiv)
        workPanel.add(rightPanel)
        logPanel= VerticalPanel(Spacing=10,BorderWidth=1)
        #DOM.setStyleAttribute(logPanel.getElement(),"backgroundColor","pink")
        DOM.setStyleAttribute(logPanel.getElement(),"border","1px")
        self.logText= HTML('Log information follows<br>')
        self.logText.setID('log%d'%myId)
        logPanel.add(self.logText)
        workPanel.add(logPanel)
        logPanel.setHeight("100%")
        logPanel.setWidth("250px")
        panel.add(workPanel)
        self.canviz= None
        self.add(panel)
#        self.saveState()
        self.newDotString= True # for later, when there is a way to replace dotString
        self.drag= False # Is drag in progress?
        self.dragStart= None
#        self.applyState(owner.getChildState(self))


    def onMouseDown(self, sender, x, y):
        self.drag= True
        self.dragStart= (x,y)

    def onMouseEnter(self, sender):
        pass
        #RootPanel().add(HTML("mouseenter"))      

    def onMouseLeave(self, sender):
        if self.drag:
            self.drag= False

    def onMouseMove(self, sender, x, y):
        pass

    def onMouseUp(self, sender, x, y):
        if self.drag:
            sX,sY= self.dragStart
            sbX,sbY= self.canviz.ctx.getBackProjectedCoords(sX,sY)
            ebX,ebY= self.canviz.ctx.getBackProjectedCoords(x,y)
            #Window.alert('drag %s %s -> %s %s'%(sbX,sbY,ebX,ebY))
            self.drag= False
            self.canviz.centeredTranslate(ebX-sbX,ebY-sbY)
            self.redraw()

    def applyState(self,state):
        if state.has_key("dotString"):
            self.dotString= state["dotString"]
        ServiceInteractor.applyState(self,state)
        
    def saveState(self):
        self.state["dotString"]= self.dotString
        ServiceInteractor.saveState(self)

    def _gatherOptions(self):
        tempinfo = list(self.info)
        tempinfo.append(["Options",self.optionsTextBox.getText()])
        layoutIndex = self.layoutTypeBox.getSelectedIndex()
        if layoutIndex > -1:
            tempinfo.append(["Layout",self.layoutTypeBox.getItemText(layoutIndex)])
        vaxIndex = self.vaxListBox.getSelectedIndex()
        if vaxIndex > 0: # do nothing for "all vaccines"
            tempinfo.append(["Vax",self.vaxListBox.getItemText(vaxIndex)])
        return tempinfo

    def doActionCall(self, sender):
        if sender == self.downloadButton:
            if info == None:
                return None,None
            tempinfo = self._gatherOptions()
            tempinfo.append(["Download","svg"])
            id = self.remoteService.getNetworkDotGraph(self.state['SessionKey'],tempinfo,self)
            info = ("downloadButton", None)
            return id, info

        elif sender == self.rebuildGraphButton:
            if info == None:
                return None,None
            tempinfo = self._gatherOptions()
            id = self.remoteService.getNetworkDotGraph(self.state['SessionKey'],tempinfo,self)
            info = ("rebuildGraphButton", None)
            return id, info
            
        else:
            return None,None
            

    def doActionResponse(self, callInfo, response, request_info):
        sender,method = callInfo
        if sender == "downloadButton":
            (blah, downloadKey) = JSONParser().decode(response)
            if self.downloadPanel.prepAndSubmit(downloadKey, 
                                                {'targetKey':downloadKey, 
                                                 'sessionKey':self.state['SessionKey']}):
                self.owner.setStatus('got download key <%s>; commencing download'%str(uploadKey))
                return True
            else:
                self.owner.setStatus('got download key <%s>; but download aborted'%str(uploadKey))
                return False

        elif sender == "rebuildGraphButton":
            (info, self.dotString) = JSONParser().decode(response)
            self.newDotString = True
            self.owner.setStatus('got new DotString.  Redrawing.')
            self.redraw()
            return True

        return True
