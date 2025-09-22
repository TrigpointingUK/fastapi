"""
Tests for app.core.tracing utilities.
"""

from app.core import tracing


def test_setup_xray_tracing_disabled(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", False, raising=False)
    assert tracing.setup_xray_tracing() is False


def test_setup_xray_tracing_import_error(monkeypatch):
    # With XRAY enabled but sdk not installed, function should return False
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    assert tracing.setup_xray_tracing() is False


def test_get_trace_id_no_xray():
    # Without sdk, get_trace_id should return None gracefully
    assert tracing.get_trace_id() is None


def test_trace_function_disabled(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", False, raising=False)

    calls = {}

    @tracing.trace_function("name")
    def foo(x):  # noqa: ANN001
        calls["ran"] = True
        return x + 1

    assert foo(1) == 2
    assert calls.get("ran") is True
