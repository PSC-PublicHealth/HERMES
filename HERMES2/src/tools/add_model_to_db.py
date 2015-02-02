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

__doc__=""" Takes a .kvp file as input; adds that model to the database
"""
_hermes_svn_id_="$Id$"
import ipath

import os.path

import input
import globals
from main import parseCommandLine
# more delayed imports below, so that values in globals can be changed before import

def isModelNameUnique(modelName):
    #too many imports
    #todo: trim to only necessary
    from alembic import op
    import sqlalchemy as sa
    import ipath
    import shadow_network
    import privs
    from typeholdermodel import allTypesModelName, installUserTypeHolderModel
    from db_routines import DbInterface
    import shadow_network_db_api
    import util
    import site_info
    import csv_tools
    dbInterface = DbInterface()
    conn = dbInterface.engine.connect()
    meta = dbInterface.Base.metadata

    models = sa.Table('models', meta, autoload=True, autoload_with=conn.engine)
    unique = True
    for row in conn.execute(sa.select([models]).where(models.c.name==modelName)):
        unique = False
        break
    return unique

def main():
    unifiedInput = input.UnifiedInput()  # pointers to 'unified' files
    userInputList,gblInputs= parseCommandLine()

    globals.deterministic= gblInputs['deterministic']

    # Delayed inputs- we wanted to modify globals before causing these modules to load
    # we don't need hermes or util yet but this is a reminder that when we do need them
    # that we shouldn't load them at the top.
    #import hermes
    #import util
    import shadow_network
    import session_support_wrapper as session_support
    import db_routines
    from privs import Privileges
    
    #import load_typemanagers

    iface = db_routines.DbInterface(echo=False)
    iface.createTables()
    session = iface.Session()

    for idx,userInput in enumerate(userInputList):
        inputName = userInput.definitionFileName
        if inputName is None:
            modelName = 'model_%d'%idx
        else:
            modelName = os.path.splitext(os.path.split(inputName)[1])[0]
        
        if ( gblInputs['no_overwrite_db'] and not isModelNameUnique(modelName) ):
            #raise Exception('Model-name "%s" already exists'%(modelName))
            print 'Model-name "%s" already exists'%(modelName)
            continue
        
        shdTypes = shadow_network.ShdTypes()
        shdTypes.loadShdNetworkTypeManagers(userInput, unifiedInput)
        net = shadow_network.loadShdNetwork(userInput, shdTypes, name=modelName)
        net.attachParms(inputName)

        iface = db_routines.DbInterface(echo=False)
        #iface.dropTables(IReallyWantToDoThis=True)
        #return
    
        iface.createTables()
        
        #conn = iface.engine.connect()
        #ins = net.insert()  
        #conn.execute(ins)
        session.add(net)
        session.commit()
        Privileges(2).registerModelId(session,net.modelId,2,2)
############
# Main hook
############

if __name__=="__main__":
    main()

