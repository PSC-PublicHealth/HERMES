#! /usr/bin/env python

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

"""
Start HERMES standalone_server and launch Chromium embedded
"""
from __future__ import print_function
import platform, sys, subprocess, os, shlex, time, urllib, socket

import psutil
from cefpython3 import cefpython as cef

def main():
    url = "http://localhost:8080/bottle_hermes/top"
    os.chdir("../ui_server")
    worked = False
    procServer = hiddenProcess("python standalone_server.py")
    for second in range(15): # seconds to wait for the started server to fully respond with "200 OK"
        if getHttpCode(url) == 200: # server up
            worked = True
        time.sleep(1) # second
    if worked:
        startBrowser(url)
        kill(procServer.pid) # then clean up
    else:
        print("Error starting server")
        kill(procServer.pid) # just in case our server detector failed and it actually started
        sys.exit(1) # return error

def getHttpCode(url,timeout=30): # seconds to wait for the server to even handshake, and not have IOError
    pingstarttime = time.clock()
    elapsedtime = 0
    httpcode = None
    socket.setdefaulttimeout(0.5)  # seconds for urllib.urlopen timeout, otherwise may hang forever
    while ( httpcode == None ) and ( elapsedtime < timeout ):
        elapsedtime = time.clock() - pingstarttime
        try:
            httpcode = urllib.urlopen(url).getcode()
        except IOError:
            continue
    return httpcode

def hiddenProcess(cmd):
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
    p = subprocess.Popen(shlex.split(cmd),startupinfo=startupinfo)
    return p

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.terminate()
    process.wait(timeout=5) # seconds

def startBrowser(url):
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    settings = {}
    
    WINDOWS = (platform.system() == "Windows")
    if WINDOWS:
        settings["auto_zooming"] = ""  # Disable faulty zooming during High DPI support
    cef.Initialize(settings)
    #cef.DpiAware.SetProcessDpiAware()  # Do not use faulty init of High DPI support, it flickers on Windows
    
    # To get this to display without blurriness in high-DPI Windows systems during development mode
    # Set your python.exe Compatibility Properties to:
    # Disable display scaling on high DPI settings
    # or run unblurred_win.py found in this same directory
    
    cef.CreateBrowserSync(url=url, window_title="HERMES")
    cef.MessageLoop()
    cef.Shutdown()


def check_versions():
    assert cef.__version__ >= "55.3", "CEF Python v55.3+ required to run this"

if __name__ == '__main__':
    main()
