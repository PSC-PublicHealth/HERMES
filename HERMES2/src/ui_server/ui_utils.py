#!/usr/bin/env python

_hermes_svn_id_="$Id$"

import sys,os,time,traceback,types
import site_info

import base64

from HermesServiceException import HermesServiceException

import shadow_network_db_api

#def _(s): raise HermesServiceException("Inlizer needed but not imported")
def _(s):
    # Delayed import to avoid circular import dependencies
    from session_support_wrapper import translateString
    return translateString(s)

_sI = site_info.SiteInfo()
_scratchDir= _sI.scratchDir()
_outTmpDir= _sI.outTmpDir()
_logFileName= "%s/hermes_service.log"%_scratchDir
_logFileHandle = None

def _logMessage(lstr):
    lstr = lstr.rstrip()
    if len(lstr) == 0:
        return
    try:
        if _logFileName is not None:
            with open(_logFileName,'a+') as f:
                f.write("%s %s\n"%(time.strftime('%Y/%m/%d %H:%M:%S'),lstr))
    except Exception,e:
        print 'exception %s on %s'%(e,lstr)
        pass
    if _logFileHandle:
        try:
            _logFileHandle.write("%s %s\n"%(time.strftime('%Y/%m/%d %H:%M:%S'),lstr))
        except:
            pass
    
