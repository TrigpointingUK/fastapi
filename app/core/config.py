"""
Core configuration settings for the FastAPI application.
"""

import logging
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "TrigpointingUK API"
    ENVIRONMENT: str = "development"  # staging, production, development
    DEBUG: bool = False

    # Database - constructed from individual components
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "user"
    DB_PASSWORD: str = "pass"
    DB_NAME: str = "db"

    # Database Pool Configuration
    DATABASE_POOL_SIZE: int = 5
    DATABASE_POOL_RECYCLE: int = 300

    @property
    def DATABASE_URL(self) -> str:
        """Construct DATABASE_URL from individual database components."""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Auth0 Configuration
    AUTH0_DOMAIN: Optional[str] = None
    AUTH0_SECRET_NAME: Optional[str] = None
    AUTH0_CONNECTION: Optional[str] = None
    # SPA client for Swagger OAuth2 (PKCE)
    AUTH0_SPA_CLIENT_ID: Optional[str] = None
    # M2M client for Management API
    AUTH0_M2M_CLIENT_ID: Optional[str] = None
    AUTH0_M2M_CLIENT_SECRET: Optional[str] = None
    # Backwards compatibility (deprecated): if new vars missing, fall back to these
    AUTH0_CLIENT_ID: Optional[str] = None
    AUTH0_CLIENT_SECRET: Optional[str] = None

    # Auth0 Audience Configuration
    # These are separate audiences for different purposes:
    # - MANAGEMENT_API_AUDIENCE: For accessing Auth0 Management API (user sync, etc.)
    # - API_AUDIENCE: For validating tokens from your API clients
    AUTH0_MANAGEMENT_API_AUDIENCE: Optional[str] = None
    AUTH0_API_AUDIENCE: Optional[str] = None  # e.g., "https://api.trigpointing.me/v1/"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"

    # Orientation model (ONNX) configuration
    ORIENTATION_MODEL_ENABLED: bool = False
    ORIENTATION_MODEL_PATH: Optional[str] = None
    ORIENTATION_MODEL_THRESHOLD: float = 0.65

    # Photo upload configuration
    PHOTOS_SERVER_ID: int = 1  # Default to S3 server (server.id = 1)
    PHOTOS_S3_BUCKET: str = "trigpointinguk-photos"
    MAX_IMAGE_SIZE: int = 20 * 1024 * 1024  # 20MB
    MAX_IMAGE_DIMENSION: int = 4000
    THUMBNAIL_SIZE: int = 120

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
