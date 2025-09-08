"""
Tests for custom OpenAPI configuration.
"""

from fastapi.testclient import TestClient


def test_openapi_schema_has_security_schemes(client: TestClient):
    """Test that OpenAPI schema includes BearerAuth security scheme."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "BearerAuth" in schema["components"]["securitySchemes"]

    bearer_auth = schema["components"]["securitySchemes"]["BearerAuth"]
    assert bearer_auth["type"] == "http"
    assert bearer_auth["scheme"] == "bearer"
    assert bearer_auth["bearerFormat"] == "JWT"


def test_openapi_schema_has_security_requirements(client: TestClient):
    """Test that OpenAPI schema includes security requirements on protected endpoints."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema

    # Check that protected endpoints have security requirements
    protected_endpoints = [
        "/api/v1/analysis/username-duplicates",
        "/api/v1/analysis/email-duplicates",
        "/api/v1/user/me",
        "/api/v1/users/email/{user_id}",
    ]

    for endpoint_path in protected_endpoints:
        if endpoint_path in schema["paths"]:
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in schema["paths"][endpoint_path]:
                    endpoint = schema["paths"][endpoint_path][method]
                    assert "security" in endpoint
                    assert endpoint["security"] == [{"BearerAuth": []}]


def test_openapi_schema_public_endpoints_no_security(client: TestClient):
    """Test that public endpoints don't have security requirements."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema

    # Check that public endpoints don't have security requirements
    public_endpoints = [
        "/health",
        "/debug/auth",  # This one is special - it has optional auth
        "/api/v1/auth/login",
    ]

    for endpoint_path in public_endpoints:
        if endpoint_path in schema["paths"]:
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in schema["paths"][endpoint_path]:
                    endpoint = schema["paths"][endpoint_path][method]
                    # Public endpoints should not have security requirements
                    # (except debug/auth which has optional auth)
                    if endpoint_path != "/debug/auth":
                        assert "security" not in endpoint


def test_openapi_schema_metadata(client: TestClient):
    """Test that OpenAPI schema has correct metadata."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert schema["info"]["title"] == "Legacy API Migration"
    assert schema["info"]["version"] == "1.0.0"
    assert (
        "Legacy API Migration with JWT Authentication" in schema["info"]["description"]
    )


def test_openapi_schema_cached(client: TestClient):
    """Test that OpenAPI schema is properly cached."""
    # First request
    response1 = client.get("/api/v1/openapi.json")
    assert response1.status_code == 200

    # Second request should return the same cached schema
    response2 = client.get("/api/v1/openapi.json")
    assert response2.status_code == 200

    # Both responses should be identical
    assert response1.json() == response2.json()
