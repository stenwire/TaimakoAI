import pytest
from fastapi.testclient import TestClient
from app.models.business import Business
from app.models.user import User
from app.core.security import create_access_token

def test_create_business(client, db_session):
    """Test creating a business profile."""
    # Create a user
    user = User(
        email="business@test.com",
        name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create access token
    token = create_access_token(subject=user.id)
    
    # Create business
    business_data = {
        "business_name": "Test Business",
        "description": "A test business",
        "website": "https://test.com",
        "custom_agent_instruction": "Be very friendly and helpful."
    }
    
    response = client.post(
        "/business",
        json=business_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["business_name"] == "Test Business"
    assert data["data"]["user_id"] == user.id
    
    # Verify in database
    business = db_session.query(Business).filter(Business.user_id == user.id).first()
    assert business is not None
    assert business.business_name == "Test Business"

def test_create_duplicate_business(client, db_session):
    """Test that creating a duplicate business fails."""
    # Create a user with existing business
    user = User(email="duplicate@test.com", name="Test User", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    business = Business(
        user_id=user.id,
        business_name="Existing Business"
    )
    db_session.add(business)
    db_session.commit()
    
    token = create_access_token(subject=user.id)
    
    # Try to create another business
    response = client.post(
        "/business",
        json={"business_name": "New Business"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["message"]

def test_get_business(client, db_session):
    """Test retrieving a business profile."""
    # Create user and business
    user = User(email="get@test.com", name="Test User", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    business = Business(
        user_id=user.id,
        business_name="Get Test Business",
        description="Test description"
    )
    db_session.add(business)
    db_session.commit()
    
    token = create_access_token(subject=user.id)
    
    response = client.get(
        "/business",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["business_name"] == "Get Test Business"
    assert data["data"]["description"] == "Test description"

def test_get_business_not_found(client, db_session):
    """Test getting business when none exists."""
    user = User(email="nobus@test.com", name="Test User", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    token = create_access_token(subject=user.id)
    
    response = client.get(
        "/business",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["message"]

def test_update_business(client, db_session):
    """Test updating a business profile."""
    # Create user and business
    user = User(email="update@test.com", name="Test User", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    business = Business(
        user_id=user.id,
        business_name="Original Name",
        description="Original description"
    )
    db_session.add(business)
    db_session.commit()
    
    token = create_access_token(subject=user.id)
    
    # Update business
    update_data = {
        "business_name": "Updated Name",
        "custom_agent_instruction": "New instruction"
    }
    
    response = client.put(
        "/business",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["business_name"] == "Updated Name"
    assert data["data"]["custom_agent_instruction"] == "New instruction"
    assert data["data"]["description"] == "Original description"  # Unchanged

def test_update_business_not_found(client, db_session):
    """Test updating business when none exists."""
    user = User(email="noupdate@test.com", name="Test User", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    token = create_access_token(subject=user.id)
    
    response = client.put(
        "/business",
        json={"business_name": "New Name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["message"]

def test_chat_requires_business(client, db_session):
    """Test that chat endpoint requires a business profile."""
    user = User(email="chat@test.com", name="Test User", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    token = create_access_token(subject=user.id)
    
    response = client.post(
        "/chat",
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "Business profile not found" in response.json()["message"]
