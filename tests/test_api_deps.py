"""
Target coverage for app/api/deps.py require_scopes branches.
"""

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import require_scopes


def _build_app():
    app = FastAPI()
    r = APIRouter()

    @r.get("/scoped", dependencies=[Depends(require_scopes("user:admin"))])
    def scoped():
        return {"ok": True}

    app.include_router(r)
    return app


def test_require_scopes_auth0_missing_scope(monkeypatch):
    app = _build_app()
    c = TestClient(app)

    payload = {"token_type": "auth0", "permissions": ["trig:admin"], "sub": "auth0|u"}
    # Patch where the dependency resolves the symbol
    monkeypatch.setattr(
        "app.core.security.auth0_validator.validate_auth0_token", lambda t: payload
    )
    # No db user found
    monkeypatch.setattr(
        "app.api.deps.get_user_by_auth0_id", lambda db, auth0_user_id: None
    )

    res = c.get("/scoped", headers={"Authorization": "Bearer t"})
    assert res.status_code == 403
    assert "Missing required scope" in res.json().get("detail", "")
