from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import secrets
import hashlib
from config import settings
from database import get_db
from auth.models import User, Organization, UserOrganization
from utils.errors import AuthenticationError, AuthorizationError
from utils.logging import get_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scopes={
        "read": "Read access to resources",
        "write": "Write access to resources",
        "admin": "Administrative access"
    }
)

# HTTP Bearer scheme for API keys
bearer_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with proper claims"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    # Add standard JWT claims for better security
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "access",
        "jti": secrets.token_urlsafe(16)  # JWT ID for tracking/blacklisting
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(user_id: str, remember_me: bool = False) -> tuple[str, datetime]:
    """Create a refresh token and return it with expiration time"""
    if remember_me:
        expires_delta = timedelta(days=30)  # Extended for "remember me"
    else:
        expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    
    expire = datetime.utcnow() + expires_delta
    
    data = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)  # JWT ID for session tracking
    }
    
    encoded_jwt = jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt, expire

def verify_refresh_token(token: str) -> tuple[str, str]:
    """Verify refresh token and return user ID and JTI"""
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer
        )
        
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")
        
        if user_id is None or token_type != "refresh" or jti is None:
            raise AuthenticationError("Invalid refresh token")
        
        return user_id, jti
    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {str(e)}")
        raise AuthenticationError("Invalid refresh token")

def generate_reset_token() -> tuple[str, str]:
    """Generate password reset token and its hash"""
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash

def verify_reset_token(db: Session, token: str) -> Optional[User]:
    """Verify password reset token and return user if valid"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    user = db.query(User).filter(
        User.reset_token_hash == token_hash,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    return user

def clear_reset_token(db: Session, user: User):
    """Clear password reset token after use"""
    user.reset_token_hash = None
    user.reset_token_expires = None
    db.commit()

def create_password_reset_token(db: Session, user: User) -> str:
    """Create and store password reset token for user"""
    token, token_hash = generate_reset_token()
    
    # Token expires in 1 hour
    user.reset_token_hash = token_hash
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    return token

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token with proper claims validation"""
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer
        )
        
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "access":
            raise AuthenticationError("Invalid token")
        
        return {
            "username": username, 
            "scopes": payload.get("scopes", []),
            "jti": payload.get("jti"),
            "iat": payload.get("iat")
        }
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise AuthenticationError("Invalid token")

def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash"""
    # Generate a secure random API key
    api_key = f"ew_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(32))}"
    
    # Hash the API key for storage
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    return api_key, api_key_hash

def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash"""
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key_hash == stored_hash

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user with username/email and password"""
    # Try to find user by username or email
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def get_user_by_token(db: Session, token: str) -> User:
    """Get user from JWT token"""
    token_data = verify_token(token)
    
    user = db.query(User).filter(User.username == token_data["username"]).first()
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("Inactive user")
    
    return user

def get_user_by_api_key(db: Session, api_key: str) -> User:
    """Get user from API key"""
    if not api_key.startswith("ew_"):
        raise AuthenticationError("Invalid API key format")
    
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    user = db.query(User).filter(User.api_key_hash == api_key_hash).first()
    if not user:
        raise AuthenticationError("Invalid API key")
    
    if not user.is_active:
        raise AuthenticationError("Inactive user")
    
    return user

# Dependency for getting current user from JWT token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    return get_user_by_token(db, token)

# Dependency for getting current user from API key or JWT token
async def get_current_user_flexible(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from API key or JWT token"""
    if not credentials:
        raise AuthenticationError("Authentication required")
    
    token = credentials.credentials
    
    # Try API key first (if it starts with our prefix)
    if token.startswith("ew_"):
        return get_user_by_api_key(db, token)
    else:
        # Try JWT token
        return get_user_by_token(db, token)

# Dependency for requiring admin privileges
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and require admin privileges"""
    if not current_user.is_superuser:
        raise AuthorizationError("Admin privileges required")
    return current_user

# Dependency for requiring active user
async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and require active status"""
    if not current_user.is_active:
        raise AuthenticationError("Inactive user")
    return current_user

