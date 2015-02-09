###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################

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
