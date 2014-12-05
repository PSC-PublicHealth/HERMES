#!/usr/bin/env python 

########################################################################
# Copyright C 2010, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

__doc__=""" htmlHelper.py
This module holds helper functions for creating HTML elements
"""

_hermes_svn_id_="$Id: util.py 1425 2013-08-30 19:55:57Z stbrown $"
import types

class HTMLPrimitive:
    _allowedStyleElements = ['width','height','visibility',
                             'display','table-layout','border',
                             'background','color','fontweight','fontsize']
    def __init__(self,name_,**kwargs):
        self.name = name_
        self.classString = ''
        self.styleString = ''
        self.styles = kwargs
        for arg,value in kwargs.items():
            if self.styleString == '':
                self.styleString = ' style="'
            if arg == 'cssclass':
                self.classString = ' class = "%s" '%value
            if arg in self._allowedStyleElements:
                if arg == 'fontsize':
                    self.styleString += 'font-size:%s;'%value
                elif arg == 'fontweight':
                    self.styleString += 'font-weight:%s;'%value
                else:
                    self.styleString += '%s:%s;'%(arg,value)
        if self.styleString != '':
            self.styleString += '" '
            
class HTMLElement(HTMLPrimitive):
    def __init__(self,name_,pretty_=True,**kwargs):
        HTMLPrimitive.__init__(self,name_,**kwargs)
        self.name = name_
        self.pretty = pretty_
        
    def htmlString(self):
        return None

class HTMLConstruct(HTMLPrimitive):
    def __init__(self,name_,pretty_=False,**kwargs):
        HTMLPrimitive.__init__(self,name_,**kwargs)
        self.pretty = pretty_
        self.headerStringList = []
        self.footerStringList = []
        
    def _addHeader(self,text_):
        self.headerStringList.append(text_)
    
    def _addFooter(self,text_):
        self.footerStringList.append(text_)
        
    def htmlString(self):
        htmlStringList = []
        [htmlStringList.append(x) for x in self.headerStringList]
        htmlStringList.append(self.htmlStringLocal())
        [htmlStringList.append(x) for x in self.footerStringList]
        
        if self.pretty:
            return '\n'.join(htmlStringList)
        else:
            return ''.join(htmlStringList) 
        
    def htmlStringLocal(self):
        pass
            
class HTMLDocument:
    def __init__(self,name_,title_,standAlone_=False,pretty_=True):
        self.name = name_
        self.title = title_            
        self.pretty = pretty_          ### make it human readable
        self.standAlone = standAlone_  ### Should the be a full html document
        
        self.constructList = []
        
    def addConstruct(self,construct_):
        ### add Type checking
        self.constructList.append(construct_)
        
    def htmlString(self):
        htmlStringList = []
        if self.standAlone:
            htmlStringList.append("<html><head><title>%s</title></head><body>"%(self.title))
        for construct in self.constructList:
            htmlStringList.append(construct.htmlString())
        
        if self.standAlone:
            htmlStringList.append("</html>")
            
        if self.pretty:
            return '\n'.join(htmlStringList)
        else:
            return ''.join(htmlStringList)
        
class HTMLTableRow(HTMLElement):
    def __init__(self,name_="TableRow",pretty_=True,**kwargs):
        HTMLElement.__init__(self,name_,pretty_,**kwargs)
        
        self.columns = []
        self.pretty = pretty_
        
    def addColumn(self,htmlColumn_):
        self.columns.append(htmlColumn_)
    
    def htmlString(self):
        htmlStringList = []
        htmlStringList.append('<tr id="%s" %s>'%(self.name,self.styleString))
        for column in self.columns:
            htmlStringList.append(column.htmlString())
        htmlStringList.append('</tr>')
        
        if self.pretty:
            #print str(htmlStringList)
            return '\n'.join(htmlStringList)
        else:
            return ''.join(htmlStringList)

    
class HTMLTableColumn(HTMLElement):
    def __init__(self,name_="TableColumn",value_=None,colspan_=1,header_=False,pretty_=True,**kwargs):
        HTMLElement.__init__(self,name_,pretty_,**kwargs)
        ### Add a formatting parameter so that I can control the look of numbers such as currency
        
        self.value = " "
        if value_ is not None:
            self.value = value_  
        self.pretty_ = pretty_
        self.colspan = colspan_
        self.header = header_
        
    def htmlString(self):
        if self.header:
            mon = "th"
        else:
            mon = "td"
        
        return '<%s id="%s" colspan=%d %s %s>%s</%s>'%(mon,self.name,self.colspan,self.classString,self.styleString,str(self.value),mon)
    
