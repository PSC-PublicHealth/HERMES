#! /usr/bin/env python

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


__doc__ = """ input.py
This module handles and parses user input to the HERMES model
"""
_hermes_svn_id_="$Id$"

import sys,os,os.path,types
import csv
import ipath
import csv_tools
import globals as G
import kvp_tools
import util
import chardet

KeywordTokenTypes = [ 'TF', 'string', 'stringOrNone', 'int', 'intOrNone', 'long', 'longOrNone',
                     'float', 'floatOrNone', 'probability','string_list', 'int_list', 'float_list', 'long_list',
                     'filename','filenameOrNone','filename_list']

class KeywordTokenDefinition:
    def __init__(self,rec):
        #print csvrow
        self.name = rec['Keyword']
        self.type = rec['Type']
        self.displayName = rec['DisplayName']
        self.description = rec['Description']
        self.level = int(rec['Level'])
        self.notes = rec['Notes']
        self.default = None
        self.order =  int(rec['Order'])
        self.rowOrder = rec['_roworder_']
        
        defaultString = str(rec['DefaultValue'])
        if self.type not in KeywordTokenTypes:
            raise RuntimeError("Keyword %s type of %s is not a valid type"%(self.name,self.type))
        
        if self.type == "string_list":
            if defaultString.lower() == 'none' : self.default = None
            else: self.default = [str(x) for x in defaultString.split(':')]
        elif self.type == "float_list":
            if defaultString.lower() == 'none' : self.default = None
            else: self.default = [float(x) for x in defaultString.split(':')]
        elif self.type == "int_list":
            if defaultString.lower() == 'none' : self.default = None
            else: self.default = [int(x) for x in defaultString.split(':')]
        else:
            if defaultString.lower()=='none': self.default= None
            elif defaultString.lower()=='true': self.default= True
            elif defaultString.lower()=='false': self.default= False
            elif self.type in ["int","intOrNone","long","longOrNone","float","floatOrNone"]: 
                try:
                    if self.type in ["int","intOrNone"]: self.default= int(defaultString)
                    elif self.type in ["long","longOrNone"]: self.default= long(defaultString)
                    elif self.type in ["float","floatOrNone","probability"]: self.default= float(defaultString)
                    else: raise RuntimeError("Internal error: mis-handled input default type")
                except ValueError:
                    raise RuntimeError("Keyword %s default value %s inconsistent with type %s"%\
                                       (self.name,self.default,self.type))
            else: self.default = defaultString

    def __str__(self):
        return "KeywordTokenDefinition(%s,%s,%s,%s,%s)"%(self.name,self.type,str(self.default),
                                                         self.description,self.notes)
        
    
    def csvrowFormat(self):
        returnlist = []
        returnlist.append(self.name)
        if type(self.default) == list:
            for i in range(0,len(self.default)):    
                returnlist.append(self.default[i])
        else:
            returnlist.append(self.default)
        returnlist.append(self.notes)
        return returnlist

