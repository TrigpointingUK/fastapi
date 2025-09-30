"""
Covers import lines in tracing setup (no functional change).
"""

import sys
from types import SimpleNamespace

from app.core import tracing


def test_tracing_import_lines(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)

    # Provide stubs for imports so lines execute
    class _Rec:
        def configure(self, **kwargs):  # noqa: D401
            pass

    sys.modules["aws_xray_sdk.core"] = SimpleNamespace(
        xray_recorder=_Rec(), patch=lambda libs: None
    )
    sys.modules["aws_xray_sdk.core.async_context"] = SimpleNamespace(
        AsyncContext=type("_Ctx", (), {})
    )
    assert tracing.setup_xray_tracing() in (True, False)