class HTMLTable(HTMLConstruct):
    def __init__(self,name_="Table",title_=None,pretty_=True,titleColor_="#282A57",majorColor_="#D6D6D6",
                 minorColor_="#EDEDED",**kwargs):
        if "table_class" in kwargs.keys():
            kwargs['class'] = kwargs['table_class']
        HTMLConstruct.__init__(self,name_,pretty_,**kwargs)
        
        self.nCols = 0
        self.nRows = 0
        self.name = name_
        self.title = title_
        self.titleColor = titleColor_
        self.majorColor = majorColor_
        self.minorColor = minorColor_
        
        self.data = []
        self.possibleFormats = ["m","n","b","c"] #Major, Minor, Clear
        self.rowFormats = []
        self.rows = []
        
    def addRow(self,rowList,rowFormats):
        if len(rowList)+1 != len(rowFormats):
            #print "RowList: " + str(rowList)
            #print "RowFormats: " + str(rowFormats)
            raise RuntimeError("In Table %s, incorrect list being passed to add row"%self.name)
        
        ### Create the HTML Row and fill it with data
        self.data.append(rowList)
        self.rowFormats.append(rowFormats) ## Add Checking for format
        ncols = sum(rowFormats[1:])
        if ncols > self.nCols:
            self.nCols = ncols
    def createTableElements(self):
        ### create Title Row
        if self.title is not None:
            titleRow = HTMLTableRow("%s_title_row"%self.name,self.pretty,background=self.titleColor,color="white",fontweight='bold',fontsize='18px')
            titleRow.addColumn(HTMLTableColumn("%s_title_col"%self.name,self.title,self.nCols,True,self.pretty))
            self.rows.append(titleRow)

        for i in range(0,len(self.data)):
            rowData = self.data[i]
            rowFormat = self.rowFormats[i]
            rowStyle = rowFormat.pop(0)
            #if rowStyle == 'h':#print "row hidden"
            #    display = "none"
                #visibility='hidden'
            #else:
            #    display = "inline"
                #visibility='visible'
            #if self.styles.has_key("width"):
            #    row = HTMLTableRow("%s_row_%d"%(self.name,i),self.pretty,display=display,width=self.styles['width'])
            #else:
            if rowStyle == 'h':
                row = HTMLTableRow("%s_row_%d"%(self.name,i),self.pretty,display='none')
            elif rowStyle == 'm':
                row = HTMLTableRow("%s_row_%d"%(self.name,i),self.pretty,background=self.majorColor,color="black",fontweight='bold',fontsize='16px')
            elif rowStyle == 'n':
                row = HTMLTableRow("%s_row_%d"%(self.name,i),self.pretty,background=self.minorColor,color="black",fontweight='bold',fontsize='14px')
            elif rowStyle == 'b':
                row = HTMLTableRow("%s_row_%d"%(self.name,i),self.pretty,background="white",color="black",fontweight='bold',fontsize='12px')
            else:
                row = HTMLTableRow("%s_row_%d"%(self.name,i),self.pretty,background="white",color="black",fontsize='12px')
            for j in range(0,len(rowData)):
                row.addColumn(HTMLTableColumn("%s_col_%d"%(row.name,j),rowData[j],rowFormat.pop(0),False,self.pretty))
            
            self.rows.append(row)   
                
    def htmlStringLocal(self):
        #print "Rows = " + str(self.data)
        #print "RowForms = " + str(self.rowFormats)
        style = self.styleString[:-2] + 'table-layout:fixed;"'
        htmlList = ['<table id="%s" %s %s>'%(self.name,self.classString,style)]
        self.createTableElements()
        for row in self.rows:
            htmlList.append(row.htmlString())
        htmlList.append("</table>")
        
        if self.pretty:
            return '\n'.join(htmlList)
        else:
            return ''.join(htmlList)
        
class HTMLForm(HTMLTable):
    def __init__(self,name_,title_=None, action_=None, pretty_=True, **kwargs):
        #self.name = name_
        #self.title = title_
        HTMLTable.__init__(self, name_+"_table", title_, pretty_,**kwargs)
        self.action = action_
        
        if self.action is not None:
            self._addHeader('<form id="%s" action=%s method="GET">'%(self.name,self.action))
        else:
            self._addHeader('<form id=%s method="GET">'%(self.name))
        #self._addFooter('<input type="submit" id="%s" value="%s">'%("submit-%s"%self.name,"Save"))
        self._addFooter('</form>')
        #self.elementList = []
        
    def addElement(self,htmlElement_):
        if htmlElement_.styles.has_key('visibility') and htmlElement_.styles['visibility'] == 'hidden':
            print "hidden"
            self.addRow([htmlElement_.title,htmlElement_.htmlString()],["h",1,1])
        elif hasattr(htmlElement_,'title') and htmlElement_.title is not None:
            self.addRow([htmlElement_.title,htmlElement_.htmlString()], ["b",1,1])
        else:
            self.addRow([" ",htmlElement_.htmlString()],["b",1,1])
        
