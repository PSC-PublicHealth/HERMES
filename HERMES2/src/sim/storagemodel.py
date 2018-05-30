#!/usr/bin/env python
__doc__=""" storagemodel.py
This module implements classes which determine the behavior of CanOwn instances
with respect to storage- do they store diluent with vaccine or at room temperature,
or example.
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

import sys, types, math, random, util, unittest, cStringIO
import abstractbaseclasses

class StorageModel:
    """
    A representation of the storage policy of a CanOwn (e.g. a store or truck).  
    """
    def __init__(self,storeDiluentWithVaccines):
        """
        This is the base class.  We are using it as the primary class
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
    
    def canStoreShippableType(self, shippableType, storageType):
        """
        return whether a specific shippable type _can_ be reasonably stored in a specific storageType.
        (there may be better places to store the shippable but if this returns true it shouldn't be
        bad to store it in this type)
        """
        if self.storeDiluentWithVaccines:
            rBL = shippableType.getRequiredByList()
            if len(rBL) == 0: 
                # This is an actual deliverable
                return shippableType.canStore(storageType)
            else:
                # 'storeDiluentWithVaccines' is interpreted to mean 'store this diluent like it were vaccine'
                return rBL[0].canStore(storageType)
        else:
            return shippableType.canStore(storageType)



    def wantStoreShippableType(self, shippableType, storageType):
        """
        return whether a specific shippable type prefers to be stored in a specific storageType.  
        If this returns true then this should be a nearly optimal storage type for this shippable.
        """
        if self.storeDiluentWithVaccines:
            rBL = shippableType.getRequiredByList()
            if len(rBL) == 0: 
                # This is an actual deliverable
                return shippableType.wantStore(storageType)
            else:
                # 'storeDiluentWithVaccines' is interpreted to mean 'store this diluent like it were vaccine'
                return rBL[0].wantStore(storageType)
        else:
            return shippableType.wantStore(storageType)


    def preferredStoreShippableType(self, shippableType):
        """
        return whether a specific shippable type prefers to be stored in a specific storageType.  
        If this returns true then this should be a nearly optimal storage type for this shippable.
        """
        if self.storeDiluentWithVaccines:
            rBL = shippableType.getRequiredByList()
            if len(rBL) == 0: 
                # This is an actual deliverable
                return shippableType.preferred()
            else:
                # 'storeDiluentWithVaccines' is interpreted to mean 'store this diluent like it were vaccine'
                return rBL[0].preferredStore()
        else:
            return shippableType.preferredStore()


    
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
    
      
class AvoidWarmStorageModel(StorageModel):
    """
    This derived class exists for cases where we need to provide a StorageModel, but
    where it should never actually be used.  For example, an AttachedClinic must by
    definition have a StorageModel, but any access should go through its host Warehouse.
    """
    def __init__(self,storeDiluentWithVaccines):
        StorageModel.__init__(self,storeDiluentWithVaccines)

        # cache this
#        self.warmStorage = typeManager.getTypeByName("roomtemperature")

    
    def getShippableTypeStoragePriorityList(self,shippableType):
        """
        Filter the natural storage priority list for the shippableType according to the
        StorageModel.  For example, diluents can normally be stored warm, but at clinics
        they are typically stored with the associated vaccine and thus must be stored
        cold.
        """
        warmStorage = shippableType.sim.typeManager.getTypeByName("roomtemperature")
        pList = StorageModel.getShippableTypeStoragePriorityList(self, shippableType)

        ret = []
        found = False
        for st in pList:
            if st is warmStorage:
                found = True
                continue
            ret.append(st)
        if found:
            ret.append(warmStorage)

        return ret
            

    def canStoreShippableType(self, shippableType, storageType):
        """
        return whether a specific shippable type _can_ be reasonably stored in a specific storageType.
        (there may be better places to store the shippable but if this returns true it shouldn't be
        bad to store it in this type)
        """

        if storageType == 'roomtemperature':
            return False
        return StorageModel.canStoreShippableType(self, shippableType, storageType)


    def wantStoreShippableType(self, shippableType, storageType):
        """
        return whether a specific shippable type prefers to be stored in a specific storageType.  
        If this returns true then this should be a nearly optimal storage type for this shippable.
        """
        if storageType == 'roomtemperature':
            return False
        return StorageModel.wantStoreShippableType(self, shippableType, storageType)


    def preferredStoreShippableType(self, shippableType):
        """
        return whether a specific shippable type prefers to be stored in a specific storageType.  
        If this returns true then this should be a nearly optimal storage type for this shippable.
        """
        if storageType == 'roomtemperature':
            return False
        return StorageModel.preferredStoreShippableType(self, shippableType, storageType)
        
