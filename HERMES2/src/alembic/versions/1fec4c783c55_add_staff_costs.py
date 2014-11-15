"""add staff costs

Revision ID: 1fec4c783c55
Revises: 27a7bae2b85e
Create Date: 2014-11-10 14:18:01.425064

"""

# revision identifiers, used by Alembic.
revision = '1fec4c783c55'
down_revision = '27a7bae2b85e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('stafftypes',
    sa.Column('stafftypeId', sa.Integer(), nullable=False),
    sa.Column('DisplayName', sa.String(length=250), nullable=True),
    sa.Column('SortOrder', sa.Integer(), nullable=True),
    sa.Column('BaseSalary', sa.Float(), nullable=True),
    sa.Column('BaseSalaryCurCode', sa.String(length=250), nullable=True),
    sa.Column('BaseSalaryYear', sa.Integer(), nullable=True),
    sa.Column('FractionEPI', sa.Float(), nullable=True),
    sa.Column('Notes', sa.String(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['stafftypeId'], ['types.typeId'], ),
    sa.PrimaryKeyConstraint('stafftypeId')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('stafftypes')
    ### end Alembic commands ###
