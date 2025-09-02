"""
Session management utilities with concurrent session limits
"""
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from auth.models import User
from config import settings
import logging

logger = logging.getLogger(__name__)

SessionBase = declarative_base()

class UserSession(SessionBase):
    """Database model for user sessions"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False)
    refresh_token_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(255), nullable=True)


class SessionManager:
    """Manages user sessions with concurrent limits and security"""
    
    def __init__(self, max_sessions_per_user: int = None):
        self.max_sessions = max_sessions_per_user or settings.max_concurrent_sessions
        
    def create_session(
        self, 
        db: Session, 
        user: User, 
        refresh_token: str,
        ip_address: str = None,
        user_agent: str = None,
        expires_at: datetime = None
    ) -> str:
        """
        Create a new user session with concurrent session management
        Returns session_id
        """
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Hash the refresh token for storage
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        # Set expiration if not provided
        if not expires_at:
            expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Check existing active sessions
        active_sessions = self.get_active_sessions(db, user.id)
        
        # If at session limit, revoke oldest session
        if len(active_sessions) >= self.max_sessions:
            oldest_sessions = sorted(active_sessions, key=lambda x: x.last_accessed)[
                :len(active_sessions) - self.max_sessions + 1
            ]
            
            for old_session in oldest_sessions:
                self.revoke_session(
                    db, 
                    old_session.session_id, 
                    "Session limit exceeded - oldest session revoked"
                )
                logger.info(f"Revoked session {old_session.session_id} for user {user.username} due to session limit")
        
        # Create new session
        new_session = UserSession(
            user_id=user.id,
            session_id=session_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(new_session)
        db.commit()
        
        logger.info(f"Created session {session_id} for user {user.username}")
        
        return session_id
    
    def get_active_sessions(self, db: Session, user_id: uuid.UUID) -> List[UserSession]:
        """Get all active sessions for a user"""
        return db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).all()
    
    def validate_session(
        self, 
        db: Session, 
        session_id: str, 
        refresh_token: str = None
    ) -> Optional[UserSession]:
        """
        Validate a session and optionally check refresh token
        Updates last_accessed timestamp
        """
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            return None
        
        # Validate refresh token if provided
        if refresh_token:
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            if session.refresh_token_hash != token_hash:
                logger.warning(f"Invalid refresh token for session {session_id}")
                return None
        
        # Update last accessed
        session.last_accessed = datetime.utcnow()
        db.commit()
        
        return session
    
    def revoke_session(
        self, 
        db: Session, 
        session_id: str, 
        reason: str = "Manual revocation"
    ) -> bool:
        """Revoke a specific session"""
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return False
        
        session.is_active = False
        session.revoked_at = datetime.utcnow()
        session.revoked_reason = reason
        db.commit()
        
        logger.info(f"Revoked session {session_id}, reason: {reason}")
        return True
    
    def revoke_all_user_sessions(
        self, 
        db: Session, 
        user_id: uuid.UUID, 
        except_session_id: str = None,
        reason: str = "All sessions revoked"
    ) -> int:
        """Revoke all sessions for a user, optionally except one"""
        query = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )
        
        if except_session_id:
            query = query.filter(UserSession.session_id != except_session_id)
        
        sessions = query.all()
        count = 0
        
        for session in sessions:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = reason
            count += 1
        
        db.commit()
        
        logger.info(f"Revoked {count} sessions for user {user_id}, reason: {reason}")
        return count
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """Remove expired sessions from database"""
        cutoff_date = datetime.utcnow()
        
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at < cutoff_date
        ).all()
        
        count = len(expired_sessions)
        
        for session in expired_sessions:
            if session.is_active:
                session.is_active = False
                session.revoked_at = datetime.utcnow()
                session.revoked_reason = "Expired"
        
        db.commit()
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")
        
        return count
    
    def get_session_info(self, db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get session information for a user (for admin/user management)"""
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).order_by(UserSession.last_accessed.desc()).all()
        
        session_info = []
        for session in sessions:
            session_info.append({
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "is_active": session.is_active,
                "revoked_at": session.revoked_at.isoformat() if session.revoked_at else None,
                "revoked_reason": session.revoked_reason
            })
        
        return session_info
    
    def detect_suspicious_sessions(self, db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Detect potentially suspicious sessions (different IPs, user agents, etc.)"""
        sessions = self.get_active_sessions(db, user_id)
        
        if len(sessions) <= 1:
            return []
        
        suspicious = []
        
        # Group by IP address
        ip_groups = {}
        for session in sessions:
            ip = session.ip_address or "unknown"
            if ip not in ip_groups:
                ip_groups[ip] = []
            ip_groups[ip].append(session)
        
        # Flag sessions from different IPs as potentially suspicious
        if len(ip_groups) > 1:
            for ip, ip_sessions in ip_groups.items():
                if len(ip_sessions) < len(sessions) // 2:  # Minority IP addresses
                    for session in ip_sessions:
                        suspicious.append({
                            "session_id": session.session_id,
                            "reason": "Different IP address",
                            "ip_address": session.ip_address,
                            "last_accessed": session.last_accessed.isoformat()
                        })
        
        # Check for rapid session creation
        recent_sessions = [s for s in sessions if 
                          (datetime.utcnow() - s.created_at).total_seconds() < 3600]  # Last hour
        
        if len(recent_sessions) >= 3:
            suspicious.extend([
                {
                    "session_id": s.session_id,
                    "reason": "Rapid session creation",
                    "created_at": s.created_at.isoformat()
                } for s in recent_sessions[-2:]  # Flag the most recent ones
            ])
        
        return suspicious


# Global session manager instance
session_manager = SessionManager()