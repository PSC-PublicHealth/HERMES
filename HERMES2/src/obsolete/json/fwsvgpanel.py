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
from pyjamas.ui.ScrollPanel import ScrollPanel
from toolpanel import ToolPanel
from filedownloader import FileDownloadSimplePanel
from serviceinteractor import ServiceInteractor
from pyjamas.JSONParser import JSONParser
import base64

class NavButton:
    def __init__(self, panel, storeId, text):
        self.panel = panel
        self.storeId = storeId
        self.button = Button(text, self)

    def getButton(self):
        return self.button

    def onClick(self, sender):
        self.panel.setDetails_Nav(self.storeId)

class DetailsButton:
    def __init__(self, panel, storeId, text):
        self.panel = panel
        self.storeId = storeId
        self.button = Button(text, self)

    def getButton(self):
        return self.button

    def onClick(self, sender):
        self.panel.setDetails_Details(self.storeId)

class RouteButton:
    def __init__(self, panel, RouteName, text):
        self.panel = panel
        self.RouteName = RouteName
        self.button = Button(text, self)

    def getButton(self):
        return self.button

    def onClick(self, sender):
        self.panel.setDetails_Route(self.RouteName)

def NotImp(sender):
    Window.alert("Not Implemented")

def fis2s(v):
    """
    float, int or string (typically 'NA') to string
    but with 0 decimal places if int, 2 places if float
    or copy string if string
    """
    if type(v) is type(5):
        return "%d"%v
    if type(v) is type(2.5):
        return "%8.2f"%v
    return str(v)


