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

_hermes_svn_id_="$Id$"


class PreOrderTree():
    def __init__(self, table=None):
        if table is None: 
            self.table = []
        else: 
            self.table = table

    def find(self,obj):
        for l,r,lvl,o in self.table:
            if o == obj: return (l,r,lvl)
        raise RuntimeError("preordertree._find failed on %s"%obj)
        
    def add(self,obj,parentObj,tpl=None):
        if self.table == []:
            assert parentObj is None,"Wait, the tree isn't empty"
            self.table.append((0,1,0,obj))
            return 0
        else:
            assert self.table != [], "Wait, the tree is empty"
            if tpl is None:
                plk,prk,plvl = self.find(parentObj)
            else:
                plk,prk,plvl = tpl
            afterKey = prk-1
            newTuple = (afterKey+1,afterKey+2,plvl+1,obj)
            newList = [newTuple]
            for l,r,lvl,o in self.table:
                if l>afterKey: l += 2
                if r>afterKey: r += 2
                newList.append((l,r,lvl,o))
            self.table = newList
            return afterKey+1
        
    def remove(self,obj,tpl=None):
        assert self.table != [], "Wait, the tree is empty"
        if tpl is None:
            lhere,rhere,_ = self.find(obj)
        else:
            lhere,rhere,_ = tpl
        if lhere==0:
            raise RuntimeError("Removing the root node is not supported")
        newList = []
        for l,r,lvl,o in self.table:
            if l!=lhere:
                if l>lhere and r<rhere: lvl -= 1
                if l>=lhere: l -= 1
                if l>=rhere: l -= 1
                if r>=lhere: r -= 1
                if r>=rhere: r -= 1
                newList.append((l,r,lvl,o))                
        self.table = newList

    def removeRecursively(self,obj,tpl=None):
        assert self.table != [], "Wait, the tree is empty"
        if tpl is None:
            lhere,rhere,_ = self.find(obj)
        else:
            lhere,rhere,_ = tpl
        if lhere==0:
            raise RuntimeError("Removing the root node is not supported")
        newList = []
        diff = rhere - lhere + 1
        deletedObjs = []
        for l,r,lvl,o in self.table:
            if l >= lhere and r <= rhere:
                # These get deleted
                deletedObjs.append(o)
            else:
                if l > lhere: l -= diff
                if r > rhere: r -= diff
                newList.append((l,r,lvl,o))                
        self.table = newList
        return deletedObjs

    def isLeaf(self,obj,tpl=None):
        if tpl is None:
            lhere,rhere,_ = self.find(obj)
        else:
            lhere,rhere,_ = tpl
        return (rhere == lhere+1)
        
    def nTotalKids(self,obj,tpl=None):
        if tpl is None:
            lhere,rhere,_ = self.find(obj)
        else:
            lhere,rhere,_ = tpl
        return (rhere-(lhere+1))/2
    
    def nKids(self,obj,tpl=None):
        if tpl is None:
            lhere,rhere,lvlhere = self.find(obj)
        else:
            lhere,rhere,lvlhere = tpl
        descendants = (rhere - (lhere+1))/2
        for l,r,lvl,_ in self.table:
            if l>lhere and r<rhere and lvl==lvlhere+1:
                descendants -= (r-(l+1))/2
        return descendants # which is now only direct descendants
    
    def getKids(self,obj,tpl=None,returnAll=False):
        if tpl is None:
            lhere,rhere,lvlhere = self.find(obj)
        else:
            lhere,rhere,lvlhere = tpl
        kidList = []
        if returnAll:
            for l,r,lvl,o in self.table:
                if l>lhere and r<rhere and lvl==lvlhere+1:
                    kidList.append((l,r,lvl,o))
        else:
            for l,r,lvl,o in self.table:
                if l>lhere and r<rhere and lvl==lvlhere+1:
                    kidList.append(o)
        return kidList
                
    
    def getRoot(self,returnAll=False):
        for l,r,lvl,obj in self.table:
            if l == 0: 
                if returnAll: return (l,r,lvl,obj)
                else: return obj
        return None
            
    def emit(self,obj=None,tpl=None):
        stack = []
        self.table.sort()
        if obj is None:
            # Emit everything
            for l,r,lvl,o in self.table:
                if stack != []:
                    while r > stack[-1]:
                        stack.pop()
                print "%s (%d %d %d %s)"%(len(stack)*'  ',l,r,lvl,o)
                stack.append(r)
        else:
            if tpl is None:
                lhere,rhere,_ = self.find(obj)
            else:
                lhere,rhere,_ = tpl
                for l,r,lvl,o in self.table:
                    if l>=lhere and r<=rhere:
                        if stack != []:
                            while r > stack[-1]:
                                stack.pop()
                        print "%s (%d %d %d %s)"%(len(stack)*'  ',l,r,lvl,o)
                        stack.append(r)
                           

def main():
    pot = PreOrderTree()
    print 'add root'
    pot.add('root',None)
    pot.emit()
    print 'add root->first'
    pot.add("first",'root')
    pot.emit()
    print 'add first->second'
    pot.add("second",'first')
    pot.emit()
    print 'add second->third'
    pot.add("third",'second')
    pot.emit()
    print 'add root-fourth'
    pot.add("fourth",'root')
    pot.emit()
    print 'add fourth->fifth'
    pot.add("fifth","fourth")
    pot.emit()
    for s in ['root','first','second','third','fourth','fifth']:
        print '%s has %d descendants total, %d direct kids'%(s,pot.nTotalKids(s),pot.nKids(s))
    print 'remove fourth'
    pot.remove("fourth")
    pot.emit()
    print 'remove root'
    try:
        pot.remove("root")
    except Exception,e:
        print 'Attempt to remove root threw %s'%e
    pot.emit()

############
# Main hook
############

if __name__=="__main__":
    main()


            
    