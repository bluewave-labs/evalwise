"""
Application startup validation utilities
"""
import os
import sys
import logging
from typing import List, Dict, Any
from config import settings
from database import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

class StartupValidator:
    """Validates application configuration and dependencies on startup"""
    
    @classmethod
    def validate_all(cls) -> None:
        """Run all startup validations"""
        logger.info("Starting application validation...")
        
        try:
            # Critical validations that should prevent startup
            cls._validate_required_environment_variables()
            cls._validate_security_configuration()
            cls._validate_database_connection()
            
            # Warning-level validations
            cls._validate_optional_configuration()
            
            logger.info("Application validation completed successfully")
            
        except Exception as e:
            logger.error(f"Application validation failed: {str(e)}")
            sys.exit(1)
    
    @classmethod
    def _validate_required_environment_variables(cls) -> None:
        """Validate that all required environment variables are set"""
        required_vars = [
            "SECRET_KEY",
            "JWT_SECRET_KEY", 
            "POSTGRES_PASSWORD",
            "DATABASE_URL"
        ]
        
        missing_vars = []
        weak_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            elif var.endswith("_KEY") and len(value) < 32:
                weak_vars.append(f"{var} (length: {len(value)}, recommended: 32+)")
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please check your .env file and ensure all required variables are set."
            )
        
        if weak_vars:
            logger.warning(
                f"Weak security keys detected: {', '.join(weak_vars)}. "
                "Consider using stronger keys generated with: openssl rand -hex 32"
            )
    
    @classmethod
    def _validate_security_configuration(cls) -> None:
        """Validate security-related configuration"""
        
        # Check if running in production with secure settings
        if settings.is_production:
            if not settings.should_use_secure_cookies:
                logger.warning(
                    "Running in production but secure cookies are disabled. "
                    "Set COOKIE_SECURE=true for production deployments."
                )
            
            if settings.debug:
                raise ValueError(
                    "DEBUG mode is enabled in production environment. "
                    "Set DEBUG=false for production deployments."
                )
            
            if settings.cors_origins == ["http://localhost:3001"]:
                logger.warning(
                    "CORS origins still set to development defaults in production. "
                    "Update CORS_ORIGINS environment variable for production."
                )
        
        # Validate JWT configuration
        if settings.jwt_access_token_expire_minutes > 60:
            logger.warning(
                f"JWT access token expiry is set to {settings.jwt_access_token_expire_minutes} minutes. "
                "Consider using shorter expiry times (15-30 minutes) for better security."
            )
        
        # Check encryption key requirement
        try:
            from utils.encryption import encryption
            # This will fail if API_ENCRYPTION_KEY is not set
        except ValueError as e:
            if "API_ENCRYPTION_KEY" in str(e):
                raise ValueError(
                    "API_ENCRYPTION_KEY environment variable is required. "
                    "Generate with: openssl rand -hex 32"
                )
            raise e
    
    @classmethod
    def _validate_database_connection(cls) -> None:
        """Validate database connectivity"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("Database connection validated successfully")
        except Exception as e:
            raise ValueError(f"Database connection failed: {str(e)}")
    
    @classmethod
    def _validate_optional_configuration(cls) -> None:
        """Validate optional configuration and issue warnings if needed"""
        
        # Check for email configuration if password reset is expected to work
        if not settings.smtp_username:
            logger.warning(
                "SMTP configuration is not complete. Password reset emails will not work. "
                "Configure SMTP_* environment variables if email functionality is needed."
            )
        
        # Check for external API keys
        if not settings.openai_api_key and not settings.azure_openai_api_key:
            logger.warning(
                "No OpenAI API keys configured. LLM evaluation features will not work. "
                "Set OPENAI_API_KEY or Azure OpenAI credentials if needed."
            )
        
        # Check logging level
        if settings.log_level.upper() == "DEBUG" and settings.is_production:
            logger.warning(
                "Debug logging is enabled in production. "
                "Consider setting LOG_LEVEL=INFO or LOG_LEVEL=WARNING for production."
            )


def validate_startup() -> None:
    """Main startup validation function"""
    StartupValidator.validate_all()