class FwSVGPanel(ToolPanel):
    FW_DISP_SIZE_X = 500
    FW_DISP_SIZE_Y = 500
    ZOOM_IN_MAG = 1.5
    ZOOM_OUT_MAG = 1 / ZOOM_IN_MAG

    def repositionSVG(self):
        svgWidth  = self.svgSize_x
        svgHeight = self.svgSize_y
        svgLeft = self.frameCenter_x - self.svgSize_x * self.svgCenterOffset_x
        svgTop  = self.frameCenter_y - self.svgSize_y * self.svgCenterOffset_y
        myiframe = self.iframeId
        JS("""
            var iframe = parent.document.getElementById(myiframe);
            var mysvg = iframe.contentDocument.getElementById("thissvg");
            mysvg.width  = Math.floor(svgWidth);
            mysvg.height = Math.floor(svgHeight);
            leftfl = Math.floor(svgLeft);
            mysvg.style.left = leftfl.toString() + "px";
            topfl = Math.floor(svgTop);
            mysvg.style.top  = topfl.toString() + "px";
        """)


    def zoomIn(self):
        self.svgSize_x *= FwSVGPanel.ZOOM_IN_MAG
        self.svgSize_y *= FwSVGPanel.ZOOM_IN_MAG
        self.repositionSVG()

    def zoomOut(self):
        self.svgSize_x *= FwSVGPanel.ZOOM_OUT_MAG
        self.svgSize_y *= FwSVGPanel.ZOOM_OUT_MAG
        self.repositionSVG()

    def zoomReset(self):
        self.svgSize_x = self.svgBaseSize_x
        self.svgSize_y = self.svgBaseSize_y
        self.svgCenterOffset_x = 0.5
        self.svgCenterOffset_y = 0.5
        self.repositionSVG()

    def onMouseDown(self, sender, x, y):
        self.drag= True
        self.dragStart= (x,y)

    def onMouseEnter(self, sender):
        if self.drag:
            self.drag = False

    def onMouseLeave(self, sender):
        if self.drag:
            self.drag= False

    def onMouseMove(self, sender, x, y):
        if self.drag:
            (sx,sy) = self.dragStart
            self.dragStart = (x,y)

            dx = (x - sx) / self.svgSize_x
            dy = (y - sy) / self.svgSize_y
            
            self.svgCenterOffset_x -= dx
            self.svgCenterOffset_y -= dy

            self.repositionSVG()
        #RootPanel().add(HTML("mousemove: %d,%d"%(x,y)))


    def onMouseUp(self, sender, x, y):
        if self.drag:
            (sx,sy) = self.dragStart

            dx = (x - sx) / self.svgSize_x
            dy = (y - sy) / self.svgSize_y
            
            self.svgCenterOffset_x -= dx
            self.svgCenterOffset_y -= dy

            self.drag = False
            self.repositionSVG()


    def redraw(self):
        myiframe = self.iframeId
        if (self.newDotString):
            self.newDotString = False
            url = "/bottle_hermes/simpleget/%s/%s"%(self.state['SessionKey'], self.fileId)
            JS("""
              iframe = parent.document.getElementById(myiframe);
              mysvg = iframe.contentDocument.getElementById("thissvg");
              mysvg.data = url;
            """)
            self.zoomReset()

    def onAttach(self):
        ToolPanel.onAttach(self)
        myId= self.getMyId()
        self.redraw()


    def buildControlPanel(self):
        self.controlPanel= HorizontalPanel(Spacing=10,Width="100%")

        labelPanel = VerticalPanel()
        labelPanel.add(Label("Graph Label"))
        self.labelTextBox = TextBox(VisibleLength=30)
        labelPanel.add(self.labelTextBox)
        self.controlPanel.add(labelPanel)

        layoutPanel = VerticalPanel()
        layoutPanel.add(Label("Graph Layout"))
        self.layoutTypeBox = ListBox()
        self.layoutTypeBox.setVisibleItemCount(0)
        # circo and dot seem to be the only ones that really work for us
        # but I'll leave the rest here too.
        for item in ("circo","dot","neato","fdp","sfdp","twopi"):
            self.layoutTypeBox.addItem(item)
        layoutPanel.add(self.layoutTypeBox)
        self.controlPanel.add(layoutPanel)
        
        coloringPanel = VerticalPanel()
        coloringPanel.add(Label("Graph Coloring"))
        self.vaxListBox = ListBox()
        self.vaxListBox.setVisibleItemCount(0)
        self.vaxListBox.addItem("Fill Ratio")
        # apparently we don't have an all vax supply ratio
        #self.vaxListBox.addItem("All Vaccine Supply Ratio")

        if len(self.vaxList):
            for vax in self.vaxList:
                self.vaxListBox.addItem(vax)

        # not sure if I should even display this listbox if we don't have a report file
        if len(self.vaxList):
            coloringPanel.add(self.vaxListBox)
        else:
            coloringPanel.add(Label("Disabled"))
            coloringPanel.add(Label("(No Report File)"))
        self.controlPanel.add(coloringPanel)

        rootNodePanel = VerticalPanel()
        rootNodePanel.add(Label("RootNode"))
        self.rootNodeListBox = ListBox()
        self.rootNodeListBox.setVisibleItemCount(0)
        self.rootNodeListBox.addItem("Default")
        for storePair in self.storesList:
            store = storePair[0]
            id = storePair[1]
            self.rootNodeListBox.addItem("%d: %s"%(id,store))
        rootNodePanel.add(self.rootNodeListBox)
        self.controlPanel.add(rootNodePanel)

        self.rebuildGraphButton = Button("Rebuild Graph", self)
        self.controlPanel.add(self.rebuildGraphButton)
        self.downloadButton= Button("Download", self)
        self.controlPanel.add(self.downloadButton)


    def buildGraphicsPanel(self):
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
        self.iframeId = "svgiframe%d"%myId
        iframesrc =  '<iframe id="svgiframe%d" '%myId
        iframesrc += 'src="/bottle_hermes/panelhelper/fw_iframes/%s/%s/%s" '%(self.state['SessionKey'],self.fileId,self.iframeId)
        iframesrc += 'height="%s" width="%s" scrolling="no" style="border-width: 0px" />'%(FwSVGPanel.FW_DISP_SIZE_Y, FwSVGPanel.FW_DISP_SIZE_X)
        self.svgiframe = HTML(iframesrc)
        leftPanel.add(self.svgiframe)
        
        return leftPanel

    def buildDetailsPanel(self):
        detailsPanel= VerticalPanel(Spacing=10,BorderWidth=1)
#        detailsPanel= ScrollPanel()
        detailsPanel.setSize('300px','500px')
        DOM.setStyleAttribute(detailsPanel.getElement(),"backgroundColor","lightgreen")        
