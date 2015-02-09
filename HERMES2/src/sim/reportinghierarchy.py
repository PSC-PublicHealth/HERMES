#!/usr/bin/env python 

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

__doc__=""" reportinghierarchy.py
This module holds classes used in building reporting hierarchies.
"""

_hermes_svn_id_="$Id: reportinghieararchy.py 879 2012-03-08 16:47:47Z jleonard $"

import sys, os, copy, unittest, StringIO, types
import csv_tools, util, abstractbaseclasses

class ReportingHierarchyNode:
    
    def __init__(self, levelName, branchName, objList=[], overrides=[]):
        """
        Create a node.
        
        Parameters are:
            levelName: a name for this node's level in the hierarchy.  When this node
            is inserted as a child of another, all children of that node must share the
            same levelName.
            
            branchName: a name used to distinguish the nodes at a given level.  For
            example, if levelName were "region", branchName might be "Pennsylvania" and 
            all the child nodes of this node might share the levelName "county".
            
            objList: a list of objects associated with this node.  The object must be an 
            instance of this class (indicating that it is to become a child node) or an 
            instance of abstractbaseclasses.StatProvider.
            
            overrides: a dict of the form {fieldName:overrideCB,...} where overrideCB
            has the form:
            
                val = overrideCB(thisRHN, fieldName)
                
                or
                
                replacemaneFieldName,val = overrideCB(thisRHN, fieldName)
                
                
        """
        self.levelName= levelName
        self.branchName= branchName
        self.kidName= None
        self.parent= None
        self.overrides= overrides
        self.kidList= []
        self.leafList= []
        for o in objList: self.add(o)
        
    def __str__(self): return "<ReportingHierarchyNode(%s,%s)>"%(self.levelName,self.branchName)
        
    def add(self,obj):
        """
        Adds the given object as a child or leaf.  The object must be an instance of this class (indicating
        that it is to become a child node) or an instance of abstractbaseclasses.StatProvider.
        
        Adding None throws an exception.
        """
        if obj is None:
            raise RuntimeError('Tried to add None to %s'%self)
        elif isinstance(obj,self.__class__):
            assert obj.parent is None, \
                "ReportingHierarchyNode %s cannot add %s; that node is someone else's child"%(self,obj)
            if self.kidName is None:
                self.kidName= obj.levelName
            else:
                if obj.levelName != self.kidName:
                    raise RuntimeError("Name mismatch adding '%s' to %s when child levelName is '%s'"%\
                                       (obj,self,self.kidName))
            self.kidList.append(obj)
            obj.parent = self
        else:
            assert isinstance(obj,abstractbaseclasses.StatProvider), \
                "Objects added to a %s must implement %s or StatProvider"%(self.__class__.__name__,self.__class__.__name__)
            self.leafList.append(obj)
            
    def getAvailableFieldNames(self):
        """
        Returns a set of all field names known to this node or any of its descendants.
        """
        result = set()
        for l in self.leafList: 
            result.update(l.getAvailableStatNameList())
        for k in self.kidList: 
            result.update(k.getAvailableFieldNames())
        return result
    
    def report(self, fieldNameList, dictFactory = None):
        """
        Queries all children and leaves for the values of the named fields, returning a list of records
        each of which is a Dict (in the manner of csv_tools).  The records will contain the fields named
        by fieldNameList, if available, plus the fields "ReportingLevel" and "ReportingBranch".  There will
        be a single summary record, plus all records from all children's 'report()' results.

        It is an error to include "ReportingLevel" or "ReportingBranch" in fieldNameList.
        """
        for forbiddenName in ["ReportingLevel", "ReportingBranch"]:
            assert forbiddenName not in fieldNameList, \
                "%s is not a valid field name for %s.report()"%(forbiddenName,self.__class__.name)
        if dictFactory is None: summaryRec = {}
        else: summaryRec = dictFactory()
        summaryRec.update({"ReportingLevel":self.levelName, "ReportingBranch":self.branchName})
        for l in self.leafList:
            for field in fieldNameList:
                v= l.getStat(field)
                if v is not None:
                    if field in summaryRec: summaryRec[field] += v
                    else: summaryRec[field] = copy.deepcopy(v)
        recList= [summaryRec] # so summaryRec will be returned *first*
        for k in self.kidList:
            newRecList= k.report(fieldNameList, dictFactory=dictFactory) 
            recList += newRecList
            kidSummaryRec= newRecList[0]  # because summaryRec was returned *first* above
            for field in fieldNameList:
                if field in kidSummaryRec:
                    if field in summaryRec: 
                        summaryRec[field] += kidSummaryRec[field]
                    else: 
                        summaryRec[field] = copy.deepcopy(kidSummaryRec[field])  
        for f in self.overrides:
            if f not in summaryRec: summaryRec[f] = 0.0
            newVal = self.overrides[f](summaryRec,f)
            if newVal is not None:
                if isinstance(newVal,types.TupleType):
                    del summaryRec[f] # since the key is being replaced
                    summaryRec[newVal[0]] = newVal[1]
                else:
                    summaryRec[f]= newVal
        return recList

    def getReportingLevel(self):
        return self.levelName
    
    def getReportingBranch(self):
        return self.branchName

