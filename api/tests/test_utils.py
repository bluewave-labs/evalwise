import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from utils.logging import get_logger, CustomJSONEncoder, RequestContext
from utils.errors import (
    ValidationError, NotFoundError, ConflictError, 
    AuthenticationError, AuthorizationError, ErrorDetail
)
from config import settings


class TestLogging:
    """Test logging utilities"""
    
    @pytest.mark.unit
    def test_get_logger(self):
        """Test logger creation"""
        logger = get_logger("test_module")
        assert logger.name == "test_module"
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
    
    @pytest.mark.unit
    def test_custom_json_encoder(self):
        """Test custom JSON encoder for datetime objects"""
        encoder = CustomJSONEncoder()
        
        # Test datetime encoding
        now = datetime.utcnow()
        result = encoder.default(now)
        assert isinstance(result, str)
        assert result == now.isoformat()
        
        # Test non-datetime object (should raise TypeError)
        with pytest.raises(TypeError):
            encoder.default({"not": "datetime"})
    
    @pytest.mark.unit
    def test_structured_logging(self):
        """Test structured logging functionality"""
        logger = get_logger("test_structured")
        
        # Test that we can add structured data to logs
        try:
            logger.info("Test message", extra={
                "request_id": "test-request-123",
                "user_id": "user-456",
                "operation": "test_operation"
            })
            # If no exception is raised, structured logging works
            assert True
        except Exception as e:
            pytest.fail(f"Structured logging failed: {e}")
    
    @pytest.mark.unit
    def test_logger_with_extra_context(self):
        """Test logger with extra context information"""
        logger = get_logger("test_context")
        
        # This test verifies the logger can handle extra parameters
        # In a real scenario, this would be captured by log handlers
        try:
            logger.info("Test message", extra={"request_id": "test-123", "user_id": "user-456"})
            # If no exception is raised, the logger handled extra parameters correctly
            assert True
        except Exception as e:
            pytest.fail(f"Logger failed to handle extra parameters: {e}")


class TestErrorHandling:
    """Test error handling utilities"""
    
    @pytest.mark.unit
    def test_error_detail(self):
        """Test ErrorDetail model"""
        detail = ErrorDetail(
            code="TEST_ERROR",
            message="Test error message",
            field="test_field"
        )
        
        assert detail.code == "TEST_ERROR"
        assert detail.message == "Test error message"
        assert detail.field == "test_field"
    
    @pytest.mark.unit
    def test_validation_error(self):
        """Test ValidationError exception"""
        details = [
            ErrorDetail(code="REQUIRED", message="Field is required", field="name"),
            ErrorDetail(code="INVALID", message="Field is invalid", field="email")
        ]
        
        error = ValidationError(
            "Validation failed",
            details=details,
            request_id="test-request-123"
        )
        
        assert error.status_code == 422
        assert error.error_response.message == "Validation failed"
        assert error.error_response.details == details
        assert error.error_response.request_id == "test-request-123"
    
    @pytest.mark.unit
    def test_authentication_error(self):
        """Test AuthenticationError exception"""
        error = AuthenticationError("Invalid credentials", request_id="test-123")
        
        assert error.status_code == 401
        assert error.error_response.message == "Invalid credentials"
        assert error.error_response.request_id == "test-123"
    
    @pytest.mark.unit
    def test_authorization_error(self):
        """Test AuthorizationError exception"""
        error = AuthorizationError("Insufficient permissions", request_id="test-123")
        
        assert error.status_code == 403
        assert error.error_response.message == "Insufficient permissions"
        assert error.error_response.request_id == "test-123"
    
    @pytest.mark.unit
    def test_not_found_error(self):
        """Test NotFoundError exception"""
        error = NotFoundError("User", resource_id="123", request_id="test-123")
        
        assert error.status_code == 404
        assert "User not found" in error.error_response.message
        assert error.error_response.request_id == "test-123"
    
    @pytest.mark.unit
    def test_conflict_error(self):
        """Test ConflictError exception"""
        details = [ErrorDetail(code="DUPLICATE", message="Resource already exists", field="email")]
        error = ConflictError(
            "Conflict occurred",
            details=details,
            request_id="test-123"
        )
        
        assert error.status_code == 409
        assert error.error_response.message == "Conflict occurred"
        assert error.error_response.details == details
        assert error.error_response.request_id == "test-123"