#        self.innerDetailsDiv= HTML('<div id="inner-details%d">Details</div>'%self.getMyId())
#        self.innerDetailsDiv.setSize('300px','500px')
#        DOM.setStyleAttribute(self.innerDetailsDiv.getElement(),"backgroundColor","lightgreen")
#        rightPanel.add(self.innerDetailsDiv)
        return detailsPanel

    def buildLogPanel(self):
        logPanel= VerticalPanel(Spacing=10,BorderWidth=1)
        DOM.setStyleAttribute(logPanel.getElement(),"border","1px")
        self.logText= HTML('Log information follows<br>')
        self.logText.setID('log%d'%self.getMyId())
        logPanel.add(self.logText)
        logPanel.setHeight("100%")
        logPanel.setWidth("250px")
        return logPanel

    def prepSvgVars(self):
        # svg position stuff
        gh = self.globals['graphHeight']
        gw = self.globals['graphWidth']
        dh = FwSVGPanel.FW_DISP_SIZE_Y
        dw = FwSVGPanel.FW_DISP_SIZE_X

        if (gw / gh) > (dw / dh):
            self.svgSize_x = dw
            self.svgSize_y = dw * gh / gw
        else:
            self.svgSize_y = dh
            self.svgSize_x = dh * gw / gh

        self.svgBaseSize_x = self.svgSize_x
        self.svgBaseSize_y = self.svgSize_y

        self.frameCenter_x = FwSVGPanel.FW_DISP_SIZE_X / 2
        self.frameCenter_y = FwSVGPanel.FW_DISP_SIZE_Y / 2
        self.svgCenterOffset_x = 0.5
        self.svgCenterOffset_y = 0.5

                
    def __init__(self,owner,name=None, sk=None, data=None):
        
        #     fileId,name=None,info=None,sk=None,vaxList=None,storesList=None, 
        #         storesData=None, routesData=None):
        ToolPanel.__init__(self, owner, name)
        self.state= {'SessionKey':sk}
        if name is None:
            self.name= "Fireworks%d"%self.getMyId()

#        self.data = data
        self.info = data['InfoList']
        self.fileId = data['FileKey']
        self.vaxList = data['VaxList']
        self.storesList = sorted(data['StoresList'], key=lambda store: store[1])
        self.stores = data['StoresData']
        self.routes = data['RoutesData']
        self.rootStore = data['Globals']['rootStore']
        self.globals = data['Globals']
        self.peopleTypes = data['PeopleTypes']
        panel = VerticalPanel(Spacing=10,Width="100%")

        self.buildControlPanel()
        panel.add(self.controlPanel)

        self.downloadPanel= FileDownloadSimplePanel("FireworksDownloader")
        panel.add(self.downloadPanel)

        workPanel= HorizontalPanel(Spacing=10)
        #workPanel.setSize("100%","500px")


        workPanel.add(self.buildGraphicsPanel())
        self.detailsPanel = self.buildDetailsPanel()
        workPanel.add(self.detailsPanel)
        workPanel.add(self.buildLogPanel())
        self.svgiframe.addMouseListener(self)

        panel.add(workPanel)
        self.add(panel)
#        self.saveState()
        self.newDotString= False # for later, when there is a way to replace dotString
        self.drag= False # Is drag in progress?
        self.dragStart= None
