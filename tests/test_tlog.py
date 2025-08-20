"""
Tests for tlog endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_get_trig_count_success(client: TestClient, test_tlog_entries):
    """Test successful trig count retrieval."""
    response = client.get(f"{settings.API_V1_STR}/tlog/trig-count/1")
    assert response.status_code == 200
    data = response.json()
    assert data["trig_id"] == 1
    assert data["count"] == 3


def test_get_trig_count_zero_results(client: TestClient, test_tlog_entries):
    """Test trig count with no matching entries."""
    response = client.get(f"{settings.API_V1_STR}/tlog/trig-count/999")
    assert response.status_code == 200
    data = response.json()
    assert data["trig_id"] == 999
    assert data["count"] == 0


def test_get_trig_count_multiple_results(client: TestClient, test_tlog_entries):
    """Test trig count with multiple matching entries."""
    response = client.get(f"{settings.API_V1_STR}/tlog/trig-count/2")
    assert response.status_code == 200
    data = response.json()
    assert data["trig_id"] == 2
    assert data["count"] == 2


def test_get_trig_count_invalid_id(client: TestClient):
    """Test trig count with invalid ID format."""
    response = client.get(f"{settings.API_V1_STR}/tlog/trig-count/invalid")
    assert response.status_code == 422  # Validation error


def test_get_trig_count_negative_id(client: TestClient):
    """Test trig count with negative ID."""
    response = client.get(f"{settings.API_V1_STR}/tlog/trig-count/-1")
    assert response.status_code == 200
    data = response.json()
    assert data["trig_id"] == -1
    assert data["count"] == 0
