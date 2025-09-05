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
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "mysql+pymysql://user:pass@localhost/db"

    # JWT
    JWT_SECRET_KEY: str = "default-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Auth0 Configuration
    AUTH0_DOMAIN: Optional[str] = None
    AUTH0_SECRET_NAME: Optional[str] = None
    AUTH0_CONNECTION: str = "Username-Password-Authentication"
    AUTH0_ENABLED: bool = False

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
