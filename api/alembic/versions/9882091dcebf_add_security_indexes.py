"""add_security_indexes

Revision ID: 9882091dcebf
Revises: 937aee5d512a
Create Date: 2025-08-29 08:42:09.051301

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9882091dcebf'
down_revision = '937aee5d512a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Helper function to check if index exists
    def index_exists(index_name, table_name):
        result = conn.execute(
            sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :index_name AND tablename = :table_name"),
            {"index_name": index_name, "table_name": table_name}
        )
        return result.fetchone() is not None
    
    # Add indexes for authentication queries
    if not index_exists('ix_users_email', 'users'):
        op.create_index('ix_users_email', 'users', ['email'])
    if not index_exists('ix_users_username', 'users'):
        op.create_index('ix_users_username', 'users', ['username'])
    if not index_exists('ix_users_refresh_token_hash', 'users'):
        op.create_index('ix_users_refresh_token_hash', 'users', ['refresh_token_hash'])
    if not index_exists('ix_users_api_key_hash', 'users'):
        op.create_index('ix_users_api_key_hash', 'users', ['api_key_hash'])
    
    # Add indexes for login attempts (rate limiting)
    if not index_exists('ix_login_attempts_username_email', 'login_attempts'):
        op.create_index('ix_login_attempts_username_email', 'login_attempts', ['username_or_email'])
    if not index_exists('ix_login_attempts_ip_created', 'login_attempts'):
        op.create_index('ix_login_attempts_ip_created', 'login_attempts', ['ip_address', 'created_at'])
    if not index_exists('ix_login_attempts_created_at', 'login_attempts'):
        op.create_index('ix_login_attempts_created_at', 'login_attempts', ['created_at'])
    
    # Add indexes for user sessions
    if not index_exists('ix_user_sessions_user_id', 'user_sessions'):
        op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    if not index_exists('ix_user_sessions_token_hash', 'user_sessions'):
        op.create_index('ix_user_sessions_token_hash', 'user_sessions', ['session_token_hash'])
    if not index_exists('ix_user_sessions_expires_active', 'user_sessions'):
        op.create_index('ix_user_sessions_expires_active', 'user_sessions', ['expires_at', 'is_active'])
    if not index_exists('ix_user_sessions_last_accessed', 'user_sessions'):
        op.create_index('ix_user_sessions_last_accessed', 'user_sessions', ['last_accessed'])
    
    # Add indexes for audit logs
    if not index_exists('ix_audit_logs_user_id', 'audit_logs'):
        op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    if not index_exists('ix_audit_logs_action', 'audit_logs'):
        op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    if not index_exists('ix_audit_logs_created_at', 'audit_logs'):
        op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    if not index_exists('ix_audit_logs_ip_address', 'audit_logs'):
        op.create_index('ix_audit_logs_ip_address', 'audit_logs', ['ip_address'])
    
    # Add indexes for organizations
    if not index_exists('ix_user_organizations_user_id', 'user_organizations'):
        op.create_index('ix_user_organizations_user_id', 'user_organizations', ['user_id'])
    if not index_exists('ix_user_organizations_org_id', 'user_organizations'):
        op.create_index('ix_user_organizations_org_id', 'user_organizations', ['organization_id'])
    if not index_exists('ix_user_organizations_role_active', 'user_organizations'):
        op.create_index('ix_user_organizations_role_active', 'user_organizations', ['role', 'is_active'])


def downgrade() -> None:
    # Remove indexes in reverse order
    op.drop_index('ix_user_organizations_role_active')
    op.drop_index('ix_user_organizations_org_id')
    op.drop_index('ix_user_organizations_user_id')
    
    op.drop_index('ix_audit_logs_ip_address')
    op.drop_index('ix_audit_logs_created_at')
    op.drop_index('ix_audit_logs_action')
    op.drop_index('ix_audit_logs_user_id')
    
    op.drop_index('ix_user_sessions_last_accessed')
    op.drop_index('ix_user_sessions_expires_active')
    op.drop_index('ix_user_sessions_token_hash')
    op.drop_index('ix_user_sessions_user_id')
    
    op.drop_index('ix_login_attempts_created_at')
    op.drop_index('ix_login_attempts_ip_created')
    op.drop_index('ix_login_attempts_username_email')
    
    op.drop_index('ix_users_api_key_hash')
    op.drop_index('ix_users_refresh_token_hash')
    op.drop_index('ix_users_username')
    op.drop_index('ix_users_email')