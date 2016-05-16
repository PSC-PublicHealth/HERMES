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

_hermes_svn_id_="$Id$"

import sys, os.path, time, types, zipfile, cStringIO
from contextlib import closing
from HermesServiceException import HermesServiceException
from ui_utils import _logMessage

_debug= False

class HermesUserFS(object):
    """
    The framework for storing files/metadata in Hermes' web interface

    the server side info dictionary is guaranteed to have the following keys:
    uploadKey (this is the primary key for the file)
    shortName (this is what the user refers to the file as.  This is also indexed)
    type (general file type so we know what can use this file)
    note (any text commentary on the file), 
    serverSideName (fully qualified file name on the server)
    createTime (when the file was added to the server)
    accessTime (when the file was last accessed)

    other keys a file info dictionary might have:
    shared (set to True if the file is one of the shared files)
    uploading (set to True if the file hasn't been fully uploaded yet)

    I still need to work out semantics for dealing with archive files
    """

    @property
    def files(self): return self.uiSession['fs_files']
    @files.setter
    def files(self,value): self.uiSession['fs_files'] = value
    @files.deleter
    def files(self): del self.uiSession['fs_files']

    @property
    def shortNames(self): return self.uiSession['fs_shortNames']
    @shortNames.setter
    def shortNames(self,value): self.uiSession['fs_shortNames'] = value
    @shortNames.deleter
    def shortNames(self): del self.uiSession['fs_shortNames']

    @property
    def nextFileNo(self): return self.uiSession['fs_nextFileNo']
    @nextFileNo.setter
    def nextFileNo(self,value): self.uiSession['fs_nextFileNo'] = value
    @nextFileNo.deleter
    def nextFileNo(self): del self.uiSession['fs_nextFileNo']

    @property
    def workDir(self): return self.uiSession['fs_workDir']
    @workDir.setter
    def workDir(self,value): self.uiSession['fs_workDir'] = value
    @workDir.deleter
    def workDir(self): del self.uiSession['fs_workDir']

    @property
    def maxFileSize(self): return self.uiSession['fs_maxFileSize']
    @maxFileSize.setter
    def maxFileSize(self,value): self.uiSession['fs_maxFileSize'] = value
    @maxFileSize.deleter
    def maxFileSize(self): del self.uiSession['fs_maxFileSize']

    def __init__(self, uiSession, maxFileSize=10000000):
        self.uiSession = uiSession
        if 'fs_files' in uiSession:
            assert all([(thing in uiSession) for thing in ['fs_nextFileNo', 'fs_files', 'fs_shortNames', 
                                                           'fs_workDir', 'fs_maxFileSize']]), \
                'User file system entry in session dict is broken'
            if not os.path.lexists(uiSession['fs_workDir']):
                self.workDir = self.uiSession.getScratchDir()
            if _debug: _logMessage("user_fs.__init__ happened, rebuilt from session")
        else:
            self.files = {}
            self.shortNames = {}
            self.workDir = self.uiSession.getScratchDir()
            self.maxFileSize = maxFileSize
            self.nextFileNo = 1
            self.save()
            if _debug: _logMessage("user_fs.__init__ from nothing happened")
        
    def save(self):
        self.uiSession.save()
        
    def getNewFileKey(self):
        fileKey = 'f%06d'%self.nextFileNo
        self.nextFileNo = self.nextFileNo + 1 # it is a property func, so avoid using +=
        self.save()
        if _debug: _logMessage("user_fs.getNewFileKey returning %s"%fileKey)
        return fileKey

    def clearAllInfo(self):
        """
        Reset everything except nextFileNo
        """
        self.files = {}
        self.shortNames = {}
        self.save()
        if _debug: _logMessage('user_fs.clearAllInfo happened')

    def makeNewFileInfo(self, shortName, fileType, ext=None, 
                        note=None, appendUL=False, noUpload=False, 
                        shared=False, serverSideName=None, fileKey=None, 
                        archiveKey = None, deleteIfPresent=False):
        """
        creates new file info dictionaries.  There is far too much that is 
        overrideable in this but for now that's what we have.
        """
        if fileKey is None:
            fileKey = 'f%06d'%self.nextFileNo
        if appendUL == True:
            shortName += '%s'%self.nextFileNo

        # no harm in incrementing even if it's unused.
        self.nextFileNo += 1

        if note is None:
            note = "no notes"
        if serverSideName is None:
            serverSideName = os.path.join(self.workDir, shortName)
        retServerSideName = serverSideName[:]
        if ext is not None:
            serverSideName += '.%s'%ext
        info = {'note':note,
                'uploadKey':fileKey,
                'shortName':shortName,
                'type':fileType,
                'serverSideName':serverSideName,
                'createTime':time.time(),
                'accessTime':time.time()}
        if archiveKey is not None:
            info['archiveKey'] = archiveKey
        if shared:
            info['shared'] = True

        if not noUpload:
            info['uploading'] = True

