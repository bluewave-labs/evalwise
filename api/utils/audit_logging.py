"""
Security audit logging utilities
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from config import settings
from database import get_db

# Separate logger for audit events
audit_logger = logging.getLogger("security_audit")

# If we want to store audit logs in database
AuditBase = declarative_base()

class AuditEventType(Enum):
    """Types of security events to audit"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_BLOCKED = "login_blocked"  # Due to rate limiting
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REFRESH_FAILED = "token_refresh_failed"
    
    # Password events  
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    PASSWORD_RESET_FAILED = "password_reset_failed"
    
    # Authorization events
    ACCESS_DENIED = "access_denied"
    PERMISSION_ESCALATION = "permission_escalation"
    ADMIN_ACTION = "admin_action"
    
    # Data access events
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    BULK_DATA_EXPORT = "bulk_data_export"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    FILE_UPLOAD = "file_upload"
    FILE_UPLOAD_REJECTED = "file_upload_rejected"
    
    # System events
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGED = "configuration_changed"


class AuditLog(AuditBase):
    """Database model for audit logs"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type = Column(String(50), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    username = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    resource = Column(String(255), nullable=True)
    action = Column(String(100), nullable=True)
    outcome = Column(String(20), nullable=False)  # success, failure, blocked
    details = Column(Text, nullable=True)  # JSON string
    risk_score = Column(Integer, default=0)  # 0-100 risk scoring
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)


class SecurityAuditor:
    """Central security audit logging system"""
    
    def __init__(self):
        self.logger = audit_logger
        
    def log_event(
        self,
        event_type: AuditEventType,
        outcome: str = "success",  # success, failure, blocked
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        risk_score: int = 0,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log a security audit event"""
        
        # Create audit record
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "outcome": outcome,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "resource": resource,
            "action": action,
            "details": json.dumps(details) if details else None,
            "risk_score": risk_score,
            "session_id": session_id,
            "request_id": request_id
        }
        
        # Log to structured logger
        self.logger.info(
            f"AUDIT: {event_type.value} - {outcome}",
            extra={
                "audit_event": True,
                **{k: v for k, v in audit_record.items() if v is not None}
            }
        )
        
        # Store in database if configured
        if settings.environment == "production":
            try:
                self._store_in_database(audit_record)
            except Exception as e:
                # Don't let audit logging break the main application
                self.logger.error(f"Failed to store audit log in database: {str(e)}")
    
    def _store_in_database(self, audit_record: Dict[str, Any]) -> None:
        """Store audit log in database"""
        try:
            # This would require setting up a separate database connection
            # or using the main database with proper transaction handling
            pass  # Placeholder for database storage
        except Exception as e:
            self.logger.error(f"Database audit log storage failed: {str(e)}")
    
    # Convenience methods for common events
    def log_login_success(self, user_id: str, username: str, ip_address: str, 
                         user_agent: str, session_id: str, request_id: str):
        self.log_event(
            AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id
        )
    
    def log_login_failed(self, username: str, ip_address: str, user_agent: str, 
                        reason: str, request_id: str, risk_score: int = 30):
        self.log_event(
            AuditEventType.LOGIN_FAILED,
            outcome="failure",
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"failure_reason": reason},
            risk_score=risk_score,
            request_id=request_id
        )
    
    def log_login_blocked(self, username: str, ip_address: str, reason: str, request_id: str):
        self.log_event(
            AuditEventType.LOGIN_BLOCKED,
            outcome="blocked",
            username=username,
            ip_address=ip_address,
            details={"block_reason": reason},
            risk_score=50,
            request_id=request_id
        )
    
    def log_access_denied(self, user_id: str, username: str, resource: str, 
                         action: str, ip_address: str, request_id: str):
        self.log_event(
            AuditEventType.ACCESS_DENIED,
            outcome="blocked",
            user_id=user_id,
            username=username,
            resource=resource,
            action=action,
            ip_address=ip_address,
            risk_score=40,
            request_id=request_id
        )
    
    def log_admin_action(self, user_id: str, username: str, action: str, 
                        resource: str, details: Dict[str, Any], ip_address: str, request_id: str):
        self.log_event(
            AuditEventType.ADMIN_ACTION,
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            risk_score=20,  # Admin actions are expected but need tracking
            request_id=request_id
        )
    
    def log_data_access(self, user_id: str, username: str, resource: str, 
                       record_count: int, ip_address: str, request_id: str):
        risk_score = min(10 + (record_count // 100), 30)  # Higher risk for bulk access
        self.log_event(
            AuditEventType.SENSITIVE_DATA_ACCESS,
            user_id=user_id,
            username=username,
            resource=resource,
            details={"record_count": record_count},
            ip_address=ip_address,
            risk_score=risk_score,
            request_id=request_id
        )
    
    def log_file_upload(self, user_id: str, username: str, filename: str, 
                       file_size: int, ip_address: str, request_id: str, success: bool = True):
        event_type = AuditEventType.FILE_UPLOAD if success else AuditEventType.FILE_UPLOAD_REJECTED
        outcome = "success" if success else "blocked"
        self.log_event(
            event_type,
            outcome=outcome,
            user_id=user_id,
            username=username,
            resource="file_upload",
            details={"filename": filename, "size_bytes": file_size},
            ip_address=ip_address,
            risk_score=15 if success else 25,
            request_id=request_id
        )
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str, request_id: str):
        self.log_event(
            AuditEventType.RATE_LIMIT_EXCEEDED,
            outcome="blocked",
            resource=endpoint,
            ip_address=ip_address,
            risk_score=35,
            request_id=request_id
        )
    
    def log_suspicious_activity(self, user_id: str, username: str, activity: str, 
                               details: Dict[str, Any], ip_address: str, request_id: str):
        self.log_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            outcome="detected",
            user_id=user_id,
            username=username,
            action=activity,
            details=details,
            ip_address=ip_address,
            risk_score=70,
            request_id=request_id
        )


# Global auditor instance
security_auditor = SecurityAuditor()


def get_client_ip(request) -> str:
    """Extract client IP address from request"""
    forwarded_for = getattr(request, 'headers', {}).get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    client = getattr(request, 'client', None)
    if client and hasattr(client, 'host'):
        return client.host
    
    return "unknown"


def get_user_agent(request) -> str:
    """Extract user agent from request"""
    return getattr(request, 'headers', {}).get("User-Agent", "unknown")


def get_request_id(request) -> str:
    """Extract request ID from request state"""
    return getattr(getattr(request, 'state', {}), 'request_id', str(uuid.uuid4()))