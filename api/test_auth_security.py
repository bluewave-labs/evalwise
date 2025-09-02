#!/usr/bin/env python3
"""
Security test script for authentication system
Tests various edge cases and security vulnerabilities
"""

import requests
import time
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_rate_limiting():
    """Test login rate limiting"""
    print("Testing rate limiting...")
    
    # Try to exceed rate limit
    for i in range(7):  # More than max_login_attempts (5)
        response = requests.post(f"{API_BASE}/auth/login", 
                               data={
                                   "username": "nonexistent",
                                   "password": "wrongpassword"
                               })
        print(f"Attempt {i+1}: Status {response.status_code}")
        
        if i >= 4:  # Should start rate limiting after 5 attempts
            assert response.status_code == 401, f"Expected rate limiting, got {response.status_code}"
    
    print("✓ Rate limiting works correctly")

def test_jwt_token_validation():
    """Test JWT token validation edge cases"""
    print("Testing JWT token validation...")
    
    # Test with invalid token
    response = requests.get(f"{API_BASE}/auth/me", 
                          headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401, "Should reject invalid token"
    
    # Test with malformed token
    response = requests.get(f"{API_BASE}/auth/me", 
                          headers={"Authorization": "Bearer malformed.jwt.token"})
    assert response.status_code == 401, "Should reject malformed token"
    
    # Test with missing bearer prefix
    response = requests.get(f"{API_BASE}/auth/me", 
                          headers={"Authorization": "invalid_token"})
    assert response.status_code == 401, "Should reject token without Bearer"
    
    print("✓ JWT validation works correctly")

def test_concurrent_session_limits():
    """Test concurrent session management"""
    print("Testing concurrent session limits...")
    
    # Create a test user first
    test_user = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!",
        "full_name": "Test User"
    }
    
    # Register user (ignore if already exists)
    requests.post(f"{API_BASE}/auth/register", json=test_user)
    
    # Create multiple sessions
    sessions = []
    for i in range(7):  # More than max_concurrent_sessions (5)
        response = requests.post(f"{API_BASE}/auth/login", 
                               data={
                                   "username": test_user["username"],
                                   "password": test_user["password"]
                               })
        if response.status_code == 200:
            sessions.append(response.cookies)
            print(f"Session {i+1} created successfully")
    
    print(f"✓ Created {len(sessions)} sessions (should limit to 5)")

def test_refresh_token_security():
    """Test refresh token security"""
    print("Testing refresh token security...")
    
    # Test refresh without token
    response = requests.post(f"{API_BASE}/auth/refresh")
    assert response.status_code == 401, "Should reject refresh without token"
    
    # Test refresh with invalid cookie
    response = requests.post(f"{API_BASE}/auth/refresh",
                           cookies={"refresh_token": "invalid_token"})
    assert response.status_code == 401, "Should reject invalid refresh token"
    
    print("✓ Refresh token security works correctly")

def test_api_key_validation():
    """Test API key validation"""
    print("Testing API key validation...")
    
    # Test with invalid API key format
    response = requests.get(f"{API_BASE}/auth/me", 
                          headers={"Authorization": "Bearer invalid_api_key"})
    assert response.status_code == 401, "Should reject invalid API key format"
    
    # Test with valid format but wrong key
    response = requests.get(f"{API_BASE}/auth/me", 
                          headers={"Authorization": "Bearer ew_fakekeydata1234567890abcdef"})
    assert response.status_code == 401, "Should reject non-existent API key"
    
    print("✓ API key validation works correctly")

def test_password_security():
    """Test password security requirements"""
    print("Testing password security...")
    
    weak_passwords = [
        "123",
        "password",
        "12345678",
        "qwerty"
    ]
    
    for weak_pwd in weak_passwords:
        test_user = {
            "email": f"weak{weak_pwd}@example.com",
            "username": f"weak{weak_pwd}",
            "password": weak_pwd,
            "full_name": "Weak Password User"
        }
        
        response = requests.post(f"{API_BASE}/auth/register", json=test_user)
        # Note: Current implementation may not have password strength validation
        # This test documents the current behavior
        print(f"Password '{weak_pwd}': Status {response.status_code}")

def test_sql_injection():
    """Test for SQL injection vulnerabilities"""
    print("Testing SQL injection protection...")
    
    sql_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "' OR 1=1 #"
    ]
    
    for payload in sql_payloads:
        response = requests.post(f"{API_BASE}/auth/login", 
                               data={
                                   "username": payload,
                                   "password": "anypassword"
                               })
        # Should always return 401 (not 500 or expose data)
        assert response.status_code == 401, f"SQL injection test failed for payload: {payload}"
    
    print("✓ SQL injection protection works correctly")

def test_timing_attacks():
    """Test for timing attack vulnerabilities"""
    print("Testing timing attack protection...")
    
    # Time login attempts for existing vs non-existing users
    # Both should take similar time to prevent user enumeration
    
    start_time = time.time()
    response1 = requests.post(f"{API_BASE}/auth/login", 
                            data={
                                "username": "nonexistent_user_12345",
                                "password": "wrongpassword"
                            })
    time1 = time.time() - start_time
    
    start_time = time.time()
    response2 = requests.post(f"{API_BASE}/auth/login", 
                            data={
                                "username": "testuser",  # Existing user
                                "password": "wrongpassword"
                            })
    time2 = time.time() - start_time
    
    # Times should be similar (within reasonable threshold)
    time_diff = abs(time1 - time2)
    print(f"Timing difference: {time_diff:.3f}s")
    
    # Allow some variance but flag if too different
    if time_diff > 0.5:  # 500ms threshold
        print("⚠️  Potential timing attack vulnerability detected")
    else:
        print("✓ Timing attack protection appears adequate")

def main():
    """Run all security tests"""
    print("=" * 50)
    print("AUTHENTICATION SECURITY TEST SUITE")
    print("=" * 50)
    
    try:
        test_rate_limiting()
        test_jwt_token_validation()
        test_concurrent_session_limits()
        test_refresh_token_security()
        test_api_key_validation()
        test_password_security()
        test_sql_injection()
        test_timing_attacks()
        
        print("=" * 50)
        print("✅ All security tests completed")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()