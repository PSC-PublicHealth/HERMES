"""fridge and truck compatibility tweaks

Revision ID: 230f55ad2536
Revises: 2ab3330d0d4
Create Date: 2014-07-25 13:46:42.505432

"""

# revision identifiers, used by Alembic.
revision = '230f55ad2536'
down_revision = '2ab3330d0d4'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import csv_tools
import os.path

def keyMap(k):
    if k=='BaseCostCur' : return 'BaseCostCurCode'
    else: return k

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    
    conn = op.get_bind()
    meta = sa.MetaData()

    print '##### loading fridgeTypeInfo #####'
    here = os.path.split(os.path.abspath(__file__))[0]
    with open(os.path.join(here,'..','..','..','master_data','standardtypes','fridgeTypeInfo.csv'),'rU') as f:
        keys,recs = csv_tools.parseCSV(f)
    recDict = {r['Name']:r for r in recs}
        
    print '##### finding AllTypesModel #####'
    models = sa.Table('models', meta, autoload=True, autoload_with=conn.engine)
    typeTable = sa.Table('types', meta, autoload=True, autoload_with=conn.engine)
    allTypesModelId = None
    for row in conn.execute(sa.select([models]).where(models.c.name==op.inline_literal('AllTypesModel'))):
        allTypesModelId = row[models.c.modelId]
    
    print '##### updating storagetypes table #####'
    storagetypes = sa.Table('storagetypes', meta, autoload=True, autoload_with=conn.engine)

    updateTuples = []
    for row in conn.execute(sa.select([typeTable]).where(typeTable.c.modelId==allTypesModelId).where(typeTable.c.typeClass==op.inline_literal('fridges'))):
        for fRow in conn.execute(sa.select([storagetypes]).where(storagetypes.c.storagetypeId==row[typeTable.c.typeId])):
            if row[typeTable.c.Name] in ['Std_ColdRoomFreezer_U','Std_ColdRoomFridge_U']:
                newRow = recDict[row[typeTable.c.Name]]
                updateTuples.append((row[typeTable.c.typeId], 
                                     {newKey:newVal for newKey,newVal in newRow.items() 
                                      if keyMap(newKey) in fRow and newVal != fRow[keyMap(newKey)] and newVal != ''}))
    print "updates: %s"%str(updateTuples)
    for id,upDict in updateTuples:
        if upDict:
            op.execute(storagetypes.update().where(storagetypes.c.storagetypeId==op.inline_literal(str(id))).values(upDict))

    print '##### loading truckTypeInfo #####'
    here = os.path.split(os.path.abspath(__file__))[0]
    with open(os.path.join(here,'..','..','..','master_data','standardtypes','truckTypeInfo.csv'),'rU') as f:
        keys,recs = csv_tools.parseCSV(f)
    recDict = {r['Name']:r for r in recs}
        
    print '##### Renaming ToyotaHilux -> Std_DoubleCabTruck #####'
    op.execute(typeTable.update().where(typeTable.c.modelId==allTypesModelId)\
               .where(typeTable.c.Name==op.inline_literal('Std_ToyotaHilux_4x4'))\
               .values({typeTable.c.Name:op.inline_literal('Std_DoubleCabTruck')}))

    print '##### updating trucktypes table #####'
    trucktypes = sa.Table('trucktypes', meta, autoload=True, autoload_with=conn.engine)

    updateTuples = []
    for row in conn.execute(sa.select([typeTable]).where(typeTable.c.modelId==allTypesModelId).where(typeTable.c.typeClass==op.inline_literal('trucks'))):
        for fRow in conn.execute(sa.select([trucktypes]).where(trucktypes.c.trucktypeId==row[typeTable.c.typeId])):
            #if row[typeTable.c.Name] in ['Std_ColdRoomFreezer_U','Std_ColdRoomFridge_U']:
            print recDict.keys()
            print row[typeTable.c.Name]
            newRow = recDict[row[typeTable.c.Name]]
            updateTuples.append((row[typeTable.c.typeId], 
                                 {newKey:newVal for newKey,newVal in newRow.items() 
                                  if keyMap(newKey) in fRow and newVal != fRow[keyMap(newKey)] and newVal != ''}))
    print "updates: %s"%str(updateTuples)
    for id,upDict in updateTuples:
        if upDict:
            op.execute(trucktypes.update().where(trucktypes.c.trucktypeId==op.inline_literal(str(id))).values(upDict))

    print '##### done #####'
    
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    pass
    ### end Alembic commands ###