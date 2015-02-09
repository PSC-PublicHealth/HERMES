#! /usr/bin/env python

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
"""
This module contains functions that may be of use in alembic version scripts.
"""

_hermes_svn_id_="$Id$"

from alembic import op
import sqlalchemy as sa

def copyTableRecords(inTable, outTable, conn, defaultVal=None):
    oldKeys = [c.name for c in inTable.columns]
    newKeys = [c.name for c in outTable.columns]
    rows = conn.execute(sa.select([inTable])).fetchall()
    for i in range(len(rows)):
        row = rows[i]
        try:
            newRow = {}
            for k in newKeys:
                if k in oldKeys:
                    newRow[k] = row[k]
                else:
                    newRow[k] = defaultVal
            # print newRow
            conn.execute(outTable.insert(), newRow)
        except Exception, e:
            print 'dropping bad record on error: %s' % str(e)
            rows = conn.execute(sa.select([inTable])).fetchall()

def findAllTypesModelId(conn, meta):
    """
    Find the id of the AllTypesModel.  Returns NULL if that model doesn't exist.
    """
    models = sa.Table('models', meta, autoload=True, autoload_with=conn.engine)
    allTypesModelId = None
    for row in conn.execute(sa.select([models]).where(models.c.name==op.inline_literal('AllTypesModel'))):
        allTypesModelId = row[models.c.modelId]
    return allTypesModelId
