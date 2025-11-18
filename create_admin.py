#!/usr/bin/env python3
"""
Create a fresh admin user for testing
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from database import SessionLocal, engine
from auth.models import User, Organization, UserOrganization
from auth.security import get_password_hash

def create_admin():
    db = SessionLocal()
    try:
        # Delete existing admin user if exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Deleting existing admin user...")
            db.delete(existing_admin)
            db.commit()
        
        # Get default organization
        default_org = db.query(Organization).filter(Organization.name == "Default Organization").first()
        if not default_org:
            default_org = Organization(
                name="Default Organization",
                description="Default organization",
                max_users=100,
                max_datasets=1000,
                max_runs_per_month=10000
            )
            db.add(default_org)
            db.flush()
        
        # Create new admin user with known password
        admin_user = User(
            username="admin",
            email="admin@evalwise.local",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            is_active=True,
            is_superuser=True,
            rate_limit_tier="enterprise"
        )
        db.add(admin_user)
        db.flush()
        
        # Add to organization
        user_org = UserOrganization(
            user_id=admin_user.id,
            organization_id=default_org.id,
            role="admin"
        )
        db.add(user_org)
        
        db.commit()
        print(f"✅ Created admin user: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Password: admin123")
        print(f"   Superuser: {admin_user.is_superuser}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()