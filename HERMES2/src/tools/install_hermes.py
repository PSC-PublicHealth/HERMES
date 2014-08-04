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

__doc__=""" 
This script is supposed to create and populate the database and do other 
steps necessary to create a runnable HERMES UI environment.
"""
_hermes_svn_id_="$Id$"

import platform
import sys, os, os.path, subprocess
import ipath
import site_info
from db_routines import DbInterface
import db_routines
import util
import shadow_network
import privs
from typeholdermodel import allTypesModelName

import sqlalchemy as sa

sI = site_info.SiteInfo()

_uri = None

def getURI():
    global _uri
    if _uri is None:
        _uri = DbInterface().getURI()
    return _uri

def createAlembicIni():
    url = getURI()
    print 'url is '+url
    path = os.path.join(sI.srcDir(),'../..')
    
    if os.path.lexists(os.path.join(path,'alembic.ini')):
        count = 0
        while True:
            if count==0: savName = 'alembic.ini.sav'
            else: savName = 'alembic.ini.sav%d'%count
            if os.path.lexists(os.path.join(path,savName)):
                count += 1
            else:
                break
        os.rename(os.path.join(path,'alembic.ini'),os.path.join(path,savName))
    
    with open(os.path.join(path,'alembic.ini.prototype'),'r') as ifile:
        with open(os.path.join(path,'alembic.ini'),'w') as ofile:
            for rec in ifile:
                if rec.strip().startswith('sqlalchemy.url ='):
                    ofile.write('sqlalchemy.url = %s\n'%url)
                else:
                    ofile.write(rec)

def createDBFromCode():
    dbI = DbInterface()
    dbI.createTables()