def get_user_organizations(db: Session, user: User) -> list[dict]:
    """Get all organizations for a user with their roles"""
    user_orgs = db.query(UserOrganization).filter(
        UserOrganization.user_id == user.id,
        UserOrganization.is_active == True
    ).all()
    
    organizations = []
    for user_org in user_orgs:
        org = db.query(Organization).filter(Organization.id == user_org.organization_id).first()
        if org and org.is_active:
            organizations.append({
                "id": str(org.id),
                "name": org.name,
                "description": org.description,
                "role": user_org.role,
                "joined_at": user_org.created_at
            })
    
    return organizations

def has_org_permission(db: Session, user: User, org_id: str, required_role: str = "member") -> bool:
    """Check if user has required role in organization"""
    role_hierarchy = {"viewer": 1, "member": 2, "admin": 3}
    required_level = role_hierarchy.get(required_role, 0)
    
    user_org = db.query(UserOrganization).filter(
        UserOrganization.user_id == user.id,
        UserOrganization.organization_id == org_id,
        UserOrganization.is_active == True
    ).first()
    
    if not user_org:
        return False
    
    user_level = role_hierarchy.get(user_org.role, 0)
    return user_level >= required_level

# Organization role dependency
async def require_org_admin(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Require admin role in specified organization"""
    if not has_org_permission(db, current_user, org_id, "admin"):
        raise AuthorizationError("Organization admin privileges required")
    return current_user

async def require_org_member(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Require member role in specified organization"""
    if not has_org_permission(db, current_user, org_id, "member"):
        raise AuthorizationError("Organization membership required")
    return current_user

# Rate limiting and session management
def check_login_rate_limit(db: Session, username_or_email: str, ip_address: str) -> bool:
    """Check if login attempts exceed rate limit"""
    from auth.models import LoginAttempt
    
    # Check attempts in the last window
    window_start = datetime.utcnow() - timedelta(minutes=settings.login_attempt_window_minutes)
    
    failed_attempts = db.query(LoginAttempt).filter(
        LoginAttempt.username_or_email == username_or_email,
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.success == False,
        LoginAttempt.created_at >= window_start
    ).count()
    
    return failed_attempts < settings.max_login_attempts

def log_login_attempt(db: Session, username_or_email: str, ip_address: str, 
                     user_agent: str, success: bool):
    """Log login attempt for rate limiting"""
    from auth.models import LoginAttempt
    
    attempt = LoginAttempt(
        username_or_email=username_or_email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success
    )
    db.add(attempt)
    db.commit()

def create_user_session(db: Session, user: User, refresh_token: str, 
                       ip_address: str, user_agent: str, expires_at: datetime) -> str:
    """Create a new user session and manage concurrent sessions"""
    from auth.models import UserSession
    
    # Check concurrent session limit
    active_sessions = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).count()
    
    if active_sessions >= settings.max_concurrent_sessions:
        # Deactivate oldest session
        oldest_session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).order_by(UserSession.last_accessed).first()
        
        if oldest_session:
            oldest_session.is_active = False
            db.commit()
    
    # Create new session
    session_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    session = UserSession(
        user_id=user.id,
        session_token_hash=session_token_hash,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return str(session.id)

def invalidate_user_sessions(db: Session, user: User, exclude_session_id: str = None):
    """Invalidate all user sessions (e.g., on password change)"""
    from auth.models import UserSession
    
    query = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active == True
    )
    
    if exclude_session_id:
        query = query.filter(UserSession.id != exclude_session_id)
    
    sessions = query.all()
    for session in sessions:
        session.is_active = False
    
    db.commit()

def log_security_event(db: Session, user_id: str, action: str, ip_address: str,
                      user_agent: str, success: bool, details: str = None):
    """Log security-related events for audit"""
    from auth.models import AuditLog
    
    audit = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        details=details
    )
    db.add(audit)
    db.commit()

def get_client_info(request: Request) -> tuple[str, str]:
    """Extract client IP and user agent from request"""
    # Handle proxy headers for real IP
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
        request.headers.get("X-Real-IP", "") or
        request.client.host
    )
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    return client_ip, user_agent