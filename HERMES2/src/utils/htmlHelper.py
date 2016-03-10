#!/usr/bin/env python 
# -*- coding: utf-8 -*-

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################

__doc__=""" htmlHelper.py
This module holds helper functions for creating HTML elements
"""

_hermes_svn_id_="$Id: util.py 1425 2013-08-30 19:55:57Z stbrown $"
import types

class HTMLPrimitive:
    _allowedStyleElements = ['width','height','visibility',
                             'display','table-layout','border',
                             'background','color','fontweight',u'fontsize',
                             'minwidth','maxwidth','paddingright'
                             '']
    def __init__(self,name_,**kwargs):
        self.name = name_
        self.classString = u''
        self.styleString = u''
        self.styles = kwargs
        for arg,value in kwargs.items():
            if self.styleString == '':
                self.styleString = u' style="'
            if arg == 'cssclass':
                print 'Setting Class to ' + str(value)
                self.classString = u' class = "%s" '%value
            if arg in self._allowedStyleElements:
                if arg == 'fontsize':
                    self.styleString += u'font-size:%s;'%value
                elif arg == 'fontweight':
                    self.styleString += u'font-weight:%s;'%value
                elif arg == 'minwidth':
                    self.styleString += u'min-width:{0};'.format(value)
                elif arg == 'maxwidth':
                    self.styleString += u'max-width:{0};'.format(value)
                elif arg == 'paddingright':
                    self.styleString += u'padding-right:{0};'.format(value)
                else:
                    self.styleString += u'%s:%s;'%(arg,value)
        if self.styleString != '':
            self.styleString += u'" '
            
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
            return u'\n'.join(htmlStringList)
        else:
            return u''.join(htmlStringList) 
        
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
            htmlStringList.append(u"<html><head><title>%s</title></head><body>"%(self.title))
        for construct in self.constructList:
            htmlStringList.append(construct.htmlString())
        
        if self.standAlone:
            htmlStringList.append(u"</html>")
            
        if self.pretty:
            return u'\n'.join(htmlStringList)
        else:
            return u''.join(htmlStringList)
        
class HTMLTableRow(HTMLElement):
    def __init__(self,name_="TableRow",pretty_=True,**kwargs):
        HTMLElement.__init__(self,name_,pretty_,**kwargs)
        
        self.columns = []
        self.pretty = pretty_
        
    def addColumn(self,htmlColumn_):
        self.columns.append(htmlColumn_)
    
    def htmlString(self):
        htmlStringList = []
        htmlStringList.append(u'<tr id="%s" %s>'%(self.name,self.styleString))
        for column in self.columns:
            htmlStringList.append(column.htmlString())
        htmlStringList.append(u'</tr>')
        
        if self.pretty:
            return u'\n'.join(htmlStringList)
        else:
            return u''.join(htmlStringList)

    
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
            mon = u"td"
        else:
            mon = u"td"
        
        return u'<%s id="%s" colspan=%d %s %s>%s</%s>'%(mon,self.name,self.colspan,self.classString,self.styleString,unicode(self.value),mon)
    
class HTMLTable(HTMLConstruct):
    def __init__(self,name_="Table",title_=None,pretty_=True,titleColor_=u"#282A57",majorColor_=u"#D6D6D6",
                 minorColor_=u"#EDEDED",**kwargs):
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
        self.possibleFormats = ["m","n","b","c","N"] #Major, Minor, Clear
        self.rowFormats = []
        self.rows = []
        
    def addRow(self,rowList,rowFormats):
        print "F"
        if len(rowList)+1 != len(rowFormats):
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
            titleRow = HTMLTableRow(u"%s_title_row"%self.name,self.pretty,background=self.titleColor,color="white",fontweight='bold',fontsize='18px')
            titleRow.addColumn(HTMLTableColumn(u"%s_title_col"%self.name,self.title,self.nCols,True,self.pretty))
            self.rows.append(titleRow)
    
        for i in range(0,len(self.data)):
            rowData = self.data[i]
            rowFormat = self.rowFormats[i]
            rowStyle = rowFormat.pop(0)
            if rowStyle == 'h':
                row = HTMLTableRow(u"%s_row_%d"%(self.name,i),self.pretty,display=u'none')
            elif rowStyle == 'm':
                row = HTMLTableRow(u"%s_row_%d"%(self.name,i),self.pretty,background=self.majorColor,color=u"black",fontweight=u'bold',fontsize=u'16px')
            elif rowStyle == 'n':
                row = HTMLTableRow(u"%s_row_%d"%(self.name,i),self.pretty,background=self.minorColor,color=u"black",fontweight='bold',fontsize='14px')
            elif rowStyle == 'b':
                row = HTMLTableRow(u"%s_row_%d"%(self.name,i),self.pretty,background=u"white",color=u"black",fontweight=u'bold',fontsize=u'12px')
            elif rowStyle == 'c':
                row = HTMLTableRow(u"%s_row_%d"%(self.name,i),self.pretty,background=u"white",color=u"black",fontsize=u'12px',paddingright=u'10px')
            elif rowStyle =='U':
                row = HTMLTableRow(u"%s_row_%d"%(self.name,i),self.pretty)
            else:
                row = HTMLTableRow(u"%s_row_%d"%(self.name,i),self.pretty)
                
            for j in range(0,len(rowData)):
                row.addColumn(HTMLTableColumn(u"%s_col_%d"%(row.name,j),rowData[j],rowFormat.pop(0),False,self.pretty))
            
            self.rows.append(row)   
                
    def htmlStringLocal(self):
        style = self.styleString[:-2] + u'table-layout:fixed;"'
        htmlList = [u'<table id="%s" %s %s>'%(self.name,self.classString,style)]
        self.createTableElements()
        for row in self.rows:
            htmlList.append(row.htmlString())
        htmlList.append(u"</table>")
        if self.pretty:
            return u'\n'.join(htmlList)
        else:
            return u''.join(htmlList)
        
