"""merge oauth migration with existing heads

Revision ID: a0d8fb353876
Revises: 
Create Date: 2025-12-08 20:17:08.576281

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0d8fb353876'
down_revision = ('a1b2c3d4e5f7', 'd9ac10e39b15')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
