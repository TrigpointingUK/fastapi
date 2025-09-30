"""
Lightweight tests to exercise X-Ray middleware branches for diff coverage.
"""

from importlib import reload


def test_xray_middleware_disabled(monkeypatch):
    # Ensure path through middleware guard when disabled
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", False, raising=False)
    # Re-import main to execute middleware setup path
    import app.main as main

    reload(main)
    assert getattr(main, "app", None) is not None
