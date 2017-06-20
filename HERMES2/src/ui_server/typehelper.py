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

__doc__ = """typehelper
This module provides routines to generate information about managed types, including support for
fallback to the AllTypesModel.
"""
_hermes_svn_id_="$Id: typehelper.py 2315 2015-07-29 22:25:46Z stbrown $"

import types
from collections import defaultdict
import ipath
import shadow_network_db_api
from typeholdermodel import allTypesModelName

from HermesServiceException import HermesServiceException

from ui_utils import _logMessage, _logStacktrace

import shadow_network
import i18n
from model import parseInventoryString

inlizer = i18n.i18n('locale')
_ = inlizer.translateString

hiddenTypesSet = set(['OUTDOORS'])

alwaysPresentTypes = defaultdict(lambda: [],
                                 {'staff': ['Std_WarehouseStaff', 'Std_Driver'],
                                  'perdiems': ['Std_PerDiem_None'],
                                  'types': ['Std_WarehouseStaff', 'Std_Driver', 'Std_PerDiem_None']
                                  })

# The following typenames are used elsewhere and should be considered reserved
specialTypeNames = {'no-perdiem': 'Std_PerDiem_None'
                    }


def _getAllTypesModel(db):
    return (db.query(shadow_network.ShdNetwork)
            .filter(shadow_network.ShdNetwork.name == allTypesModelName).one())


def getAllTypesModel(db):
    return _getAllTypesModel(db)


def getTypeList(db, modelId, typeClass, fallback=True):
    """
    typeClass must be a valid entry in the types.typeClass polymorphic database table.
    """

    m = shadow_network_db_api.ShdNetworkDB(db, modelId)
    # Insert some special case types if absent
    for nm in alwaysPresentTypes[typeClass]:
        if nm not in getattr(m, typeClass):
            addTypeToModel(db, m, nm, srcModel=None, force=True)
    names = set()
    tList = []
    for k, v in getattr(m, typeClass).items():
        if k in hiddenTypesSet:
            continue
        names.add(k)
        attrRec = {'_inmodel': True, 'modelId': modelId}
        shadow_network._copyAttrsToRec(attrRec, v)
        tList.append(attrRec)
    if fallback:
        aM = _getAllTypesModel(db)
        for k, v in getattr(aM, typeClass).items():
            if k in hiddenTypesSet:
                continue
            if k not in names:
                names.add(k)
                attrRec = {'_inmodel': False, 'modelId': aM.modelId}
                shadow_network._copyAttrsToRec(attrRec, v)
                tList.append(attrRec)
    return tList


def checkTypeDependencies(db, oldModelOrModelId, newModelOrModelId, typeName):
    if oldModelOrModelId is None:
        oM = _getAllTypesModel(db)
    elif isinstance(oldModelOrModelId, types.IntType):
        oM = shadow_network_db_api.ShdNetworkDB(db, oldModelOrModelId)
    else:
        oM = oldModelOrModelId
    if isinstance(newModelOrModelId, types.IntType):
        nM = shadow_network_db_api.ShdNetworkDB(db, newModelOrModelId)
    else:
        nM = newModelOrModelId
    if typeName not in oM.types:
        raise RuntimeError(_("Type {0} is not present in model {1}").format(typeName, oM.name))

    instance = oM.types[typeName]
    needed = []
    for attr in ['Storage', 'Inventory']:
        if hasattr(instance, attr):
            for count, tpStr in parseInventoryString(getattr(instance, attr)):  # @UnusedVariable
                if tpStr not in nM.types:
                    needed.append(tpStr)
    return needed

def checkDependentTypes(db, modelOrModelId, typeName):
    if isinstance(modelOrModelId, types.IntType):
        m = shadow_network_db_api.ShdNetworkDB(db,modelOrModelId)
    else:
        m = modelOrModelId
    if typeName not in m.types:
        raise RuntimeError(_("Type {0} is not present in model {1}").format(typeName,m.name))
    needs = []
    for owningTp in m.types.values():
        for attr in ['Storage','Inventory']:
            if hasattr(owningTp,attr):
                needTarget = (typeName in [tpStr for count,tpStr in parseInventoryString(getattr(owningTp,attr))])
                if needTarget: needs.append(owningTp.Name)
    return needs


def addTypeToModel(db, modelOrModelId, typeName, srcModel=None, force=False, ignore=False):
    """
    Copy the given type from srcModel to the given model, if it does not already
    exist.  If srcModel is None (the usual case), AllTypesModel 
    is used as the source.
    """
    if isinstance(modelOrModelId, types.IntType):
        targetModel = shadow_network_db_api.ShdNetworkDB(db,modelOrModelId)
    else:
        targetModel = modelOrModelId
    if typeName in targetModel.types:
        if ignore:
            return
        else:
            raise RuntimeError(_("Type {0} is already present in model {1}").format(typeName,targetModel.name))
    if srcModel is None:
        fromModel = _getAllTypesModel(db)
    else:
        fromModel = srcModel
    if typeName not in fromModel.types:
        raise RuntimeError(_("No such type {0}").format(typeName))
    missingDependencies = checkTypeDependencies(db, fromModel, targetModel, typeName)
    if force:
        for tpStr in missingDependencies: addTypeToModel(db, targetModel, tpStr, srcModel=fromModel)
    else:
        if  missingDependencies != []:
            if len(missingDependencies)==1:
                raise RuntimeError(_("This type depends on the type {0}, which is not in the model.").format(missingDependencies[0]))
            else:
                raise RuntimeError(_("To include this type in the model, you must also include the following types: {0}")\
                                   .format(", ".join(missingDependencies)))
    tpInstance = fromModel.types[typeName]
    targetModel.types[typeName] = tpInstance.copy()
    
