"""
Covers adding X-Ray headers via middleware helper when SDK provides a trace id.
"""

from types import SimpleNamespace

from app.core.xray_middleware import add_xray_headers
from fastapi import Response


def test_add_xray_headers_with_stub_trace(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_TRACE_HEADER", "X-Amzn-Trace-Id", raising=False
    )

    # Stub xray_recorder.current_trace_id
    import sys

    stub = SimpleNamespace(current_trace_id="1-abcdef12-34567890abcdef12")
    monkeypatch.setitem(
        sys.modules, "aws_xray_sdk.core", SimpleNamespace(xray_recorder=stub)
    )

    r = Response()
    out = add_xray_headers(r)
    assert out.headers.get("X-Amzn-Trace-Id", "").startswith("Root=1-")
