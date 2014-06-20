#!/usr/bin/env python
__doc__=""" storagemodel.py
This module implements classes which determine the behavior of CanOwn instances
with respect to storage- do they store diluent with vaccine or at room temperature,
or example.
"""

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

_hermes_svn_id_="$Id$"

import sys, types, math, random, util, unittest, cStringIO
import abstractbaseclasses

class StorageModel:
    """
    A representation of the storage policy of a CanOwn (e.g. a store or truck).  
    """
    def __init__(self,storeDiluentWithVaccines):
        """
        This is the base class; the user is not expected to instantiate
        this type directly.
        """
        self.storeDiluentWithVaccines = storeDiluentWithVaccines

    def __str__(self):
        return "<StorageModel>"
    
    def getStoreVaccinesWithDiluent(self,shippableType):
        """
        Return true if the diluent for this shippableType is to be stored with the shippable.
        """
        return self.storeDiluentWithVaccines
    
    def getShippableTypeStoragePriorityList(self,shippableType):
        """
        Filter the natural storage priority list for the shippableType according to the
        StorageModel.  For example, diluents can normally be stored warm, but at clinics
        they are typically stored with the associated vaccine and thus must be stored
        cold.
        """
        if self.storeDiluentWithVaccines:
            rBL = shippableType.getRequiredByList()
            if len(rBL) == 0: 
                # This is an actual deliverable
                return shippableType.getStoragePriorityList()
            else:
                # 'storeDiluentWithVaccines' is interpreted to mean 'store this diluent like it were vaccine'
                return rBL[0].getStoragePriorityList()
        else:
            return shippableType.getStoragePriorityList()
    
    def canFreezeShippableType(self, shippableType):
        """
        Filter the natural 'canFreeze' attribute of the shippableType according to the
        StorageModel.  
        """
        if self.storeDiluentWithVaccines:
            rBL = shippableType.getRequiredByList()
            if len(rBL) == 0: 
                # This is an actual deliverable
                return shippableType.canFreeze()
            else:
                # 'storeDiluentWithVaccines' is interpreted to mean 'store this diluent like it were vaccine'
                return rBL[0].canFreeze()
        else:
            return shippableType.canFreeze()
    
    def canLeaveOutShippableType(self, shippableType):
        """
        Filter the natural 'canLeaveOut' attribute of the shippableType according to the
        StorageModel
        """
        if self.storeDiluentWithVaccines:
            rBL = shippableType.getRequiredByList()
            if len(rBL) == 0: 
                # This is an actual deliverable
                return shippableType.canLeaveOut()
            else:
                # 'storeDiluentWithVaccines' is interpreted to mean 'store this diluent like it were vaccine'
                return rBL[0].canLeaveOut()
        else:
            return shippableType.canLeaveOut()
    
class DummyStorageModel(StorageModel):
    """
    This derived class exists for cases where we need to provide a StorageModel, but
    where it should never actually be used.  For example, an AttachedClinic must by
    definition have a StorageModel, but any access should go through its host Warehouse.
    """
    def __init__(self):
        StorageModel.__init__(self,False)
        
    def getStoreVaccinesWithDiluent(self,vaccineType):
        """
        For special cases involving the shuffling of empty fridges, we special-case the rule
        that fridges are always stored without diluent.  (They don't have diluent anyway).  
        Otherwise, this StorageModel should never be called.
        """
        if isinstance(vaccineType,abstractbaseclasses.CanStoreType):
            return False
        else:
            raise RuntimeError("Attempt to access dummyStorageModel.getStoreVaccinesWithDiluent")
    
      