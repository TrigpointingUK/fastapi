"""
Tests for API router inclusion.
"""

from api.core.config import settings


def test_router_inclusion(client):
    # Use OpenAPI to verify routers are mounted without hitting the database
    resp = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "paths" in schema
    paths = schema["paths"].keys()
    assert f"{settings.API_V1_STR}/trigs/{{trig_id}}" in paths
    assert f"{settings.API_V1_STR}/photos/{{photo_id}}" in paths
    # new routes
    assert f"{settings.API_V1_STR}/logs" in paths
    assert f"{settings.API_V1_STR}/logs/{{log_id}}" in paths
    assert f"{settings.API_V1_STR}/trigs/{{trig_id}}/logs" in paths
    assert f"{settings.API_V1_STR}/trigs/{{trig_id}}/photos" in paths
    assert f"{settings.API_V1_STR}/users/{{user_id}}/logs" in paths
    assert f"{settings.API_V1_STR}/users/{{user_id}}/photos" in paths
