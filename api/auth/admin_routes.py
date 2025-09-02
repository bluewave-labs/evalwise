"""
Admin routes for user and organization management
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from database import get_db
from auth.models import User, Organization, UserOrganization, AuditLog, LoginAttempt, UserSession
from auth.security import get_current_admin_user, get_password_hash, log_security_event, get_client_info
from auth.schemas import UserResponse
from utils.errors import NotFoundError, ConflictError, AuthorizationError, ErrorDetail
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

# Pydantic models for admin operations
from pydantic import BaseModel, Field

class AdminUserCreate(BaseModel):
    """Schema for creating users as admin"""
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    is_active: bool = Field(True, description="User active status")
    is_superuser: bool = Field(False, description="Superuser status")
    rate_limit_tier: str = Field("basic", description="Rate limit tier")

class AdminUserUpdate(BaseModel):
    """Schema for updating users as admin"""
    email: Optional[str] = Field(None, description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    is_active: Optional[bool] = Field(None, description="User active status")
    is_superuser: Optional[bool] = Field(None, description="Superuser status")
    rate_limit_tier: Optional[str] = Field(None, description="Rate limit tier")

class OrganizationCreate(BaseModel):
    """Schema for creating organizations"""
    name: str = Field(..., max_length=200, description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    max_users: int = Field(10, description="Maximum users allowed")
    max_datasets: int = Field(50, description="Maximum datasets allowed")
    max_runs_per_month: int = Field(1000, description="Maximum runs per month")

class OrganizationUpdate(BaseModel):
    """Schema for updating organizations"""
    name: Optional[str] = Field(None, max_length=200, description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    is_active: Optional[bool] = Field(None, description="Organization active status")
    max_users: Optional[int] = Field(None, description="Maximum users allowed")
    max_datasets: Optional[int] = Field(None, description="Maximum datasets allowed")
    max_runs_per_month: Optional[int] = Field(None, description="Maximum runs per month")

class UserOrganizationAssign(BaseModel):
    """Schema for assigning users to organizations"""
    user_id: str = Field(..., description="User ID")
    organization_id: str = Field(..., description="Organization ID")
    role: str = Field("member", description="Role in organization")

class AdminStatsResponse(BaseModel):
    """Schema for admin dashboard statistics"""
    total_users: int
    active_users: int
    total_organizations: int
    active_organizations: int
    recent_logins: int
    failed_logins_24h: int
    active_sessions: int

# Admin dashboard stats
@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # User stats
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    
    # Organization stats
    total_organizations = db.query(func.count(Organization.id)).scalar()
    active_organizations = db.query(func.count(Organization.id)).filter(Organization.is_active == True).scalar()
    
    # Login stats (last 24 hours)
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_logins = db.query(func.count(LoginAttempt.id)).filter(
        LoginAttempt.success == True,
        LoginAttempt.created_at >= last_24h
    ).scalar()
    
    failed_logins_24h = db.query(func.count(LoginAttempt.id)).filter(
        LoginAttempt.success == False,
        LoginAttempt.created_at >= last_24h
    ).scalar()
    
    # Active sessions
    active_sessions = db.query(func.count(UserSession.id)).filter(
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).scalar()
    
    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_organizations=total_organizations,
        active_organizations=active_organizations,
        recent_logins=recent_logins,
        failed_logins_24h=failed_logins_24h,
        active_sessions=active_sessions
    )

# User management
@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search by username, email, or full name"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users with pagination and search"""
    
    query = db.query(User).options(joinedload(User.user_organizations))
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_filter)) |
            (User.email.ilike(search_filter)) |
            (User.full_name.ilike(search_filter))
        )
    
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    return [
        UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None,
            rate_limit_tier=user.rate_limit_tier,
            organizations=[]  # Can be populated if needed
        )
        for user in users
    ]

@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: AdminUserCreate,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user as admin"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    client_ip, user_agent = get_client_info(request)
    
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
        hashed_password=hashed_password,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser,
        rate_limit_tier=user_data.rate_limit_tier
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log admin action
    log_security_event(db, str(current_user.id), "admin_user_create", client_ip, user_agent, True,
                      f"Created user {db_user.username} (ID: {db_user.id})")
    
    logger.info(
        f"Admin {current_user.username} created user: {db_user.username}",
        extra={'request_id': request_id, 'admin_id': str(current_user.id), 'created_user_id': str(db_user.id)}
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
        rate_limit_tier=db_user.rate_limit_tier,
        organizations=[]
    )

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: AdminUserUpdate,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user as admin"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    client_ip, user_agent = get_client_info(request)
    
    # Get user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found", request_id=request_id)
    
    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Check for conflicts if email/username changed
    if user_data.email or user_data.username:
        existing_user = db.query(User).filter(
            User.id != user_id,
            (User.email == (user_data.email or user.email)) | 
            (User.username == (user_data.username or user.username))
        ).first()
        
        if existing_user:
            raise ConflictError("Email or username already exists", request_id=request_id)
    
    db.commit()
    db.refresh(user)
    
    # Log admin action
    log_security_event(db, str(current_user.id), "admin_user_update", client_ip, user_agent, True,
                      f"Updated user {user.username} (ID: {user.id})")
    
    logger.info(
        f"Admin {current_user.username} updated user: {user.username}",
        extra={'request_id': request_id, 'admin_id': str(current_user.id), 'updated_user_id': str(user.id)}
    )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
        rate_limit_tier=user.rate_limit_tier,
        organizations=[]
    )

@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Soft delete user (deactivate)"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    client_ip, user_agent = get_client_info(request)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found", request_id=request_id)
    
    if user.id == current_user.id:
        raise AuthorizationError("Cannot delete yourself", request_id=request_id)
    
    user.is_active = False
    db.commit()
    
    # Log admin action
    log_security_event(db, str(current_user.id), "admin_user_delete", client_ip, user_agent, True,
                      f"Deactivated user {user.username} (ID: {user.id})")
    
    logger.info(
        f"Admin {current_user.username} deactivated user: {user.username}",
        extra={'request_id': request_id, 'admin_id': str(current_user.id), 'deleted_user_id': str(user.id)}
    )
    
    return {"message": "User deactivated successfully"}