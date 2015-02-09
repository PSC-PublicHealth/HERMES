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


__doc__=""" eventlog.py
This module provides a logger, which efficiently writes timestamped
event records to a file.
"""

_hermes_svn_id_="$Id: eventlog.py 879 2012-03-08 16:47:47Z welling $"

import sys, os, os.path, unittest, StringIO, types, re
import util

EVT_DELIVERY = "delivery"
EVT_PICKUP = "pickup"
EVT_REQUEST = "request"
EVT_SCALEDREQUEST = "scaledrequest"
EVT_RECYCLE = "recycle"
EVT_RECYCLEDELIVERY = "recycledelivery"

_eventNameDict = { "delivery":EVT_DELIVERY, "pickup":EVT_PICKUP,
                   "request":EVT_REQUEST, "scaledrequest":EVT_SCALEDREQUEST,
                   "recycle":EVT_RECYCLE, "recycledelivery":EVT_RECYCLEDELIVERY}

def getEventFromEventName(strName):
    """
    Returns the event matching the given name, or None if there is no such event.
    """
    if strName in _eventNameDict: return _eventNameDict[strName]
    else: return None

def _quoteStrings(x):
    if isinstance(x,types.StringTypes): return '"%s"'%x
    else: return x

def _genericDictProc(event,evtDict,kwDict):
    """
    Return a string based on the contents of evtDict, supplemented by keyword arguments.
    Keyword values will override pre-existing entries in evtDict
    """
    str1 = ''.join(['"%s":%s, '%(k,_quoteStrings(v)) for k,v in kwDict.items()])
    str2 = ''.join(['"%s":%s, '%(str(k),_quoteStrings(v)) for k,v in evtDict.items()
                    if isinstance(v,types.StringTypes) or v>0])
    return '"event":%s, %s%s'%(_quoteStrings(event),str1,str2)

_eventHandlerDict = { EVT_DELIVERY:_genericDictProc,
                      EVT_PICKUP:_genericDictProc,
                      EVT_REQUEST:_genericDictProc,
                      EVT_SCALEDREQUEST:_genericDictProc,
                      EVT_RECYCLE:_genericDictProc,
                      EVT_RECYCLEDELIVERY:_genericDictProc,
                      }

class EventLogException(Exception):
    pass

class EventLog:
    """
    This base class exists only to provide the real and dummy event logs
    with a consistent type.
    """
    pass

class DummyEventLog:
    def __init__(self):
        pass
    def close(self):
        pass
    def flush(self):
        pass
    def log(self,timeNow,eventType,evtDict,**kwargs):
        pass
    def setEventList(self,evList):
        pass
    def setFilterRegex(self,regexStr):
        pass

class FileEventLog:
    def __init__(self,logFileOrFileName):
        """
        logFileOrFileName may be an open file, or a name string.
        Zipfile name strings ('zipfile:...') are supported.
        """
        self.selectedEvents = set(_eventHandlerDict.keys())
        self.regex = re.compile('.*') # matches everything
        if isinstance(logFileOrFileName,types.StringType) or isinstance(logFileOrFileName,types.UnicodeType):
            self.fileName = logFileOrFileName
            self.file = util.openOutputFile(self.fileName, useTempFile=True)
        else:
            self.fileName = None
            self.file = logFileOrFileName

    def setEventList(self,evList):
        assert all([e in _eventHandlerDict.keys() for e in evList]),\
               "Some of the selected events are not valid"
        self.selectedEvents = set(evList)

    def setFilterRegex(self,regexStr):
        """
        If the given regex matches any of the keyword arguments (typically
        including supplier, client, and route), include the record in the
        log.  If not, drop the record.  It counts as a match if the regex
        matches anywhere in the string, not just at the beginning.
        """
        self.regex = re.compile(regexStr)

    def close(self):
        """
        Because the file may actually be a handle to a zip file, it's
        important that it be properly closed.
        """
        self.file.flush()
        self.file.close()

    def flush(self):
        self.file.flush()

    def log(self,timeNow,eventType,evtDict,**kwargs):
        if eventType not in _eventHandlerDict:
            raise EventLogException("Unknown event type %s"%eventType)
        if eventType not in self.selectedEvents:
            return
        if any([(isinstance(v,types.StringType) and self.regex.search(v))
                for v in kwargs.values()]):
            resultStr = _eventHandlerDict[eventType](eventType,evtDict,kwargs)
            self.file.write('"time":%f, %s\n'%(timeNow,resultStr))

def describeSelf():
    print \
