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

__doc__=""" load_typemanagers.py
Load all of the typemanagers used by hermes
"""
_hermes_svn_id_="$Id$"

import sys
import typemanager
import peopletypes
import storagetypes
import trackabletypes
import vaccinetypes
import peopletypes
import trucktypes
import fridgetypes
import icetypes
import packagetypes
import stafftypes

class TypeManagerLoader():
    """
    Class used to provide tools to load the typemanager, used by loadTypeManagers()
    """

    def _importTypeRecords(self, fileName, whatType):
        if fileName is None:
            return
        
        if self.shdNet:
            shdTypes = getattr(self.shdNet, fileName)
            recs = map(lambda t: t.createRecord(), shdTypes.values())
            self.typeManager.addTypeRecordsFromRecs(recs, whatType, self.verbose, self.debug)
        else:
            self.typeManager.addTypeRecordsFromFile(fileName, whatType, self.verbose, self.debug)


    def __init__(self, userInput, unifiedInput, sim, verbose = False, debug = False):
        #
        #  Create the sim-wide type manager, and define all initially known types.  Order is
        #  important, as later types are built upon earlier types.
        #
        self.userInput = userInput
        self.sim = sim
        self.verbose = verbose
        self.debug = debug

        self.shdNet = sim.shdNet
        shdNet = sim.shdNet
        
        tms = {}  #dictionary of the individual type managers
        self.typeManager= typemanager.TypeManager([], verbose=verbose, debug=debug, sim=sim)
    
        for rec in [{"Name":stn} for stn in storagetypes.storageTypeNames]: 
            self.typeManager.addType(rec, storagetypes.StorageType, verbose, debug)
    
        tms['storage']= storagetypes.StorageTypeManager(self.typeManager)
        # Force the storage type names to be active; they are needed in parsing files below.
        for stn in storagetypes.storageTypeNames: tms['storage'].getTypeByName(stn)
    
        if shdNet:
            self._importTypeRecords('people', peopletypes.PeopleType)
        else:
            self._importTypeRecords(userInput['peoplefile'], peopletypes.PeopleType)
            self._importTypeRecords(unifiedInput.peopleFile, peopletypes.PeopleType)
        if not self.typeManager.validTypeName(peopletypes.genericPeopleTypeName):
            self.typeManager.addType({'Name':peopletypes.genericPeopleTypeName}, 
                                     peopletypes.PeopleType,
                                     self.verbose, self.debug)
        tms['people'] = peopletypes.PeopleTypeManager(self.typeManager)

        if shdNet:
            self._importTypeRecords('packaging', packagetypes.PackageType)
        else:
            self._importTypeRecords(userInput['packagefile'], packagetypes.PackageType)
            self._importTypeRecords(unifiedInput.packageFile, packagetypes.PackageType)
        tms['packaging'] = packagetypes.PackageTypeManager(self.typeManager)

        if shdNet:
            self._importTypeRecords('trucks', trucktypes.TruckType)
        else:
            self._importTypeRecords(userInput['truckfile'], trucktypes.TruckType)
            self._importTypeRecords(unifiedInput.truckFile, trucktypes.TruckType)
        self.typeManager.addType({"Name":"default", "CoolVolumeCC":1.0e9, 
                                  "Note":"default truck type"},
                                 trucktypes.TruckType, self.verbose, self.debug)
        tms['trucks']= trucktypes.TruckTypeManager(self.typeManager)

        if shdNet:
            self._importTypeRecords('staff', stafftypes.StaffType)
        else:
            self._importTypeRecords(userInput['stafffile'], stafftypes.StaffType)
            self._importTypeRecords(unifiedInput.staffFile, stafftypes.StaffType)
        tms['staff'] = stafftypes.StaffTypeManager(self.typeManager)
         
        tms['shippables']= trackabletypes.TrackableTypeManager(self.typeManager)
        if shdNet:
            vRecs = map(lambda t: t.createRecord(), shdNet.vaccines.values())
            iRecs = map(lambda t: t.createRecord(), shdNet.ice.values())
            fRecs = map(lambda t: t.createRecord(), shdNet.fridges.values())
            tms['shippables'].importRecords([(vRecs,
                                              vaccinetypes.VaccineType, 
                                              vaccinetypes.DeliverableVaccineType),
                                             (iRecs,
                                              None, icetypes.IceType),
                                             (fRecs,
                                              None, fridgetypes.FridgeType)],
                                            self.verbose, self.debug)
        else:
            tms['shippables'].importRecords([([userInput['vaccinefile'], unifiedInput.vaccineFile],
                                              vaccinetypes.VaccineType, vaccinetypes.DeliverableVaccineType),
                                             ([userInput['icefile'], unifiedInput.iceFile],
                                              None, icetypes.IceType),
                                             ([userInput['fridgefile'], unifiedInput.fridgeFile],
                                              None, fridgetypes.FridgeType)],
                                            self.verbose, self.debug)
        tms['vaccines']= vaccinetypes.VaccineTypeManager(self.typeManager)
        tms['ice'] = icetypes.IceTypeManager(self.typeManager)
        tms['fridges'] = fridgetypes.FridgeTypeManager(self.typeManager)

        for name in tms['packaging'].getAllValidTypeNames():
            pkgType = tms['packaging'].getTypeByName(name,activateFlag=False)
            tms['shippables'].getTypeByName(pkgType.containsStr, activateFlag=False).addPackageType(pkgType)
            
        self.typeManagers = tms
        

def loadTypeManagers(userInput, unifiedInput, sim, verbose = False, debug = False):
    """
    Load the typemanager and import all of the types from the input files
    """
    tml = TypeManagerLoader(userInput, unifiedInput, sim, verbose, debug)
    return (tml.typeManager, tml.typeManagers)

