#! /usr/bin/env python


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

def getPageHelp(url,tag=None):
    localeName = session_support.inlizer.currentLocaleName
    
    if tag is None:
        p = urlparse.urlparse(url)
        path = p.path[len(serverconfig.rootPath):]
        helpTemplatePath = '%s/%s/help_%s'%(pageHelpDir,localeName,path)
    else:
        path = serverconfig.rootPath
        helpTemplatePath = "%s/%s/help_%s"%(pageHelpDir,localeName,tag)
    if not helpTemplatePath.endswith('.tpl'): helpTemplatePath += '.tpl'
    print "%s"%helpTemplatePath
        
    try:
        return bottle.template(helpTemplatePath,{'pageurl':url, 'pagepath':path})
    except bottle.TemplateError:
        return _("There is no language-specific help available for this page.")

@bottle.route('/json/page-help')
def jsonPageHelp():
    try:
        url = _getOrThrowError(bottle.request.params, 'url')
        tag = _getOrThrowError(bottle.request.params, 'tag')
        print "****** Tag = " + tag
        if url=="None":
            if tag =="None":
                result = {'success':True,'value':getPageHelp("fake")}
            else:
                result = {'success':True,'value':getPageHelp(url=None,tag=tag)}
        else:  
            result = { 'success':True, 'value':getPageHelp(url) }
    except privs.PrivilegeException,e:
        _logStacktrace()
        result = { 'success':False, 'msg':'PrivilegeException: %s'%str(e)}
    except Exception,e:
        _logStacktrace()
        result = { 'success':False, 'msg':str(e)}
    return result

