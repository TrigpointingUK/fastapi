"""
Tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_login_success(client: TestClient, test_user):
    """Test successful login."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": test_user.email, "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_email(client: TestClient, test_user):
    """Test login with invalid email."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "nonexistent@example.com", "password": "testpassword123"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_invalid_password(client: TestClient, test_user):
    """Test login with invalid password."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_missing_credentials(client: TestClient):
    """Test login with missing credentials."""
    response = client.post(f"{settings.API_V1_STR}/auth/login", data={})
    assert response.status_code == 422  # Validation error
