"""
Covers async branch of trace_function with a stub xray recorder.
"""

import asyncio
import sys
from contextlib import contextmanager
from types import SimpleNamespace

from app.core.tracing import trace_function


class StubRecorder:
    def __init__(self):  # noqa: D401
        self.seg = object()

    def current_segment(self):  # noqa: D401
        return self.seg

    @contextmanager
    def in_subsegment(self, name):  # noqa: D401
        yield


def test_trace_function_async_branch(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    stub_core = SimpleNamespace(xray_recorder=StubRecorder())
    monkeypatch.setitem(sys.modules, "aws_xray_sdk.core", stub_core)

    @trace_function("async.branch")
    async def foo(x: int) -> int:
        await asyncio.sleep(0)
        return x + 7

    assert asyncio.run(foo(5)) == 12
