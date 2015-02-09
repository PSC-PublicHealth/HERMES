###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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

import sys,os,os.path,types
import ipath
import bottle
import typehelper
import shadow_network_db_api
import session_support_wrapper as session_support
import shadow_network
import privs
from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

inlizer=session_support.inlizer
_=session_support.translateString

wireTypeMap = {'people':shadow_network.ShdPeopleType, 'vaccine':shadow_network.ShdVaccineType,
               'fridge':shadow_network.ShdStorageType,'truck':shadow_network.ShdTruckType,
               'staff':shadow_network.ShdStaffType, 'perdiems':shadow_network.ShdPerDiemType}
wireTypeNameMap = { k:v.__name__ for k,v in wireTypeMap.items() }

class Clipboard(object):
    class MockModelTypes(object):
        def __init__(self, owner):
            self.cb = owner
        def __getitem__(self,typeName):
            try:
                if self.cb.getClipDataName() == typeName:
                    return self.cb.get('ShdType')
            except:
                raise KeyError(typeName)
        def __contains__(self,typeName):
            return (typeName == self.cb.getClipDataName())

    @property
    def types(self):
        return Clipboard.MockModelTypes(self)
    
    def __init__(self,uiSession):
        self.uiSession = uiSession
    
    def put(self, thing):
        tp = type(thing)
        typeName = tp.__name__
        assert hasattr(tp,'mro'), _('Cannot put an instance of the old-style class {0} on the clipboard').format()
        
        if isinstance(thing, shadow_network.ShdType):
            self.uiSession['clipType'] = [t.__name__ for t in tp.mro()]
            self.uiSession['clipObj'] = thing.createRecord()
            self.uiSession['clipName'] = thing.Name
        else:
            raise RuntimeError(_('Cannot encode a {0} to the clipboard').format(typeName))
        
    def get(self, expectedTypeOrTypeName):
        if isinstance(expectedTypeOrTypeName, types.StringTypes):
            typeName = expectedTypeOrTypeName
        else:
            typeName = expectedTypeOrTypeName.__name__
        if 'clipObj' not in self.uiSession or self.uiSession['clipObj'] is None:
            raise RuntimeError(_('Clipboard is empty'))
        tpList = self.uiSession['clipType']
        if typeName in tpList:
            if 'ShdType' in tpList[tpList.index(typeName):]: # check if requested type is ShdType or subclass
                return getattr(globals()['shadow_network'],tpList[0])(self.uiSession['clipObj'])
            else:
                raise RuntimeError(_('Cannot decode a {0} from the clipboard').format(typeName))
        else:
            raise RuntimeError(_('Clipboard has a {0}; {1} expected').format(self.uiSession['clipType'][0], typeName))
        
    def hasData(self):
        return ('clipObj' in self.uiSession and self.uiSession['clipObj'] is not None)
    
    def hasDataOfType(self,expectedTypeOrTypeName):
        if isinstance(expectedTypeOrTypeName,types.StringTypes):
            return (self.hasData() and expectedTypeOrTypeName in self.uiSession['clipType'])
        else:
            return (self.hasData() and expectedTypeOrTypeName.__name__ in self.uiSession['clipType'])
        
    def getClipDataName(self):
        if 'clipName' in self.uiSession: return self.uiSession['clipName']
        else: return None
        
    def getClipDataType(self):
        if 'clipType' in self.uiSession: return self.uiSession['clipType'][0]
        else: return None

        
@bottle.route('/json/test-clipboard-type')
def jsonTestClipboardType(uiSession):
    try:
        typeStr = _getOrThrowError(bottle.request.params, 'type')
        if typeStr in wireTypeNameMap:
            cb = Clipboard(uiSession)
            if cb.hasDataOfType(wireTypeNameMap[typeStr]):
                result = {'success':True, 'value':True}
            else:
                result = {'success':True, 'value':False}
        else:
            raise RuntimeError(_('cannot map wire type {0} to clipboard').format(typeStr))
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = { 'success':False, 'msg':str(e)}
    return result

@bottle.route('/json/get-clipboard-name')
def jsonGetClipboardName(uiSession):
    try:
        result = {'success':True, 'value':Clipboard(uiSession).getClipDataName()}
    except privs.PrivilegeException:
        result = { 'success':False, 'msg':_('User cannot read this model')}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = { 'success':False, 'msg':str(e)}
    return result

@bottle.route('/json/copy-type-to-clipboard')
def jsonCopyTypeToClipboard(db, uiSession):
    try:
        modelId = _safeGetReqParam(bottle.request.params, 'modelId',isInt=True)
        if modelId is None: 
            raise RuntimeError(_('No such model {0}').format(modelId))
        uiSession.getPrivs().mayReadModelId(db, modelId)
        name = _getOrThrowError(bottle.request.params, 'name')
        dummy,t = typehelper.getTypeWithFallback(db, modelId, name)
        Clipboard(uiSession).put(t)
        result = { 'success':True }
    except privs.PrivilegeException:
        result = { 'success':False, 'msg':_('User cannot read this model')}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = { 'success':False, 'msg':str(e)}
    return result

@bottle.route('/json/paste-clipboard-to-type')
def jsonPasteClipboardToType(db, uiSession):
    try:
        modelId = _safeGetReqParam(bottle.request.params, 'modelId',isInt=True)
        if modelId is None: 
            raise RuntimeError(_('No such model {0}').format(modelId))
        uiSession.getPrivs().mayModifyModelId(db, modelId)
        name = _getOrThrowError(bottle.request.params, 'name')
        typeStr = _getOrThrowError(bottle.request.params, 'type')
        if typeStr in wireTypeNameMap:
            cb = Clipboard(uiSession)
            if cb.hasDataOfType(wireTypeNameMap[typeStr]):
                typehelper.addTypeToModel(db, modelId, name, srcModel=cb)
#                 t = cb.get(wireTypeMap[typeStr])
#                 t.Name = name
#                 #getDBSession().add(t)
#                 m = shadow_network_db_api.ShdNetworkDB(db,modelId)
#                 m.types[name] = t
                result = {'success':True}
            else:
                raise RuntimeError(_('Clipboard does not hold a {0}').format(typeStr))
        else:
            raise RuntimeError(_('cannot map wire type {0} from clipboard').format(typeStr))
    except privs.PrivilegeException:
        result = { 'success':False, 'msg':_('User cannot modify this model')}
    except Exception,e:
        _logMessage(str(e))
        _logStacktrace()
        result = { 'success':False, 'msg':str(e)}
    return result
        
        