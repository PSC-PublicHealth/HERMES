#!/usr/bin/env python

####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id: google_earth_hooks.py 1435 2013-09-12 18:31:51Z welling $"

import sys,os,os.path,time,json,math,types
import bottle
from sqlalchemy.exc import SQLAlchemyError
import ipath
import site_info
import shadow_network_db_api
import privs
import session_support_wrapper as session_support
import shadow_network
import util
import kml_jquery_shdNtwk as kml

from HermesServiceException import HermesServiceException
from ui_utils import _logMessage, _logStacktrace, _safeGetReqParam, _getOrThrowError

## If executing under mod_wsgi, we need to add the path to the source
## directory of this script.
sI = site_info.SiteInfo()

inlizer=session_support.inlizer
_=session_support.translateString

#def googleEarthTopPage():
@bottle.route('/google_earth_demo')
def googleEarthTopPage(db, uiSession):
    modelId = _safeGetReqParam(bottle.request.params,'modelId',isInt=True)
    runId = _safeGetReqParam(bottle.request.params,'runId',isInt=True)    
    ## Get the appropriate KMLString and extract it to a file
    return bottle.template("google_earth_demo.tpl",{"breadcrumbPairs":[("top",_("Welcome"))],
                               "pageHelpText":_("This is intended to show page-specific help")},
                               _=_,inlizer=inlizer,modelId=modelId,runId=runId)


@bottle.route('/json/google-earth-kmlstring')
def jsonGoogleEarthKMLString(db,uiSession):
    try:
        modelId = _getOrThrowError(bottle.request.params,'modelId',isInt=True)
        resultsId = _getOrThrowError(bottle.request.params,'resultsId',isInt=True)
        #print "ModelId = " + str(modelId) + " ResultsId = " + str(resultsId)
        uiSession.getPrivs().mayReadModelId(db,modelId)
        m = shadow_network_db_api.ShdNetworkDB(db,modelId)
        r = m.getResultById(resultsId)
    
        result = {}
    
        kmlString = r.getKmlVizString()
        if kmlString is None or kmlString == '':
            _logMessage("Building KML visualization")
            kDate = kml.KMLDate(2013,1,1)
            viz = kml.KMLVisualization(shadow_network_db_= m, 
                                       resultsID_= resultsId,    
                                       kmlDate_=kDate,
                                       title_="GEViz")
            if viz is None:
                raise Exception
            _logMessage("Done making viz")
            viz.build()
            _logMessage("Done building")
            viz.output() 
            _logMessage("Done outputing")
         
        kmlString = r.getKmlVizString()
        
        if kmlString is None or kmlString == "":
            result['kmlString'] = ''
        else:
            result['kmlString'] = kmlString.replace('\n','')
            
        result['success'] = True
        return result
    except Exception,e:
        result = {'success':False, 'msg':str(e)}
        return result

    
    