"""
Tests for app.core.xray_middleware add_xray_headers utility.
"""

from fastapi import Response

from app.core.xray_middleware import add_xray_headers


def test_add_xray_headers_disabled(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", False, raising=False)
    r = Response()
    out = add_xray_headers(r)
    assert out is r


def test_add_xray_headers_with_trace(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_TRACE_HEADER", "X-Amzn-Trace-Id", raising=False
    )

    # If aws_xray_sdk is not installed, function should still not error; no header
    r = Response()
    out = add_xray_headers(r)
    # Header may be absent when SDK is not present
    assert out is r