#        self.applyState(owner.getChildState(self))

        self.prepSvgVars()
        self.setDetails_Nav(self.rootStore, center=False)



    def applyState(self,state):
        if state.has_key("fileId"):
            self.fileId= state["fileId"]
        ServiceInteractor.applyState(self,state)
        
    def saveState(self):
        self.state["fileId"]= self.fileId
        ServiceInteractor.saveState(self)

    def _gatherOptions(self):
        tempinfo = list(self.info)
        if len(self.labelTextBox.getText()):
            tempinfo.append(["B64Label", base64.b64encode(self.labelTextBox.getText())])
        layoutIndex = self.layoutTypeBox.getSelectedIndex()
        if layoutIndex > -1:
            tempinfo.append(["Layout",self.layoutTypeBox.getItemText(layoutIndex)])
        vaxIndex = self.vaxListBox.getSelectedIndex()
        if vaxIndex > 0: # do nothing for show fill ratio
            tempinfo.append(["Show", "supplyratio"])
            if vaxIndex > 0:  #don't specify anything for "all vaccines" which isn't an option anymore
                tempinfo.append(["Vax", self.vaxListBox.getItemText(vaxIndex)])
        rootIndex = self.rootNodeListBox.getSelectedIndex()
        if rootIndex > 0: # do nothing for default
            tempinfo.append(['RootNode', '%s'%self.storesList[rootIndex-1][1]])
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
            tempinfo.append(["Download","svg"])
            tempinfo.append(["Size","100%"])
            tempinfo.append(["GetCSVData", "1"])
            id = self.remoteService.getNetworkDotGraph(self.state['SessionKey'],tempinfo,self)
            info = ("rebuildGraphButton", None)
            return id, info
            
        else:
            return None,None
            

    def doActionResponse(self, callInfo, response, request_info):
        sender,method = callInfo
        if sender == "downloadButton":
            response = JSONParser().decode(response)
            downloadKey = response['FileKey']
            if self.downloadPanel.prepAndSubmit(downloadKey, 
                                                {'targetKey':downloadKey, 
                                                 'sessionKey':self.state['SessionKey']}):
                self.owner.setStatus('got download key <%s>; commencing download'%str(uploadKey))
                return True
            else:
                self.owner.setStatus('got download key <%s>; but download aborted'%str(uploadKey))
                return False

        elif sender == "rebuildGraphButton":
            response = JSONParser().decode(response)
            self.fileId = response['FileKey']
            self.stores = response['StoresData']
            self.routes = response['RoutesData']
            self.globals = response['Globals']
            self.newDotString = True
            self.owner.setStatus('got new SVG.  Redrawing?')
            self.redraw()
            self.prepSvgVars()
            self.setDetails_Nav(self.rootStore, center=False)
            return True

        return True



    def setDetails_Nav(self, storeId, center=True):
        store = self.stores[storeId]

        dp = self.detailsPanel # ignore the LOLs over the var name
        dp.clear()
        panel = HorizontalPanel(Spacing=10, Width="100%")
        panel.add(Label("Navigation Panel"))
        button = DetailsButton(self, storeId, "Details Panel")
        panel.add(button.getButton())
        dp.add(panel)

        vpanel = VerticalPanel(Spacing=10, Width="100%")
        vpanel.add(Label("%s: %s"%(storeId,store['NAME'])))
        vpanel.add(Label("%s"%store['FUNCTION']))
        dp.add(vpanel)
        
        if store['parent'] is not None:
            vpanel = VerticalPanel(Spacing=10, Width="100%")
            vpanel.add(Label("Supplier:"))
            hpanel = HorizontalPanel()
            label = "%s: %s"%(store['parent'], self.stores[store['parent']]['NAME'])
            button = NavButton(self, store['parent'], label)
            hpanel.add(button.getButton())
            button = DetailsButton(self, store['parent'], "Details")
            hpanel.add(button.getButton())
            vpanel.add(hpanel)
            if store['parentRoute']:
                vpanel.add(Label("Suplier Route:"))
                button = RouteButton(self, store['parentRoute'], store['parentRoute'])
                vpanel.add(button.getButton())
            dp.add(vpanel)

        if len(store['children']):
            vpanel = VerticalPanel(Spacing=10, Width="100%")
            vpanel.add(Label("Clients:"))
            for child in sorted(store['children'], key=int):
                hpanel = HorizontalPanel()
                label = "%s: %s"%(child, self.stores[child]['NAME'])
                button = NavButton(self, child, label)
                hpanel.add(button.getButton())
                button = DetailsButton(self, child, "Details")
                hpanel.add(button.getButton())
                vpanel.add(hpanel)
            dp.add(vpanel)

        if center:
            self.svgCenterOffset_x = store['graph_x']
            self.svgCenterOffset_y = store['graph_y']
#            Window.alert("x: %f, y: %f, width: %f, height: %f"%(store['graph_x'] * 100, store['graph_y'] * 100, store['disp_w']*100, store['disp_h']*100))
            dw = store['disp_w']
            dh = store['disp_h']
            gh = self.globals['graphHeight']
            gw = self.globals['graphWidth']
            if (dw / dh) > (gw / gh):
#                dh = dw * (gh / gw)
                sx = self.svgBaseSize_x / dw
                sy = self.svgBaseSize_y / dw
            else:
#                dw = dh * (gw / gh)
                sx = self.svgBaseSize_x / dh
                sy = self.svgBaseSize_y / dh
            
            self.svgSize_x = sx / 1.1
            self.svgSize_y = sy / 1.1
