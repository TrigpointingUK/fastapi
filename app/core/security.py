"""
Security utilities for JWT authentication and password hashing.

This module uses PyJWT for JWT token handling, which is the recommended library
for FastAPI applications and is sponsored by Auth0 for long-term compatibility.
"""

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
import requests
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
        self.api_audience = settings.AUTH0_API_AUDIENCE  # Use configured API audience
        self.jwks_url = (
            f"https://{self.domain}/.well-known/jwks.json" if self.domain else None
        )
        self._jwks_cache = None
        self._jwks_cache_expires = None

    def _jwk_to_public_key(self, jwk: Dict[str, Any]) -> Any:
        """Convert a JWK to a public key for PyJWT validation."""
        try:
            # For RSA keys, we need to construct the public key from the JWK components
            if jwk.get("kty") == "RSA":
                # Decode the base64url encoded values
                n = base64.urlsafe_b64decode(jwk["n"] + "==")
                e = base64.urlsafe_b64decode(jwk["e"] + "==")

                # Convert to integers
                n_int = int.from_bytes(n, byteorder="big")
                e_int = int.from_bytes(e, byteorder="big")

                # Create RSA public key
                from cryptography.hazmat.primitives.asymmetric import rsa

                public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
                return public_key
            else:
                # For other key types, we might need different handling
                # For now, return the JWK as-is and let PyJWT handle it
                return jwk
        except Exception as e:
            log_data = {
                "event": "jwk_to_public_key_failed",
                "error": str(e),
                "jwk_kty": jwk.get("kty"),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None

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

    def validate_auth0_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an Auth0 access token and return user information.

        Args:
            token: Auth0 access token

        Returns:
            Dictionary containing user information or None if invalid
        """
        if not self.domain:
            log_data = {
                "event": "auth0_token_validation_failed",
                "reason": "no_auth0_domain_configured",
                "domain": self.domain,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            raise ValueError("AUTH0_DOMAIN is required but not configured")

        try:
            # Get audience for validation
            audience = self.api_audience
            if not audience:
                log_data = {
                    "event": "auth0_token_validation_failed",
                    "reason": "no_api_audience_configured",
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

            # Decode the token header to get the key ID
            try:
                unverified_header = jwt.get_unverified_header(token)
                kid = unverified_header.get("kid")
            except Exception as e:
                log_data = {
                    "event": "auth0_token_validation_failed",
                    "reason": "invalid_token_header",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.error(json.dumps(log_data))
                return None

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
            jwk = None
            available_kids = [key.get("kid") for key in jwks.get("keys", [])]
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    jwk = key
                    break

            if not jwk:
                log_data = {
                    "event": "auth0_token_validation_failed",
                    "reason": "key_not_found",
                    "kid": kid,
                    "available_kids": available_kids,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.error(json.dumps(log_data))
                return None

            # Convert JWK to public key for PyJWT
            public_key = self._jwk_to_public_key(jwk)
            if not public_key:
                log_data = {
                    "event": "auth0_token_validation_failed",
                    "reason": "jwk_conversion_failed",
                    "kid": kid,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                }
                logger.error(json.dumps(log_data))
                return None

            # Validate token using PyJWT
            payload = jwt.decode(
                token,
                public_key,
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

            # Add required fields for authentication logic
            return {
                **payload,
                "token_type": "auth0",
                "auth0_user_id": payload.get("sub"),
            }

        except jwt.ExpiredSignatureError:
            log_data = {
                "event": "auth0_token_validation_failed",
                "reason": "expired_signature",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            }
            logger.error(json.dumps(log_data))
            return None
        except jwt.InvalidTokenError as e:
            log_data = {
                "event": "auth0_token_validation_failed",
                "reason": "invalid_token",
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


# def validate_legacy_jwt_token(token: str) -> Optional[Dict[str, Any]]:
#     """
#     Validate a legacy JWT token created by our own system.

#     Args:
#         token: Legacy JWT token

#     Returns:
#         Dictionary containing token payload or None if invalid
#     """
#     try:
#         payload = jwt.decode(
#             token,
#             settings.JWT_SECRET_KEY,
#             algorithms=[settings.JWT_ALGORITHM],
#         )

#         log_data = {
#             "event": "legacy_jwt_token_validated",
#             "sub": payload.get("sub", ""),
#             "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
#         }
#         logger.debug(json.dumps(log_data))

#         return payload

#     except jwt.ExpiredSignatureError:
#         log_data = {
#             "event": "legacy_jwt_token_validation_failed",
#             "reason": "expired_signature",
#             "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
#         }
#         logger.debug(json.dumps(log_data))
#         return None
#     except jwt.InvalidTokenError as e:
#         log_data = {
#             "event": "legacy_jwt_token_validation_failed",
#             "reason": "invalid_token",
#             "error": str(e),
#             "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
#         }
#         logger.debug(json.dumps(log_data))
#         return None
#     except Exception as e:
#         log_data = {
#             "event": "legacy_jwt_token_validation_failed",
#             "reason": "unexpected_error",
#             "error": str(e),
#             "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
#         }
#         logger.error(json.dumps(log_data))
#         return None


# def validate_any_token(token: str) -> Optional[Dict[str, Any]]:
#     """
#     Validate either a legacy JWT token or Auth0 access token.

#     Args:
#         token: JWT token (legacy or Auth0)

#     Returns:
#         Dictionary containing token payload and token type, or None if invalid
#     """
#     # If Auth0 is enabled, only accept Auth0 tokens
#     if settings.AUTH0_ENABLED:
#         auth0_payload = auth0_validator.validate_auth0_token(token)
#         if auth0_payload:
#             return {
#                 **auth0_payload,
#                 "token_type": "auth0",
#                 "auth0_user_id": auth0_payload.get("sub"),
#             }
#         return None

#     # Otherwise (development), accept legacy first then Auth0
#     legacy_payload = validate_legacy_jwt_token(token)
#     if legacy_payload:
#         return {
#             **legacy_payload,
#             "token_type": "legacy",
#             "user_id": int(legacy_payload.get("sub", 0)),
#         }
#     auth0_payload = auth0_validator.validate_auth0_token(token)
#     if auth0_payload:
#         return {
#             **auth0_payload,
#             "token_type": "auth0",
#             "auth0_user_id": auth0_payload.get("sub"),
#         }

#     return None


def extract_scopes(token_payload: Dict[str, Any]) -> set[str]:
    """Extract scopes from Auth0 token payload supporting 'scope' string or 'permissions' list."""
    scopes: set[str] = set()
    if not token_payload:
        return scopes
    if "scope" in token_payload and isinstance(token_payload["scope"], str):
        scopes.update(s for s in token_payload["scope"].split() if s)
    if "permissions" in token_payload and isinstance(
        token_payload["permissions"], list
    ):
        scopes.update(str(s) for s in token_payload["permissions"])
    return scopes
