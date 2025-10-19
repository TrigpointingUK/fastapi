"""
Tests for POST /v1/users user provisioning endpoint.
"""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.crud.user import create_user
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture
def mock_m2m_token():
    """Mock M2M token validation to return valid payload."""
    with patch("app.api.deps.auth0_validator.validate_m2m_token") as mock:
        mock.return_value = {
            "aud": "https://api.trigpointing.me/v1/",
            "client_id": "test_client_id",
            "azp": "test_client_id",
        }
        yield mock


def test_create_user_success(db: Session, mock_m2m_token):
    """Test successful user creation via POST endpoint."""
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "auth0_user_id": "auth0|newuser123",
    }

    response = client.post(
        "/v1/users",
        json=payload,
        headers={"Authorization": "Bearer mock_m2m_token"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["auth0_user_id"] == "auth0|newuser123"
    assert "id" in data


def test_create_user_invalid_token(db: Session):
    """Test that invalid M2M token returns 401."""
    with patch("app.api.deps.auth0_validator.validate_m2m_token") as mock:
        mock.return_value = None

        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "auth0_user_id": "auth0|test123",
        }

        response = client.post(
            "/v1/users",
            json=payload,
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401


def test_create_user_missing_token(db: Session):
    """Test that missing token returns 401."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "auth0_user_id": "auth0|test123",
    }

    response = client.post("/v1/users", json=payload)

    assert response.status_code == 401


def test_create_user_duplicate_username(db: Session, mock_m2m_token):
    """Test that duplicate username returns 409 with proper error message.

    This test verifies the error format that the Auth0 Action relies on
    to detect username collisions and retry with a different name.
    """
    # Create first user directly in DB
    create_user(
        db=db,
        username="duplicate",
        email="first@example.com",
        auth0_user_id="auth0|first123",
    )

    # Try to create second user with same username via API
    payload = {
        "username": "duplicate",
        "email": "second@example.com",
        "auth0_user_id": "auth0|second123",
    }

    response = client.post(
        "/v1/users",
        json=payload,
        headers={"Authorization": "Bearer mock_m2m_token"},
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    # Auth0 Action checks for "username" in the error message
    assert "username" in detail.lower()
    # Verify it includes the attempted username for debugging
    assert "duplicate" in detail.lower()


def test_create_user_duplicate_email(db: Session, mock_m2m_token):
    """Test that duplicate email returns 409."""
    # Create first user directly in DB
    create_user(
        db=db,
        username="user1",
        email="duplicate@example.com",
        auth0_user_id="auth0|user1",
    )

    # Try to create second user with same email via API
    payload = {
        "username": "user2",
        "email": "duplicate@example.com",
        "auth0_user_id": "auth0|user2",
    }

    response = client.post(
        "/v1/users",
        json=payload,
        headers={"Authorization": "Bearer mock_m2m_token"},
    )

    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


def test_create_user_duplicate_auth0_user_id(db: Session, mock_m2m_token):
    """Test that duplicate auth0_user_id returns 409."""
    # Create first user directly in DB
    create_user(
        db=db,
        username="user1",
        email="user1@example.com",
        auth0_user_id="auth0|duplicate",
    )

    # Try to create second user with same auth0_user_id via API
    payload = {
        "username": "user2",
        "email": "user2@example.com",
        "auth0_user_id": "auth0|duplicate",
    }

    response = client.post(
        "/v1/users",
        json=payload,
        headers={"Authorization": "Bearer mock_m2m_token"},
    )

    assert response.status_code == 409
    assert "auth0" in response.json()["detail"].lower()


def test_create_user_invalid_payload_missing_username(db: Session, mock_m2m_token):
    """Test that missing username returns 422."""
    payload = {
        "email": "test@example.com",
        "auth0_user_id": "auth0|test123",
    }

    response = client.post(
        "/v1/users",
        json=payload,
        headers={"Authorization": "Bearer mock_m2m_token"},
    )

    assert response.status_code == 422


def test_create_user_invalid_payload_missing_email(db: Session, mock_m2m_token):
    """Test that missing email returns 422."""
    payload = {
        "username": "testuser",
        "auth0_user_id": "auth0|test123",
    }

    response = client.post(
        "/v1/users",
        json=payload,
        headers={"Authorization": "Bearer mock_m2m_token"},
    )

    assert response.status_code == 422


def test_create_user_invalid_payload_missing_auth0_user_id(db: Session, mock_m2m_token):
    """Test that missing auth0_user_id returns 422."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
    }

    response = client.post(
        "/v1/users",
        json=payload,
        headers={"Authorization": "Bearer mock_m2m_token"},
    )

    assert response.status_code == 422


def test_create_user_empty_username(db: Session, mock_m2m_token):
    """Test that empty username returns 422."""
    payload = {
        "username": "",
        "email": "test@example.com",
        "auth0_user_id": "auth0|test123",
    }

    response = client.post(
        "/v1/users",
        json=payload,
        headers={"Authorization": "Bearer mock_m2m_token"},
    )

    assert response.status_code == 422


def test_create_user_database_error(db: Session, mock_m2m_token):
    """Test that database errors are handled gracefully."""
    with patch("app.crud.user.create_user") as mock_create:
        mock_create.side_effect = Exception("Database connection error")

        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "auth0_user_id": "auth0|test123",
        }

        response = client.post(
            "/v1/users",
            json=payload,
            headers={"Authorization": "Bearer mock_m2m_token"},
        )

        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()
