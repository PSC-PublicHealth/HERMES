#!/usr/bin/env python

####################################
# Notes:

####################################
_hermes_svn_id_="$Id$"

import sys,os,os.path
import bottle
import site_info
import HermesService

HermesService._logFileName= 'standalone.log'
bottle.debug(True)

root= bottle.Bottle()
root.mount(HermesService.application, 'bottle_hermes')

@root.route('/hermes/output/:filepath')
def serveRegularFiles(filepath='hermes_ui.html'):
    sI = site_info.SiteInfo()
    fullDir= os.path.join(sI.srcDir(),'json/output')
    HermesService._logMessage('Serving %s from %s'%(filepath,fullDir))
    return bottle.static_file(filepath,root=fullDir)

HermesService._logMessage('starting up under standalone server')
bottle.run(root,port=8080)

