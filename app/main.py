"""
Main FastAPI application entry point.
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from fastapi import Depends, FastAPI

# Configure logging first
setup_logging()

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

    # Add security requirement to all protected endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                endpoint = openapi_schema["paths"][path][method]
                if "security" not in endpoint:
                    endpoint["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/debug/auth")
def debug_auth(credentials: HTTPBearer = Depends(HTTPBearer(auto_error=False))):
    """Debug endpoint to test authentication."""
    if credentials is None:
        return {"authenticated": False, "error": "No credentials provided"}

    try:
        from jose import jwt

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
            "token": credentials.credentials[:50] + "..."
            if len(credentials.credentials) > 50
            else credentials.credentials,
        }


if __name__ == "__main__":
    import os

    import uvicorn

    # Use 127.0.0.1 for security unless explicitly overridden (schema configurable)
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
