import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime, timedelta

from auth.models import User
from auth.security import create_access_token, verify_password, get_password_hash
from utils.errors import AuthenticationError, ConflictError


class TestUserRegistration:
    """Test user registration functionality"""
    
    @pytest.mark.auth
    def test_register_user_success(self, client: TestClient):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepass123",
            "full_name": "New User"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.auth
    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,  # Duplicate email
            "username": "differentuser",
            "password": "securepass123",
            "full_name": "Different User"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 409  # Conflict
        
        data = response.json()
        assert data["error"] is True
        assert "Email already registered" in data["message"]
    
    @pytest.mark.auth
    def test_register_duplicate_username(self, client: TestClient, test_user):
        """Test registration with duplicate username"""
        user_data = {
            "email": "different@example.com",
            "username": test_user.username,  # Duplicate username
            "password": "securepass123",
            "full_name": "Different User"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 409  # Conflict
        
        data = response.json()
        assert data["error"] is True
        assert "Username already taken" in data["message"]
    
    @pytest.mark.auth
    def test_register_invalid_data(self, client: TestClient):
        """Test registration with invalid data"""
        user_data = {
            "email": "invalid-email",  # Invalid email format
            "username": "",  # Empty username
            "password": "123",  # Too short password
            "full_name": ""
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality"""
    
    @pytest.mark.auth
    def test_login_success(self, client: TestClient, test_user, test_user_data):
        """Test successful user login"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        
        # Verify user data in response
        user_data = data["user"]
        assert user_data["username"] == test_user.username
        assert user_data["email"] == test_user.email
    
    @pytest.mark.auth
    def test_login_invalid_username(self, client: TestClient):
        """Test login with invalid username"""
        login_data = {
            "username": "nonexistent",
            "password": "anypassword"
        }
        
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401  # Unauthorized
        
        data = response.json()
        assert data["error"] is True
        assert "Incorrect username or password" in data["message"]
    
    @pytest.mark.auth
    def test_login_invalid_password(self, client: TestClient, test_user_data):
        """Test login with invalid password"""
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401  # Unauthorized


class TestCurrentUser:
    """Test current user functionality"""
    
    @pytest.mark.auth
    def test_get_current_user_with_jwt(self, client: TestClient, test_user, auth_headers):
        """Test getting current user info with JWT token"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] == test_user.is_active
    
    @pytest.mark.auth
    def test_get_current_user_with_api_key(self, client: TestClient, test_user, api_key_headers):
        """Test getting current user info with API key"""
        response = client.get("/auth/me", headers=api_key_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
    
    @pytest.mark.auth
    def test_get_current_user_no_auth(self, client: TestClient):
        """Test getting current user info without authentication"""
        response = client.get("/auth/me")
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.auth
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user info with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401  # Unauthorized


class TestApiKey:
    """Test API key functionality"""
    
    @pytest.mark.auth
    def test_create_api_key_success(self, client: TestClient, test_user, auth_headers):
        """Test successful API key creation"""
        response = client.post("/auth/api-key", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("ew_")
        assert data["key_id"] == str(test_user.id)
        assert "created_at" in data
        assert data["expires_at"] is None
    
    @pytest.mark.auth
    def test_create_api_key_no_auth(self, client: TestClient):
        """Test API key creation without authentication"""
        response = client.post("/auth/api-key")
        assert response.status_code == 401  # Unauthorized


class TestPasswordChange:
    """Test password change functionality"""
    
    @pytest.mark.auth
    def test_change_password_success(self, client: TestClient, test_user_data, auth_headers):
        """Test successful password change"""
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "newsecurepass123"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "Password changed successfully" in data["message"]
    
    @pytest.mark.auth
    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """Test password change with wrong current password"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newsecurepass123"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 401  # Unauthorized
        
        data = response.json()
        assert data["error"] is True
        assert "Current password is incorrect" in data["message"]
    
    @pytest.mark.auth
    def test_change_password_no_auth(self, client: TestClient):
        """Test password change without authentication"""
        password_data = {
            "current_password": "anypassword",
            "new_password": "newsecurepass123"
        }
        
        response = client.post("/auth/change-password", json=password_data)
        assert response.status_code == 401  # Unauthorized


class TestLogout:
    """Test logout functionality"""
    
    @pytest.mark.auth
    def test_logout_success(self, client: TestClient, auth_headers):
        """Test successful logout"""
        response = client.post("/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "Logged out successfully" in data["message"]
    
    @pytest.mark.auth
    def test_logout_no_auth(self, client: TestClient):
        """Test logout without authentication"""
        response = client.post("/auth/logout")
        assert response.status_code == 401  # Unauthorized


class TestSecurityUtils:
    """Test security utility functions"""
    
    @pytest.mark.unit
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should not be the same as password
        assert hashed != password
        
        # Verification should work
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    @pytest.mark.unit
    def test_jwt_token_creation(self):
        """Test JWT token creation"""
        data = {"sub": "testuser", "scopes": ["read", "write"]}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Token should contain encoded data
        from jose import jwt
        from config import settings
        
        decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert decoded["sub"] == "testuser"
        assert decoded["scopes"] == ["read", "write"]
        assert "exp" in decoded
    
    @pytest.mark.unit
    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        data = {"sub": "testuser"}
        
        # Create token with short expiration
        short_expiry = timedelta(seconds=1)
        token = create_access_token(data, expires_delta=short_expiry)
        
        # Decode immediately - should work
        from jose import jwt
        from config import settings
        
        decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert decoded["sub"] == "testuser"
        
        # After expiration, decoding should fail
        import time
        time.sleep(2)
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])