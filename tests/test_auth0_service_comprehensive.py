"""
Comprehensive tests for Auth0Service to improve code coverage.
"""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from app.services.auth0_service import Auth0Service


class TestAuth0ServiceComprehensive:
    """Comprehensive tests for Auth0Service to improve coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user_data = {
            "user_id": "auth0|123456789",
            "email": "test@example.com",
            "name": "Test User",
            "username": "testuser",
            "identities": [
                {"connection": "Username-Password-Authentication", "provider": "auth0"}
            ],
        }

    @patch("app.services.auth0_service.settings")
    def test_init_disabled(self, mock_settings):
        """Test Auth0Service initialization when disabled."""
        mock_settings.AUTH0_ENABLED = False
        mock_settings.AUTH0_DOMAIN = None
        mock_settings.AUTH0_SECRET_NAME = None
        mock_settings.AUTH0_CONNECTION = "test-connection"

        service = Auth0Service()
        assert not service.enabled
        assert service.domain is None
        assert service.secret_name is None

    @patch("app.services.auth0_service.settings")
    def test_init_missing_config(self, mock_settings):
        """Test Auth0Service initialization with missing configuration."""
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = None
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        service = Auth0Service()
        assert not service.enabled

    @patch("app.services.auth0_service.settings")
    def test_init_missing_secret_name(self, mock_settings):
        """Test Auth0Service initialization with missing secret name."""
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = None
        mock_settings.AUTH0_CONNECTION = "test-connection"

        service = Auth0Service()
        assert not service.enabled

    @patch("app.services.auth0_service.boto3.session.Session")
    def test_get_auth0_credentials_client_error_decryption(self, mock_session):
        """Test _get_auth0_credentials with DecryptionFailureException."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_SECRET_NAME = "test-secret"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.secret_name = "test-secret"

            # Mock ClientError for DecryptionFailureException
            mock_client = MagicMock()
            mock_client.get_secret_value.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "DecryptionFailureException",
                        "Message": "Decryption failed",
                    }
                },
                "GetSecretValue",
            )
            mock_session.return_value.client.return_value = mock_client

            result = service._get_auth0_credentials()
            assert result is None

    @patch("app.services.auth0_service.boto3.session.Session")
    def test_get_auth0_credentials_client_error_internal_service(self, mock_session):
        """Test _get_auth0_credentials with InternalServiceErrorException."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_SECRET_NAME = "test-secret"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.secret_name = "test-secret"

            # Mock ClientError for InternalServiceErrorException
            mock_client = MagicMock()
            mock_client.get_secret_value.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "InternalServiceErrorException",
                        "Message": "Internal error",
                    }
                },
                "GetSecretValue",
            )
            mock_session.return_value.client.return_value = mock_client

            result = service._get_auth0_credentials()
            assert result is None

    @patch("app.services.auth0_service.boto3.session.Session")
    def test_get_auth0_credentials_client_error_invalid_parameter(self, mock_session):
        """Test _get_auth0_credentials with InvalidParameterException."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_SECRET_NAME = "test-secret"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.secret_name = "test-secret"

            # Mock ClientError for InvalidParameterException
            mock_client = MagicMock()
            mock_client.get_secret_value.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "InvalidParameterException",
                        "Message": "Invalid parameter",
                    }
                },
                "GetSecretValue",
            )
            mock_session.return_value.client.return_value = mock_client

            result = service._get_auth0_credentials()
            assert result is None

    @patch("app.services.auth0_service.boto3.session.Session")
    def test_get_auth0_credentials_client_error_invalid_request(self, mock_session):
        """Test _get_auth0_credentials with InvalidRequestException."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_SECRET_NAME = "test-secret"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.secret_name = "test-secret"

            # Mock ClientError for InvalidRequestException
            mock_client = MagicMock()
            mock_client.get_secret_value.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "InvalidRequestException",
                        "Message": "Invalid request",
                    }
                },
                "GetSecretValue",
            )
            mock_session.return_value.client.return_value = mock_client

            result = service._get_auth0_credentials()
            assert result is None

    @patch("app.services.auth0_service.boto3.session.Session")
    def test_get_auth0_credentials_client_error_resource_not_found(self, mock_session):
        """Test _get_auth0_credentials with ResourceNotFoundException."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_SECRET_NAME = "test-secret"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.secret_name = "test-secret"

            # Mock ClientError for ResourceNotFoundException
            mock_client = MagicMock()
            mock_client.get_secret_value.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "ResourceNotFoundException",
                        "Message": "Resource not found",
                    }
                },
                "GetSecretValue",
            )
            mock_session.return_value.client.return_value = mock_client

            result = service._get_auth0_credentials()
            assert result is None

    @patch("app.services.auth0_service.boto3.session.Session")
    def test_get_auth0_credentials_client_error_unknown(self, mock_session):
        """Test _get_auth0_credentials with unknown ClientError."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_SECRET_NAME = "test-secret"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.secret_name = "test-secret"

            # Mock ClientError for unknown error
            mock_client = MagicMock()
            mock_client.get_secret_value.side_effect = ClientError(
                {"Error": {"Code": "UnknownError", "Message": "Unknown error"}},
                "GetSecretValue",
            )
            mock_session.return_value.client.return_value = mock_client

            result = service._get_auth0_credentials()
            assert result is None

    @patch("app.services.auth0_service.boto3.session.Session")
    def test_get_auth0_credentials_general_exception(self, mock_session):
        """Test _get_auth0_credentials with general exception."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_SECRET_NAME = "test-secret"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.secret_name = "test-secret"

            # Mock general exception
            mock_client = MagicMock()
            mock_client.get_secret_value.side_effect = Exception("General error")
            mock_session.return_value.client.return_value = mock_client

            result = service._get_auth0_credentials()
            assert result is None

    @patch("app.services.auth0_service.requests.post")
    def test_get_access_token_request_exception_with_response(self, mock_post):
        """Test _get_access_token with RequestException that has response details."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock credentials retrieval
            with patch.object(service, "_get_auth0_credentials") as mock_creds:
                mock_creds.return_value = {
                    "client_id": "test_client",
                    "client_secret": "test_secret",
                    "audience": "test_audience",
                }

                # Mock RequestException with response
                mock_response = MagicMock()
                mock_response.status_code = 400
                mock_response.text = "Bad Request"
                mock_response.headers = {"Content-Type": "application/json"}
                mock_response.json.return_value = {"error": "invalid_request"}

                mock_exception = Exception("Request failed")
                mock_exception.response = mock_response
                mock_post.side_effect = mock_exception

                result = service._get_access_token()
                assert result is None

    @patch("app.services.auth0_service.requests.post")
    def test_get_access_token_request_exception_without_response(self, mock_post):
        """Test _get_access_token with RequestException without response details."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock credentials retrieval
            with patch.object(service, "_get_auth0_credentials") as mock_creds:
                mock_creds.return_value = {
                    "client_id": "test_client",
                    "client_secret": "test_secret",
                    "audience": "test_audience",
                }

                # Mock RequestException without response
                mock_exception = Exception("Request failed")
                mock_exception.response = None
                mock_post.side_effect = mock_exception

                result = service._get_access_token()
                assert result is None

    @patch("app.services.auth0_service.requests.post")
    def test_get_access_token_general_exception(self, mock_post):
        """Test _get_access_token with general exception."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock credentials retrieval
            with patch.object(service, "_get_auth0_credentials") as mock_creds:
                mock_creds.return_value = {
                    "client_id": "test_client",
                    "client_secret": "test_secret",
                    "audience": "test_audience",
                }

                # Mock general exception
                mock_post.side_effect = Exception("General error")

                result = service._get_access_token()
                assert result is None

    @patch("app.services.auth0_service.requests.request")
    def test_make_auth0_request_success_201(self, mock_request):
        """Test _make_auth0_request with 201 success response."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock access token
            with patch.object(service, "_get_access_token") as mock_token:
                mock_token.return_value = "test_token"

                # Mock successful response
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {"id": "123", "name": "test"}
                mock_request.return_value = mock_response

                result = service._make_auth0_request("POST", "users", {"name": "test"})
                assert result == {"id": "123", "name": "test"}

    @patch("app.services.auth0_service.requests.request")
    def test_make_auth0_request_failure_with_json_error(self, mock_request):
        """Test _make_auth0_request with failure response containing JSON error."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock access token
            with patch.object(service, "_get_access_token") as mock_token:
                mock_token.return_value = "test_token"

                # Mock failure response with JSON error
                mock_response = MagicMock()
                mock_response.status_code = 400
                mock_response.json.return_value = {"error": "invalid_request"}
                mock_response.headers = {"Content-Type": "application/json"}
                mock_request.return_value = mock_response

                result = service._make_auth0_request("POST", "users", {"name": "test"})
                assert result is None

    @patch("app.services.auth0_service.requests.request")
    def test_make_auth0_request_failure_with_text_error(self, mock_request):
        """Test _make_auth0_request with failure response containing text error."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock access token
            with patch.object(service, "_get_access_token") as mock_token:
                mock_token.return_value = "test_token"

                # Mock failure response with text error
                mock_response = MagicMock()
                mock_response.status_code = 400
                mock_response.text = "Bad Request"
                mock_response.headers = {"Content-Type": "text/plain"}
                mock_response.json.side_effect = ValueError("Not JSON")
                mock_request.return_value = mock_response

                result = service._make_auth0_request("POST", "users", {"name": "test"})
                assert result is None

    @patch("app.services.auth0_service.requests.request")
    def test_make_auth0_request_exception_with_response(self, mock_request):
        """Test _make_auth0_request with RequestException that has response details."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock access token
            with patch.object(service, "_get_access_token") as mock_token:
                mock_token.return_value = "test_token"

                # Mock RequestException with response
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_response.headers = {"Content-Type": "text/plain"}
                mock_response.json.return_value = {"error": "server_error"}

                mock_exception = Exception("Request failed")
                mock_exception.response = mock_response
                mock_request.side_effect = mock_exception

                result = service._make_auth0_request("POST", "users", {"name": "test"})
                assert result is None

    @patch("app.services.auth0_service.requests.request")
    def test_make_auth0_request_exception_without_response(self, mock_request):
        """Test _make_auth0_request with RequestException without response details."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock access token
            with patch.object(service, "_get_access_token") as mock_token:
                mock_token.return_value = "test_token"

                # Mock RequestException without response
                mock_exception = Exception("Request failed")
                mock_exception.response = None
                mock_request.side_effect = mock_exception

                result = service._make_auth0_request("POST", "users", {"name": "test"})
                assert result is None

    @patch("app.services.auth0_service.requests.request")
    def test_make_auth0_request_general_exception(self, mock_request):
        """Test _make_auth0_request with general exception."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True
            service.domain = "test.auth0.com"

            # Mock access token
            with patch.object(service, "_get_access_token") as mock_token:
                mock_token.return_value = "test_token"

                # Mock general exception
                mock_request.side_effect = Exception("General error")

                result = service._make_auth0_request("POST", "users", {"name": "test"})
                assert result is None

    def test_find_user_by_username_disabled(self):
        """Test find_user_by_username when service is disabled."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = False

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            result = service.find_user_by_username("testuser")
            assert result is None

    def test_find_user_by_email_disabled(self):
        """Test find_user_by_email when service is disabled."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = False

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            result = service.find_user_by_email("test@example.com")
            assert result is None

    def test_find_user_comprehensive_disabled(self):
        """Test find_user_comprehensive when service is disabled."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = False

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            result = service.find_user_comprehensive("testuser", "test@example.com")
            assert result is None

    def test_create_user_disabled(self):
        """Test create_user when service is disabled."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = False

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            result = service.create_user(
                "testuser", "test@example.com", "Test User", "password", 1
            )
            assert result is None

    def test_update_user_email_disabled(self):
        """Test update_user_email when service is disabled."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = False

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            result = service.update_user_email("auth0|123", "new@example.com")
            assert result is False

    def test_update_user_profile_disabled(self):
        """Test update_user_profile when service is disabled."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = False

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            result = service.update_user_profile("auth0|123", "John", "Doe", "johndoe")
            assert result is False

    def test_sync_user_to_auth0_disabled(self):
        """Test sync_user_to_auth0 when service is disabled."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = False

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            result = service.sync_user_to_auth0(
                "testuser", "test@example.com", "Test User", "password", 1
            )
            assert result is None

    def test_update_user_profile_no_fields(self):
        """Test update_user_profile with no fields to update."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            # Test with no fields to update
            result = service.update_user_profile("auth0|123")
            assert result is True

    @patch("app.services.auth0_service.Auth0Service._make_auth0_request")
    def test_update_user_email_success(self, mock_request):
        """Test update_user_email success."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            mock_request.return_value = {
                "user_id": "auth0|123",
                "email": "new@example.com",
            }

            result = service.update_user_email("auth0|123", "new@example.com")
            assert result is True
            mock_request.assert_called_once_with(
                "PATCH",
                "users/auth0|123",
                {"email": "new@example.com", "email_verified": True},
            )

    @patch("app.services.auth0_service.Auth0Service._make_auth0_request")
    def test_update_user_email_failure(self, mock_request):
        """Test update_user_email failure."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            mock_request.return_value = None

            result = service.update_user_email("auth0|123", "new@example.com")
            assert result is False

    @patch("app.services.auth0_service.Auth0Service._make_auth0_request")
    def test_update_user_profile_success(self, mock_request):
        """Test update_user_profile success."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            mock_request.return_value = {"user_id": "auth0|123"}

            result = service.update_user_profile("auth0|123", "John", "Doe", "johndoe")
            assert result is True
            mock_request.assert_called_once_with(
                "PATCH",
                "users/auth0|123",
                {"given_name": "John", "family_name": "Doe", "nickname": "johndoe"},
            )

    @patch("app.services.auth0_service.Auth0Service._make_auth0_request")
    def test_update_user_profile_failure(self, mock_request):
        """Test update_user_profile failure."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            mock_request.return_value = None

            result = service.update_user_profile("auth0|123", "John", "Doe", "johndoe")
            assert result is False

    def test_filter_users_by_connection_empty_list(self):
        """Test _filter_users_by_connection with empty list."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            result = service._filter_users_by_connection([], "test-connection")
            assert result == []

    def test_filter_users_by_connection_no_matches(self):
        """Test _filter_users_by_connection with no matching connections."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            users = [
                {"user_id": "1", "identities": [{"connection": "other-connection"}]},
                {"user_id": "2", "identities": [{"connection": "another-connection"}]},
            ]

            result = service._filter_users_by_connection(users, "test-connection")
            assert result == []

    def test_filter_users_by_connection_with_matches(self):
        """Test _filter_users_by_connection with matching connections."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            users = [
                {"user_id": "1", "identities": [{"connection": "other-connection"}]},
                {"user_id": "2", "identities": [{"connection": "test-connection"}]},
                {"user_id": "3", "identities": [{"connection": "test-connection"}]},
            ]

            result = service._filter_users_by_connection(users, "test-connection")
            assert len(result) == 2
            assert result[0]["user_id"] == "2"
            assert result[1]["user_id"] == "3"

    def test_filter_users_by_connection_missing_identities(self):
        """Test _filter_users_by_connection with users missing identities."""
        mock_settings = MagicMock()
        mock_settings.AUTH0_ENABLED = True
        mock_settings.AUTH0_DOMAIN = "test.auth0.com"
        mock_settings.AUTH0_SECRET_NAME = "test-secret"
        mock_settings.AUTH0_CONNECTION = "test-connection"

        with patch("app.services.auth0_service.settings", mock_settings):
            service = Auth0Service()
            service.enabled = True

            users = [
                {"user_id": "1"},  # No identities key
                {"user_id": "2", "identities": []},  # Empty identities
                {"user_id": "3", "identities": [{"connection": "test-connection"}]},
            ]

            result = service._filter_users_by_connection(users, "test-connection")
            assert len(result) == 1
            assert result[0]["user_id"] == "3"
