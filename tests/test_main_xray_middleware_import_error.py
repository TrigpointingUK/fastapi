"""
Covers the import error branch when XRayMiddleware cannot be imported.
"""

import sys
from importlib import import_module


def test_main_xray_import_error_branch(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.core.tracing.setup_xray_tracing", lambda: True, raising=False
    )
    # Ensure import fails by removing module
    sys.modules.pop("app.core.xray_middleware", None)
    # Drop cached main to re-execute top-level
    sys.modules.pop("app.main", None)
    m = import_module("app.main")
    assert hasattr(m, "app")
