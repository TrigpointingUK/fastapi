"""
Tests for API router configuration.
"""

from app.core.config import settings
from fastapi.testclient import TestClient


def test_username_analysis_router_included(client: TestClient):
    """Test that username analysis router is included in the API."""
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema

    # Check that username analysis endpoints are present
    username_analysis_endpoints = [
        f"{settings.API_V1_STR}/legacy/username-duplicates",
        f"{settings.API_V1_STR}/legacy/email-duplicates",
    ]

    for endpoint in username_analysis_endpoints:
        assert endpoint in schema["paths"]
        assert "get" in schema["paths"][endpoint]


def test_username_analysis_endpoints_have_correct_tags(client: TestClient):
    """Test that username analysis endpoints have correct tags."""
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200

    schema = response.json()

    # Check username-duplicates endpoint
    username_endpoint = schema["paths"][
        f"{settings.API_V1_STR}/legacy/username-duplicates"
    ]["get"]
    assert "tags" in username_endpoint
    assert "legacy" in username_endpoint["tags"]

    # Check email-duplicates endpoint
    email_endpoint = schema["paths"][f"{settings.API_V1_STR}/legacy/email-duplicates"][
        "get"
    ]
    assert "tags" in email_endpoint
    assert "legacy" in email_endpoint["tags"]


def test_username_analysis_endpoints_have_security(client: TestClient):
    """Test that username analysis endpoints have security requirements."""
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200

    schema = response.json()

    # Check username-duplicates endpoint
    username_endpoint = schema["paths"][
        f"{settings.API_V1_STR}/legacy/username-duplicates"
    ]["get"]
    assert "security" in username_endpoint
    assert username_endpoint["security"] == [
        {"OAuth2": ["openid", "profile", "user:admin"]}
    ]

    # Check email-duplicates endpoint
    email_endpoint = schema["paths"][f"{settings.API_V1_STR}/legacy/email-duplicates"][
        "get"
    ]
    assert "security" in email_endpoint
    assert email_endpoint["security"] == [
        {"OAuth2": ["openid", "profile", "user:admin"]}
    ]


def test_username_analysis_endpoints_have_parameters(client: TestClient):
    """Test that email-duplicates endpoint has pagination parameters."""
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200

    schema = response.json()

    # Check email-duplicates endpoint has limit and offset parameters
    email_endpoint = schema["paths"][f"{settings.API_V1_STR}/legacy/email-duplicates"][
        "get"
    ]
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
