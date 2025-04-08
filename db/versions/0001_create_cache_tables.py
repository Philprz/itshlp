"""create cached tables

Revision ID: 0001_create_cache_tables
Revises: 
Create Date: 2025-04-08

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_create_cache_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('cached_queries',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('query', sa.Text()),
        sa.Column('filters', sa.JSON()),
        sa.Column('limit', sa.Integer()),
        sa.Column('embedding', sa.Integer()),
        sa.Column('raw_results', sa.JSON()),
        sa.Column('created_at', sa.DateTime())
    )
    op.create_table('cached_formats',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('format_type', sa.String()),
        sa.Column('content', sa.Text()),
        sa.Column('sources', sa.String()),
        sa.Column('meta', sa.JSON()),
        sa.Column('created_at', sa.DateTime())
    )

def downgrade():
    op.drop_table('cached_queries')
    op.drop_table('cached_formats')
