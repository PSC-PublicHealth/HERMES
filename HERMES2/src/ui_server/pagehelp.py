#! /usr/bin/env python

########################################################################
# Copyright C 2012, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

__doc__ = """pagehelp
This module provides help text.
"""

_hermes_svn_id_="$Id$"

import os,os.path,urlparse
import bottle
import serverconfig
import privs
import session_support_wrapper as session_support
from ui_utils import _getOrThrowError, _logStacktrace

pageHelpDir = 'pagehelp'

def getPageHelp(url):
    p = urlparse.urlparse(url)
    path = p.path[len(serverconfig.rootPath):]
    localeName = session_support.inlizer.currentLocaleName
    helpTemplatePath = '%s/%s/help_%s'%(pageHelpDir,localeName,path)
    if not helpTemplatePath.endswith('.tpl'): helpTemplatePath += '.tpl'
    try:
        return bottle.template(helpTemplatePath,{'pageurl':url, 'pagepath':path})
    except bottle.TemplateError:
        return _("There is no language-specific help available for this page.")

@bottle.route('/json/page-help')
def jsonPageHelp():
    try:
        url = _getOrThrowError(bottle.request.params, 'url')
        
        result = { 'success':True, 'value':getPageHelp(url) }
    except privs.PrivilegeException,e:
        _logStacktrace()
        result = { 'success':False, 'msg':'PrivilegeException: %s'%str(e)}
    except Exception,e:
        _logStacktrace()
        result = { 'success':False, 'msg':str(e)}
    return result