class TestConfiguration:
    """Test configuration settings"""
    
    @pytest.mark.unit
    def test_settings_exist(self):
        """Test that required settings exist"""
        # Test database settings
        assert hasattr(settings, 'database_url')
        assert isinstance(settings.database_url, str)
        
        # Test JWT settings
        assert hasattr(settings, 'jwt_secret_key')
        assert hasattr(settings, 'jwt_algorithm')
        assert hasattr(settings, 'jwt_access_token_expire_minutes')
        
        # Test Redis settings
        assert hasattr(settings, 'redis_url')
        assert hasattr(settings, 'celery_broker_url')
        assert hasattr(settings, 'celery_result_backend')
        
        # Test general settings
        assert hasattr(settings, 'secret_key')
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'debug')
        assert hasattr(settings, 'log_level')
    
    @pytest.mark.unit
    def test_jwt_settings_valid(self):
        """Test JWT settings are valid"""
        assert settings.jwt_algorithm in ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        assert isinstance(settings.jwt_access_token_expire_minutes, int)
        assert settings.jwt_access_token_expire_minutes > 0
        assert len(settings.jwt_secret_key) > 10  # Should be reasonably long
    
    @pytest.mark.unit 
    def test_environment_settings(self):
        """Test environment-specific settings"""
        assert settings.environment in ['development', 'testing', 'production']
        assert isinstance(settings.debug, bool)
        assert settings.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    @pytest.mark.unit
    def test_urls_format(self):
        """Test URL format validation"""
        # Database URL should contain database info
        db_url = settings.database_url
        assert 'postgresql' in db_url.lower() or 'sqlite' in db_url.lower()
        
        # Redis URLs should be valid
        redis_url = settings.redis_url
        assert redis_url.startswith('redis://') or redis_url.startswith('rediss://')


class TestMiddleware:
    """Test middleware functionality"""
    
    @pytest.mark.integration
    def test_error_handling_middleware(self, client):
        """Test error handling middleware integration"""
        # Test with invalid JSON
        response = client.post(
            "/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should get a proper error response, not raw FastAPI error
        assert response.status_code in [400, 422]
        
        # Try to parse response as JSON
        try:
            data = response.json()
            # If it's our custom error format, should have these fields
            if isinstance(data, dict) and data.get("error"):
                assert "error_id" in data
                assert "timestamp" in data
        except json.JSONDecodeError:
            # If it's not JSON, that's also acceptable for malformed requests
            pass
    
    @pytest.mark.integration
    def test_request_tracking_middleware(self, client):
        """Test request tracking middleware"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        # Health endpoint includes timestamp, indicating request was processed
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)


class TestDatabaseIntegration:
    """Test database integration and models"""
    
    @pytest.mark.integration
    def test_user_model_creation(self, db_session):
        """Test TestUser model creation and database operations"""
        from tests.conftest import TestUser
        from auth.security import get_password_hash
        
        user_data = {
            "email": "test@db.com",
            "username": "dbtest",
            "hashed_password": get_password_hash("testpass"),
            "full_name": "DB Test User",
            "is_active": True,
            "is_superuser": False,
            "rate_limit_tier": "basic"
        }
        
        user = TestUser(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Verify user was created
        assert user.id is not None
        assert user.email == user_data["email"]
        assert user.username == user_data["username"]
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.integration
    def test_user_model_constraints(self, db_session):
        """Test TestUser model unique constraints"""
        from tests.conftest import TestUser
        from auth.security import get_password_hash
        from sqlalchemy.exc import IntegrityError
        
        # Create first user
        user1 = TestUser(
            email="unique@test.com",
            username="uniqueuser",
            hashed_password=get_password_hash("pass"),
            full_name="User One"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create user with same email - should fail
        user2 = TestUser(
            email="unique@test.com",  # Same email
            username="differentuser",
            hashed_password=get_password_hash("pass"),
            full_name="User Two"
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Try to create user with same username - should fail
        user3 = TestUser(
            email="different@test.com",
            username="uniqueuser",  # Same username
            hashed_password=get_password_hash("pass"),
            full_name="User Three"
        )
        db_session.add(user3)
        
        with pytest.raises(IntegrityError):
            db_session.commit()