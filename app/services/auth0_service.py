"""
Auth0 Management API service for user synchronization.

This service handles:
- Obtaining Auth0 Management API access tokens
- Creating new Auth0 users
- Updating existing Auth0 users
- Graceful error handling with detailed logging
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

import boto3
import requests
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


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
                "timestamp": datetime.utcnow().isoformat() + "Z",
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
                "timestamp": datetime.utcnow().isoformat() + "Z",
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
                "timestamp": datetime.utcnow().isoformat() + "Z",
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
            and datetime.utcnow() < self._token_expires_at
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
            self._token_expires_at = datetime.utcnow() + timedelta(
                seconds=expires_in - 300
            )

            log_data = {
                "event": "auth0_access_token_obtained",
                "domain": self.domain,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return self._access_token

        except requests.exceptions.RequestException as e:
            log_data = {
                "event": "auth0_access_token_failed",
                "error_type": "RequestException",
                "error_message": str(e),
                "domain": self.domain,
                "status_code": getattr(e.response, "status_code", None),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None
        except Exception as e:
            log_data = {
                "event": "auth0_access_token_failed",
                "error_type": "UnexpectedError",
                "error_message": str(e),
                "domain": self.domain,
                "timestamp": datetime.utcnow().isoformat() + "Z",
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

            # Log the request details
            logger.info(
                "Auth0 API request",
                extra={
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "url": url,
                },
            )

            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            else:
                logger.warning(
                    "Auth0 API request failed",
                    extra={
                        "method": method,
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "response_text": response.text,
                        "url": url,
                    },
                )
                return None

        except requests.exceptions.RequestException as e:
            log_data = {
                "event": "auth0_api_request_failed",
                "error_type": "RequestException",
                "error_message": str(e),
                "method": method,
                "endpoint": endpoint,
                "url": url,
                "timestamp": datetime.utcnow().isoformat() + "Z",
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
                "timestamp": datetime.utcnow().isoformat() + "Z",
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

        # Search for user by username
        endpoint = f"users?q=username:{username}&search_engine=v3"
        response = self._make_auth0_request("GET", endpoint)

        if response and "users" in response and len(response["users"]) > 0:
            return response["users"][0]
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

        # Search for user by email
        endpoint = f"users?q=email:{email}&search_engine=v3"
        response = self._make_auth0_request("GET", endpoint)

        if response and "users" in response and len(response["users"]) > 0:
            return response["users"][0]
        return None

    def create_user(
        self, username: str, email: Optional[str], name: str
    ) -> Optional[Dict]:
        """
        Create a new user in Auth0.

        Args:
            username: Username for the new user
            email: Email address (optional)
            name: Display name

        Returns:
            Created user data dictionary or None if failed
        """
        if not self.enabled:
            return None

        user_data = {
            "connection": self.connection,
            "username": username,
            "name": name,
            "email_verified": False,
            "verify_email": False,
        }

        if email:
            user_data["email"] = email
            user_data["email_verified"] = True

        response = self._make_auth0_request("POST", "users", user_data)

        if response:
            log_data = {
                "event": "auth0_user_created",
                "username": username,
                "email": email or "",
                "auth0_user_id": response.get("user_id") or "",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
        else:
            log_data = {
                "event": "auth0_user_creation_failed",
                "username": username,
                "email": email or "",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))

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
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return True
        else:
            log_data = {
                "event": "auth0_user_email_update_failed",
                "user_id": user_id,
                "email": email,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return False

    def sync_user_to_auth0(
        self, username: str, email: Optional[str], name: str
    ) -> Optional[Dict]:
        """
        Sync a user to Auth0, creating or updating as needed.

        This is the main method that should be called after successful authentication.

        Args:
            username: Username from legacy database
            email: Email address from legacy database (optional)
            name: Display name from legacy database

        Returns:
            Auth0 user data dictionary or None if sync failed
        """
        if not self.enabled:
            log_data = {
                "event": "auth0_sync_skipped",
                "reason": "service_disabled",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))
            return None

        log_data = {
            "event": "auth0_user_sync_started",
            "username": username,
            "email": email or "",
            "name": name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        logger.info(json.dumps(log_data))

        try:
            # First, try to find user by username
            auth0_user = self.find_user_by_username(username)

            if auth0_user:
                # User exists, check if email needs updating
                current_email = auth0_user.get("email")
                if email and current_email != email:
                    log_data = {
                        "event": "auth0_user_email_update_started",
                        "username": username,
                        "old_email": current_email or "",
                        "new_email": email or "",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                    logger.info(json.dumps(log_data))
                    self.update_user_email(auth0_user["user_id"], email)
                    auth0_user["email"] = email

                log_data = {
                    "event": "auth0_user_sync_completed_updated",
                    "username": username,
                    "auth0_user_id": auth0_user["user_id"],
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return auth0_user
            else:
                # User doesn't exist, create new one
                log_data = {
                    "event": "auth0_user_creation_started",
                    "username": username,
                    "email": email or "",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                logger.info(json.dumps(log_data))
                return self.create_user(username, email, name)

        except Exception as e:
            log_data = {
                "event": "auth0_user_sync_failed",
                "error_type": "UnexpectedError",
                "error_message": str(e),
                "username": username,
                "email": email or "",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None


# Global instance
auth0_service = Auth0Service()
