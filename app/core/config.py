"""
Core configuration settings for the FastAPI application.
"""

import logging
from typing import Any, Callable, List, Optional, Union

import boto3
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


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

    # Database Pool Configuration
    DATABASE_POOL_SIZE: int = 5
    DATABASE_POOL_RECYCLE: int = 300

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
    AUTH0_CLIENT_ID: Optional[str] = None
    AUTH0_CLIENT_SECRET: Optional[str] = None

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

    # AWS X-Ray Configuration
    XRAY_ENABLED: bool = False
    XRAY_SERVICE_NAME: str = "trigpointing-api"
    XRAY_SAMPLING_RATE: float = 0.1  # 10% sampling rate
    XRAY_DAEMON_ADDRESS: Optional[str] = None  # e.g., "127.0.0.1:2000"
    XRAY_TRACE_HEADER: str = "X-Amzn-Trace-Id"

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

    def __init__(self, **kwargs):
        """Initialize settings and load Parameter Store configuration if in AWS environment."""
        super().__init__(**kwargs)
        # Load Parameter Store values if in AWS environment
        if self.ENVIRONMENT in ["staging", "production"]:
            self._load_parameter_store_config()

    def _load_parameter_store_config(self) -> None:
        """
        Load configuration from AWS Parameter Store.

        This method reads parameters from the path pattern:
        /{project_name}/{environment}/{category}/{parameter}

        And maps them to the corresponding Settings attributes.
        """
        try:
            ssm = boto3.client("ssm")
            parameter_prefix = f"/trigpointing/{self.ENVIRONMENT.lower()}/"

            logger.info(
                f"Loading Parameter Store configuration from {parameter_prefix}"
            )

            # Get all parameters for this environment
            response = ssm.get_parameters_by_path(
                Path=parameter_prefix, Recursive=True, WithDecryption=True
            )

            parameters_loaded = 0

            # Parse parameters into config
            for param in response.get("Parameters", []):
                param_name = param["Name"]
                param_value = param["Value"]

                # Extract the parameter key (remove prefix)
                key_path = param_name.replace(parameter_prefix, "")

                try:
                    self._apply_parameter_value(key_path, param_value)
                    parameters_loaded += 1
                    logger.debug(f"Loaded parameter: {key_path} = {param_value}")
                except Exception as e:
                    logger.warning(f"Failed to apply parameter {key_path}: {e}")

            logger.info(
                f"Successfully loaded {parameters_loaded} parameters from Parameter Store"
            )

        except Exception as e:
            logger.warning(f"Failed to load Parameter Store configuration: {e}")
            # Don't fail startup if Parameter Store is unavailable
            # Fall back to environment variables and defaults

    def _apply_parameter_value(self, key_path: str, value: str) -> None:
        """
        Apply a parameter value to the appropriate Settings attribute.

        Args:
            key_path: The parameter path (e.g., "xray/enabled", "app/log_level")
            value: The parameter value as a string
        """
        # Map Parameter Store paths to Settings attributes
        parameter_mappings: dict[str, tuple[str, Callable[[str], Any]]] = {
            # X-Ray configuration
            "xray/enabled": ("XRAY_ENABLED", lambda v: v.lower() == "true"),
            "xray/service_name": ("XRAY_SERVICE_NAME", str),
            "xray/sampling_rate": ("XRAY_SAMPLING_RATE", float),
            "xray/daemon_address": ("XRAY_DAEMON_ADDRESS", str),
            # Application configuration
            "app/log_level": ("LOG_LEVEL", str),
            "app/cors_origins": (
                "BACKEND_CORS_ORIGINS",
                lambda v: [origin.strip() for origin in v.split(",") if origin.strip()],
            ),
            # Database configuration
            "database/pool_size": ("DATABASE_POOL_SIZE", int),
            "database/pool_recycle": ("DATABASE_POOL_RECYCLE", int),
        }

        if key_path in parameter_mappings:
            attr_name, converter = parameter_mappings[key_path]

            try:
                converted_value = converter(value)
                setattr(self, attr_name, converted_value)
                logger.debug(
                    f"Set {attr_name} = {converted_value} (from Parameter Store)"
                )
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Failed to convert parameter {key_path} value '{value}': {e}"
                )
        else:
            logger.debug(f"Unknown parameter path: {key_path}")


settings = Settings()
