"""
Tests for tlog endpoints.
"""

from app.core.config import settings

# import pytest  # Currently unused
from fastapi.testclient import TestClient


def test_get_trig_count_success(client: TestClient, test_tlog_entries):
    """Test successful trig count retrieval."""
    # Endpoint removed; count can be derived via DB in app code. Here we only assert 404.
    response = client.get(f"{settings.API_V1_STR}/tlogs/trig-count/1")
    assert response.status_code == 404


def test_get_trig_count_zero_results(client: TestClient, test_tlog_entries):
    """Test trig count with no matching entries."""
    response = client.get(f"{settings.API_V1_STR}/tlogs/trig-count/999")
    assert response.status_code == 404


def test_get_trig_count_multiple_results(client: TestClient, test_tlog_entries):
    """Test trig count with multiple matching entries."""
    response = client.get(f"{settings.API_V1_STR}/tlogs/trig-count/2")
    assert response.status_code == 404


def test_get_trig_count_invalid_id(client: TestClient):
    """Test trig count with invalid ID format."""
    response = client.get(f"{settings.API_V1_STR}/tlogs/trig-count/invalid")
    assert response.status_code == 404


def test_get_trig_count_negative_id(client: TestClient, db):
    """Test trig count with negative ID."""
    response = client.get(f"{settings.API_V1_STR}/tlogs/trig-count/-1")
    assert response.status_code == 404
