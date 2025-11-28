"""add analyzed_at to posts

Revision ID: 7f8e9d0c1b2a
Revises: 3a4b5c6d7e8f
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f8e9d0c1b2a'
down_revision = '3a4b5c6d7e8f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('analyzed_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('posts', 'analyzed_at')

