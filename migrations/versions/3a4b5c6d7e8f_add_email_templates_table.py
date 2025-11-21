"""add email_templates table

Revision ID: 3a4b5c6d7e8f
Revises: 2ddb63f4447f
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a4b5c6d7e8f'
down_revision = '2ddb63f4447f'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_templates table
    op.create_table('email_templates',
        sa.Column('template_id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('template_id')
    )
    
    # Insert 3 default templates (tenant_id is NULL for defaults)
    # Using fixed UUIDs for default templates so they're consistent across all tenants
    op.execute("""
        INSERT INTO email_templates (template_id, tenant_id, name, subject, body, is_default, created_at, updated_at)
        VALUES 
        (
            '00000000-0000-0000-0000-000000000001',
            NULL,
            'Professional',
            'Congratulations on {{product_name}} launch',
            $$Hi {{recipient_name}},

I noticed {{company_name}}'s recent announcement about {{product_name}}.

{{post_summary}}

Would you be open to a brief call to explore potential synergies?

Best regards,
{{sender_name}}$$,
            true,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ),
        (
            '00000000-0000-0000-0000-000000000002',
            NULL,
            'Friendly',
            'Exciting launch! 🚀',
            $$Hey {{recipient_name}},

Just saw your post about {{product_name}} - looks amazing!

{{post_summary}}

Any chance you're free for a quick chat this week?

Cheers,
{{sender_name}}$$,
            true,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ),
        (
            '00000000-0000-0000-0000-000000000003',
            NULL,
            'Direct',
            '{{product_name}} partnership opportunity?',
            $${{recipient_name}},

{{company_name}}'s {{product_name}} caught my attention.

{{post_summary}}

15 minutes to discuss potential collaboration?

{{sender_name}}$$,
            true,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
    """)


def downgrade():
    op.drop_table('email_templates')

