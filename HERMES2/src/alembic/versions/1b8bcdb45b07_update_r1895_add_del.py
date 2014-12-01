"""update r1895 add delays

Revision ID: 1b8bcdb45b07
Revises: 4b0eaa18e1e1
Create Date: 2014-09-22 19:04:37.840000

"""

# revision identifiers, used by Alembic.
revision = '1b8bcdb45b07'
down_revision = '4b0eaa18e1e1'

from alembic import op
import sqlalchemy as sa
import sys


def upgrade():
    
    conn = op.get_bind()
    meta = sa.MetaData()
    
    routes = sa.Table('routes', meta, autoload=True, autoload_with=conn.engine)
    
    newroutes = sa.Table('newroutes',meta,
                sa.Column('routeId', sa.Integer(), nullable=False),
                sa.Column('modelId', sa.Integer(), nullable=True),
                sa.Column('RouteName', sa.String(length=250), nullable=True),
                sa.Column('Type', sa.String(length=250), nullable=True),
                sa.Column('TruckType', sa.String(length=250), nullable=True),
                sa.Column('ShipIntervalDays', sa.Float(), nullable=True),
                sa.Column('ShipLatencyDays', sa.Float(), nullable=True),
                sa.Column('Conditions', sa.String(length=250), nullable=True),
                sa.Column('PickupDelayFrequency',sa.Float(),nullable=True),
                sa.Column('PickupDelayMagnitude',sa.Float(),nullable=True),
                sa.Column('PickupDelaySigma',sa.Float(),nullable=True),
                sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
                sa.PrimaryKeyConstraint('routeId')
                )
    newroutes.create(conn, checkfirst=True)
    
    print '## Transcribing old routes'
    result = conn.execute(sa.select([routes]))
    rows = result.fetchall()
    
    for i in range(len(rows)):
        row = rows[i]
        try:
            conn.execute(newroutes.insert().values(routeId=row[routes.c.routeId],
                                                   modelId=row[routes.c.modelId],
                                                   RouteName=row[routes.c.RouteName],
                                                   Type=row[routes.c.Type],
                                                   TruckType=row[routes.c.TruckType],
                                                   ShipIntervalDays=row[routes.c.ShipIntervalDays],
                                                   ShipLatencyDays=row[routes.c.ShipLatencyDays],
                                                   Conditions=row[routes.c.Conditions],
                                                   PickupDelayFrequency=0.0,
                                                   PickupDelayMagnitude=0.0,
                                                   PickupDelaySigma=0.0
                                                   ))
        except Exception,e:
            print 'Error migrating Routes'
            print str(e)
            sys.exit()
        
    print '### swapping route tables ###'
    op.rename_table('routes','oldroutes')
    op.rename_table('newroutes','routes')
    op.drop_table('oldroutes')
    
    routes2 = sa.Table('routes',meta,autoload=True,extend_existing=True,autoload_with=conn.engine)
    print '#### done #####'
    
def downgrade():
    pass
    ### end Alembic commands ###
