#!/usr/bin/env python
__doc__=""" packagingmodel.py
This module implements classes which determine the behavior of warehouses
with respect to packaging- do they always ship full boxes, for example.
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

import ipath
import sys, types, math, random, util, unittest, cStringIO
import storagemodel
import abstractbaseclasses
from enums import StorageTypeEnums as ST

# Packaging categories, in increasing order of size.
PKG_SINGLE = 0
PKG_SMALLBOX = 1
PKG_BOX = 2
PKG_CARTON = 3 

pkgCategoryNames = {PKG_SINGLE:"single", PKG_SMALLBOX:"smallbox", PKG_BOX:"box", PKG_CARTON:"carton"}
pkgCategories = {"single":PKG_SINGLE, "smallbox":PKG_SMALLBOX, "box":PKG_BOX, "carton":PKG_CARTON}
pkgCategorySet = set(pkgCategories.values())

class PackagingModel:
    """
    A representation of the packaging policy of a CanOwn (e.g. a store or truck).  
    """
    def __init__(self):
        """
        This is the base class; the user is not expected to instantiate
        this type directly.
        """
        pass

    def __str__(self):
        return "<PackagingModel>"
    
    def applyPackagingRestrictions(self,shippableCollection):
        """
        This method applies the packaging policy embodied by this model to the given
        shippableCollection, and returns a new shippableCollection satisfying the
        restrictions.  For example, if the packaging policy forbids packages smaller 
        than PKG_BOX, all counts might be rounded up to that needed to fill an integral
        number of boxes of the associated ShippableType.
        """
        raise RuntimeError("PackagingModel.applyPackagingRestrictions called")
            
    def getStorageVolumeTriple(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given shippableCollection.  For example,
        if a given Shippable is stored at the 'box' level, any number of that shippable might be
        rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple (frozenVolCC,coolVolCC,warmVolCC).
        """
        raise RuntimeError("PackagingModel.getStorageVolumeTriple called")
    
    def getStorageVolumeSCTriple(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given shippableCollection as a triple of per-shippable
        collections.  For example, if a given Shippable is stored at the 'box' level, any number of that shippable 
        might be rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple of collections: (frozenVolVC,coolVolVC,warmVolVC).
        """
        raise RuntimeError("PackagingModel.getStorageVolumeSCTriple called")
    
    def getStorageVolumeHex(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given shippableCollection.  For example,
        if a given Shippable is stored at the 'box' level, any number of that shippable might be
        rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 6-element tuple (frozenOnlyVolCC,coolOnlyVolCC,warmOnlyVolCC,
        frozenCoolVolCC, coolWarmVolCC, anyVolCC).
        """
        raise RuntimeError("PackagingModel.getStorageVolumeHex called")
    
    def getStorageVolumeSCHex(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given shippableCollection as a triple of per-shippable
        collections.  For example, if a given Shippable is stored at the 'box' level, any number of that shippable 
        might be rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 6-element tuple of collections: (frozenOnlyVolVC,coolOnlyVolVC,
        warmOnlyVolVC, frozenCoolVolVC, coolWarmVolVC, anyVolVC).
        """
        raise RuntimeError("PackagingModel.getStorageVolumeSCHex called")
    
    def getNThatFit(self,volCC,shippableType, storageModel):
        """
        This method returns an integer count of the number of shippable instances
        of the given ShippableType which will fit in the given volume (in CC) under
        this packaging policy.
        """
        if volCC == 0.0: return 0
        elif isinstance(shippableType,abstractbaseclasses.CanStoreType):
            # Fridges are always stored as single units, without diluent, so we can
            # live without further details on packaging or the storage model.
            return int(math.floor(volCC/shippableType.getSingletonStorageVolume(False)))
        else:
            print 'failing on %s %s %s'%(volCC,shippableType,storageModel)
            raise RuntimeError("PackagingModel.getNThatFit called")

    def repackage(self, shippable):
        """
        Set the packaging of the given shippable to whatever is appropriate for the model.  This
        can change the effective size of the shippable.  The same shippable is returned for convenience.
        """
        raise RuntimeError("PackagingModel.repackage called")
    
    def sortToPackingOrder(self, trackableTypeList, storageModel):
        """
        Given a list of ShippableTypes, return a list of those types in packing order- that is, the first
        element of the list should be the first stored when filling new storage space, and the last in the
        list should be last stored.  For example, if packing singletons, one would typically organize them
        largest first.  The output list includes only ShippableType instances; bare TrackableType instances
        (like trucks non-shippable Fridges) are not copied from the input list.
        
        The base class has a not-completely-trivial implementation so that lists of refrigerators
        can be sorted in out-of-service trucks.  This can be triggered when the ice melts in a 
        PVSD and triggers reallocation of storage, for example.
        """
        if all([isinstance(v,abstractbaseclasses.CanStoreType) for v in trackableTypeList]):
            l= [(v.getSingletonStorageVolume(False),v) for v in trackableTypeList
                if isinstance(v,abstractbaseclasses.ShippableType)]
            l.sort(None,None,True)
            return [v for _,v in l]
        else:
            raise RuntimeError("PackagingModel.sortToPackingOrder can only handle fridges")
    
    def _getLargestForShippableType(self,shippableType):
        """
        Return value is a PackageType, or None representing the implied singleton package
        """
        raise RuntimeError("PackagingModel._getLargestForShippableType called")
        
"""
This model is only present to cover the need for a non-None PackagingModel for structures which are
not yet fully initialized.  If any of its methods are called, it should throw an exception.
"""
class DummyPackagingModel(PackagingModel):
    def __str__(self):
        return "<DummyPackagingModel>"
    def repackage(self, shippable):
        """
        Set the packaging of the given shippable to whatever is appropriate for the model.  This
        can change the effective size of the shippable.  The same shippable is returned for convenience.
        """
        if shippable.getCount() == 1:
            shippable.setPackageType(None)
            return shippable
        else:
            raise RuntimeError("DummyPackagingModel.repackage was asked to repackage a non-singleton.")
    
"""
This model assumes all packages can and should be broken down to the single vial level.
"""
class SimplePackagingModel(PackagingModel):
    """
    This model assumes all packages can and should be broken down to the single vial level.
    """
    def __init__(self):
        """
        This model assumes all packages can and should be broken down to the single vial level.
        """
        PackagingModel.__init__(self)
                                           
    def __str__(self):
        return "<SimplePackagingModel()>"
    
    def __repr__(self):
        return "SimplePackagingModel()"
    
    def applyPackagingRestrictions(self,shippableCollection):
        """
        This method applies the packaging policy embodied by this model to the given
        shippableCollection, and returns a new shippableCollection satisfying the
        restrictions.  For example, if the packaging policy forbids packages smaller 
        than PKG_BOX, all counts might be rounded up to that needed to fill an integral
        number of boxes of the associated ShippableType.

        This method implementation simply rounds up to the nearest integral number
        of single vials.
        """
        return shippableCollection.copy()
        #tL = [(v,math.ceil(n)) for v,n in shippableCollection.items()]
        #return shippableCollection.getSimilarCollection(tL)

    def getStorageVolumeTriple(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given trackableCollection.  For example,
        if a given Shippable is stored at the 'box' level, any number of that shippable might be
        rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple (frozenVolCC,coolVolCC,warmVolCC).
        
        This method assumes all shippables are broken down to the single vial level.
        """
        freezeCC = coolCC = warmCC = 0
        for v,n in trackableCollection.items():
            #dv = math.ceil(n)*v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
            if isinstance(v,abstractbaseclasses.ShippableType):
                dv = n*v.getSingletonStorageVolume(storageModel)
                #print 'coolTotalVol += %f for %s %s'%(dv,n,v.name)
                if storageModel.canStoreShippableType(v, ST.STORE_WARM): warmCC += dv
                elif storageModel.canStoreShippableType(v, ST.STORE_FREEZE): freezeCC += dv
                else: coolCC += dv
            else:
                # Non-Shippable objects like trucks and stationary fridges take up no space
                pass
        return (freezeCC, coolCC, warmCC)
    
    def getStorageVolumeSCTriple(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given shippableCollection as a triple of per-shippable
        collections.  For example, if a given Shippable is stored at the 'box' level, any number of that shippable 
        might be rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple of collections: (frozenVolVC,coolVolVC,warmVolVC).

        This method assumes all shippables are broken down to the single vial level.
        """
        freezeCC = coolCC = warmCC = 0
        freezeTuples = []
        coolTuples = []
        warmTuples = []
        for v,n in trackableCollection.items():
            #dv = math.ceil(n)*v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
            if isinstance(v,abstractbaseclasses.ShippableType):
                dv = n*v.getSingletonStorageVolume(storageModel)
                #print 'coolTotalVol += %f for %s %s'%(dv,n,v.name)
                if storageModel.canStoreShippableType(v, ST.STORE_WARM): warmCC += dv
                elif storageModel.canStoreShippableType(v, ST.STORE_FREEZE): freezeCC += dv
                if storageModel.canStoreShippableType(v, ST.STORE_WARM): warmTuples.append((v,dv))
                elif storageModel.canStoreShippableType(v, ST.STORE_FREEZE): freezeTuples.append((v,dv))
                else: coolTuples.append((v,dv))
            else:
                # Non-Shippable objects like trucks and stationary fridges take up no space
                pass
        return (trackableCollection.getSimilarCollection(freezeTuples),
                trackableCollection.getSimilarCollection(coolTuples),
                trackableCollection.getSimilarCollection(warmTuples))
                
    def getStorageVolumeHex(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given trackableCollection.  For example,
        if a given Shippable is stored at the 'box' level, any number of that shippable might be
        rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 6-element tuple (frozenVolCC, coolVolCC, warmVolCC, 
        frozenCoolVolCC, coolWarmVolCC, anyVolCC).
        
        This method assumes all shippables are broken down to the single vial level.
        """
        freezeCC = coolCC = warmCC = freezeCoolCC = coolWarmCC = anyCC = 0
        for v,n in trackableCollection.items():
            #dv = math.ceil(n)*v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
            if isinstance(v,abstractbaseclasses.ShippableType):
                dv = n*v.getSingletonStorageVolume(storageModel)
                #print 'coolTotalVol += %f for %s %s'%(dv,n,v.name)
                (warm, fridge, freeze) = [storageModel.canStoreShippableType(v, st) 
                                          for st in (ST.STORE_WARM, ST.STORE_COOL, ST.STORE_FREEZE)]
                if freeze and fridge and warm:
                    anyCC += dv
                elif freeze and fridge:
                    freezeCoolCC += dv
                elif fridge and warm:
                    coolWarmCC += dv
                elif warm:
                    warmCC += dv
                elif fridge:
                    coolCC += dv
                elif freeze:
                    freezeCC += dv
                else:  # apparently no storage method is viable
                    anyCC += dv
            else:
                # Non-Shippable objects like trucks and stationary fridges take up no space
                pass
        return (freezeCC, coolCC, warmCC, freezeCoolCC, coolWarmCC, anyCC)
    
    def getStorageVolumeSCHex(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given shippableCollection as a triple of per-shippable
        collections.  For example, if a given Shippable is stored at the 'box' level, any number of that shippable 
        might be rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple of collections: (frozenVolVC,coolVolVC,warmVolVC).

        This method assumes all shippables are broken down to the single vial level.
        """
        freezeTuples = []
        coolTuples = []
        warmTuples = []
        freezeCoolTuples = []
        coolWarmTuples = []
        anyTuples = []
        for v,n in trackableCollection.items():
            #dv = math.ceil(n)*v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
            if isinstance(v,abstractbaseclasses.ShippableType):
                dv = n*v.getSingletonStorageVolume(storageModel)

                #print 'coolTotalVol += %f for %s %s'%(dv,n,v.name)
                (warm, fridge, freeze) = [storageModel.canStoreShippableType(v, st) 
                                          for st in (ST.STORE_WARM, ST.STORE_COOL, ST.STORE_FREEZE)]
                if freeze and fridge and warm:
                    anyTuples.append((v, dv))
                elif freeze and fridge:
                    freezeCoolTuples.append((v, dv))
                elif fridge and warm:
                    coolWarmTuples.append((v, dv))
                elif warm:
                    warmTuples.append((v, dv))
                elif fridge:
                    coolTuples.append((v, dv))
                elif freeze:
                    freezeTuples.append((v, dv))
                else:  # apparently no storage method is viable
                    anyTuples.append((v, dv))
            else:
                # Non-Shippable objects like trucks and stationary fridges take up no space
                pass
        return (trackableCollection.getSimilarCollection(freezeTuples),
                trackableCollection.getSimilarCollection(coolTuples),
                trackableCollection.getSimilarCollection(warmTuples),
                trackableCollection.getSimilarCollection(freezeCoolTuples),
                trackableCollection.getSimilarCollection(coolWarmTuples),
                trackableCollection.getSimilarCollection(anyTuples))
                
    def getNThatFit(self,volCC,shippableType, storageModel):
        """
        This method returns an integer count of the number of shippable instances
        of the given ShippableType which will fit in the given volume (in CC) under
        this packaging policy.

        This method implementation assumes that all the shippables are stored as
        single items.
        """
        return int(math.floor(volCC/shippableType.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(shippableType))))

    def repackage(self, shippable):
        """
        Set the packaging of the given shippable to whatever is appropriate for the model.  This
        can change the effective size of the shippable.  The same shippable is returned for convenience.
        """
        shippable.setPackageType(None)
        return shippable

    def sortToPackingOrder(self, trackableTypeList, storageModel):
        """
        Given a list of ShippableTypes, return a list of those types in packing order- that is, the first
        element of the list should be the first stored when filling new storage space, and the last in the
        list should be last stored.  For example, if packing singletons, one would typically organize them
        largest first.  The output list includes only ShippableType instances; bare TrackableType instances
        (like trucks non-shippable Fridges) are not copied from the input list.
        """
        l= [(v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v)),v) 
            for v in trackableTypeList if isinstance(v,abstractbaseclasses.ShippableType)]
        l.sort(None,None,True)
        return [v for _,v in l]
        
    def _getLargestForShippableType(self,shippableType):
        """
        Return value is a PackageType, or None representing the implied singleton package
        """
        return None
        
"""
This model assumes all packages can and should be broken down to the single vial level.
"""
class ListPackagingModel(PackagingModel):
    """
    This packaging model includes a list of all shippables and their associated package types;
    any shippable not on the list is treated as if packaged in singletons.
    """
    def __init__(self, pkgTypeList):
        """
        pkgTypeList is a list of (shippableType,packageType) pairs.  ShippableTypes not given in the list
        are treated as if shipped as singletons.
        """
        PackagingModel.__init__(self)
        for sT,pT in pkgTypeList:
            assert isinstance(sT,abstractbaseclasses.ShippableType), \
                "% is not a ShippableType and so cannot be packaged"%sT.name
        self.pkgTypeDict = dict(pkgTypeList)
                                           
    def __str__(self):
        tokStr = "["
        first = True
        nameList = [(t.name,p.name) for t,p in self.pkgTypeDict.items()]
        nameList.sort()
        for tN,pN in nameList:
            if first:
                tokStr += "("+tN+","+pN+")"
                first = False
            else:
                tokStr += ",("+tN+","+pN+")"
        tokStr += "]"
        #return "<ListPackagingModel(%s)>"%[(t.name,p.name) for t,p in self.pkgTypeDict.items()]
        return "<ListPackagingModel("+tokStr+")>" 
    
    def __repr__(self):
        return "ListPackagingModel(%s)"%[(repr(t),repr(p)) for t,p in self.pkgTypeDict.items()]
    
    def applyPackagingRestrictions(self,shippableCollection):
        """
        This method applies the packaging policy embodied by this model to the given
        shippableCollection, and returns a new shippableCollection satisfying the
        restrictions.  For example, if the packaging policy forbids packages smaller 
        than PKG_BOX, all counts might be rounded up to that needed to fill an integral
        number of boxes of the associated ShippableType.

        This method implementation simply returns a copy of the original collection,
        essentially allowing single instances of all shippables.
        """
        tupleList = []
        #print 'filtering %s'%shippableCollection
        for v,n in shippableCollection.items():
            if v in self.pkgTypeDict: 
                nPer = self.pkgTypeDict[v].count
                nBoxes = math.ceil(float(n)/nPer)
                #print '%s implies %d becomes %d*%d=%d'%(self.pkgTypeDict[v].name,n,nPer,nBoxes,nPer*nBoxes)
                tupleList.append((v,nPer*nBoxes))
            else:
                tupleList.append((v,math.ceil(n)))
        return shippableCollection.getSimilarCollection(tupleList)
                
    def getStorageVolumeTriple(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given trackableCollection.  For example,
        if a given Shippable is stored at the 'box' level, any number of that shippable might be
        rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple (frozenVolCC,coolVolCC,warmVolCC).
        
        This method assumes all shippables are stored in completely filled packages, with leftovers 
        stored in the next package size down.
        """        
        freezeCC = coolCC = warmCC = 0.0
        for v,n in trackableCollection.items():
            if isinstance(v, abstractbaseclasses.ShippableType):
                if v in self.pkgTypeDict:
                    pT = self.pkgTypeDict[v]
                    dv = 0.0
                    while pT is not None and n>0:
                        nPkg = int(n/pT.count)
                        dv += nPkg * pT.volumeCC
                        n -= nPkg * pT.count
                        pT = pT.getNextSmaller()
                    dv += n * v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
                else:
                    dv = math.ceil(n)*v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
                if storageModel.canStoreShippableType(v, ST.STORE_WARM): warmCC += dv
                elif storageModel.canStoreShippableType(v, ST.STORE_FREEZE): freezeCC += dv
                else: coolCC += dv
            else:
                # Only Shippables have volume
                pass
        return (freezeCC, coolCC, warmCC)

    def getStorageVolumeSCTriple(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given shippableCollection as a triple of per-shippable
        collections.  For example, if a given Shippable is stored at the 'box' level, any number of that shippable 
        might be rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple of collections: (frozenVolVC,coolVolVC,warmVolVC).

        This method assumes all shippables are stored in completely filled packages, with leftovers 
        stored in the next package size down.
        """
        freezeCC = coolCC = warmCC = 0
        freezeTuples = []
        coolTuples = []
        warmTuples = []
        for v,n in trackableCollection.items():
            if isinstance(v,abstractbaseclasses.ShippableType):
                if v in self.pkgTypeDict:
                    pT = self.pkgTypeDict[v]
                    dv = 0.0
                    while pT is not None and n>0:
                        nPkg = int(n/pT.count)
                        dv += nPkg * pT.volumeCC
                        n -= nPkg * pT.count
                        pT = pT.getNextSmaller()
                    dv += n * v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
                else:
                    dv = math.ceil(n)*v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
                if storageModel.canStoreShippableType(v, ST.STORE_WARM): warmCC += dv
                elif storageModel.canStoreShippableType(v, ST.STORE_FREEZE): freezeCC += dv
                else: coolTuples.append((v,dv))
            else:
                # Non-Shippable objects like trucks and stationary fridges take up no space
                pass
        return (trackableCollection.getSimilarCollection(freezeTuples),
                trackableCollection.getSimilarCollection(coolTuples),
                trackableCollection.getSimilarCollection(warmTuples))

    def getStorageVolumeHex(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given trackableCollection.  For example,
        if a given Shippable is stored at the 'box' level, any number of that shippable might be
        rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple (frozenVolCC,coolVolCC,warmVolCC).
        
        This method assumes all shippables are stored in completely filled packages, with leftovers 
        stored in the next package size down.
        """        
        freezeCC = coolCC = warmCC = freezeCoolCC = coolWarmCC = anyCC = 0
        for v,n in trackableCollection.items():
            if isinstance(v, abstractbaseclasses.ShippableType):
                if v in self.pkgTypeDict:
                    pT = self.pkgTypeDict[v]
                    dv = 0.0
                    while pT is not None and n>0:
                        nPkg = int(n/pT.count)
                        dv += nPkg * pT.volumeCC
                        n -= nPkg * pT.count
                        pT = pT.getNextSmaller()
                    dv += n * v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
                else:
                    dv = math.ceil(n)*v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
                (warm, fridge, freeze) = [storageModel.canStoreShippableType(v, st) 
                                          for st in (ST.STORE_WARM, ST.STORE_COOL, ST.STORE_FREEZE)]
                if freeze and fridge and warm:
                    anyCC += dv
                elif freeze and fridge:
                    freezeCoolCC += dv
                elif fridge and warm:
                    coolWarmCC += dv
                elif warm:
                    warmCC += dv
                elif fridge:
                    coolCC += dv
                elif freeze:
                    coolCC += dv
                else:  # apparently no storage method is viable
                    anyCC += dv
            else:
                # Non-Shippable objects like trucks and stationary fridges take up no space
                pass
        return (freezeCC, coolCC, warmCC, freezeCoolCC, coolWarmCC, anyCC)

    def getStorageVolumeSCHex(self, trackableCollection, storageModel):
        """
        This method calculates the storage volume of the given shippableCollection as a triple of per-shippable
        collections.  For example, if a given Shippable is stored at the 'box' level, any number of that shippable 
        might be rounded up to the nearest box, to simulate that fact that the storage area may contain 
        partially-full boxes.  The return value is a 3-element tuple of collections: (frozenVolVC,coolVolVC,warmVolVC).

        This method assumes all shippables are stored in completely filled packages, with leftovers 
        stored in the next package size down.
        """
        freezeTuples = []
        coolTuples = []
        warmTuples = []
        freezeCoolTuples = []
        coolWarmTuples = []
        anyTuples = []
        for v,n in trackableCollection.items():
            if isinstance(v,abstractbaseclasses.ShippableType):
                if v in self.pkgTypeDict:
                    pT = self.pkgTypeDict[v]
                    dv = 0.0
                    while pT is not None and n>0:
                        nPkg = int(n/pT.count)
                        dv += nPkg * pT.volumeCC
                        n -= nPkg * pT.count
                        pT = pT.getNextSmaller()
                    dv += n * v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
                else:
                    dv = math.ceil(n)*v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v))
                (warm, fridge, freeze) = [storageModel.canStoreShippableType(v, st) 
                                          for st in (ST.STORE_WARM, ST.STORE_COOL, ST.STORE_FREEZE)]
                if freeze and fridge and warm:
                    anyTuples.append((v, dv))
                elif freeze and fridge:
                    freezeCoolTuples.append((v, dv))
                elif fridge and warm:
                    coolWarmTuples.append((v, dv))
                elif warm:
                    warmTuples.append((v, dv))
                elif fridge:
                    coolTuples.append((v, dv))
                elif freeze:
                    freezeTuples.append((v, dv))
                else:  # apparently no storage method is viable
                    anyTuples.append((v, dv))
            else:
                # Non-Shippable objects like trucks and stationary fridges take up no space
                pass
        return (trackableCollection.getSimilarCollection(freezeTuples),
                trackableCollection.getSimilarCollection(coolTuples),
                trackableCollection.getSimilarCollection(warmTuples),
                trackableCollection.getSimilarCollection(freezeCoolTuples),
                trackableCollection.getSimilarCollection(coolWarmTuples),
                trackableCollection.getSimilarCollection(anyTuples))
            
    def getNThatFit(self,volCC,shippableType, storageModel):
        """
        This method returns an integer count of the number of shippable instances
        of the given ShippableType which will fit in the given volume (in CC) under
        this packaging policy.

        If a packageType has been specified for the given shippableType, the return
        value will be an integral number of boxes' worth of the shippableType.  Otherwise,
        capacity is based on individual units of the shippable.
        """
        if shippableType in self.pkgTypeDict:
            pT = self.pkgTypeDict[shippableType]
            nBoxes = int(math.floor(volCC/pT.volumeCC))
            return pT.count*nBoxes
        else:
            return int(math.floor(volCC/shippableType.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(shippableType))))

    def repackage(self, shippable):
        """
        Set the packaging of the given shippable to whatever is appropriate for the model.  This
        can change the effective size of the shippable.  The same shippable is returned for convenience.
        """
        if shippable.getType() in self.pkgTypeDict:
            shippableCount = shippable.getCount()
            pT = self.pkgTypeDict[shippable.getType()]
            while pT is not None and pT.count > shippableCount: 
                pT = pT.getNextSmaller()
            shippable.setPackageType(pT)
        else:
            shippable.setPackageType(None) #implied singleton package
        return shippable
    
    def sortToPackingOrder(self,trackableTypeList, storageModel):
        """
        Given a list of ShippableTypes, return a list of those types in packing order- that is, the first
        element of the list should be the first stored when filling new storage space, and the last in the
        list should be last stored.  For example, if packing singletons, one would typically organize them
        largest first.  The output list includes only ShippableType instances; bare TrackableType instances
        (like trucks non-shippable Fridges) are not copied from the input list.
        """
        sortList = []
        for v in [t for t in trackableTypeList if isinstance(t,abstractbaseclasses.ShippableType)]:
            if v in self.pkgTypeDict: sortList.append((self.pkgTypeDict[v].volumeCC,v))
            else: sortList.append((v.getSingletonStorageVolume(storageModel.getStoreVaccinesWithDiluent(v)),v))
        sortList.sort(None,None,True)
        return [v for s,v in sortList]
        
    def _getLargestForShippableType(self,shippableType):
        """
        Return value is a PackageType, or None representing the implied singleton package
        """
        if shippableType in self.pkgTypeDict:
            return self.pkgTypeDict[shippableType]
        else:
            return None
        
class PackagingModelMergerModel:
    """
    It is sometimes necessary to figure out an aggregate packaging model from a collection of other models- 
    for example when multiple clients in a shipping loop collectively determine the packaging model for the
    loop as a whole.  This class provides a mechanism to manage that merger.
    """
    def __init__(self,sim):
        self.sim = sim
        self.noSmallerPkgMap = {}
        self.noLargerPkgMap = {}
    
    def __str__(self):
        return "<PackagingModelMergerModel>"
    
    def addDownstreamPackagingModel(self,packagingModel):
        """
        Add the given packagingModel as a downstream client of the merged model.
        """
        for s in self.sim.shippables.getActiveTypes():
            pT = packagingModel._getLargestForShippableType(s)
            if pT is not None:
                if s not in self.noSmallerPkgMap or pT.count > self.noSmallerPkgMap[s].count:
                    self.noSmallerPkgMap[s] = pT

    def addUpstreamPackagingModel(self,packagingModel):
        """
        Add the given packagingModel as an upstream supplier of the merged model.
        """
        for s in self.sim.shippables.getActiveTypes():
            pT = packagingModel._getLargestForShippableType(s)
            if pT is None:
                self.noLargerPkgMap[s] = None
            else:
                if pT not in self.noLargerPkgMap or pT.count<self.noLargerPkgMap[s]:
                    self.noLargerPkgMap[s] = pT
    
    def getNetPackagingModel(self):
        pairList = self.noSmallerPkgMap.items()
        tweakedPairList = []
        for s,p in pairList:
            if s in self.noLargerPkgMap:
                if p.count <= self.noLargerPkgMap[s].count:
                    tweakedPairList.append((s,p))
                else:
                    tweakedPairList.append((s,self.noLargerPkgMap[s]))
            else:
                tweakedPairList.append((s,p))
        if len(tweakedPairList) > 0:
            return ListPackagingModel(tweakedPairList)
        else:
            return SimplePackagingModel()


def describeSelf():
    print \
"""
Testing options:

  testPackageConstruction
  
     runs a test of the process by which packages are associated with their shippables
     
  testSimple

     runs a test of SimplePackagingModel

  testList

     runs a test of ListPackagingModel
     
  testMerge
  
     runs a test of PackagingModelMergerModel

"""
        
def main(myargv=None):
    "Provides a few test routines"
    import globals
    import sampler
    import typemanager
    import storagetypes
    import peopletypes
    from peopletypes import genericPeopleTypeName
    import trackabletypes
    import trucktypes
    import vaccinetypes
    import icetypes
    import packagetypes
    import input
    globals.deterministic = True

    class _mockSim:
        """
        This is used to mock the sim parameter needed by DemandModels during testing.
        """
        def __init__(self):
            self.userInput = input.UserInput()
            self.typeManager= typemanager.TypeManager([], verbose=False, debug=False, sim=self)
            tms = {}

            for rec in [{"Name":stn} for stn in storagetypes.storageTypeNames]: 
                self.typeManager.addType(rec, storagetypes.StorageType, False, False)
            self.storage= storagetypes.StorageTypeManager(self.typeManager)
            # Force the storage type names to be active; they are needed in parsing files below.
            for stn in storagetypes.storageTypeNames: self.storage.getTypeByName(stn)
            tms['storage'] = self.storage

            self.buildTypeRecords([{"Name":"People1","SortOrder":1,"Notes":""},
                                   {"Name":"People2","SortOrder":2,"Notes":""},
                                   {"Name":"People3","SortOrder":3,"Notes":""},
                                   {"Name":"People4","SortOrder":4,"Notes":""},
                                   {"Name":genericPeopleTypeName,"SortOrder":4,"Notes":""}],
                                   peopletypes.PeopleType)
            tms['people'] = self.people = peopletypes.PeopleTypeManager(self.typeManager)
            
            self.buildTypeRecords([{'Name':'VAC1_Box', 'Contains':'VAC1', 'Count':25, 'Category':'box',
                                    'Volume(CC)':66.00, 'SortOrder':2, 'Notes':''},
                                   {'Name':'VAC1_Carton', 'Contains':'VAC1', 'Count':2000, 'Category':'carton',
                                    'Volume(CC)':5300.00, 'SortOrder':3, 'Notes':''},                                    
                                   {'Name':'VAC2_Box', 'Contains':'VAC2', 'Count':50, 'Category':'box',
                                    'Volume(CC)':400.00, 'SortOrder':102, 'Notes':''},
                                   {'Name':'VAC3_Carton', 'Contains':'VAC3', 'Count':1000, 'Category':'carton',
                                     'Volume(CC)':25000.00, 'SortOrder':203, 'Notes':''}],                                    
                                   packagetypes.PackageType)
            
            tms['packaging'] = packagetypes.PackageTypeManager(self.typeManager)

            self.typeManager.addType({"Name":"default", "CoolVolumeCC":1.0e9, "Note":"default truck type"},
                                     trucktypes.TruckType, False, False)
            tms['trucks'] = self.trucks = trucktypes.TruckTypeManager(self.typeManager)
            
            tms['shippables'] = self.shippables = trackabletypes.TrackableTypeManager(self.typeManager)
            
            self.shippables.importRecords([([{"Name":"VAC1","DisplayName":"V1",
                                              "Doses per vial":2,"Packed vol/dose(cc) of vaccine":1.23,
                                              "Packed vol/dose(cc) of diluent":4.46,"Doses/person":1,"LifetimeFreezerDays":1.23,
                                              "LifetimeCoolerDays":672,"LifetimeRoomTempDays":0.02,"LifetimeOpenDays":0.25,
                                              "RandomKey":1000},
                                             {"Name":"VAC2","DisplayName":"V2",
                                              "Doses per vial":5,"Packed vol/dose(cc) of vaccine":1.23,
                                              "Packed vol/dose(cc) of diluent":4.46,"Doses/person":2,"LifetimeFreezerDays":1.23,
                                              "LifetimeCoolerDays":672,"LifetimeRoomTempDays":0.02,"LifetimeOpenDays":0.25,
                                              "RandomKey":1000},
                                             {"Name":"VAC3","DisplayName":"V3",
                                              "Doses per vial":10,"Packed vol/dose(cc) of vaccine":1.23,
                                              "Packed vol/dose(cc) of diluent":4.46,"Doses/person":3,"LifetimeFreezerDays":1.23,
                                              "LifetimeCoolerDays":672,"LifetimeRoomTempDays":0.02,"LifetimeOpenDays":0.25,
                                              "RandomKey":1000},
                                             {"Name":"VAC4","DisplayName":"V4",
                                              "Doses per vial":20,"Packed vol/dose(cc) of vaccine":1.23,
                                              "Packed vol/dose(cc) of diluent":4.46,"Doses/person":4,"LifetimeFreezerDays":600.0,
                                              "LifetimeCoolerDays":672,"LifetimeRoomTempDays":0.02,"LifetimeOpenDays":0.25,
                                              "RandomKey":1000}],
                                              vaccinetypes.VaccineType,vaccinetypes.DeliverableVaccineType)])

            tms['vaccines'] = self.vaccines = vaccinetypes.VaccineTypeManager(self.typeManager)
            tms['ice'] = self.ice= icetypes.IceTypeManager(self.typeManager)
            tms['fridges'] = self.fridges= None # to avoid a dependency on userInput in the constructor
            for name in tms['packaging'].getAllValidTypeNames():
                pkgType = tms['packaging'].getTypeByName(name,activateFlag=False)
                tms['shippables'].getTypeByName(pkgType.containsStr, activateFlag=False).addPackageType(pkgType)
             
            self.typeManagers = tms
            
            self.staticDemand = False
            self.randomRounder = util.RandomRounder(1234)
            self.verbose = False
            self.debug = False
            self.uniqueIdDict = {}

        def buildTypeRecords(self, recList, whatType):
            for rec in recList: self.typeManager.addType(rec, whatType, False, False)

        def getUniqueString(self, base):
            """
            This is used by various components to generate names, primarily for debugging.  
            If called with base='foo' (for example), it will return first 'foo0', then 'foo1',
            etc.
            """
            if not self.uniqueIdDict.has_key(base):
                self.uniqueIdDict[base]= 0
            retVal= "%s%d"%(base,self.uniqueIdDict[base])
            self.uniqueIdDict[base] += 1
            return retVal
        
        def now(self):
            return 1.2345

    def stringFromVC(vc):
        if vc is None:
            return "None"
        else:
            l = [(v.name,v) for v in vc.keys()]
            l.sort()
            l = [v for name,v in l]
            s = ""
            for v in l: s += "%s:%s,"%(v.name,vc[v])
            if len(s): s= s[:-1]
            return s

    def testPackagingModel(p):
        for v in sim.vaccines.getActiveTypes(): v.randSeed(1234)
        sM = storagemodel.StorageModel(False)
        print "str: %s"%str(p)
        print "repr: %s"%repr(p)
        tL = [('VAC1',1.0),('VAC2',2.0),('VAC3',3.5), ('VAC4',4.1)]
        l = [(sim.shippables.getTypeByName(name),ct) for name,ct in tL]
        sC = sim.shippables.getCollection(l)
        print "input sC: %s"%stringFromVC(sC)
        print "volume of individual units: %s"%[(name,sim.shippables.getTypeByName(name).getSingletonStorageVolume(sM))
                                                for name,ct in tL]
        print "output of applyPackingRestrictions: %s"%stringFromVC(p.applyPackagingRestrictions(sC))
        print "output of getStorageVolumeTriple: %f %f %f"%p.getStorageVolumeTriple(sC, sM)
        print "output of getStorageVolumeSCTriple: %s %s %s"%p.getStorageVolumeSCTriple(sC, sM)
        print "num that fit in 9999.5 CC: %s"%[(sN,p.getNThatFit(9999.5,sim.shippables.getTypeByName(sN),sM)) 
                                              for sN in ['VAC1', 'VAC2', 'VAC3', 'VAC4']]
        for name,ct in [('VAC1',400),('VAC2',600),('VAC3',100)]:
            groupedShippable = sim.shippables.getTypeByName(name).createInstance(ct)
            pTBefore = groupedShippable.getPackageType()
            assert p.repackage(groupedShippable) == groupedShippable , "p.repackage failed to return its argument"
            pTAfter = groupedShippable.getPackageType()
            print 'repackage changed the package type of %s from %s to %s'%(groupedShippable,pTBefore,pTAfter)
        unsortedTypes = [sim.shippables.getTypeByName(name) for name,ct in tL]
        sortedTypes = p.sortToPackingOrder(unsortedTypes,sM)
        print 'sortToPackingOrder changed %s to %s'%([v.name for v in unsortedTypes],[v.name for v in sortedTypes])

    if myargv is None: 
        myargv = sys.argv
        
    sim = _mockSim()
    random.seed(1234)
    if len(myargv)<2:
        describeSelf()
    elif myargv[1]=="testPackageConstruction":
        sM = storagemodel.StorageModel(False)
        if len(myargv)==2:
            for vName in ['VAC1','VAC2','VAC3','VAC4']:
                v = sim.vaccines.getTypeByName(vName)
                print "For shippable %s with unit size %f:"%(vName, v.getSingletonStorageVolume(sM))
                pList = v.getPackageTypeList()
                if len(pList) > 0:
                    for p in pList: print "   %s"%p.summarystring()
                else:
                    print '   None'
        else:
            print "Wrong number of arguments!"
            describeSelf()        
    elif myargv[1]=="testSimple":
        if len(myargv)==2:
            p = SimplePackagingModel()
            testPackagingModel(p)
        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=="testList":
        if len(myargv)==2:
            tL = [(sim.typeManager.getTypeByName(vN), sim.typeManager.getTypeByName(pN)) 
                  for vN,pN in [('VAC1','VAC1_Carton'),('VAC2','VAC2_Box')]]
            p = ListPackagingModel(tL)
            testPackagingModel(p)
        else:
            print "Wrong number of arguments!"
            describeSelf()
    elif myargv[1]=='testMerge':
        if len(myargv)==2:
            tL = [(sim.typeManager.getTypeByName(vN), sim.typeManager.getTypeByName(pN)) 
                  for vN,pN in [('VAC1','VAC1_Carton'),('VAC2','VAC2_Box')]]
            p1 = ListPackagingModel(tL)
            tL = [(sim.typeManager.getTypeByName(vN), sim.typeManager.getTypeByName(pN)) 
                  for vN,pN in [('VAC3','VAC3_Carton'),('VAC2','VAC2_Box'),('VAC1','VAC1_Box')]]
            p2 = ListPackagingModel(tL)
            p3 = SimplePackagingModel()
            pMMM = PackagingModelMergerModel(sim)
            pMMM.addDownstreamPackagingModel(p1)
            print "Merge 1 downstream: %s"%pMMM.getNetPackagingModel()
            pMMM.addDownstreamPackagingModel(p3)
            print "Merge 3 downstream: %s"%pMMM.getNetPackagingModel()
            pMMM.addUpstreamPackagingModel(p2)
            print "Merge 2 upstream: %s"%pMMM.getNetPackagingModel()
            pMMM.addDownstreamPackagingModel(p2)
            print "Merge 2 downstream: %s"%pMMM.getNetPackagingModel()
        else:
            print "Wrong number of arguments!"
            describeSelf()
    else:
        describeSelf()

class TestPackagingModels(unittest.TestCase):
    def getReadBackBuf(self, wordList):
        try:
            sys.stdout = myStdout = cStringIO.StringIO()
            main(wordList)
        finally:
            sys.stdout = sys.__stdout__
        return cStringIO.StringIO(myStdout.getvalue())

    def compareOutputs(self, correctStr, readBack):
        correctRecs = cStringIO.StringIO(correctStr)
        for a,b in zip(readBack.readlines(), correctRecs.readlines()):
            #print "<%s> vs. <%s>"%(a,b)
            if a.strip() != b.strip(): 
                print "\nExpected <%s>"%b
                print "     Got <%s>"%a
            self.assertTrue(a.strip() == b.strip())
    
    def test_Build(self):
        correctStr = """For shippable VAC1 with unit size 2.460000:
   VAC1_Carton: contains 2000 of VAC1, volume 5300.000000
   VAC1_Box: contains 25 of VAC1, volume 66.000000
For shippable VAC2 with unit size 6.150000:
   VAC2_Box: contains 50 of VAC2, volume 400.000000
For shippable VAC3 with unit size 12.300000:
   VAC3_Carton: contains 1000 of VAC3, volume 25000.000000
For shippable VAC4 with unit size 24.600000:
   None

        """
        readBack= self.getReadBackBuf(['dummy','testPackageConstruction'])
        self.compareOutputs(correctStr, readBack)
        
    def test_Simple(self):
        correctStr = """str: <SimplePackagingModel()>
repr: SimplePackagingModel()
input sC: VAC1:1.0,VAC2:2.0,VAC3:3.5,VAC4:4.1
volume of individual units: [('VAC1', 2.46), ('VAC2', 6.15), ('VAC3', 12.3), ('VAC4', 24.6)]
output of applyPackingRestrictions: VAC1:1.0,VAC2:2.0,VAC3:3.5,VAC4:4.1
output of getStorageVolumeTriple: 100.860000 57.810000 0.000000
output of getStorageVolumeSCTriple: <ManagedCollection(VAC4:100.86)> <ManagedCollection(VAC3:43.05,VAC2:12.3,VAC1:2.46)> <ManagedCollection()>
num that fit in 9999.5 CC: [('VAC1', 4064), ('VAC2', 1625), ('VAC3', 812), ('VAC4', 406)]
repackage changed the package type of <VaccineGroup(400,VAC1,cooler,None,vg0,0x1,0.0)> from None to None
repackage changed the package type of <VaccineGroup(600,VAC2,cooler,None,vg1,0x1,0.0)> from None to None
repackage changed the package type of <VaccineGroup(100,VAC3,cooler,None,vg2,0x1,0.0)> from None to None
sortToPackingOrder changed ['VAC1', 'VAC2', 'VAC3', 'VAC4'] to ['VAC4', 'VAC3', 'VAC2', 'VAC1']
        """
        readBack= self.getReadBackBuf(['dummy','testSimple'])
        self.compareOutputs(correctStr, readBack)

    def test_List(self):
        correctStr = """str: <ListPackagingModel([(VAC1,VAC1_Carton),(VAC2,VAC2_Box)])>
repr: ListPackagingModel([('<VaccineType(VAC1,2,1.23,1,[<StorageType(cooler)>, <StorageType(freezer)>, <StorageType(roomtemperature)>],546.341,1,33600,2688,672)>', '<PackageType(VAC1_Carton,2000.000000)>'), ('<VaccineType(VAC2,5,1.23,2,[<StorageType(cooler)>, <StorageType(freezer)>, <StorageType(roomtemperature)>],546.341,1,33600,2688,672)>', '<PackageType(VAC2_Box,50.000000)>')])
input sC: VAC1:1.0,VAC2:2.0,VAC3:3.5,VAC4:4.1
volume of individual units: [('VAC1', 2.46), ('VAC2', 6.15), ('VAC3', 12.3), ('VAC4', 24.6)]
output of applyPackingRestrictions: VAC1:2000.0,VAC2:50.0,VAC3:4.0,VAC4:5.0
output of getStorageVolumeTriple: 123.000000 63.960000 0.000000
output of getStorageVolumeSCTriple: <ManagedCollection(VAC4:123)> <ManagedCollection(VAC3:49.2,VAC2:12.3,VAC1:2.46)> <ManagedCollection()>
num that fit in 9999.5 CC: [('VAC1', 2000), ('VAC2', 1200), ('VAC3', 812), ('VAC4', 406)]
repackage changed the package type of <VaccineGroup(400,VAC1,cooler,VAC1_Box,vg0,0x1,0.0)> from None to VAC1_Box
repackage changed the package type of <VaccineGroup(600,VAC2,cooler,VAC2_Box,vg1,0x1,0.0)> from None to VAC2_Box
repackage changed the package type of <VaccineGroup(100,VAC3,cooler,None,vg2,0x1,0.0)> from None to None
sortToPackingOrder changed ['VAC1', 'VAC2', 'VAC3', 'VAC4'] to ['VAC1', 'VAC2', 'VAC4', 'VAC3']
        """
        readBack= self.getReadBackBuf(['dummy','testList'])
        self.compareOutputs(correctStr, readBack)

    def test_Merge(self):
        correctStr = """Merge 1 downstream: <ListPackagingModel([(VAC1,VAC1_Carton),(VAC2,VAC2_Box)])>
Merge 3 downstream: <ListPackagingModel([(VAC1,VAC1_Carton),(VAC2,VAC2_Box)])>
Merge 2 upstream: <ListPackagingModel([(VAC1,VAC1_Box),(VAC2,VAC2_Box)])>
Merge 2 downstream: <ListPackagingModel([(VAC1,VAC1_Box),(VAC2,VAC2_Box),(VAC3,VAC3_Carton)])>
        """
        readBack= self.getReadBackBuf(['dummy','testMerge'])
        self.compareOutputs(correctStr, readBack)

############
# Main hook
############

if __name__=="__main__":
    main()
      
