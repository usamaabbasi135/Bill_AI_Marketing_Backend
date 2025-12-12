"""add email sending fields

Revision ID: add_email_sending_fields
Revises: a0d8fb353876
Create Date: 2025-12-08 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_email_sending_fields'
down_revision = 'a0d8fb353876'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns if they don't exist
    op.add_column('emails', sa.Column('message_id', sa.String(length=255), nullable=True))
    op.add_column('emails', sa.Column('sent_at', sa.DateTime(), nullable=True))
    op.add_column('emails', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('emails', 'error_message')
    op.drop_column('emails', 'sent_at')
    op.drop_column('emails', 'message_id')