"""
Testing options:

  testlog
     does simple tests of EventLog

  testlog2
     test restricting the event set

  testlog3
     test the filter regex feature

"""

def main(myargv=None):
    "Provides a few test routines"

    if myargv is None: 
        myargv = sys.argv
    
    if len(myargv)<2:
        describeSelf()
    elif myargv[1]=='testlog':
        if len(myargv)==2:
            evL = FileEventLog(sys.stdout)
            try:
                evL.log(1.23,"hello",{"foo":"bar","baz":"blrfl"})
            except EventLogException,e:
                print "got exception \"%s\""%e
            for eventType in _eventHandlerDict.keys():
                try:
                    print "Trying event %s"%eventType
                    evL.log(1.23,eventType,{"foo":"bar","baz":"blrfl"})
                except EventLogException,e:
                    print "got exception \"%s\""%e
        else:
            print "Wrong number of arguments!"
            describeSelf()

    elif myargv[1]=='testlog2':
        if len(myargv)==2:
            evL = FileEventLog(sys.stdout)
            evL.setEventList([EVT_DELIVERY])
            try:
                evL.log(1.23,"hello",{"foo":"bar","baz":"blrfl"},something="myvalue")
            except EventLogException,e:
                print "got exception \"%s\""%e
            for eventType in _eventHandlerDict.keys():
                try:
                    print "Trying event %s"%eventType
                    evL.log(1.23,eventType,{"foo":"bar","baz":"blrfl"},something="myvalue")
                except EventLogException,e:
                    print "got exception \"%s\""%e
        else:
            print "Wrong number of arguments!"
            describeSelf()

    elif myargv[1]=='testlog3':
        if len(myargv)==2:
            evL = FileEventLog(sys.stdout)
            evL.setFilterRegex('((these)|(those))')
            try:
                evL.log(1.23,EVT_RECYCLE,{"foo":"bar","baz":"blrfl"},something="myvalue")
                evL.log(1.23,EVT_PICKUP,{"foo":"bar","baz":"blrfl"},something="Iwantthese")
                evL.log(1.23,EVT_REQUEST,{"foo":"bar","baz":"blrfl"},otherthing=17)
                evL.log(1.23,EVT_DELIVERY,{"foo":"bar","baz":"blrfl"},something="alsothose")
                evL.log(1.23,EVT_RECYCLEDELIVERY,{"foo":"bar","baz":"blrfl"},something="butnotThese")
            except EventLogException,e:
                print "got exception \"%s\""%e
        else:
            print "Wrong number of arguments!"
            describeSelf()

    else:
        describeSelf()

class TestEventLog(unittest.TestCase):
    """
    This class implements unit tests for the eventlog module.
    """
    def getReadBackBuf(self, wordList):
        try:
            sys.stdout = myStdout = StringIO.StringIO()
            main(wordList)
        finally:
            sys.stdout = sys.__stdout__
        return StringIO.StringIO(myStdout.getvalue())
    
    def compareOutputs(self, correctStr, readBack):
        correctRecs = StringIO.StringIO(correctStr)
        for a,b in zip(readBack.readlines(), correctRecs.readlines()):
            #print "<%s> vs. <%s>"%(a,b)
            self.assertTrue(a.strip() == b.strip())
    
    def test_eventlog(self):
        correctStr = """got exception "Unknown event type hello"
Trying event recycledelivery
Trying event scaledrequest
Trying event request
Trying event delivery
Trying event pickup
Trying event recycle
        """
        readBack= self.getReadBackBuf(['dummy','testlog'])
        self.compareOutputs(correctStr, readBack)
        
    def test_eventlog2(self):
        correctStr = """got exception "Unknown event type hello"
Trying event recycledelivery
Trying event scaledrequest
Trying event request
Trying event delivery
"time":1.230000, "event":"delivery", "something":"myvalue", "foo":"bar", "baz":"blrfl", 
Trying event pickup
Trying event recycle
        """
        readBack= self.getReadBackBuf(['dummy','testlog2'])
        self.compareOutputs(correctStr, readBack)

    def test_eventlog3(self):
        correctStr = """"time":1.230000, "event":"pickup", "something":"Iwantthese", "foo":"bar", "baz":"blrfl", 
"time":1.230000, "event":"delivery", "something":"alsothose", "foo":"bar", "baz":"blrfl", 
        """
        readBack= self.getReadBackBuf(['dummy','testlog3'])
        self.compareOutputs(correctStr, readBack)
        


############
# Main hook
############

if __name__=="__main__":
    main()

