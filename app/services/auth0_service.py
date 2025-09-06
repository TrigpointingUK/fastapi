"""
Auth0 Management API service for user synchronization.

This service handles:
- Obtaining Auth0 Management API access tokens
- Creating new Auth0 users
- Updating existing Auth0 users
- Graceful error handling with detailed logging
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import boto3
import requests
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Auth0Service:
    """Service for interacting with Auth0 Management API."""

    def __init__(self):
        """Initialize the Auth0 service."""
        self.domain = settings.AUTH0_DOMAIN
        self.secret_name = settings.AUTH0_SECRET_NAME
        self.connection = settings.AUTH0_CONNECTION
        self.enabled = settings.AUTH0_ENABLED
        self._access_token = None
        self._token_expires_at = None

        if not self.enabled:
            logger.info("Auth0 integration is disabled")
            return

        if not self.domain or not self.secret_name:
            logger.warning("Auth0 domain or secret name not configured")
            self.enabled = False
            return

    def _get_auth0_credentials(self) -> Optional[Dict[str, str]]:
        """
        Retrieve Auth0 credentials from AWS Secrets Manager.

        Returns:
            Dictionary containing Auth0 credentials or None if failed
        """
        if not self.enabled:
            return None

        try:
            # Create a Secrets Manager client
            session = boto3.session.Session()
            client = session.client(
                service_name="secretsmanager",
                region_name="us-west-2",  # TODO: Make this configurable
            )

            # Retrieve the secret
            response = client.get_secret_value(SecretId=self.secret_name)
            secret_data = json.loads(response["SecretString"])

            log_data = {
                "event": "auth0_credentials_retrieved",
                "secret_name": self.secret_name,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return secret_data

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            log_data = {
                "event": "auth0_credentials_retrieval_failed",
                "error_type": "ClientError",
                "error_code": error_code,
                "error_message": error_message,
                "secret_name": self.secret_name,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }

            if error_code == "DecryptionFailureException":
                log_data["error_description"] = (
                    "Auth0 credentials could not be decrypted"
                )
            elif error_code == "InternalServiceErrorException":
                log_data["error_description"] = (
                    "AWS internal service error retrieving Auth0 credentials"
                )
            elif error_code == "InvalidParameterException":
                log_data["error_description"] = (
                    "Invalid parameter retrieving Auth0 credentials"
                )
            elif error_code == "InvalidRequestException":
                log_data["error_description"] = (
                    "Invalid request retrieving Auth0 credentials"
                )
            elif error_code == "ResourceNotFoundException":
                log_data["error_description"] = "Auth0 secret not found"
            else:
                log_data["error_description"] = (
                    "Unexpected error retrieving Auth0 credentials"
                )

            logger.error(json.dumps(log_data))
            return None

        except Exception as e:
            log_data = {
                "event": "auth0_credentials_retrieval_failed",
                "error_type": "UnexpectedError",
                "error_message": str(e),
                "secret_name": self.secret_name,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None

    def _get_access_token(self) -> Optional[str]:
        """
        Get a valid Auth0 Management API access token.

        Returns:
            Access token string or None if failed
        """
        if not self.enabled:
            return None

        # Check if we have a valid cached token
        if (
            self._access_token
            and self._token_expires_at
            and datetime.now(timezone.utc) < self._token_expires_at
        ):
            return self._access_token

        # Get credentials
        credentials = self._get_auth0_credentials()
        if not credentials:
            return None

        try:
            # Request access token
            token_url = f"https://{self.domain}/oauth/token"
            payload = {
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"],
                "audience": credentials["audience"],
                "grant_type": "client_credentials",
            }

            response = requests.post(token_url, json=payload, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]

            # Set expiration time (with 5 minute buffer)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=expires_in - 300
            )

            log_data = {
                "event": "auth0_access_token_obtained",
                "domain": self.domain,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return self._access_token

        except requests.exceptions.RequestException as e:
            # Try to get response details if available
            response_details = {}
            if hasattr(e, "response") and e.response is not None:
                response_details = {
                    "status_code": e.response.status_code,
                    "response_text": e.response.text,
                    "response_headers": dict(e.response.headers),
                }
                try:
                    response_details["error_response"] = e.response.json()
                except (ValueError, KeyError):
                    pass

            log_data = {
                "event": "auth0_access_token_failed",
                "error_type": "RequestException",
                "error_message": str(e),
                "domain": self.domain,
                "token_url": f"https://{self.domain}/oauth/token",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                **response_details,
            }
            logger.error(json.dumps(log_data))
            return None
        except Exception as e:
            log_data = {
                "event": "auth0_access_token_failed",
                "error_type": "UnexpectedError",
                "error_message": str(e),
                "domain": self.domain,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None

    def _make_auth0_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make a request to the Auth0 Management API.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            endpoint: API endpoint (without domain)
            data: Request data for POST/PATCH requests

        Returns:
            Response data as dictionary or None if failed
        """
        if not self.enabled:
            return None

        access_token = self._get_access_token()
        if not access_token:
            return None

        try:
            url = f"https://{self.domain}/api/v2/{endpoint}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response = requests.request(
                method=method, url=url, headers=headers, json=data, timeout=10
            )

            # Log successful requests
            if response.status_code == 200 or response.status_code == 201:
                log_data = {
                    "event": "auth0_api_request_success",
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "url": url,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return response.json()
            else:
                # Log failed requests with detailed error information
                try:
                    error_response = response.json()
                except (ValueError, KeyError):
                    error_response = {"raw_response": response.text}

                log_data = {
                    "event": "auth0_api_request_failed",
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "url": url,
                    "error_response": error_response,
                    "response_headers": dict(response.headers),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.error(json.dumps(log_data))
                return None

        except requests.exceptions.RequestException as e:
            # Try to get response details if available
            response_details = {}
            if hasattr(e, "response") and e.response is not None:
                response_details = {
                    "status_code": e.response.status_code,
                    "response_text": e.response.text,
                    "response_headers": dict(e.response.headers),
                }
                try:
                    response_details["error_response"] = e.response.json()
                except (ValueError, KeyError):
                    pass

            log_data = {
                "event": "auth0_api_request_failed",
                "error_type": "RequestException",
                "error_message": str(e),
                "method": method,
                "endpoint": endpoint,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                **response_details,
            }
            logger.error(json.dumps(log_data))
            return None
        except Exception as e:
            log_data = {
                "event": "auth0_api_request_failed",
                "error_type": "UnexpectedError",
                "error_message": str(e),
                "method": method,
                "endpoint": endpoint,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None

    def find_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Find a user by username in Auth0.

        Args:
            username: Username to search for

        Returns:
            User data dictionary or None if not found
        """
        if not self.enabled:
            return None

        # Search for user by username - try multiple search formats
        endpoint = f'users?q=username:"{username}"&search_engine=v3'
        log_data = {
            "event": "auth0_user_search_by_username_started",
            "username": username,
            "endpoint": endpoint,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        response = self._make_auth0_request("GET", endpoint)

        if response and isinstance(response, list) and len(response) > 0:
            # Filter users by connection since Auth0 API doesn't support connection filtering in search
            filtered_users = self._filter_users_by_connection(response, self.connection)

            if filtered_users:
                log_data = {
                    "event": "auth0_user_found_by_username",
                    "username": username,
                    "auth0_user_id": filtered_users[0].get("user_id", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return filtered_users[0]
            else:
                log_data = {
                    "event": "auth0_user_not_found_by_username_connection_filtered",
                    "username": username,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return None
        else:
            log_data = {
                "event": "auth0_user_not_found_by_username",
                "username": username,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return None

    def find_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Find a user by email in Auth0.

        Args:
            email: Email address to search for

        Returns:
            User data dictionary or None if not found
        """
        if not self.enabled:
            return None

        log_data = {
            "event": "auth0_find_user_by_email_called",
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        # Search for user by email
        endpoint = f'users?q=email:"{email}"&search_engine=v3'
        response = self._make_auth0_request("GET", endpoint)

        if response and isinstance(response, list) and len(response) > 0:
            # Filter users by connection since Auth0 API doesn't support connection filtering in search
            filtered_users = self._filter_users_by_connection(response, self.connection)

            if filtered_users:
                log_data = {
                    "event": "auth0_user_found_by_email",
                    "email": email,
                    "auth0_user_id": filtered_users[0].get("user_id", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return filtered_users[0]
            else:
                log_data = {
                    "event": "auth0_user_not_found_by_email_connection_filtered",
                    "email": email,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return None
        else:
            log_data = {
                "event": "auth0_user_not_found_by_email",
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return None

    def find_user_comprehensive(
        self, username: str, email: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find a user using multiple search strategies.

        Args:
            username: Username to search for
            email: Email address to search for (optional)

        Returns:
            User data dictionary or None if not found
        """
        if not self.enabled:
            return None

        # Try username search first
        log_data = {
            "event": "auth0_comprehensive_search_username_attempt",
            "username": username,
            "connection": str(
                self.connection
            ),  # Convert to string to handle MagicMock in tests
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        user = self.find_user_by_username(username)
        if user:
            log_data = {
                "event": "auth0_comprehensive_search_username_success",
                "username": username,
                "auth0_user_id": user.get("user_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return user

        # If email provided, try email search
        if email:
            log_data = {
                "event": "auth0_comprehensive_search_email_attempt",
                "username": username,
                "email": email,
                "connection": str(
                    self.connection
                ),  # Convert to string to handle MagicMock in tests
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))

            user = self.find_user_by_email(email)
            if user:
                log_data = {
                    "event": "auth0_comprehensive_search_email_success",
                    "username": username,
                    "email": email,
                    "auth0_user_id": user.get("user_id", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return user

        # Try searching by username without quotes (fallback)
        if not user:
            log_data = {
                "event": "auth0_comprehensive_search_fallback_attempt",
                "username": username,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            try:
                endpoint = f"users?q=username:{username}&search_engine=v3"
                response = self._make_auth0_request("GET", endpoint)
                if response and isinstance(response, list) and len(response) > 0:
                    # Filter users by connection since Auth0 API doesn't support connection filtering in search
                    filtered_users = self._filter_users_by_connection(
                        response, self.connection
                    )

                    if filtered_users:
                        log_data = {
                            "event": "auth0_user_found_by_username_fallback",
                            "username": username,
                            "auth0_user_id": filtered_users[0].get("user_id", ""),
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                        }
                        logger.info(json.dumps(log_data))
                        return filtered_users[0]
                    else:
                        log_data = {
                            "event": "auth0_user_not_found_by_username_fallback_connection_filtered",
                            "username": username,
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                        }
                        logger.info(json.dumps(log_data))
            except Exception as e:
                log_data = {
                    "event": "auth0_user_search_fallback_failed",
                    "username": username,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.warning(json.dumps(log_data))

        log_data = {
            "event": "auth0_comprehensive_search_no_user_found",
            "username": username,
            "email": email or "",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))
        return None

    def _filter_users_by_connection(
        self, users: List[Dict], connection: str
    ) -> List[Dict]:
        """
        Filter users by connection since Auth0 API doesn't support connection filtering in search.

        Args:
            users: List of user dictionaries from Auth0
            connection: Connection name to filter by

        Returns:
            Filtered list of users matching the connection
        """
        if not users:
            return []

        # Debug: Log the actual user data structure
        log_data = {
            "event": "auth0_users_debug_before_filtering",
            "total_users": len(users),
            "connection": str(
                connection
            ),  # Convert to string to handle MagicMock in tests
            "users_sample": [
                {
                    "user_id": user.get("user_id", ""),
                    "username": user.get("username", ""),
                    "email": user.get("email", ""),
                    "identities": user.get("identities", []),
                }
                for user in users[:3]  # Log first 3 users for debugging
            ],
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        filtered_users = [
            user
            for user in users
            if user.get("identities")
            and len(user.get("identities", [])) > 0
            and user.get("identities", [{}])[0].get("connection") == connection
        ]

        log_data = {
            "event": "auth0_users_filtered_by_connection",
            "total_users": len(users),
            "filtered_users": len(filtered_users),
            "connection": str(
                connection
            ),  # Convert to string to handle MagicMock in tests
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        return filtered_users

    def create_user(
        self,
        username: str,
        email: Optional[str],
        name: str,
        password: str,
        user_id: int,
        firstname: Optional[str] = None,
        surname: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create a new user in Auth0.

        Args:
            username: Username for the new user
            email: Email address (optional)
            name: Display name
            password: Password for the new user
            user_id: Legacy user ID to store in app_metadata
            firstname: First name for given_name field (optional)
            surname: Surname for family_name field (optional)

        Returns:
            Created user data dictionary or None if failed
        """
        if not self.enabled:
            return None

        user_data = {
            "connection": self.connection,
            "username": username,
            "name": name,
            "password": password,
            "email_verified": False,
            "verify_email": False,
            "app_metadata": {
                "legacy_user_id": user_id,
            },
        }

        # Add profile fields if provided
        if firstname:
            user_data["given_name"] = firstname
        if surname:
            user_data["family_name"] = surname
        if username:
            user_data["nickname"] = username

        if email:
            user_data["email"] = email
            user_data["email_verified"] = True

        log_data = {
            "event": "auth0_user_creation_api_call",
            "username": username,
            "email": email or "",
            "connection": self.connection,
            "user_data": user_data,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        response = self._make_auth0_request("POST", "users", user_data)

        if response:
            log_data = {
                "event": "auth0_user_created",
                "username": username,
                "email": email or "",
                "auth0_user_id": response.get("user_id") or "",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
        else:
            # Check if this is a user already exists error
            log_data = {
                "event": "auth0_user_creation_failedxxxxx",
                "username": username,
                "email": email or "",
                "connection": self.connection,
                "user_data": user_data,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))

            # Try to find the existing user and return it instead of failing
            log_data = {
                "event": "auth0_user_creation_conflict_attempting_fallback",
                "username": username,
                "email": email or "",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.warning(json.dumps(log_data))

            # Try to find the existing user
            existing_user = self.find_user_comprehensive(username, email)
            if existing_user:
                log_data = {
                    "event": "auth0_user_creation_conflict_resolved",
                    "username": username,
                    "email": email or "",
                    "auth0_user_id": existing_user.get("user_id", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return existing_user

        return response

    def update_user_email(self, user_id: str, email: str) -> bool:
        """
        Update a user's email address in Auth0.

        Args:
            user_id: Auth0 user ID
            email: New email address

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        user_data = {"email": email, "email_verified": True}

        response = self._make_auth0_request("PATCH", f"users/{user_id}", user_data)

        if response:
            log_data = {
                "event": "auth0_user_email_updated",
                "user_id": user_id,
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return True
        else:
            log_data = {
                "event": "auth0_user_email_update_failed",
                "user_id": user_id,
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return False

    def update_user_profile(
        self,
        user_id: str,
        firstname: Optional[str] = None,
        surname: Optional[str] = None,
        nickname: Optional[str] = None,
    ) -> bool:
        """
        Update a user's profile fields in Auth0.

        Args:
            user_id: Auth0 user ID
            firstname: First name for given_name field (optional)
            surname: Surname for family_name field (optional)
            nickname: Nickname field (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        user_data = {}
        if firstname is not None:
            user_data["given_name"] = firstname
        if surname is not None:
            user_data["family_name"] = surname
        if nickname is not None:
            user_data["nickname"] = nickname

        if not user_data:
            # No fields to update
            return True

        response = self._make_auth0_request("PATCH", f"users/{user_id}", user_data)

        if response:
            log_data = {
                "event": "auth0_user_profile_updated",
                "user_id": user_id,
                "updated_fields": list(user_data.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return True
        else:
            log_data = {
                "event": "auth0_user_profile_update_failed",
                "user_id": user_id,
                "updated_fields": list(user_data.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return False

    def sync_user_to_auth0(
        self,
        username: str,
        email: Optional[str],
        name: str,
        password: str,
        user_id: int,
        firstname: Optional[str] = None,
        surname: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Sync a user to Auth0, creating or updating as needed.

        This is the main method that should be called after successful authentication.

        Args:
            username: Username from legacy database
            email: Email address from legacy database (optional)
            name: Display name from legacy database
            password: Password from legacy database
            user_id: User ID from legacy database
            firstname: First name from legacy database (optional)
            surname: Surname from legacy database (optional)

        Returns:
            Auth0 user data dictionary or None if sync failed
        """
        log_data = {
            "event": "auth0_sync_method_called",
            "username": username,
            "email": email or "",
            "user_id": user_id,
            "enabled": self.enabled,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        if not self.enabled:
            log_data = {
                "event": "auth0_sync_skipped",
                "reason": "service_disabled",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return None

        log_data = {
            "event": "auth0_user_sync_started",
            "username": username,
            "email": email or "",
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        try:
            # Use comprehensive search to find user
            log_data = {
                "event": "auth0_user_search_started",
                "username": username,
                "email": email or "",
                "connection": str(self.connection),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))

            auth0_user = self.find_user_comprehensive(username, email)

            log_data = {
                "event": "auth0_user_search_completed",
                "username": username,
                "email": email or "",
                "user_found": str(auth0_user is not None),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))

            if auth0_user:
                log_data = {
                    "event": "auth0_user_found_during_sync",
                    "username": username,
                    "email": email or "",
                    "auth0_user_id": auth0_user.get("user_id", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                # User exists, check if email or profile needs updating
                current_email = auth0_user.get("email")
                if email and current_email != email:
                    log_data = {
                        "event": "auth0_user_email_update_started",
                        "username": username,
                        "old_email": current_email or "",
                        "new_email": email or "",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                    }
                    logger.info(json.dumps(log_data))
                    self.update_user_email(auth0_user["user_id"], email)
                    auth0_user["email"] = email

                # Check if profile fields need updating
                current_given_name = auth0_user.get("given_name")
                current_family_name = auth0_user.get("family_name")
                current_nickname = auth0_user.get("nickname")

                profile_updated = False
                if (
                    (firstname and current_given_name != firstname)
                    or (surname and current_family_name != surname)
                    or (username and current_nickname != username)
                ):
                    log_data = {
                        "event": "auth0_user_profile_update_started",
                        "username": username,
                        "old_given_name": current_given_name or "",
                        "new_given_name": firstname or "",
                        "old_family_name": current_family_name or "",
                        "new_family_name": surname or "",
                        "old_nickname": current_nickname or "",
                        "new_nickname": username or "",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                    }
                    logger.info(json.dumps(log_data))
                    self.update_user_profile(
                        auth0_user["user_id"],
                        firstname=firstname,
                        surname=surname,
                        nickname=username,
                    )
                    profile_updated = True

                log_data = {
                    "event": "auth0_user_sync_completed_updated",
                    "username": username,
                    "auth0_user_id": auth0_user["user_id"],
                    "profile_updated": str(profile_updated),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return auth0_user
            else:
                # User doesn't exist, create new one
                log_data = {
                    "event": "auth0_user_not_found_during_sync",
                    "username": username,
                    "email": email or "",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))

                log_data = {
                    "event": "auth0_user_creation_started",
                    "username": username,
                    "email": email or "",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return self.create_user(
                    username, email, name, password, user_id, firstname, surname
                )

        except Exception as e:
            log_data = {
                "event": "auth0_user_sync_failed",
                "error_type": "UnexpectedError",
                "error_message": str(e),
                "username": username,
                "email": email or "",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None


# Global instance
auth0_service = Auth0Service()
