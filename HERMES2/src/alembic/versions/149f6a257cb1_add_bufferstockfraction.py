"""'add_bufferStockFraction'

Revision ID: 149f6a257cb1
Revises: 23ef41cec1b7
Create Date: 2016-10-12 03:02:17.859000

"""

# revision identifiers, used by Alembic.
revision = '149f6a257cb1'
down_revision = '23ef41cec1b7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    #op.drop_table('factoryOVW')
    op.drop_table('runs')
    op.add_column('stores', sa.Column('BufferStockFraction', sa.Float(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('stores', 'BufferStockFraction')
    op.create_table('runs',
    sa.Column('runId', sa.INTEGER(), nullable=False),
    sa.Column('startTime', sa.DATETIME(), nullable=True),
    sa.Column('endTime', sa.DATETIME(), nullable=True),
    sa.Column('name', sa.VARCHAR(length=250), nullable=True),
    sa.Column('modelId', sa.INTEGER(), nullable=True),
    sa.Column('status', sa.VARCHAR(length=250), nullable=True),
    sa.Column('run_location', sa.VARCHAR(length=250), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], [u'models.modelId'], ),
    sa.PrimaryKeyConstraint('runId')
    )
    #op.create_table('factoryOVW',
    #sa.Column('factoryOVWId', sa.INTEGER(), nullable=False),
    #sa.Column('modelId', sa.INTEGER(), nullable=True),
    #sa.Column('Name', sa.VARCHAR(length=250), nullable=True),
    #sa.Column('OVW', sa.FLOAT(), nullable=True),
    #sa.Column('Notes', sa.VARCHAR(length=4096), nullable=True),
    #sa.ForeignKeyConstraint(['modelId'], [u'models.modelId'], ),
    #sa.PrimaryKeyConstraint('factoryOVWId')
    #)
    ### end Alembic commands ###
