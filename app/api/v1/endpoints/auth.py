"""
Authentication endpoints.
"""

from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, validate_any_token
from app.crud.user import (
    authenticate_user_flexible,
    get_user_by_auth0_id,
    update_user_auth0_id,
)
from app.db.database import get_db
from app.schemas.user import LoginResponse
from app.services.auth0_service import auth0_service
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Enhanced login endpoint returning JWT token + essential user data.

    Accepts either email address or username in the 'username' field.
    Auto-detects the type and authenticates accordingly.

    Returns:
    - JWT access token for API authentication
    - Essential user data (name, email if public, etc.)
    - Token expiration time

    This reduces the need for an immediate /user/me API call after login.

    Examples:
    - username: "john@example.com" (email)
    - username: "johndoe" (username)
    """
    user = authenticate_user_flexible(
        db, identifier=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Sync user to Auth0 and store mapping
    if settings.AUTH0_ENABLED and not user.auth0_user_id:
        try:
            auth0_user = auth0_service.sync_user_to_auth0(
                username=str(user.name),
                email=str(user.email) if user.email else None,
                name=f"{user.firstname} {user.surname}".strip() or str(user.name),
                password=form_data.password,  # This will be used for Auth0 user creation
                user_id=int(user.id),
                firstname=str(user.firstname),
                surname=str(user.surname),
            )

            if auth0_user:
                # Store Auth0 user ID mapping in the database
                update_user_auth0_id(
                    db=db,
                    user_id=int(user.id),
                    auth0_user_id=str(auth0_user.get("user_id")),
                )
        except Exception as e:
            # Log error but don't fail the login
            from app.core.logging import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to sync user to Auth0: {e}")

    # Create JWT token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )

    # Import here to avoid circular imports
    from app.api.v1.endpoints.user import filter_user_fields

    # Build user response with appropriate field filtering
    # For login response, user sees their own data (full access)
    user_data = filter_user_fields(user, current_user=user)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",  # nosec B106 - OAuth2 standard token type, not a password
        user=user_data,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )


@router.post("/auth0-login", response_model=LoginResponse)
def auth0_login(access_token: str, db: Session = Depends(get_db)):
    """
    Login endpoint for Auth0 access tokens.

    This endpoint validates Auth0 access tokens and returns user data.
    Used by Android app when authenticating via Auth0.

    Args:
        access_token: Auth0 access token
        db: Database session

    Returns:
        LoginResponse with user data
    """
    import json

    from app.api.v1.endpoints.user import filter_user_fields
    from app.core.logging import get_logger

    logger = get_logger(__name__)

    # Log the attempt
    log_data = {
        "event": "auth0_login_attempt",
        "token_length": len(access_token),
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }
    logger.info(json.dumps(log_data))

    # Validate the Auth0 token
    token_payload = validate_any_token(access_token)
    if not token_payload:
        log_data = {
            "event": "auth0_login_failed",
            "reason": "token_validation_failed",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.error(json.dumps(log_data))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Auth0 token - validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_payload.get("token_type") != "auth0":
        log_data = {
            "event": "auth0_login_failed",
            "reason": "not_auth0_token",
            "token_type": token_payload.get("token_type"),
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.error(json.dumps(log_data))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type: {token_payload.get('token_type')}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get Auth0 user ID from token
    auth0_user_id = token_payload.get("auth0_user_id")
    if not auth0_user_id:
        log_data = {
            "event": "auth0_login_failed",
            "reason": "no_auth0_user_id",
            "token_payload": {
                k: v for k, v in token_payload.items() if k != "auth0_user_id"
            },
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.error(json.dumps(log_data))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Auth0 token format - no user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find user in database by Auth0 ID
    user = get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
    if not user:
        log_data = {
            "event": "auth0_login_failed",
            "reason": "user_not_found",
            "auth0_user_id": auth0_user_id,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        }
        logger.error(json.dumps(log_data))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not found for Auth0 account: {auth0_user_id}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Build user response
    user_data = filter_user_fields(user, current_user=user)

    log_data = {
        "event": "auth0_login_success",
        "auth0_user_id": auth0_user_id,
        "user_id": user.id,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }
    logger.info(json.dumps(log_data))

    return LoginResponse(
        access_token=access_token,  # Return the Auth0 token
        token_type="bearer",  # nosec B106 - OAuth2 standard token type, not a password
        user=user_data,
        expires_in=token_payload.get("exp", 0)
        - int(datetime.now(timezone.utc).timestamp()),
    )


@router.post("/auth0-debug")
def auth0_debug(access_token: str):
    """
    Debug endpoint for Auth0 token validation.

    This endpoint provides detailed information about Auth0 token validation
    without requiring database access. Useful for troubleshooting.

    Args:
        access_token: Auth0 access token

    Returns:
        Detailed debug information about the token
    """
    import json

    from app.core.logging import get_logger

    logger = get_logger(__name__)

    # Log the debug attempt
    log_data = {
        "event": "auth0_debug_attempt",
        "token_length": len(access_token),
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }
    logger.info(json.dumps(log_data))

    debug_info: dict = {
        "token_length": len(access_token),
        "auth0_enabled": settings.AUTH0_ENABLED,
        "auth0_domain": settings.AUTH0_DOMAIN,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }

    try:
        # Try to decode the token header
        try:
            unverified_header = jwt.get_unverified_header(access_token)
            debug_info["token_header"] = unverified_header
        except Exception as e:
            debug_info["header_decode_error"] = str(e)

        # Try to validate the token
        token_payload = validate_any_token(access_token)
        if token_payload:
            debug_info["validation_success"] = True
            debug_info["token_type"] = token_payload.get("token_type")
            debug_info["payload"] = {
                k: v
                for k, v in token_payload.items()
                if k
                not in ["iat", "exp", "nbf"]  # Exclude timestamp fields for brevity
            }
        else:
            debug_info["validation_success"] = False
            debug_info["validation_error"] = "Token validation failed"

        # Try to get JWKS info
        try:
            from app.core.security import auth0_validator

            jwks = auth0_validator._get_jwks()
            if jwks:
                debug_info["jwks_available"] = True
                debug_info["jwks_keys_count"] = len(jwks.get("keys", []))
                debug_info["jwks_kids"] = [
                    key.get("kid") for key in jwks.get("keys", [])
                ]
            else:
                debug_info["jwks_available"] = False
        except Exception as e:
            debug_info["jwks_error"] = str(e)

        # Try to get audience
        try:
            from app.core.security import auth0_validator

            audience = auth0_validator.api_audience
            debug_info["audience"] = audience
        except Exception as e:
            debug_info["audience_error"] = str(e)

    except Exception as e:
        debug_info["unexpected_error"] = str(e)
        logger.error(f"Auth0 debug error: {e}")

    return debug_info
