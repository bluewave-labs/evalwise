from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base

class Organization(Base):
    """Organization model for multi-tenant support"""
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Settings
    max_users = Column(Integer, default=10)
    max_datasets = Column(Integer, default=50)
    max_runs_per_month = Column(Integer, default=1000)
    
    # Relationships
    user_organizations = relationship("UserOrganization", back_populates="organization")
    encrypted_api_keys = relationship("EncryptedApiKey", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization(name='{self.name}')>"


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Session management
    refresh_token_hash = Column(String, nullable=True)
    refresh_token_expires = Column(DateTime, nullable=True)
    
    # Password reset
    reset_token_hash = Column(String, nullable=True) 
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Additional fields for API usage tracking
    api_key_hash = Column(String, nullable=True)  # For API key authentication
    rate_limit_tier = Column(String, default="basic")  # basic, premium, enterprise
    
    # Relationships
    user_organizations = relationship("UserOrganization", back_populates="user")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class UserOrganization(Base):
    """Many-to-many relationship between users and organizations with roles"""
    __tablename__ = "user_organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    role = Column(String, nullable=False, default="member")  # admin, member, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_organizations")
    organization = relationship("Organization", back_populates="user_organizations")
    
    def __repr__(self):
        return f"<UserOrganization(user_id='{self.user_id}', org_id='{self.organization_id}', role='{self.role}')>"


class EncryptedApiKey(Base):
    """Encrypted storage for user's LLM provider API keys"""
    __tablename__ = "encrypted_api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    provider = Column(String, nullable=False)  # openai, anthropic, huggingface, etc.
    encrypted_key = Column(Text, nullable=False)  # AES encrypted API key
    key_name = Column(String, nullable=False)  # User-friendly name for the key
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Usage tracking
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    organization = relationship("Organization", back_populates="encrypted_api_keys")
    
    def __repr__(self):
        return f"<EncryptedApiKey(provider='{self.provider}', name='{self.key_name}')>"


class LoginAttempt(Base):
    """Track failed login attempts for rate limiting"""
    __tablename__ = "login_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username_or_email = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"<LoginAttempt({self.username_or_email}: {status})>"


class UserSession(Base):
    """Track active user sessions"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token_hash = Column(String, nullable=False)  # Hash of refresh token
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', active={self.is_active})>"


class AuditLog(Base):
    """Security audit log for sensitive operations"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # login, logout, password_change, etc.
    resource_type = Column(String, nullable=True)  # user, organization, etc.
    resource_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON details
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', success={self.success})>"