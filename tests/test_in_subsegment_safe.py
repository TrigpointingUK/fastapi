"""
Test in_subsegment_safe context manager for X-Ray subsegments.
"""

import sys
from contextlib import contextmanager
from types import SimpleNamespace

from app.core import tracing


def test_in_subsegment_safe_with_segment(monkeypatch):
    """Test in_subsegment_safe when there is an active segment."""
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)

    class RecorderWithSegment:
        """Stub recorder with an active segment."""

        def __init__(self):
            self._segment = object()

        def current_segment(self):
            """Return an active segment."""
            return self._segment

        @contextmanager
        def in_subsegment(self, name):
            """Create a subsegment."""
            yield self._segment

    stub_recorder = RecorderWithSegment()
    sys.modules["aws_xray_sdk.core"] = SimpleNamespace(xray_recorder=stub_recorder)

    # Use the context manager
    with tracing.in_subsegment_safe("test.subsegment"):
        # This should create a subsegment
        result = 42

    assert result == 42


def test_in_subsegment_safe_no_segment(monkeypatch):
    """Test in_subsegment_safe when there is no active segment."""
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)

    class RecorderNoSegment:
        """Stub recorder with no active segment."""

        def current_segment(self):
            """Return None (no active segment)."""
            return None

        @contextmanager
        def in_subsegment(self, name):
            """This shouldn't be called."""
            raise AssertionError(
                "in_subsegment should not be called when no segment exists"
            )

    stub_recorder = RecorderNoSegment()
    sys.modules["aws_xray_sdk.core"] = SimpleNamespace(xray_recorder=stub_recorder)

    # Use the context manager - should be a no-op
    with tracing.in_subsegment_safe("test.subsegment"):
        result = 42

    assert result == 42