def _logStacktrace():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    _logMessage(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

def _readCmdOutputToList(cmd):
    #print "executing <%s>"%cmd
    cmdout= os.popen(cmd)
    result= cmdout.readlines()
    if cmdout.close() != None :
        raise HermesServiceException("Command failed: %s"%cmd)
    return result

def _getAttrDict(bottleRequest, db, uiSession, fMap, throwException=False):
    """
    fMap is a field map list, as described for various routines in the htmlgenerator module.
    """
    modelId = _safeGetReqParam(bottleRequest.params, 'modelId',isInt=True)
    uiSession.getPrivs().mayReadModelId(db, modelId)
    attrRec = {'modelId':modelId}
    for field in fMap:
        if field['type']=='int':
            v = _safeGetReqParam(bottleRequest.params,field['id'],isInt=True)
        elif field['type']=='float':
            v = _safeGetReqParam(bottleRequest.params,field['id'],isFloat=True)
        elif field['type']=='lifetime':
            v = (_safeGetReqParam(bottleRequest.params,field['id'],isFloat=True),
                 _safeGetReqParam(bottleRequest.params,field['id']+'_units'))
        elif field['type']=='bool':
            v = (_safeGetReqParam(bottleRequest.params, field['id']).lower() == 'true')
        else:
            v = _safeGetReqParam(bottleRequest.params,field['id'])
        attrRec[field['key']] = v
    if throwException:
        badParms = [ k for k,v in attrRec.items() if v is None ]
        if badParms:
            fieldDict = dict([(r['key'],r) for r in fMap])
            badSList = [ (fieldDict[k]['label'] if k in fieldDict else str(k)) for k in badParms ]
            badStr = ", ".join(badSList)
            raise HermesServiceException(_("Missing or invalid parameters for {0}").format(badStr))
    return attrRec

def _mergeFormResults(bottleRequest, db, uiSession, fieldMap, allowNameCollisions=False):
    """
    fieldMap is a field map list, as described for various routines in the htmlgenerator module.
    """
    fieldDict = dict([(r['id'],r) for r in fieldMap])
    attrRec = _getAttrDict(bottleRequest, db, uiSession, fieldMap)
    badStr = ""
    if 'modelId' in attrRec:
        m = shadow_network_db_api.ShdNetworkDB(db,attrRec['modelId'])
        if attrRec['Name'] in m.types and not allowNameCollisions:
            badStr += _("The name {0} is already in use. ").format(attrRec['Name'])
    else:
        m = None
        badStr += _("Model information is missing.")
    badParms = [ k for k,v in attrRec.items() if v is None ]

    # Scan to find disabled fields
    disabledItems = set()
    for d in fieldMap:
        if d['key'] in attrRec:
            if d['type'] == 'select':
                selected = attrRec[d['key']]
                for val,txt,enabledList,disabledList in d['options']:  # @UnusedVariable
                    if val==selected:
                        disabledItems.update([fieldDict[disabledId]['key'] for disabledId in disabledList])
            elif d['type'] == 'hide':
                disabledItems.add(d['key'])
    nBP = []
    #print disabledItems
    for p in badParms:
        if p in disabledItems and attrRec[p] is None:
            for r in fieldMap:
                if r['key']==p and 'default' in r:
                    attrRec[p] = r['default']
        else: nBP.append(p)
    #print nBP
    badParms = nBP

    if badParms:
        badSList = [ (fieldDict[k]['label'] if k in fieldDict else str(k)) for k in badParms ]
        badStr += _("The following parameters are invalid: ")
        badStr += ", ".join(badSList)

    return m,attrRec,badParms,badStr

def _safeGetReqParam(reqParam,paramStr,isInt=False,isFloat=False,isTimeUnit=False,isBool=False,default=None):
    if default is None: 
        if isBool:
            myDefault = False
        else:
            myDefault = None
    else: myDefault = default # paranoia about Python default handling
    if paramStr in reqParam:
        if isInt:
            try:
                return int(reqParam[paramStr])
            except ValueError:
                return myDefault
        elif isFloat:
            try:
                return float(reqParam[paramStr])
            except ValueError:
                return myDefault
        elif isTimeUnit:
            v = reqParam[paramStr]
            if v in ['hour','day','week','month','year']: return v
            else: return myDefault;
        elif isBool:
            rP = reqParam[paramStr]
            if isinstance(rP, types.StringTypes):
                if rP.lower() in ['t','true']: return True
                else: return False
            else:
                v = int(rP)
                if v == 0:
                    return False
                else:
                    return True
        else:
            return reqParam.getunicode(paramStr)
    else:
        return myDefault

def _getOrThrowError(reqParam,paramStr,isInt=False,isBool=False,isFloat=False,isTimeUnit=False):
    import session_support_wrapper as session_support

    inlizer=session_support.inlizer
    _=session_support.translateString

    if paramStr in reqParam:
        if isInt: return int(reqParam[paramStr])
        elif isFloat: return float(reqParam[paramStr])
        elif isBool:
            rP = reqParam[paramStr]
            if isinstance(rP, types.StringTypes):
                if rP.lower() in ['t','true']: return True
                else: return False
            else:
                v = int(rP)
                if v == 0:
                    return False
                else:
                    return True
        elif isTimeUnit:
            v = reqParam[paramStr]
            if v not in ['hour','day','week','month','year']:
                raise HermesServiceException(_('{0} is not a valid unit of time').format(v))
            return v
        else: return reqParam.getunicode(paramStr)
    else:
        raise HermesServiceException(_('Ill-formed request: missing the required parameter {0}').format(paramStr))

def _smartStrip(s):
    if isinstance(s,types.ListType):
        return [_smartStrip(subS) for subS in s]
    else:
        for ch in ['"',"'"]:
            if s.startswith(ch) and s.endswith(ch): s = s[1:-1]
        return s


class loggingFileHandle():
    def __init__(self, t = None):
        self.t = t

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
    
    def write(self, string):
        _logMessage(string)
        if self.t:
            self.t.write(string)

    def writelines(self, strings):
        for s in strings:
            _logMessage(s)
        if self.t:
            self.t.writelines(strings)

    def flush(self):
        if self.t:
            self.t.flush()

    def close(self):
        if self.t:
            self.t.close()


def b64E(s):
    return base64.b64encode(unicode(s).encode('utf-8'))

def b64D(s):
    # yes I really want to use str() here
    return base64.b64decode(str(s)).decode('utf-8')

