"""
Tests for PII scope authorization (api:read-pii).
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.crud.user import create_user
from api.main import app

client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        auth0_user_id="auth0|test123",
    )
    return user


def test_update_pii_without_scope_returns_403(db: Session, test_user):
    """Test that updating PII fields without api:read-pii scope returns 403."""
    with patch("api.api.deps.auth0_validator.validate_auth0_token") as mock:
        # Mock token WITHOUT api:read-pii scope
        mock.return_value = {
            "token_type": "auth0",
            "auth0_user_id": test_user.auth0_user_id,
            "sub": test_user.auth0_user_id,
            "scope": "api:write",  # Missing api:read-pii
        }

        # Try to update email
        response = client.patch(
            "/v1/users/me",
            json={"email": "newemail@example.com"},
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 403
        assert "api:read-pii" in response.json()["detail"]


def test_update_firstname_without_scope_returns_403(db: Session, test_user):
    """Test that updating firstname without api:read-pii scope returns 403."""
    with patch("api.api.deps.auth0_validator.validate_auth0_token") as mock:
        mock.return_value = {
            "token_type": "auth0",
            "auth0_user_id": test_user.auth0_user_id,
            "sub": test_user.auth0_user_id,
            "scope": "api:write",
        }

        response = client.patch(
            "/v1/users/me",
            json={"firstname": "John"},
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 403
        assert "api:read-pii" in response.json()["detail"]


def test_update_surname_without_scope_returns_403(db: Session, test_user):
    """Test that updating surname without api:read-pii scope returns 403."""
    with patch("api.api.deps.auth0_validator.validate_auth0_token") as mock:
        mock.return_value = {
            "token_type": "auth0",
            "auth0_user_id": test_user.auth0_user_id,
            "sub": test_user.auth0_user_id,
            "scope": "api:write",
        }

        response = client.patch(
            "/v1/users/me",
            json={"surname": "Doe"},
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 403
        assert "api:read-pii" in response.json()["detail"]


def test_update_non_pii_fields_without_pii_scope_succeeds(db: Session, test_user):
    """Test that updating non-PII fields works without api:read-pii scope."""
    with patch("api.api.deps.auth0_validator.validate_auth0_token") as mock:
        mock.return_value = {
            "token_type": "auth0",
            "auth0_user_id": test_user.auth0_user_id,
            "sub": test_user.auth0_user_id,
            "scope": "api:write",  # No api:read-pii needed for non-PII fields
        }

        with patch("api.services.auth0_service.auth0_service") as mock_service:
            mock_service.update_user_profile.return_value = True

            response = client.patch(
                "/v1/users/me",
                json={"name": "newusername", "homepage": "https://example.com"},
                headers={"Authorization": "Bearer mock_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "newusername"
            assert data["homepage"] == "https://example.com"


def test_update_pii_with_scope_succeeds(db: Session, test_user):
    """Test that updating PII fields with api:read-pii scope succeeds."""
    with patch("api.api.deps.auth0_validator.validate_auth0_token") as mock:
        mock.return_value = {
            "token_type": "auth0",
            "auth0_user_id": test_user.auth0_user_id,
            "sub": test_user.auth0_user_id,
            "scope": "api:write api:read-pii",  # Has required scope
        }

        with patch("api.services.auth0_service.auth0_service") as mock_service:
            mock_service.update_user_email.return_value = True

            response = client.patch(
                "/v1/users/me",
                json={"email": "newemail@example.com"},
                headers={"Authorization": "Bearer mock_token"},
            )

            assert response.status_code == 200
            # Email field may not be in response if it's excluded by default
            # but the update should have succeeded
