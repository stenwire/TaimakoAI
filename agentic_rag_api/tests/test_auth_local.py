from fastapi.testclient import TestClient
from app.main import app
from app.api.routes import router

def test_signup_success(client):
    response = client.post("/auth/signup", json={
        "email": "newuser@example.com",
        "password": "securepassword",
        "name": "New User"
    })
    # response should be wrapped
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "newuser@example.com"
    assert "id" in data["data"]

def test_signup_duplicate_email(client):
    # First signup
    client.post("/auth/signup", json={
        "email": "duplicate@example.com",
        "password": "password",
        "name": "User 1"
    })
    # Second signup
    response = client.post("/auth/signup", json={
        "email": "duplicate@example.com",
        "password": "password",
        "name": "User 2"
    })
    # Should fail
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert "already exists" in data["message"]

def test_login_success(client):
    # Signup first
    client.post("/auth/signup", json={
        "email": "loginuser@example.com",
        "password": "password123",
        "name": "Login User"
    })
    
    # Login
    response = client.post("/auth/login", json={
        "email": "loginuser@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

def test_login_invalid_credentials(client):
    # Signup first
    client.post("/auth/signup", json={
        "email": "invalid@example.com",
        "password": "password123",
        "name": "Invalid User"
    })
    
    # Login with wrong password
    response = client.post("/auth/login", json={
        "email": "invalid@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"
