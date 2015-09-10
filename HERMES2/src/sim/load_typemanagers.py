#! /usr/bin/env python

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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


__doc__=""" load_typemanagers.py
Load all of the typemanagers used by hermes
"""
_hermes_svn_id_ = "$Id$"

import sys
import abstractbaseclasses
import util
import typemanager
import peopletypes
import storagetypes
import trackabletypes
import vaccinetypes
import trucktypes
import fridgetypes
import icetypes
import packagetypes
import stafftypes
import perdiemtypes


class TypeManagerLoader(object):
    """
    Class used to provide tools to load the typemanager,
    used by loadTypeManagers()
    """

    def _readTypeRecords(self, fileName1, fileName2, whatType):
        assert not self.shdNet, \
            "Tried to read CSV type records when database expected"
        if fileName1 is not None:
            self.typeManager.addTypeRecordsFromFile(fileName1, whatType,
                                                    self.verbose, self.debug)
        if fileName2 is not None:
            self.typeManager.addTypeRecordsFromFile(fileName2, whatType,
                                                    self.verbose, self.debug)

    def _importTypeRecords(self, fileName, whatType):
        if fileName is None:
            return

        assert self.shdNet, \
            "Tried to load type records from database when CSV expected"
        shdTypes = getattr(self.shdNet, fileName)
        recs = map(lambda t: t.createRecord(), shdTypes.values())
        self.typeManager.addTypeRecordsFromRecs(recs, whatType,
                                                self.verbose, self.debug)

    def _getDBRecs(self, attr):
        return map(lambda t: t.createRecord(),
                   getattr(self.shdNet, attr).values())

    def __init__(self, userInput, unifiedInput, sim, verbose = False, debug = False):
        #
        #  Create the sim-wide type manager, and define all initially known
        #  types.  Order is important, as later types are built upon earlier
        #  types.
        #
        self.userInput = userInput
        self.sim = sim
        self.verbose = verbose
        self.debug = debug

        self.shdNet = sim.shdNet
        shdNet = sim.shdNet

        self.typeManager = typemanager.TypeManager([], verbose=verbose,
                                                   debug=debug, sim=sim)
        trackableTypes = trackabletypes.TrackableTypeManager(self.typeManager)

        # Import the storage type names and make them active;
        # they are needed in parsing files below.
        for stn in storagetypes.storageTypeNames:
            self.typeManager.addType({"Name": stn}, storagetypes.StorageType,
                                     verbose, debug)
            self.typeManager.getTypeByName(stn)
        # make a special outdoors type that can be used when we wish to track and 
        # differentiate room temperature storage. 
        self.typeManager.addType({"Name": "outdoorDiscard"}, storagetypes.StorageType,
                                     verbose, debug)
        if sim.userInput.getValue("limitedroomtemp"):
            print "*******************************************"
            print "**** limited room temperature *************"
            print "*******************************************"

            # this is gross and should be fixed:
            # make "outdoors" storage type visible from a high level because very little is accessible
            # in the weeds of fridge storage routines.  Ultimately it should be attached somewhere to
            # the fridge outdoors in some way but attaching it is proving very frustrating right now.
            #
            # this also has the effect of activating this type
            storagetypes.OUTDOORS = self.typeManager.getTypeByName("outdoorDiscard")
        else:
            storagetypes.OUTDOORS = self.typeManager.getTypeByName("roomtemperature")

        # genericPeopleTypeName is a hold-over from ancient models which
        # did not specify population types.  'default' is the name of a
        # truck that serves the same function.
        sourceList = [({'Name': peopletypes.genericPeopleTypeName},
                       None, peopletypes.PeopleType),
#                       ({"Name": "default", "CoolVolumeCC": 1.0e9,
#                         "Note": "default truck type"},
#                        None, trucktypes.TruckType)
                      ]

        # Order is important in these imports, since some type definitions
        # include references to other types
        if shdNet:
            sourceList += [(self._getDBRecs('people'),
                            None, peopletypes.PeopleType),
                           (self._getDBRecs('packaging'),
                            None, packagetypes.PackageType),
                           (self._getDBRecs('trucks'),
                            None, trucktypes.TruckType),
                           (self._getDBRecs('staff'),
                            None, stafftypes.StaffType),
                           (self._getDBRecs('vaccines'),
                            vaccinetypes.VaccineType,
                            vaccinetypes.DeliverableVaccineType),
                           (self._getDBRecs('ice'),
                            None, icetypes.IceType),
                           (self._getDBRecs('fridges'),
                            None, fridgetypes.FridgeType),
                           (self._getDBRecs('perdiems'),
                            None, perdiemtypes.PerDiemType)
                           ]
        else:
            sourceList += [([userInput['peoplefile'],
                             unifiedInput.peopleFile],
                            None, peopletypes.PeopleType),
                           ([userInput['packagefile'],
                             unifiedInput.packageFile],
                            None, packagetypes.PackageType),
                           ([userInput['truckfile'],
                             unifiedInput.truckFile],
                            None, trucktypes.TruckType),
                           ([userInput['stafffile'],
                             unifiedInput.staffFile],
                            None, stafftypes.StaffType),
                           ([userInput['vaccinefile'],
                             unifiedInput.vaccineFile],
                            vaccinetypes.VaccineType,
                            vaccinetypes.DeliverableVaccineType),
                           ([userInput['icefile'],
                             unifiedInput.iceFile],
                            None, icetypes.IceType),
                           ([userInput['fridgefile'],
                             unifiedInput.fridgeFile],
                            None, fridgetypes.FridgeType),
                           ([userInput['perdiemfile'],
                             unifiedInput.perDiemFile],
                            None, perdiemtypes.PerDiemType),
                           ]
        trackableTypes.importRecords(sourceList,
                                     self.verbose, self.debug)

        # dictionary of the individual type managers by subTypeKey
        tms = {c.subTypeKey: c(self.typeManager)
               for c in util.createSubclassIterator(typemanager.SubTypeManager)}

        # Pull in any package types not mentioned explicitly but contained in
        # package types that are mentioned
        for name in tms['packaging'].getAllValidTypeNames():
            pkgType = tms['packaging'].getTypeByName(name, activateFlag=False)
            tms['shippables'].getTypeByName(pkgType.containsStr,
                                            activateFlag=False).addPackageType(pkgType)

        self.typeManagers = tms


def loadTypeManagers(userInput, unifiedInput, sim, verbose = False, debug = False):
    """
    Load the typemanager and import all of the types from the input files
    """
    tml = TypeManagerLoader(userInput, unifiedInput, sim, verbose, debug)
    return (tml.typeManager, tml.typeManagers)

