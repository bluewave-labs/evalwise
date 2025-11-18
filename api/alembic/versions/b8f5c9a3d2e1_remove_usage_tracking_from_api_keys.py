"""remove_usage_tracking_from_api_keys

Revision ID: b8f5c9a3d2e1
Revises: 9b8d8990d1c0
Create Date: 2025-01-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8f5c9a3d2e1'
down_revision = '9b8d8990d1c0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove usage tracking columns from encrypted_api_keys table
    op.drop_column('encrypted_api_keys', 'last_used')
    op.drop_column('encrypted_api_keys', 'usage_count')


def downgrade() -> None:
    # Add the columns back if we need to rollback
    op.add_column('encrypted_api_keys', sa.Column('usage_count', sa.Integer(), nullable=True, default=0))
    op.add_column('encrypted_api_keys', sa.Column('last_used', sa.DateTime(), nullable=True))