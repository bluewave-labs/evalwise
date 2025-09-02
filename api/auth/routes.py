from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
import uuid
import hashlib

from database import get_db
from auth.models import User, Organization, UserOrganization
from auth.schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse, 
    PasswordResetRequest, PasswordResetConfirm, PasswordChange, ApiKeyResponse
)
from auth.security import (
    get_password_hash, authenticate_user, create_access_token, create_refresh_token,
    verify_refresh_token, get_current_user, get_current_active_user, 
    get_current_user_flexible, generate_api_key, get_user_organizations, 
    create_password_reset_token, verify_reset_token, clear_reset_token,
    check_login_rate_limit, log_login_attempt, create_user_session, 
    invalidate_user_sessions, log_security_event, get_client_info
)
from utils.errors import (
    ValidationError, NotFoundError, ConflictError, 
    AuthenticationError, ErrorDetail
)
from utils.logging import get_logger, RequestContext
from utils.audit_logging import security_auditor, get_client_ip, get_user_agent, get_request_id
from config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
def register_user(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info(
        f"User registration attempt: {user_data.username}",
        extra={'request_id': request_id, 'username': user_data.username}
    )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise ConflictError(
                "Email already registered",
                details=[ErrorDetail(
                    code="EMAIL_EXISTS",
                    message="A user with this email already exists",
                    field="email"
                )],
                request_id=request_id
            )
        else:
            raise ConflictError(
                "Username already taken",
                details=[ErrorDetail(
                    code="USERNAME_EXISTS", 
                    message="A user with this username already exists",
                    field="username"
                )],
                request_id=request_id
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(
        f"User registered successfully: {db_user.username}",
        extra={'request_id': request_id, 'user_id': str(db_user.id)}
    )
    
    return UserResponse(
        id=str(db_user.id),
        email=db_user.email,
        username=db_user.username,
        full_name=db_user.full_name,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        created_at=db_user.created_at.isoformat(),
        last_login=db_user.last_login.isoformat() if db_user.last_login else None,
        rate_limit_tier=db_user.rate_limit_tier
    )

@router.post("/login", response_model=TokenResponse)
def login_user(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Authenticate user with security measures and return JWT token"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4())) if request else str(uuid.uuid4())
    client_ip, user_agent = get_client_info(request)
    
    # Rate limiting check
    if not check_login_rate_limit(db, username, client_ip):
        log_login_attempt(db, username, client_ip, user_agent, False)
        log_security_event(db, None, "login_rate_limit", client_ip, user_agent, False, 
                          f"Rate limit exceeded for {username}")
        # Audit log for rate limiting
        security_auditor.log_login_blocked(
            username=username,
            ip_address=client_ip,
            reason=f"Rate limit exceeded - too many attempts in {settings.login_attempt_window_minutes} minutes",
            request_id=request_id
        )
        raise AuthenticationError(
            f"Too many login attempts. Please try again in {settings.login_attempt_window_minutes} minutes.",
            request_id=request_id
        )
    
    logger.info(
        f"Login attempt: {username}",
        extra={'request_id': request_id, 'username': username, 'ip': client_ip}
    )
    
    user = authenticate_user(db, username, password)
    if not user:
        # Log failed attempt
        log_login_attempt(db, username, client_ip, user_agent, False)
        log_security_event(db, None, "login_failed", client_ip, user_agent, False, 
                          f"Invalid credentials for {username}")
        
        # Audit log for failed login
        security_auditor.log_login_failed(
            username=username,
            ip_address=client_ip,
            user_agent=user_agent,
            reason="Invalid credentials",
            request_id=request_id
        )
        
        logger.warning(
            f"Failed login attempt: {username}",
            extra={'request_id': request_id, 'username': username, 'ip': client_ip}
        )
        raise AuthenticationError(
            "Incorrect username or password",
            request_id=request_id
        )
    
    # Log successful attempt
    log_login_attempt(db, username, client_ip, user_agent, True)
    
    # Audit log for successful login
    security_auditor.log_login_success(
        user_id=str(user.id),
        username=username,
        ip_address=client_ip,
        user_agent=user_agent,
        session_id="",  # Will be updated after session creation
        request_id=request_id
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": ["read", "write"], "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token, refresh_expires = create_refresh_token(str(user.id), remember_me)
    
    # Create user session and manage concurrent sessions
    session_id = create_user_session(db, user, refresh_token, client_ip, user_agent, refresh_expires)
    
    # Store refresh token hash in user record (for backward compatibility)
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    user.refresh_token_hash = refresh_token_hash
    user.refresh_token_expires = refresh_expires
    db.commit()
    
    # Set refresh token as httpOnly cookie with proper security
    cookie_max_age = (30 * 24 * 60 * 60) if remember_me else (7 * 24 * 60 * 60)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=cookie_max_age,
        httponly=True,
        secure=settings.should_use_secure_cookies,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain
    )
    
    # Log successful login
    log_security_event(db, str(user.id), "login_success", client_ip, user_agent, True, 
                      f"Session {session_id} created")
    
    logger.info(
        f"User logged in successfully: {user.username}",
        extra={'request_id': request_id, 'user_id': str(user.id), 'session_id': session_id}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get current user information with organizations"""
    organizations = get_user_organizations(db, current_user)
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
        rate_limit_tier=current_user.rate_limit_tier,
        organizations=organizations
    )

@router.post("/api-key", response_model=ApiKeyResponse)
def create_api_key(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current user"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info(
        f"API key creation requested: {current_user.username}",
        extra={'request_id': request_id, 'user_id': str(current_user.id)}
    )
    
    # Generate API key
    api_key, api_key_hash = generate_api_key()
    
    # Update user with new API key hash
    current_user.api_key_hash = api_key_hash
    db.commit()
    
    logger.info(
        f"API key created for user: {current_user.username}",
        extra={'request_id': request_id, 'user_id': str(current_user.id)}
    )
    
    return ApiKeyResponse(
        api_key=api_key,
        key_id=str(current_user.id),
        created_at=current_user.updated_at.isoformat(),
        expires_at=None  # API keys don't expire by default
    )

@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info(
        f"Password change requested: {current_user.username}",
        extra={'request_id': request_id, 'user_id': str(current_user.id)}
    )
    
    # Verify current password
    from auth.security import verify_password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise AuthenticationError(
            "Current password is incorrect",
            request_id=request_id
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    logger.info(
        f"Password changed successfully: {current_user.username}",
        extra={'request_id': request_id, 'user_id': str(current_user.id)}
    )
    
    return {"message": "Password changed successfully"}

@router.post("/logout")
def logout_user(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user and clear refresh token"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Clear refresh token from database
    current_user.refresh_token_hash = None
    current_user.refresh_token_expires = None
    db.commit()
    
    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    
    logger.info(
        f"User logged out: {current_user.username}",
        extra={'request_id': request_id, 'user_id': str(current_user.id)}
    )
    
    return {"message": "Logged out successfully"}

@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token from httpOnly cookie"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    client_ip, user_agent = get_client_info(request)
    
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        log_security_event(db, None, "refresh_no_token", client_ip, user_agent, False, 
                          "Refresh attempt without token")
        raise AuthenticationError("Refresh token not found", request_id=request_id)
    
    try:
        # Verify refresh token with enhanced validation
        user_id, jti = verify_refresh_token(refresh_token)
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            log_security_event(db, user_id, "refresh_invalid_user", client_ip, user_agent, False,
                              "User not found or inactive")
            raise AuthenticationError("User not found or inactive", request_id=request_id)
        
        # Verify session exists and is active
        from auth.models import UserSession
        session_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        active_session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.session_token_hash == session_token_hash,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not active_session:
            log_security_event(db, str(user.id), "refresh_invalid_session", client_ip, user_agent, False,
                              "Session not found or expired")
            raise AuthenticationError("Invalid session", request_id=request_id)
        
        # Update session last accessed
        active_session.last_accessed = datetime.utcnow()
        db.commit()
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username, "scopes": ["read", "write"], "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Log successful refresh
        log_security_event(db, str(user.id), "refresh_success", client_ip, user_agent, True,
                          f"Session {active_session.id} token refreshed")
        
        logger.info(
            f"Token refreshed for user: {user.username}",
            extra={'request_id': request_id, 'user_id': str(user.id), 'session_id': str(active_session.id)}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )
        
    except Exception as e:
        # Clear invalid refresh token cookie
        response.delete_cookie(
            key="refresh_token", 
            httponly=True, 
            samesite=settings.cookie_samesite,
            secure=settings.should_use_secure_cookies
        )
        
        # Log the failed refresh attempt
        log_security_event(db, None, "refresh_failed", client_ip, user_agent, False, str(e))
        
        logger.warning(f"Token refresh failed: {str(e)}", 
                      extra={'request_id': request_id, 'ip': client_ip})
        
        raise AuthenticationError("Invalid or expired refresh token", request_id=request_id)

@router.post("/password-reset/request")
def request_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request password reset - always returns success to prevent email enumeration"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    client_ip, user_agent = get_client_info(request)
    
    logger.info(
        f"Password reset requested for email: {reset_data.email}",
        extra={'request_id': request_id, 'ip': client_ip}
    )
    
    # Find user by email
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    if user and user.is_active:
        try:
            # Create reset token
            reset_token = create_password_reset_token(db, user)
            
            # Send email (import here to avoid circular imports)
            from utils.email import send_password_reset_email
            email_sent = send_password_reset_email(
                user.email, 
                user.full_name or user.username, 
                reset_token
            )
            
            # Log security event
            log_security_event(db, str(user.id), "password_reset_request", client_ip, user_agent, 
                              email_sent, f"Reset token generated and email sent: {email_sent}")
            
            logger.info(
                f"Password reset token created for user: {user.username}, email sent: {email_sent}",
                extra={'request_id': request_id, 'user_id': str(user.id)}
            )
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}", 
                        extra={'request_id': request_id, 'user_id': str(user.id)})
            
            # Still return success to prevent information leakage
            pass
    else:
        # Log attempt for non-existent or inactive user
        log_security_event(db, None, "password_reset_request", client_ip, user_agent, False,
                          f"Reset requested for non-existent/inactive email: {reset_data.email}")
    
    # Always return success to prevent email enumeration attacks
    return {"message": "If the email exists in our system, you will receive password reset instructions."}

@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token and set new password"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    client_ip, user_agent = get_client_info(request)
    
    logger.info(
        f"Password reset confirmation attempt",
        extra={'request_id': request_id, 'ip': client_ip}
    )
    
    # Verify reset token
    user = verify_reset_token(db, reset_data.token)
    if not user:
        log_security_event(db, None, "password_reset_invalid_token", client_ip, user_agent, False,
                          "Invalid or expired reset token used")
        raise AuthenticationError("Invalid or expired reset token", request_id=request_id)
    
    if not user.is_active:
        log_security_event(db, str(user.id), "password_reset_inactive_user", client_ip, user_agent, False,
                          "Password reset attempted on inactive user")
        raise AuthenticationError("Account is inactive", request_id=request_id)
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    
    # Clear reset token
    clear_reset_token(db, user)
    
    # Invalidate all existing sessions for security
    invalidate_user_sessions(db, user)
    
    # Log successful password reset
    log_security_event(db, str(user.id), "password_reset_success", client_ip, user_agent, True,
                      "Password reset completed successfully")
    
    logger.info(
        f"Password reset completed for user: {user.username}",
        extra={'request_id': request_id, 'user_id': str(user.id)}
    )
    
    return {"message": "Password reset successfully. Please log in with your new password."}