class InputDefault:
    def __init__(self):
        self.TokenDict = {}
        recList =[]
        keyList =[]
        with open(os.path.join(os.path.join(os.path.dirname(__file__),
                                            G.defaultInputTokenFile)),
                                            'rb') as f:
            keyList,recList = csv_tools.parseCSV(f)
                      
            for idx,rec in enumerate(recList):
                if rec['Keyword'] is not None:
                    rec['_roworder_'] = idx
                    self.TokenDict[rec['Keyword']] = KeywordTokenDefinition(rec)


    def getTokenType(self,key):
        if key not in self.TokenDict.keys():
            raise RuntimeError("Keyword %s not in default inputs list"%str(key))
        return self.TokenDict[key].type
    
    def getTokenLevel(self,key):
        if key not in self.TokenDict.keys():
            raise RuntimeError("Keyword %s not in default inputs list"%str(key))
        return self.TokenDict[key].level
    
    def orderedTokenListByLevel(self,level=None,allBelow=False):
        rList = []
        if level is None: # which means include all
            for key, token in self.TokenDict.items():
                rList.append((token.level, token.order, token.rowOrder, key))
        else:
            for key, token in self.TokenDict.items():
                if allBelow:
                    if token.level <= level:
                        rList.append((token.level, token.order, token.rowOrder, key))
                else:    
                    if token.level == level:
                        rList.append((token.level, token.order, token.rowOrder, key))
        rList.sort()
        tokenList = [self.TokenDict[key] for lvl,order,row,key in rList] # @UnusedVariable
        
        return tokenList
      
    def getTokenDisplayName(self,key):
        if key not in self.TokenDict.keys():
            raise RuntimeError("Keyword %s not in default inputs list"%str(key))
        return self.TokenDict[key].displayName
    
    def keys(self):
        return self.TokenDict.keys()
    
    def has_key(self,key):
        return key in self.TokenDict.keys()
    
    def iterkeys(self):
        return self.TokenDict.iterkeys()
    
    def getToken(self,key):
        return self.TokenDict[key]
    
    def __getitem__(self, key):
        return self.TokenDict[key].default
       
    def processKeywordValue(self,key,val=None):   
        if key not in self.TokenDict.keys():
            raise RuntimeError("Keyword %s not in default inputs list"%str(key))
        
        TokenType = self.TokenDict[key].type
        if val is None:
            return self.TokenDict[key].default
        
        if TokenType == 'TF':
            if isinstance(val,types.BooleanType):
                return val
            elif isinstance(val,types.NoneType):
                return False
            elif isinstance(val,types.StringType) or isinstance(val,unicode):
                if val.lower() in ['true', 't']: return True
                elif val.lower() in ['false', 'f']: return False
                else: 
                    raise RuntimeError("Keyword %s has a invalid value of %s: acceptable values are True, False, T, or F"%\
                                       (key,val))
            else:
                raise RuntimeError("Keyword %s has a invalid value of %s: acceptable values are True, False, T, or F"%\
                                   (key,val))
                
        elif TokenType in ['string', 'filename']:
            if type(val) == types.NoneType or (isinstance(val, types.StringTypes) and val.lower=='none'):
                raise RuntimeError("Keyword %s has invalid value %s; a string is required"%(key,val))
            return unicode(val)
        elif TokenType in ['stringOrNone','filenameOrNone']:
            if val is None: return val
            elif isinstance(val, types.StringTypes) and val.lower=='none': return None
            else: return unicode(val)
        elif TokenType == 'int':
            if type(val) == types.IntType: return val
            else:
                try:
                    valtmp = int(val)
                except:
                    raise RuntimeError("Keyword %s has invalid value %s; should be an integer"%(key,val))
                return valtmp
        elif TokenType == 'intOrNone':
            if val is None: return val
            elif type(val) == types.IntType: return val
            else:
                if val == "":
                    return None
                else:
                    try:
                        valtmp = int(val)
                    except:
                        raise RuntimeError("Keyword %s has invalid value %s; should be an integer"%(key,val))
                    return valtmp
        elif TokenType == 'long':
            if type(val) in [types.IntType, types.LongType]: return long(val)
            else:
                try:
                    valtmp = long(val)
                except:
                    raise RuntimeError("Keyword %s has invalid value %s; should be an integer or long integer"%(key,val))          
                return valtmp  
        elif TokenType == 'longOrNone':
            if val is None: return val
            elif type(val) in [types.IntType, types.LongType]: return long(val)
            else:
                if val == "":
                    return None
                else:
                    try:
                        valtmp = long(val)
                    except:
                        raise RuntimeError("Keyword %s has invalid value %s; should be an integer or long integer"%(key,val)) 
                    return valtmp           
        elif TokenType == 'float':
            if type(val) == types.FloatType: return val
            elif type(val) == types.IntType: return float(val)
            else: 
                try:
                    valtmp = float(val)
                except:
                    raise RuntimeError("Keyword %s has invalid value %s; should be a floating point number"%(key,val))  
                return valtmp    
        elif TokenType == 'probability':
            valClean = 0.0
            if type(val) == types.FloatType: valClean = val
            elif type(val) == types.IntType: valClean = float(val)
            else:
                try:
                    valClean = float(val)
                except:
                    raise RuntimeError("Keyword %s probability has invalid value %s; should be a floating point number between 0.0 and 1.0"%(key,str(val)))      
            
            if valClean < 0.0 or valClean > 1.0:
                print "probablity val is %s"%(str(val))
                raise RuntimeError("Keyword %s probability has value %s; should be a floating point number between 0.0 and 1.0"%(key,str(val)))
            return valClean
              
        elif TokenType == 'floatOrNone':
            if val is None: return val
            elif type(val) == types.FloatType: return val
            else:
                if val == "":
                    return None
                else:
                    try:
                        valtmp = float(val)
                    except:
                        raise RuntimeError("Keyword %s has invalid value %s; should be a floating point number"%(key,val))
                    return valtmp
        elif TokenType in ['string_list', 'filename_list']:
            if type(val) == types.ListType:
                return [unicode(x).replace('"','').replace("'","") for x in val]
            elif val is None:
                return []
            else:
                return [unicode(x).replace('"','').replace("'","") for x in val.split(",")]
        elif TokenType == 'int_list':
            try:
                if type(val) == types.ListType:
                    return [int(x) for x in val]
                elif type(val) in [types.IntType, types.LongType]:
                    return [val]
                elif val is None:
                    return []
                else:
                    return [int(x) for x in val.split(",")]
            except:
                raise RuntimeError("Keyword %s has invalid value %s; should be a series of integers"%(key,val))

        elif TokenType == 'long_list':
            try:
                if type(val) == types.ListType:
                    return [long(x) for x in val]
                elif type(val) in [types.IntType, types.LongType]:
                    return [long(val)]
                elif val is None:
                    return []
                else:
                    return [long(x) for x in val.split(",")]
            except:
                raise RuntimeError("Keyword %s has invalid value %s; should be a series of integers"%(key,val))

        elif TokenType == 'float_list':
            try:
                if type(val) == types.ListType:
                    return [float(x) for x in val]
                elif val is None:
                    return []
                else:
                    return [float(x) for x in val.split(",")]
            except:
                raise RuntimeError("Keyword %s has invalid value %s; should be a series of floats"%(key,val))
        else:
            raise RuntimeError("Internal error: encountered unknown UserInput type %s"%TokenType)

