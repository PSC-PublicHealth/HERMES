#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
# -Other session's files could be downloaded the same way.
####################################
_hermes_svn_id_="$Id$"

import sys,os,os.path,thread,time,cPickle, codecs, shutil, traceback
import bottle, json, urllib2, string
import re
import StringIO

# If executing under mod_wsgi, we need to add the path to the source
# directory of this script.
try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    # also need the directory above
    updir = os.path.join(cwd, '..')
    if updir not in sys.path:
        sys.path.append(updir)
except:
    pass

from session import LockedState, HermesUserFS
import site_info
from csv_tools import parseCSVHeader, parseCSV
import hermes_data
from HermesServiceException import HermesServiceException
bottle.debug(True)

_sI = site_info.SiteInfo()
_scratchDir= _sI.scratchDir()
_outTmpDir= _sI.outTmpDir()
_logFileName= "%s/hermes_service.log"%_scratchDir
_outFileLifetime= 24.0*60.0*60.0 # output files get lifetime of 24 hours
_housekeepingInterval= 60.0 # Do housekeeping no more often than this
_debug= True
_uploadChunkSize= 10000

def _logMessage(lstr):
    try:
        with open(_logFileName,'a+') as f:
            f.write("%s %s\n"%(time.strftime('%Y/%m/%d %H:%M:%S'),lstr))
    except Exception:
        pass
