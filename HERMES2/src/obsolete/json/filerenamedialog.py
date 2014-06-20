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
from filecopydialog import FileCopyDialog

        
class FileRenameDialog(FileCopyDialog):
    def __init__(self, captionHtmlString,labelString, idString, owner):
        FileCopyDialog.__init__(self, captionHtmlString, labelString, idString, owner)
        self.setText("Rename a Server-Side File")
                    
    def show(self):
        str= self.newName.getText()
        if len(str)==0:
            selected= self.fileInfoList[self.fileList.getSelectedIndex()]
            self.newName.setText(selected['shortName'])
        DialogBox.show(self)            



