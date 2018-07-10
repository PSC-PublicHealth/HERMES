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

__doc__=""" 
This script is supposed to create and populate the database and do other 
steps necessary to create a runnable HERMES UI environment.
"""
_hermes_svn_id_="$Id$"

########################################################################
# ONLY PYTHON-SHIPPED LIBRARIES SHOULD BE IMPORTED AT THE TOP-LEVEL ####
# OF THIS FILE!                                                     ####
########################################################################

import platform
import sys, os, os.path, subprocess

# only import core python modules in the top level unless we can be certain that
# they will not import any 3rd party modules

import ipath


#import site_info
#from db_routines import DbInterface
#import db_routines
#import util
#import shadow_network
#import privs
#from typeholdermodel import allTypesModelName

#import sqlalchemy as sa

#sI = site_info.SiteInfo()

_uri = None

def getURI():
    from db_routines import DbInterface
    global _uri
    if _uri is None:
        _uri = DbInterface().getURI()
    return _uri

def innerCreateAlembicIni(path):
    """
    This routine unconditionally writes a new alembic.ini file
    """
    import site_info
    sI = site_info.SiteInfo()
   
    url = getURI()
    prototypeFile = os.path.join(sI.baseDir(),'alembic.ini.prototype')
    
    with open(prototypeFile,'r') as ifile:  
        with open(os.path.join(path,'alembic.ini'),'w') as ofile:
            for rec in ifile:
                if rec.strip().startswith('sqlalchemy.url ='):
                    ofile.write('sqlalchemy.url = %s\n'%url)
                else:
                    ofile.write(rec)

def createAlembicIni(replace=True):
    import site_info
    sI = site_info.SiteInfo()

    alembicPath = sI.alembicPath()
    
    #path = os.path.join(sI.srcDir(),'../..')
    #pathHere = path
    #if newpath:
    #    pathHere = newpath
    if os.path.lexists(os.path.join(alembicPath,'alembic.ini')):
        if replace:
            count = 0
            while True:
                if count==0: savName = 'alembic.ini.sav'
                else: savName = 'alembic.ini.sav%d'%count
                if os.path.lexists(os.path.join(alembicPath,savName)):
                    count += 1
                else:
                    break
            os.rename(os.path.join(alembicPath,'alembic.ini'),os.path.join(alembicPath,savName))
        
            innerCreateAlembicIni(alembicPath)
        else:
            print 'alembic.ini exists and replace is false; not overwriting'
        
    else:
        innerCreateAlembicIni(alembicPath)

def createDBFromCode():
    from db_routines import DbInterface
    dbI = DbInterface()
    dbI.createTables()

def getTableByName(tblName, metadata, engine):
    import sqlalchemy as sa
    return sa.Table(tblName, metadata, autoload=True, autoload_with=engine)

def dropAllTables():
    """
    Drop all tables in the database, so we can start from scratch
    """
    import sqlalchemy as sa
    
    engine = sa.create_engine(getURI(), echo=True)
    md = sa.MetaData(engine)
    md.drop_all()
    

