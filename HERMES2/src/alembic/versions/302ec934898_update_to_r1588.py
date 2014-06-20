"""update to r1588

Revision ID: 302ec934898
Revises: 1f72fe425541
Create Date: 2014-01-01 15:53:18.271000

"""

# revision identifiers, used by Alembic.
revision = '302ec934898'
down_revision = '1f72fe425541'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('parms', sa.Column('resultsGroupId', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('parms', 'resultsGroupId')
    ### end Alembic commands ###