#         if shortName in self.shortNames:
#             if deleteIfPresent:
#                 try:
#                     os.remove(self.getFileInfoByShortName(shortName)['serverSideName'])
#                 except:
#                     pass
#                 self.removeFileInfo(self.getFileKeyByShortName(shortName))
#             else:
#                 raise HermesServiceException('shortName %s already exists'%shortName)
        self.shortNames[shortName] = fileKey
        self.files[fileKey] = info
        self.save()
        if _debug: _logMessage("user_fs.makeNewFileInfo created info for fileKey %s"%fileKey)
        return (fileKey, retServerSideName)

    def getJSONSafeSummary(self):
        d = {}
        for shortName,fileKey in self.shortNames.items():
            info = self.files[fileKey]
            #d[shortName] = info['serverSideName']
            d[shortName] = info
        if _debug: _logMessage("user_fs.getJSONSafeSummary happened")
        return d

    def addContainsKey(self, info, newKey):
        if not isinstance(info, types.DictType):
            info = self.getFileInfo(info, 'addContainsKey')
        if 'contains' not in info:
            info['contains'] = set()
        info['contains'].add(newKey)
        self.save()
        if _debug: _logMessage("user_fs.addContainsKey added %s to %s"%(newKey,info['shortName']))
    
    def delContainsKey(self, info, delKey):
        if not isinstance(info, types.DictType):
            info = self.getFileInfo(info, 'delContainsKey')
        if 'contains' not in info:
            return
        if delKey not in info['contains']:
            return
        info['contains'].remove(delKey)
        if 0 == len(info['contains']):
            del info['contains'] 
        self.save()
        if _debug: _logMessage("user_fs.delContainsKey removed %s to %s"%(delKey,info['shortName']))
                    
    def testFileKeyExists(self, fileKey, action):
        if fileKey not in self.files:
            raise HermesServiceException("%s: fileKey %s doesn't exist"%(action, fileKey))
        self.files[fileKey]['accessTime'] = time.time()
        self.save()
        if _debug: _logMessage("user_fs.testFileExists on %s"%fileKey)

    def getFileInfo(self, fileKey, action='getFileInfo'):
        self.testFileKeyExists(fileKey, action)
        if _debug: _logMessage("user_fs.getFileInfo on %s"%fileKey)
        return self.files[fileKey]
    
    def uploadFinished(self, fileKey):
        self.testFileKeyExists(fileKey, 'uploadFinished')
        if 'uploading' not in self.files[fileKey]:
            raise HermesServiceException("file %s already marked as finished uploading"%fileKey)
        del self.files[fileKey]['uploading']
        self.save()
        if _debug: _logMessage("user_fs.uploadFinished on %s"%fileKey)

    def removeFileInfo(self, fileKey, recurLvl = 0):
        """
        this doesn't remove the actual file, just the info entry
        """
        info = self.getFileInfo(fileKey, 'removeFileInfo')
        while 'contains' in info:
            subKey = info['contains'].__iter__().next()
            self.removeFileInfo(subKey, recurLvl+1)
        if 'archiveKey' in info:
            self.delContainsKey(info['archiveKey'], fileKey)
        del self.shortNames[info['shortName']]
        del self.files[fileKey]
        self.save()
        if _debug and recurLvl==0: _logMessage("user_fs.removeFileInfo on %s"%fileKey)

    def getFileKeyByShortName(self, shortName):
        if shortName not in self.shortNames:
            raise HermesServiceException("ShortName %s doesn't exist"%shortName)
        if _debug: _logMessage("user_fs.getFileKeyByShortName on %s"%shortName)
        return self.shortNames[shortName]

    def getFileInfoByShortName(self, shortName):
        fileKey = self.getFileKeyByShortName(shortName)
        result = self.getFileInfo(fileKey, 'getFileInfoByShortName')
        if _debug: _logMessage("user_fs.getFileInfoByShortName on %s"%shortName)
        return result

    def getFileHandle(self, fileKey):
        """
        return an open file handle for the fileKey
        """
        info = self.getFileInfo(fileKey, 'getFileHandle')
        if 'archiveKey' not in info:
            if _debug: _logMessage("user_fs.getFileHandle on %s (not an archive)"%fileKey)
            return open(info['serverSideName'], 'rb')
        else:
            zInfo = self.getFileInfo(info['archiveKey'], 'getFileHandle')
            with closing(zipfile.ZipFile(zInfo['serverSideName'])) as zi:
                data = zi.read(info['serverSideName'])
            if _debug: _logMessage("user_fs.getFileHandle on %s (archive %s)"%(fileKey,zInfo['serverSideName']))
            return cStringIO.StringIO(data)

    def copyFileInfo(self, srcKey, dstShortName):
        """
        creates a new file info object from another one.
        just like makeNewFileInfo, it returns the destination
        fileKey and serverSideName
        """
        srcInfo = self.getFileInfo(srcKey, 'copyFileInfo')
        note = "Copied from %s"%srcInfo['shortName'] + srcInfo['note']
        result = self.makeNewFileInfo(dstShortName,
                                      srcInfo['type'],
                                      note=note)
        if _debug: _logMessage("user_fs.copyFileInfo copied %s to %s"%(srcKey,dstShortName))
        return result
                             
    def renameShortName(self, fileKey, dstShortName):
        """
        change the short name for a file
        """
        #if dstShortName in self.shortNames:
        #    raise HermesServiceException("shortName %s already exists"%dstShortName)
        info = self.getFileInfo(fileKey, 'renameShortName')
        oldShortName = info['shortName']
        del self.shortNames[oldShortName]
        self.shortNames[dstShortName] = info
        info['shortName'] = dstShortName
        self.save()
        if _debug: _logMessage("user_fs.renameShortName renamed %s to %s"%(fileKey,dstShortName))

    def extensionToType(self, ext):
        tmap = {'.csv':'text/csv', '.dot':'text/xml', '.svg':'image/svg+xml', '.jpg':'image/jpeg', 
                '.png':'image/png', '.zip':'application/zip','.xls':'application/vnd.ms-excel',
                '.xlsx':'application/vnd.ms-excel'}
        if ext in tmap: 
            if _debug: _logMessage("user_fs.extensionToType mapped %s to %s"%(ext,tmap[ext]))
            return tmap[ext]
        else: 
            if _debug: _logMessage("user_fs.extensionToType has no map for %s"%ext)
            return None

    def getExtensionAndType(self, fileKey):
        typeExtensions = {'Stores':('.csv','text/csv'), 
                          'Routes':('.csv','text/csv'), 
                          'Report':('.csv','text/csv'),
                          'NetGraph_dot':('.dot', 'text/xml'), 
                          'NetGraph_svg':('.svg', 'image/svg+xml'),
                          'NetGraph_jpg':('.jpg', 'image/jpeg'),
                          'NetGraph_png':('.png', 'image/png'),
                          'zip-archive':('.zip', 'application/zip'),
                          'excel-file':('.xls', 'application/vnd.ms-excel'),
                          'excelx-file':('.xlsx','application/vnd.ms-excel')
                          }

        info = self.getFileInfo(fileKey, 'getExtensionAndType')
        if info['type'] not in typeExtensions:
            if _debug: _logMessage("user_fs.getExtensionAndType has no map for %s"%fileKey)
            return ("", None)
        else:
            result = typeExtensions[info['type']]
            if _debug: _logMessage("user_fs.getExtensionAndType mapped %s to %s"%(fileKey,result))
            return result

    def getFileInfoList(self, tp=None, shared=None, uploading=None):
        "return a list of file info blocks that match the parameters"
        infoList = []
        for key,info in self.files.items(): # @UnusedVariable
            if tp is not None:
                if info['type'] != tp:
                    continue
            if shared is not None:
                if shared and 'shared' not in info:
                    continue
                if not shared and 'shared' in info:
                    continue
            if uploading is not None:
                if uploading and 'uploading' not in info:
                    continue
                if not uploading and 'uploading' in info:
                    continue
            infoList.append(info)
            if _debug: _logMessage("user_fs.getFileInfoList with tp=%s, shared=%s, uploading=%s"%(tp,shared,uploading))
        return infoList

    def importArchiveContents(self, zFileKey):
        """
        open an archive file, extract the info blob
        create new file info blocks for the enclosed files.
        """
        zInfo = self.getFileInfo(zFileKey, 'importArchiveContents')
        with closing(zipfile.ZipFile(zInfo['serverSideName'])) as zi:
            for fileName in zi.namelist():
                offset = fileName.rfind('.')
                if offset>=0: 
                    fileExt = fileName[offset:]
                    fileType = self.extensionToType(fileExt)
                else: 
                    fileExt = None
                    fileType = None
                innerInfo = self.makeNewFileInfo(fileName, fileType, fileExt, noUpload=True, archiveKey=zFileKey)
                self.addContainsKey(zInfo,innerInfo['uploadKey'])
        self.save()
        if _debug: _logMessage("user_fs.importArchiveContents on archive file %s"%zFileKey)
