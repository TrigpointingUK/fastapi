"""
Unit tests for Auth0 integration in CRUD operations.
"""

from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.crud.user import authenticate_user_flexible
from app.models.user import User


class TestAuth0IntegrationInCRUD:
    """Test cases for Auth0 integration in CRUD operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user = User(
            id=1,
            name="testuser",
            email="test@example.com",
            cryptpw="$1$salt$hash",
            admin_ind="N",
            public_ind="Y",
        )

        self.mock_db = Mock(spec=Session)

    @patch("app.crud.user.auth0_service")
    @patch("app.crud.user.verify_password")
    @patch("app.crud.user.get_user_by_name")
    def test_authenticate_user_flexible_with_auth0_sync_success(
        self, mock_get_user, mock_verify_password, mock_auth0_service
    ):
        """Test successful authentication with Auth0 sync."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_verify_password.return_value = True
        mock_auth0_service.sync_user_to_auth0.return_value = {"user_id": "auth0|123"}

        # Call function
        result = authenticate_user_flexible(self.mock_db, "testuser", "password")

        # Assertions
        assert result == self.mock_user
        mock_get_user.assert_called_once_with(self.mock_db, "testuser")
        mock_verify_password.assert_called_once_with("password", "$1$salt$hash")
        mock_auth0_service.sync_user_to_auth0.assert_called_once_with(
            username="testuser",
            email="test@example.com",
            name="testuser",
            password="password",
            user_id=1,
        )

    @patch("app.crud.user.auth0_service")
    @patch("app.crud.user.verify_password")
    @patch("app.crud.user.get_user_by_name")
    def test_authenticate_user_flexible_with_auth0_sync_failure(
        self, mock_get_user, mock_verify_password, mock_auth0_service
    ):
        """Test authentication with Auth0 sync failure (should not affect auth)."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_verify_password.return_value = True
        mock_auth0_service.sync_user_to_auth0.side_effect = Exception("Auth0 Error")

        # Call function
        result = authenticate_user_flexible(self.mock_db, "testuser", "password")

        # Assertions
        assert result == self.mock_user  # Authentication should still succeed
        mock_auth0_service.sync_user_to_auth0.assert_called_once_with(
            username="testuser",
            email="test@example.com",
            name="testuser",
            password="password",
            user_id=1,
        )

    @patch("app.crud.user.auth0_service")
    @patch("app.crud.user.verify_password")
    @patch("app.crud.user.get_user_by_email")
    def test_authenticate_user_flexible_email_with_auth0_sync(
        self, mock_get_user, mock_verify_password, mock_auth0_service
    ):
        """Test authentication with email identifier and Auth0 sync."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_verify_password.return_value = True
        mock_auth0_service.sync_user_to_auth0.return_value = {"user_id": "auth0|123"}

        # Call function with email
        result = authenticate_user_flexible(
            self.mock_db, "test@example.com", "password"
        )

        # Assertions
        assert result == self.mock_user
        mock_get_user.assert_called_once_with(self.mock_db, "test@example.com")
        mock_auth0_service.sync_user_to_auth0.assert_called_once_with(
            username="testuser",
            email="test@example.com",
            name="testuser",
            password="password",
            user_id=1,
        )

    @patch("app.crud.user.auth0_service")
    @patch("app.crud.user.verify_password")
    @patch("app.crud.user.get_user_by_name")
    @patch("app.crud.user.get_user_by_email")
    def test_authenticate_user_flexible_user_not_found(
        self,
        mock_get_user_email,
        mock_get_user,
        mock_verify_password,
        mock_auth0_service,
    ):
        """Test authentication when user is not found."""
        # Setup mocks
        mock_get_user.return_value = None
        mock_get_user_email.return_value = None

        # Call function
        result = authenticate_user_flexible(self.mock_db, "nonexistent", "password")

        # Assertions
        assert result is None
        mock_auth0_service.sync_user_to_auth0.assert_not_called()

    @patch("app.crud.user.auth0_service")
    @patch("app.crud.user.verify_password")
    @patch("app.crud.user.get_user_by_name")
    def test_authenticate_user_flexible_wrong_password(
        self, mock_get_user, mock_verify_password, mock_auth0_service
    ):
        """Test authentication with wrong password."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_verify_password.return_value = False

        # Call function
        result = authenticate_user_flexible(self.mock_db, "testuser", "wrongpassword")

        # Assertions
        assert result is None
        mock_auth0_service.sync_user_to_auth0.assert_not_called()

    @patch("app.crud.user.auth0_service")
    @patch("app.crud.user.verify_password")
    @patch("app.crud.user.get_user_by_name")
    def test_authenticate_user_flexible_user_without_email(
        self, mock_get_user, mock_verify_password, mock_auth0_service
    ):
        """Test authentication with user that has no email."""
        # Setup mocks
        user_no_email = User(
            id=1,
            name="testuser",
            email=None,
            cryptpw="$1$salt$hash",
            admin_ind="N",
            public_ind="Y",
        )
        mock_get_user.return_value = user_no_email
        mock_verify_password.return_value = True
        mock_auth0_service.sync_user_to_auth0.return_value = {"user_id": "auth0|123"}

        # Call function
        result = authenticate_user_flexible(self.mock_db, "testuser", "password")

        # Assertions
        assert result == user_no_email
        mock_auth0_service.sync_user_to_auth0.assert_called_once_with(
            username="testuser",
            email=None,
            name="testuser",
            password="password",
            user_id=1,
        )

    @patch("app.crud.user.auth0_service")
    @patch("app.crud.user.verify_password")
    @patch("app.crud.user.get_user_by_name")
    def test_authenticate_user_flexible_auth0_service_disabled(
        self, mock_get_user, mock_verify_password, mock_auth0_service
    ):
        """Test authentication when Auth0 service is disabled."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_verify_password.return_value = True
        mock_auth0_service.sync_user_to_auth0.return_value = None  # Disabled service

        # Call function
        result = authenticate_user_flexible(self.mock_db, "testuser", "password")

        # Assertions
        assert result == self.mock_user
        mock_auth0_service.sync_user_to_auth0.assert_called_once_with(
            username="testuser",
            email="test@example.com",
            name="testuser",
            password="password",
            user_id=1,
        )

    @patch("app.crud.user.auth0_service")
    @patch("app.crud.user.verify_password")
    @patch("app.crud.user.get_user_by_name")
    def test_authenticate_user_flexible_auth0_sync_returns_none(
        self, mock_get_user, mock_verify_password, mock_auth0_service
    ):
        """Test authentication when Auth0 sync returns None (service disabled)."""
        # Setup mocks
        mock_get_user.return_value = self.mock_user
        mock_verify_password.return_value = True
        mock_auth0_service.sync_user_to_auth0.return_value = None

        # Call function
        result = authenticate_user_flexible(self.mock_db, "testuser", "password")

        # Assertions
        assert result == self.mock_user  # Authentication should still succeed
        mock_auth0_service.sync_user_to_auth0.assert_called_once_with(
            username="testuser",
            email="test@example.com",
            name="testuser",
            password="password",
            user_id=1,
        )
