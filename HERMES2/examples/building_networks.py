#! /usr/bin/env python

_hermes_svn_id_="$Id$"

import sys,os,optparse,types
import random
from SimPy.Simulation  import *
#from SimPy.SimulationTrace  import *
def register(foo,bar=None,name=None):
    pass

import constants as C
import globals as G
import recorders
import vaccinetypes
import trucktypes
import peopletypes
from vaccinetools import VaccineGroup, VaccineCollection
from peopletools import PeopleCollection
from util import NoteHolder
import warehouse
import demandmodel
import model

print "point 1"
vaccinetypes.initialize(G.vaccinePresentationsFile)
G.vaccineTypes= vaccinetypes.activeVaccineTypes
trucktypes.initialize(G.truckTypesFile)
peopletypes.initialize(G.peopleTypesFile)

sUF= 0.9  # storage utility factor
wastage= 0.01 # breakage rate
frz_walk_in_liters= 10.0
frz_liters= 3.0
cool_walk_in_liters= 12.0
cool_liters= 5.0
lotsOfSpace= 100000000.0
emptyPopPC= PeopleCollection([])
#targetPopPC= PeopleCollection([(peopletypes.getPeopleTypeByName('Newborn'),
#                               100),
#                               (peopletypes.getPeopleTypeByName('Pregnant'),
#                                102)])
targetPopPC= PeopleCollection([(peopletypes.getPeopleTypeByName('GenericPeople'),
                               100)])
storageSpace= [('freezer',
                C.ccPerLiter*sUF*(frz_walk_in_liters + frz_liters)),
               ('cooler',
                C.ccPerLiter*sUF*(cool_walk_in_liters + cool_liters)),
               ('roomtemperature',lotsOfSpace)]


myWarehouse= warehouse.Warehouse(G.vaccineTypes,
                                 G.storageTypes,
                                 storageSpace,
                                 emptyPopPC,  
                                 name='warehouse1',breakage=wastage,
                                 latitude=0.0,longitude=0.0)


myClinic= warehouse.Clinic(G.vaccineTypes,
                           G.storageTypes,
                           storageSpace,
                           targetPopPC,
                           name="myclinic",breakage=wastage,
                           latitude=0.0,longitude=0.0)

# If first param is 'None', we can sort out owner later
myAC= warehouse.AttachedClinic(myWarehouse,
                               targetPopPC,
                               name="myattached", breakage=wastage)

# This process 'places orders'.  7 is the repetition interval;
# 1 is the startup latency.
v1= vaccinetypes.getVaccineTypeByName("T_Tuberculosis")
v2= vaccinetypes.getVaccineTypeByName("T_DTP")
v3= vaccinetypes.getVaccineTypeByName("T_Measles")
trucktypes.instantiateTrucks("T_vaccine_carrier_large",1)
truck1= trucktypes.getTruckTypeByName("T_vaccine_carrier_large")
shipVC= VaccineCollection([(v2,17.0)])
shipSched= warehouse.ScheduledShipment(myWarehouse,myClinic,7.0,shipVC,
                                       startupLatency=1.0)

shipperProc= warehouse.ShipperProcess(myWarehouse,
                                      [(1.0,myClinic)],
                                      7.0, 1.0, C.shipPriority,
                                      startupLatency= 2.0,
                                      truckType=truck1)

demand= demandmodel.SimpleDemandModel(["T_DTP","T_Measles"]) # v2 and v3
useVials= warehouse.UseVials(myClinic,
                             demand,
                             30.0, # days tick interval
                             0.6,  # days patients are willing to wait
                             C.useVialPriority)

acDemand= demandmodel.SimpleDemandModel(['T_Tuberculosis'])
acUseVials= warehouse.UseVials(myAC,
                               acDemand,
                               14.0, # days tick interval
                               0.6,  # days patients are willing to wait
                               C.useVialPriority)

yearlyFactoryVC= VaccineCollection([(v1,100.0),(v2,100.0),(v3,100.0)])
factory= warehouse.Factory(myWarehouse,
                           60.0, # Days between shipments
                           yearlyFactoryVC)

activate(shipSched,shipSched.run())
activate(shipperProc,shipperProc.run())
activate(useVials,useVials.run())
activate(acUseVials,acUseVials.run())
activate(factory,factory.run())

#warehouse.debug= True
warehouse.verbose= True
simulate(until=400.0)