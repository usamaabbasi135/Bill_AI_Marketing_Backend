"""Fix jobs table columns

Revision ID: b13bbce8fbd
Revises: 9a8b7c6d5e4f
Create Date: 2025-01-27 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'b13bbce8fbd'
down_revision = '9a8b7c6d5e4f'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to jobs table if they don't exist."""
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'jobs' not in inspector.get_table_names():
        # Table doesn't exist, skip
        return
    
    existing_cols = [col['name'] for col in inspector.get_columns('jobs')]
    
    # Add missing new columns if they don't exist
    if 'job_type' not in existing_cols:
        op.add_column('jobs', sa.Column('job_type', sa.String(length=50), nullable=True))
    
    if 'total_items' not in existing_cols:
        op.add_column('jobs', sa.Column('total_items', sa.Integer(), nullable=True, server_default='0'))
    
    if 'completed_items' not in existing_cols:
        op.add_column('jobs', sa.Column('completed_items', sa.Integer(), nullable=True, server_default='0'))
    
    if 'success_count' not in existing_cols:
        op.add_column('jobs', sa.Column('success_count', sa.Integer(), nullable=True, server_default='0'))
    
    if 'failed_count' not in existing_cols:
        op.add_column('jobs', sa.Column('failed_count', sa.Integer(), nullable=True, server_default='0'))
    
    if 'result_data' not in existing_cols:
        op.add_column('jobs', sa.Column('result_data', sa.Text(), nullable=True))
    
    if 'error_message' not in existing_cols:
        op.add_column('jobs', sa.Column('error_message', sa.Text(), nullable=True))
    
    if 'completed_at' not in existing_cols:
        op.add_column('jobs', sa.Column('completed_at', sa.DateTime(), nullable=True))
    
    # Ensure legacy fields exist (for backward compatibility)
    if 'task_name' not in existing_cols:
        op.add_column('jobs', sa.Column('task_name', sa.String(length=255), nullable=True))
    
    if 'result' not in existing_cols:
        op.add_column('jobs', sa.Column('result', sa.JSON(), nullable=True))
    
    if 'error' not in existing_cols:
        op.add_column('jobs', sa.Column('error', sa.Text(), nullable=True))
    
    # Ensure status has a default value if it exists
    if 'status' in existing_cols:
        try:
            # Try to set server default if not already set
            op.alter_column('jobs', 'status', server_default='pending')
        except Exception:
            # Server default might already be set or not supported, ignore
            pass


def downgrade():
    """Remove the columns that were added (optional - for rollback)."""
    # Note: This is optional - you may want to keep these columns
    # Uncomment if you need to rollback
    # op.drop_column('jobs', 'job_type')
    # op.drop_column('jobs', 'total_items')
    # op.drop_column('jobs', 'completed_items')
    # op.drop_column('jobs', 'success_count')
    # op.drop_column('jobs', 'failed_count')
    # op.drop_column('jobs', 'result_data')
    # op.drop_column('jobs', 'error_message')
    # op.drop_column('jobs', 'completed_at')
    pass

