"""merge multiple migration heads

Revision ID: 9a8b7c6d5e4f
Revises: ('ee57f89c10f5', 'f6e5d4c3b2a1', 'b0e54d60e98b')
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a8b7c6d5e4f'
down_revision = ('ee57f89c10f5', 'f6e5d4c3b2a1', 'b0e54d60e98b')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no schema changes needed
    # It just merges the three migration heads into one
    pass


def downgrade():
    # This is a merge migration - no schema changes needed
    pass

