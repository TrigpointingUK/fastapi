"""
API dependencies for authentication and database access.
"""

# from typing import Generator  # Currently unused

from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import auth0_validator, extract_scopes
from app.crud.user import (
    get_user_by_auth0_id,
    get_user_by_email,
    get_user_by_name,
    update_user_auth0_mapping,
)
from app.db.database import get_db
from app.models.user import User

# from app.schemas.user import TokenData
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """Get current authenticated user (Auth0 bearer only when enabled)."""
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        logger.warning("No credentials provided to get_current_user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token (Auth0-only when enabled)
    token_payload = auth0_validator.validate_auth0_token(credentials.credentials)
    if not token_payload:
        logger.warning("Token validation failed in get_current_user")
        raise credentials_exception

    logger.info(
        "Auth0 token validated successfully",
        extra={
            "auth0_user_id": token_payload.get("auth0_user_id"),
        },
    )

    # For Auth0 tokens, find user by Auth0 user ID
    if token_payload.get("token_type") == "auth0":
        auth0_user_id = token_payload.get("auth0_user_id")
        if not auth0_user_id:
            raise credentials_exception
        user = get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
        if user is None:
            # User not found in database - try to sync from Auth0
            from app.core.logging import get_logger
            from app.services.auth0_service import auth0_service

            logger = get_logger(__name__)
            logger.info(
                f"Auth0 user not found in database, attempting sync: {auth0_user_id}",
                extra={
                    "auth0_user_id": auth0_user_id,
                    "token_email": token_payload.get("email"),
                    "token_nickname": token_payload.get("nickname"),
                    "token_name": token_payload.get("name"),
                },
            )

            # Get Auth0 user details
            auth0_user = auth0_service.find_user_by_auth0_id(auth0_user_id)
            if auth0_user:
                # Try to find user by email or display name from Auth0 data
                email = auth0_user.get("email")
                display_name = auth0_user.get("nickname") or auth0_user.get("name")

                logger.info(
                    "Auth0 user details retrieved, searching database",
                    extra={
                        "auth0_email": email,
                        "auth0_display_name": display_name,
                    },
                )

                # Try to find existing user by email first
                if email:
                    user = get_user_by_email(db, email)
                    if user:
                        logger.info(
                            f"Found user by email: {email} -> user_id {user.id}"
                        )

                # If not found by email, try by display name (nickname/name)
                if not user and display_name:
                    user = get_user_by_name(db, display_name)
                    if user:
                        logger.info(
                            f"Found user by name: {display_name} -> user_id {user.id}"
                        )

                # If user found, update their Auth0 mapping (ID + username)
                if user:
                    update_user_auth0_mapping(
                        db,
                        int(user.id),
                        auth0_user_id,
                    )
                    logger.info(f"Updated user {user.id} with Auth0 ID {auth0_user_id}")
                    setattr(user, "_token_payload", token_payload)
                    return user
                else:
                    logger.warning(
                        f"No matching user found in database for Auth0 user {auth0_user_id}",
                        extra={
                            "auth0_email": email,
                            "auth0_display_name": display_name,
                        },
                    )
            else:
                logger.warning(
                    f"Could not retrieve Auth0 user details for {auth0_user_id}"
                )

            # If no user found or Auth0 sync failed, raise credentials exception
            raise credentials_exception
        setattr(user, "_token_payload", token_payload)
        return user

    # Only Auth0 tokens are supported
    raise credentials_exception


def get_current_user_optional(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Get current user from token, returning None if not authenticated."""
    if credentials is None:
        return None

    try:
        token_payload = auth0_validator.validate_auth0_token(credentials.credentials)
        if not token_payload:
            return None

        if token_payload.get("token_type") == "auth0":
            auth0_user_id = token_payload.get("auth0_user_id")
            if not auth0_user_id:
                return None
            user = get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
            if user is None:
                # User not found in database - try to sync from Auth0
                from app.services.auth0_service import auth0_service

                # Get Auth0 user details
                auth0_user = auth0_service.find_user_by_auth0_id(auth0_user_id)
                if auth0_user:
                    # Try to find user by email or display name from Auth0 data
                    email = auth0_user.get("email")
                    display_name = auth0_user.get("nickname") or auth0_user.get("name")

                    # Try to find existing user by email first
                    if email:
                        user = get_user_by_email(db, email)

                    # If not found by email, try by display name (nickname/name)
                    if not user and display_name:
                        user = get_user_by_name(db, display_name)

                    # If user found, update their Auth0 mapping (ID + username)
                    if user:
                        update_user_auth0_mapping(
                            db,
                            int(user.id),
                            auth0_user_id,
                        )
                        setattr(user, "_token_payload", token_payload)
                        return user
            if user:
                setattr(user, "_token_payload", token_payload)
            return user

    except Exception:
        return None

    return None


class _TokenContext(BaseModel):
    token_payload: dict


def get_token_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> _TokenContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_payload = auth0_validator.validate_auth0_token(credentials.credentials)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _TokenContext(token_payload=token_payload)


def require_scopes(*required_scopes: str):
    def _dep(
        ctx: _TokenContext = Depends(get_token_context),
        db: Session = Depends(get_db),
    ) -> User:
        token_payload = ctx.token_payload
        token_type = token_payload.get("token_type")

        if token_type == "auth0":  # nosec B105
            scopes = extract_scopes(token_payload)
            missing = [s for s in required_scopes if s not in scopes]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scope(s): {', '.join(missing)}",
                )
            auth0_user_id = token_payload.get("auth0_user_id")
            user = (
                get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
                if auth0_user_id
                else None
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only Auth0 tokens are supported",
            )

        setattr(user, "_token_payload", token_payload)
        return user

    return _dep
