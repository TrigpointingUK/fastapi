"""
Execute real setup_xray_tracing to cover configure arguments.
"""

import sys
from types import SimpleNamespace

from app.core import tracing


def test_setup_xray_tracing_real(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_SERVICE_NAME", "test-service", raising=False
    )
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_DAEMON_ADDRESS",
        "127.0.0.1:2000",
        raising=False,
    )

    # Provide minimal stubs so configure path executes
    class _Rec:
        def configure(self, **kwargs):  # noqa: D401
            pass

    sys.modules["aws_xray_sdk.core"] = SimpleNamespace(
        xray_recorder=_Rec(), patch=lambda libs: None
    )

    assert tracing.setup_xray_tracing() is True
