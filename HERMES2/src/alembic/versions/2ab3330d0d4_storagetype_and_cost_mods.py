"""storagetype and cost mods

Revision ID: 2ab3330d0d4
Revises: 41b11c660c3
Create Date: 2014-07-10 16:08:02.333893

"""

# revision identifiers, used by Alembic.
revision = '2ab3330d0d4'
down_revision = '41b11c660c3'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import csv_tools
import os.path
import types

def upgrade():
    
    conn = op.get_bind()
    meta = sa.MetaData()

    print '##### creating new storagetype table #####'
    storagetypes = sa.Table('storagetypes', meta, autoload=True, autoload_with=conn.engine)
    newstoragetypes = sa.Table('newstoragetypes', meta, 
                    sa.Column(u'storagetypeId', sa.Integer(), nullable=False),
                    sa.Column(u'DisplayName', sa.String(length=250), nullable=True),
                    sa.Column(u'Make', sa.String(length=250), nullable=True),
                    sa.Column(u'Model', sa.String(length=250), nullable=True),
                    sa.Column(u'Year', sa.String(length=250), nullable=True),
                    sa.Column(u'Energy', sa.String(length=250), nullable=True),
                    sa.Column(u'BaseCost', sa.Float(), nullable=True),
                    sa.Column(u'BaseCostCurCode', sa.String(length=250), nullable=True),
                    sa.Column(u'BaseCostYear', sa.Integer(), nullable=True),
                    sa.Column(u'Category', sa.String(length=250), nullable=True),
                    sa.Column(u'NoPowerHoldoverDays', sa.Float(), nullable=True),
                    sa.Column(u'PowerRate', sa.Float(), nullable=True),
                    sa.Column(u'PowerRateUnits', sa.String(length=250), nullable=True),
                    sa.Column(u'Technology', sa.String(length=250), nullable=True),
                    sa.Column(u'freezer', sa.Float(), nullable=True),
                    sa.Column(u'cooler', sa.Float(), nullable=True),
                    sa.Column(u'roomtemperature', sa.Float(), nullable=True),
                    sa.Column(u'ClassName', sa.String(length=250), nullable=True),
                    sa.Column(u'chain', sa.String(length=250), nullable=True),
                    sa.Column(u'ColdLifetime', sa.Float(), nullable=True),
                    sa.Column(u'AlarmDays', sa.Float(), nullable=True),
                    sa.Column(u'SnoozeDays', sa.Float(), nullable=True),
                    sa.Column(u'Requires', sa.String(length=250), nullable=True),
                    sa.Column(u'Notes', sa.String(length=4096), nullable=True),
                    sa.ForeignKeyConstraint([u'storagetypeId'], ['types.typeId'], ),
                    sa.PrimaryKeyConstraint(u'storagetypeId')
                )
    newstoragetypes.create(conn, checkfirst=True)
    
    print '##### transcribing old storagetype records #####'
    for row in conn.execute(sa.select([storagetypes])):
        if row[storagetypes.c.Energy] in ['U','EnergyUnk']:
            energy = 'U'
        else:
            energy = row[storagetypes.c.Energy]
        print ['%s:%s'%(k,v) for k,v in row.items()]
        conn.execute( newstoragetypes.insert().values( storagetypeId=row[storagetypes.c.storagetypeId],
                                                       DisplayName=row[storagetypes.c.DisplayName],
                                                       Make=row[storagetypes.c.Make],
                                                       Model=row[storagetypes.c.Model],
                                                       Year=row[storagetypes.c.Year],
                                                       Energy=energy,
                                                       Category=None,
                                                       Technology=None,
                                                       BaseCost=None,
                                                       BaseCostCurCode=None,
                                                       BaseCostYear=None,
                                                       NoPowerHoldoverDays=None,
                                                       PowerRate=None,
                                                       PowerRateUnits=None,
                                                       freezer=row[storagetypes.c.freezer],
                                                       cooler=row[storagetypes.c.cooler],
                                                       roomtemperature=row[storagetypes.c.roomtemperature],
                                                       ClassName=row[storagetypes.c.ClassName],
                                                       chain=None,
                                                       ColdLifetime=row[storagetypes.c.ColdLifetime],
                                                       AlarmDays=row[storagetypes.c.AlarmDays],
                                                       SnoozeDays=row[storagetypes.c.SnoozeDays],
                                                       Requires=row[storagetypes.c.Requires],
                                                       Notes=row[storagetypes.c.Notes]
                                                       ) )

    print '##### swapping tables #####'
    op.rename_table('storagetypes','oldstoragetypes')
    op.rename_table('newstoragetypes','storagetypes')
    op.drop_table('oldstoragetypes')

    storagetypes2 = sa.Table('storagetypes', meta, autoload=True, extend_existing=True, autoload_with=conn.engine)

    print '##### clearing AllTypesModel storagetypes #####'
    models = sa.Table('models', meta, autoload=True, autoload_with=conn.engine)
    typeTable = sa.Table('types', meta, autoload=True, autoload_with=conn.engine)
    allTypesModelId = None
    for row in conn.execute(sa.select([models]).where(models.c.name==op.inline_literal('AllTypesModel'))):
        allTypesModelId = row[models.c.modelId]
    
    for row in conn.execute(sa.select([typeTable]).where(typeTable.c.modelId==allTypesModelId).where(typeTable.c.typeClass==op.inline_literal('fridges'))):
        conn.execute(storagetypes2.delete().where(storagetypes2.c.storagetypeId == row[typeTable.c.typeId]))
        conn.execute(typeTable.delete().where(typeTable.c.typeId == row[typeTable.c.typeId]))
    
    print '##### loading fridgeTypeInfo #####'
    here = os.path.split(os.path.abspath(__file__))[0]
    with open(os.path.join(here,'..','..','..','master_data','standardtypes','fridgeTypeInfo.csv'),'rU') as f:
        keys,recs = csv_tools.parseCSV(f)
        
    print '##### inserting standard types #####'
    for rec in recs: 
        #print rec['Name']
        for k in ['Year', 'BaseCost', 'BaseCostYear', 'NoPowerHoldoverDays', 'PowerRate', 'freezer', 'cooler',
                  'roomtemperature', 'ColdLifetime', 'AlarmDays', 'SnoozeDays']:
            if rec[k] == '': rec[k] = None
        for k,v in rec.items():
            if type(v) == types.StringType:
                rec[k] = v.decode('utf8')
            
        result = conn.execute( typeTable.insert().values(typeClass='fridges', modelId=allTypesModelId, Name=rec['Name']))
        conn.execute( storagetypes2.insert().values( storagetypeId=result.inserted_primary_key[0],
                                                       DisplayName=rec['DisplayName'],
                                                       Make=rec['Make'],
                                                       Model=rec['Model'],
                                                       Year=rec['Year'],
                                                       Energy=rec['Energy'],
                                                       BaseCost=rec['BaseCost'],
                                                       BaseCostCurCode=rec['BaseCostCur'],
                                                       BaseCostYear=rec['BaseCostYear'],
                                                       Category=rec['Category'],
                                                       NoPowerHoldoverDays=rec['NoPowerHoldoverDays'],
                                                       PowerRate=rec['PowerRate'],
                                                       PowerRateUnits=rec['PowerRateUnits'],
                                                       Technology=rec['Technology'],
                                                       freezer=rec['freezer'],
                                                       cooler=rec['cooler'],
                                                       roomtemperature=rec['roomtemperature'],
                                                       ClassName=rec['ClassName'],
                                                       chain=rec['chain'],
                                                       ColdLifetime=rec['ColdLifetime'],
                                                       AlarmDays=rec['AlarmDays'],
                                                       SnoozeDays=rec['SnoozeDays'],
                                                       Notes=rec['Notes'] ) )
    
    print '##### done #####'

    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###

    conn = op.get_bind()
    meta = sa.MetaData()
    print '##### recreating downgraded storagetype table #####'
    storagetypes = sa.Table('storagetypes', meta, autoload=True, autoload_with=conn.engine)
    newstoragetypes = sa.Table('newstoragetypes', meta, 
                    sa.Column(u'storagetypeId', sa.Integer(), nullable=False),
                    sa.Column(u'DisplayName', sa.String(length=250), nullable=True),
                    sa.Column(u'Make', sa.String(length=250), nullable=True),
                    sa.Column(u'Model', sa.String(length=250), nullable=True),
                    sa.Column(u'Year', sa.String(length=250), nullable=True),
                    sa.Column(u'Energy', sa.String(length=250), nullable=True),
                    sa.Column(u'freezer', sa.Float(), nullable=True),
                    sa.Column(u'cooler', sa.Float(), nullable=True),
                    sa.Column(u'roomtemperature', sa.Float(), nullable=True),
                    sa.Column(u'ClassName', sa.String(length=250), nullable=True),
                    sa.Column(u'ColdLifetime', sa.Float(), nullable=True),
                    sa.Column(u'AlarmDays', sa.Float(), nullable=True),
                    sa.Column(u'SnoozeDays', sa.Float(), nullable=True),
                    sa.Column(u'Requires', sa.String(length=250), nullable=True),
                    sa.Column(u'Notes', sa.String(length=4096), nullable=True),
                    sa.ForeignKeyConstraint([u'storagetypeId'], ['types.typeId'], ),
                    sa.PrimaryKeyConstraint(u'storagetypeId')
                )
    newstoragetypes.create(conn, checkfirst=True)
    
    print '##### transcribing records #####'
    for row in conn.execute(sa.select([storagetypes])):
        if row[storagetypes.c.Energy] in ['U','EnergyUnk']:
            energy = 'U'
        else:
            energy = row[storagetypes.c.Energy]
        conn.execute( newstoragetypes.insert().values( storagetypeId=row[storagetypes.c.storagetypeId],
                                                       DisplayName=row[storagetypes.c.DisplayName],
                                                       Make=row[storagetypes.c.Make],
                                                       Model=row[storagetypes.c.Model],
                                                       Year=row[storagetypes.c.Year],
                                                       Energy=energy,
                                                       freezer=row[storagetypes.c.freezer],
                                                       cooler=row[storagetypes.c.cooler],
                                                       roomtemperature=row[storagetypes.c.roomtemperature],
                                                       ClassName=row[storagetypes.c.ClassName],
                                                       ColdLifetime=row[storagetypes.c.ColdLifetime],
                                                       AlarmDays=row[storagetypes.c.AlarmDays],
                                                       SnoozeDays=row[storagetypes.c.SnoozeDays],
                                                       Requires=row[storagetypes.c.Requires],
                                                       Notes=row[storagetypes.c.Notes]
                                                       ) )
        
    print '##### swapping tables #####'
    op.rename_table('storagetypes','oldstoragetypes')
    op.rename_table('newstoragetypes','storagetypes')
    op.drop_table('oldstoragetypes')
    print '##### done #####'

    ### end Alembic commands ###
