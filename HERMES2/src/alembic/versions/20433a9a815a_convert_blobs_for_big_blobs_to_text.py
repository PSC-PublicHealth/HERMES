"""convert blobs for big blobs to text

Revision ID: 20433a9a815a
Revises: 2e15e69fbdab 
Create Date: 2016-03-31 13:51:31.509929

"""

# revision identifiers, used by Alembic.
revision = '20433a9a815a'
down_revision = '2e15e69fbdab'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

longblob = None
    
def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    
    try:
        op.alter_column('costSummaryKeyPointsBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('costSummaryResultsBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('geoResultsBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('hierarchicalCostSummaryBarChartBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('hierarchicalCostSummaryTreeMapBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('storeVialsBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('storeCapHistBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('modelD3JsonBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('vaHistBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('modelSummaryBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('transCapHistBlobHolder', 'blob',
                   existing_type=sa.BLOB(),
                   type_=mysql.LONGBLOB(),
                   existing_nullable=True)
        op.alter_column('models', 'refOnly',
                   existing_type=mysql.TINYINT(display_width=1),
                   type_=sa.Boolean(),
                   existing_nullable=True)
        op.alter_column('perdiemtypes', 'CountFirstDay',
                   existing_type=mysql.TINYINT(display_width=1),
                   type_=sa.Boolean(),
                   existing_nullable=True)
        op.alter_column('perdiemtypes', 'MustBeOvernight',
                   existing_type=mysql.TINYINT(display_width=1),
                   type_=sa.Boolean(),
                   existing_nullable=True)
        op.alter_column('stops', 'isSupplier',
                   existing_type=mysql.TINYINT(display_width=1),
                   type_=sa.Boolean(),
                   existing_nullable=True)
    except:
        pass
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('stops', 'isSupplier',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('perdiemtypes', 'MustBeOvernight',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('perdiemtypes', 'CountFirstDay',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('models', 'refOnly',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('geoResultsBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('costSummaryResultsBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('costSummaryKeyPointsBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('hierarchicalCostSummaryBarChartBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('hierarchicalCostSummaryTreeMapBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('modelD3JsonBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('modelSummaryBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('storeCapHistBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('storeVialsBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)
    op.alter_column('transCapHistBlobHolder', 'blob',
               existing_type=mysql.LONGBLOB(),
               type_=sa.BLOB(),
               existing_nullable=True)


    ### end Alembic commands ###