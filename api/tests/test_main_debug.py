"""
Tests for main application debug endpoints.
"""

# from api.core.security import create_access_token  # Legacy JWT removed
from fastapi.testclient import TestClient


def test_debug_auth_removed(client: TestClient):
    """Debug auth endpoint removed; should 404."""
    response = client.get("/debug/auth")
    assert response.status_code == 404


def test_debug_auth_invalid_token_removed(client: TestClient):
    response = client.get("/debug/auth", headers={"Authorization": "Bearer x"})
    assert response.status_code == 404


# def test_debug_auth_valid_token_removed(client: TestClient, test_admin_user):
#     from datetime import timedelta

#     access_token = create_access_token(
#         subject=test_admin_user.id, expires_delta=timedelta(minutes=30)
#     )
#     response = client.get(
#         "/debug/auth", headers={"Authorization": f"Bearer {access_token}"}
#     )
#     assert response.status_code == 404


# def test_debug_auth_expired_token_removed(client: TestClient, test_admin_user):
#     from datetime import timedelta

#     access_token = create_access_token(
#         subject=test_admin_user.id, expires_delta=timedelta(seconds=-3600)
#     )
#     response = client.get(
#         "/debug/auth", headers={"Authorization": f"Bearer {access_token}"}
#     )
#     assert response.status_code == 404


def test_debug_auth_malformed_token_removed(client: TestClient):
    response = client.get(
        "/debug/auth", headers={"Authorization": "Bearer not.a.valid.jwt"}
    )
    assert response.status_code == 404


def test_debug_auth_long_token_removed(client: TestClient):
    long_token = "a" * 100
    response = client.get(
        "/debug/auth", headers={"Authorization": f"Bearer {long_token}"}
    )
    assert response.status_code == 404


def test_debug_auth_short_token_removed(client: TestClient):
    short_token = "short"
    response = client.get(
        "/debug/auth", headers={"Authorization": f"Bearer {short_token}"}
    )
    assert response.status_code == 404
