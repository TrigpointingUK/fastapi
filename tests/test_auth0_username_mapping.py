"""
Tests for Auth0 user ID mapping behaviour. Auth0 usernames are no longer supported.
"""

from unittest.mock import ANY, patch

from fastapi.testclient import TestClient
from passlib.hash import md5_crypt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.user import update_user_auth0_mapping
from app.models.user import User


def _make_user(
    db: Session, *, user_id: int, name: str, email: str, password: str
) -> User:
    cryptpw = md5_crypt.using(salt="testsalt").hash(password)
    user = User(
        id=user_id,
        name=name,
        firstname="Test",
        surname="User",
        email=email,
        cryptpw=cryptpw,
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()
    return user


@patch("app.api.v1.endpoints.auth.update_user_auth0_mapping")
@patch("app.api.v1.endpoints.auth.auth0_service")
def test_login_persists_auth0_user_id(
    mock_auth0_service,
    mock_update_mapping,
    client: TestClient,
    db: Session,
    monkeypatch,
):
    # Arrange
    user = _make_user(
        db,
        user_id=4201,
        name="login_user",
        email="login@example.com",
        password="pw123456",
    )
    assert user.auth0_user_id is None

    # Mock sync to return user id only
    mock_auth0_service.sync_user_to_auth0.return_value = {
        "user_id": "auth0|abc123",
    }

    # Act
    response = client.post(
        f"{settings.API_V1_STR}/legacy/login",
        data={"username": "login@example.com", "password": "pw123456"},
    )

    # Assert
    assert response.status_code == 200
    mock_update_mapping.assert_called_once_with(
        db=ANY,
        user_id=4201,
        auth0_user_id="auth0|abc123",
    )


@patch("app.api.deps.update_user_auth0_mapping")
@patch("app.services.auth0_service.auth0_service")
@patch("app.api.deps.get_user_by_name")
@patch("app.api.deps.get_user_by_email")
@patch("app.api.deps.get_user_by_auth0_id")
@patch("app.core.security.auth0_validator.validate_auth0_token")
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

    # Create legacy user; Auth0 returns matching email
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
        "nickname": "deps_user",
        "name": "deps_user",
    }
    mock_get_by_email.return_value = user
    mock_get_by_name.return_value = None

    # Act
    headers = {"Authorization": "Bearer dummy"}
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)

    # Assert
    assert response.status_code == 200
    mock_update_mapping.assert_called_once_with(
        ANY,
        4202,
        "auth0|xyz789",
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
    )
    assert ok is True
    # Act/Assert: round-trip via getter
    from app.crud.user import get_user_auth0_id

    assert get_user_auth0_id(db, 4204) == "auth0|map"


def test_update_user_auth0_mapping_simple_update(db: Session):
    # Arrange
    _make_user(
        db,
        user_id=4203,
        name="user name",
        email="mismatch@example.com",
        password="pw123456",
    )

    # Act
    ok = update_user_auth0_mapping(
        db=db,
        user_id=4203,
        auth0_user_id="auth0|mismatch",
    )

    # Assert
    assert ok is True
    refreshed = db.query(User).filter(User.id == 4203).first()
    assert refreshed.auth0_user_id == "auth0|mismatch"


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
    )

    # Assert
    assert ok is False
    assert update_user_auth0_id(FakeDB(), 999999, "auth0|none") is False


def test_update_user_auth0_mapping_exception_does_not_crash(monkeypatch, caplog):
    # Arrange: user exists, but sanitizer raises exception
    import app.crud.user as crud_user

    user = type("U", (), {"name": "user name", "auth0_user_id": None})()
    monkeypatch.setattr(crud_user, "get_user_by_id", lambda db, user_id: user)
    # No sanitizer used anymore; force error at commit layer

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
        )
    assert ok is True
    assert user.auth0_user_id == "auth0|x"
    # Username fields are no longer tracked


# def test_update_user_auth0_mapping_commit_fallback_success(monkeypatch, caplog):
#     # Arrange: first commit raises, fallback commit succeeds
#     # This test is no longer relevant since fallback logic was removed
#     import app.crud.user as crud_user

#     user = type(
#         "U", (), {"name": "user", "auth0_user_id": None}
#     )()
#     monkeypatch.setattr(crud_user, "get_user_by_id", lambda db, user_id: user)

#     class FakeDB:
#         def __init__(self):
#             self.calls = 0

#         def commit(self):
#             self.calls += 1
#             if self.calls == 1:
#                 raise RuntimeError("db error on first commit")

#         def rollback(self):
#             pass

#     with caplog.at_level("WARNING"):
#         ok = update_user_auth0_mapping(
#             db=FakeDB(),
#             user_id=1,
#             auth0_user_id="auth0|y",
#         )
#     assert ok is True
#     assert user.auth0_user_id == "auth0|y"
#     # auth0_username field removed from User model
#     # Fallback retry logic removed


def test_update_user_auth0_mapping_commit_fallback_failure(monkeypatch, caplog):
    # Arrange: both initial and fallback commit raise
    import app.crud.user as crud_user

    user = type("U", (), {"name": "user", "auth0_user_id": None})()
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
    )
    # Assert
    assert ok is True
    refreshed = db.query(User).filter(User.id == 4206).first()
    assert refreshed.auth0_user_id == "auth0|ok"
    # Username fields are no longer tracked


@patch("app.api.deps.update_user_auth0_mapping")
@patch("app.services.auth0_service.auth0_service")
@patch("app.api.deps.get_user_by_name")
@patch("app.api.deps.get_user_by_email")
@patch("app.api.deps.get_user_by_auth0_id")
@patch("app.core.security.auth0_validator.validate_auth0_token")
def test_get_current_user_optional_links_and_updates_id(
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
        "nickname": "opt_user",
        "name": "opt_user",
    }
    mock_get_by_email.return_value = None
    mock_get_by_name.return_value = created

    from app.api.deps import get_current_user_optional

    # Act
    result = get_current_user_optional(db=db, credentials=Cred())

    # Assert
    assert result is created
    mock_update_mapping.assert_called_once_with(ANY, 4205, "auth0|opt")
