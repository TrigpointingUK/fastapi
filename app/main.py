"""
Main FastAPI application entry point.
"""

import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.tracing import setup_xray_tracing
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

logger = logging.getLogger(__name__)

# Configure logging first
setup_logging()

# Set up tracing - use only AWS X-Ray SDK to avoid conflicts
xray_enabled = setup_xray_tracing()
otel_enabled = False  # Disabled to avoid conflicts with X-Ray SDK

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "clientId": (settings.AUTH0_SPA_CLIENT_ID or settings.AUTH0_CLIENT_ID or ""),
        "appName": settings.PROJECT_NAME,
        # PKCE is recommended for SPA/Swagger flows
        "usePkceWithAuthorizationCodeGrant": True,
        # Pass audience so Auth0 issues an API token, not just OIDC profile
        "additionalQueryStringParams": {
            "audience": settings.AUTH0_API_AUDIENCE or "",
        },
    },
)

# Configure security scheme for Swagger UI
security_scheme = HTTPBearer()
app.openapi_schema = None  # Clear the schema cache


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="TrigpointingUK API",
        routes=app.routes,
    )

    # Add only OAuth2 security scheme (remove any Bearer schemes)
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    # Clean up any auto-added Bearer schemes from dependencies
    for k in list(openapi_schema["components"]["securitySchemes"].keys()):
        if k.lower().startswith("bearer") or k.lower() == "httpbearer":
            del openapi_schema["components"]["securitySchemes"][k]
    # OAuth2 Authorization Code (PKCE) for Auth0 login via Swagger UI
    # Always include OAuth2 scheme for docs/tests even if domain is not configured
    auth_domain = (
        f"https://{settings.AUTH0_DOMAIN}"
        if getattr(settings, "AUTH0_DOMAIN", None)
        else "https://example.com"
    )
    openapi_schema["components"]["securitySchemes"]["OAuth2"] = {
        "type": "oauth2",
        "flows": {
            "authorizationCode": {
                "authorizationUrl": f"{auth_domain}/authorize",
                "tokenUrl": f"{auth_domain}/oauth/token",
                "scopes": {
                    "openid": "OpenID Connect scope",
                    "profile": "Basic profile information",
                    "trig:admin": "Administrative access to trig resources",
                    "user:admin": "Administrative access to users",
                },
            }
        },
    }

    # Define public endpoints that should not have security requirements
    # Note: GET requests to these paths are public, but POST/PUT/DELETE require auth
    public_endpoints = {
        "/health",
        f"{settings.API_V1_STR}/trigs",
        f"{settings.API_V1_STR}/trigs/{{trig_id}}",
        f"{settings.API_V1_STR}/trigs/{{trig_id}}/logs",
        f"{settings.API_V1_STR}/trigs/{{trig_id}}/map",
        f"{settings.API_V1_STR}/trigs/{{trig_id}}/photos",
        f"{settings.API_V1_STR}/trigs/waypoint/{{waypoint}}",
        f"{settings.API_V1_STR}/photos",
        f"{settings.API_V1_STR}/photos/{{photo_id}}",
        f"{settings.API_V1_STR}/photos/{{photo_id}}/evaluate",
        f"{settings.API_V1_STR}/users",
        f"{settings.API_V1_STR}/users/{{user_id}}/badge",
        f"{settings.API_V1_STR}/users/{{user_id}}/logs",
        f"{settings.API_V1_STR}/users/{{user_id}}/map",
        f"{settings.API_V1_STR}/users/{{user_id}}/photos",
        f"{settings.API_V1_STR}/logs",
        f"{settings.API_V1_STR}/logs/{{log_id}}",
        f"{settings.API_V1_STR}/logs/{{log_id}}/photos",
    }

    # Define endpoints that are public regardless of HTTP method
    # Used for special cases like migration/onboarding endpoints
    fully_public_endpoints = {
        f"{settings.API_V1_STR}/legacy/login",
    }

    # Define endpoints with optional auth (should not have required security)
    optional_auth_endpoints: set[str] = {
        # Currently no endpoints require optional auth
    }

    admin_endpoints = {
        f"{settings.API_V1_STR}/legacy/username-duplicates",
        f"{settings.API_V1_STR}/legacy/email-duplicates",
    }

    # Add security requirement to protected endpoints only
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                endpoint = openapi_schema["paths"][path][method]

                # Skip fully public endpoints (all HTTP methods)
                if path in fully_public_endpoints:
                    continue

                # Skip public endpoints (GET requests only)
                if path in public_endpoints and method == "get":
                    continue

                # For optional auth endpoints, set optional security (grey padlock in Swagger)
                if path in optional_auth_endpoints:
                    endpoint["security"] = [
                        {"OAuth2": []},
                        {},
                    ]  # Empty object makes it optional
                    continue

                # Add security requirement to write endpoints and admin endpoints
                if path in admin_endpoints:
                    endpoint["security"] = [
                        {"OAuth2": ["openid", "profile", "user:admin"]}
                    ]
                elif method in ["post", "put", "patch", "delete"]:
                    # Require authentication for write operations
                    endpoint["security"] = [{"OAuth2": []}]
                else:
                    # GET requests to protected paths require authentication
                    endpoint["security"] = [{"OAuth2": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add X-Ray middleware for FastAPI using custom middleware
if xray_enabled:
    try:
        from aws_xray_sdk.core import xray_recorder
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from starlette.responses import Response

        class XRayMiddleware(BaseHTTPMiddleware):
            def __init__(self, app, recorder=None):
                super().__init__(app)
                self.recorder = recorder or xray_recorder

            async def dispatch(self, request: Request, call_next):
                # Skip X-Ray for the debug endpoint (it creates its own segment)
                if request.url.path == "/debug/xray":
                    return await call_next(request)

                # Start a segment for this request only if one doesn't already exist
                segment_created_here = False
                segment = None
                try:
                    # Reuse existing segment if present; otherwise begin a new root segment
                    segment = self.recorder.current_segment()
                    if segment is None:
                        segment = self.recorder.begin_segment()
                        segment_created_here = True
                    # Store reference for downstream usage
                    request.state.xray_segment = segment
                except Exception as e:
                    logger.warning(f"Failed to create X-Ray segment: {e}")
                    # If segment creation fails, continue without tracing
                    return await call_next(request)

                try:
                    # Add HTTP metadata the correct way for X-Ray (with error handling)
                    if segment:
                        try:
                            segment.put_http_meta("method", request.method)
                            segment.put_http_meta("url", str(request.url))
                            if request.headers.get("user-agent"):
                                segment.put_http_meta(
                                    "user_agent", request.headers.get("user-agent")
                                )
                            if request.client:
                                segment.put_http_meta("client_ip", request.client.host)
                        except Exception as meta_err:
                            logger.debug(
                                f"Failed to add X-Ray request metadata (segment may have ended): {meta_err}"
                            )

                    # Process the request
                    response: Response = await call_next(request)

                    # Add response metadata (with error handling for race conditions)
                    if segment:
                        try:
                            segment.put_http_meta("status", response.status_code)
                            if response.headers.get("content-length"):
                                segment.put_http_meta(
                                    "content_length",
                                    response.headers.get("content-length"),
                                )
                        except Exception as meta_err:
                            logger.debug(
                                f"Failed to add X-Ray metadata (segment may have ended): {meta_err}"
                            )

                    return response

                except Exception as e:
                    # Mark segment as error with traceback stack
                    try:
                        import sys
                        import traceback

                        if segment:
                            _, _, tb = sys.exc_info()
                            stack = traceback.extract_tb(tb) if tb else None
                            segment.add_exception(e, stack)
                    except Exception as add_exc_err:
                        logger.debug(f"Failed to record X-Ray exception: {add_exc_err}")
                    raise
                finally:
                    # Always end the segment
                    try:
                        # Only end the segment if we created it in this middleware
                        if segment_created_here:
                            # Restore current entity before ending to handle async context switches
                            if segment is not None and hasattr(
                                self.recorder, "_context"
                            ):
                                try:
                                    self.recorder._context.set_trace_entity(segment)  # type: ignore[attr-defined]
                                except Exception as context_err:
                                    logger.debug(
                                        f"Could not set X-Ray current entity before end: {context_err}"
                                    )
                            self.recorder.end_segment()
                    except Exception as e:
                        logger.warning(f"Failed to end X-Ray segment: {e}")

        app.add_middleware(XRayMiddleware, recorder=xray_recorder)
        logger.info("X-Ray custom middleware added successfully")
    except Exception as e:
        logger.error(f"Error setting up X-Ray middleware: {e}")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    # Import version information
    try:
        from app.__version__ import __build_time__, __version__

        version_info = {"version": __version__, "build_time": __build_time__}
    except ImportError:
        version_info = {"version": "unknown", "build_time": "unknown"}

    tracing_info = {
        "xray_enabled": xray_enabled,
        "otel_enabled": otel_enabled,
        "tracing_conflict_resolved": True,  # Indicate that the conflict has been resolved
    }

    # Add X-Ray configuration details if enabled
    if xray_enabled:
        tracing_info.update(
            {
                "xray_service_name": settings.XRAY_SERVICE_NAME,
                "xray_sampling_rate": settings.XRAY_SAMPLING_RATE,
                "xray_daemon_address": settings.XRAY_DAEMON_ADDRESS,
            }
        )

        # Try to get X-Ray status
        try:
            from aws_xray_sdk.core import xray_recorder

            # Check if recorder is configured
            tracing_info["xray_recorder_type"] = type(xray_recorder).__name__

            # For AsyncAWSXRayRecorder, check if it's properly configured
            if hasattr(xray_recorder, "service"):
                tracing_info["xray_recorder_service"] = xray_recorder.service
            if hasattr(xray_recorder, "daemon_address"):
                tracing_info["xray_recorder_daemon_address"] = (
                    xray_recorder.daemon_address
                )
            if hasattr(xray_recorder, "_context"):
                tracing_info["xray_recorder_has_context"] = (
                    xray_recorder._context is not None
                )

            # Try to check if sampling is working
            tracing_info["xray_recorder_configured"] = True

        except Exception as e:
            tracing_info["xray_recorder_error"] = str(e)

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": version_info["version"],
        "build_time": version_info["build_time"],
        "tracing": tracing_info,
    }


# moved to /v1/debug/xray under debug router


if __name__ == "__main__":
    import os

    import uvicorn

    # Use 127.0.0.1 for security unless explicitly overridden (schema configurable)
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