def createDBFromHistory():
    """
    This is basically an auto-generated Alembic script, modified
    to call SQLAlchemy directly.
    
    complete creation up to r1481
    
    Revision ID: 3ce5a00e170b
    Revises: None
    Create Date: 2013-10-14 16:41:01.235910
    
    """
    
    # revision identifiers, used by Alembic.
    revision = '3ce5a00e170b'
    down_revision = None

    engine = sa.create_engine(getURI(), echo=True)    
    md = sa.MetaData()
    
    ### commands auto generated by Alembic - please adjust! ###
    storeVialsBlobHolder = sa.Table('storeVialsBlobHolder', md,
    sa.Column('blobId', sa.Integer(), nullable=False),
    sa.Column('blob', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('blobId')
    )
    uisessions = sa.Table('uisessions', md,
    sa.Column('sessionId', sa.String(length=36), nullable=False),
    sa.Column('sessionDict', sa.PickleType(), nullable=True),
    sa.PrimaryKeyConstraint('sessionId')
    )
    blobHolder = sa.Table('blobHolder', md,
    sa.Column('blobId', sa.Integer(), nullable=False),
    sa.Column('blob', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('blobId')
    )
    prvusers = sa.Table('prvusers', md,
    sa.Column('userId', sa.Integer(), nullable=False),
    sa.Column('userName', sa.String(length=32), nullable=True),
    sa.PrimaryKeyConstraint('userId')
    )
    models = sa.Table('models', md,
    sa.Column('modelId', sa.Integer(), nullable=False),
    sa.Column('note', sa.String(length=4096), nullable=True),
    sa.Column('name', sa.String(length=250), nullable=True),
    sa.PrimaryKeyConstraint('modelId'),
    mysql_engine='InnoDB'
    )
    prvgroups = sa.Table('prvgroups', md,
    sa.Column('groupId', sa.Integer(), nullable=False),
    sa.Column('groupName', sa.String(length=32), nullable=True),
    sa.PrimaryKeyConstraint('groupId')
    )
    types = sa.Table('types', md,
    sa.Column('typeId', sa.Integer(), nullable=False),
    sa.Column('typeClass', sa.String(length=30), nullable=True),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('Name', sa.String(length=250), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('typeId')
    )
    parms = sa.Table('parms', md,
    sa.Column('parmId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('key', sa.String(length=250), nullable=True),
    sa.Column('value', sa.String(length=250), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('parmId')
    )
    demand = sa.Table('demand', md,
    sa.Column('demandId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('demandType', sa.CHAR(length=1), nullable=True),
    sa.Column('vaccineStr', sa.String(length=250), nullable=True),
    sa.Column('peopleStr', sa.String(length=250), nullable=True),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('demandId')
    )
    costs = sa.Table('costs', md,
    sa.Column('costId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('Name', sa.String(length=250), nullable=True),
    sa.Column('Currency', sa.String(length=250), nullable=True),
    sa.Column('PerKm', sa.Float(), nullable=True),
    sa.Column('PerYear', sa.Float(), nullable=True),
    sa.Column('PerTrip', sa.Float(), nullable=True),
    sa.Column('PerTreatmentDay', sa.Float(), nullable=True),
    sa.Column('PerDiem', sa.Float(), nullable=True),
    sa.Column('PerVial', sa.Float(), nullable=True),
    sa.Column('Level', sa.String(length=250), nullable=True),
    sa.Column('Conditions', sa.String(length=250), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('costId')
    )
    currencyConversion = sa.Table('currencyConversion', md,
    sa.Column('currencyId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('country', sa.String(length=250), nullable=True),
    sa.Column('currency', sa.String(length=250), nullable=True),
    sa.Column('code', sa.String(length=250), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('value', sa.Float(), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('currencyId')
    )
    routes = sa.Table('routes', md,
    sa.Column('routeId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('RouteName', sa.String(length=250), nullable=True),
    sa.Column('Type', sa.String(length=250), nullable=True),
    sa.Column('TruckType', sa.String(length=250), nullable=True),
    sa.Column('ShipIntervalDays', sa.Float(), nullable=True),
    sa.Column('ShipLatencyDays', sa.Float(), nullable=True),
    sa.Column('Conditions', sa.String(length=250), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('routeId')
    )
    stores = sa.Table('stores', md,
    sa.Column('storeId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('CATEGORY', sa.String(length=250), nullable=True),
    sa.Column('FUNCTION', sa.String(length=250), nullable=True),
    sa.Column('NAME', sa.String(length=250), nullable=True),
    sa.Column('idcode', sa.Integer(), nullable=True),
    sa.Column('utilizationRate', sa.Float(), nullable=True),
    sa.Column('Latitude', sa.Float(), nullable=True),
    sa.Column('Longitude', sa.Float(), nullable=True),
    sa.Column('UseVialsInterval', sa.Float(), nullable=True),
    sa.Column('UseVialsLatency', sa.Float(), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('storeId')
    )
    resultsGroup = sa.Table('resultsGroup', md,
    sa.Column('resultsGroupId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=250), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('resultsGroupId')
    )
    prvmodelaccessrights = sa.Table('prvmodelaccessrights', md,
    sa.Column('primKey', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('ownerId', sa.Integer(), nullable=True),
    sa.Column('readGroupId', sa.Integer(), nullable=True),
    sa.Column('writeGroupId', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.ForeignKeyConstraint(['ownerId'], ['prvusers.userId'], ),
    sa.ForeignKeyConstraint(['readGroupId'], ['prvgroups.groupId'], ),
    sa.ForeignKeyConstraint(['writeGroupId'], ['prvgroups.groupId'], ),
    sa.PrimaryKeyConstraint('primKey')
    )
    prvusergroupassociation = sa.Table('prvusergroupassociation', md,
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['prvgroups.groupId'], ),
    sa.ForeignKeyConstraint(['user_id'], ['prvusers.userId'], ),
    sa.PrimaryKeyConstraint()
    )
    factoryOVW = sa.Table('factoryOVW', md,
    sa.Column('factoryOVWId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('Name', sa.String(length=250), nullable=True),
    sa.Column('OVW', sa.Float(), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('factoryOVWId')
    )
    stops = sa.Table('stops', md,
    sa.Column('stopId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('RouteName', sa.String(length=250), nullable=True),
    sa.Column('idcode', sa.Integer(), nullable=True),
    sa.Column('RouteOrder', sa.Integer(), nullable=True),
    sa.Column('TransitHours', sa.Float(), nullable=True),
    sa.Column('DistanceKM', sa.Float(), nullable=True),
    sa.Column('PullOrderAmountDays', sa.Float(), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.Column('isSupplier', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('stopId')
    )
    inventory = sa.Table('inventory', md,
    sa.Column('inventoryId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('sourceType', sa.Integer(), nullable=True),
    sa.Column('idcode', sa.Integer(), nullable=True),
    sa.Column('Name', sa.String(length=250), nullable=True),
    sa.Column('invName', sa.String(length=250), nullable=True),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('inventoryId')
    )
    calendarEntries = sa.Table('calendarEntries', md,
    sa.Column('calendarEntryId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('calendarType', sa.CHAR(length=1), nullable=True),
    sa.Column('startDate', sa.Float(), nullable=True),
    sa.Column('typeId', sa.Integer(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.ForeignKeyConstraint(['typeId'], ['types.typeId'], ),
    sa.PrimaryKeyConstraint('calendarEntryId')
    )
    peopletypes = sa.Table('peopletypes', md,
    sa.Column('peopletypeId', sa.Integer(), nullable=False),
    sa.Column('DisplayName', sa.String(length=250), nullable=True),
    sa.Column('SortOrder', sa.Integer(), nullable=True),
    sa.Column('Requires', sa.String(length=250), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['peopletypeId'], ['types.typeId'], ),
    sa.PrimaryKeyConstraint('peopletypeId')
    )
    vaccinetypes = sa.Table('vaccinetypes', md,
    sa.Column('vaccinetypeId', sa.Integer(), nullable=False),
    sa.Column('DisplayName', sa.String(length=250), nullable=True),
    sa.Column('Abbreviation', sa.String(length=250), nullable=True),
    sa.Column('presentation', sa.String(length=250), nullable=True),
    sa.Column('administration', sa.String(length=250), nullable=True),
    sa.Column('dosesPerVial', sa.Integer(), nullable=True),
    sa.Column('volPerDose', sa.Float(), nullable=True),
    sa.Column('diluentVolPerDose', sa.Float(), nullable=True),
    sa.Column('pricePerVial', sa.Float(), nullable=True),
    sa.Column('pricePerDose', sa.Float(), nullable=True),
    sa.Column('priceUnits', sa.String(length=250), nullable=True),
    sa.Column('dosesPerPerson', sa.Integer(), nullable=True),
    sa.Column('freezerDays', sa.Float(), nullable=True),
    sa.Column('coolerDays', sa.Float(), nullable=True),
    sa.Column('roomtempDays', sa.Float(), nullable=True),
    sa.Column('openDays', sa.Float(), nullable=True),
    sa.Column('RandomKey', sa.Integer(), nullable=True),
    sa.Column('wastageRate', sa.Float(), nullable=True),
    sa.Column('Requires', sa.String(length=250), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['vaccinetypeId'], ['types.typeId'], ),
    sa.PrimaryKeyConstraint('vaccinetypeId')
    )
    trucktypes = sa.Table('trucktypes', md,
    sa.Column('trucktypeId', sa.Integer(), nullable=False),
    sa.Column('DisplayName', sa.String(length=250), nullable=True),
    sa.Column('CoolVolumeCC', sa.Float(), nullable=True),
    sa.Column('Storage', sa.String(length=250), nullable=True),
    sa.Column('Requires', sa.String(length=250), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['trucktypeId'], ['types.typeId'], ),
    sa.PrimaryKeyConstraint('trucktypeId')
    )
    packagetypes = sa.Table('packagetypes', md,
    sa.Column('packagetypeId', sa.Integer(), nullable=False),
    sa.Column('DisplayName', sa.String(length=250), nullable=True),
    sa.Column('Contains', sa.String(length=250), nullable=True),
    sa.Column('Count', sa.Integer(), nullable=True),
    sa.Column('Category', sa.String(length=250), nullable=True),
    sa.Column('Volume', sa.Float(), nullable=True),
    sa.Column('SortOrder', sa.Integer(), nullable=True),
    sa.Column('Requires', sa.String(length=250), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['packagetypeId'], ['types.typeId'], ),
    sa.PrimaryKeyConstraint('packagetypeId')
    )
    results = sa.Table('results', md,
    sa.Column('resultsId', sa.Integer(), nullable=False),
    sa.Column('resultsGroupId', sa.Integer(), nullable=True),
    sa.Column('runNumber', sa.Integer(), nullable=True),
    sa.Column('resultsType', sa.String(length=250), nullable=True),
    sa.Column('kmlVizStringRef', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['kmlVizStringRef'], ['blobHolder.blobId'], ),
    sa.ForeignKeyConstraint(['resultsGroupId'], ['resultsGroup.resultsGroupId'], ),
    sa.PrimaryKeyConstraint('resultsId')
    )
    storagetypes = sa.Table('storagetypes', md,
    sa.Column('storagetypeId', sa.Integer(), nullable=False),
    sa.Column('DisplayName', sa.String(length=250), nullable=True),
    sa.Column('Make', sa.String(length=250), nullable=True),
    sa.Column('Model', sa.String(length=250), nullable=True),
    sa.Column('Year', sa.String(length=250), nullable=True),
    sa.Column('Energy', sa.String(length=250), nullable=True),
    sa.Column('freezer', sa.Float(), nullable=True),
    sa.Column('cooler', sa.Float(), nullable=True),
    sa.Column('roomtemperature', sa.Float(), nullable=True),
    sa.Column('ClassName', sa.String(length=250), nullable=True),
    sa.Column('ColdLifetime', sa.Float(), nullable=True),
    sa.Column('AlarmDays', sa.Float(), nullable=True),
    sa.Column('SnoozeDays', sa.Float(), nullable=True),
    sa.Column('Requires', sa.String(length=250), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['storagetypeId'], ['types.typeId'], ),
    sa.PrimaryKeyConstraint('storagetypeId')
    )
    icetypes = sa.Table('icetypes', md,
    sa.Column('icetypeId', sa.Integer(), nullable=False),
    sa.Column('DisplayName', sa.String(length=250), nullable=True),
    sa.Column('VolCC', sa.Float(), nullable=True),
    sa.Column('FridgeType', sa.String(length=250), nullable=True),
    sa.Column('RandKey', sa.Integer(), nullable=True),
    sa.Column('ClassName', sa.String(length=250), nullable=True),
    sa.Column('Requires', sa.String(length=250), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['icetypeId'], ['types.typeId'], ),
    sa.PrimaryKeyConstraint('icetypeId')
    )
    typeSummary = sa.Table('typeSummary', md,
    sa.Column('summaryId', sa.Integer(), nullable=False),
    sa.Column('typeClass', sa.String(length=30), nullable=True),
    sa.Column('resultsId', sa.Integer(), nullable=True),
    sa.Column('Name', sa.String(length=250), nullable=True),
    sa.Column('Type', sa.String(length=250), nullable=True),
    sa.ForeignKeyConstraint(['resultsId'], ['results.resultsId'], ),
    sa.PrimaryKeyConstraint('summaryId')
    )
    routesRpt = sa.Table('routesRpt', md,
    sa.Column('routesRptId', sa.Integer(), nullable=False),
    sa.Column('resultsId', sa.Integer(), nullable=True),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('RouteName', sa.String(length=250), nullable=True),
    sa.Column('RouteFill', sa.Float(), nullable=True),
    sa.Column('RouteTrips', sa.Float(), nullable=True),
    sa.Column('RouteTruckType', sa.String(length=250), nullable=True),
    sa.Column('triptimes_multival', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.ForeignKeyConstraint(['resultsId'], ['results.resultsId'], ),
    sa.ForeignKeyConstraint(['triptimes_multival'], ['blobHolder.blobId'], ),
    sa.PrimaryKeyConstraint('routesRptId')
    )
    storesRpt = sa.Table('storesRpt', md,
    sa.Column('storesRptId', sa.Integer(), nullable=False),
    sa.Column('resultsId', sa.Integer(), nullable=True),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('code', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(length=250), nullable=True),
    sa.Column('one_vaccine_outages', sa.Float(), nullable=True),
    sa.Column('overstock_time', sa.Float(), nullable=True),
    sa.Column('stockout_time', sa.Float(), nullable=True),
    sa.Column('tot_delivery_vol', sa.Float(), nullable=True),
    sa.Column('storageRatio_multival', sa.Integer(), nullable=True),
    sa.Column('storeVialCount_multival', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.ForeignKeyConstraint(['resultsId'], ['results.resultsId'], ),
    sa.ForeignKeyConstraint(['storageRatio_multival'], ['blobHolder.blobId'], ),
    sa.ForeignKeyConstraint(['storeVialCount_multival'], ['storeVialsBlobHolder.blobId'], ),
    sa.PrimaryKeyConstraint('storesRptId')
    )
    storageRpt = sa.Table('storageRpt', md,
    sa.Column('storageRptId', sa.Integer(), nullable=False),
    sa.Column('storesRptId', sa.Integer(), nullable=True),
    sa.Column('storageType', sa.String(length=250), nullable=True),
    sa.Column('fillRatio', sa.Float(), nullable=True),
    sa.Column('vol', sa.Float(), nullable=True),
    sa.Column('vol_used', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['storesRptId'], ['storesRpt.storesRptId'], ),
    sa.PrimaryKeyConstraint('storageRptId')
    )
    vaxRpt = sa.Table('vaxRpt', md,
    sa.Column('vaxRptId', sa.Integer(), nullable=False),
    sa.Column('storesRptId', sa.Integer(), nullable=True),
    sa.Column('vax', sa.String(length=250), nullable=True),
    sa.Column('expired', sa.Float(), nullable=True),
    sa.Column('outages', sa.Float(), nullable=True),
    sa.Column('patients', sa.Float(), nullable=True),
    sa.Column('treated', sa.Float(), nullable=True),
    sa.Column('vials', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['storesRptId'], ['storesRpt.storesRptId'], ),
    sa.PrimaryKeyConstraint('vaxRptId')
    )
    basicSummry = sa.Table('basicSummary', md,
    sa.Column('basicSummaryId', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['basicSummaryId'], ['typeSummary.summaryId'], ),
    sa.PrimaryKeyConstraint('basicSummaryId')
    )
    iceSummary = sa.Table('iceSummary', md,
    sa.Column('iceSummaryId', sa.Integer(), nullable=False),
    sa.Column('TotalTrips', sa.Integer(), nullable=True),
    sa.Column('TotalKm', sa.Float(), nullable=True),
    sa.Column('TotalTravelDays', sa.Float(), nullable=True),
    sa.Column('NBroken', sa.Integer(), nullable=True),
    sa.Column('NCreated', sa.Integer(), nullable=True),
    sa.Column('NBrokenAbsolute', sa.Integer(), nullable=True),
    sa.Column('NCreatedAbsolute', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['iceSummaryId'], ['typeSummary.summaryId'], ),
    sa.PrimaryKeyConstraint('iceSummaryId')
    )
    truckSummary = sa.Table('truckSummary', md,
    sa.Column('truckSummaryId', sa.Integer(), nullable=False),
    sa.Column('TotalTrips', sa.Float(), nullable=True),
    sa.Column('TotalKm', sa.Float(), nullable=True),
    sa.Column('TotalTravelDays', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['truckSummaryId'], ['typeSummary.summaryId'], ),
    sa.PrimaryKeyConstraint('truckSummaryId')
    )
    vaccineSummary = sa.Table('vaccineSummary', md,
    sa.Column('vaccineSummaryId', sa.Integer(), nullable=False),
    sa.Column('DisplayName', sa.String(length=250), nullable=True),
    sa.Column('DosesPerVial', sa.Integer(), nullable=True),
    sa.Column('StorageHistoryVialDays', sa.Float(), nullable=True),
    sa.Column('roomtemperatureStorageFrac', sa.Float(), nullable=True),
    sa.Column('coolerStorageFrac', sa.Float(), nullable=True),
    sa.Column('freezerStorageFrac', sa.Float(), nullable=True),
    sa.Column('ShipTimeDays', sa.Float(), nullable=True),
    sa.Column('ShipVialDays', sa.Float(), nullable=True),
    sa.Column('ShipKm', sa.Float(), nullable=True),
    sa.Column('ShipVialKm', sa.Float(), nullable=True),
    sa.Column('Applied', sa.Integer(), nullable=True),
    sa.Column('Treated', sa.Integer(), nullable=True),
    sa.Column('SupplyRatio', sa.Float(), nullable=True),
    sa.Column('OpenVialWasteFrac', sa.Float(), nullable=True),
    sa.Column('VialsUsed', sa.Integer(), nullable=True),
    sa.Column('VialsExpired', sa.Integer(), nullable=True),
    sa.Column('VialsBroken', sa.Integer(), nullable=True),
    sa.Column('VialsCreated', sa.Integer(), nullable=True),
    sa.Column('VialsUsedAbsolute', sa.Integer(), nullable=True),
    sa.Column('VialsExpiredAbsolute', sa.Integer(), nullable=True),
    sa.Column('VialsBrokenAbsolute', sa.Integer(), nullable=True),
    sa.Column('VialsCreatedAbsolute', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['vaccineSummaryId'], ['typeSummary.summaryId'], ),
    sa.PrimaryKeyConstraint('vaccineSummaryId')
    )
    fridgeSummary = sa.Table('fridgeSummary', md,
    sa.Column('fridgeSummaryId', sa.Integer(), nullable=False),
    sa.Column('NCreated', sa.Integer(), nullable=True),
    sa.Column('NCreatedAbsolute', sa.Integer(), nullable=True),
    sa.Column('ShipTimeDays', sa.Float(), nullable=True),
    sa.Column('ShipInstanceTimeDays', sa.Float(), nullable=True),
    sa.Column('ShipKm', sa.Float(), nullable=True),
    sa.Column('ShipInstanceKm', sa.Float(), nullable=True),
    sa.Column('NBroken', sa.Integer(), nullable=True),
    sa.Column('NBrokenAbsolute', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['fridgeSummaryId'], ['typeSummary.summaryId'], ),
    sa.PrimaryKeyConstraint('fridgeSummaryId')
    )
    ### end Alembic commands ###
    alembic_version_table = sa.Table('alembic_version', md,
                                     sa.Column('version_num', sa.String(length=32), nullable=False))
    
    md.create_all(engine)

    conn = engine.connect()
    conn.execute(alembic_version_table.insert(),version_num='2512bc078649')
    
def getTableByName(tblName, metadata, engine):
    return sa.Table(tblName, metadata, autoload=True, autoload_with=engine)

def buildPrivTables():
    # Initialize the privilege tables
    
    engine = sa.create_engine(getURI(), echo=True)    
    md = sa.MetaData()
    
    conn = engine.connect()
    conn.execute(getTableByName('prvgroups',md,engine).insert(),
                 [{'groupId':1, 'groupName':'sysgroup'},
                  {'groupId':2, 'groupName':'everyone'}
                  ])

    conn.execute(getTableByName('prvusers',md,engine).insert(),
                 [{'userId':1, 'userName':'system'},
                  {'userId':2, 'userName':'anyone'}
                  ])
    conn.execute(getTableByName('prvusergroupassociation',md,engine).insert(),
                 [{'user_id':1,'group_id':1},
                  {'user_id':1,'group_id':2},
                  {'user_id':2,'group_id':2},
                  ])

def installEZInstall():
    pathBase = os.path.join(sI.srcDir(),'..','ui_server','thirdparty','setuptools')
    subprocess.check_call(['python','ez_setup.py'],cwd = pathBase)

def maybeInstallSqlalchemy():
    pathBase = sI.srcDir()
    subprocess.check_call(['easy_install','sqlalchemy'],cwd = pathBase)

def maybeInstallAlembic():
    pass

def installPip():
    """ Bootstrap pip, which will read requirements.txt to install dependencies """
    pathBase = sI.srcDir()
    subprocess.check_call(['easy_install','pip'],cwd = pathBase)

def installRequirements():
    pathBase = sI.srcDir()
    requirementsFile = '%s/../../requirements.txt' % pathBase
    subprocess.check_call(['pip','install','-r',requirementsFile],cwd = pathBase)

def callAlembicUpgrade():
    pathBase = os.path.join(sI.srcDir(),'..','..',)
    if platform.system() == 'Windows': sep = ';'
    else: sep = ':'
    if 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] = '%s%s%s%s%s'%(os.environ['PYTHONPATH'],
                                                 sep,
                                                 os.path.join(pathBase,'src/sim'),
                                                 sep,
                                                 os.path.join(pathBase,'src/ui_server'))
    else:
        os.environ['PYTHONPATH'] = '%s%s%s'%(os.path.join(pathBase,'src/sim'),
                                             sep,
                                             os.path.join(pathBase,'src/ui_server'))
    subprocess.check_call(['alembic','upgrade','head'],cwd = pathBase)

def addTypeHolderModel():
    stdTypePath = os.path.join(sI.srcDir(),os.pardir,os.pardir,'master_data','standardtypes')
    shdTypes = shadow_network.ShdTypes()
    for fN in os.listdir(stdTypePath):
        if fN.endswith('.csv'):
            for s,tp in [('vaccine','vaccines'),
                         ('ice','ice'),
                         ('people','people'),
                         ('packaging','packaging'),
                         ('fridge','fridges'),
                         ('truck','trucks')
                         ]:
                if fN.lower().find(s)>=0: 
                    with util.logContext("loading types from %s as %s for shadow network"%(fN,tp)):
                        shdTypes.importRecordsFromFile(os.path.join(stdTypePath,fN), tp)

    net = shadow_network.ShdNetwork([], [], [], shdTypes, name=allTypesModelName)
    session = db_routines.DbInterface().Session()
    session.add(net)
    session.commit()
    privs.Privileges(1).registerModelId(session, net.modelId,1,1)


def main():
    
    installEZInstall()
    #maybeInstallSqlalchemy()
    #maybeInstallAlembic()
    installPip()
    installRequirements()
    
    scratchDir = sI.scratchDir()
    if not os.path.isdir(scratchDir): os.makedirs(scratchDir)
    
    createAlembicIni()
    
    createDBFromHistory()
    callAlembicUpgrade()
    
    # This routine creates the DB as embodied by the current code, but does not set an
    # appropriate Alembic version number.
    #createDBFromCode()

    buildPrivTables()
    addTypeHolderModel()
    
    
############
# Main hook
############

if __name__=="__main__":
    main()