def removeTypeFromModel(db, modelOrModelId, typeName, force=False):
    """
    If the given type is in the given model, remove it completely from that model
    """
    if isinstance(modelOrModelId, types.IntType):
        targetModel = shadow_network_db_api.ShdNetworkDB(db,modelOrModelId)
    else:
        targetModel = modelOrModelId
    if typeName not in targetModel.types:
        raise RuntimeError(_("Type {0} is not present in model {1}").format(typeName,targetModel.name))
    dependents = checkDependentTypes(db, targetModel, typeName)
    if force:
        for tpStr in dependents: removeTypeFromModel(db, targetModel, tpStr)
    else:
        if dependents != []:
            if len(dependents) == 1:
                raise RuntimeError(_("This type is used by the type {0}.  You must delete that type first.").format(dependents[0]))
            else:
                raise RuntimeError(_("The following types use {0}: {1}.  You must delete those types first.")\
                                   .format(typeName,", ".join(dependents)))
    targetType = targetModel.types[typeName]
    if isinstance(targetType,shadow_network.ShdPeopleType):
        for s in targetModel.stores.values(): s.updateDemand(targetType,0)
    else:
        for s in targetModel.stores.values(): s.updateInventory(targetType,0)
        
    for rG in targetModel.resultsGroups:
        for r in rG.results:
            for routesRpt in r.routesRpts.values():
                if routesRpt.RouteTruckType == typeName: 
                    r.routesRpts.remove(routesRpt)
            for storesRpt in r.storesRpts.values():
                if typeName in storesRpt.vax: 
                    del storesRpt.vax[typeName]
                if typeName in storesRpt.storage: 
                    del storesRpt.storage[typeName]
            if typeName in r.summaryRecs: 
                del r.summaryRecs[typeName]
    
    toDel = []
    
    nDemand = [d for d in targetModel.unifiedDemands if typeName != d.vaccineStr]
    targetModel.unifiedDemands = nDemand
    
    del targetModel.types[typeName]
    
def getTypeWithFallback(db,modelId,typeName):
    """
    Get the named type, either from the given model or from AllTypesModel
    """
    targetModel = shadow_network_db_api.ShdNetworkDB(db,modelId)
    if typeName in targetModel.types:
        return True,targetModel.types[typeName]
    aM = _getAllTypesModel(db)
    if typeName in aM.types:
        return False, aM.types[typeName]
    raise RuntimeError(_("No such type {0}").format(typeName))

def getSuggestedName(db, modelId, target, proposedName, excludeATM=False):
    if target == 'runName':
        matchfun = lambda nm : (db.query(shadow_network.HermesResultsGroup) \
                .filter_by(modelId=modelId).filter_by(name=nm).count() > 0)
    elif (target == 'typeName' or target in shadow_network.ShdTypes.typesMap
          or (target+'s') in shadow_network.ShdTypes.typesMap):
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        if excludeATM:
            # exclude the AllTypesModel too
            aM = _getAllTypesModel(db)
            matchfun = lambda nm : ((nm in m.types) or (nm in aM.types))
        else:
            matchfun = lambda nm : (nm in m.types)
    else:
        raise HermesServiceException(_('getSuggestedName: unknown target {0}').format(target))
    currentName = proposedName
    offset = 1
    while True:
        hasMatch = matchfun(currentName)
        if not hasMatch: return currentName
        offset += 1
        currentName = '%s_v%d'%(proposedName,offset)
    
def elaborateFieldMap(proposedName, instanceOrValDict, fieldMap):
    outMap = []
    print fieldMap
    for rec in fieldMap:
        outRec = rec.copy()
        if rec['key'] == 'Name': outRec['value'] = proposedName
        elif isinstance(instanceOrValDict,types.DictType) and rec['key'] in instanceOrValDict:
            if outRec['type'] == 'lifetime':
                outRec['value'] = (instanceOrValDict[rec['key']], instanceOrValDict[rec['key'+'Units']] )
            elif outRec['type'] == 'cost':
                if not outRec.has_key('recMap'):
                    pass # NEED To throw an error
                print instanceOrValDict.keys()
                print rec['recMap']
                print instanceOrValDict.keys()
                outRec['value'] =  (instanceOrValDict[rec['recMap'][0]],
                                    instanceOrValDict[rec['recMap'][1]],
                                    instanceOrValDict[rec['recMap'][2]])
            else:
                outRec['value'] = instanceOrValDict[rec['key']]
        elif hasattr(instanceOrValDict,rec['key']):
            if outRec['type'] == 'lifetime':
                outRec['value'] = (getattr(instanceOrValDict,rec['key']),getattr(instanceOrValDict,rec['key']+'Units'))
            elif outRec['type'] == 'cost':
                if not outRec.has_key('recMap'):
                    pass # NEED To throw an error
                outRec['value'] =  (getattr(instanceOrValDict,rec['recMap'][0]),
                                                    getattr(instanceOrValDict,rec['recMap'][1]),
                                                    getattr(instanceOrValDict,rec['recMap'][2]))
            else:
                outRec['value'] = getattr(instanceOrValDict,rec['key'])
        outMap.append(outRec)
    return outMap
    