""" 
This class will hold all of the user defined inputs
"""
class UserInput:
    defaultInput = InputDefault()
    
    def __init__(self,userInputFileName=None, useDb=None, dbSession=None):
        self.definitionFileName = userInputFileName
        self.fromDb = useDb

        self.frozen= False # Until this is True, new values can be set/added
        
        """ possibly read and populate the default keywords dictionary """
#         if UserInput.defaultTokenDict is None:
#             UserInput.defaultTokenDict = dict()
#             recList =[]
#             keyList =[]
#             with open(os.path.join(os.path.join(os.path.dirname(__file__),
#                                                 G.defaultInputTokenFile)),
#                                    'rb') as f:
#                 keyList,recList = csv_tools.parseCSV(f)
#                       
#             for rec in recList:
#                 if rec['Keyword'] is not None:
#                     UserInput.defaultTokenDict[rec['Keyword']] = KeywordTokenDefinition(rec)

        """ This dictionary will hold all of the user defined input values """
        self.inputDict = dict()

        if useDb:
            import shadow_db_routines as shd_db
            strRecs = shd_db.getDbInputRecs(userInputFileName, session_in=dbSession)
            self.addValues(strRecs, replace=True, vtype="kvp")
            return
        
        """ Make the definitions, if any """
        if userInputFileName is not None:
            with util.openDataFullPath(userInputFileName,'rU') as f:
                lines = f.readlines()
            encodingInfo = chardet.detect("".join(lines))
            encoding = encodingInfo['encoding']
            if encodingInfo['confidence'] >= 0.8:
                encoding = encodingInfo['encoding']
            else:
                encoding = sys.getdefaultencoding()
            if encoding == "utf8" or encoding == "utf-8": encoding = "utf-8-sig"
            with util.openDataFullPath(userInputFileName,'rU') as f:
                if userInputFileName[-4:] == '.kvp':
                    self.addValues(f,replace=True,vtype="kvp",encoding=encoding)
                else:
                    self.addValues(f,replace=True,vtype="csv")
                                    
    def printTable(self):
        for keywords in self.inputDict.keys():
            print str(keywords) + ": " + str(self.inputDict[keywords])        
            
    def freeze(self,printInfo=False):
        """
        This method causes the input information to be frozen, meaning that no additional values
        can be set or appended.  After this function is called, all valid keys will have values; those
        values may be the defaults for the key.  If a key is defined such that the default value
        is invalid- None when a string is required, for example- an exception will be raised.  This
        provides a mechanism to force the user to explicitly supply some values.
        
        This function can be called explicitly.  If it is not called explicitly, accessing the value of any
        key (explicitly, via the len() function, or via an iterator) will call the function implicitly.
        
        If printInfo is True, a table of keys and associated values is printed via the printTabel() method.  
        This is true even if freeze() has been called previously on this instance.
        """
        if not self.frozen:
            """ Fill in default values where there are none defined by the user """
            for keyword in self.defaultInput.keys():
                if keyword not in self.inputDict:
                    #defTok =.defaultTokenDict[keyword]
                    #self.inputDict[keyword] = self.checkValAgainstType(keyword,defTok.default,defTok.type)
                    self.inputDict[keyword] = self.defaultInput.processKeywordValue(keyword)
            self.frozen= True
        if printInfo: self.printTable()
        
    def addValues(self,inputIterator,replace=True,vtype="csv",encoding=None):
        """
        This method adds the values defined by inputIterator to this UserInput instance.  inputIterator 
        is an iterator providing lines of input either in key-value format or in csvrow format.  If 'replace' 
        is true the values replace any value already present for that keyword.  If 'replace' is false, new 
        values are ignored for any keyword for which a value is already defined.
        
        vtype must be "csv" or "kvp" for comma-separated-value or key-value-pair values respectively.
        """
        inputIterator= iter(inputIterator) # in case a raw list got passed in
        if vtype == "csv":
            userReader = csv.reader(inputIterator)
            for row in userReader:
                if row[0] != "Keyword":
                    """ Make sure this is a keyword of HERMES, and if it is, get the default token """
                    key = row[0]
                    val = row[1]
                    if self.defaultInput.has_key(key):
                        val = self.defaultInput.processKeywordValue(key,val)
                        if self.inputDict.has_key(key):
                            if replace:
                                self.inputDict[key] = val
                            else:
                                pass
                        else:
                            self.inputDict[key] = val
                    else:
                        raise RuntimeError("Keyword %s is not a valid HERMES keyword" % key)
                         
        elif vtype=="kvp":
            parser= kvp_tools.KVPParser()
            uncheckedDict= parser.parse(inputIterator, encoding)
            for key,val in uncheckedDict.items():
                if self.defaultInput.has_key(key):
                    val = self.defaultInput.processKeywordValue(key,val)

                    if self.inputDict.has_key(key):
                        if replace:
                            self.inputDict[key]= val
                        else:
                            pass
                    else:
                        self.inputDict[key]= val
                else:
                    raise RuntimeError("Keyword %s is not a valid HERMES keyword"%key)
                    
        else:
            raise RuntimeError('Unknown user info format %s'%vtype)
        
    def safeGetValue(self,keyword,default):
        if not self.frozen: self.freeze()
        if self.has_key(keyword): return self.getValue(keyword)
        else: return default
    
    def getValue(self,keyword):
        if not self.frozen: self.freeze()
        if not self.inputDict.has_key(keyword):
            raise RuntimeError("Attempting to get a keyword from input that does not exist: %s"%keyword)
        return self.inputDict[keyword]

    def safeGetValueFromList(self,keyword,index,default):
        if not self.frozen: self.freeze()
        if self.has_key(keyword): 
            l = self.getValue(keyword)
            if not l:
                return None
            assert isinstance(l,types.ListType), "Value of %s should be a list or None"%keyword
            return l[index%len(l)]
        else: 
            return default
    
    def getValueFromList(self,keyword,index):
        if not self.frozen: self.freeze()
        if not self.inputDict.has_key(keyword):
            raise RuntimeError("Attempting to get a keyword from input that does not exist: %s"%keyword)
        l = self.getValue(keyword)
        if not l:
            return None
        else:
            assert isinstance(l,types.ListType), "Value of %s should be a list or None"%keyword
            return l[index%len(l)]

    def __getitem__(self,keyword):
        if not self.frozen: self.freeze()
        return self.getValue(keyword)
    
    def __setitem__(self,keyword,value):
        if self.frozen:
            raise RuntimeError("Attempted to set an item in a UserInput after freezing")
        else:
            self.inputDict[keyword]= value
    
    def __delitem__(self,keyword):
        if self.frozen:
            raise RuntimeError("Attempted to delete an item from a UserInput after freezing")
        else:
            del self.inputDict[keyword]
    
    def __len__(self):
        if not self.frozen: self.freeze()
        return len(self.inputDict)
    
    def __iter__(self):
        if not self.frozen: self.freeze()
        return iter(self.inputDict)
    
    def iterkeys(self):
        return self.__iter__()
    
    def __contains__(self,item):
        if not self.frozen: self.freeze()
        return self.inputDict.__contains__(item)
    
    def has_key(self,item):
        return self.__contains__(item)
    

