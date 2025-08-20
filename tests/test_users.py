"""
Tests for user endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_get_own_email_success(client: TestClient, test_user, user_token):
    """Test user getting their own email."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get(
        f"{settings.API_V1_STR}/users/email/{test_user.user_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.user_id
    assert data["email"] == test_user.email


def test_admin_get_any_email_success(client: TestClient, test_user, test_admin_user, admin_token):
    """Test admin getting any user's email."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get(
        f"{settings.API_V1_STR}/users/email/{test_user.user_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.user_id
    assert data["email"] == test_user.email


def test_user_get_other_email_forbidden(client: TestClient, test_user, test_admin_user, user_token):
    """Test regular user trying to get another user's email (should fail)."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get(
        f"{settings.API_V1_STR}/users/email/{test_admin_user.user_id}",
        headers=headers
    )
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]


def test_get_email_without_auth(client: TestClient, test_user):
    """Test getting email without authentication."""
    response = client.get(f"{settings.API_V1_STR}/users/email/{test_user.user_id}")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_get_email_invalid_token(client: TestClient, test_user):
    """Test getting email with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get(
        f"{settings.API_V1_STR}/users/email/{test_user.user_id}",
        headers=headers
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_get_email_nonexistent_user(client: TestClient, user_token):
    """Test getting email for nonexistent user."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get(
        f"{settings.API_V1_STR}/users/email/999999",
        headers=headers
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_get_email_invalid_user_id(client: TestClient, user_token):
    """Test getting email with invalid user ID format."""
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get(
        f"{settings.API_V1_STR}/users/email/invalid",
        headers=headers
    )
    assert response.status_code == 422  # Validation error
