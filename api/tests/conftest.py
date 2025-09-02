import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os
import uuid
from faker import Faker

from main_v2 import app
from database import get_db, Base
from auth.security import get_password_hash
from config import settings


fake = Faker()

# Test database URL - using SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test metadata and models for SQLite testing
from sqlalchemy import MetaData, Column, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

TestBase = declarative_base(metadata=MetaData())

class TestUser(TestBase):
    """Test User model compatible with SQLite"""
    __tablename__ = "test_users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    api_key_hash = Column(String, nullable=True)
    rate_limit_tier = Column(String, default="basic")
    
    def __repr__(self):
        return f"<TestUser(username='{self.username}', email='{self.email}')>"


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    TestBase.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        TestBase.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency overrides"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Generate test user data"""
    return {
        "email": fake.email(),
        "username": fake.user_name(),
        "password": "testpass123",
        "full_name": fake.name(),
    }


@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user in the database"""
    hashed_password = get_password_hash(test_user_data["password"])
    
    user = TestUser(
        email=test_user_data["email"],
        username=test_user_data["username"],
        hashed_password=hashed_password,
        full_name=test_user_data["full_name"],
        is_active=True,
        is_superuser=False,
        rate_limit_tier="basic"
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(client, test_user_data):
    """Get authentication headers with JWT token"""
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def api_key_headers(client, test_user_data):
    """Get authentication headers with API key"""
    # First get JWT token to create API key
    login_data = {
        "username": test_user_data["username"], 
        "password": test_user_data["password"]
    }
    
    response = client.post("/auth/login", data=login_data)
    token_data = response.json()
    jwt_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # Create API key
    response = client.post("/auth/api-key", headers=jwt_headers)
    assert response.status_code == 200
    
    api_key_data = response.json()
    api_key = api_key_data["api_key"]
    
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture
def sample_run_data():
    """Generate sample run data for testing"""
    return {
        "name": fake.sentence(nb_words=3),
        "dataset_id": str(fake.uuid4()),
        "model_config": {
            "model_name": "gpt-3.5-turbo",
            "provider": "openai",
            "temperature": 0.7,
            "max_tokens": 150,
            "api_key": "test-api-key"
        },
        "evaluation_config": {
            "metrics": ["accuracy", "relevance"],
            "custom_prompts": {}
        }
    }


@pytest.fixture
def sample_dataset_data():
    """Generate sample dataset data for testing"""
    return {
        "name": fake.sentence(nb_words=2),
        "description": fake.text(max_nb_chars=200),
        "data": [
            {
                "input": fake.sentence(),
                "expected_output": fake.sentence(),
                "metadata": {"category": "test"}
            }
        ]
    }