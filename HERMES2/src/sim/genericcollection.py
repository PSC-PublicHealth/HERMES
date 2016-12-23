#!/usr/bin/env python
__doc__=""" genericcollection.py
A base class used to implement 'collections' of things like vaccines
and people.

"""

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

import types, math, copy

import globals

class GenericCollection:
    """
    A supply of different but similar types, with some convenient
    math operators.
    """
    
    def __init__(self, tupleList=[]):
        "format of tupleList is [(someType,n),(someType,n)...]"
        self.vDict= {}
        vDict= self.vDict # cache for speed
        self.typeName= "GenericCollection"
        for v,n in tupleList:
            if v in vDict: vDict[v] += n
            else: vDict[v]= n
    def copy(self):
        result= copy.copy(self)
        result.vDict= self.vDict.copy()
        return result
    def getTupleList(self):
        return [(v,i) for v,i in self.items()]
    def __repr__(self):
        return "<%s(%s)>"%(self.typeName,repr(self.getTupleList()))
    def __str__(self):
        outStr= ""
        for v,n in self.getTupleList(): 
            if n!=0.0:
                outStr= outStr+"%s:%g,"%(str(v),n)
        #for v,n in self.getTupleList(): 
        #    if v.name=='T_Oral Polio': outStr= outStr+"%s:%g,"%(str(v),n)
        outStr= outStr[:-1] # lose trailing ','
        return "<%s(%s)>"%(self.typeName,outStr)
    def __add__(self,other):
        result= self.copy()
        if isinstance(other,type(self)):
            for v,n in other.items():
                if v in result.vDict: result.vDict[v] += n
                else: result.vDict[v]= n
        elif isinstance(other,int):
            for k in self.keys():
                self.vDict[k] += other
        elif isinstance(other,float):
            for k in self.keys():
                self.vDict[k] += other
        else:
            raise RuntimeError('Unrecognized type for other in GenericCollection.add')
        
        return result
    def __iadd__(self,other):
        if isinstance(other,type(self)):
            for v,n in other.items():
                if v in self.vDict: self.vDict[v] += n
                else: self.vDict[v]= n
        elif isinstance(other,int) or isinstance(other,float):
            for k in self.keys():
                self.vDict[k] += other
        else:
            raise RuntimeError('Unrecognized type for other in GenericCollection.iadd')
        return self
    def __sub__(self,other):
        result= self.copy()
        if isinstance(other,type(self)):
            for v,n in other.items():
                if v in result.vDict: result.vDict[v] -= n
                else: result.vDict[v]= -n
        elif isinstance(other,int) or isinstance(other,float):
            for k in self.keys():
                result.vDict[k] -= other
        else:
            raise RuntimeError('Unrecognized type for other in GenericCollection.sub')                                 
        return result
    def __isub__(self,other):
        if isinstance(other,type(self)):
            for v,n in other.items():
                if v in self.vDict: self.vDict[v] -= n
                else: self.vDict[v]= -n
        elif isinstance(other,int) or isinstance(other,float):
            for k in self.keys():
                self.vDict[k]-= other
        else:
            raise RuntimeError('Unrecognized type for other in GenericCollection.isub')
        return self
    def __div__(self,other):
        result= self.copy()
        result.vDict.clear()
        allKeys= self.keys()
        for k in other.keys():
            if not k in allKeys: allKeys.append(k)
        for k in allKeys:
            # Division may throw exception or KeyError, but that's OK- it's the
            # correct diagnostic.
            if k in self.vDict:
                if k in other.vDict:
                    if self.vDict[k]==other.vDict[k]: # handle 0.0/0.0 case
                        result.vDict[k]= 1.0
                    else:
                        try:
                            result.vDict[k]= float(self.vDict[k])/float(other.vDict[k])
                        except ZeroDivisionError,e:
                            raise ZeroDivisionError("%g/%g %s"%(self.vDict[k],
                                                                other.vDict[k],
                                                                e))
                elif self.vDict[k]==0.0:
                    result.vDict[k]= 1.0
                else:
                    raise ZeroDivisionError("%g/(nothing)"%self.vDict[k])
            else:
                result.vDict[k]= 0.0
        return result
    def __mul__(self,other):
        result= self.copy()
        result.vDict.clear()
        if isinstance(other,type(self)):
            for k in self.keys():
                if k in other.vDict:
                    result.vDict[k]= self.vDict[k]*other.vDict[k]
                else:
                    result.vDict[k]= 0
            for k in other.keys():
                if k not in result.vDict:
                    result.vDict[k]= 0
        elif isinstance(other,int):
            for k in self.keys():
                result.vDict[k]= other*self.vDict[k]
        elif isinstance(other,long):
            for k in self.keys():
                result.vDict[k]= other*self.vDict[k]
        elif isinstance(other,float):
            for k in self.keys():
                result.vDict[k]= other*self.vDict[k]
        else:
            raise TypeError("unsupported operand type(s) for *: 'GenericCollection' and '%s'"%type(other))
        return result
    def __imul__(self,other):
        if isinstance(other,type(self)):
            for k in self.keys():
                if k in other.vDict:
                    self.vDict[k]= self.vDict[k]*other.vDict[k]
                else:
                    self.vDict[k]= 0
            for k in other.keys():
                if k not in self.vDict:
                    self.vDict[k]= 0
        elif isinstance(other,int):
            for k in self.keys():
                self.vDict[k]= other*self.vDict[k]
        elif isinstance(other,float):
            for k in self.keys():
                self.vDict[k]= other*self.vDict[k]
        else:
            raise TypeError("unsupported operand type(s) for *: 'GenericCollection' and '%s'"%type(other))
        return self
    def __eq__(self,other):
        if type(self)!=type(other): return False
        for k,v in self.items():
            if other[k]!=v: return False
        for k in other.keys():
            if other[k] == 0.0: continue
            elif k not in self.vDict: return False
        return True
    def __ne__(self,other):
        return not self.__eq__(other)
    def __getitem__(self,key):
        if key in self.vDict: return self.vDict[key]
        else: return 0
    def __setitem__(self,key,val):
        self.vDict[key]= val
    def has_key(self,key): return key in self.vDict
    def __contains__(self,key): return key in self.vDict
    def keys(self):
        l= self.vDict.keys()
        if globals.deterministic: l.sort()
        return l
    def items(self):
        l= self.vDict.items()
        if globals.deterministic: l.sort()
        return l
    def totalCount(self):
        """
        Returns the total number of elements of any type-
        Useful for detecting empty collections
        """
        return sum([n for v,n in self.items()])
    
    def filter(self,other,filt):
        if not isinstance(other,type(self)) or not isinstance(filt,type(self)):
            raise RuntimeError('GenericCollection.filter requires that all function arguments be of the same type')

        for v,n in filt.items():
            if v in self.vDict and v in other.vDict and n!=0:
                self.vDict[v] = other.vDict[v] * n

        return self
    
    def replace(self,other):
        if isinstance(other,type(self)):
            for v,n in other.items():
                if v in self.vDict and n!=0:
                    self.vDict[v] = n
        else:
            raise RuntimeError('Unrecognized type for other in GenericCollection.isub')
        return self
    def floorZero(self):
        for v,nV in self.items():
            if nV<0: self.vDict[v]= 0
    def ceilingOne(self):
        for v,nV in self.items():
            if nV>1:
                if type(nV)==types.IntType or type(nV)==types.LongType:
                    self.vDict[v]=1
                else:
                    self.vDict[v]=1.0
                
    def roundUp(self):
        for v,nV in self.items():
            self.vDict[v]= int(math.ceil(nV))
    def roundDown(self):
        for v,nV in self.items():
            self.vDict[v]= int(math.floor(nV))
    def round(self):
        for v,nV in self.items():
            self.vDict[v]= int(round(nV))
    def keysNotInCollection(self,other):
        keyList = []
        for okey in other.keys():
            if okey not in self.keys():
                keyList.append(okey)
        return keyList
    
    @classmethod
    def min(cls,c1,c2):
        result= c1.copy()
        if isinstance(c2,cls):
            for v,nV in c2.items():
                if v in result:
                    result.vDict[v]= min(result.vDict[v],nV)
                else:
                    result.vDict[v]= nV
        elif isinstance(c2,int) or isinstance(c2,float):
            for v,nV in result.items():
                result.vDict[v]= min(nV,c2)
        else:
            raise TypeError("unsupported operand type(s) for min: 'GenericCollection' and '%s'"%type(other))
        return result
                
    @classmethod
    def max(cls,c1,c2):
        result= c1.copy()
        if isinstance(c2,cls):
            for v,nV in c2.items():
                if v in result.vDict:
                    result.vDict[v]= min(result.vDict[v],nV)
                else:
                    result.vDict[v]= nV
        elif isinstance(c2,int) or isinstance(c2,float):
            for v,nV in result.items():
                result.vDict[v]= min(nV,c2)
        else:
            raise TypeError("unsupported operand type(s) for max: 'GenericCollection' and '%s'"%type(other))
        return result
                
    
                
                                           
