"""
Security utilities for JWT authentication and password hashing.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import requests
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


class Auth0TokenValidator:
    """Validates Auth0 access tokens and extracts user information."""

    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.audience = None  # Will be set from Auth0 credentials
        self.jwks_url = (
            f"https://{self.domain}/.well-known/jwks.json" if self.domain else None
        )
        self._jwks_cache = None
        self._jwks_cache_expires = None

    def _get_jwks(self) -> Optional[Dict]:
        """Get JWKS (JSON Web Key Set) from Auth0 with caching."""
        if not self.jwks_url:
            return None

        # Check if we have a valid cached JWKS
        if (
            self._jwks_cache
            and self._jwks_cache_expires
            and datetime.now(timezone.utc) < self._jwks_cache_expires
        ):
            return self._jwks_cache

        try:
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()

            jwks = response.json()
            # Cache for 1 hour
            self._jwks_cache = jwks
            self._jwks_cache_expires = datetime.now(timezone.utc) + timedelta(hours=1)

            log_data = {
                "event": "auth0_jwks_retrieved",
                "domain": self.domain,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.debug(json.dumps(log_data))

            return jwks

        except Exception as e:
            log_data = {
                "event": "auth0_jwks_retrieval_failed",
                "error": str(e),
                "domain": self.domain,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None

    def _get_auth0_audience(self) -> Optional[str]:
        """Get Auth0 audience from credentials."""
        if self.audience:
            return self.audience

        # Try to get audience from Auth0 credentials
        try:
            from app.services.auth0_service import auth0_service

            credentials = auth0_service._get_auth0_credentials()
            if credentials and "audience" in credentials:
                self.audience = credentials["audience"]
                return self.audience
        except Exception as e:
            log_data = {
                "event": "auth0_audience_retrieval_failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.debug(json.dumps(log_data))

        return None

    def validate_auth0_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an Auth0 access token and return user information.

        Args:
            token: Auth0 access token

        Returns:
            Dictionary containing user information or None if invalid
        """
        if not self.domain or not settings.AUTH0_ENABLED:
            log_data = {
                "event": "auth0_token_validation_failed",
                "reason": "auth0_disabled_or_no_domain",
                "domain": self.domain,
                "enabled": settings.AUTH0_ENABLED,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.debug(json.dumps(log_data))
            return None

        try:
            # Get audience for validation
            audience = self._get_auth0_audience()
            if not audience:
                log_data = {
                    "event": "auth0_token_validation_failed",
                    "reason": "no_audience_configured",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.error(json.dumps(log_data))
                return None

            # Get JWKS for token validation
            jwks = self._get_jwks()
            if not jwks:
                log_data = {
                    "event": "auth0_token_validation_failed",
                    "reason": "jwks_retrieval_failed",
                    "domain": self.domain,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.error(json.dumps(log_data))
                return None

            # Use python-jose's get_unverified_header to get the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                log_data = {
                    "event": "auth0_token_validation_failed",
                    "reason": "no_kid_in_header",
                    "header": unverified_header,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.error(json.dumps(log_data))
                return None

            # Find the correct key from JWKS
            key = None
            available_kids = [jwk.get("kid") for jwk in jwks.get("keys", [])]
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break

            if not key:
                log_data = {
                    "event": "auth0_token_validation_failed",
                    "reason": "key_not_found",
                    "kid": kid,
                    "available_kids": available_kids,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.error(json.dumps(log_data))
                return None

            # Validate token using the JWK
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=audience,
                issuer=f"https://{self.domain}/",
            )

            log_data = {
                "event": "auth0_token_validated",
                "sub": payload.get("sub", ""),
                "aud": payload.get("aud", ""),
                "iss": payload.get("iss", ""),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.info(json.dumps(log_data))

            return payload

        except jwt.ExpiredSignatureError:
            log_data = {
                "event": "auth0_token_validation_failed",
                "reason": "expired_signature",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None
        except jwt.JWTClaimsError as e:
            log_data = {
                "event": "auth0_token_validation_failed",
                "reason": "jwt_claims_error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None
        except jwt.JWTError as e:
            log_data = {
                "event": "auth0_token_validation_failed",
                "reason": "jwt_error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None
        except Exception as e:
            log_data = {
                "event": "auth0_token_validation_failed",
                "reason": "unexpected_error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None


# Global Auth0 validator instance
auth0_validator = Auth0TokenValidator()


def validate_legacy_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a legacy JWT token created by our own system.

    Args:
        token: Legacy JWT token

    Returns:
        Dictionary containing token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        log_data = {
            "event": "legacy_jwt_token_validated",
            "sub": payload.get("sub", ""),
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.debug(json.dumps(log_data))

        return payload

    except jwt.ExpiredSignatureError:
        log_data = {
            "event": "legacy_jwt_token_validation_failed",
            "reason": "expired_signature",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.debug(json.dumps(log_data))
        return None
    except jwt.JWTError as e:
        log_data = {
            "event": "legacy_jwt_token_validation_failed",
            "reason": "jwt_error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.debug(json.dumps(log_data))
        return None
    except Exception as e:
        log_data = {
            "event": "legacy_jwt_token_validation_failed",
            "reason": "unexpected_error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.error(json.dumps(log_data))
        return None


def validate_any_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate either a legacy JWT token or Auth0 access token.

    Args:
        token: JWT token (legacy or Auth0)

    Returns:
        Dictionary containing token payload and token type, or None if invalid
    """
    # First try legacy JWT validation
    legacy_payload = validate_legacy_jwt_token(token)
    if legacy_payload:
        return {
            **legacy_payload,
            "token_type": "legacy",
            "user_id": int(legacy_payload.get("sub", 0)),
        }

    # Then try Auth0 validation
    auth0_payload = auth0_validator.validate_auth0_token(token)
    if auth0_payload:
        return {
            **auth0_payload,
            "token_type": "auth0",
            "auth0_user_id": auth0_payload.get("sub"),
        }

    return None