class HTMLFormSelectBox(HTMLElement):
    def __init__(self,name_,title_,options_=[],default_=None,
                 pretty_=True,**kwargs):
        HTMLElement.__init__(self,name_,pretty_,**kwargs)
        self.title = title_
        self.options = options_ # options is a list of tuples (name,value)
        
        ### argument checking 
        if len(options_) > 0:
            for option in options_:
                if len(option) != 2:
                    raise Exception("HTMLFormSelectBox %s Option List not defined correctly: Should be list of 2D tuples (name,value)"%self.name)
        
        if default_ is not None:
            if default_ not in [x[0] for x in self.options]:
                raise Exception("Default value not in list of options for HTMLFormSelectBox: %s"%self.name)
        
        self.default = default_
        
        #self._addStyle('width',self.width)
        
    def addOption(self,name_,value_=None,unique=True):
        for option in self.options:
            if unique:
                if option[0] == name_ and option[1] == value_:
                    raise Exception("HTMLFormSelectBox %s trying to add Option (%s,%s")
                
            if value_ == None:
                value_ = name_
            
            self.options.append((name_,value_))

    def htmlString(self):        
        htmlList = []
        htmlList.append('<select id="%s" %s>'%(self.name,self.styleString))
        for option in self.options:
            if option[0] == self.default:
                htmlList.append('<option value="%s" selected>%s</option>'%(option[1],option[0]))
            else:
                htmlList.append('<option value="%s">%s</option>'%(option[1],option[0]))
                
        htmlList.append('</select>')
        if self.pretty:
            return '\n'.join(htmlList)
        else:
            return ''.join(htmlList)

class HTMLFormInputBox(HTMLElement):
    _acceptableTypes = {'int':'number','string':'text','float':'number'}
    def __init__(self,name_,title_,default_=None,type_='int',pretty_=True,**kwargs):
        HTMLElement.__init__(self,name_,pretty_,**kwargs)
        self.title = title_
        
        if type_ not in self._acceptableTypes.keys():
            raise Exception("HTMLFormInputBox %s: undefined type %s specified"%(self.name,str(type_)))
        self.type = type_
        self.pretty = pretty_
        
        self.default = None
        if default_ is not None:
            self.default = self.processValue(default_)
        
    def processValue(self,value):
        if self.type == 'int':
            if type(value) != types.IntType:
                try:
                    value = int(value)
                except Exception,e:
                    raise Exception("HTMLFormInputBox %s: value %s not consistent with Integer type"%(self.name,value))
        elif self.type == 'float':
            if type(value) != types.FloatType:
                if type(value) in [types.IntType,types.LongType]:
                    value = float(value)
                else:
                    try:
                        value = float(value)
                    except Exception,e:
                        raise Exception("HTMLFormInputBox %s: value %s not consistent with Float type"%(self.name,value))
        elif self.type == 'string':
            value = str(value)
        return value
    
    def htmlString(self):
        parsedType = self._acceptableTypes[self.type]
        if self.default is not None:
            return '<input id=%s type=%s value="%s" %s>'%(self.name,parsedType,self.default,
                                                          self.styleString)
        else:
            return '<input id=%s type=%s %s>'%(self.name,parsedType,
                                               self.styleString)

class HTMLFormCheckBox(HTMLElement):
    def __init__(self,name_,title_,default_=False,pretty_=True,**kwargs):
        HTMLElement.__init__(self,name_,pretty_,**kwargs)
        self.title = title_
        print default_
        if not isinstance(default_,bool):
            if default_.lower() == "true":
                default_ = True
            elif default_.lower() == "false":
                default_ = False
            else:
                raise Exception("HTMLFormCheckBox %s: default value has to be a boolean"%(self.name))
        if default_:
            self.default = "checked"
        else:
            self.default = ""

    def htmlString(self):
        return '<input id=%s type="checkbox" %s %s>'%(self.name,self.default,self.styleString)
            
def main():
    htmlDoc = HTMLDocument(name_="test_doc",title_="Test HTML Document",standAlone_=True)
    htmlForm = HTMLForm(name_="test_form",title_="Testing Form",width=800)
    htmlForm.addElement(HTMLFormSelectBox(name_="test_select",title_="Test Select Box",
                                         options_ = [('option_1','1'),('option_2','2'),('option_3','3')],
                                         default_ = 'option_2',visibility="visible",width=200))
    
    htmlForm.addElement(HTMLFormInputBox(name_="test_box", title_="Test Number Box",
                                         default_="12.0", type_='float',visibility="hidden"))
    htmlForm.addElement(HTMLFormCheckBox(name_="test_check", title_="Test CheckBox", default_=True))
    htmlForm.addElement(HTMLFormInputBox(name_="test_hidden", title_="HIDDEN", default_="you shouldn't see this", 
                                         type_="string", visibility="hidden"))
    htmlDoc.addConstruct(htmlForm)
    with open("test.html","wb") as f:
        f.write("%s"%htmlDoc.htmlString())
    

if __name__ == '__main__':
    main()         

