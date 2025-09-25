"""
Authentication endpoints.
"""

from datetime import datetime, timezone  # noqa: F401

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud.user import (
    authenticate_user_flexible,
    update_user_auth0_mapping,
)
from app.schemas.user import UserResponse
from app.services.auth0_service import auth0_service

router = APIRouter()


@router.post("/login", response_model=UserResponse)
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
        )

    # Sync user to Auth0 and store mapping
    if not user.auth0_user_id:
        try:
            auth0_user = auth0_service.sync_user_to_auth0(
                username=str(user.name),
                email=str(user.email) if user.email else None,
                name=str(user.name),  # mirror nickname as name
                password=form_data.password,
                user_id=int(user.id),
            )

            if auth0_user:
                # Store Auth0 user ID mapping in the database
                update_user_auth0_mapping(
                    db=db,
                    user_id=int(user.id),
                    auth0_user_id=str(auth0_user.get("user_id")),
                )
        except Exception as e:
            # Log error but don't fail the login
            from app.core.logging import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to sync user to Auth0: {e}")

    return user


# removed auth0-login and auth0-debug endpoints
