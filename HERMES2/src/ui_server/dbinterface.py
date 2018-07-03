#!/usr/bin/env python

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

