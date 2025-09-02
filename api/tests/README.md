# Test Suite for EvalWise API

This directory contains comprehensive tests for the EvalWise API, covering security, utilities, authentication, and API functionality.

## Test Structure

### Test Files
- `conftest.py` - Pytest configuration and fixtures
- `test_auth.py` - Authentication system tests
- `test_api.py` - API endpoint tests (currently has integration issues)
- `test_utils.py` - Utility function and configuration tests

### Test Categories

#### Unit Tests (Working ✅)
- **Security Utils**: Password hashing, JWT token creation/validation
- **Logging**: JSON formatting, structured logging
- **Error Handling**: Custom exception classes and error responses
- **Configuration**: Settings validation and environment configuration

#### Integration Tests (Partially Working ⚠️)
- **Database Models**: User model creation and constraint testing
- **Authentication Flow**: Some tests working with test database
- **API Endpoints**: Need fixes for proper integration testing

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock pytest-cov faker
```

### Run Specific Test Categories

```bash
# Unit tests only (all passing)
pytest tests/test_utils.py::TestLogging -v
pytest tests/test_utils.py::TestErrorHandling -v
pytest tests/test_utils.py::TestConfiguration -v
pytest tests/test_auth.py::TestSecurityUtils -v

# Integration tests (SQLite database tests)
pytest tests/test_utils.py::TestDatabaseIntegration -v

# All working tests
pytest tests/test_utils.py tests/test_auth.py::TestSecurityUtils -v
```

### Test Coverage

#### ✅ Fully Tested Components
1. **JWT Authentication System**
   - Token creation and validation
   - Password hashing and verification
   - Token expiration handling

2. **Error Handling System** 
   - Custom exception classes
   - Structured error responses
   - Error detail formatting

3. **Logging System**
   - JSON formatting with datetime handling
   - Structured logging with extra context
   - Custom JSON encoder

4. **Configuration Management**
   - Environment variable validation
   - Settings structure verification
   - URL format validation

#### ⚠️ Partially Tested Components
1. **Database Integration**
   - Basic model operations (working with SQLite test DB)
   - Constraint testing
   - Need full PostgreSQL integration tests

2. **API Endpoints**
   - Test structure created but needs fixes for FastAPI integration
   - Authentication flow tests need database mocking improvements

#### 🚧 Needs Implementation
1. **Full API Integration Tests**
   - Complete request/response cycle testing
   - Authentication middleware testing
   - Error handling middleware testing

2. **Performance Tests**
   - Load testing for authentication endpoints
   - Database connection pooling tests

3. **Security Tests**
   - Input validation testing
   - SQL injection prevention
   - XSS protection validation

## Test Configuration

The test suite uses:
- **SQLite in-memory database** for fast, isolated testing
- **Custom TestUser model** compatible with SQLite (no UUID support)
- **Separate test metadata** to avoid conflicts with production models
- **Faker library** for generating realistic test data

## Current Status

**Working Tests**: 17/62 tests passing
- All unit tests for core functionality
- Basic integration tests for database models
- Security utility functions

**Issues to Fix**:
- FastAPI test client integration with custom authentication
- Database session management in integration tests
- API endpoint testing with proper mocking

## Next Steps

1. Fix FastAPI integration test issues
2. Add comprehensive API endpoint coverage
3. Implement performance and security testing
4. Add test coverage reporting
5. Set up continuous integration testing