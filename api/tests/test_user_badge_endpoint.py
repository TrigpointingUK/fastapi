"""
Tests for the user badge endpoint.
"""

import io
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api.main import app

# import pytest  # Not used directly but may be needed by test framework


class TestUserBadgeEndpoint:
    """Test cases for the /v1/users/badge endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @patch("api.api.v1.endpoints.users.BadgeService")
    @patch("api.api.v1.endpoints.users.get_db")
    def test_get_user_badge_success(self, mock_get_db, mock_badge_service_class):
        """Test successful badge generation."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock badge service
        mock_service = Mock()
        mock_badge_bytes = io.BytesIO(b"fake_png_data")
        mock_service.generate_badge.return_value = mock_badge_bytes
        mock_badge_service_class.return_value = mock_service

        response = self.client.get("/v1/users/1/badge")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert "user_1_badge.png" in response.headers.get("content-disposition", "")
        assert "max-age=300" in response.headers.get("cache-control", "")

        # Verify the service was called (don't check exact db object due to dependency injection)
        mock_service.generate_badge.assert_called_once()
        call_args = mock_service.generate_badge.call_args
        assert call_args[0][1] == 1  # user_id should be 1

    @patch("api.api.v1.endpoints.users.BadgeService")
    @patch("api.api.v1.endpoints.users.get_db")
    def test_get_user_badge_user_not_found(self, mock_get_db, mock_badge_service_class):
        """Test badge generation when user is not found."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock badge service to raise ValueError
        mock_service = Mock()
        mock_service.generate_badge.side_effect = ValueError(
            "User with ID 999 not found"
        )
        mock_badge_service_class.return_value = mock_service

        response = self.client.get("/v1/users/999/badge")

        assert response.status_code == 404
        # Accept normalised not-found message
        assert "User not found" in response.json()["detail"]

    @patch("api.api.v1.endpoints.users.BadgeService")
    @patch("api.api.v1.endpoints.users.get_db")
    def test_get_user_badge_logo_not_found(self, mock_get_db, mock_badge_service_class):
        """Test badge generation when logo file is not found."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock badge service to raise FileNotFoundError
        mock_service = Mock()
        mock_service.generate_badge.side_effect = FileNotFoundError(
            "Logo file not found"
        )
        mock_badge_service_class.return_value = mock_service

        response = self.client.get("/v1/users/1/badge")

        assert response.status_code == 500
        assert "Server configuration error" in response.json()["detail"]
        assert "Logo file not found" in response.json()["detail"]

    @patch("api.api.v1.endpoints.users.BadgeService")
    @patch("api.api.v1.endpoints.users.get_db")
    def test_get_user_badge_general_error(self, mock_get_db, mock_badge_service_class):
        """Test badge generation with general error."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock badge service to raise general exception
        mock_service = Mock()
        mock_service.generate_badge.side_effect = Exception("Something went wrong")
        mock_badge_service_class.return_value = mock_service

        response = self.client.get("/v1/users/1/badge")

        assert response.status_code == 500
        assert "Error generating badge" in response.json()["detail"]
        assert "Something went wrong" in response.json()["detail"]

    def test_get_user_badge_missing_user_id(self):
        """Test badge generation without user_id in path."""
        response = self.client.get("/v1/users/badge")

        assert response.status_code == 422  # FastAPI tries to parse "badge" as user_id
        assert (
            "input should be a valid integer"
            in response.json()["detail"][0]["msg"].lower()
        )

    def test_get_user_badge_invalid_user_id(self):
        """Test badge generation with invalid user_id in path."""
        response = self.client.get("/v1/users/invalid/badge")

        assert response.status_code == 422
        assert (
            "input should be a valid integer"
            in response.json()["detail"][0]["msg"].lower()
        )

    @patch("api.api.v1.endpoints.users.BadgeService")
    @patch("api.api.v1.endpoints.users.get_db")
    def test_get_user_badge_with_scale(self, mock_get_db, mock_badge_service_class):
        """Test badge generation with scale parameter."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock badge service
        mock_service = Mock()
        mock_badge_bytes = io.BytesIO(b"fake_scaled_png_data")
        mock_service.generate_badge.return_value = mock_badge_bytes
        mock_badge_service_class.return_value = mock_service

        response = self.client.get("/v1/users/1/badge?scale=2.0")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

        # Verify the service was called with the scale parameter
        mock_service.generate_badge.assert_called_once()
        call_args = mock_service.generate_badge.call_args
        assert call_args[1]["scale"] == 2.0  # Check keyword argument

    @patch("api.api.v1.endpoints.users.BadgeService")
    @patch("api.api.v1.endpoints.users.get_db")
    def test_get_user_badge_invalid_scale(self, mock_get_db, mock_badge_service_class):
        """Test badge generation with invalid scale parameter."""
        response = self.client.get("/v1/users/1/badge?scale=10.0")  # Too large

        assert response.status_code == 422
        assert (
            "input should be less than or equal to 5"
            in response.json()["detail"][0]["msg"].lower()
        )

        response = self.client.get("/v1/users/1/badge?scale=0.05")  # Too small

        assert response.status_code == 422
        assert (
            "input should be greater than or equal to 0.1"
            in response.json()["detail"][0]["msg"].lower()
        )
