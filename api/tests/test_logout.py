"""Tests for the logout endpoint."""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_logout_redirects_to_auth0(client, monkeypatch):
    """Test that logout endpoint redirects to Auth0 logout URL."""
    # Mock Auth0 domain
    from api.core import config

    monkeypatch.setattr(config.settings, "AUTH0_CUSTOM_DOMAIN", "test-domain.auth0.com")
    monkeypatch.setattr(config.settings, "FASTAPI_URL", "https://api.test.com")
    monkeypatch.setattr(config.settings, "AUTH0_SPA_CLIENT_ID", "test-client-id")

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 307  # Temporary redirect
    assert "test-domain.auth0.com/v2/logout" in response.headers["location"]
    assert "client_id=test-client-id" in response.headers["location"]
    assert "returnTo=https://api.test.com/docs" in response.headers["location"]


def test_logout_uses_spa_client_id_when_available(client, monkeypatch):
    """Test that logout endpoint uses SPA client ID."""
    from api.core import config

    monkeypatch.setattr(config.settings, "AUTH0_CUSTOM_DOMAIN", "test-domain.auth0.com")
    monkeypatch.setattr(config.settings, "FASTAPI_URL", "https://api.test.com")
    monkeypatch.setattr(config.settings, "AUTH0_SPA_CLIENT_ID", "spa-client-id")

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 307
    assert "client_id=spa-client-id" in response.headers["location"]


def test_logout_fails_when_auth0_domain_not_configured(client, monkeypatch):
    """Test that logout endpoint returns 501 when AUTH0_CUSTOM_DOMAIN is not configured."""
    from api.core import config

    monkeypatch.setattr(config.settings, "AUTH0_CUSTOM_DOMAIN", None)

    response = client.get("/logout")

    assert response.status_code == 501
    assert "AUTH0_CUSTOM_DOMAIN not configured" in response.json()["detail"]


def test_logout_not_in_openapi_schema(client):
    """Test that logout endpoint is excluded from OpenAPI schema."""
    response = client.get("/v1/openapi.json")
    openapi_schema = response.json()

    # Check that /logout is not in the paths
    assert "/logout" not in openapi_schema.get("paths", {})
