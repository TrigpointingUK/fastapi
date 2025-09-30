"""
Tests for app.core.tracing utilities.
"""

from app.core import tracing


def test_setup_xray_tracing_disabled(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", False, raising=False)
    assert tracing.setup_xray_tracing() is False


def test_setup_xray_tracing_import_error(monkeypatch):
    # With XRAY disabled, function should return False (CI environment)
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", False, raising=False)
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


def test_setup_xray_tracing_enabled(monkeypatch):
    # Exercise configure path when enabled
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    # Provide stub core module with xray_recorder having configure()
    import sys
    from types import SimpleNamespace

    class _Stub:
        def __init__(self):
            self.called = False

        def configure(self, **kwargs):  # noqa: D401
            self.called = True

    stub = _Stub()
    monkeypatch.setitem(
        sys.modules,
        "aws_xray_sdk.core",
        SimpleNamespace(xray_recorder=stub, patch=lambda libs: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "aws_xray_sdk.core.async_context",
        SimpleNamespace(AsyncContext=object),
    )
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_SERVICE_NAME", "test-service", raising=False
    )
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_DAEMON_ADDRESS",
        "127.0.0.1:2000",
        raising=False,
    )
    assert tracing.setup_xray_tracing() is True
