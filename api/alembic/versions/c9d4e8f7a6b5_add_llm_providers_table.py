"""add_llm_providers_table

Revision ID: c9d4e8f7a6b5
Revises: b8f5c9a3d2e1
Create Date: 2025-01-05 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9d4e8f7a6b5'
down_revision = 'b8f5c9a3d2e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create llm_providers table
    op.create_table('llm_providers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('provider_type', sa.String(), nullable=False),
        sa.Column('encrypted_api_key', sa.Text(), nullable=True),
        sa.Column('base_url', sa.String(), nullable=True),
        sa.Column('default_model_name', sa.String(), nullable=False),
        sa.Column('default_temperature', sa.Float(), nullable=False),
        sa.Column('default_max_tokens', sa.Integer(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop the table if we need to rollback
    op.drop_table('llm_providers')