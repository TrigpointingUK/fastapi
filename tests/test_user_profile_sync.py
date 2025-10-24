"""
Tests for PATCH /v1/users/me with Auth0 sync logic.
"""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.crud.user import create_user
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture
def test_user_with_auth0(db: Session):
    """Create a test user with Auth0 ID."""
    user = create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        auth0_user_id="auth0|test123",
    )
    return user


@pytest.fixture
def mock_auth0_token(test_user_with_auth0):
    """Mock Auth0 token validation to return test user."""
    with patch("app.api.deps.auth0_validator.validate_auth0_token") as mock:
        mock.return_value = {
            "token_type": "auth0",
            "auth0_user_id": test_user_with_auth0.auth0_user_id,
            "sub": test_user_with_auth0.auth0_user_id,
            "scope": "api:write api:read-pii",
        }
        yield mock


def test_update_firstname_surname_no_sync(
    db: Session, test_user_with_auth0, mock_auth0_token
):
    """Test updating firstname/surname (database only, no Auth0 sync)."""
    with patch("app.services.auth0_service.auth0_service") as mock_service:
        payload = {
            "firstname": "John",
            "surname": "Doe",
        }

        response = client.patch(
            "/v1/users/me",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 200
        # Auth0 service should not be called for firstname/surname
        mock_service.update_user_profile.assert_not_called()
        mock_service.update_user_email.assert_not_called()


def test_update_name_syncs_to_auth0(
    db: Session, test_user_with_auth0, mock_auth0_token
):
    """Test updating name/nickname syncs to Auth0."""
    with patch("app.services.auth0_service.auth0_service") as mock_service:
        mock_service.update_user_profile.return_value = True

        payload = {
            "name": "newusername",
        }

        response = client.patch(
            "/v1/users/me",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 200
        # Auth0 service should be called to sync nickname
        mock_service.update_user_profile.assert_called_once_with(
            user_id="auth0|test123",
            nickname="newusername",
        )


def test_update_email_syncs_to_auth0(
    db: Session, test_user_with_auth0, mock_auth0_token
):
    """Test updating email syncs to Auth0."""
    with patch("app.services.auth0_service.auth0_service") as mock_service:
        mock_service.update_user_email.return_value = True

        payload = {
            "email": "newemail@example.com",
        }

        response = client.patch(
            "/v1/users/me",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 200
        # Auth0 service should be called to sync email
        mock_service.update_user_email.assert_called_once_with(
            user_id="auth0|test123",
            email="newemail@example.com",
        )


def test_update_name_duplicate_validation(
    db: Session, test_user_with_auth0, mock_auth0_token
):
    """Test that duplicate name is rejected."""
    # Create another user with different name
    create_user(
        db=db,
        username="existinguser",
        email="existing@example.com",
        auth0_user_id="auth0|existing123",
    )

    payload = {
        "name": "existinguser",  # Try to change to existing username
    }

    response = client.patch(
        "/v1/users/me",
        json=payload,
        headers={"Authorization": "Bearer mock_token"},
    )

    assert response.status_code == 409
    assert (
        "username" in response.json()["detail"].lower()
        or "taken" in response.json()["detail"].lower()
    )


def test_update_email_duplicate_validation(
    db: Session, test_user_with_auth0, mock_auth0_token
):
    """Test that duplicate email is rejected."""
    # Create another user with different email
    create_user(
        db=db,
        username="anotheruser",
        email="existing@example.com",
        auth0_user_id="auth0|another123",
    )

    payload = {
        "email": "existing@example.com",  # Try to change to existing email
    }

    response = client.patch(
        "/v1/users/me",
        json=payload,
        headers={"Authorization": "Bearer mock_token"},
    )

    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


def test_auth0_sync_failure_doesnt_fail_update(
    db: Session, test_user_with_auth0, mock_auth0_token
):
    """Test that Auth0 sync failure doesn't fail the database update."""
    with patch("app.services.auth0_service.auth0_service") as mock_service:
        # Mock Auth0 sync to fail
        mock_service.update_user_profile.return_value = False

        payload = {
            "name": "newnickname",
        }

        response = client.patch(
            "/v1/users/me",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        # Request should still succeed
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "newnickname"


def test_combined_updates_work(db: Session, test_user_with_auth0, mock_auth0_token):
    """Test that multiple fields can be updated at once."""
    with patch("app.services.auth0_service.auth0_service") as mock_service:
        mock_service.update_user_profile.return_value = True
        mock_service.update_user_email.return_value = True

        payload = {
            "name": "updatedname",
            "email": "updated@example.com",
            "firstname": "Updated",
            "surname": "User",
            "homepage": "https://example.com",
        }

        response = client.patch(
            "/v1/users/me",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 200
        # Both Auth0 syncs should be called
        mock_service.update_user_profile.assert_called_once()
        mock_service.update_user_email.assert_called_once()


def test_update_no_auth0_id_skips_sync(db: Session, mock_auth0_token):
    """Test that users without auth0_user_id skip Auth0 sync."""
    # Create user without auth0_user_id
    import secrets
    from datetime import date, datetime, time

    from app.models.user import User

    user = User(
        name="legacyuser",
        email="legacy@example.com",
        auth0_user_id=None,
        cryptpw=secrets.token_urlsafe(32),
        firstname="",
        surname="",
        email_valid="Y",
        email_ind="N",
        public_ind="N",
        homepage="",
        distance_ind="K",
        about="",
        status_max=0,
        crt_date=date.today(),
        crt_time=time(),
        upd_timestamp=datetime.now(),
        online_map_type="",
        online_map_type2="lla",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Mock token to return this user
    with patch("app.api.deps.auth0_validator.validate_auth0_token") as mock_token_val:
        mock_token_val.return_value = {
            "token_type": "auth0",
            "auth0_user_id": None,
            "sub": "legacy_sub",
        }

        with patch("app.api.deps.get_user_by_auth0_id") as mock_get_user:
            mock_get_user.return_value = user

            with patch("app.services.auth0_service.auth0_service") as mock_service:
                payload = {
                    "name": "newname",
                }

                _ = client.patch(
                    "/v1/users/me",
                    json=payload,
                    headers={"Authorization": "Bearer mock_token"},
                )

                # Auth0 sync should not be called
                mock_service.update_user_profile.assert_not_called()


def test_auth0_sync_exception_doesnt_fail_update(
    db: Session, test_user_with_auth0, mock_auth0_token
):
    """Test that Auth0 sync exception doesn't fail the database update."""
    with patch("app.services.auth0_service.auth0_service") as mock_service:
        # Mock Auth0 sync to raise exception
        mock_service.update_user_email.side_effect = Exception("Auth0 API error")

        payload = {
            "email": "newemail@example.com",
        }

        response = client.patch(
            "/v1/users/me",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        # Request should still succeed even when Auth0 sync fails
        assert response.status_code == 200

        # Verify database was updated despite Auth0 sync failure
        # Refresh the session to see committed changes from the endpoint
        db.expire_all()
        from app.crud.user import get_user_by_auth0_id

        user = get_user_by_auth0_id(db, test_user_with_auth0.auth0_user_id)
        assert user is not None
        assert user.email == "newemail@example.com"
