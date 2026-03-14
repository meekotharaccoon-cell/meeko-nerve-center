"""
Authentication tests
"""

import pytest
import unittest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.main import app
from app.models.user import User, UserRole, UserStatus

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def mock_user_model():
    """Returns a mock user model instance that satisfies the UserResponse schema."""
    user = unittest.mock.MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.phone = "+1234567890"
    user.bio = "Test bio"
    user.timezone = "UTC"
    user.language = "en"
    user.currency = "USD"
    user.role = UserRole.CUSTOMER
    user.status = UserStatus.ACTIVE
    user.is_active = True
    user.email_verified = True
    user.phone_verified = False
    user.avatar_url = None
    user.company_name = None
    user.business_address = None
    user.tax_id = None
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    user.last_login_at = None
    user.password_hash = "a_very_hashed_password"
    return user

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "POD E-commerce Platform"}

@patch("app.api.api_v1.endpoints.auth.UserService")
def test_register_user(MockUserService, client, mock_user_model):
    """Test user registration with mocked service"""
    mock_user_service_instance = MockUserService.return_value
    mock_user_service_instance.get_by_email = AsyncMock(return_value=None)
    mock_user_service_instance.create = AsyncMock(return_value=mock_user_model)

    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1234567890",
        "bio": "Test bio",
        "timezone": "UTC",
        "language": "en",
        "currency": "USD",
    }

    with patch('app.database.get_async_db', new=lambda: unittest.mock.MagicMock()):
        response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]
    mock_user_service_instance.get_by_email.assert_awaited_once_with(user_data["email"])
    mock_user_service_instance.create.assert_awaited_once()

@patch("app.api.api_v1.endpoints.auth.AuthService")
def test_login_user(MockAuthService, client, mock_user_model):
    """Test user login with mocked service"""
    mock_auth_service_instance = MockAuthService.return_value
    mock_auth_service_instance.authenticate = AsyncMock(return_value=mock_user_model)
    mock_auth_service_instance.create_access_token.return_value = "fake_access_token"

    login_data = {"username": "test@example.com", "password": "testpassword123"}

    with patch('app.database.get_async_db', new=lambda: unittest.mock.MagicMock()):
        response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["access_token"] == "fake_access_token"
    mock_auth_service_instance.authenticate.assert_awaited_once()
    mock_auth_service_instance.create_access_token.assert_called_once()

@patch("app.api.api_v1.endpoints.auth.AuthService")
def test_invalid_login(MockAuthService, client):
    """Test invalid login credentials with mocked service"""
    mock_auth_service_instance = MockAuthService.return_value
    mock_auth_service_instance.authenticate = AsyncMock(return_value=None)

    login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}

    with patch('app.database.get_async_db', new=lambda: unittest.mock.MagicMock()):
        response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}
    mock_auth_service_instance.authenticate.assert_awaited_once()

@patch("app.api.api_v1.endpoints.auth.AuthService")
def test_get_current_user(MockAuthService, client, mock_user_model):
    """Test getting current user info with mocked service"""
    mock_auth_service_instance = MockAuthService.return_value
    mock_auth_service_instance.get_current_user = AsyncMock(return_value=mock_user_model)

    with patch('app.database.get_async_db', new=lambda: unittest.mock.MagicMock()):
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake_token"})

    assert response.status_code == 200
    assert response.json()["email"] == mock_user_model.email
    mock_auth_service_instance.get_current_user.assert_awaited_once_with("fake_token")