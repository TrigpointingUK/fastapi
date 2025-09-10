"""
Tests for persisting auth0_username alongside auth0_user_id and sanity check behaviour.
"""

import crypt
from unittest.mock import ANY, patch

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.user import update_user_auth0_mapping
from app.models.user import User
from fastapi.testclient import TestClient


def _make_user(
    db: Session, *, user_id: int, name: str, email: str, password: str
) -> User:
    cryptpw = crypt.crypt(password, "$1$testsalt$")
    user = User(
        id=user_id,
        name=name,
        firstname="Test",
        surname="User",
        email=email,
        cryptpw=cryptpw,
        admin_ind="N",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()
    return user


@patch("app.api.v1.endpoints.auth.update_user_auth0_mapping")
@patch("app.api.v1.endpoints.auth.auth0_service")
def test_login_persists_auth0_username(
    mock_auth0_service, mock_update_mapping, client: TestClient, db: Session
):
    # Arrange
    user = _make_user(
        db,
        user_id=4201,
        name="login_user",
        email="login@example.com",
        password="pw123456",
    )
    # Ensure legacy user has no auth0 linkage before
    assert user.auth0_user_id is None

    # Enable Auth0 and mock sync to return user id + username
    mock_auth0_service.sync_user_to_auth0.return_value = {
        "user_id": "auth0|abc123",
        "username": "login_user",
    }

    # Act
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "login@example.com", "password": "pw123456"},
    )

    # Assert
    assert response.status_code == 200
    mock_update_mapping.assert_called_once_with(
        db=ANY,
        user_id=4201,
        auth0_user_id="auth0|abc123",
        auth0_username="login_user",
    )


@patch("app.api.deps.update_user_auth0_mapping")
@patch("app.services.auth0_service.auth0_service")
@patch("app.api.deps.get_user_by_name")
@patch("app.api.deps.get_user_by_email")
@patch("app.api.deps.get_user_by_auth0_id")
@patch("app.api.deps.validate_any_token")
def test_deps_links_and_updates_username(
    mock_validate_token,
    mock_get_by_auth0,
    mock_get_by_email,
    mock_get_by_name,
    mock_auth0_service,
    mock_update_mapping,
    client: TestClient,
    db: Session,
):
    # Arrange: Token presents as Auth0 with given sub
    mock_validate_token.return_value = {
        "token_type": "auth0",
        "auth0_user_id": "auth0|xyz789",
    }
    mock_get_by_auth0.return_value = None  # Force fallback path

    # Create legacy user; Auth0 returns matching email & username
    user = _make_user(
        db,
        user_id=4202,
        name="deps_user",
        email="deps@example.com",
        password="pw123456",
    )
    mock_auth0_service.find_user_by_auth0_id.return_value = {
        "user_id": "auth0|xyz789",
        "email": "deps@example.com",
        "username": "deps_user",
        "nickname": "deps_user",
    }
    mock_get_by_email.return_value = user
    mock_get_by_name.return_value = None

    # Act
    headers = {"Authorization": "Bearer dummy"}
    response = client.get(f"{settings.API_V1_STR}/user/me", headers=headers)

    # Assert
    assert response.status_code == 200
    mock_update_mapping.assert_called_once_with(
        ANY,
        4202,
        "auth0|xyz789",
        "deps_user",
    )


def test_get_user_auth0_id_helper(db: Session):
    # Arrange: create user with mapping
    _make_user(
        db, user_id=4204, name="map_user", email="map@example.com", password="pw123456"
    )
    # Set mapping via CRUD
    ok = update_user_auth0_mapping(
        db=db,
        user_id=4204,
        auth0_user_id="auth0|map",
        auth0_username="map_user",
    )
    assert ok is True
    # Act/Assert: round-trip via getter
    from app.crud.user import get_user_auth0_id

    assert get_user_auth0_id(db, 4204) == "auth0|map"


def test_update_user_auth0_mapping_sanity_check_mismatch(caplog, db: Session):
    # Arrange: user name sanitizes to something else than provided auth0 username
    _make_user(
        db,
        user_id=4203,
        name="user name",
        email="mismatch@example.com",
        password="pw123456",
    )

    # Act
    with caplog.at_level("ERROR"):
        ok = update_user_auth0_mapping(
            db=db,
            user_id=4203,
            auth0_user_id="auth0|mismatch",
            auth0_username="different_sanitized",
        )

    # Assert: update succeeded but error logged for mismatch
    assert ok is True
    # Fetch back to confirm DB state
    refreshed = db.query(User).filter(User.id == 4203).first()
    assert refreshed.auth0_user_id == "auth0|mismatch"
    assert refreshed.auth0_username == "different_sanitized"
    assert any(
        "Auth0 username mismatch after sanitization" in rec.message
        for rec in caplog.records
    )


def test_update_user_auth0_mapping_user_not_found(monkeypatch):
    # Arrange: patch get_user_by_id to return None
    import app.crud.user as crud_user

    monkeypatch.setattr(crud_user, "get_user_by_id", lambda db, user_id: None)

    class FakeDB:
        def commit(self):
            pass

        def rollback(self):
            pass

    # Act
    # Also cover update_user_auth0_id not found
    from app.crud.user import update_user_auth0_id

    ok = update_user_auth0_mapping(
        db=FakeDB(),
        user_id=999999,
        auth0_user_id="auth0|none",
        auth0_username="who",
    )

    # Assert
    assert ok is False
    assert update_user_auth0_id(FakeDB(), 999999, "auth0|none") is False


