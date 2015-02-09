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
import util

import sys, os, os.path, codecs

ui_utils._logFileName = os.path.join(site_info.SiteInfo().scratchDir(), 'standalone.log')
#ui_utils._logFileHandle = sys.stdout

rootPath = serverconfig.rootPath

root= bottle.Bottle(catchall=True)
#root.mount(matcher.application, rootPath)
root.mount(rootPath, matcher.application)
oldStdout = sys.stdout
oldStderr = sys.stderr

parser = argparse.ArgumentParser(description='HERMES Standalone Web Server',
                                 prefix_chars='-+')

parser.add_argument('-p', '--promiscuous', action='store_true',
        help = 'Default is to listen only to connections from localhost; ' + 
            'use this flag to accept connections from any address')
parser.add_argument('+p', '++promiscuous', '--no-promiscuous', action='store_false',
                    help=argparse.SUPPRESS)
parser.add_argument('-P', '--port', default='8080', type=int,
        help = 'Port to listen on')
parser.add_argument('+P', '++port', action='store_const', const=8080,
                    help=argparse.SUPPRESS)
parser.add_argument('-d', '--debug', action='store_false',
                    help = 'turn on debug mode')
parser.add_argument('+d', '++debug', '--no-debug', action='store_true',
                    help=argparse.SUPPRESS)
parser.add_argument('-o', '--logfile', default=ui_utils._logFileName,
                    help = 'set logfile name, use +o to disable logfile' +
                    'defaults to %s'%ui_utils._logFileName)
parser.add_argument('+o', '++logfile', '--no-logfile', action='store_const', const=None,
                    help = argparse.SUPPRESS)
parser.add_argument('-m', '--mirror', action='store_true',
                    help = 'mirror logging to stdout')
parser.add_argument('+m', '++mirror', '--no-mirror', action='store_false',
                    help=argparse.SUPPRESS)
args = parser.parse_args()
print args

if args.mirror:
    ui_utils._logFileHandle = sys.stdout
else:
    ui_utils._logFileHandle = None

ui_utils._logFileName = args.logfile

kwargs = dict(reloader=True, debug=args.debug, port=args.port)

if args.promiscuous:
    kwargs['host'] = '0.0.0.0'

with ui_utils.loggingFileHandle() as f:
    encoding = util.getPreferredOutputEncoding()
    sys.stdout = codecs.getwriter(encoding)(f, 'replace')
    sys.stderr = codecs.getwriter(encoding)(f, 'replace')

    matcher._logMessage('starting up under standalone server')
    (major, minor, rev) = bottle.__version__.replace('-','.').split('.')

    if int(major) == 0 and int(minor) < 11:
        kwargs['debug'] = False
    
    bottle.run(app=root, **kwargs)

sys.stderr = oldStderr
sys.stdout = oldStdout
