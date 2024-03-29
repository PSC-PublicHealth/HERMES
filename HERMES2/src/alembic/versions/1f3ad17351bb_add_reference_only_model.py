"""add ref only models (which are intended to only hold types and similar

Revision ID: 1f3ad17351bb
Revises: 3574610fd4e0
Create Date: 2014-12-05 10:25:41.372518

"""

# revision identifiers, used by Alembic.
revision = '1f3ad17351bb'
down_revision = '3574610fd4e0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('models', sa.Column('refOnly', sa.Boolean(), nullable=True))

    conn = op.get_bind()
    meta = sa.MetaData()

    models = sa.Table('models', meta, autoload=True, autoload_with=conn.engine)
    prvmodelaccessrights = sa.Table('prvmodelaccessrights', meta, autoload=True, autoload_with=conn.engine)

    conn.execute(models.update().values(refOnly=False))
    conn.execute(models.update().where(models.c.name=="AllTypesModel").values(refOnly=True))
    try:
        conn.execute(models.delete().where(models.c.name=="UserTypesModel"))
        conn.execute(prvmodelaccessrights.update().where(prvmodelaccessrights.c.readGroupId==1).values(readGroupId=2))
    except:
        pass
        

    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('models', 'refOnly')
    ### end Alembic commands ###
