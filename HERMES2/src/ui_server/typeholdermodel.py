#!/usr/bin/env python

###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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

