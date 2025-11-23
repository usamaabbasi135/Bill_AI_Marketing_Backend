"""add deleted_at to emails for soft delete

Revision ID: ee57f89c10f5
Revises: 6b7c8d9e0f1a
Create Date: 2025-11-22 22:06:25.863167

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee57f89c10f5'
down_revision = '6b7c8d9e0f1a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('emails', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('emails', 'deleted_at')
