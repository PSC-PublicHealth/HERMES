_hermes_svn_id_="$Id$"

import pyjd # dummy in pyjs

from pyjamas import DOM, Window
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui.TextBox import TextBox
from pyjamas.ui.Label import Label
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.JSONParser import JSONParser
from pyjamas.ui.SimplePanel import SimplePanel
from pyjamas.ui.FormPanel import FormPanel
from pyjamas.ui.FileUpload import FileUpload
from pyjamas.ui.Hidden import Hidden
from pyjamas.ui import HasAlignment
from pyjamas.ui.DialogBox import DialogBox
from pyjamas.ui.DockPanel import DockPanel
from pyjamas.ui.Frame import Frame

class FileUploadSimplePanel(SimplePanel):
    def __init__(self,labelString,idString,owner,handler=None):
        SimplePanel.__init__(self)

        self.idString= idString
        self.owner= owner
        self.parser= JSONParser()
        self.form = FormPanel()
        self.form.setEncoding(FormPanel.ENCODING_MULTIPART)
        self.form.setMethod(FormPanel.METHOD_POST)
        self.form.setAction("dummy")
        self.setID(idString)

        vPanel = VerticalPanel()

        hPanel1 = HorizontalPanel()
        hPanel1.setSpacing(5)
        hPanel1.add(Label(labelString))
        vPanel.add(hPanel1)

        self.field = FileUpload()
        self.field.setName("file")
        hPanel1.add(self.field)
        
        hPanel2 = HorizontalPanel()
        hPanel2.setSpacing(5)
        
        hPanel2.add(Label('Short Name:'))
        self.shortName= TextBox()
        self.shortName.setVisibleLength(20)
        self.shortName.setMaxLength(60)
        hPanel2.add(self.shortName)
        vPanel.add(hPanel2)
        self.metadata= Hidden(name="metadata")
        vPanel.add(self.metadata)

        self.form.add(vPanel)
        self.add(self.form)
        if handler is None:
            self.form.addFormHandler(self)
        else:
            self.form.addFormHandler(handler)
        
    def fixShortName(self):
        shortNameTxt= self.shortName.getText()
        shortNameTxt= shortNameTxt.trim()
        if len(shortNameTxt)==0:
            shortNameTxt= self.field.getFilename()
            extLoc= shortNameTxt.rfind('.')
            slashLoc= max(shortNameTxt.rfind('/'),shortNameTxt.rfind('\\'))
            if extLoc>slashLoc:
                shortNameTxt= shortNameTxt[:extLoc]
            if slashLoc>0:
                shortNameTxt= shortNameTxt[slashLoc:]
            self.shortName.setText(shortNameTxt)

    def prepAndSubmit(self, uploadKey, metadataDict):
        if len(self.field.getFilename())>0:
            metadataDict['uploadKey']= uploadKey
            metadataDict['uploaderIDString']= self.idString
            self.fixShortName()
            metadataDict['shortName']= self.shortName.getText()
            self.metadata.setValue(self.parser.encode(metadataDict))
            self.form.setAction('/bottle_hermes/upload/%s'%uploadKey)
            self.form.submit()
            return True
        else:
            Window.alert('No file is selected for upload.')
            return False

        
    def onSubmit(self, event):
        # This event is fired just before the form is submitted. We can take
        # this opportunity to perform validation.
        #if (self.tb.getText().length == 0):
        #    Window.alert("The text box must not be empty")
        #    event.setCancelled(True)
        #self.owner.alert('The onSubmit method is happening')
        pass

    def onSubmitComplete(self,event):
        # When the form submission is successfully completed, this event is
        # fired. Assuming the service returned a response of type text/plain,
        # we can get the result text here (see the FormPanel documentation for
        # further explanation).
        resultStr= event.getResults()
        self.owner.onUploadComplete(self.idString,self.parser.decode(resultStr))

    def getState(self):
        return {'shortName':self.shortName.getText(), 'filename':self.field.getFilename()}
    
    def setState(self, state):
        if state.has_key('shortName'):
            self.shortName.setText(state['shortName'])
        # Apparently security restrictions prevent our filling in the filename blank.
        #if state.has_key('filename'):
        #    self.field.setFilename(state['filename'])

class FileUploadWidget(SimplePanel):
    def __init__(self,labelString,idString,owner):
        SimplePanel.__init__(self)

        self.innerWidget= FileUploadSimplePanel(labelString,idString,owner)
        self.owner= owner
        self.idString= idString

        vPanel = VerticalPanel()
        vPanel.add(self.innerWidget)
        self.button= Button("Upload",self.owner)
        vPanel.add(self.button)
        self.add(vPanel)
        
    def prepAndSubmit(self, uploadKey, metadataDict):
        return self.innerWidget.prepAndSubmit(uploadKey,metadataDict)
        
    def getState(self):
        return self.innerWidget.getState()
    
    def setState(self, state):
        self.innerWidget.setState(state)
        
class FileUploadDialog(DialogBox):
    def __init__(self, captionHtmlString,labelString, idString, owner):
        DialogBox.__init__(self, glass=True)
        self.setText("File Upload")

        self.idString= idString
        self.owner= owner
        self.innerWidget = FileUploadSimplePanel(labelString, idString, owner, handler=self)
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
        dock.add(self.innerWidget, DockPanel.CENTER)

        dock.setCellHorizontalAlignment(hPanel, HasAlignment.ALIGN_RIGHT)
        dock.setCellWidth(self.innerWidget, "100%")
        dock.setWidth("100%")
        self.innerWidget.setWidth("36em")
        self.innerWidget.setHeight("6em")
        self.setWidget(dock)

    def onClick(self, sender):
        if sender==self.cancelButton:
            self.hide() # Form must stay up until upload completes or is aborted
        else:
            self.owner.onClick(sender)

    def getState(self):
        return self.innerWidget.getState()
    
    def setState(self, state):
        self.innerWidget.setState(state)

    def onSubmit(self, event):
        # This event is fired just before the form is submitted. We can take
        # this opportunity to perform validation.
        #if (self.tb.getText().length == 0):
        #    Window.alert("The text box must not be empty")
        #    event.setCancelled(True)
        #self.owner.alert('The onSubmit method is happening')
        pass

    def onSubmitComplete(self,event):
        # When the form submission is successfully completed, this event is
        # fired. Assuming the service returned a response of type text/plain,
        # we can get the result text here (see the FormPanel documentation for
        # further explanation).
        resultStr= event.getResults()
        if resultStr:
            self.owner.onUploadComplete(self.idString,self.innerWidget.parser.decode(resultStr))
            self.hide()

