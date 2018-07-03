
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

engine = create_engine("mysql+mysqldb://hermes:hermes_pass@localhost/hermes?charset=utf8&use_unicode=0")
conn = engine.connect()

context = MigrationContext.configure(conn)
current_rev = context.get_current_revision()

from alembic.operations import Operations
op = Operations(context)
import sqlalchemy as sa

#perform whatever alembic ops you like here!
#examples:
#op.alter_column("mytable", "somecolumn", nullable=True)
#op.add_column('results', sa.Column('kmlVizStringRef', sa.Integer(), nullable=True))
#op.drop_column('results', 'kmlVizStringRef')
#op.execute("INSERT INTO prvgroups VALUES (1,'sysgroup')")
#op.create_table('prvusers',
#    sa.Column('userId', sa.Integer(), nullable=False),
#    sa.Column('userName', sa.String(length=32), nullable=True),
#    sa.PrimaryKeyConstraint('userId')
#    )
#op.drop_table('prvmodelaccessrights')
