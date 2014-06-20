_hermes_svn_id_="$Id$"

import sys, os, os.path, cPickle, thread, json
from fcntl import flock, LOCK_UN, LOCK_SH, LOCK_EX
import time
import cStringIO
import zipfile
import types

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
import site_info
from HermesServiceException import HermesServiceException
from csv_tools import parseCSV

_sI = site_info.SiteInfo()
_scratchDir= _sI.scratchDir()
_outTmpDir= _sI.outTmpDir()
_debug= True

class HermesUserFS:
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

    def __init__(self, state, workDir, maxFileSize=10000000):
        self.files = {}
        self.shortNames = {}
        self.nextFileNo = 1
        self.workDir = workDir
        self.maxFileSize = maxFileSize

    def getNewFileKey(self):
        fileKey = 'f%06d'%self.nextFileNo
        self.nextFileNo += 1
        return fileKey

    def makeNewFileInfo(self, shortName, fileType, ext=None, 
                        note=None, appendUL=False, noUpload=False, 
                        shared=False, serverSideName=None, fileKey=None, 
                        archiveKey = None):
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
            serverSideName = os.path.join(self.workDir, fileKey)
        retServerSideName = serverSideName
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

        if shortName in self.shortNames:
            raise HermesServiceException('shortName %s already exists'%shortName)
        self.shortNames[shortName] = fileKey
        self.files[fileKey] = info
        return (fileKey, retServerSideName)

    def addContainsKey(self, info, newKey):
        if not isinstance(info, types.DictType):
            info = self.getFileInfo(info, 'addContainsKey')
        if 'contains' not in info:
            info['contains'] = set()
        info['contains'].add(newKey)
    
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
                    
    def testFileKeyExists(self, fileKey, action):
        if fileKey not in self.files:
            raise HermesServiceException("%s: fileKey %s doesn't exist"%(action, fileKey))
        self.files[fileKey]['accessTime'] = time.time()

    def getFileInfo(self, fileKey, action='getFileInfo'):
        self.testFileKeyExists(fileKey, action)
        return self.files[fileKey]
    
    def uploadFinished(self, fileKey):
        self.testFileKeyExists(fileKey, 'uploadFinished')
        if 'uploading' not in self.files[fileKey]:
            raise HermesServiceException("file %s already maked as finished uploading"%fileKey)
        del self.files[fileKey]['uploading']

    # this doesn't remove the actual file, just the info entry
    def removeFileInfo(self, fileKey):
        info = self.getFileInfo(fileKey, 'removeFileInfo')
        while 'contains' in info:
            subKey = info['contains'].__iter__().next()
            self.removeFileInfo(subKey)
        if 'archiveKey' in info:
            self.delContainsKey(info['archiveKey'], fileKey)
        del self.shortNames[info['shortName']]
        del self.files[fileKey]

    def getFileKeyByShortName(self, shortName):
        if shortName not in self.shortNames:
            raise HermesServiceException("ShortName %s doesn't exist"%shortName)
        return self.shortNames[shortName]

    def getFileInfoByShortName(self, shortName):
        fileKey = self.getFileKeyByShortName(shortName)
        return self.getFileInfo(fileKey, 'getFileInfoByShortName')

    def getFileHandle(self, fileKey):
        "return an open file handle for the fileKey"
        info = self.getFileInfo(fileKey, 'getFileHandle')
        if 'archiveKey' not in info:
            return open(info['serverSideName'], 'rb')
        zInfo = self.getFileInfo(info['archiveKey'], 'getFileHandle')
        zipfile.open(zInfo['serverSideName'], 'r')
        data = zipfile.read(info['serverSideName'])
        return cStringIO.StringIO(data)

    def copyFileInfo(self, srcKey, dstShortName):
        """
        creates a new file info object from another one.
        just like makeNewFileInfo, it returns the destination
        fileKey and serverSideName
        """
        srcInfo = self.getFileInfo(srcKey, 'copyFileInfo')
        note = "Copied from %s"%srcInfo['shortName'] + srcInfo['note']
        return self.makeNewFileInfo(dstShortName,
                                    srcInfo['type'],
                                    note=note)
                             
    def renameShortName(self, fileKey, dstShortName):
        "change the short name for a file"
        info = self.getFileInfo(fileKey, 'renameShortName')
        if dstShortName in self.shortNames:
            raise HermesServiceException("shortName %s already exists"%dstShortName)
        oldShortName = info['shortName']
        del self.shortNames[oldShortName]
        self.shortNames[dstShortName] = info
        info['shortName'] = dstShortName

    def getExtensionAndType(self, fileKey):
        typeExtensions = {'Stores':('.csv','text/csv'), 
                          'Routes':('.csv','text/csv'), 
                          'Report':('.csv','text/csv'),
                          'NetGraph_dot':('.dot', 'text/xml'), 
                          'NetGraph_svg':('.svg', 'image/svg+xml'),
                          'NetGraph_jpg':('.jpg', 'image/jpeg'),
                          'NetGraph_png':('.png', 'image/png'),
                          'zip-archive':('.zip', 'application/zip')}

        info = self.getFileInfo(fileKey, 'getExtensionAndType')
        if info['type'] not in typeExtensions:
            return ("", None)
        return typeExtensions[info['type']]

    def getFileInfoList(self, type=None, shared=None, uploading=None):
        "return a list of file info blocks that match the parameters"
        infoList = []
        for key,info in self.files.items():
            if type is not None:
                if info['type'] != type:
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
        return infoList

    def importArchiveContents(self, fileKey):
        """
        open an archive file, extract the info blob
        create new file info blocks for the enclosed files.
        """
        info = self.getFileInfo(fileKey, 'importArchiveContents')
        with zipfile.ZipFile(info['serverSideName']) as z:
            mInfo = z.getinfo('hermes_meta.csv')
            if mInfo.file_size > self.maxFileSize:
                raise HermesServiceException("size of hermes_meta.csv exceeds %d bytes"%self.maxFileSize)
            archiveCSV = zipfile.read(mInfo)
            archiveCSV_FH = cStringIO.StringIO(archiveCSV)
            (keys, lines) = parseCSV(archiveCSV_FH)
            castColumn(lines, "name", castTypes.STRING)
            castColumn(lines, "type", castTypes.STRING)
            castColumn(lines, "note", (castTypes.EMPTY_IS_NULL_STRING, castTypes.STRING))
            for line in lines:
                fInfo = z.getinfo(line['name'])
                if fInfo.file_size > self.maxFileSize:
                    raise HermesServiceException("size of %s in %s exceeds %d bytes"%(
                            line['name'], info['serverSideName'], self.maxFileSize))
                shortName = info['shortName'] + '.' + line['name']
                note = line['note'] + '\nThis is a member of the archive %s'%info['shortName']
                (key,ssn) = self.makeNewFileInfo(shortName = shortName,
                                                 fileType = line['type'],
                                                 note = note,
                                                 noUpload = True,
                                                 serverSideName = line['name'],
                                                 archiveKey = fileKey)
                self.addContainsKey(info, key)

                                    
                