#            Window.alert("base ratio %f, new ratio %f"%(self.svgBaseSize_x / self.svgBaseSize_y, sx / sy))
            self.repositionSVG()


    def setDetails_Route(self, RouteName, center=True):
        route = self.routes[RouteName]

        dp = self.detailsPanel # ignore the LOLs over the var name
        dp.clear()

        panel = HorizontalPanel(Spacing=10, Width="100%")
        panel.add(Label("Route Panel"))
        dp.add(panel)

        panel = VerticalPanel(Spacing=10, Width="100%")
        panel.add(Label("Route: %s"%route['RouteName']))
        panel.add(Label("Type: %s"%route['Type']))
        panel.add(Label("TruckType: %s"%route['TruckType']))
        dp.add(panel)

        panel = VerticalPanel(Spacing=10, Width="100%")
        panel.add(Label("Stops:"))
        for stop in route['stops']:
            label = "%s: %s"%(stop[1], self.stores[stop[1]]['NAME'])
            button = NavButton(self, stop[1], label)
            panel.add(button.getButton())
        dp.add(panel)

        if route.has_key('report'):
            report = route['report']
            panel = VerticalPanel(Spacing=10, Width="100%")
            panel.add(Label("Report Data:"))
            panel.add(Label("Fill: %s"%report['RouteFill']))
            panel.add(Label("Trips: %f"%report['RouteTrips']))
            dp.add(panel)




    def setDetails_Details(self, storeId, center=True):
        store = self.stores[storeId]

        dp = self.detailsPanel # ignore the LOLs over the var name
        dp.clear()
        panel = HorizontalPanel(Spacing=10, Width="100%")
        button = NavButton(self, storeId, "Navigation Panel")
        panel.add(button.getButton())
        panel.add(Label("Details Panel"))
        dp.add(panel)

        vpanel = VerticalPanel(Spacing=10, Width="100%")
        vpanel.add(Label("%s: %s"%(storeId,store['NAME'])))
        vpanel.add(Label("%s"%store['FUNCTION']))
        if (store['Walk in -(lit)'] > 0):
            vpanel.add(Label("Walk in freezer: %sl"%fis2s(store['Walk in -(lit)'])))
        if (store['Walk in +(lit)'] > 0):
            vpanel.add(Label("Walk in refrigerator: %sl"%fis2s(store['Walk in +(lit)'])))
        if (store['VOL - (lit)'] > 0):
            vpanel.add(Label("Freezer: %sl"%fis2s(store['VOL - (lit)'])))
        if (store['VOL + (lit)'] > 0):
            vpanel.add(Label("Refrigerator: %sl"%fis2s(store['VOL + (lit)'])))
        dp.add(vpanel)

        vpanel = VerticalPanel(Spacing=10, Width="100%")
        vpanel.add(Label("Population:"))
        for pt in self.peopleTypes:
            if store.has_key(pt):
                vpanel.add(Label("%s: %s"%(pt, fis2s(store[pt]))))
        dp.add(vpanel)

        if store.has_key('report'):
            report = store['report']
            panel = VerticalPanel(Spacing=10, Width="100%")
            panel.add(Label("Vaccine Usage Stats:"))

            for vax in self.vaxList:
                showme = False
                patients = treated = vials = outages = 'NA'
                if report.has_key('%s_patients'%vax):
                    patients = report['%s_patients'%vax]
                if report.has_key('%s_treated'%vax):
                    treated = report['%s_treated'%vax]
                if report.has_key('%s_vials'%vax):
                    vials = report['%s_vials'%vax]
                if report.has_key('%s_outages'%vax):
                    outages = report['%s_outages'%vax]
                percent = 'NA'
                if patients != 'NA' and patients > 0 and treated != 'NA' and treated >= 0:
                    percent = treated / patients * 100
                    showme = True
                patients = fis2s(patients)
                treated = fis2s(treated)
                vials = fis2s(vials)
                outages = fis2s(outages)
                percent = fis2s(percent)
                if showme:
                    subPanel = VerticalPanel(Width="100%")
                    subPanel.add(Label("%s"%vax))
                    subPanel.add(Label("patients: %s, treated: %s (%s%%)"%(patients, treated, percent)))
                    subPanel.add(Label("vials: %s, outages: %s"%(vials, outages)))
                    panel.add(subPanel)
            dp.add(panel)

        


