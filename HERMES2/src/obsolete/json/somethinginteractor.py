##################################
# Notes-
#
##################################

_hermes_svn_id_="$Id$"

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
from pyjamas.ui.PopupPanel import PopupPanel
from serviceinteractor import ServiceInteractor
from fileuploader import FileUploadDialog
from filedownloader import FileDownloadSimplePanel
from filecopydialog import FileCopyDialog
from filerenamedialog import FileRenameDialog
from hermesservices import TopLevelService

class SomethingInteractor(ServiceInteractor):
    def __init__(self, owner, thingName= "Something", name="somethingInteractor"):
        ServiceInteractor.__init__(self,owner,name,TopLevelService())
        
        self.thingName= thingName
        self.parser= JSONParser()

        info = """
        <p>Manage Server-Side %s Files
           </p>"""%thingName

        self.file_list = ListBox()
        self.file_list.setVisibleItemCount(1)
        self.fileIndexList= []
        self.file_list.addChangeListener(self.onClick)
    
        list_panel = VerticalPanel()
        list_panel.add(HTML("Available %s files: "%self.thingName))
        list_panel.add(self.file_list)
        list_panel.setSpacing(10)
        
        self.downloadPanel= FileDownloadSimplePanel("%sDownloader"%self.thingName)

        buttons= VerticalPanel()
        
        self.dialogs= []
        self.uploadDialog= FileUploadDialog("<center>Add %s files to the server-side<br>list for this session</center>"%self.thingName,
                                            "%s File to Upload"%self.thingName,
                                            "%sUploader"%self.thingName,self)
        self.dialogs.append(('uploader',self.uploadDialog))
        self.uploadButton= Button('Upload Another?',self)
        self.copyDialog= FileCopyDialog("<center>Copy a Server-Side %s File</center>"%self.thingName,
                                            "%s File to Copy"%self.thingName,
                                            "%sCopier"%self.thingName,self)
        self.dialogs.append(('copier',self.copyDialog))
        self.copyButton= Button('Copy',self)
        self.renameDialog= FileRenameDialog("<center>Rename a Server-Side %s File</center>"%self.thingName,
                                            "%s File to Rename"%self.thingName,"%sRenamer"%self.thingName,self)
        self.dialogs.append(('renamer',self.renameDialog))
        self.renameButton= Button('Rename',self)
        self.infoButton= Button('Info',self)
        self.downloadButton= Button('Download',self)
        self.editButton= Button('View/Edit',getattr(self,"showNotImplementedPopup"))
        for b in [self.uploadButton,self.copyButton,self.renameButton,self.infoButton,self.downloadButton,
                  self.editButton]:
            buttons.add(b)
        
        panel = HorizontalPanel(Spacing=8)
        panel.add(list_panel)
        panel.add(buttons)
        panel.add(self.downloadPanel)
        outerPanel= VerticalPanel(Spacing=10)
        outerPanel.add(HTML(info))
        outerPanel.add(panel)
        self.add(outerPanel)
            
        self.popup= None
        
        self.owner.subscribeToResource(self.thingName,getattr(self,"handleResourceUpdate"))
        
    def showNotImplementedPopup(self,event):
        contents = HTML("Sorry; not yet implemented.")
        contents.addClickListener(getattr(self,"closePopup"))

        self._popup = PopupPanel(autoHide=True)
        self._popup.add(contents)
        self._popup.setStyleName("gwt-DialogBox")

        left = self.editButton.getAbsoluteLeft() + 10
        top  = self.editButton.getAbsoluteTop() + 10
        self._popup.setPopupPosition(left, top)
        self._popup.show()

    def closePopup(self,event):
        self._popup.hide()
        
    def handleResourceUpdate(self,name,infoList):
        #Window.alert('%s handleResourceUpdate %s got %s'%(self.thingName,name,str(infoList)))
        self.file_list.clear()
        self.fileIndexList= []
        for r in infoList:
            self.file_list.addItem(r['shortName'])
            self.fileIndexList.append(r)
        self.file_list.setSelectedIndex(0)
        
    def lateBuild(self):
        self.onClick('update_list') # Trick base class into updating the drop-down list

    def applyState(self,state):
        for name,thing in self.dialogs:
            if state.has_key(name):
                thing.setState(state[name])
        if state.has_key('fileList'):
            self.owner.updateResource(self.thingName,state['fileList'])
        if state.has_key('FileIndex'):
            self.file_list.setSelectedIndex(state['FileIndex'])
        ServiceInteractor.applyState(self,state)
        
    def saveState(self):
        for name,thing in self.dialogs:
            self.state[name]= thing.getState()
        self.state['FileIndex']= self.file_list.getSelectedIndex()
        self.state['fileList']= self.fileIndexList
        ServiceInteractor.saveState(self)

    def doActionCall(self, sender):
        if sender == self.uploadDialog.okButton:
            id= self.remoteService.getUploadHandle(self.state['SessionKey'],self)
            return id, ('button_upload',self.uploadDialog.idString)
        elif sender == self.uploadButton:
            left = self.uploadButton.getAbsoluteLeft() + 10
            top = self.uploadButton.getAbsoluteTop() + 10
            self.uploadDialog.setPopupPosition(left, top)
            self.uploadDialog.show()
            self.owner.setStatus('%s upload dialog up'%self.thingName)
            return 0,None
        elif sender == self.copyDialog.okButton:
            fromInfo= self.copyDialog.fileInfoList[self.copyDialog.fileList.getSelectedIndex()]
            id= self.remoteService.copyServerSideFile(self.state['SessionKey'],
                                                      fromInfo['uploadKey'],
                                                      self.copyDialog.newName.getText(),
                                                      self)
            self.copyDialog.hide()
            return id, ('button_copy',self.copyDialog.idString)
        elif sender==self.copyButton:
            left = self.copyButton.getAbsoluteLeft() + 10
            top = self.copyButton.getAbsoluteTop() + 10
            self.copyDialog.setPopupPosition(left, top)
            self.copyDialog.setFileList(self.fileIndexList,self.file_list.getSelectedIndex())
            self.copyDialog.show()
            self.owner.setStatus('%s copy dialog up'%self.thingName)
            return 0,None
        elif sender == self.renameDialog.okButton:
            fromInfo= self.renameDialog.fileInfoList[self.renameDialog.fileList.getSelectedIndex()]
            if fromInfo.has_key('noWrite') and fromInfo['noWrite']:
                Window.alert('That file cannot be renamed; make a copy of it instead.')
                return 0,None
            else:
                id= self.remoteService.renameServerSideFile(self.state['SessionKey'],
                                                            fromInfo['uploadKey'],
                                                            self.renameDialog.newName.getText(),
                                                            self)
                self.renameDialog.hide()
            return id, ('button_rename',fromInfo['shortName'])
        elif sender==self.renameButton:
            left = self.renameButton.getAbsoluteLeft() + 10
            top = self.renameButton.getAbsoluteTop() + 10
            self.renameDialog.setPopupPosition(left, top)
            self.renameDialog.setFileList(self.fileIndexList,self.file_list.getSelectedIndex())
            self.renameDialog.show()
            self.owner.setStatus('%s rename dialog up'%self.thingName)
            return 0,None
        elif sender==self.infoButton:
            info= self.fileIndexList[self.file_list.getSelectedIndex()]
            id= self.remoteService.getFileInfo(self.state['SessionKey'],info['uploadKey'],self)
            return id,('info',info)
        elif sender==self.downloadButton:
            info= self.fileIndexList[self.file_list.getSelectedIndex()]
            id= self.remoteService.getDownloadHandle(self.state['SessionKey'],self)
            return id, ('button_download',info)
        elif sender=='update_list':
            id= self.remoteService.getFilesOfType(self.state['SessionKey'],self.thingName,self)
            return id, ('update_list',None)
        elif sender==self.file_list:
            self.state['FileIndex']= self.file_list.getSelectedIndex()
            for name,dlg in self.dialogs:
                if hasattr(dlg,'setFileList'):
                    dlg.setFileList(self.fileIndexList,self.file_list.getSelectedIndex())
            self.saveState()
            return 0,None
        else:
            return None,None

    def closePopup(self,event):
        self._popup.hide()
        
    def doActionResponse(self, callInfo, response,request_info):
        sender,method= callInfo
        if sender=='button_upload':
            uploadKey= response
            uploaderIDString= method
            if self.uploadDialog.innerWidget.prepAndSubmit(uploadKey, {'sessionKey':self.state['SessionKey'],
                                                                       'type':self.thingName}):
                self.inFlight[uploadKey]= (uploadKey,None)
                self.owner.setStatus('got upload key <%s>; commencing upload'%str(uploadKey))
                return True
            else:
                self.owner.setStatus('got upload key <%s>; but upload aborted'%str(uploadKey))
                return False
        if sender=='button_download':
            downloadKey= response
            clientInfoDict= method
            if self.downloadPanel.prepAndSubmit(downloadKey, {'targetKey':clientInfoDict['uploadKey'],
                                                              'sessionKey':self.state['SessionKey']}):
                self.owner.setStatus('got download key <%s>; commencing download'%str(uploadKey))
                return True
            else:
                self.owner.setStatus('got download key <%s>; but download aborted'%str(uploadKey))
                return False
        elif sender=='button_copy':
            newFileInfo= response
            newIndex= self.file_list.getItemCount()
            self.fileIndexList.append(newFileInfo)
            self.owner.updateResource(self.thingName,self.fileIndexList)
            self.file_list.setSelectedIndex(newIndex)
            return True
        elif sender=='button_rename':
            newFileInfo= response
            oldShortName= method
            self.file_list.selectItem(oldShortName)
            index= self.file_list.getSelectedIndex()
            self.fileIndexList[index]['shortName']= newFileInfo['shortName']
            self.owner.updateResource(self.thingName,self.fileIndexList)
            self.file_list.setSelectedIndex(index)
            return True
        elif sender=='update_list':
            resultList= self.parser.decode(response)
            self.owner.updateResource(self.thingName,resultList)
            return True
        elif sender=='info':
            infoDict= response
            clientInfoDict= method
            cStr= "Short Name: %s<br>"%infoDict['shortName']
            cStr += "Type: %s<br>"%infoDict['type']
            if infoDict.has_key('Note'):
                cStr += "Note: %s<br>"%infoDict['Note']
            if clientInfoDict.has_key('noWrite'):
                if clientInfoDict['noWrite']:
                    cStr += "Editable: False<br>"
                else:
                    cStr += "Editable: True<br>"
            else:
                cStr += "Writable status is missing"
            contents = HTML(cStr)
            contents.addClickListener(getattr(self,"closePopup"))
    
            self._popup = PopupPanel(autoHide=True)
            self._popup.add(contents)
            self._popup.setStyleName("gwt-DialogBox")
    
            left = self.infoButton.getAbsoluteLeft() + 10
            top  = self.infoButton.getAbsoluteTop() + 10
            self._popup.setPopupPosition(left, top)
            self._popup.show()
            return True
        else:
            return False

    def onUploadComplete(self, uploaderIDString, metadata):
        uploadKey= metadata['uploadKey']
        if not self.inFlight.has_key(uploadKey):
            Window.alert('Internal error; <%s> is not in %s'%(uploadKey,self.inFlight.keys()))
            self.owner.setStatus('upload of %s via uploader %s failed.'%(metadata['shortName'],
                                                                        uploaderIDString))
            # No state update
        else:
            del self.inFlight[uploadKey]
            if metadata['code']!=0:
                Window.alert('Upload failed: %s'%metadata['message'])
                self.owner.setStatus('upload of %s via uploader %s failed.'%(metadata['shortName'],
                                                                             uploaderIDString))
            else:
                self.owner.setStatus('upload of %s via uploader %s is complete.'%(metadata['shortName'],
                                                                                  uploaderIDString))
                newIndex= self.file_list.getItemCount()
                self.fileIndexList.append(metadata)
                self.owner.updateResource(self.thingName,self.fileIndexList)
                self.file_list.setSelectedIndex(newIndex)
                self.saveState()
