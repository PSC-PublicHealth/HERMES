#!/usr/bin/env python


####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id$"

import sys,os,os.path,time,json,math,types
import bottle
import ipath
import site_info
import i18n
import gettext
from HermesServiceException import HermesServiceException

from ui_utils import _logMessage, _logStacktrace

sI = site_info.SiteInfo()

_scratchDir= sI.scratchDir()
_outTmpDir= sI.outTmpDir()
_uploadChunkSize= 10000

inlizer = i18n.i18n('locale')
_=inlizer.translateString

# Generator to buffer file chunks
def _fbuffer(f, chunk_size=_uploadChunkSize):
    while True:
        chunk = f.read(chunk_size)
        if not chunk: break
        yield chunk

def _noWriteTest(fileInfo):
    if 'shared' in fileInfo and fileInfo['shared']:
        return True
    return False
    
def makeClientFileInfo(fileInfo):
    return {'uploadKey':fileInfo['uploadKey'],
            'type':fileInfo['type'],
            'shortName':fileInfo['shortName'],
            'noWrite':_noWriteTest(fileInfo)}

def uploadAndStore(bottleRequest,uiSession):
    """
    Given a bottle request containing upload information, perform the upload and return
    the server-side file information.  May raise HermesServiceException.
    """
    logMsg= "Upload:"
    formMDict = bottleRequest.forms
    fileMDict = bottleRequest.files
    fileNameList= []
    for k in fileMDict:
        fileNameList.append(fileMDict[k].filename)
        v = fileMDict[k]
    logMsg += """
    forms entries: %s
    files entries: %s
    client-side filenames: %s
    """%(formMDict.keys(),fileMDict.keys(),fileNameList)
    if len(fileNameList) != 1:
        raise HermesServiceException('upload of %d files; should be exactly 1'%len(fileNameList))
    clientFileName = fileNameList[0]
    clientFileExt = os.path.splitext(clientFileName)[1]
    note = 'Uploaded at %s '%time.strftime('%Y/%m/%d %H:%M:%S')
    if 'shortname' in formMDict: shortName = formMDict['shortname']
    else: shortName = os.path.split(clientFileName)[1]
    print "-9-090-09-09-09-09-09-0"
    print shortName
    
    with uiSession.getLockedState() as state:
        print state.fs().extensionToType(clientFileExt)
        print "-fdssdfaefsdfadsfasdfsdafdd----"
        fileType = state.fs().extensionToType(clientFileExt)
        if fileType is None:
            raise HermesServiceException('File for upload %s has an unknown extension; cannot identify file type'%clientFileName)
        (fileKey, fileName) = \
            state.fs().makeNewFileInfo(shortName = shortName,
                                       fileType = fileType,
                                       note = note)
    logMsg += "server-side name: %s\n"%fileName
    _logMessage(logMsg)
    logMsg += "fileKey: %s"%fileKey
    with open(fileName,'wb',_uploadChunkSize) as f:
        for chunk in _fbuffer(v.file):
            f.write(chunk)

    with uiSession.getLockedState() as state:
        state.fs().uploadFinished(fileKey)
        info = state.fs().getFileInfo(fileKey)
    #uiSession['notes'] += ", uploaded %s"%info['shortName']

    print "dsfsdfsdfffffffffffffffffffffffffffffffffffffffff"
    print formMDict.keys()
    if 'modelId' in formMDict.keys():
        info['modelId'] = formMDict['modelId']
    
    if 'overrideNames' in formMDict.keys():
        if formMDict['overrideNames'] == 'true':
            info['overrideNames'] = True
        else:
            info['overrideNames'] = False
        #info['overrideNames'] = formMDict['overrideNames']
    return info

