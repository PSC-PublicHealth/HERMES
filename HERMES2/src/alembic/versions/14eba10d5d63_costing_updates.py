"""costing updates

Revision ID: 14eba10d5d63
Revises: 3d9c8b4b7acd
Create Date: 2014-09-24 13:37:27.860230

"""

# revision identifiers, used by Alembic.
revision = '14eba10d5d63'
down_revision = '3d9c8b4b7acd'

from alembic import op
import sqlalchemy as sa
import sys

def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData()
    
    # Update the cost parameters of OUTDOORS (and any other storagetype made by
    # 'mothernature'
    fridgeTable = sa.Table('storagetypes', meta, autoload=True, autoload_with=conn.engine)

    print "######### completing 'mothernature' cost entries"
    conn.execute(fridgeTable.update().where(fridgeTable.c.Make=='mothernature')\
                 .values({fridgeTable.c.BaseCost:0.0,
                          fridgeTable.c.BaseCostCurCode:u'EUR',
                          fridgeTable.c.BaseCostYear:2012}))
    
    print "######### creating replacement legacy cost table"
    legacyCostSummary = sa.Table('legacyCostSummary', meta, autoload=True, autoload_with=conn.engine)
    newLegacyCostSummary = sa.Table('newLegacyCostSummary', meta,
        sa.Column('legacySummaryId', sa.Integer(), nullable=False),
        sa.Column('ReportingLevel', sa.String(length=250), nullable=True),
        sa.Column('ReportingBranch', sa.String(length=250), nullable=True),
        sa.Column('ReportingIntervalDays', sa.Float(), nullable=True),
        sa.Column('DaysPerYear', sa.Float(), nullable=True),
        sa.Column('Currency', sa.String(length=250), nullable=True),
        sa.Column('BaseYear', sa.Integer(), nullable=True),
        sa.Column('RouteTrips', sa.Integer(), nullable=True),
        sa.Column('PerDiemDays', sa.Integer(), nullable=True),
        sa.Column('CostingTreatmentDays', sa.Integer(), nullable=True),
        sa.Column('PerDiemCost', sa.Float(), nullable=True),
        sa.Column('PerKmCost', sa.Float(), nullable=True),
        sa.Column('PerTripCost', sa.Float(), nullable=True),
        sa.Column('TransportCost', sa.Float(), nullable=True),
        sa.Column('LaborCost', sa.Float(), nullable=True),
        sa.Column('StorageCost', sa.Float(), nullable=True),
        sa.Column('BuildingCost', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['legacySummaryId'], ['costSummary.summaryId'], ),
        sa.PrimaryKeyConstraint('legacySummaryId')
    )
    newLegacyCostSummary.create(conn, checkfirst=True)
    
    print "######## copying records"
    
    rows = conn.execute(sa.select([legacyCostSummary])).fetchall()
    for i in range(len(rows)):
        row = rows[i]
        try:
            conn.execute( newLegacyCostSummary.insert().values( legacySummaryId=row[legacyCostSummary.c.legacySummaryId],
                                                                ReportingLevel=row[legacyCostSummary.c.ReportingLevel],
                                                                ReportingBranch=row[legacyCostSummary.c.ReportingBranch],
                                                                ReportingIntervalDays=row[legacyCostSummary.c.ReportingIntervalDays],
                                                                DaysPerYear=row[legacyCostSummary.c.DaysPerYear],
                                                                Currency=row[legacyCostSummary.c.Currency],
                                                                BaseYear=None,
                                                                RouteTrips=row[legacyCostSummary.c.RouteTrips],
                                                                PerDiemDays=row[legacyCostSummary.c.PerDiemDays],
                                                                CostingTreatmentDays=row[legacyCostSummary.c.CostingTreatmentDays],
                                                                PerDiemCost=row[legacyCostSummary.c.PerDiemCost],
                                                                PerKmCost=row[legacyCostSummary.c.PerKmCost],
                                                                PerTripCost=row[legacyCostSummary.c.PerTripCost],
                                                                TransportCost=row[legacyCostSummary.c.TransportCost],
                                                                LaborCost=row[legacyCostSummary.c.LaborCost],
                                                                StorageCost=row[legacyCostSummary.c.StorageCost],
                                                                BuildingCost=row[legacyCostSummary.c.BuildingCost]
                                                               ))
        except Exception,e:
            print 'dropping bad record on error: %s'%str(e)
            rows = conn.execute(sa.select([legacyCostSummary])).fetchall()
            
    print "####### swapping tables"
    op.rename_table('legacyCostSummary', 'oldLegacyCostSummary')
    op.rename_table('newLegacyCostSummary', 'legacyCostSummary')
    op.drop_table('oldLegacyCostSummary')
    
    print "####### done"

