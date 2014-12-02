"""add store costs

Revision ID: 3574610fd4e0
Revises: 5440d70e660d
Create Date: 2014-12-01 16:00:30.340501

"""

# revision identifiers, used by Alembic.
revision = '3574610fd4e0'
down_revision = '5440d70e660d'

from alembic import op
import sqlalchemy as sa
from alembic_helper import copyTableRecords


def upgrade():

    print '##### Creating newstores table #####'
    op.create_table('newstores',
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
                    sa.Column('SiteCost', sa.Float(), nullable=True),
                    sa.Column('SiteCostCurCode', sa.String(length=250), nullable=True),
                    sa.Column('SiteCostYear', sa.Integer(), nullable=True),
                    sa.Column('Notes', sa.String(length=4096), nullable=True),
                    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
                    sa.PrimaryKeyConstraint('storeId')
                    )

    print '##### Copying records #####'
    conn = op.get_bind()
    meta = sa.MetaData()

    stores = sa.Table('stores', meta, autoload=True, autoload_with=conn.engine)
    newstores = sa.Table('newstores', meta, autoload=True, autoload_with=conn.engine)

    copyTableRecords(stores, newstores, conn)

    print '##### swapping tables #####'
    op.rename_table('stores', 'oldstores')
    op.rename_table('newstores', 'stores')
    op.drop_table('oldstores')

    print '##### done #####'


def downgrade():
    print '##### Creating downgraded newstores table #####'
    op.create_table('newstores',
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

    print '##### Copying records #####'
    conn = op.get_bind()
    meta = sa.MetaData()

    stores = sa.Table('stores', meta, autoload=True, autoload_with=conn.engine)
    newstores = sa.Table('newstores', meta, autoload=True, autoload_with=conn.engine)

    copyTableRecords(stores, newstores, conn)

    print '##### swapping tables #####'
    op.rename_table('stores', 'oldstores')
    op.rename_table('newstores', 'stores')
    op.drop_table('oldstores')

    print '##### done #####'
    ### end Alembic commands ###
