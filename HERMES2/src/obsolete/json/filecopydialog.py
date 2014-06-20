_hermes_svn_id_="$Id$"

from pyjamas import DOM, Window
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui.TextBox import TextBox
from pyjamas.ui.ListBox import ListBox
from pyjamas.ui.Label import Label
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.JSONParser import JSONParser
from pyjamas.ui.SimplePanel import SimplePanel
from pyjamas.ui import HasAlignment
from pyjamas.ui.DialogBox import DialogBox
from pyjamas.ui.DockPanel import DockPanel
from pyjamas.ui.Frame import Frame

        
class FileCopyDialog(DialogBox):
    def __init__(self, captionHtmlString,labelString, idString, owner):
        DialogBox.__init__(self, glass=True)
        self.setText("Copy Server-Side File")

        self.idString= idString
        self.owner= owner
        self.fileInfoList= None
        innerPanel = VerticalPanel()
        p= HorizontalPanel()
        p.add(Label(labelString))
        self.fileList= ListBox()
        p.add(self.fileList)
        innerPanel.add(p)
        p= HorizontalPanel()
        p.add(Label('New Short Name'))
        self.newName= TextBox()
        p.add(self.newName)
        self.newName.setVisibleLength(20)
        self.newName.setMaxLength(60)
        innerPanel.add(p)
        
        self.cancelButton = Button("Cancel", self)
        self.okButton = Button("OK", self)
        msg = HTML(captionHtmlString, True)
        
        hPanel= HorizontalPanel()
        hPanel.add(self.cancelButton)
        hPanel.add(self.okButton)

        dock = DockPanel()
        dock.setSpacing(4)

        dock.add(hPanel, DockPanel.SOUTH)
        dock.add(msg, DockPanel.NORTH)
        dock.add(innerPanel, DockPanel.CENTER)

        dock.setCellHorizontalAlignment(hPanel, HasAlignment.ALIGN_RIGHT)
        dock.setCellWidth(innerPanel, "100%")
        dock.setWidth("100%")
        innerPanel.setWidth("36em")
        innerPanel.setHeight("6em")
        self.setWidget(dock)
        
    def setFileList(self,fileList,selectedIndex):
        self.fileInfoList= fileList
        self.fileList.clear()
        for r in fileList:
            self.fileList.addItem(r['shortName'])
        self.fileList.setSelectedIndex(selectedIndex)
        

    def onClick(self, sender):
        if sender==self.cancelButton:
            self.hide() # Form must stay up until upload completes or is aborted
        else:
            txt= self.newName.getText()
            match= False
            for i in xrange(self.fileList.getItemCount()):
                if txt==self.fileList.getItemText(i):
                    match= True
            if match:
                Window.alert('That short name is already in use')
            elif len(txt)==0:
                Window.alert('Please specify a short name for the new file')
            else:
                self.owner.onClick(sender)
                self.newName.setText("") 
            
    def show(self):
        str= self.newName.getText()
        if len(str)==0:
            selected= self.fileInfoList[self.fileList.getSelectedIndex()]
            self.newName.setText(selected['shortName']+'_copy')
        DialogBox.show(self)            

    def getState(self):
        return {'shortName':self.fileList.getSelectedItemText(), 'newName':self.newName.getText()}
    
    def setState(self, state):
        if state.has_key('shortName'):
            self.fileList.selectItem(state['shortName'])
        if state.has_key('newName'):
            self.newName.setText(state['newName'])