class HTMLForm(HTMLTable):
    def __init__(self,name_,title_=None, action_=None, pretty_=True, **kwargs):
        HTMLTable.__init__(self, name_+"_table", title_, pretty_,**kwargs)
        self.action = action_
        
        if self.action is not None:
            self._addHeader(u'<form id="%s" action=%s method="GET">'%(self.name,self.action))
        else:
            self._addHeader(u'<form id=%s method="GET">'%(self.name))
        self._addFooter(u'</form>')
        
    def addElement(self,htmlElement_):
        if htmlElement_.styles.has_key('visibility') and htmlElement_.styles['visibility'] == 'hidden':
            self.addRow([htmlElement_.title,htmlElement_.htmlString()],["h",1,1])
        elif hasattr(htmlElement_,'title') and htmlElement_.title is not None:
            self.addRow([htmlElement_.title,htmlElement_.htmlString()], ["N",1,1])
        else:
            self.addRow([u" ",htmlElement_.htmlString()],["N",1,1])
        
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
            if default_ not in [x[1] for x in self.options]:
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
        print 'RR'     
        htmlList = []
        htmlList.append(u'<select id="%s" %s %s>'%(self.name,self.classString,self.styleString))
        for option in self.options:
            if option[1] == self.default:
                htmlList.append(u'<option value="%s" selected>%s</option>'%(option[1],option[0]))
            else:
                htmlList.append(u'<option value="%s">%s</option>'%(option[1],option[0]))
                
        htmlList.append(u'</select>')
        htmlstring = u''.join(htmlList)
        if self.pretty:
            return u'\n'.join(htmlList)
        else:
            return u''.join(htmlList)

class HTMLFormInputBox(HTMLElement):
    _acceptableTypes = {'int':'number min="0" step="1"','string':'text','float':'number min="0" step="0.1"','dbkey':'text'}
    def __init__(self,name_,title_,default_=None,type_='int',data_=None,pretty_=True,**kwargs):
        HTMLElement.__init__(self,name_,pretty_,**kwargs)
        self.title = title_
        
        if type_ not in self._acceptableTypes.keys():
            raise Exception("HTMLFormInputBox %s: undefined type %s specified"%(self.name,str(type_)))
        self.type = type_
        self.pretty = pretty_
        self.data = data_
        
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
        elif self.type in ['string','dbkey']:
            value = unicode(value)
        return value
    
    def htmlString(self):
        parsedType = self._acceptableTypes[self.type]
        thisString = u''
#         dataString = ''
#         if self.data is not None:
#             dataString = u'data self.data-fieldmap
        if self.default is not None:
            thisString = u'<input id={0} type={1} value="{2}" {3} {4}>'.format(self.name,parsedType,self.default,
                                                                               self.classString,self.styleString)
        else:
            thisString = u'<input id=%s type=%s %s %s>'%(self.name,parsedType,
                                                  self.classString,self.styleString)
            
        return thisString

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
            self.default = u"checked"
        else:
            self.default = u""

    def htmlString(self):
        return u'<input id=%s type="checkbox" %s %s %s>'%(self.name,self.default,
                                                         self.classString, self.styleString)
        
class HTMLFormTextArea(HTMLElement):
    def __init__(self,name_,title_,default_='',rows_=4, cols_=100, pretty_=True,**kwargs):
        HTMLElement.__init__(self,name_,pretty_,**kwargs)
        self.title = title_
        self.default = default_
        self.rows=rows_
        self.cols=cols_

    def htmlString(self):
        return u'<textarea id={0} rows="{1}" cols="{2}">{3}</textarea>'.format(self.name,
                                                                                                                                                            self.rows,
                                                                                                                                                             self.cols,
                                                                                                                                                             self.default)
    
        

            
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

