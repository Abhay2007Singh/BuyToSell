import pytest
from fastapi.testclient import TestClient

def test_register_success(client: TestClient):
    """Test successful user registration"""
    user_data = {
        "email": "newuser@example.com",
        "password": "testpass",
        "role": "customer"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["role"] == user_data["role"]
    assert "id" in data
    assert "created_at" in data

def test_register_duplicate_email(client: TestClient):
    """Test registration with duplicate email"""
    user_data = {
        "email": "test_admin@example.com",
        "password": "testpass",
        "role": "customer"
    }
    
    # First registration should succeed
    response1 = client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 201
    
    # Second registration with same email should fail
    response2 = client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "Email already registered" in response2.json()["detail"]

def test_register_missing_fields(client: TestClient):
    """Test registration with missing required fields"""
    # Missing email
    response = client.post("/api/v1/auth/register", json={"password": "testpass"})
    assert response.status_code == 422
    
    # Missing password
    response = client.post("/api/v1/auth/register", json={"email": "test@example.com"})
    assert response.status_code == 422

def test_login_success(customer_client):
    """Test successful login"""
    with customer_client as client:
        login_data = {
            "email": "test_customer@example.com",
            "password": "testpass"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient):
    """Test login with wrong password"""
    login_data = {
        "email": "test_admin@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "testpass"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_token_refresh_valid(customer_client):
    """Test valid token refresh"""
    with customer_client as client:
        # First login to get refresh token
        login_data = {
            "email": "test_customer@example.com",
            "password": "testpass"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

def test_token_refresh_invalid(client: TestClient):
    """Test refresh with invalid token"""
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})
    
    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]
