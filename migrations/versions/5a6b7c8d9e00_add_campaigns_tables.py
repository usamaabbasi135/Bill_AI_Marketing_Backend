"""add campaigns tables

Revision ID: 5a6b7c8d9e00
Revises: 7f8e9d0c1b2a
Create Date: 2025-01-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a6b7c8d9e00'
down_revision = '7f8e9d0c1b2a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'campaigns',
        sa.Column('campaign_id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('post_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.post_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('campaign_id')
    )

    op.create_table(
        'campaign_profiles',
        sa.Column('campaign_id', sa.String(length=36), nullable=False),
        sa.Column('profile_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('email_id', sa.String(length=36), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.campaign_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.profile_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['email_id'], ['emails.email_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('campaign_id', 'profile_id')
    )


def downgrade():
    op.drop_table('campaign_profiles')
    op.drop_table('campaigns')


