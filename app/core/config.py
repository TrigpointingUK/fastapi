"""
Core configuration settings for the FastAPI application.
"""

from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Legacy API Migration"
    ENVIRONMENT: str = "development"  # staging, production, development
    DEBUG: bool = False

    # Database - constructed from individual components
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "user"
    DB_PASSWORD: str = "pass"
    DB_NAME: str = "db"

    @property
    def DATABASE_URL(self) -> str:
        """Construct DATABASE_URL from individual database components."""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # JWT
    JWT_SECRET_KEY: str = "default-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Auth0 Configuration
    AUTH0_DOMAIN: Optional[str] = None
    AUTH0_SECRET_NAME: Optional[str] = None
    AUTH0_CONNECTION: Optional[str] = None
    AUTH0_ENABLED: bool = False

    # Auth0 Audience Configuration
    # These are separate audiences for different purposes:
    # - MANAGEMENT_API_AUDIENCE: For accessing Auth0 Management API (user sync, etc.)
    # - API_AUDIENCE: For validating tokens from your API clients
    AUTH0_MANAGEMENT_API_AUDIENCE: Optional[str] = None
    AUTH0_API_AUDIENCE: Optional[str] = (
        None  # e.g., "https://api.trigpointing.me/api/v1/"
    )

    # Logging Configuration
    LOG_LEVEL: str = "INFO"

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