def describeSelf():
    print \
"""
Testing options:

  treetest

     generates and prints a tree of ReportingHierarchyNodes

"""

def main(myargv=None):
    "Provides a few test routines"
    
    class MySP (abstractbaseclasses.StatProvider):
        def __init__(self, inDict):
            self.myDict= inDict.copy()
        def getStat(self, key):
            if key in self.myDict: return self.myDict[key]
            else: return None
        def getAvailableStatNameList(self):
            return self.myDict.keys()

    if myargv is None:
        myargv = sys.argv
        
    if len(myargv)<2:
        describeSelf()
    elif myargv[1]=="treetest":
        if len(myargv)==2:

            sp1= MySP({"foo":"hello ","bar":1.0,"name":"sp1"})
            sp2= MySP({"foo":"world ","bar":10.0}) # No name for this one
            sp3= MySP({"foo":"from ","bar":100.0,"name":"sp3"})
            sp4= MySP({"foo":"main() ","bar":1000.0,"name":"sp4"})
            
            nd1= ReportingHierarchyNode("IHC","Pittsburgh",[sp1,sp2])
            nd2= ReportingHierarchyNode("IHC","Philadelphia",[sp3])
            nd3= ReportingHierarchyNode("District","Ohio")

            print "try adding a leaf which does not implement StatProvider"
            try:
                 nd3.add("HelloWorld")
            except Exception,e:
                print "Exception: %s"%e
            print ""
            
            nd3.add(sp4)
            
            print "try building a tree from inappropriate children"
            try:
                nd4= ReportingHierarchyNode("Region","MidWest",[nd1,nd2,nd3])
            except Exception,e:
                print "Exception: %s"%e
            print ""

            # We recreate because the old RHNs remember that they are already in a tree
            nd1= ReportingHierarchyNode("IHC","Pittsburgh",[sp1,sp2])
            nd2= ReportingHierarchyNode("IHC","Philadelphia",[sp3])
            nd3= ReportingHierarchyNode("District","Ohio")

            nd4= ReportingHierarchyNode("District","Pennsylvania",[nd1,nd2])
            nd5= ReportingHierarchyNode("Region","Midwest",[nd3,nd4])
            
            print "generate a report on a subset of fields"
            rep= nd5.report(["foo","name"])
            for rec in rep: print rec

        else:
            print "Wrong number of arguments!"
            describeSelf()
    else:
        describeSelf()

class TestReportingHierarchy(unittest.TestCase):
    def getReadBackBuf(self, wordList):
        try:
            sys.stdout = myStdout = StringIO.StringIO()
            main(wordList)
        finally:
            sys.stdout = sys.__stdout__
        return StringIO.StringIO(myStdout.getvalue())
    
    def compareOutputs(self, correctStr, readBack):
        correctRecs = StringIO.StringIO(correctStr)
        for a,b in zip(readBack.readlines(), correctRecs.readlines()):
            #print "<%s> vs. <%s>"%(a,b)
            self.assertTrue(a.strip() == b.strip())
    
    def test_reportinghierarchy(self):
        correctStr = """try adding a leaf which does not implement StatProvider
Exception: Objects added to a ReportingHierarchyNode must implement ReportingHierarchyNode or StatProvider

try building a tree from inappropriate children
Exception: Name mismatch adding '<ReportingHierarchyNode(District,Ohio)>' to <ReportingHierarchyNode(Region,MidWest)> when child levelName is 'IHC'

generate a report on a subset of fields
{'ReportingLevel': 'Region', 'foo': 'hello world from ', 'ReportingBranch': 'Midwest', 'name': 'sp1sp3'}
{'ReportingLevel': 'District', 'ReportingBranch': 'Ohio'}
{'ReportingLevel': 'District', 'foo': 'hello world from ', 'ReportingBranch': 'Pennsylvania', 'name': 'sp1sp3'}
{'ReportingLevel': 'IHC', 'foo': 'hello world ', 'ReportingBranch': 'Pittsburgh', 'name': 'sp1'}
{'ReportingLevel': 'IHC', 'foo': 'from ', 'ReportingBranch': 'Philadelphia', 'name': 'sp3'}
        """
        readBack= self.getReadBackBuf(['dummy','treetest'])
        self.compareOutputs(correctStr, readBack)

############
# Main hook
############

if __name__=="__main__":
    main()

