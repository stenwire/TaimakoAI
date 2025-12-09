import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token

def test_login_google_redirect(client):
    # Debug: Print all routes
    print("\nRegistered Routes:")
    for route in app.routes:
        print(f"  {route.path} {route.name}")

    response = client.get("/auth/google/login")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "success"
    data = json_response["data"]
    assert "auth_url" in data
    assert "accounts.google.com" in data["auth_url"]
    assert settings.GOOGLE_CLIENT_ID in data["auth_url"]

@patch("app.auth.router.exchange_code_for_token")
@patch("app.auth.router.get_google_user_info")
def test_google_callback(mock_get_user_info, mock_exchange_code, client):
    # Mock Google responses
    mock_exchange_code.return_value = {"access_token": "fake_google_token"}
    mock_get_user_info.return_value = {
        "sub": "12345",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "http://example.com/pic.jpg"
    }

    response = client.get("/auth/google/callback?code=fake_code", follow_redirects=False)
    
    # Should redirect to frontend
    assert response.status_code == 307 # Temporary Redirect
    assert settings.FRONTEND_REDIRECT_URI in response.headers["location"]
    assert "access_token" in response.headers["location"]
    assert "refresh_token" in response.headers["location"]

from app.db.session import SessionLocal
from app.models.user import User

def test_get_me_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code == 403 # HTTPBearer raises 403 when token is missing

def test_get_me_authorized(client, db_session):
    # 1. Create a valid token
    token = create_access_token(subject="test_user_id")
    
    # 2. Mock DB query to return a user
    # Use db_session directly
    user = db_session.query(User).filter(User.id == "test_user_id").first()
    if not user:
        user = User(id="test_user_id", google_id="g_123_auth", email="test_auth@example.com", name="Test Auth", picture="pic.jpg")
        db_session.add(user)
        db_session.commit()

    # 3. Call endpoint with Bearer token
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "success"
    data = json_response["data"]
    assert data["email"] == "test_auth@example.com"
    assert data["id"] == "test_user_id"
