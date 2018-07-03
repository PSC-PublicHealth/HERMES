#!/usr/bin/env python


####################################
# Notes:
# -A session could be hijacked just by grabbing the SessionID;
#  should use an encrypted cookie to prevent this.
####################################
_hermes_svn_id_="$Id$"

import sys,os
import ipath
from input import UnifiedInput
from dbinterface import getDBSession
import shadow_network
import privs
from main import parseCommandLine

allTypesModelName = 'AllTypesModel'
userTypesModelName = 'UserTypesModel'

def typeHolderModels(db):
    "return a list of all system type holder models"
    model = db.query(shadow_network.ShdNetwork).filter(shadow_network.ShdNetwork.name==allTypesModelName).one()
    return [model]

def installTypeHolderModel():
    
    unifiedInput = UnifiedInput()  # pointers to 'unified' files
    userInputList,gblInputs= parseCommandLine()

    userInput = userInputList[0]
    userInputFile = gblInputs['input_files'][0]
    userInputFile,_,_ = userInputFile.partition(":")
    
    shdTypes = shadow_network.ShdTypes()
    shdTypes.loadShdNetworkTypeManagers(userInput, unifiedInput)

    net = shadow_network.ShdNetwork([], [], [], shdTypes, name=allTypesModelName)
    session = getDBSession()
    session.add(net)
    session.commit()
    privs.Privileges(1).registerModelId(session, net.modelId,1,1)


def installUserTypeHolderModel():
    # this will need to be updated 
    shdTypes = shadow_network.ShdTypes()
    net = shadow_network.ShdNetwork([], [], [], shdTypes, name=userTypesModelName)
    session = getDBSession()
    session.add(net)
    session.commit()
    privs.Privileges(2).registerModelId(session, net.modelId,2,2)
    

def main():
    installTypeHolderModel()
    installUserTypeHolderModel()

############
# Main hook
############

if __name__=="__main__":
    main()

