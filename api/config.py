import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    postgres_db: str = Field("evalwise", env="POSTGRES_DB")
    postgres_user: str = Field("evalwise", env="POSTGRES_USER") 
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    
    # Redis Configuration
    redis_url: str = Field("redis://redis:6379/0", env="REDIS_URL")
    celery_broker_url: str = Field("redis://redis:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://redis:6379/0", env="CELERY_RESULT_BACKEND")
    
    # API Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(15, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")  # Reduced from 30 to 15
    jwt_refresh_token_expire_days: int = Field(7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_issuer: str = Field("evalwise-api", env="JWT_ISSUER")
    jwt_audience: str = Field("evalwise-client", env="JWT_AUDIENCE")
    
    # Security Configuration
    bcrypt_rounds: int = Field(12, env="BCRYPT_ROUNDS")
    max_login_attempts: int = Field(5, env="MAX_LOGIN_ATTEMPTS") 
    login_attempt_window_minutes: int = Field(15, env="LOGIN_ATTEMPT_WINDOW_MINUTES")
    max_concurrent_sessions: int = Field(5, env="MAX_CONCURRENT_SESSIONS")
    
    # Cookie Configuration
    cookie_secure: Optional[bool] = Field(None, env="COOKIE_SECURE")  # Auto-detect based on environment
    cookie_samesite: str = Field("lax", env="COOKIE_SAMESITE")
    cookie_domain: Optional[str] = Field(None, env="COOKIE_DOMAIN")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        ["http://localhost:3001", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )  # Default to development, override in production
    
    # Server Configuration
    environment: str = Field("production", env="ENVIRONMENT")  # Default to production for safety
    debug: bool = Field(False, env="DEBUG")  # Never default to debug mode
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def should_use_secure_cookies(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.is_production  # Auto-detect: secure cookies only in production
    
    # External API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    azure_openai_api_key: Optional[str] = Field(None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(None, env="AZURE_OPENAI_ENDPOINT")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Email Configuration (for password reset)
    smtp_server: str = Field("localhost", env="SMTP_SERVER")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")
    from_email: str = Field("noreply@evalwise.local", env="FROM_EMAIL")
    app_name: str = Field("EvalWise", env="APP_NAME")
    frontend_url: str = Field("http://localhost:3001", env="FRONTEND_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

    def is_development(self) -> bool:
        return self.environment.lower() == "development"

# Global settings instance
settings = Settings()