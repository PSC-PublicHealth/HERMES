"""Convert ShdParam to json

Revision ID: 2647c0b31065
Revises: 14eba10d5d63
Create Date: 2014-09-27 23:00:46.760645

"""

# revision identifiers, used by Alembic.
revision = '2647c0b31065'
down_revision = '14eba10d5d63'

from alembic import op
import sqlalchemy as sa
import sys
import json
import types
from input import InputDefault

def upgrade():
    ### Alembic commands follow ###

    conn = op.get_bind()
    meta = sa.MetaData()

    print "######### creating the InputDefault parser"
    defTokenizer = InputDefault()
    
    print "######### creating replacement parms table"
    parms = sa.Table('parms', meta, autoload=True, autoload_with=conn.engine)
    newParms = sa.Table('newParms', meta,
        sa.Column('parmId', sa.Integer(), nullable=False),
        sa.Column('modelId', sa.Integer(), nullable=True),
        sa.Column('key', sa.String(length=250), nullable=True),
        sa.Column('value', sa.String(length=250), nullable=True),
        sa.Column('resultsGroupId', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
        sa.PrimaryKeyConstraint('parmId')
    )
    newParms.create(conn, checkfirst=True)

    print "######## copying records"

    rows = conn.execute(sa.select([parms])).fetchall()
    for i in range(len(rows)):
        row = rows[i]
        try:
            
            oldKey = row[parms.c.key]
            oldVal = row[parms.c.value]
            tokType = defTokenizer.TokenDict[oldKey].type
            if tokType in ['string', 'stringOrNone', 'filename', 'filenameOrNone']:
                if (oldVal.startswith ("'") and oldVal.endswith("'")) \
                    or (oldVal.startswith ("'") and oldVal.endswith("'")):
                    oldVal = oldVal[1:-1]
            
            if tokType in ['stringOrNone', 'intOrNone', 'longOrNone', 'floatOrNone', 'filenameOrNone'] \
                and isinstance(oldVal,types.StringTypes) and oldVal.lower() == 'none':
                oldVal = None
            
            newVal = json.dumps(defTokenizer.processKeywordValue(oldKey, oldVal), separators=(',',':'))
            conn.execute( newParms.insert().values( parmId=row[parms.c.parmId],
                                                    modelId=row[parms.c.modelId],
                                                    key=row[parms.c.key],
                                                    value=newVal,
                                                    resultsGroupId=row[parms.c.resultsGroupId]
                                                    ))
        except Exception,e:
            print 'dropping bad record on error: %s'%str(e)
            rows = conn.execute(sa.select([parms])).fetchall()
            
    print "####### swapping tables"
    op.rename_table('parms', 'oldParms')
    op.rename_table('newParms', 'parms')
    op.drop_table('oldParms')
    
    print "####### done"
    
    ### end Alembic commands ###


def downgrade():
    ### Alembic commands follow ###
    conn = op.get_bind()
    meta = sa.MetaData()

    print "######### creating the InputDefault parser"
    defTokenizer = InputDefault()
     
    print "######### creating replacement parms table"
    parms = sa.Table('parms', meta, autoload=True, autoload_with=conn.engine)
    newParms = sa.Table('newParms', meta,
        sa.Column('parmId', sa.Integer(), nullable=False),
        sa.Column('modelId', sa.Integer(), nullable=True),
        sa.Column('key', sa.String(length=250), nullable=True),
        sa.Column('value', sa.String(length=250), nullable=True),
        sa.Column('resultsGroupId', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['modelId'], ['models.modelId'], ),
        sa.PrimaryKeyConstraint('parmId')
    )
    newParms.create(conn, checkfirst=True)
 
    print "######## copying records"
     
    rows = conn.execute(sa.select([parms])).fetchall()
    for i in range(len(rows)):
        row = rows[i]
        try:
             
            oldKey = row[parms.c.key]
            oldVal = json.loads(row[parms.c.value])
            tokType = defTokenizer.TokenDict[oldKey].type
            if isinstance(oldVal, types.ListType):
                if tokType in ['string_list','filename_list'] and oldKey != 'monitor':
                    newVal = ','.join(["'%s'"%e for e in oldVal])
                else:
                    newVal = ','.join([str(e) for e in oldVal])
            elif tokType in ['string', 'stringOrNone']:
                newVal = oldVal
                if oldKey == 'model': 
                    if newVal[0] not in ['"',"'",u'"',u"'"] and newVal.lower()!='none':
                        if isinstance(newVal, types.StringType):
                            newVal = "'"+newVal+"'"
                        elif isinstance(newVal, types.UnicodeType):
                            newVal = u"'"+newVal+u"'"
#                 if isinstance(newVal, types.StringType):
#                     newVal = "'"+newVal+"'"
#                 elif isinstance(newVal, types.UnicodeType):
#                     newVal = u"'"+newVal+u"'"
            elif tokType in ['filename', 'filenameOrNone']:
                newVal = oldVal
                if newVal[0] not in ['"',"'",u'"',u"'"] and newVal.lower()!='none':
                    if isinstance(newVal, types.StringType):
                        newVal = "'"+newVal+"'"
                    elif isinstance(newVal, types.UnicodeType):
                        newVal = u"'"+newVal+u"'"
            else:
                newVal = unicode(oldVal)
            conn.execute( newParms.insert().values( parmId=row[parms.c.parmId],
                                                    modelId=row[parms.c.modelId],
                                                    key=row[parms.c.key],
                                                    value=newVal,
                                                    resultsGroupId=row[parms.c.resultsGroupId]
                                                    ))
        except Exception,e:
            print 'dropping bad record on error: %s'%str(e)
            rows = conn.execute(sa.select([parms])).fetchall()
             
    print "####### swapping tables"
    op.rename_table('parms', 'oldnewParms')
    op.rename_table('newParms', 'parms')
    op.drop_table('oldnewParms')
    
    print "####### done"
    

    ### end Alembic commands ###
