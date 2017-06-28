"""
Start HERMES standalone_server and launch Chromium embedded
"""
from __future__ import print_function
from cefpython3 import cefpython as cef
import platform
import sys
import subprocess, os, shlex, time, urllib
import psutil

url = "http://localhost:8080/bottle_hermes/top"

def main():
    os.chdir("../ui_server")
    worked = False
    procServer = hiddenProcess("python standalone_server.py")
    time.sleep(5) #seconds
    for second in range(2):
        httpcode = urllib.urlopen(url).getcode()
        if httpcode == 200:   # server up
            worked = True
        time.sleep(1)
    if worked:    
        startBrowser()
        # then clean up
        kill(procServer.pid)
        time.sleep(5) #seconds
    else:
        print("Error starting server")
        sys.exit(1)

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
    process.kill()

def startBrowser():
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()
    
    settings = {}
    """
    ### This code bugs out the graphics for me -Eli
    WINDOWS = (platform.system() == "Windows")
    if WINDOWS:
        settings["auto_zooming"] = "system_dpi"  # High DPI support
        # noinspection PyUnresolvedReferences, PyArgumentList
        cef.DpiAware.SetProcessDpiAware()  # Alternative is to embed manifest
    """
    
    cef.CreateBrowserSync(url=url, window_title="HERMES")
    cef.MessageLoop()
    cef.Shutdown()


def check_versions():
    assert cef.__version__ >= "55.3", "CEF Python v55.3+ required to run this"

if __name__ == '__main__':
    main()