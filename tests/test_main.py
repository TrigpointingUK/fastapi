"""
Tests for main application endpoints.
"""

from app.core.config import settings

# import pytest  # Currently unused
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == settings.ENVIRONMENT
    assert "version" in data
    assert "build_time" in data


def test_openapi_docs(client: TestClient):
    """Test that OpenAPI docs are accessible."""
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
