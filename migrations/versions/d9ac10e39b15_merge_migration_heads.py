"""Merge migration heads

Revision ID: d9ac10e39b15
Revises: abc123def456, b13bbce8fbd
Create Date: 2025-12-03 02:08:05.930643

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9ac10e39b15'
down_revision = ('abc123def456', 'b13bbce8fbd')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
