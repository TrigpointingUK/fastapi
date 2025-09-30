"""
Test to cover sampling=True line in xray_recorder.configure (line 43).
"""

import sys
from types import SimpleNamespace


def test_setup_xray_with_sampling_parameter(monkeypatch):
    """Test that setup_xray_tracing passes sampling=True to configure."""
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_SERVICE_NAME", "test-service", raising=False
    )
    monkeypatch.setattr(
        "app.core.config.settings.XRAY_DAEMON_ADDRESS",
        "127.0.0.1:2000",
        raising=False,
    )

    # Track configure calls
    configure_kwargs = {}

    class RecorderStub:
        """Stub that captures configure arguments."""

        def configure(self, **kwargs):  # noqa: D401
            configure_kwargs.update(kwargs)

    # Provide stubs
    sys.modules["aws_xray_sdk.core"] = SimpleNamespace(
        xray_recorder=RecorderStub(), patch=lambda libs: None
    )
    sys.modules["aws_xray_sdk.core.async_context"] = SimpleNamespace(
        AsyncContext=type("_Ctx", (), {})
    )

    # Import and call setup_xray_tracing
    from app.core import tracing

    result = tracing.setup_xray_tracing()

    # Verify the function returns True and sampling was set
    assert result is True
    assert "sampling" in configure_kwargs
    assert configure_kwargs["sampling"] is True
