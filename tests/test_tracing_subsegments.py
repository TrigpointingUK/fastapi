"""
Additional tests for tracing helpers to improve diff coverage.
"""

import asyncio

from app.core import tracing

# pytest not used directly


def test_in_subsegment_safe_disabled(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", False, raising=False)
    with tracing.in_subsegment_safe("any.name"):
        # Should be a no-op
        x = 1 + 1
    assert x == 2


def test_in_subsegment_safe_no_current_segment(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)

    class DummyRecorder:
        def current_segment(self):  # noqa: D401
            return None

    # Monkeypatch module attribute accessed inside context manager
    monkeypatch.setitem(tracing.__dict__, "xray_recorder", DummyRecorder())

    with tracing.in_subsegment_safe("no.segment"):
        y = 3
    assert y == 3


def test_trace_function_async_wrapper_disabled(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", False, raising=False)

    @tracing.trace_function("async.test")
    async def foo(x: int) -> int:  # noqa: D401
        await asyncio.sleep(0)
        return x + 2

    out = asyncio.run(foo(3))
    assert out == 5
