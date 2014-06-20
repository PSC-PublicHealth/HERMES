#!/usr/bin/env python

####################################
# Notes:

####################################
_hermes_svn_id_="$Id$"

import argparse
import ipath
import bottle
import serverconfig
import matcher
import ui_utils
import site_info

import sys, os, os.path

ui_utils._logFileName = os.path.join(site_info.SiteInfo().scratchDir(), 'standalone.log')
ui_utils._logFileHandle = sys.stdout

rootPath = serverconfig.rootPath

root= bottle.Bottle(catchall=True)
#root.mount(matcher.application, rootPath)
root.mount(rootPath, matcher.application)
oldStdout = sys.stdout
oldStderr = sys.stderr

parser = argparse.ArgumentParser(description='HERMES Standalone Web Server')

parser.add_argument('-p', '--promiscuous', action='store_true',
        help = 'Default is to listen only to connections from localhost; ' + 
            'use this flag to accept connections from any address')
parser.add_argument('-P', '--port', default='8080', type=int,
        help = 'Port to listen on')

args = parser.parse_args()

kwargs = dict(reloader=True, debug=True, port=args.port)

if args.promiscuous:
    kwargs['host'] = '0.0.0.0'

with ui_utils.loggingFileHandle() as f:
    sys.stdout = f
    sys.stderr = f

    matcher._logMessage('starting up under standalone server')
    (major, minor, rev) = bottle.__version__.replace('-','.').split('.')

    if int(major) == 0 and int(minor) < 11:
        kwargs['debug'] = False
    
    bottle.run(app=root, **kwargs)

sys.stderr = oldStderr
sys.stdout = oldStdout
