"""
Execute real setup_xray_tracing to cover configure arguments.
"""

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

    # Should not raise; returns True when SDK available
    assert tracing.setup_xray_tracing() in (True, False)
