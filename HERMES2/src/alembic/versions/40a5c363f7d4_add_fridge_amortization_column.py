"""Add fridge amortization column

Revision ID: 40a5c363f7d4
Revises: 3ac2bb5bd921
Create Date: 2014-12-05 15:25:28.685550

"""

# revision identifiers, used by Alembic.
revision = '40a5c363f7d4'
down_revision = '3ac2bb5bd921'

import os.path
from alembic import op
import sqlalchemy as sa
import ipath
import csv_tools

        
from alembic_helper import copyTableRecords, findAllTypesModelId

def upgrade():

    print '##### creating new storagetype table #####'

    op.create_table('newstoragetypes',
                    sa.Column(u'storagetypeId', sa.Integer(), nullable=False),
                    sa.Column(u'DisplayName', sa.String(length=250), nullable=True),
                    sa.Column(u'Make', sa.String(length=250), nullable=True),
                    sa.Column(u'Model', sa.String(length=250), nullable=True),
                    sa.Column(u'Year', sa.String(length=250), nullable=True),
                    sa.Column(u'Energy', sa.String(length=250), nullable=True),
                    sa.Column(u'BaseCost', sa.Float(), nullable=True),
                    sa.Column(u'BaseCostCurCode', sa.String(length=250), nullable=True),
                    sa.Column(u'BaseCostYear', sa.Integer(), nullable=True),
                    sa.Column(u'AmortYears', sa.Float(), nullable=True),
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

    print '##### Copying records #####'
    conn = op.get_bind()
    meta = sa.MetaData()

    storagetypes = sa.Table('storagetypes', meta, autoload=True, autoload_with=conn.engine)
    newstoragetypes = sa.Table('newstoragetypes', meta, autoload=True, autoload_with=conn.engine)
    types = sa.Table('types', meta, autoload=True, autoload_with=conn.engine)

    copyTableRecords(storagetypes, newstoragetypes, conn)

    print '##### finding AllTypesModel #####'
    allTypesModelId = findAllTypesModelId(conn, meta)
    if allTypesModelId is None:
        print '##### no AllTypesModel to update #####'
    else:
        print '##### AllTypesModel is %d #####' % allTypesModelId
        print '##### loading fridgeTypeInfo #####'
        here = os.path.split(os.path.abspath(__file__))[0]
        with open(os.path.join(here, '..', '..', '..', 'master_data',
                               'standardtypes', 'fridgeTypeInfo.csv'), 'rU') as f:
            keys, recs = csv_tools.parseCSV(f)  # @UnusedVariable

        print '##### inserting standard types values #####'
        for r in recs:
            conn.execute(newstoragetypes.update()
                         .values({newstoragetypes.c.AmortYears: r['AmortYears']})
                         .where(newstoragetypes.c.storagetypeId == types.c.typeId)
                         .where(types.c.modelId == allTypesModelId)
                         .where(types.c.Name == r['Name']))

    print '##### swapping tables #####'
    op.rename_table('storagetypes', 'oldstoragetypes')
    op.rename_table('newstoragetypes', 'storagetypes')
    op.drop_table('oldstoragetypes')

            


    print '##### done #####'


def downgrade():

    print '##### creating new downgraded storagetype table #####'

    op.create_table('newstoragetypes',
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

    print '##### Copying records #####'
    conn = op.get_bind()
    meta = sa.MetaData()

    storagetypes = sa.Table('storagetypes', meta, autoload=True, autoload_with=conn.engine)
    newstoragetypes = sa.Table('newstoragetypes', meta, autoload=True, autoload_with=conn.engine)

    copyTableRecords(storagetypes, newstoragetypes, conn)

    print '##### swapping tables #####'
    op.rename_table('storagetypes', 'oldstoragetypes')
    op.rename_table('newstoragetypes', 'storagetypes')
    op.drop_table('oldstoragetypes')

    print '##### done #####'