class UnifiedInput:
    def __init__(self):
        # if / when any input files are added to this list, besides having them load
        # with the other type managers, they should be: 
        #
        #   * made override-able locally (input_default and load_typemanagers.py)
        #   * added to the list of files added when inputs are zipped.  This includes
        #     adding both the unified file and the field in userInput for the override
        #     file.  (HermesInput.py)
        #   * added to the list of files to be faked in shadow_network.writeCSVRepresentation

        self.vaccineFile = "UnifiedVaccineTypeInfo.csv"
        self.truckFile   = "UnifiedTruckCapacityInfo.csv"
        self.peopleFile  = "UnifiedPeopleTypeInfo.csv"
        self.fridgeFile  = "UnifiedStorageTypeInfo.csv"
        self.iceFile     = "UnifiedIceTypeInfo.csv"
        self.packageFile = "UnifiedPackageTypeInfo.csv"
        self.staffFile   = "UnifiedStaffTypeInfo.csv"
        self.perDiemFile = "UnifiedPerDiemTypeInfo.csv"

def main():
    inputDefault = InputDefault()
    paramsListForLevel = inputDefault.orderedTokenListByLevel(1, True)
    print "Just for 1 = "+ str([x.name for x in paramsListForLevel])
    paramsListForLevel = inputDefault.orderedTokenListByLevel(2, True)
    print "Just for 1,2 = "+ str([x.name for x in paramsListForLevel])
    
if __name__ == '__main__':
    main()        
               
