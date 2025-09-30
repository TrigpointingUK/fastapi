"""
Hit the async decorator warning path.
"""

import asyncio
import sys
from types import SimpleNamespace

from app.core.tracing import trace_function


def test_async_trace_handles_exception(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)

    class _Rec:
        def current_segment(self):  # noqa: D401
            return object()

        def in_subsegment(self, name):  # noqa: D401
            raise RuntimeError("boom")

    monkeypatch.setitem(
        sys.modules, "aws_xray_sdk.core", SimpleNamespace(xray_recorder=_Rec())
    )

    @trace_function("async.err")
    async def foo(x):
        await asyncio.sleep(0)
        return x

    assert asyncio.run(foo(3)) == 3
