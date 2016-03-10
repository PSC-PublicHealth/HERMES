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

import sys,os,os.path
import ipath
import argparse
import bottle
import runserverconfig
import site_info

from HermesServiceException import HermesServiceException
from ui_utils import _logFileName, _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError, _smartStrip

_logFileName = os.path.join(site_info.SiteInfo().scratchDir(),"runLog.log")
app = bottle.app()
root=bottle.Bottle()
root.mount(runserverconfig.rootPath,app)
#bottle.Bottle(catchall=True)

@app.route('/run')
def run():
    return "I will run a job"

bottle.run(app=root, host="localhost",port=13500)
