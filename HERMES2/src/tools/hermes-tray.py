from winsystray import SysTrayIcon
import subprocess
import time
import webbrowser
import sys
import urllib2
import os
DETACHED_PROCESS = 0x00000008

seconds_to_attempt = 15
url = 'http://localhost:8080/bottle_hermes/top'

def start_browser(sysTrayIcon=None):
    webbrowser.open(url,new=2)
def bye(sysTrayIcon):
    proc.terminate()

isfirstrun = not os.path.isfile(os.environ['userprofile']+'\standalone.log')
os.environ["PATH"] = os.path.dirname(os.path.abspath(sys.argv[0]))+'\\python;'+os.environ["PATH"]
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])) + '\\..\\ui_server')
proc = subprocess.Popen(['pythonw','standalone_server.py'],shell=False,stdin=None,stdout=None,stderr=None,close_fds=True,creationflags=DETACHED_PROCESS)    
#time.sleep(3)
#pid = proc.pid

foundHttpServer = False
for i in xrange(seconds_to_attempt):
    time.sleep(1)
    try:
        urllib2.urlopen(url)
        foundHttpServer = True
        break
    except urllib2.HTTPError, e:
        urlError = 'HTTP Error ' + e.code
        pass
    except urllib2.URLError, e:
        urlError = repr(e.args)
        pass
if foundHttpServer == True:
    start_browser()
    hover_text = "HERMES"
    baloon_title = "HERMES"
    baloon_text = "First time running HERMES? Restart or quit it from here."
    menu_options = (('Launch', None, start_browser),)
    SysTrayIcon('..\\ui_www\\icons\\favicon.ico', hover_text, menu_options, baloon_title, baloon_text, on_quit=bye, default_menu_index=1,window_class_name=None,popup_on_start=isfirstrun)
else:
    print "Cannot run HERMES GUI:\n" + urlError 
    sys.exit(1)