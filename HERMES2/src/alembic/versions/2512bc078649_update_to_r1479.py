"""update to r1479

Revision ID: 2512bc078649
Revises: fd6bb381a6e
Create Date: 2013-10-13 13:49:22.048000

"""

# revision identifiers, used by Alembic.
revision = '2512bc078649'
down_revision = 'fd6bb381a6e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('storesRpt', sa.Column('category', sa.String(length=250), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('storesRpt', 'category')
    ### end Alembic commands ###
