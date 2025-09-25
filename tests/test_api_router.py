"""
Tests for API router inclusion.
"""

from app.core.config import settings


def test_router_inclusion(client):
    # Use OpenAPI to verify routers are mounted without hitting the database
    resp = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "paths" in schema
    paths = schema["paths"].keys()
    assert f"{settings.API_V1_STR}/trigs/{{trig_id}}" in paths
    assert f"{settings.API_V1_STR}/photos/{{photo_id}}" in paths
