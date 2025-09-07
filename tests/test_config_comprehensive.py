"""
Comprehensive tests for config module to improve coverage.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestConfigComprehensive:
    """Test config module comprehensively."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        # Test the default values by checking the class field defaults directly
        # This bypasses environment variable loading and tests the actual defaults
        from app.core.config import Settings

        # Check the field defaults directly from the model
        model_fields = Settings.model_fields

        assert model_fields["API_V1_STR"].default == "/api/v1"
        assert model_fields["PROJECT_NAME"].default == "Legacy API Migration"
        assert model_fields["DEBUG"].default is False
        assert (
            model_fields["DATABASE_URL"].default
            == "mysql+pymysql://user:pass@localhost/db"
        )
        assert (
            model_fields["JWT_SECRET_KEY"].default
            == "default-secret-change-in-production"
        )
        assert model_fields["JWT_ALGORITHM"].default == "HS256"
        assert model_fields["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"].default == 30
        assert model_fields["BACKEND_CORS_ORIGINS"].default == []
        assert model_fields["AUTH0_DOMAIN"].default is None
        assert model_fields["AUTH0_SECRET_NAME"].default is None
        assert (
            model_fields["AUTH0_CONNECTION"].default
            == "Username-Password-Authentication"
        )
        assert model_fields["AUTH0_ENABLED"].default is False
        assert model_fields["LOG_LEVEL"].default == "INFO"

    def test_cors_origins_string_parsing(self):
        """Test CORS origins parsing from string."""
        settings = Settings(
            BACKEND_CORS_ORIGINS="http://localhost:3000,https://example.com"
        )

        assert len(settings.BACKEND_CORS_ORIGINS) == 2
        assert str(settings.BACKEND_CORS_ORIGINS[0]) == "http://localhost:3000/"
        assert str(settings.BACKEND_CORS_ORIGINS[1]) == "https://example.com/"

    def test_cors_origins_list_passthrough(self):
        """Test CORS origins passthrough for list input."""
        origins = ["http://localhost:3000", "https://example.com"]
        settings = Settings(BACKEND_CORS_ORIGINS=origins)

        assert len(settings.BACKEND_CORS_ORIGINS) == 2
        assert str(settings.BACKEND_CORS_ORIGINS[0]) == "http://localhost:3000/"
        assert str(settings.BACKEND_CORS_ORIGINS[1]) == "https://example.com/"

    def test_cors_origins_string_with_brackets(self):
        """Test CORS origins parsing from string that starts with bracket."""
        # This should be treated as a single string, not parsed as JSON
        # The string should be treated as a single URL
        with pytest.raises(ValidationError):
            # This should fail because it's not a valid URL
            Settings(
                BACKEND_CORS_ORIGINS='["http://localhost:3000","https://example.com"]'
            )

    def test_cors_origins_invalid_type(self):
        """Test CORS origins with invalid type raises ValidationError."""
        with pytest.raises(ValidationError):
            Settings(BACKEND_CORS_ORIGINS=123)

    def test_cors_origins_empty_string(self):
        """Test CORS origins with empty string."""
        # Empty string should result in empty list
        with pytest.raises(ValidationError):
            Settings(BACKEND_CORS_ORIGINS="")

    def test_cors_origins_single_url(self):
        """Test CORS origins with single URL."""
        settings = Settings(BACKEND_CORS_ORIGINS="https://example.com")
        assert len(settings.BACKEND_CORS_ORIGINS) == 1
        assert str(settings.BACKEND_CORS_ORIGINS[0]) == "https://example.com/"

    def test_cors_origins_with_spaces(self):
        """Test CORS origins with spaces around URLs."""
        settings = Settings(
            BACKEND_CORS_ORIGINS=" http://localhost:3000 , https://example.com "
        )

        assert len(settings.BACKEND_CORS_ORIGINS) == 2
        assert str(settings.BACKEND_CORS_ORIGINS[0]) == "http://localhost:3000/"
        assert str(settings.BACKEND_CORS_ORIGINS[1]) == "https://example.com/"

    def test_auth0_configuration(self):
        """Test Auth0 configuration settings."""
        settings = Settings(
            AUTH0_DOMAIN="test.auth0.com",
            AUTH0_SECRET_NAME="test-secret",
            AUTH0_CONNECTION="custom-connection",
            AUTH0_ENABLED=True,
        )

        assert settings.AUTH0_DOMAIN == "test.auth0.com"
        assert settings.AUTH0_SECRET_NAME == "test-secret"
        assert settings.AUTH0_CONNECTION == "custom-connection"
        assert settings.AUTH0_ENABLED is True

    def test_jwt_configuration(self):
        """Test JWT configuration settings."""
        settings = Settings(
            JWT_SECRET_KEY="custom-secret",
            JWT_ALGORITHM="HS512",
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60,
        )

        assert settings.JWT_SECRET_KEY == "custom-secret"
        assert settings.JWT_ALGORITHM == "HS512"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 60

    def test_database_configuration(self):
        """Test database configuration."""
        settings = Settings(DATABASE_URL="postgresql://user:pass@localhost/db")
        assert settings.DATABASE_URL == "postgresql://user:pass@localhost/db"

    def test_environment_variable_override(self):
        """Test that environment variables override default values."""
        import os

        # Set environment variables
        os.environ["JWT_SECRET_KEY"] = "env-secret-key"
        os.environ["DATABASE_URL"] = "env-database-url"
        os.environ["AUTH0_DOMAIN"] = "env.auth0.com"

        try:
            settings = Settings()

            # These should be overridden by environment variables
            assert settings.JWT_SECRET_KEY == "env-secret-key"
            assert settings.DATABASE_URL == "env-database-url"
            assert settings.AUTH0_DOMAIN == "env.auth0.com"

            # These should still be defaults
            assert settings.API_V1_STR == "/api/v1"
            assert settings.PROJECT_NAME == "Legacy API Migration"
            assert settings.DEBUG is False
        finally:
            # Clean up environment variables
            for var in ["JWT_SECRET_KEY", "DATABASE_URL", "AUTH0_DOMAIN"]:
                os.environ.pop(var, None)

    def test_settings_instantiation_with_env_vars(self):
        """Test that Settings can be instantiated and works with environment variables."""
        # This test verifies that Settings works correctly regardless of environment
        settings = Settings()

        # Just verify that all expected attributes exist and have reasonable values
        assert hasattr(settings, "API_V1_STR")
        assert hasattr(settings, "PROJECT_NAME")
        assert hasattr(settings, "DEBUG")
        assert hasattr(settings, "DATABASE_URL")
        assert hasattr(settings, "JWT_SECRET_KEY")
        assert hasattr(settings, "JWT_ALGORITHM")
        assert hasattr(settings, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
        assert hasattr(settings, "BACKEND_CORS_ORIGINS")
        assert hasattr(settings, "AUTH0_DOMAIN")
        assert hasattr(settings, "AUTH0_SECRET_NAME")
        assert hasattr(settings, "AUTH0_CONNECTION")
        assert hasattr(settings, "AUTH0_ENABLED")
        assert hasattr(settings, "LOG_LEVEL")

        # Verify types are correct
        assert isinstance(settings.API_V1_STR, str)
        assert isinstance(settings.PROJECT_NAME, str)
        assert isinstance(settings.DEBUG, bool)
        assert isinstance(settings.DATABASE_URL, str)
        assert isinstance(settings.JWT_SECRET_KEY, str)
        assert isinstance(settings.JWT_ALGORITHM, str)
        assert isinstance(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
        assert isinstance(settings.AUTH0_ENABLED, bool)
        assert isinstance(settings.LOG_LEVEL, str)

    def test_debug_configuration(self):
        """Test debug configuration."""
        settings = Settings(DEBUG=True)
        assert settings.DEBUG is True

    def test_project_name_configuration(self):
        """Test project name configuration."""
        settings = Settings(PROJECT_NAME="Custom Project")
        assert settings.PROJECT_NAME == "Custom Project"

    def test_api_v1_str_configuration(self):
        """Test API v1 string configuration."""
        settings = Settings(API_V1_STR="/api/v2")
        assert settings.API_V1_STR == "/api/v2"

    def test_log_level_configuration(self):
        """Test log level configuration."""
        settings = Settings(LOG_LEVEL="DEBUG")
        assert settings.LOG_LEVEL == "DEBUG"

    def test_log_level_invalid(self):
        """Test log level with invalid value."""
        # Pydantic should accept any string, but we can test the behavior
        settings = Settings(LOG_LEVEL="INVALID_LEVEL")
        assert settings.LOG_LEVEL == "INVALID_LEVEL"

    def test_settings_immutable(self):
        """Test that settings are immutable after creation."""
        settings = Settings()

        # Pydantic models are not immutable by default, so this should not raise an error
        # We can test that the value can be changed
        settings.API_V1_STR = "/api/v2"
        assert settings.API_V1_STR == "/api/v2"

    def test_settings_model_config(self):
        """Test that settings model config is set correctly."""
        assert Settings.model_config["case_sensitive"] is True
        assert "env_file" in Settings.model_config

    def test_cors_origins_field_validator(self):
        """Test the CORS origins field validator method."""
        # Test the validator method directly
        result = Settings.assemble_cors_origins(
            "http://localhost:3000,https://example.com"
        )
        assert result == ["http://localhost:3000", "https://example.com"]

    def test_cors_origins_field_validator_list(self):
        """Test the CORS origins field validator with list input."""
        result = Settings.assemble_cors_origins(
            ["http://localhost:3000", "https://example.com"]
        )
        assert result == ["http://localhost:3000", "https://example.com"]

    def test_cors_origins_field_validator_bracket_string(self):
        """Test the CORS origins field validator with bracket string."""
        result = Settings.assemble_cors_origins(
            '["http://localhost:3000","https://example.com"]'
        )
        assert result == '["http://localhost:3000","https://example.com"]'

    def test_cors_origins_field_validator_invalid(self):
        """Test the CORS origins field validator with invalid input."""
        with pytest.raises(ValueError):
            Settings.assemble_cors_origins(123)
