"""
Ensure module-level X-Ray middleware init lines execute under import.
"""

import sys
from importlib import import_module


def test_main_import_xray_enabled(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.XRAY_ENABLED", True, raising=False)
    monkeypatch.setattr(
        "app.core.tracing.setup_xray_tracing", lambda: True, raising=False
    )
    # Provide XRayMiddleware class import path
    import types

    mod = types.ModuleType("app.core.xray_middleware")

    class _MW:
        def __init__(self, *a, **k):
            pass

    mod.XRayMiddleware = _MW
    sys.modules["app.core.xray_middleware"] = mod

    # Remove cached module to force re-execution
    sys.modules.pop("app.main", None)

    m = import_module("app.main")
    assert hasattr(m, "app")
