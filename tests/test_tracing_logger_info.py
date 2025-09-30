"""
Test to cover logger.info line in setup_xray_tracing (line 57).
"""

import logging
import sys
from types import SimpleNamespace


def test_setup_xray_logs_success_message(monkeypatch, caplog):
    """Test that setup_xray_tracing logs success message."""
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_SERVICE_NAME", "test-service", raising=False
    )
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_DAEMON_ADDRESS",
        "127.0.0.1:2000",
        raising=False,
    )

    class RecorderStub:
        """Stub recorder."""

        def configure(self, **kwargs):  # noqa: D401
            pass

    sys.modules["aws_xray_sdk.core"] = SimpleNamespace(
        xray_recorder=RecorderStub(), patch=lambda libs: None
    )

    # Import fresh to ensure setup runs
    from app.core import tracing

    with caplog.at_level(logging.INFO):
        result = tracing.setup_xray_tracing()

    assert result is True
    # Check that success message was logged
    assert any(
        "X-Ray tracing enabled for service" in record.message
        for record in caplog.records
    )
