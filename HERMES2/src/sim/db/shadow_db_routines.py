#! /usr/bin/env python



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


def resetInterface():
    print "!!!!!! Resetting Interface"
    iface.engine.dispose()
        
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
    print "CALLING THIS"
    if session_in is None:
        session = iface.Session()
    else:
        session = session_in

    resultsGroup = shd.HermesResultsGroup(modelId, name)
    
    session.add(resultsGroup)
    #session.commit()

    aveResults = shd.HermesResults(resultsGroup,resultsType='average',runNumber=99999)
    
    session.add(aveResults)
    try:
        session.commit()
    except:
        session.rollback()
    #finally:
    #    session.flush()
    #resultsGroup.results.append(aveResults)
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
    results = session.query(shd.HermesResults).filter_by(resultsGroupId=resultsGroupId)
    for result in resultsGroup.results:
        print "exists = {0}".format(result.resultsId)
    #resultsGroup.results = []
#     for result in results:
#         if result.resultsType != "average":
#             print "RES = {0}".format(result.resultsId)
#             resultsGroup.results.append(result)
#         
    resultsGroup._mergeResults(net)
    
    try:
        session.commit()
    except:
        session.rollback()
    finally:
        session.flush()
    session.flush()
    
    
def commitResultsEntry(results, session_in=None,doFlush=True):
    if session_in is None:
        session = iface.Session()
    else:
        session = session_in
    session.add(results)
    try:
        session.commit()
    except:
        session.rollback()
    finally:
        if doFlush:
            session.flush()
    #session.commit()
    #session.flush()
    #resultsGroup = session.query(shd.HermesResultsGroup).filter_by(modelId=modelId,resultsGroupId=results.resultsGroupIdlt).one())
