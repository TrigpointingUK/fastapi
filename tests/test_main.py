"""
Tests for main application endpoints.
"""

from app.core.config import settings
from fastapi.testclient import TestClient


def test_health_check(client: TestClient, db):
    """Test health check endpoint with database connectivity."""
    # db fixture ensures tables are created
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == settings.ENVIRONMENT
    assert "version" in data
    assert "build_time" in data
    assert data["database"] == "connected"


def test_health_check_database_failure():
    """Test health check endpoint returns 503 when database is unavailable."""
    from app.db.database import get_db
    from app.main import app
    from fastapi.testclient import TestClient

    # Create a mock database session that will fail on execute
    class FailingSession:
        def execute(self, *args, **kwargs):
            raise Exception("Database connection failed")

        def close(self):
            pass

    # Override get_db to return a failing session
    def failing_get_db():
        try:
            yield FailingSession()
        finally:
            pass

    # Save original override and apply failing one
    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = failing_get_db

    try:
        with TestClient(app) as test_client:
            response = test_client.get("/health")
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["status"] == "unhealthy"
            assert data["detail"]["database"] == "error"
            assert "error" in data["detail"]
    finally:
        # Restore original override
        if original_override:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_openapi_docs(client: TestClient):
    """Test that OpenAPI docs are accessible."""
    response = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
