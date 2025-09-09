"""
API dependencies for authentication and database access.
"""

# from typing import Generator  # Currently unused

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import validate_any_token
from app.crud.user import (
    get_user_by_auth0_id,
    get_user_by_email,
    get_user_by_id,
    get_user_by_name,
    is_admin,
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
    """Get current authenticated user from either legacy JWT or Auth0 token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token (supports both legacy JWT and Auth0)
    token_payload = validate_any_token(credentials.credentials)
    if not token_payload:
        raise credentials_exception

    # For legacy tokens, user_id is the database user ID
    if token_payload.get("token_type") == "legacy":
        user_id = token_payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        user = get_user_by_id(db, user_id=user_id)
        if user is None:
            raise credentials_exception
        return user

    # For Auth0 tokens, find user by Auth0 user ID
    elif token_payload.get("token_type") == "auth0":
        auth0_user_id = token_payload.get("auth0_user_id")
        if not auth0_user_id:
            raise credentials_exception
        user = get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
        if user is None:
            # User not found in database - try to sync from Auth0
            from app.crud.user import update_user_auth0_id
            from app.services.auth0_service import auth0_service

            # Get Auth0 user details
            auth0_user = auth0_service.find_user_by_auth0_id(auth0_user_id)
            if auth0_user:
                # Try to find user by email or username from Auth0 data
                email = auth0_user.get("email")
                username = auth0_user.get("username") or auth0_user.get("nickname")

                # Try to find existing user by email first
                if email:
                    user = get_user_by_email(db, email)

                # If not found by email, try by username
                if not user and username:
                    user = get_user_by_name(db, username)

                # If user found, update their Auth0 ID
                if user:
                    update_user_auth0_id(db, int(user.id), auth0_user_id)
                    return user

            # If no user found or Auth0 sync failed, raise credentials exception
            raise credentials_exception
        return user

    raise credentials_exception


def get_current_user_optional(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Get current user from token, returning None if not authenticated."""
    if credentials is None:
        return None

    try:
        token_payload = validate_any_token(credentials.credentials)
        if not token_payload:
            return None

        if token_payload.get("token_type") == "legacy":
            user_id = token_payload.get("user_id")
            if user_id is None:
                return None
            return get_user_by_id(db, user_id=user_id)
        elif token_payload.get("token_type") == "auth0":
            auth0_user_id = token_payload.get("auth0_user_id")
            if not auth0_user_id:
                return None
            user = get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
            if user is None:
                # User not found in database - try to sync from Auth0
                from app.crud.user import update_user_auth0_id
                from app.services.auth0_service import auth0_service

                # Get Auth0 user details
                auth0_user = auth0_service.find_user_by_auth0_id(auth0_user_id)
                if auth0_user:
                    # Try to find user by email or username from Auth0 data
                    email = auth0_user.get("email")
                    username = auth0_user.get("username") or auth0_user.get("nickname")

                    # Try to find existing user by email first
                    if email:
                        user = get_user_by_email(db, email)

                    # If not found by email, try by username
                    if not user and username:
                        user = get_user_by_name(db, username)

                    # If user found, update their Auth0 ID
                    if user:
                        update_user_auth0_id(db, int(user.id), auth0_user_id)
                        return user
            return user

    except Exception:
        return None

    return None


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current authenticated user and verify they have admin privileges."""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
