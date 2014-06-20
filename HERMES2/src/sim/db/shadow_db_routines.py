#! /usr/bin/env python

########################################################################
# Copyright C 2013, Pittsburgh Supercomputing Center (PSC).            #
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

__doc__=""" 
routines for interfacing with a db version of the shadow network
"""
_hermes_svn_id_="$Id$"


import shadow_network as shd
import db_routines as db

try:
    iface = db.DbInterface()
except:
    pass


def getDbInputRecs(model, resultsGroup=None, session_in=None):
    "get the input records from a db model id."

    if session_in is None:
        session = iface.Session()
    else:
        session = session_in

    parms = session.query(shd.ShdParameter).filter_by(modelId=model,resultsGroupId=resultsGroup)
    return map(lambda p: p.toStr(), parms)

def getNetwork(model, session_in=None):
    "get a shadow network from a db model id."

    if session_in is None:
        session = iface.Session()
    else:
        session = session_in

    net = session.query(shd.ShdNetwork).filter_by(modelId=model).one()
    # this is a hack that should get fixed.
    # save the session within the network so that it doesn't get garbage collected.
    # we need to work out a clear line of when sessions should come and go.
    net.session = session
    return net


def addResultsGroup(modelId, name, session_in=None):
    "create, attach and return a new results group id from a db model."

    if session_in is None:
        session = iface.Session()
    else:
        session = session_in

    resultsGroup = shd.HermesResultsGroup(modelId, name)
    
    session.add(resultsGroup)
    session.commit()

    aveResults = shd.HermesResults(resultsGroup,resultsType='average',runNumber=99999)
    
    session.add(aveResults)
    session.commit()
    resultsGroup.results.append(aveResults)
    # Once committed this will be reloaded with a resultsGroupId.
    # We're going to let the session be reaped by GC so we're only
    # going to return the id rather than the entire structure.
    return  resultsGroup.resultsGroupId

def averageResultsGroup(modelId, resultsGroupId, session_in=None):
     
    if session_in is None:
        session = iface.Session()
    else:
        session = session_in
    
    net = session.query(shd.ShdNetwork).filter_by(modelId=modelId).one()
    resultsGroup = session.query(shd.HermesResultsGroup).filter_by(modelId=modelId,resultsGroupId=resultsGroupId).one()
    
    resultsGroup._mergeResults(net)
    
    session.commit()
    session.flush()
    
    
def commitResultsEntry(results, session_in=None):
    if session_in is None:
        session = iface.Session()
    else:
        session = session_in
    session.add(results)
    session.commit()