def createDBFromHistory(replace=True):
    """
    This is basically an auto-generated Alembic script, modified
    to call SQLAlchemy directly.
    
    complete creation up to r1481
    
    Revision ID: 3ce5a00e170b
    Revises: None
    Create Date: 2013-10-14 16:41:01.235910
    
    """
    
    import sqlalchemy as sa
    
    # revision identifiers, used by Alembic.
    revision = '3ce5a00e170b'
    down_revision = None

    engine = sa.create_engine(getURI(), echo=True)
    inspector = sa.inspect(engine)
    md = sa.MetaData(engine)
    
    if replace:
        print 'dropping all existing tables'
        md.drop_all()
        
    existingTables = set(inspector.get_table_names())
    
    ### commands auto generated by Alembic - please adjust! ###
    if replace or not existingTables.__contains__('geoResultsBlobHolder'):
        geoResultsBlobHolder = sa.Table('geoResultsBlobHolder', md,
        sa.Column('blobId', sa.Integer(), nullable=False),
        sa.Column('blob', sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint('blobId')
        )
    else:
        print 'table geoResultsBlobHolder exists; not replacing'
    if replace or not existingTables.__contains__('modelD3JsonBlobHolder'):
        geoResultsBlobHolder = sa.Table('modelD3JsonBlobHolder', md,
        sa.Column('blobId', sa.Integer(), nullable=False),
        sa.Column('blob', sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint('blobId')
        )
    else:
        print 'table modelD3JsonBlobHolder exists; not replacing'

    if replace or not existingTables.__contains__('storeVialsBlobHolder'):
        storeVialsBlobHolder = sa.Table('storeVialsBlobHolder', md,
        sa.Column('blobId', sa.Integer(), nullable=False),
        sa.Column('blob', sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint('blobId')
        )
    else:
        print 'table storeVialsBlobHolder exists; not replacing'
    
    if replace or not existingTables.__contains__('uisessions'):
        uisessions = sa.Table('uisessions', md,
        sa.Column('sessionId', sa.String(length=36), nullable=False),
        sa.Column('sessionDict', sa.PickleType(), nullable=True),
        sa.PrimaryKeyConstraint('sessionId')
        )
    else:
        print 'uisessions exists; not replacing'
        
    if replace or not existingTables.__contains__('blobHolder'):
        blobHolder = sa.Table('blobHolder', md,
        sa.Column('blobId', sa.Integer(), nullable=False),
        sa.Column('blob', sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint('blobId')
        )
    else:
        print 'blobHolder exists; not replacing'
        
    if replace or not existingTables.__contains__('prvusers'):
        prvusers = sa.Table('prvusers', md,
        sa.Column('userId', sa.Integer(), nullable=False),
        sa.Column('userName', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('userId')
        )
    else:
        print 'prvusers exists; not replacing'
        
    if replace or not existingTables.__contains__('models'):
        models = sa.Table('models', md,
        sa.Column('modelId', sa.Integer(), nullable=False),
        sa.Column('note', sa.String(length=4096), nullable=True),
        sa.Column('name', sa.String(length=250), nullable=True),
        sa.PrimaryKeyConstraint('modelId'),
        mysql_engine='InnoDB'
        )
    else:
        models = getTableByName('models',md,engine) # import for use by later tables
        print 'models exists; not replacing'
        
    if replace or not existingTables.__contains__('prvgroups'):
        prvgroups = sa.Table('prvgroups', md,
        sa.Column('groupId', sa.Integer(), nullable=False),
        sa.Column('groupName', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('groupId')
        )
    else:
        print 'prvgroups exists; not replacing'
        
    if replace or not existingTables.__contains__('types'):
        types = sa.Table('types', md,
        sa.Column('typeId', sa.Integer(), nullable=False),
        sa.Column('typeClass', sa.String(length=30), nullable=True),
        sa.Column('modelId', sa.Integer(), nullable=True),
        sa.Column('Name', sa.String(length=250), nullable=True),
        sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
        sa.PrimaryKeyConstraint('typeId')
        )
    else:
        print 'types exists; not replacing'
        
    if replace or not existingTables.__contains__('parms'):
        parms = sa.Table('parms', md,
        sa.Column('parmId', sa.Integer(), nullable=False),
        sa.Column('modelId', sa.Integer(), nullable=True),
        sa.Column('key', sa.String(length=250), nullable=True),
        sa.Column('value', sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
        sa.PrimaryKeyConstraint('parmId')
        )
    else:
        print 'parms exists; not replacing'
        
    if replace or not existingTables.__contains__('demand'):
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
    else:
        print 'demand exists; not replacing'
        
    if replace or not existingTables.__contains__('costs'):
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
    else:
        print 'costs exists; not replacing'
        
    if replace or not existingTables.__contains__('currencyConversion'):
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
    else:
        print 'currencyConversion exists; not replacing'
        
    if replace or not existingTables.__contains__('routes'):
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
    else:
        print 'routes exists; not replacing'
        
    if replace or not existingTables.__contains__('stores'):
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
    else:
        print 'stores exists; not replacing'
        
    if replace or not existingTables.__contains__('resultsGroup'):
        resultsGroup = sa.Table('resultsGroup', md,
        sa.Column('resultsGroupId', sa.Integer(), nullable=False),
        sa.Column('modelId', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=250), nullable=True),
        sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
        sa.PrimaryKeyConstraint('resultsGroupId')
        )
    else:
        print 'resultsGroup exists; not replacing'
        
    if replace or not existingTables.__contains__('prvmodelaccessrights'):
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
    else:
        print 'prvmodelaccessrights exists; not replacing'
        
    if replace or not existingTables.__contains__('prvusergroupassociation'):
        prvusergroupassociation = sa.Table('prvusergroupassociation', md,
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['prvgroups.groupId'], ),
        sa.ForeignKeyConstraint(['user_id'], ['prvusers.userId'], ),
        sa.PrimaryKeyConstraint()
        )
    else:
        print 'prvusergroupassociation exists; not replacing'
        
    if replace or not existingTables.__contains__('factoryOVW'):
        factoryOVW = sa.Table('factoryOVW', md,
        sa.Column('factoryOVWId', sa.Integer(), nullable=False),
        sa.Column('modelId', sa.Integer(), nullable=True),
        sa.Column('Name', sa.String(length=250), nullable=True),
        sa.Column('OVW', sa.Float(), nullable=True),
        sa.Column('Notes', sa.String(length=4096), nullable=True),
        sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
        sa.PrimaryKeyConstraint('factoryOVWId')
        )
    else:
        print 'factoryOVW exists; not replacing'
        
    if replace or not existingTables.__contains__('stops'):
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
    else:
        print 'stops exists; not replacing'
        
    if replace or not existingTables.__contains__('inventory'):
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
    else:
        print 'inventory exists; not replacing'
        
    if replace or not existingTables.__contains__('calendarEntries'):
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
    else:
        print 'calendarEntries exists; not replacing'
        
    if replace or not existingTables.__contains__('peopletypes'):
        peopletypes = sa.Table('peopletypes', md,
        sa.Column('peopletypeId', sa.Integer(), nullable=False),
        sa.Column('DisplayName', sa.String(length=250), nullable=True),
        sa.Column('SortOrder', sa.Integer(), nullable=True),
        sa.Column('Requires', sa.String(length=250), nullable=True),
        sa.Column('Notes', sa.String(length=4096), nullable=True),
        sa.ForeignKeyConstraint(['peopletypeId'], ['types.typeId'], ),
        sa.PrimaryKeyConstraint('peopletypeId')
        )
    else:
        print 'peopletypes exists; not replacing'
        
    if replace or not existingTables.__contains__('vaccinetypes'):
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
    else:
        print 'vaccinetyeps exists; not replacing'
        
    if replace or not existingTables.__contains__('trucktypes'):
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
    else:
        print 'trucktypes exists; not replacing'
        
    if replace or not existingTables.__contains__('packagetypes'):
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
    else:
        print 'packagetypes exists; not replacing'
        
    if replace or not existingTables.__contains__('results'):
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
    else:
        print 'results exists; not replacing'
        
    if replace or not existingTables.__contains__('storagetypes'):
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
    else:
        print 'storagetypes exists; not replacing'
        
    if replace or not existingTables.__contains__('icetypes'):
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
    else:
        print 'icetypes exists; not replacing'
        
    if replace or not existingTables.__contains__('typeSummary'):
        typeSummary = sa.Table('typeSummary', md,
        sa.Column('summaryId', sa.Integer(), nullable=False),
        sa.Column('typeClass', sa.String(length=30), nullable=True),
        sa.Column('resultsId', sa.Integer(), nullable=True),
        sa.Column('Name', sa.String(length=250), nullable=True),
        sa.Column('Type', sa.String(length=250), nullable=True),
        sa.ForeignKeyConstraint(['resultsId'], ['results.resultsId'], ),
        sa.PrimaryKeyConstraint('summaryId')
        )
    else:
        print 'typeSummary exists; not replacing'
        
    if replace or not existingTables.__contains__('routesRpt'):
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
    else:
        print 'routesRpt exists; not replacing'
        
    if replace or not existingTables.__contains__('storesRpt'):
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
    else:
        print 'storesRpt exists; not replacing'
        
    if replace or not existingTables.__contains__('storageRpt'):
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
    else:
        print 'storageRpt exists; not replacing'
        
    if replace or not existingTables.__contains__('vaxRpt'):
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
    else:
        print 'vaxRpt exists; not replacing'
        
    if replace or not existingTables.__contains__('basicSummary'):
        basicSummry = sa.Table('basicSummary', md,
        sa.Column('basicSummaryId', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['basicSummaryId'], ['typeSummary.summaryId'], ),
        sa.PrimaryKeyConstraint('basicSummaryId')
        )
    else:
        print 'basicSummary exists; not replacing'
        
    if replace or not existingTables.__contains__('iceSummary'):
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
    else:
        print 'iceSummary exists; not replacing'
        
    if replace or not existingTables.__contains__('truckSummary'):
        truckSummary = sa.Table('truckSummary', md,
        sa.Column('truckSummaryId', sa.Integer(), nullable=False),
        sa.Column('TotalTrips', sa.Float(), nullable=True),
        sa.Column('TotalKm', sa.Float(), nullable=True),
        sa.Column('TotalTravelDays', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['truckSummaryId'], ['typeSummary.summaryId'], ),
        sa.PrimaryKeyConstraint('truckSummaryId')
        )
    else:
        print 'truckSummary exists; not replacing'
        
    if replace or not existingTables.__contains__('vaccineSummary'):
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
    else:
        print 'vaccineSummary exists; not replacing'
        
    if replace or not existingTables.__contains__('fridgeSummary'):
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
    else:
        print 'fridgeSummary exists; not replacing'
    ### end Alembic commands ###
    
    trustAlembic = False
    if replace or not existingTables.__contains__('alembic_version'):
        alembic_version_table = sa.Table('alembic_version', md,
                                         sa.Column('version_num', sa.String(length=32), nullable=False))
    else:
        trustAlembic = True
        print 'alembic_version table exists; not replacing or modifying'
    
    md.create_all(engine)

    if not trustAlembic:
        conn = engine.connect()
        conn.execute(alembic_version_table.insert(),version_num='2512bc078649')
    
def buildPrivTables():
    """
    Initialize the privilege tables.  Since the structure of the table is fixed,
    we can re-install unconditionally.
    """
    import sqlalchemy as sa

    engine = sa.create_engine(getURI(), echo=True)    
    md = sa.MetaData()
    
    conn = engine.connect()
    
    # The delete halves of these pairs will fail if models exist in the DB and 
    # thus reference these tables via prvmodelaccessrights
    try:
        conn.execute(getTableByName('prvgroups',md,engine).delete())
        conn.execute(getTableByName('prvgroups',md,engine).insert(),
                     [{'groupId':1, 'groupName':'sysgroup'},
                      {'groupId':2, 'groupName':'everyone'}
                      ])
    except:
        print 'failed to rebuild prvgroups - probably harmless'

    try:
        conn.execute(getTableByName('prvusers',md,engine).delete())
        conn.execute(getTableByName('prvusers',md,engine).insert(),
                     [{'userId':1, 'userName':'system'},
                      {'userId':2, 'userName':'anyone'}
                      ])
    except:
        print 'failed to rebuild prvusers - probably harmless'
    
    try:
        conn.execute(getTableByName('prvusergroupassociation',md,engine).delete())
        conn.execute(getTableByName('prvusergroupassociation',md,engine).insert(),
                     [{'user_id':1,'group_id':1},
                      {'user_id':1,'group_id':2},
                      {'user_id':2,'group_id':2},
                      ])
    except:
        print 'failed to rebuild prvusergroupassociation - probably harmless'

def installEZInstall():
    srcDir = os.path.split(os.path.abspath(__file__))[0]

    pathBase = os.path.join(srcDir,'..','ui_server','thirdparty','setuptools')
    subprocess.check_call(['python','ez_setup.py'],cwd = pathBase)

def maybeInstallSqlalchemy():
    import site_info
    sI = site_info.SiteInfo()

    pathBase = sI.srcDir()
    subprocess.check_call(['easy_install','sqlalchemy'],cwd = pathBase)

def maybeInstallAlembic():
    pass

def installPip():
    """ Bootstrap pip, which will read requirements.txt to install dependencies """
    pathBase = os.path.split(os.path.abspath(__file__))[0]
#    pathBase = sI.srcDir()
    subprocess.check_call(['easy_install','pip'],cwd = pathBase)

def installRequirements(upgrade=False):
    pathBase = os.path.split(os.path.abspath(__file__))[0]
#    pathBase = sI.srcDir()
    requirementsFile = '%s/../../requirements.txt' % pathBase
    pip_command = ['pip','install','-r',requirementsFile]
    if upgrade:
        pip_command.append('-U')
    subprocess.check_call(pip_command, cwd = pathBase)

def callAlembicUpgrade():
    import site_info
    sI = site_info.SiteInfo()

    pathBase = os.path.join(sI.srcDir(),'..','..',)
    alembicproc = 'alembic'
    if platform.system() == 'Windows':
        sep = ';'
        if os.path.isfile(os.path.join(pathBase,'python','Scripts','alembic.bat')): alembicproc = 'alembic.bat'
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
    
    subprocess.check_call([alembicproc,"-c","{0}".format(os.path.join(sI.alembicPath(),"alembic.ini")),"upgrade","head"],cwd = pathBase)
   

def addTypeHolderModel(replace=True):
    import shadow_network
    import privs
    from typeholdermodel import allTypesModelName, installUserTypeHolderModel
    from db_routines import DbInterface
    import shadow_network_db_api
    import util
    import site_info
    import csv_tools
    sI = site_info.SiteInfo()

    # If an existing typeHolderModel exists, deal with it
    dbInterface = DbInterface()
    conn = dbInterface.engine.connect()
    session = dbInterface.Session()    
    md = dbInterface.Base.metadata
    
    models = getTableByName('models', md, dbInterface.engine)
    rows = conn.execute(models.select().where(models.c.name == allTypesModelName)).fetchall()
    if len(rows) > 0:
        if replace:
            print 'deleting and replacing existing allTypesModel(s)'
            for row in rows:
                m = shadow_network_db_api.ShdNetworkDB(session,row['modelId'])
                session.delete(m)
            print 'dropped old allTypesModel %s'%row['modelId']
        else:
            print 'allTypesModel exists; not replacing it'
            return
    
    # this needs to be harmonized with installTypeHolderModel()

    stdTypePath = os.path.join(sI.srcDir(),os.pardir,os.pardir,'master_data','standardtypes')
    shdTypes = shadow_network.ShdTypes()
    for fN in os.listdir(stdTypePath):
        if fN.endswith('.csv'):
            for s,tp in [('vaccine','vaccines'),
                         ('ice','ice'),
                         ('people','people'),
                         ('packaging','packaging'),
                         ('fridge','fridges'),
                         ('truck','trucks'),
                         ('staff','staff'),
                         ('perdiem','perdiems')
                         ]:
                if fN.lower().find(s)>=0: 
                    with util.logContext("loading types from %s as %s for shadow network"%(fN,tp)):
                        shdTypes.importRecordsFromFile(os.path.join(stdTypePath,fN), tp)

    net = shadow_network.ShdNetwork([], [], [], shdTypes, name=allTypesModelName, refOnly=True)

    currencyFilePath = os.path.join(sI.srcDir(), os.pardir, os.pardir, 'master_data', 'unified',
                                    'CurrencyConversionTable.csv')
    if os.path.isfile(currencyFilePath):
        with util.logContext("loading currency conversion records from %s" % currencyFilePath):
            keys, recs = csv_tools.parseCSV(currencyFilePath)  # @UnusedVariable
            net.addCurrencyTable(recs)
    else:
        print "Warning: CurrencyConversionTable is missing!"

    session.add(net)
    session.commit()
    privs.Privileges(1).registerModelId(session, net.modelId,2,1)
    
    # let the alembic scripts do this instead.
    # installUserTypeHolderModel()

def addInitialModels():
    import site_info
    sI = site_info.SiteInfo()
    pathBase = os.path.join(sI.srcDir(),'..','..')
    curWorkDir = os.path.join(pathBase,'src','tools')
    print curWorkDir
    automodelsDir = os.path.join('master_data','automodels')
    path = os.path.join(pathBase,automodelsDir)
    for file in os.listdir(path):
        if file.lower().endswith(".zip"):
            filePath = os.path.join('..','..',automodelsDir,file)
            print "Attempting to add initial model: %s"%(file)
            subprocess.check_call(['python','add_model_to_db.py','--no_overwrite_db','--use_zip='+filePath],cwd = curWorkDir)
    

def _install_hermes(overwrite = False):

    import site_info
    sI = site_info.SiteInfo()

    scratchDir = sI.scratchDir()
    if not os.path.isdir(scratchDir): os.makedirs(scratchDir)
    
    createAlembicIni(replace=overwrite)
    
    createDBFromHistory(replace=overwrite)
    callAlembicUpgrade()
     
    # This routine unconditionally creates the DB as embodied by the current code, but does not set an
    # appropriate Alembic version number.
    #createDBFromCode()
 
    buildPrivTables()
    addTypeHolderModel(replace=overwrite)
    
    addInitialModels()

def _install_dependencies(upgrade=False):
#    installEZInstall()
    #maybeInstallSqlalchemy()
    #maybeInstallAlembic()
#    installPip()
    installRequirements()
 
def main():

    import argparse
    
    parser = argparse.ArgumentParser(
            description='Install HERMES Standalone Web Server',
            prefix_chars='-+')

    parser.add_argument('-u', '--upgrade', action='store_true',
            help='Upgrade dependencies if needed.')
    parser.add_argument('-d', '--dependencies_only', action='store_true',
            help='Only install dependencies')
    parser.add_argument('-n', '--no_dependencies', action='store_true',
                        help='Do not install dependencies')
    parser.add_argument('-r', '--replace', action='store_true',
                        help='Delete and replace existing HERMES database if present')
    parser.add_argument('-C', '--clobber', action='store_true',
                        help='Totally delete tables from existing HERMES database, including schemas')
    parser.add_argument('-R', '--rebuildalltypes', action='store_true',
                        help='Delete and rebuild the AllTypesModel, leaving everything else intact')
    parser.add_argument('-a','--alembicpath',
                         help='Specifies an alternative path for the alembic.ini')
    parser.add_argument('-D','-userinstalldir',help='Specify the directory in which you would like the database installed')

    try:
        with open(os.path.join("..","version.txt"),"r") as f:
            hermes_version = f.readlines()[1]
    except IOError:
        hermes_version = None
    if hermes_version: print "Installing HERMES {0}".format(hermes_version)
    
    args = parser.parse_args()

    if args.rebuildalltypes:
        addTypeHolderModel(replace=True)
    else:
        if not args.no_dependencies:
            _install_dependencies(upgrade=args.upgrade)

        if args.clobber:
            dropAllTables()

        if not args.dependencies_only:
            _install_hermes(overwrite=args.replace)


############
# Main hook
############

if __name__=="__main__":
    main()

