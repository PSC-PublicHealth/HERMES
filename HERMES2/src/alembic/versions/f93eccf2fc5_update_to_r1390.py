"""update to r1390

Revision ID: f93eccf2fc5
Revises: 1f64c2c9f97b
Create Date: 2013-08-15 15:27:16.923884

"""

# revision identifiers, used by Alembic.
revision = 'f93eccf2fc5'
down_revision = '1f64c2c9f97b'

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('costs',
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
    op.add_column('demand', sa.Column('demandType', sa.CHAR(length=1), nullable=True))
    op.execute("UPDATE demand SET demandType='U'")
                           
    op.add_column('icetypes', sa.Column('DisplayName', sa.String(length=250), nullable=True))
    op.add_column('packagetypes', sa.Column('DisplayName', sa.String(length=250), nullable=True))
    op.add_column('peopletypes', sa.Column('DisplayName', sa.String(length=250), nullable=True))
    op.alter_column('stops', u'isSupplier',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.drop_column('storagetypes', u'className')
    op.add_column('storagetypes', sa.Column('ClassName', sa.String(length=250), nullable=True))
    op.add_column('storagetypes', sa.Column('DisplayName', sa.String(length=250), nullable=True))
    op.add_column('storagetypes', sa.Column('ColdLifetime', sa.Float(), nullable=True))
    op.drop_column('storagetypes', u'ColdLiefetime')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('storagetypes', sa.Column(u'ColdLiefetime', mysql.FLOAT(), nullable=True))
    op.add_column('storagetypes', sa.Column(u'className', mysql.VARCHAR(length=250), nullable=True))
    op.drop_column('storagetypes', 'ColdLifetime')
    op.drop_column('storagetypes', 'DisplayName')
    op.drop_column('storagetypes', 'ClassName')
    op.alter_column('stops', u'isSupplier',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.drop_column('peopletypes', 'DisplayName')
    op.drop_column('packagetypes', 'DisplayName')
    op.drop_column('icetypes', 'DisplayName')
    op.drop_column('demand', 'demandType')
    op.drop_table('costs')
    ### end Alembic commands ###
