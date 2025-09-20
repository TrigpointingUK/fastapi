"""
Main FastAPI application entry point.
"""

import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.tracing import setup_opentelemetry_tracing, setup_xray_tracing
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# Configure logging first
setup_logging()

# Set up tracing
xray_enabled = setup_xray_tracing()
otel_enabled = setup_opentelemetry_tracing()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
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
        description="Legacy API Migration with JWT Authentication",
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Define public endpoints that should not have security requirements
    public_endpoints = {
        "/health",
        "/api/v1/auth/login",
    }

    # Define endpoints with optional auth (should not have required security)
    optional_auth_endpoints = {
        "/debug/auth",
    }

    # Add security requirement to protected endpoints only
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                endpoint = openapi_schema["paths"][path][method]

                # Skip public endpoints
                if path in public_endpoints:
                    continue

                # For optional auth endpoints, remove any existing security requirements
                if path in optional_auth_endpoints:
                    if "security" in endpoint:
                        del endpoint["security"]
                    continue

                # Add security requirement to all other endpoints
                if "security" not in endpoint:
                    endpoint["security"] = [{"BearerAuth": []}]
                else:
                    # Replace any existing security with BearerAuth
                    endpoint["security"] = [{"BearerAuth": []}]

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

# Add X-Ray middleware if enabled
if xray_enabled:
    try:
        from aws_xray_sdk.core import xray_recorder
        from aws_xray_sdk.ext.fastapi import XRayMiddleware as FastAPIXRayMiddleware

        # Use the official AWS X-Ray FastAPI middleware
        app.add_middleware(FastAPIXRayMiddleware, recorder=xray_recorder)
        logger.info("X-Ray middleware added successfully")
    except ImportError as e:
        logger.warning(f"X-Ray FastAPI middleware not available: {e}")
        # Fallback: Try to patch FastAPI directly
        try:
            from aws_xray_sdk.core import patch

            patch(["fastapi"])
            logger.info("X-Ray patching applied to FastAPI")
        except Exception as patch_error:
            logger.error(f"Failed to patch FastAPI with X-Ray: {patch_error}")
    except Exception as e:
        logger.error(f"Error setting up X-Ray middleware: {e}")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    tracing_info = {
        "xray_enabled": xray_enabled,
        "otel_enabled": otel_enabled,
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

            tracing_info["xray_recorder_configured"] = xray_recorder.is_enabled()
        except Exception as e:
            tracing_info["xray_recorder_error"] = str(e)

    return {
        "status": "healthy",
        "tracing": tracing_info,
    }


@app.get("/debug/xray")
def debug_xray():
    """Debug X-Ray tracing functionality."""
    if not xray_enabled:
        return {"error": "X-Ray is not enabled"}

    try:
        from aws_xray_sdk.core import xray_recorder

        # Try to create a simple trace
        with xray_recorder.capture("debug_xray_test") as segment:
            if segment:
                segment.put_annotation("test", "debug")
                segment.put_metadata(
                    "debug_info",
                    {
                        "service_name": settings.XRAY_SERVICE_NAME,
                        "sampling_rate": settings.XRAY_SAMPLING_RATE,
                        "daemon_address": settings.XRAY_DAEMON_ADDRESS,
                    },
                )
                return {
                    "status": "success",
                    "message": "X-Ray trace created successfully",
                    "trace_id": segment.trace_id,
                    "segment_id": segment.id,
                }
            else:
                return {"error": "No segment created"}

    except Exception as e:
        return {
            "error": f"X-Ray error: {str(e)}",
            "type": type(e).__name__,
        }


@app.get("/debug/auth")
def debug_auth(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    """Debug endpoint to test authentication."""
    if credentials is None:
        return {"authenticated": False, "error": "No credentials provided"}

    try:
        import jwt

        from app.core.config import settings

        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return {
            "authenticated": True,
            "token_payload": payload,
            "user_id": payload.get("sub"),
        }
    except Exception as e:
        return {
            "authenticated": False,
            "error": str(e),
            "token": (
                credentials.credentials[:50] + "..."
                if len(credentials.credentials) > 50
                else credentials.credentials
            ),
        }


if __name__ == "__main__":
    import os

    import uvicorn

    # Use 127.0.0.1 for security unless explicitly overridden (schema configurable)
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
