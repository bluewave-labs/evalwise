"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-08-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dataset table
    op.create_table('dataset',
    sa.Column('id', UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('version_hash', sa.String(), nullable=False),
    sa.Column('tags', ARRAY(sa.String()), nullable=True),
    sa.Column('schema_json', sa.JSON(), nullable=True),
    sa.Column('is_synthetic', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # Create scenario table
    op.create_table('scenario',
    sa.Column('id', UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('params_json', sa.JSON(), nullable=True),
    sa.Column('tags', ARRAY(sa.String()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # Create evaluator table
    op.create_table('evaluator',
    sa.Column('id', UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('kind', sa.String(), nullable=False),
    sa.Column('config_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # Create item table
    op.create_table('item',
    sa.Column('id', UUID(as_uuid=True), nullable=False),
    sa.Column('dataset_id', UUID(as_uuid=True), nullable=False),
    sa.Column('input_json', sa.JSON(), nullable=False),
    sa.Column('expected_json', sa.JSON(), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create run table
    op.create_table('run',
    sa.Column('id', UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('dataset_id', UUID(as_uuid=True), nullable=False),
    sa.Column('dataset_version_hash', sa.String(), nullable=False),
    sa.Column('scenario_ids', ARRAY(UUID()), nullable=True),
    sa.Column('model_provider', sa.String(), nullable=False),
    sa.Column('model_name', sa.String(), nullable=False),
    sa.Column('model_params_json', sa.JSON(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('owner', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['dataset_id'], ['dataset.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create result table
    op.create_table('result',
    sa.Column('id', UUID(as_uuid=True), nullable=False),
    sa.Column('run_id', UUID(as_uuid=True), nullable=False),
    sa.Column('item_id', UUID(as_uuid=True), nullable=False),
    sa.Column('scenario_id', UUID(as_uuid=True), nullable=False),
    sa.Column('output_json', sa.JSON(), nullable=True),
    sa.Column('latency_ms', sa.Integer(), nullable=True),
    sa.Column('token_input', sa.Integer(), nullable=True),
    sa.Column('token_output', sa.Integer(), nullable=True),
    sa.Column('cost_usd', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], ),
    sa.ForeignKeyConstraint(['scenario_id'], ['scenario.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create evaluation table
    op.create_table('evaluation',
    sa.Column('id', UUID(as_uuid=True), nullable=False),
    sa.Column('result_id', UUID(as_uuid=True), nullable=False),
    sa.Column('evaluator_id', UUID(as_uuid=True), nullable=False),
    sa.Column('score_float', sa.Float(), nullable=True),
    sa.Column('pass_bool', sa.Boolean(), nullable=True),
    sa.Column('notes_text', sa.Text(), nullable=True),
    sa.Column('raw_json', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['evaluator_id'], ['evaluator.id'], ),
    sa.ForeignKeyConstraint(['result_id'], ['result.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_run_status', 'run', ['status'])
    op.create_index('idx_result_run_id', 'result', ['run_id'])
    op.create_index('idx_created_at_retention', 'result', ['created_at'])
    op.create_index('idx_dataset_tags', 'dataset', ['tags'], postgresql_using='gin')
    op.create_index('idx_scenario_tags', 'scenario', ['tags'], postgresql_using='gin')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_scenario_tags', table_name='scenario')
    op.drop_index('idx_dataset_tags', table_name='dataset')
    op.drop_index('idx_created_at_retention', table_name='result')
    op.drop_index('idx_result_run_id', table_name='result')
    op.drop_index('idx_run_status', table_name='run')

    # Drop tables
    op.drop_table('evaluation')
    op.drop_table('result')
    op.drop_table('run')
    op.drop_table('item')
    op.drop_table('evaluator')
    op.drop_table('scenario')
    op.drop_table('dataset')