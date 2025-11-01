"""
Coverage tests for /v1/debug/auth0 endpoint branches.
"""

from fastapi.testclient import TestClient

from api.core.config import settings


def test_debug_auth0_requires_auth(client: TestClient):
    r = client.get(f"{settings.API_V1_STR}/debug/auth0")
    assert r.status_code == 401
    assert "Authentication required" in r.json().get("detail", "")


def test_debug_auth0_invalid_token(client: TestClient, monkeypatch):
    # Ensure validator returns None to simulate invalid token
    monkeypatch.setattr(
        "api.core.security.auth0_validator.validate_auth0_token",
        lambda t: None,
        raising=False,
    )
    r = client.get(
        f"{settings.API_V1_STR}/debug/auth0",
        headers={"Authorization": "Bearer invalid"},
    )
    assert r.status_code == 401
    assert "Invalid token" in r.json().get("detail", "")


def test_debug_auth0_valid_token_with_db_user(client: TestClient, monkeypatch):
    # Simulate valid auth0 token and existing DB user
    token_payload = {"token_type": "auth0", "sub": "auth0|xyz", "email": "e@test"}
    # Patch where the endpoint imports it
    monkeypatch.setattr(
        "api.core.security.auth0_validator.validate_auth0_token",
        lambda t: token_payload,
        raising=False,
    )

    class U:
        id = 7
        name = "dbuser"
        email = "e@test"

    monkeypatch.setattr(
        "api.api.v1.endpoints.debug.get_user_by_auth0_id", lambda db, auth0_user_id: U()
    )

    r = client.get(
        f"{settings.API_V1_STR}/debug/auth0",
        headers={"Authorization": "Bearer good"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["database_user_found"] is True
    assert data["database_user_id"] == 7
