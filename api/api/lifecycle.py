"""
Endpoint lifecycle helpers to expose stability via headers and OpenAPI extensions.

Lifecycle values:
 - alpha: experimental; can change or break
 - beta: feature-complete; breaking changes unlikely but possible
 - ga: stable; no breaking changes within current API version
 - deprecated: supported until removal; consider using replacement
"""

from typing import Literal, Optional

from fastapi import Depends, Response

Lifecycle = Literal["alpha", "beta", "ga", "deprecated"]


def lifecycle(
    status: Lifecycle, sunset: Optional[str] = None, note: Optional[str] = None
):
    """Attach runtime headers indicating endpoint lifecycle.

    - X-API-Lifecycle: alpha|beta|ga|deprecated
    - Deprecation: true (if deprecated)
    - Sunset: RFC 7231 HTTP-date (if provided and deprecated)
    - X-API-Lifecycle-Note: optional free-text note
    """

    def _marker(response: Response):
        lifecycle_value: str = str(status)
        response.headers["X-API-Lifecycle"] = lifecycle_value
        if status == "deprecated":
            response.headers["Deprecation"] = "true"
            if sunset:
                response.headers["Sunset"] = sunset
        if note:
            response.headers["X-API-Lifecycle-Note"] = note

    return Depends(_marker)


def openapi_lifecycle(
    status: Lifecycle, sunset: Optional[str] = None, note: Optional[str] = None
):
    """Return OpenAPI `openapi_extra` structure with lifecycle metadata."""
    extra = {"x-lifecycle": str(status)}
    if sunset:
        extra["x-sunset"] = sunset
    if note:
        extra["x-lifecycle-note"] = note
    return extra
