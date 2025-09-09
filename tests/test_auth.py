"""
Tests for authentication endpoints.
"""

from app.core.config import settings

# import pytest  # Currently unused
from fastapi.testclient import TestClient


def test_login_success(client: TestClient, test_user):
    """Test successful login with enhanced response."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()

    # Check legacy fields (backward compatibility)
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Check enhanced fields
    assert "user" in data
    assert "expires_in" in data

    # Check user data structure
    user_data = data["user"]
    assert "id" in user_data
    assert "name" in user_data
    assert "firstname" in user_data
    assert "surname" in user_data
    assert "about" in user_data
    # Email should be present since user sees their own data
    assert "email" in user_data


def test_login_invalid_email(client: TestClient, test_user):
    """Test login with invalid email."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "nonexistent@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401
    assert "Incorrect username/email or password" in response.json()["detail"]


def test_login_invalid_password(client: TestClient, test_user):
    """Test login with invalid password."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Incorrect username/email or password" in response.json()["detail"]


def test_login_missing_credentials(client: TestClient):
    """Test login with missing credentials."""
    response = client.post(f"{settings.API_V1_STR}/auth/login", data={})
    assert response.status_code == 422  # Validation error
