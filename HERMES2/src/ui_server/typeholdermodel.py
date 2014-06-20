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


def main():
    installTypeHolderModel()

############
# Main hook
############

if __name__=="__main__":
    main()

