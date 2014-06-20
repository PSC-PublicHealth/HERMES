"""upgrade_to_r1593

Revision ID: 285b4768292c
Revises: 302ec934898
Create Date: 2014-01-13 16:20:41.703776

This script changes existing AllTypesModels to include a generic  transport types to add a 
Std_CB_RCW25 type and to reference that type from AllTypesModel generic transport types.
"""

# revision identifiers, used by Alembic.
revision = '285b4768292c'
down_revision = '302ec934898'

import sys

from alembic import op
import sqlalchemy as sa

def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData()
    models = sa.Table('models', meta, autoload=True, autoload_with=conn.engine)
    types = sa.Table('types', meta, autoload=True, autoload_with=conn.engine)
    storagetypes = sa.Table('storagetypes', meta, autoload=True, autoload_with=conn.engine)
    trucktypes = sa.Table('trucktypes', meta, autoload=True, autoload_with=conn.engine)
    allTypesRec = conn.execute( sa.select([models.c.modelId]).where(models.c.name=='AllTypesModel') ).fetchone()
    # If the AllTypesModel is not defined, there is nothing to fix.
    if allTypesRec is not None:
        allTypesModelId = allTypesRec[models.c.modelId]
        conn.execute(types.insert().values(typeClass='fridges', modelId=allTypesModelId,Name='Std_CB_RCW25'))
        newTypeId = conn.execute( sa.select([types.c.typeId]).where(types.c.Name=='Std_CB_RCW25')
                                  .where(types.c.modelId==allTypesModelId) ).fetchone()[0]
        conn.execute(storagetypes.insert().values(storagetypeId=newTypeId, DisplayName='RCW25', 
                                                  Make='generic',Model='CB',Year='YearUnk',Energy='',
                                                  freezer=0.0, cooler=20.7, roomtemperature=0.0,
                                                  ClassName='ShippableFridge',Notes='source: none'))
        conn.execute(demand.delete().where(demand.c.count==0));
        for nm,storage in [('Std_ToyotaHilux_4x4','4*Std_CB_RCW25'),
                           ('Std_SingleCabTruck','8*Std_CB_RCW25'),
                           ('Std_motorbike','Std_VC')]:
            tpId = conn.execute( sa.select([types.c.typeId]).where(types.c.Name==nm) \
                                  .where(types.c.modelId==allTypesModelId) ).fetchone()[0]
        
            conn.execute( trucktypes.update().where(trucktypes.c.trucktypeId==tpId).values(Storage=storage) )

def downgrade():
    pass
