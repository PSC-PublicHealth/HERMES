#! /usr/bin/env python

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
    models = sa.Table('models', meta, autoload=True, autoload_with=conn.engine)
    allTypesModelId = None
    for row in conn.execute(sa.select([models]).where(models.c.name==op.inline_literal('AllTypesModel'))):
        allTypesModelId = row[models.c.modelId]
    return allTypesModelId
