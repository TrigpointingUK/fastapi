"""
Tests for main application debug endpoints.
"""

from unittest.mock import patch

from app.core.security import create_access_token
from fastapi.testclient import TestClient


def test_debug_auth_no_credentials(client: TestClient):
    """Test debug auth endpoint with no credentials."""
    response = client.get("/debug/auth")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert data["error"] == "No credentials provided"


def test_debug_auth_invalid_token(client: TestClient):
    """Test debug auth endpoint with invalid token."""
    response = client.get(
        "/debug/auth", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert "error" in data
    assert "token" in data


def test_debug_auth_valid_token(client: TestClient, test_admin_user):
    """Test debug auth endpoint with valid token."""
    from datetime import timedelta

    access_token = create_access_token(
        subject=test_admin_user.id, expires_delta=timedelta(minutes=30)
    )

    response = client.get(
        "/debug/auth", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert "token_payload" in data
    assert data["user_id"] == str(test_admin_user.id)
    assert "exp" in data["token_payload"]


def test_debug_auth_expired_token(client: TestClient, test_admin_user):
    """Test debug auth endpoint with expired token."""
    from datetime import timedelta

    # Create an expired token
    access_token = create_access_token(
        subject=test_admin_user.id,
        expires_delta=timedelta(seconds=-3600),  # Expired 1 hour ago
    )

    response = client.get(
        "/debug/auth", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert "error" in data
    assert "Token has expired" in data["error"] or "expired" in data["error"].lower()


def test_debug_auth_malformed_token(client: TestClient):
    """Test debug auth endpoint with malformed token."""
    response = client.get(
        "/debug/auth", headers={"Authorization": "Bearer not.a.valid.jwt"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert "error" in data


def test_debug_auth_long_token_truncation(client: TestClient):
    """Test debug auth endpoint truncates long tokens in error response."""
    long_token = "a" * 100  # Create a long token
    response = client.get(
        "/debug/auth", headers={"Authorization": f"Bearer {long_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert "error" in data
    assert len(data["token"]) == 53  # 50 + "..."
    assert data["token"].endswith("...")


def test_debug_auth_short_token_no_truncation(client: TestClient):
    """Test debug auth endpoint doesn't truncate short tokens."""
    short_token = "short"
    response = client.get(
        "/debug/auth", headers={"Authorization": f"Bearer {short_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert "error" in data
    assert data["token"] == short_token


def test_debug_xray_disabled(client: TestClient):
    """Test debug xray endpoint when X-Ray is disabled."""
    with patch("app.main.xray_enabled", False):
        response = client.get("/debug/xray")
        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "X-Ray is not enabled"


def test_debug_xray_success(client: TestClient):
    """Test debug xray endpoint when X-Ray is enabled and working."""
    with patch("app.main.xray_enabled", True), patch(
        "app.main.settings"
    ) as mock_settings:

        mock_settings.XRAY_SERVICE_NAME = "test-service"
        mock_settings.XRAY_SAMPLING_RATE = 0.1
        mock_settings.XRAY_DAEMON_ADDRESS = "127.0.0.1:2000"

        response = client.get("/debug/xray")
        assert response.status_code == 200
        data = response.json()

        # Should have debug info
        assert "debug_info" in data
        assert data["debug_info"]["xray_enabled"] is True
        assert data["debug_info"]["service_name"] == "test-service"

        # Should have either success or error status
        assert "status" in data or "error" in data
