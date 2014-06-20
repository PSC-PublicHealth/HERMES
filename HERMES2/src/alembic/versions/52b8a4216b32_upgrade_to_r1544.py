"""upgrade to r1544

Revision ID: 52b8a4216b32
Revises: 58097291e8c6
Create Date: 2013-11-23 19:01:48.679364

"""

# revision identifiers, used by Alembic.
revision = '52b8a4216b32'
down_revision = '58097291e8c6'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### Alembic commands ###
    conn = op.get_bind()
    meta = sa.MetaData()
    demand= sa.Table('demand', meta, autoload=True, autoload_with=conn.engine)
    conn.execute(demand.delete().where(demand.c.count==0));
    ### end Alembic commands ###


def downgrade():
    ### Alembic commands ###
    pass
    ### end Alembic commands ###
