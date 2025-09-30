"""
Test to cover the import inspect line in trace_function decorator (line 186).
"""

import sys
from contextlib import contextmanager
from types import SimpleNamespace

from app.core.tracing import trace_function


class StubRecorder:
    """Stub X-Ray recorder for testing."""

    def __init__(self):  # noqa: D401
        self.seg = object()

    def current_segment(self):  # noqa: D401
        return self.seg

    @contextmanager
    def in_subsegment(self, name):  # noqa: D401
        yield


def test_trace_function_decorator_inspects_function(monkeypatch):
    """Test that trace_function decorator executes import inspect line."""
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    stub_core = SimpleNamespace(xray_recorder=StubRecorder())
    monkeypatch.setitem(sys.modules, "aws_xray_sdk.core", stub_core)

    # Decorate a synchronous function - this should execute the inspect.iscoroutinefunction check
    @trace_function("test.sync.function")
    def sync_func(x: int) -> int:
        return x * 2

    # Call the function to ensure decorator is fully applied
    result = sync_func(5)
    assert result == 10
