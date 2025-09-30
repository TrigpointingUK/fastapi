"""
Tests for profiling middleware.
"""

from unittest.mock import patch

import pytest

from app.core.profiling import ProfilingMiddleware, should_enable_profiling
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_profiling():
    """Create a test FastAPI app with profiling enabled."""
    app = FastAPI()
    app.add_middleware(ProfilingMiddleware, default_format="html")

    @app.get("/test")
    def test_endpoint():
        # Simulate some work
        result = sum(range(1000))
        return {"result": result}

    @app.get("/slow")
    def slow_endpoint():
        # Simulate slower work
        result = sum(range(100000))
        return {"result": result}

    return app


def test_profiling_disabled_by_default(app_with_profiling):
    """Test that profiling is not enabled without query parameter."""
    client = TestClient(app_with_profiling)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/json"
    assert "result" in response.json()


def test_profiling_html_output(app_with_profiling):
    """Test profiling with HTML output."""
    client = TestClient(app_with_profiling)
    response = client.get("/test?profile=1")

    assert response.status_code == 200
    assert response.headers.get("content-type") == "text/html; charset=utf-8"
    assert response.headers.get("X-Profile-Format") == "html"
    assert b"<!DOCTYPE html>" in response.content or b"<html" in response.content


def test_profiling_html_explicit(app_with_profiling):
    """Test profiling with explicit HTML format."""
    client = TestClient(app_with_profiling)
    response = client.get("/test?profile=html")

    assert response.status_code == 200
    assert response.headers.get("content-type") == "text/html; charset=utf-8"
    assert response.headers.get("X-Profile-Format") == "html"


def test_profiling_speedscope_output(app_with_profiling):
    """Test profiling with speedscope JSON output."""
    client = TestClient(app_with_profiling)
    response = client.get("/test?profile=speedscope")

    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/json"
    assert response.headers.get("X-Profile-Format") == "speedscope"
    assert (
        response.headers.get("Content-Disposition")
        == 'attachment; filename="profile.speedscope.json"'
    )

    # Verify it's valid JSON
    data = response.json()
    assert isinstance(data, dict)
    # Speedscope format has specific structure
    assert "$schema" in data or "shared" in data


def test_profiling_speedscope_json_alias(app_with_profiling):
    """Test profiling with 'json' as alias for speedscope."""
    client = TestClient(app_with_profiling)
    response = client.get("/test?profile=json")

    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/json"
    assert response.headers.get("X-Profile-Format") == "speedscope"


def test_profiling_various_parameter_values(app_with_profiling):
    """Test profiling with various parameter values for HTML."""
    client = TestClient(app_with_profiling)

    # Test various truthy values
    for value in ["1", "true", "yes", "html"]:
        response = client.get(f"/test?profile={value}")
        assert response.status_code == 200
        assert response.headers.get("X-Profile-Format") == "html"


def test_profiling_default_format():
    """Test profiling with custom default format."""
    app = FastAPI()
    app.add_middleware(ProfilingMiddleware, default_format="speedscope")

    @app.get("/test")
    def test_endpoint():
        return {"result": 123}

    client = TestClient(app)
    response = client.get("/test?profile=unknown")

    # Should use default format (speedscope) for unrecognised parameter
    assert response.status_code == 200
    assert response.headers.get("X-Profile-Format") == "speedscope"


def test_should_enable_profiling_development():
    """Test profiling is enabled in development."""
    assert should_enable_profiling("development") is True
    assert should_enable_profiling("Development") is True
    assert should_enable_profiling("DEVELOPMENT") is True


def test_should_enable_profiling_staging():
    """Test profiling is enabled in staging."""
    assert should_enable_profiling("staging") is True
    assert should_enable_profiling("Staging") is True
    assert should_enable_profiling("STAGING") is True


def test_should_enable_profiling_local():
    """Test profiling is enabled in local."""
    assert should_enable_profiling("local") is True
    assert should_enable_profiling("Local") is True
    assert should_enable_profiling("LOCAL") is True


def test_should_enable_profiling_production():
    """Test profiling is disabled in production."""
    assert should_enable_profiling("production") is False
    assert should_enable_profiling("Production") is False
    assert should_enable_profiling("PRODUCTION") is False


def test_should_enable_profiling_unknown():
    """Test profiling is disabled for unknown environments."""
    assert should_enable_profiling("unknown") is False
    assert should_enable_profiling("prod") is False
    assert should_enable_profiling("") is False


def test_profiling_with_slow_endpoint(app_with_profiling):
    """Test profiling captures data from slower endpoints."""
    client = TestClient(app_with_profiling)
    response = client.get("/slow?profile=html")

    assert response.status_code == 200
    assert response.headers.get("X-Profile-Format") == "html"
    # Should contain profiling data
    assert len(response.content) > 1000  # HTML profiling output is substantial


def test_profiling_error_handling():
    """Test profiling handles errors gracefully."""
    app = FastAPI()

    # Mock the profiler to raise an exception during output
    with patch("app.core.profiling.Profiler") as mock_profiler:
        mock_instance = mock_profiler.return_value
        mock_instance.output_html.side_effect = Exception("Profiler error")

        app.add_middleware(ProfilingMiddleware)

        @app.get("/test")
        def test_endpoint():
            return {"result": 123}

        client = TestClient(app)
        # Should not crash, should return original response
        response = client.get("/test?profile=1")

        # Should fall back to returning the original response
        assert response.status_code == 200
