"""Add new profile fields from dev_fusion actor

Revision ID: abc123def456
Revises: 9a8b7c6d5e4f
Create Date: 2025-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = '9a8b7c6d5e4f'
branch_labels = None
depends_on = None


def upgrade():
    # Check existing columns to avoid errors
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_cols = [col['name'] for col in inspector.get_columns('profiles')]
    
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        if 'first_name' not in existing_cols:
            batch_op.add_column(sa.Column('first_name', sa.String(length=255), nullable=True))
        if 'last_name' not in existing_cols:
            batch_op.add_column(sa.Column('last_name', sa.String(length=255), nullable=True))
        if 'full_name' not in existing_cols:
            batch_op.add_column(sa.Column('full_name', sa.String(length=255), nullable=True))
        if 'connections' not in existing_cols:
            batch_op.add_column(sa.Column('connections', sa.Integer(), nullable=True))
        if 'followers' not in existing_cols:
            batch_op.add_column(sa.Column('followers', sa.Integer(), nullable=True))
        if 'mobile_number' not in existing_cols:
            batch_op.add_column(sa.Column('mobile_number', sa.String(length=50), nullable=True))
        if 'job_started_on' not in existing_cols:
            batch_op.add_column(sa.Column('job_started_on', sa.String(length=50), nullable=True))
        if 'job_location' not in existing_cols:
            batch_op.add_column(sa.Column('job_location', sa.String(length=255), nullable=True))
        if 'job_still_working' not in existing_cols:
            batch_op.add_column(sa.Column('job_still_working', sa.Boolean(), nullable=True))
        if 'company_name' not in existing_cols:
            batch_op.add_column(sa.Column('company_name', sa.String(length=255), nullable=True))
        if 'company_industry' not in existing_cols:
            batch_op.add_column(sa.Column('company_industry', sa.String(length=255), nullable=True))
        if 'company_website' not in existing_cols:
            batch_op.add_column(sa.Column('company_website', sa.Text(), nullable=True))
        if 'company_linkedin' not in existing_cols:
            batch_op.add_column(sa.Column('company_linkedin', sa.Text(), nullable=True))
        if 'company_founded_in' not in existing_cols:
            batch_op.add_column(sa.Column('company_founded_in', sa.String(length=50), nullable=True))
        if 'company_size' not in existing_cols:
            batch_op.add_column(sa.Column('company_size', sa.String(length=100), nullable=True))
        if 'address_country_only' not in existing_cols:
            batch_op.add_column(sa.Column('address_country_only', sa.String(length=255), nullable=True))
        if 'address_with_country' not in existing_cols:
            batch_op.add_column(sa.Column('address_with_country', sa.String(length=255), nullable=True))
        if 'address_without_country' not in existing_cols:
            batch_op.add_column(sa.Column('address_without_country', sa.String(length=255), nullable=True))
        if 'profile_pic' not in existing_cols:
            batch_op.add_column(sa.Column('profile_pic', sa.Text(), nullable=True))
        if 'profile_pic_high_quality' not in existing_cols:
            batch_op.add_column(sa.Column('profile_pic_high_quality', sa.Text(), nullable=True))
        if 'background_pic' not in existing_cols:
            batch_op.add_column(sa.Column('background_pic', sa.Text(), nullable=True))
        if 'linkedin_id' not in existing_cols:
            batch_op.add_column(sa.Column('linkedin_id', sa.String(length=100), nullable=True))
        if 'public_identifier' not in existing_cols:
            batch_op.add_column(sa.Column('public_identifier', sa.String(length=255), nullable=True))
        if 'linkedin_public_url' not in existing_cols:
            batch_op.add_column(sa.Column('linkedin_public_url', sa.Text(), nullable=True))
        if 'urn' not in existing_cols:
            batch_op.add_column(sa.Column('urn', sa.String(length=255), nullable=True))
        if 'is_premium' not in existing_cols:
            batch_op.add_column(sa.Column('is_premium', sa.Boolean(), nullable=True))
        if 'is_verified' not in existing_cols:
            batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=True))
        if 'is_job_seeker' not in existing_cols:
            batch_op.add_column(sa.Column('is_job_seeker', sa.Boolean(), nullable=True))
        if 'is_retired' not in existing_cols:
            batch_op.add_column(sa.Column('is_retired', sa.Boolean(), nullable=True))
        if 'is_creator' not in existing_cols:
            batch_op.add_column(sa.Column('is_creator', sa.Boolean(), nullable=True))
        if 'is_influencer' not in existing_cols:
            batch_op.add_column(sa.Column('is_influencer', sa.Boolean(), nullable=True))
        if 'about' not in existing_cols:
            batch_op.add_column(sa.Column('about', sa.Text(), nullable=True))
        if 'experiences' not in existing_cols:
            batch_op.add_column(sa.Column('experiences', sa.Text(), nullable=True))
        if 'skills' not in existing_cols:
            batch_op.add_column(sa.Column('skills', sa.Text(), nullable=True))
        if 'educations' not in existing_cols:
            batch_op.add_column(sa.Column('educations', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.drop_column('educations')
        batch_op.drop_column('skills')
        batch_op.drop_column('experiences')
        batch_op.drop_column('about')
        batch_op.drop_column('is_influencer')
        batch_op.drop_column('is_creator')
        batch_op.drop_column('is_retired')
        batch_op.drop_column('is_job_seeker')
        batch_op.drop_column('is_verified')
        batch_op.drop_column('is_premium')
        batch_op.drop_column('urn')
        batch_op.drop_column('linkedin_public_url')
        batch_op.drop_column('public_identifier')
        batch_op.drop_column('linkedin_id')
        batch_op.drop_column('background_pic')
        batch_op.drop_column('profile_pic_high_quality')
        batch_op.drop_column('profile_pic')
        batch_op.drop_column('address_without_country')
        batch_op.drop_column('address_with_country')
        batch_op.drop_column('address_country_only')
        batch_op.drop_column('company_size')
        batch_op.drop_column('company_founded_in')
        batch_op.drop_column('company_linkedin')
        batch_op.drop_column('company_website')
        batch_op.drop_column('company_industry')
        batch_op.drop_column('company_name')
        batch_op.drop_column('job_still_working')
        batch_op.drop_column('job_location')
        batch_op.drop_column('job_started_on')
        batch_op.drop_column('mobile_number')
        batch_op.drop_column('followers')
        batch_op.drop_column('connections')
        batch_op.drop_column('full_name')
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')

