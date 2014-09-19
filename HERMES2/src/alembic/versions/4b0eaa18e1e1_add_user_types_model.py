"""add user types model to the database

Revision ID: 4b0eaa18e1e1
Revises: 5535d37cb69f
Create Date: 2014-09-19 15:30:08.724605

"""

# revision identifiers, used by Alembic.
revision = '4b0eaa18e1e1'
down_revision = '5535d37cb69f'

from alembic import op
import sqlalchemy as sa

def upgrade():
    conn = op.get_bind()

    md = sa.MetaData()
    
    conn = op.get_bind()
    engine = conn.engine
    conn.execute(sa.Table('models', md, autoload=True, autoload_with=engine).insert(),
                 [{'note':"user types model", 'name':'UserTypesModel'}])


def downgrade():
    pass
