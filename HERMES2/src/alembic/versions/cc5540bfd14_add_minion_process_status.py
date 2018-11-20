"""add minion process status

Revision ID: cc5540bfd14
Revises: 125b181e7324
Create Date: 2017-05-16 16:49:01.028897

"""

# revision identifiers, used by Alembic.
revision = 'cc5540bfd14'
down_revision = '4e0eaf0351e6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tickProcess',
    sa.Column('tickId', sa.Integer(), nullable=False),
    sa.Column('modelId', sa.Integer(), nullable=True),
    sa.Column('processId', sa.Integer(), nullable=True),
    sa.Column('hostName', sa.String(length=250), nullable=True),
    sa.Column('status', sa.String(length=250), nullable=True),
    sa.Column('fracDone', sa.Float(), nullable=True),
    sa.Column('lastUpdate', sa.Integer(), nullable=True),
    sa.Column('runCount',sa.Integer(),nullable=True),
    sa.Column('runName',sa.String(length=250),nullable=True),
    sa.Column('runDisplayName',sa.String(length=250),nullable=True),
    sa.Column('modelName',sa.String(length=250),nullable=True),
    sa.Column('starttime',sa.String(length=250),nullable=True),
    sa.Column('note',sa.VARCHAR(length=4096), nullable=True),
    sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
    sa.PrimaryKeyConstraint('tickId')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tickProcess')
    ### end Alembic commands ###
