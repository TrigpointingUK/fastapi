"""
Tests for app.core.security utilities focusing on legacy tokens and scopes.
"""

from datetime import timedelta

from app.core import security


def test_legacy_token_validate_success(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.AUTH0_ENABLED", False, raising=False)
    token = security.create_access_token(
        subject=123, expires_delta=timedelta(minutes=5)
    )
    payload = security.validate_legacy_jwt_token(token)
    assert payload is not None
    assert int(payload["sub"]) == 123


def test_legacy_token_validate_invalid():
    assert security.validate_legacy_jwt_token("not-a-token") is None


def test_extract_scopes():
    assert security.extract_scopes({"scope": "user:admin trig:admin"}) == {
        "user:admin",
        "trig:admin",
    }
    assert security.extract_scopes({"permissions": ["a", "b"]}) == {"a", "b"}
    assert security.extract_scopes({}) == set()