def _logStacktrace():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    _logMessage(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    
_logMessage("%s: Server starting"%__name__)

def _readCmdOutputToList(cmd):
    #print "executing <%s>"%cmd
    cmdout= os.popen(cmd)
    result= cmdout.readlines()
    if cmdout.close() != None :
        raise HermesServiceException("Command failed: %s"%cmd)
    return result

#def _cullOutputDir():
#    _logMessage("culling output directory")
#    cutoff= time.time()-_outFileLifetime
#    candidates= os.listdir(_outTmpDir)
#    for c in candidates:
#        longc= os.path.join(_outTmpDir,c)
#        if os.path.islink(longc): continue
#        if os.path.isdir(longc):
#            for root,dirs,files in os.walk(longc,topdown=False):
#                for fname in files:
#                    longname= os.path.join(root,fname)
#                    if os.stat(longname).st_mtime < cutoff:
#                        os.unlink(longname)
#                        _logMessage("unlinked %s"%longname)
#                for dirname in dirs:
#                    longpath= os.path.join(root,dirname)
#                    if os.stat(longpath).st_mtime < cutoff \
#                            and len(os.listdir(longpath))==0:
#                        os.rmdir(longpath)
#                        _logMessage("culled empty directory %s"%longpath)
#            if os.stat(longc).st_mtime < cutoff \
#                    and len(os.listdir(longc))==0:
#                os.rmdir(longc)
#                _logMessage("culled empty directory %s"%longc)
#        else:
#            if os.stat(longc).st_mtime < cutoff:
#                os.unlink(longc)
#                _logMessage("unlinked %s"%longc)
                
def _cullScratchDir():
    _logMessage("culling scratch directory")
    cutoff= time.time()-_outFileLifetime
    candidates= os.listdir(_scratchDir)
    for c in candidates:
        longc= os.path.join(_scratchDir,c)
        if os.path.islink(longc) or c=='share' or longc==_logFileName: continue
        if os.path.isdir(longc):
            for root,dirs,files in os.walk(longc,topdown=False):
                for fname in files:
                    longname= os.path.join(root,fname)
                    if os.stat(longname).st_mtime < cutoff:
                        os.unlink(longname)
                        _logMessage("unlinked %s"%longname)
                for dirname in dirs:
                    longpath= os.path.join(root,dirname)
                    if os.stat(longpath).st_mtime < cutoff \
                            and len(os.listdir(longpath))==0:
                        os.rmdir(longpath)
                        _logMessage("culled empty directory %s"%longpath)
            if os.stat(longc).st_mtime < cutoff \
                    and len(os.listdir(longc))==0:
                os.rmdir(longc)
                _logMessage("culled empty directory %s"%longc)
        else:
            if os.stat(longc).st_mtime < cutoff:
                os.unlink(longc)
                _logMessage("unlinked %s"%longc)

#def _scratchDirCleanup(target):
#    dirs= os.listdir(_scratchDir)
#    if target in dirs:
#        fullTarget= os.path.join(_scratchDir,target)
#        for root, dirs, files in os.walk(fullTarget, topdown=False):
#            for name in files:
#                os.remove(os.path.join(root, name))
#            for name in dirs:
#                os.rmdir(os.path.join(root, name))
#        os.rmdir(fullTarget)

def _doHousekeeping():
    _cullScratchDir()


@bottle.post('/CanvizExampleService')
def canvizExampleService():
    try:
        d= json.load(bottle.request.body)
        _logMessage('got canvizExampleService request '+str(d))
        if d['method']=='fetch': 
            whichStrip= int(d['params'][0])
            url= urllib2.urlopen('http://xkcd.com/%d/info.0.json'%whichStrip)
            lines= url.readlines()
            url.close()
            r= json.loads(lines[0])
        else: raise RuntimeError('Unknown method %s'%d['method'])
        return { "result":r,
                 "error":None,
                 u'id':d[u'id'] }
    except Exception,e:
        return { "result":"%s"%str(d),
                 "error":{"code":-12345,"message":str(e)},
                 u'id':d[u'id'] }

def _buildSharedState():
        sharedScratchDir= os.path.join(_scratchDir,'share')
        if not os.path.lexists(sharedScratchDir):
            os.makedirs(sharedScratchDir)
        sI = site_info.SiteInfo()
        srcDir= sI.srcDir()
        index= 0
        allDict= {}
        svnRev= None
        try:
            lines= _readCmdOutputToList("svn info %s"%srcDir)
            for l in lines:
                words= l.split()
                if words[0]=="Revision:":
                    svnRev= int(words[1])
                    break
        except Exception:
            pass
        for path,fname,info in [
                           ('master_data/niger/', 'NigerStoreInfo_REALITY_2010_NewPopModel.csv',{'type':'Stores','shortName':'NigerStore_2010pop'}),
                          ('master_data/niger/', 'NigerStoreInfo_REALITY_2011_NewPopModel.csv',{'type':'Stores','shortName':'NigerStore_2011pop'}),
                          ('master_data/niger/', 'NigerStoreInfo_REALITY_2011_NewPopModel_85percent.csv',{'type':'Stores','shortName':'NigerStore_2011pop_85percent'}),
                          ('master_data/niger/', 'NigerStoreInfo_REALITY_2016_NewPopModel.csv',{'type':'Stores','shortName':'NigerStore_2016pop'}),
                           ('master_data/niger/', 'NigerRoutes_new.csv',{'type':'Routes','shortName':'NigerRoutes_base'}),                                                  
#                           ('master_data/niger/', 'NigerRoutes_NoRegions.csv',{'type':'Routes','shortName':'NigerRoutes_NoRegions'}),                                                  
                           ('master_data/thailand_VMI/', 'VMI_Trang_Thailand_Stores_Info.csv',{'type':'Stores','shortName':'VMI_TrangStore'}),
                           ('master_data/thailand_VMI/', 'VMI_Trang_Thailand_Routes_File.csv',{'type':'Routes','shortName':'VMI_TrangRoutes'}),

                           ('master_data/thailand/', 'Trang-Thailand_Stores_Info.csv',{'type':'Stores','shortName':'TrangStore_base'}),
                           ('master_data/thailand/', 'Trang-Thailand_Routes.csv',{'type':'Routes','shortName':'TrangRoutes_base'}),                                                  
                           ('master_data/unified/', 'UnifiedPeopleTypeInfo.csv',{'type':'People','shortName':'UnifiedPeople'}),

#                           ('master_data/vietnam/', 'Vietnam_Stores_Info.csv',{'type':'Stores','shortName':'VietnamStore_base'}),
                           ('master_data/vietnam/', 'Vietnam_Stores_Info_catch_all_bins.csv',{'type':'Stores','shortName':'VietnamStore_catchall'}),
                           ('master_data/vietnam/', 'Vietnam_Stores_Info_catch_all_bins_onethird.csv',{'type':'Stores','shortName':'VietnamStore_catchall_onethird'}),
                           ('master_data/vietnam/', 'Vietnam_Routes.csv',{'type':'Routes','shortName':'VietnamRoutes_base'}),

                           ('master_data/Senegal/', 'Senegal_Routes.csv', {'type':'Routes', 'shortName':'Senegal_Routes'}),
                           ('master_data/Senegal/', 'Senegal_Stores_Info.csv', {'type':'Stores', 'shortName':'Senegal_Stores'}),
                           ]:
            outname= os.path.join(sharedScratchDir,fname)
            with open(os.path.join(srcDir,(path+fname)),"r") as infile:
                with open(outname,"w") as ofile:
                    for chunk in _fbuffer(infile):
                        ofile.write(chunk)
                info['serverSideName']= outname
                if svnRev is None:
                    info['Note']= "%s SVN rev unknown"%fname
                else:
                    info['Note']= "%s SVN rev %d"%(fname,svnRev)
                info['uploadKey']= 'shared_%04d'%index
                index += 1
                allDict[info['uploadKey']]= info
        rootDict= {}
        rootDict['Uploads']= allDict
        stateFname= os.path.join(sharedScratchDir,'shared.pkl')
        with open(stateFname,"w") as f:
            cPickle.dump(rootDict,f)

def XXX_getFileInfo(state,srcUploadKey):
    if state.has_key('Uploads') and state['Uploads'].has_key(srcUploadKey):
        return state['Uploads'][srcUploadKey]
    elif state.has_key('share') and state['share'].has_key('Uploads') \
        and state['share']['Uploads'].has_key(srcUploadKey):
        return state['share']['Uploads'][srcUploadKey]
    else:
        return None
    
def XXX_getFileInfoByShortName(state,shortName):
    candidates= []
    if state.has_key('Uploads'):
        for k,v in state['Uploads'].items():
            if v.has_key('shortName') and v['shortName']==shortName:
                candidates.append(v)
    if state.has_key('share') and state['share'].has_key('Uploads'):
        for k,v in state['share']['Uploads'].items():
            if v.has_key('shortName') and v['shortName']==shortName:
                candidates.append(v)
    if len(candidates)>1:
        raise HermesServiceException('%d files share the short name %s'%(len(candidates),shortName))
    elif len(candidates)==0:
        return None
    else: return candidates[0]

def XXX_getFileInfoListByType(state,ftype):
    candidates= []
    if state.has_key('Uploads'):
        for k,v in state['Uploads'].items():
            if v.has_key('type') and v['type']==ftype:
                candidates.append(v)
    if state.has_key('share') and state['share'].has_key('Uploads'):
        for k,v in state['share']['Uploads'].items():
            if v.has_key('type') and v['type']==ftype:
                candidates.append(v)
    return candidates

def _noWriteTest(fileInfo):
    if 'shared' in fileInfo and fileInfo['shared']:
        return True
    return False
    
def _makeClientFileInfo(fileInfo):
    return {'uploadKey':fileInfo['uploadKey'],
            'type':fileInfo['type'],
            'shortName':fileInfo['shortName'],
            'noWrite':_noWriteTest(fileInfo)}

def _makeExtendedClientFileInfo(fileInfo):
    info = fileInfo.copy()
    del info['serverSideName']
    del info['archiveName']
    info['noWrite'] = _noWriteTest(fileInfo)
    return info

def _validate_IsOneOf(val, list):
    if (not(isinstance(val, unicode) | isinstance(val, str))):
        return None
    val = val.encode('utf-8')
    for item in list:
        item = item.encode('utf-8')
        if val == item:
            return val
    return None

def _validate_Boolean(val):
    if isinstance(val,int):
        return val != 0
    if (not(isinstance(val, unicode) | isinstance(val, str))):
        return None
    val = val.encode('utf-8')
    if _validate_IsOneOf(val[0], ('t', 'T', 'y', 'Y', '1')):
        return True
    if _validate_IsOneOf(val[0], ('f', 'F', 'n', 'N', '0')):
        return False
    return None

# this is not safe for filenames and directory structures
def _validate_SafeChars(val):
    if (not(isinstance(val, unicode) | isinstance(val, str))):
        return None
    val = val.encode('utf-8')
    safeCharRE = re.compile(r'[^\w=+/-]')
    return safeCharRE.sub('_', val)

def _validate_Integer(val):
    if isinstance(val,int):
        return "%d"%val
    if (not(isinstance(val, unicode) | isinstance(val, str))):
        return None
    val = val.encode('utf-8')
    safeCharRE = re.compile(r'^\d+$')
    if None == safeCharRE.match(val):
        return None
    return val

def _getNetworkDotGraph(state,infoList):
    # Ingest the files
    storesFH = None
    routesFH = None
    reportFH = None
    peopleFH = None
    downloadType = None
    layoutType = None
    options = ""
    vax = None
    size = None
    b64Label = None
    getVaxList = None
    getStoresList = None
    getCSVData = None
    rootNode = None
    showType = None
    vaxList = None  # this is used strictly to provide info for redraws
    storesList = None  # used for setting root in redraws
    sparseInfoList = []
    for pair in infoList:
        _logMessage('pair= %s'%pair)

        if pair[0]== u'Stores':
            storesFH = state.fs.getFileHandle(pair[1])
            sparseInfoList.append(pair)

        elif pair[0]== u'Routes':
            routesFH = state.fs.getFileHandle(pair[1])
            sparseInfoList.append(pair)

        elif pair[0]== u'Reports':
            if pair[1] is not None:
                reportFH = state.fs.getFileHandle(pair[1])
            sparseInfoList.append(pair)

        elif pair[0] == u'People':
            peopleFH = state.fs.getFileHandle(pair[1])
            sparseInfoList.append(pair)

        elif pair[0]== u'Download':
            downloadType = _validate_IsOneOf(pair[1],
                                             ("svg","jpg","dot","png"))
        # circo and dot seem to be the only ones that really work for us
        # but I'll leave the rest here too.
        elif pair[0] == u'Layout':
            layoutType = _validate_IsOneOf(pair[1],
                                           ("circo","dot","neato","fdp","sfdp","twopi"))
        
        elif pair[0] == u'GetVaxList':
            temp = _validate_Boolean(pair[1])
            if temp != None:
                getVaxList = temp

        elif pair[0] == u'GetStoresList':
            temp = _validate_Boolean(pair[1])
            if temp != None:
                getStoresList = temp

        elif pair[0] == u'Show':
            showType = _validate_IsOneOf(pair[1], ("fill", "supplyratio"))

        # size can currently only be '100%'
        elif pair[0] == u'Size':
            size = '100%'
            #size = _validate_IsOneOf(pair[1], ("100%"))

        elif pair[0] == u'Vax':
            vax = _validate_SafeChars(pair[1])

        elif pair[0] == u'B64Label':
            b64Label = _validate_SafeChars(pair[1])

        elif pair[0] == u'RootNode':
            rootNode = _validate_Integer(pair[1])
            #rootNode = pair[1]

        elif pair[0] == u'GetCSVData':
            getCSVData = _validate_Boolean(pair[1])


    if peopleFH is None:
        peopleFH = state.fs.getFileHandle(state.fs.getFileKeyByShortName('UnifiedPeople'))

    if routesFH is None or storesFH is None:
        raise HermesServiceException("Internal error: not enough info to make a graph")

    try:
        if downloadType != None:
            (fileKey, fileName) = state.fs.makeNewFileInfo(
                shortName = 'NetGraph_',
                fileType = 'NetGraph_%s'%downloadType, 
                ext = downloadType, 
                note = 'no notes', 
                appendUL = True)
        else:
            fileName = '%s/dotfile'%state['scratchDir']

        hd = hermes_data.hermes_data(storesFile = storesFH,
                                     routesFile = routesFH,
                                     reportsFile = reportFH,
                                     peopleFile = peopleFH)
        attrib = {}
        if b64Label:
            attrib['label'] = base64.b64decode(b64Label)
        if vax:
            attrib['vax'] = vax
        if rootNode:
            attrib['root'] = rootNode
        if showType:
            attrib['show'] = showType
        layout = layoutType
        if layout is None:
            layout = 'circo'
        hd.build_gv_graph(attrib, layout)

        if downloadType is None:
            dotfile = hd.get_gv_render('xdot')
        elif (size is not None) and (downloadType == 'svg'):
            _logMessage('rewriting svg file\n')
            _logMessage('trying to create %s.svg'%fileName)
            try:
                svg = hd.get_gv_render('svg')
                f = StringIO.StringIO(svg)
                with open("%s.svg"%fileName, 'w') as o:
                    for line in f.readlines():
                        # this is ridiculously brittle and should at least use
                        # regexes for this test.
                        if line[0:12] == '<svg width="':
                            line = "<svg width=\"100%\" height=\"100%\"\n"
                        o.write(line)
                state.fs.uploadFinished(fileKey)
            except:
                _logStacktrace()
                raise HermesServiceException("Error generating fireworks graph: svg conversion failed")
        else:
            hd.save_gv_render(downloadType, fileName)
            state.fs.uploadFinished(fileKey)

                

    except Exception, e:
        _logStacktrace()
        if downloadType != None:
            state.fs.removeFileInfo(fileKey)
        raise e
    finally:
        if peopleFH:
            peopleFH.close()
        if storesFH:
            storesFH.close()
        if routesFH:
            routesFH.close()
        if reportFH:
            reportFH.close()
    try:
        hd.add_gv_locations()
    except:
        _logStacktrace()
        raise HermesServiceException("Error add_gv_locations()")

    output = {}
    output['InfoList'] = sparseInfoList
    if downloadType == None:
        if 0:
            try:
                with open('%s/dotfile.xdot'%state['scratchDir'],'rU') as f:
                    lines= f.readlines()
            except:
                raise HermesServiceException("Error generating fireworks graph: output not found")
            g= ""
            for line in lines: g += line
            output['DotFile'] = g
        else:
            output['DotFile'] = dotFile
    else:
        output['FileKey'] = fileKey
    if getVaxList:
        output['VaxList'] = hd.getVaxList()
    if getStoresList:
        output['StoresList'] = hd.storesList()
    if getCSVData:
        output['RoutesData'] = hd.routesData()
        output['StoresData'] = hd.storesData()
#        output['RootStore'] = hd.getRootStore()
        output['Globals'] = hd.getGlobals()
        output['PeopleTypes'] = hd.getPeopleTypes()

    return output



@bottle.post('/TopLevel')
def topLevel():
    try:
        d= json.load(bottle.request.body)
        _logMessage('<%s> params= %s'%(d['method'],d['params']))
        _doHousekeeping()
        with LockedState(d['params'][0]) as state:


            if d['method']=='test':
                r= 'This does not do anything right now.'
            elif d['method']=='getNetworkGraph':
                infoList= d['params'][1]
                r= json.dumps(_getNetworkGraph(state,infoList))
            elif d['method']=='getNetworkDotGraph':
                infoList= d['params'][1]
                r= json.dumps(_getNetworkDotGraph(state,infoList))
            elif d['method']=='buildSharedState':
                _buildSharedState()
                r= 'That should have built the shared state.'
            elif d['method']=='getSessionKey': 
                r= state['key']
            elif d['method']=='getServerState':
                r= state.toJSON()
            elif d['method']=='getClientStateUpdate':
                r= json.dumps({}) # We'll have more to return later.
            elif d['method']=='getUploadHandle':
                r = state.fs.getNewFileKey()
            elif d['method']=='getDownloadHandle':
                r = state.fs.getNewFileKey()
            elif d['method']=='getFilesOfType':
                ftype= d['params'][1]
                outList= [_makeClientFileInfo(info) for info in state.fs.getFileInfoList(type=ftype)]
                r= json.dumps(outList)

            elif d['method']=='copyServerSideFile':
                srcFileKey= d['params'][1]
                dstShortName= d['params'][2]
                (dstKey, dstName) = state.fs.copyFileInfo(srcFileKey, dstShortName)
                fh = state.fs.getFileHandle(srcFileKey)
                with open(dstName, "wb") as out:
                    out.write(fh.read())
                fh.close()
                state.fs.uploadFinished(dstKey)
                r = _makeExtendedClientFileInfo(state.fs.getFileInfo(dstKey))

            elif d['method']=='renameServerSideFile':
                srcUploadKey= d['params'][1]
                newShortName= d['params'][2]
                state.fs.renameShortName(srcUploadKey, newShortName)
                r = _makeExtendedClientFileInfo(state.fs.getFileInfo(srcUploadKey))

            elif d['method']=='getFileInfo':
                fileKey= d['params'][1]
                r = _makeExtendedClientFileInfo(state.fs.getFileInfo(fileKey))

            else: raise RuntimeError('Unknown method %s'%d['method'])
            state['transactionNumber'] += 1

        _logMessage("returning <%s>"%r)
        return { "result":r,
                 "error":None,
                 u'id':d[u'id'] }
    except Exception,e:
        _logMessage('topLevel says: '+str(e))
        _logStacktrace()
        return { "result":"%s"%str(d),
                 "error":{"code":-12345,"message":str(e)},
                 u'id':d[u'id'] }


# Generator to buffer file chunks
def _fbuffer(f, chunk_size=_uploadChunkSize):
   while True:
      chunk = f.read(chunk_size)
      if not chunk: break
      yield chunk

@bottle.post('/download/:downloadHandle')
def download(downloadHandle):
    _logMessage('File download is happening')
    mdata= None
    errcode= 0
    logMsg= "Download: handle %s"%downloadHandle
    try:
        formMDict= bottle.request.forms
        mdata= json.loads(formMDict['metadata'])
        sessionKey= mdata['sessionKey']
        with LockedState(sessionKey) as state:
            fileInfo = state.fs.getFileInfo(mdata['targetKey'])
            ext,mimetype = state.fs.getExtensionAndType(mdata['targetKey'])
        logMsg += """
        shortName: %s
        serverSideName: %s
        """%(fileInfo['shortName'],fileInfo['serverSideName'])
        suggestedName= fileInfo['shortName']+ext
        logMsg += "suggested name: %s"%suggestedName
        _logMessage(logMsg)
        dirpath,fname= os.path.split(fileInfo['serverSideName'])
        if mimetype is None:
            result= bottle.static_file(fname,root=dirpath,download=suggestedName)
        else:
            result= bottle.static_file(fname,root=dirpath,download=suggestedName,mimetype=mimetype)
        return result
    except Exception,e:
        logMsg += "\nException: %s"%e
        _logMessage(logMsg)
        _logStacktrace()

@bottle.route('/simpleget/:sessionKey/:fileKey')
def simpleGet(sessionKey, fileKey):
    _logMessage('simpleDownload is happening')
    logMsg= "Download: sessionKey: %s, fileKey: %s  "%(sessionKey, fileKey)
    try:
        formMDict= bottle.request.forms
        with LockedState(sessionKey) as state:
            fileInfo= state.fs.getFileInfo(fileKey)
            ext,mimetype = state.fs.getExtensionAndType(fileKey)
        logMsg += """
        shortName: %s
        serverSideName: %s
        """%(fileInfo['shortName'],fileInfo['serverSideName'])
        suggestedName= fileInfo['shortName']+ext
        logMsg += "suggested name: %s"%suggestedName
        _logMessage(logMsg)
        dirpath,fname= os.path.split(fileInfo['serverSideName'])
        if mimetype is None:
            result= bottle.static_file(fname,root=dirpath)
        else:
            result= bottle.static_file(fname,root=dirpath,mimetype=mimetype)
        return result
    except Exception,e:
        logMsg += "\nException: %s"%e
        _logMessage(logMsg)
        _logStacktrace()

@bottle.post('/upload/:uploadHandle')
def upload(uploadHandle):
    _logMessage('File upload is happening')
    mdata= None
    errcode= 0
    fileKey = None
    logMsg= "Upload: handle %s"%uploadHandle
    try:
        formMDict= bottle.request.forms
        fileMDict= bottle.request.files
        mdata= json.loads(formMDict['metadata'])
        sessionKey= mdata['sessionKey']
        fileNameList= []
        for k in fileMDict.keys():
            v= fileMDict[k]
            fileNameList.append("%s"%v.filename)
        logMsg += """
        forms entries: %s
        files entries: %s
        client-side filenames: %s
        """%(formMDict.keys(),fileMDict.keys(),fileNameList)
        if len(fileNameList) != 1:
            errcode= 2
            raise HermesServiceException('upload of %d files; should be exactly 1'%len(fileNameList))

        if not 'note' in mdata:
            mdata['note'] = ""
        mdata['note'] += 'Uploaded at %s '%time.strftime('%Y/%m/%d %H:%M:%S')
        with LockedState(sessionKey) as state:
            (fileKey, fileName) = \
                state.fs.makeNewFileInfo(shortName = mdata['shortName'],
                                         fileType = mdata['type'],
                                         note = mdata['note'],
                                         fileKey = mdata['uploadKey'])

        logMsg += "server-side name: %s"%fileName
        _logMessage(logMsg)
        with open(fileName,'wb',_uploadChunkSize) as f:
            for chunk in _fbuffer(v.file):
                f.write(chunk)

        with LockedState(sessionKey) as state:
            state.fs.uploadFinished(fileKey)
            info = state.fs.getFileInfo(fileKey)

        clientData= _makeClientFileInfo(info)
        clientData['code']= 0
        clientData['message']= ""
        return json.dumps(clientData)
#       This code fragment was an experiment to find a callback from a 'target' iframe.
#        return """
#        <script type="text/javascript">
#        /*
#        window.parent.$pyjs.loaded_modules['hermes_ui']['JSONRPCExample']['onUploadResponse'](null,"foobar");
#        */
#        alert("foo");
#        upFrame= window.parent.window.document.getElementById("myIDString");
#        alert("bar" + upFrame);
#        //upFrame.cbHook();
#        //alert("baz");
#        </script>
#        """
    except Exception,e:
        logMsg += "\nException: %s"%e
        _logMessage(logMsg)
        _logStacktrace()
        # We could return text which would go into a browser window set as the 'target'
        # for this upload, but there doesn't seem to be much point.
        if mdata is None:
            mdata= {'uploadKey':uploadHandle}
        if errcode==0: errcode= 1 # nothing got set before exception was raised
        mdata['code']= errcode
        mdata['message']= str(e)
        if fileKey:
            try:
                with LockedState(sessionKey) as state:
                    state.fs.removeFileInfo(fileKey)
            except:
                pass
            
        return json.dumps(mdata)
        

@bottle.route('/panelhelper/fw_iframes/:sessionKey/:fileKey/:iframeId')
@bottle.route('/panelhelper/fw_iframes/:sessionKey/:fileKey/:iframeId/:dim_x/:dim_y')
def fw_iframe(sessionKey, fileKey, iframeId, dim_x=500, dim_y=500):
    _logMessage('creating fireworks iframe')
    _logMessage("fw_iframe: sessionKey: %s, fileKey: %s"%(sessionKey, fileKey))
    url = "/bottle_hermes/simpleget/%s/%s"%(sessionKey, fileKey)

    html = """
<html>
  <head>
    <!-- The following style text sets absolute position and disables selecting 
         objects while dragging a mouse in various browser specific ways -->
    <style type="text/css">
       .absolute {
         position:absolute;
         left:0px;
         top:0px;

         -moz-user-select: none;
         -khtml-user-select: none;
         -webkit-user-select: none;
         user-select: none;

       }
     </style>
     <!-- The following javascript passes mouse events up to the 
          container's mouse handler (ie outside of the iframe) -->
     <script type="text/javascript">
       function mouseup(event) {
         iframe = parent.document.getElementById("%s");
         div = iframe.parentNode;
         div.onmouseup(event);
       }

       function mousedown(event) {
         if (event.preventDefault) { event.preventDefault(); }
         iframe = parent.document.getElementById("%s");
         div = iframe.parentNode;
         div.onmousedown(event);
       }

       function mousemove(event) {
         iframe = parent.document.getElementById("%s");
         div = iframe.parentNode;
         div.onmousemove(event);
       }

function disableSelection(target){

    if (typeof target.onselectstart!="undefined") //IE route
        target.onselectstart=function(){return false;}

    else if (typeof target.style.MozUserSelect!="undefined") //Firefox route
        target.style.MozUserSelect="none";

    target.style.cursor = "default"
}


     </script>
   </head>
   <body onload="disableSelection(document.body);">
     <object id="thissvg" class="absolute" data="%s" type="image/svg+xml" height="%s" width="%s" draggable="false">
     </object>
     <img class="absolute" id="spacer" src="/hermes/output/spacer.gif" height="%s" width="%s" draggable="false" onmouseup="mouseup(event);" onmousemove="mousemove(event);" onmousedown="mousedown(event);" />
   </body>
</html>
"""%(iframeId,iframeId,iframeId,url,dim_y, dim_x, dim_y, dim_x)

    return html




































peopleTypes= []
_asciiTransTbl= None

def colorStringFromFraction(v):
    if v<0.0: v= 0.0
    if v>1.0: v= 1.0
    if v<0.25:
        low= (255,0,0)
        high= (255,255,0)
        frac= v
    elif v<0.50:
        low= (255,255,0)
        high= (0,255,0)
        frac= v-0.25
    elif v<0.75:
        low= (0,255,0)
        high= (0,255,255)
        frac= v-0.5
    else:
        low= (0,255,255)
        high= (0,0,255)
        frac= v-0.75
    rl,gl,bl= low
    rh,gh,bh= high
    frac *= 4 # range needs to be 0.0 to 1.0
    r= int(frac*rh + (1.0-frac)*rl)
    g= int(frac*gh + (1.0-frac)*gl)
    b= int(frac*bh + (1.0-frac)*bl)
    return "#%02x%02x%02x"%(r,g,b)
        
def _decomposeId(code):
    #print "decomposeId: %d -> "%code,
    clinicCode= code % 100
    code /= 100
    districtCode= code % 100
    code /= 100
    regionCode= code % 100
    #print "(%d,%d,%d)"%(regionCode,districtCode,clinicCode)
    return (regionCode,districtCode,clinicCode)

def _composeId(regionCode,districtCode,clinicCode):
    result= long("%d%02d%02d%02d"%(1,regionCode,districtCode,clinicCode))
    #print "composeId: (%d %d %d) -> %ld"%(regionCode,districtCode,
    #                                      clinicCode,result)
    return result

def _deadWarehouse(rec):
    return (_getTotalPop(rec)==0 and _getTotalStorage(rec)==0)

def _getDefaultSupplier(rec):
    code= long(rec['idcode'])
    regionCode,districtCode,clinicCode= _decomposeId(code)
    if regionCode==0 and districtCode==0 and clinicCode==0:
        return None # This is the central store
    else:
        if districtCode==0 and clinicCode==0:
            # region; supplier is central store
            return _composeId(0,0,0) 
        elif clinicCode==0:
            # district; supplier is region
            return _composeId(regionCode,0,0) 
        else:
            # clinic; supplier is district
            return _composeId(regionCode,districtCode,0) 


def guessSupplierID(rec):
    """
    This routine is the analog of the HERMES Model.getDefaultSupplier() method.
    It uses a really stupid heuristic which happens to work for the current 
    set of models (as of September 2010).
    """
    id= rec['idcode']
    if id>1000000:
        # This is the old 7 digit form
        return _getDefaultSupplier(rec)
    else:
        if id>10000:
            return id % 10000
        else:
            return None
        
def _getTotalPop(rec):
    totPop= 0
    for k in rec.keys():
        if k.find('Population')>=0:
            totPop += rec[k]
    for pt in peopleTypes:
        if rec.has_key(pt) and rec[pt]!='':
            totPop += rec[pt]
    return totPop

def _getTotalStorage(rec):
    totVol= 0.0
    for k in rec.keys():
        if k.find('(lit)')>=0.0:
            totVol += rec[k]
    return totVol

def ascify(str):
    global _asciiTransTbl
    if _asciiTransTbl is None:
        _asciiTransTbl= bytearray('?'*256)
        for i in string.printable: _asciiTransTbl[ord(i)]= i
        _asciiTransTbl[ord(' ')]= '_'  # since gv seems to have trouble with strings including blanks
    return str
    #return str.translate(_asciiTransTbl)

def getNodeInfo(rec,showWhat,vax):
    "Returns a tuple 'color,note' with info to be associated with the node"
    lightGray= '#B0B0B0'
    gray= '#808080'
    if showWhat=='fill':
        val= rec['cooler']
        if val=='NA':
            clr= lightGray
            note= "\ncooler=NA"
        else:
            clr= colorStringFromFraction(val)
            if val>=0.8: note= "\n%s=%f"%('cooler',val)
            else: note= None
    elif showWhat=='supplyratio':
        try:
            treated= rec["%s_treated"%vax]
            patients= rec["%s_patients"%vax]
            if treated=='NA' or patients=='NA':
                clr= gray
                note= ""
            elif patients==0:
                clr= lightGray
                note= "\nno patients"
            else:
                val= float(treated)/float(patients)
                clr= colorStringFromFraction(1.0-val)
                if val<=0.2: note= "\n%s=%f"%('supply ratio',val)
                else: note= ""
        except:
            print rec
            print "%s_treated"%vax
            print "%s_patients"%vax
            raise RuntimeError("Report file doesn't contain info for requested supply ratio")
    else:
        raise RuntimeError("unknown 'show' option %s"%showWhat)
    return clr,note

def getEdgeInfo(rec,showWhat,vax):
    "Returns a tuple 'color,note' with info to be associated with the edge"
    lightGray= '#B0B0B0'
    if showWhat=='fill':
        val= rec['RouteFill']
        if val=='NA':
            edgeColor= lightGray
            labelTail="\nRouteFill=%s"%val
        else:
            edgeColor= colorStringFromFraction(val)
            if val>=0.8: labelTail="\nRouteFill=%f"%val
            else: labelTail= None
        return edgeColor,labelTail
    else:
        return "#000000",None

def buildHermesNetworkGraph(whRecs,routeRecs,peopleRecs,reportRecs=None):
    """
    This routine takes 'standard' HERMES input table rows and produces a graph
    suitable for JSON transmission.  whRecs, routeRecs and peopleRecs are the
    lists of record dictionaries produced by loading the warehouse, route, and
    peopletype definition spreadsheet files.  If reportRecs is given, values are
    taken from the report data to add color to the graph.
    
    The returned graph is a directory of directories and lists, the python
    equivalent of a JSON data structure.  Each node contains an attribute
    'hermes_id' containing the corresponding 'idcode' value as a string.
    Those which form a cluster contain an attribute 'hermes_cluster' containing
    the cluster name.
    """
    global peopleTypes
    
    # Load people types so we can recognize those columns
    for rec in peopleRecs:
        if rec['Name'] not in peopleTypes:
            peopleTypes.append(rec['Name'])

    # Sort out the routes
    routeDict= {}
    for rec in routeRecs:
        rname= rec['RouteName']
        if not routeDict.has_key(rname):
            routeDict[rname]= []
        routeDict[rname].append((int(rec['RouteOrder']),rec))
    for k in routeDict.keys():
        l= routeDict[k]
        l.sort()
        routeDict[k]= [rec for junk,rec in l]
        
    # Sort out the report records, if given
    routeReportDict= {}
    whReportDict= {}
    if reportRecs is not None:
        for r in reportRecs:
            if r.has_key('code'):
                whReportDict[r['code']]= r
            if r.has_key('RouteName'):
                routeReportDict[r['RouteName']]= r
    else:
        _logMessage('reportRecs is None')
    _logMessage('whReportDict keys: %s'%whReportDict.keys())
    
    # Build the graph
    #gv.setv(gv.protonode(g),'style','filled')
    #gv.setv(g,'mindist','0.1')
    #gv.setv(g,'clusterrank','local')
    #gv.setv(g,'compound','true')
    
    nodeDict= {}
    nodeRecDict= {}
    for rec in whRecs:
        id= int(rec['idcode'])
        nName= rec['NAME']
        n= {'name':nName, 'id':id, 'data':{'band':'foo','relation':'client'},'children':[]}
        nodeDict[id]= n
        #gv.setv(n,'URL','http://n%s.html'%id)
        labelTail= ""
        if whReportDict.has_key(id):
            clr,labelTail= getNodeInfo(whReportDict[id],"fill",None)
            if labelTail is None: labelTail= ""
            n['data']['$color']= clr
        else: 
            n['data']['$color']= '#AAAAAA'
        if rec.has_key('FUNCTION'):
            if rec['FUNCTION']=='Administration':
                if _getTotalStorage(rec)==0.0:
                    n['data']['shape']= 'diamond' # these should be 'attached' clinics
                    n['data']['label']= "%s%s"%(id,labelTail)
                else:
                    n['data']['label']= '%s\n%s%s'%(ascify(nName),id,labelTail)
                    n['data']['shape']= 'ellipse'
            elif rec['FUNCTION']=='Distribution':
                n['data']['label']= '%s\n%s%s'%(ascify(nName),id,labelTail)
                n['data']['shape']= 'box'
            elif rec['FUNCTION']=='Surrogate':
                n['data']['label']= "%s%s"%(id,labelTail)
                n['data']['shape']= 'doublecircle'
            else:
                n['data']['shape']= 'octagon'
                n['data']['$color']= '#B00000'
                n['data']['label']= '%s\n%s\n%s%s'%(ascify(nName),id,rec['FUNCTION'],labelTail)
        else:
            totPop= _getTotalPop(rec)
            if totPop !=0:
                if _getTotalStorage(rec)==0.0:
                    n['data']['label']= '%s\n%s%s'%(ascify(nName),id,labelTail)
                    n['data']['shape']= 'diamond' # these should be 'attached' clinics
                else:
                    n['data']['label']= '%s\n%s%s'%(ascify(nName),id,labelTail)
                    n['data']['shape']= 'ellipse'
            else:
                n['data']['label']= '%s\n%s%s'%(ascify(nName),id,labelTail)
                n['data']['shape']= 'box'
        nodeRecDict[id]= rec
    for routeName in routeDict.keys():
        edgeList= []
        stops= routeDict[routeName]
        fromRec= stops[0]
        stops= stops[1:]
        if routeReportDict.has_key(routeName):
            edgeColor, labelTail= getEdgeInfo(routeReportDict[routeName],"fill",None)
            if labelTail==None: labelTail= ""
        else:
            edgeColor= "#000000"
            labelTail= ""
        for rec in stops:
            fromID= int(fromRec['idcode'])
            toID= rec['idcode']
            nodeDict[fromID]['children'].append(nodeDict[toID])
            #gv.setv(edge,'color',edgeColor)
            #if rec.has_key('TruckType'):
            #    gv.setv(edge,'label',"%s\n%s\n%s%s"%\
            #            (routeName,rec['TruckType'],rec['Type'],ascify(labelTail)))
            #else:
            #    gv.setv(edge,'label',"%s\n%s%s"%(routeName,rec['Type'],ascify(labelTail)))
            #edgeList.append(edge)
            fromRec= rec
            
    # Scan for loose nodes, and try to attach them
    for id,n in nodeDict.items():
        nLinks= 0
        if len(n['children']) is None:
            rec= nodeRecDict[id]
            if _deadWarehouse(rec):
                n['data']['style']= 'dashed'
            else:
                supplierID= guessSupplierID(rec)
                if supplierID is None:
                    n['data']['$color']= '#B00000'
                else:
                    nodeDict[supplierID]['children'].append(n)
                    #edge= gv.edge(nodeDict[supplierID],node)
                    #gv.setv(edge,'label','default')
                    #gv.setv(edge,'style','dotted')

#    # Scan for clusters, and add cluster information
#    for id,node in nodeDict.items():
#        inEdge= gv.firstin(node)
#        numInEdges= 0
#        while inEdge is not None:
#            numInEdges= 1
#            inEdge= gv.nextin(node,inEdge)
#        numOutEdges= 0
#        outEdge= gv.firstout(node)
#        while outEdge is not None:
#            numOutEdges += 1
#            outEdge= gv.nextout(node,outEdge)
#        if numInEdges==1 and numOutEdges>3:
#            nodeRec= nodeRecDict[id]
#            gv.setv(node,'hermes_cluster',ascify(nodeRec['NAME']))
#    gv.setv(g,'fontsize','100.0')
#    setScale(findHead(g),100.0)


    # Find the head
    topCandidates= []
    for id,n in nodeDict.items():
        for k in n['children']:
            if not k['data'].has_key('nparents'): k['data']['nparents']= 0
            k['data']['nparents'] += 1
    for id,n in nodeDict.items():
        if not n['data'].has_key('nparents') or n['data']['nparents']==0:
             topCandidates.append((len(n['children']),n))
    topCandidates.sort()
    head= topCandidates[-1][1]
    
    return head

        
def _getNetworkGraph(state,infoList):
    # Ingest the files
    whFname= None
    routesFname= None
    reportFname= None
    peopleFname= _getFileInfoByShortName(state,'UnifiedPeople')['serverSideName']
    for pair in infoList:
        if pair[0]== u'Stores':
            whFname= _getFileInfo(state,pair[1])['serverSideName']
        elif pair[0]== u'Routes':
            routesFname= _getFileInfo(state,pair[1])['serverSideName']
        elif pair[0]== u'Reports':
            reportFname= _getFileInfo(state,pair[1])['serverSideName']
    if routesFname is None or whFname is None or peopleFname is None:
        raise HermesServiceException("Internal error: not enough info to make a graph")
    with open(whFname,"rU") as f:
        whKeys,whRecs= csv_tools.parseCSV(f)
    with open(routesFname,"rU") as f:
        routeKeys,routeRecs= csv_tools.parseCSV(f)
    with open(peopleFname,"rU") as f:
        peopleKeys,peopleRecs= csv_tools.parseCSV(f)
    if reportFname is not None:
        with open(reportFname,"rU") as f:
            reportKeys,reportRecs= csv_tools.parseCSV(f)
    else:
        reportRecs= None

    # Build the raw graph
    g= buildHermesNetworkGraph(whRecs,routeRecs,peopleRecs,reportRecs)
    return g




application= bottle.default_app()