def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData()
    
    print "######### creating downgraded legacy cost table"
    legacyCostSummary = sa.Table('legacyCostSummary', meta, autoload=True, autoload_with=conn.engine)
    newLegacyCostSummary = sa.Table('newLegacyCostSummary', meta,
        sa.Column('legacySummaryId', sa.Integer(), nullable=False),
        sa.Column('ReportingLevel', sa.String(length=250), nullable=True),
        sa.Column('ReportingBranch', sa.String(length=250), nullable=True),
        sa.Column('ReportingIntervalDays', sa.Float(), nullable=True),
        sa.Column('DaysPerYear', sa.Float(), nullable=True),
        sa.Column('Currency', sa.String(length=250), nullable=True),
        sa.Column('RouteTrips', sa.Integer(), nullable=True),
        sa.Column('PerDiemDays', sa.Integer(), nullable=True),
        sa.Column('CostingTreatmentDays', sa.Integer(), nullable=True),
        sa.Column('PerDiemCost', sa.Float(), nullable=True),
        sa.Column('PerKmCost', sa.Float(), nullable=True),
        sa.Column('PerTripCost', sa.Float(), nullable=True),
        sa.Column('TransportCost', sa.Float(), nullable=True),
        sa.Column('LaborCost', sa.Float(), nullable=True),
        sa.Column('StorageCost', sa.Float(), nullable=True),
        sa.Column('BuildingCost', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['legacySummaryId'], ['costSummary.summaryId'], ),
        sa.PrimaryKeyConstraint('legacySummaryId')
    )
    newLegacyCostSummary.create(conn, checkfirst=True)
    
    print "######## copying records"
    
    rows = conn.execute(sa.select([legacyCostSummary])).fetchall()
    for i in range(len(rows)):
        row = rows[i]
        try:
            conn.execute( newLegacyCostSummary.insert().values( legacySummaryId=row[legacyCostSummary.c.legacySummaryId],
                                                                ReportingLevel=row[legacyCostSummary.c.ReportingLevel],
                                                                ReportingBranch=row[legacyCostSummary.c.ReportingBranch],
                                                                ReportingIntervalDays=row[legacyCostSummary.c.ReportingIntervalDays],
                                                                DaysPerYear=row[legacyCostSummary.c.DaysPerYear],
                                                                Currency=row[legacyCostSummary.c.Currency],
                                                                RouteTrips=row[legacyCostSummary.c.RouteTrips],
                                                                PerDiemDays=row[legacyCostSummary.c.PerDiemDays],
                                                                CostingTreatmentDays=row[legacyCostSummary.c.CostingTreatmentDays],
                                                                PerDiemCost=row[legacyCostSummary.c.PerDiemCost],
                                                                PerKmCost=row[legacyCostSummary.c.PerKmCost],
                                                                PerTripCost=row[legacyCostSummary.c.PerTripCost],
                                                                TransportCost=row[legacyCostSummary.c.TransportCost],
                                                                LaborCost=row[legacyCostSummary.c.LaborCost],
                                                                StorageCost=row[legacyCostSummary.c.StorageCost],
                                                                BuildingCost=row[legacyCostSummary.c.BuildingCost]
                                                               ))
        except Exception,e:
            print 'dropping bad record on error: %s'%str(e)
            rows = conn.execute(sa.select([legacyCostSummary])).fetchall()
            
    print "####### swapping tables"
    op.rename_table('legacyCostSummary', 'oldLegacyCostSummary')
    op.rename_table('newLegacyCostSummary', 'legacyCostSummary')
    op.drop_table('oldLegacyCostSummary')
    
    print "####### done"
    