def test_update_user_auth0_mapping_sanity_check_exception(monkeypatch, caplog):
    # Arrange: user exists, but sanitizer raises exception
    import app.crud.user as crud_user

    user = type(
        "U", (), {"name": "user name", "auth0_user_id": None, "auth0_username": None}
    )()
    monkeypatch.setattr(crud_user, "get_user_by_id", lambda db, user_id: user)
    monkeypatch.setattr(
        crud_user,
        "sanitize_username_for_auth0",
        lambda n: (_ for _ in ()).throw(ValueError("boom")),
    )

    class FakeDB:
        def commit(self):
            pass

        def rollback(self):
            pass

    with caplog.at_level("ERROR"):
        ok = update_user_auth0_mapping(
            db=FakeDB(),
            user_id=1,
            auth0_user_id="auth0|x",
            auth0_username="different",
        )
    assert ok is True
    assert user.auth0_user_id == "auth0|x"
    assert user.auth0_username == "different"
    assert any(
        "Auth0 username sanity check failed" in rec.message for rec in caplog.records
    )


def test_update_user_auth0_mapping_commit_fallback_success(monkeypatch, caplog):
    # Arrange: first commit raises, fallback commit succeeds
    import app.crud.user as crud_user

    user = type(
        "U", (), {"name": "user", "auth0_user_id": None, "auth0_username": None}
    )()
    monkeypatch.setattr(crud_user, "get_user_by_id", lambda db, user_id: user)

    class FakeDB:
        def __init__(self):
            self.calls = 0

        def commit(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("db error on first commit")

        def rollback(self):
            pass

    with caplog.at_level("WARNING"):
        ok = update_user_auth0_mapping(
            db=FakeDB(),
            user_id=1,
            auth0_user_id="auth0|y",
            auth0_username="user",
        )
    assert ok is True
    assert user.auth0_user_id == "auth0|y"
    assert user.auth0_username is None or user.auth0_username == "user"
    assert any("retrying with ID only" in rec.message for rec in caplog.records)


def test_update_user_auth0_mapping_commit_fallback_failure(monkeypatch, caplog):
    # Arrange: both initial and fallback commit raise
    import app.crud.user as crud_user

    user = type(
        "U", (), {"name": "user", "auth0_user_id": None, "auth0_username": None}
    )()
    monkeypatch.setattr(crud_user, "get_user_by_id", lambda db, user_id: user)

    class FakeDB:
        def commit(self):
            raise RuntimeError("always fails")

        def rollback(self):
            pass

    with caplog.at_level("ERROR"):
        ok = update_user_auth0_mapping(
            db=FakeDB(),
            user_id=1,
            auth0_user_id="auth0|z",
            auth0_username="user",
        )
    assert ok is False
    assert any("Auth0 mapping update failed" in rec.message for rec in caplog.records)


def test_update_user_auth0_mapping_success_path(db: Session):
    # Arrange: normal success path sets both fields and commits
    _make_user(
        db, user_id=4206, name="ok_user", email="ok@example.com", password="pw123456"
    )
    # Act
    ok = update_user_auth0_mapping(
        db=db,
        user_id=4206,
        auth0_user_id="auth0|ok",
        auth0_username="ok_user",
    )
    # Assert
    assert ok is True
    refreshed = db.query(User).filter(User.id == 4206).first()
    assert refreshed.auth0_user_id == "auth0|ok"
    assert refreshed.auth0_username == "ok_user"


@patch("app.api.deps.update_user_auth0_mapping")
@patch("app.services.auth0_service.auth0_service")
@patch("app.api.deps.get_user_by_name")
@patch("app.api.deps.get_user_by_email")
@patch("app.api.deps.get_user_by_auth0_id")
@patch("app.api.deps.validate_any_token")
def test_get_current_user_optional_links_and_updates_username(
    mock_validate_token,
    mock_get_by_auth0,
    mock_get_by_email,
    mock_get_by_name,
    mock_auth0_service,
    mock_update_mapping,
    db: Session,
):
    # Arrange
    class Cred:
        credentials = "dummy"

    mock_validate_token.return_value = {
        "token_type": "auth0",
        "auth0_user_id": "auth0|opt",
    }
    mock_get_by_auth0.return_value = None

    created = _make_user(
        db, user_id=4205, name="opt_user", email="opt@example.com", password="pw123456"
    )
    mock_auth0_service.find_user_by_auth0_id.return_value = {
        "user_id": "auth0|opt",
        "email": "opt@example.com",
        "username": "opt_user",
        "nickname": "opt_user",
    }
    mock_get_by_email.return_value = None
    mock_get_by_name.return_value = created

    from app.api.deps import get_current_user_optional

    # Act
    result = get_current_user_optional(db=db, credentials=Cred())

    # Assert
    assert result is created
    mock_update_mapping.assert_called_once_with(ANY, 4205, "auth0|opt", "opt_user")
