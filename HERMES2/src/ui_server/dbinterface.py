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
__doc__ = """dbinterface
This module exists to avoid circular import problems in those modules accessing the database
through the shared session and interface.
"""

_hermes_svn_id_="$Id$"

import sys,os
import site_info
import db_routines

_iface = None # lazy initialization 
_dbsession = None # lazy initialization

sI = site_info.SiteInfo()

def getDBInterface():
    global _iface
    if _iface is None:
        _iface = db_routines.DbInterface(echo=False, dbType=sI.dbType())  
    return _iface

def getDBSession():
    global _dbsession
    if _dbsession is None:
        _dbsession = getDBInterface().Session()
    return _dbsession

