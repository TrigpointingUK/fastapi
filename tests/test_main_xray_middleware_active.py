"""
Exercise the X-Ray middleware happy path with a stub recorder to raise diff coverage.
"""

import sys
from contextlib import contextmanager
from importlib import reload
from types import SimpleNamespace

from starlette.testclient import TestClient


class DummySegment:
    def __init__(self):  # noqa: D401
        self.meta = {}

    def put_http_meta(self, key, value):  # noqa: D401
        self.meta[key] = value

    def add_exception(self, e, stack):  # noqa: D401
        pass


class DummyRecorder:
    def __init__(self):  # noqa: D401
        self._stack = []
        self.configured = False

    def begin_segment(self, name):  # noqa: D401
        seg = DummySegment()
        self._stack.append(seg)
        return seg

    def end_segment(self):  # noqa: D401
        if self._stack:
            self._stack.pop()

    def current_segment(self):  # noqa: D401
        return self._stack[-1] if self._stack else None

    def configure(self, **kwargs):  # noqa: D401
        self.configured = True

    def capture(self, name):  # noqa: D401
        @contextmanager
        def _cm():
            yield DummySegment()

        return _cm()


def test_xray_middleware_active(monkeypatch):
    # Enable X-Ray and inject stub recorder
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    # Ensure setup_xray_tracing returns True so main will add middleware
    monkeypatch.setattr(
        "app.core.tracing.setup_xray_tracing", lambda: True, raising=False
    )

    stub = SimpleNamespace(xray_recorder=DummyRecorder())
    monkeypatch.setitem(sys.modules, "aws_xray_sdk.core", stub)

    import app.main as main

    reload(main)
    client = TestClient(main.app)
    r = client.get("/health")
    assert r.status_code == 200
