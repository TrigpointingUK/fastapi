"""
Tests for API router configuration.
"""

from fastapi.testclient import TestClient


def test_username_analysis_router_included(client: TestClient):
    """Test that username analysis router is included in the API."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema

    # Check that username analysis endpoints are present
    username_analysis_endpoints = [
        "/api/v1/analysis/username-duplicates",
        "/api/v1/analysis/email-duplicates",
    ]

    for endpoint in username_analysis_endpoints:
        assert endpoint in schema["paths"]
        assert "get" in schema["paths"][endpoint]


def test_username_analysis_endpoints_have_correct_tags(client: TestClient):
    """Test that username analysis endpoints have correct tags."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()

    # Check username-duplicates endpoint
    username_endpoint = schema["paths"]["/api/v1/analysis/username-duplicates"]["get"]
    assert "tags" in username_endpoint
    assert "username-analysis" in username_endpoint["tags"]

    # Check email-duplicates endpoint
    email_endpoint = schema["paths"]["/api/v1/analysis/email-duplicates"]["get"]
    assert "tags" in email_endpoint
    assert "username-analysis" in email_endpoint["tags"]


def test_username_analysis_endpoints_have_security(client: TestClient):
    """Test that username analysis endpoints have security requirements."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()

    # Check username-duplicates endpoint
    username_endpoint = schema["paths"]["/api/v1/analysis/username-duplicates"]["get"]
    assert "security" in username_endpoint
    assert username_endpoint["security"] == [{"BearerAuth": []}]

    # Check email-duplicates endpoint
    email_endpoint = schema["paths"]["/api/v1/analysis/email-duplicates"]["get"]
    assert "security" in email_endpoint
    assert email_endpoint["security"] == [{"BearerAuth": []}]


def test_username_analysis_endpoints_have_parameters(client: TestClient):
    """Test that email-duplicates endpoint has pagination parameters."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()

    # Check email-duplicates endpoint has limit and offset parameters
    email_endpoint = schema["paths"]["/api/v1/analysis/email-duplicates"]["get"]
    assert "parameters" in email_endpoint

    param_names = [param["name"] for param in email_endpoint["parameters"]]
    assert "limit" in param_names
    assert "offset" in param_names

    # Check parameter details
    for param in email_endpoint["parameters"]:
        if param["name"] == "limit":
            assert param["in"] == "query"
            assert param["required"] is False
            assert param["schema"]["default"] == 50
        elif param["name"] == "offset":
            assert param["in"] == "query"
            assert param["required"] is False
            assert param["schema"]["default"] == 0
