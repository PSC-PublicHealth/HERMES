#!/usr/bin/env python
__doc__=""" breakagemodel.py
An operation on a collection of Groups which implements breakage.
"""



_hermes_svn_id_="$Id$"

import types, math, random, util
from util import poisson
import abstractbaseclasses

# Breakage types
BREAK_GENERIC = 0
BREAK_IN_STORAGE = 1
BREAK_IN_TRANSIT = 2

class BreakageModel:
    """
    A representation of damage to goods in shipping and handling.
    """
    def __init__(self):
        """
        This is the base class; the user is not expected to instantiate
        this type directly.
        """
        pass

    def __str__(self):
        return "<BreakageModel>"
    
    def applyBreakageInStorage(self,wh,groupList):
        """
        This method implements breakage which occurs in storage.
        The input groupList is of the is a list of VaccineGroups.  This method returns a
        tuple ( unbrokenGroupList, brokenGroupList ), where all vials in the first list
        are unbroken and all vials in the second are broken.  The unbrokenGroupList 
        is a shallow copy of the input groupList containing split VaccineGroups.
        """
        raise RuntimeError("BreakageModel.applyBreakageInStorage called")
            
    def applyBreakageInTransit(self,fromWh,toWh,groupList):
        """
        This method implements breakage which occurs in transit. The input
        groupList is of the is a list of VaccineGroups; this list is modified in
        place.  The inputs fromWh and toWh are the sending and receiving
        warehouses respectively.  This method returns a tuple
        (unbrokenGroupList, brokenGroupList), where all vials in the first list
        are unbroken and all vials in the second are broken.   The
        unbrokenGroupList is a shallow copy of the input groupList containing
        split VaccineGroups.
        """
        raise RuntimeError("BreakageModel.applyBreakageInTransit called")
            
    def applyBreakageCombined(self,fromWh,toWh,groupList):
        """
        This method implements breakage which occurs in storage and one link of
        subsequent transit.  Its results should match the cumulative effects of
        calling the two corresponding functions; it appears separately for
        economy of function calls.  This method returns a tuple (
        unbrokenGroupList, brokenGroupList ), where all vials in the first list
        are unbroken and all vials in the second are broken.   The unbrokenGroupList 
        is a shallow copy of the input groupList containing split VaccineGroups.
        """
        l1= self.applyBreakageInStorage(fromWh, groupList) # this changes groupList
        return l1 + self.applyBreakageInTransit(fromWh, toWh, groupList)
        
class SimpleBreakageModel(BreakageModel):
    """
    This breakage model just multiplies the given breakage fractions by the 
    number of vials in a group and rounds to find the number of broken vials.  
    This works for large VaccineGroups but fails to break vials in small groups-
    1% breakage for a 10 vial group always rounds to zero broken vials.
    """
    def __init__(self,storageBreakageFraction,transitBreakageFraction):
        """
        storageBreakageFraction and transitBreakageFraction are fractions- 
        0.01 represents 1% breakage.
        """
        BreakageModel.__init__(self)
        self.storageBreakageFraction= storageBreakageFraction
        self.transitBreakageFraction= transitBreakageFraction
                                           
    def __str__(self):
        return "<SimpleBreakageModel(%g,%g)>"%(self.storageBreakageFraction,self.transitBreakageFraction)
    
    def _break(self,groupList,f):
        brokenList= []
        unbrokenList= []
        if f>0.0:
            for g in groupList:
                if isinstance(g, abstractbaseclasses.Shippable):
                    nBroke= int(round(f*g.getCount()))
                    if nBroke>0:
                        if nBroke<g.getCount():
                            brokenG= g.split(nBroke)
                            brokenG.maybeTrack("broken in storage")
                            brokenG.getType().recordBreakage(brokenG.getCount())
                            brokenList.append(brokenG)
                            unbrokenList.append(g)
                        else:
                            brokenList.append(g)
                    else:
                        unbrokenList.append(g)
                else:
                    unbrokenList.append(g) # Only shippables can break, not fixed refrigerators
        else:
            unbrokenList= groupList[:] # shallow copy
        return unbrokenList,brokenList
        
    def applyBreakageInStorage(self,wh,groupList):
        return self._break(groupList,self.storageBreakageFraction)

    def applyBreakageInTransit(self,fromWh,toWh,groupList):
        return self._break(groupList,self.transitBreakageFraction)

    def applyBreakageCombined(self,fromWh,toWh,groupList):
        return self._break(groupList,
                           self.storageBreakageFraction+self.transitBreakageFraction)

class PoissonBreakageModel(SimpleBreakageModel):
    """
    This breakage model produces a Poisson-distributed breakage rate with
    the mean number of broken vials equal to the breakageFraction times
    the number of vials present.
    """
    def __init__(self,storageBreakageFraction,transitBreakageFraction):
        """
        storageBreakageFraction and transitBreakageFraction are fractions- 
        0.01 represents 1% breakage.
        """
        SimpleBreakageModel.__init__(self,storageBreakageFraction,transitBreakageFraction)
                                           
    def __str__(self):
        return "<SimpleBreakageModel(%g,%g)>"%(self.storageBreakageFraction,self.transitBreakageFraction)

    def _break(self,groupList,f):
        brokenList= []
        unbrokenList= []
        if f>0.0:
            for g in groupList:
                if isinstance(g,abstractbaseclasses.Shippable):
                    v= g.getType()
                    n= g.getCount()
                    if hasattr(v,"rndm"):
                        nBroke= poisson(n*f,v.rndm)
                    else:
                        nBroke= 0
                    if nBroke>0:
                        if nBroke<g.getCount():
                            brokenG= g.split(nBroke)
                            brokenG.maybeTrack("broken in storage")
                            brokenG.getType().recordBreakage(brokenG.getCount())
                            brokenList.append(brokenG)
                            unbrokenList.append(g)
                        else:
                            brokenList.append(g)
                    else:
                        unbrokenList.append(g)
                else:
                    unbrokenList.append(g) # Only shippables can break, not fixed refrigerators
        else:
            unbrokenList= groupList[:] # shallow copy
        return unbrokenList,brokenList
    
