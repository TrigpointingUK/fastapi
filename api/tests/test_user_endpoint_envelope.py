"""
Small coverage bump for user endpoint include parsing branches.
"""

from fastapi.testclient import TestClient

from api.core.config import settings


def test_get_user_bad_include(client: TestClient, monkeypatch):
    # Avoid hitting the real DB by patching CRUD function to return None
    monkeypatch.setattr(
        "api.api.v1.endpoints.users.user_crud.get_user_by_id", lambda db, user_id: None
    )
    res = client.get(f"{settings.API_V1_STR}/users/123?include=unknown")
    assert res.status_code in (400, 404)
