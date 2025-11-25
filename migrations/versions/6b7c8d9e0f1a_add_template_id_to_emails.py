"""add template_id to emails

Revision ID: 6b7c8d9e0f1a
Revises: 5a6b7c8d9e00
Create Date: 2025-01-15 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b7c8d9e0f1a'
down_revision = '5a6b7c8d9e00'
branch_labels = None
depends_on = None


def upgrade():
    # Add template_id column to emails table
    op.add_column('emails', sa.Column('template_id', sa.String(length=36), nullable=True))
    op.create_foreign_key(
        'emails_template_id_fkey',
        'emails',
        'email_templates',
        ['template_id'],
        ['template_id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('emails_template_id_fkey', 'emails', type_='foreignkey')
    op.drop_column('emails', 'template_id')

