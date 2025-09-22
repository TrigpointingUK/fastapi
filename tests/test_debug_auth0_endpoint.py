"""
Coverage tests for /v1/debug/auth0 endpoint branches.
"""

from app.core.config import settings
from fastapi.testclient import TestClient


def test_debug_auth0_requires_auth(client: TestClient):
    r = client.get(f"{settings.API_V1_STR}/debug/auth0")
    assert r.status_code == 401
    assert "Authentication required" in r.json().get("detail", "")


def test_debug_auth0_invalid_token(client: TestClient):
    r = client.get(
        f"{settings.API_V1_STR}/debug/auth0",
        headers={"Authorization": "Bearer invalid"},
    )
    assert r.status_code == 401
    assert "Invalid token" in r.json().get("detail", "")