class LockedState:
    def __init__(self,key=None):
        self.fh = None
        if key is None:
            key= "%d_%d_%d"%(int(1000*time.time()),os.getpid(),thread.get_ident())
        scratchDir,outDir= LockedState._constructSessionDirs(key)
        fname= os.path.join(scratchDir,'session.pkl')
        if not (os.path.lexists(fname)):
            self.vDict= {'scratchDir':scratchDir,
                         'outDir':outDir,
                         'key':key,
                         'upNumber':0,
                         'downNumber':0,
                         'transactionNumber':0,
                         'stateFname':fname,
#                         'Uploads':{},
                         'fs':HermesUserFS(self, scratchDir),
                         'lastAccess': time.time()}
            shared = self.getSharedDict()
            if 'Uploads' in shared:
                for (key,info) in shared['Uploads'].items():
                    self.vDict['fs'].makeNewFileInfo(info['shortName'],
                                                     info['type'],
                                                     note=info['Note'],
                                                     noUpload=True,
                                                     shared=True,
                                                     serverSideName=info['serverSideName'])

            # this is something of a race condition:
            with open(fname, "w") as f:
                cPickle.dump(self.vDict, f)

        self.fh = open(fname, "r+b")
        flock(self.fh, LOCK_EX)
        self.fh.seek(0)
        self.vDict = cPickle.load(self.fh)
        self.fs = self.vDict['fs']

    def __enter__(self):
        return self

    def write(self):
        self.vDict['lastAccess'] = time.time()
        self.fh.seek(0)
        cPickle.dump(self.vDict, self.fh)
        flock(self.fh, LOCK_UN)
        self.fh.close()
        self.fh = None

    def __exit__(self, type, value, traceback):
        self.write()

    def __del__(self):
        if self.fh is not None:
            self.write()


    def getSharedDict(self):
        sharedScratchFname= os.path.join(_scratchDir,'share','shared.pkl')
        try:
            with open(sharedScratchFname,"r") as f:
                return cPickle.load(f)
        except:
            return {}

    def __str__(self):
        return 'State<%s>'%str(self.vDict)
    def __getitem__(self,key):
        if self.vDict.has_key(key): return self.vDict[key]
        else: return None
    def __setitem__(self,key,val):
        self.vDict[key]= val
    def has_key(self,key): return self.vDict.has_key(key)
    def keys(self):
        return self.vDict.keys()
    def items(self):
        return self.vDict.items()

    @classmethod
    def _constructSessionDirs(cls,sessionKey):
        sessionScratchDir= os.path.join(_scratchDir,sessionKey)
        if not os.path.lexists(sessionScratchDir):
            os.makedirs(sessionScratchDir)
        sessionOutDir= os.path.join(_outTmpDir,sessionKey)
        if not os.path.lexists(sessionOutDir):
            os.makedirs(sessionOutDir) 
        return (sessionScratchDir,sessionOutDir)

    def toJSON(self):
        return json.dumps(self.vDict)

    @classmethod
    def fromJSON(cls,str):
        vDict= json.load(str)
        if not os.path.lexists(vDict['scratchDir']):
            os.makedirs(vDict['scratchDir'])
        if not os.path.lexists(vDict['outDir']):
            os.makedirs(vDict['outDir']) 
        with open(self.vDict['stateFname'],"w") as f:
            cPickle.dump(self.vDict,f)
        if _debug:
            with open(os.path.join(self.vDict['scratchDir'],'state_debug.txt')) as f:
                f.write('%s\n'%self)
        return LockedState(vDict['key'])
   


