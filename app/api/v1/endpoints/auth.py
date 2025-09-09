"""
Authentication endpoints.
"""

from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordRequestForm
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
    from app.api.v1.endpoints.user import filter_user_fields

    # Validate the Auth0 token
    token_payload = validate_any_token(access_token)
    if not token_payload or token_payload.get("token_type") != "auth0":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Auth0 token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get Auth0 user ID from token
    auth0_user_id = token_payload.get("auth0_user_id")
    if not auth0_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Auth0 token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find user in database by Auth0 ID
    user = get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for Auth0 account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Build user response
    user_data = filter_user_fields(user, current_user=user)

    return LoginResponse(
        access_token=access_token,  # Return the Auth0 token
        token_type="bearer",  # nosec B106 - OAuth2 standard token type, not a password
        user=user_data,
        expires_in=token_payload.get("exp", 0)
        - int(datetime.now(timezone.utc).timestamp()),
    )
