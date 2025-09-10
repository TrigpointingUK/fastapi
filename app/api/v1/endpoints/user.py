"""
User endpoints with permission-based field filtering.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.core.security import validate_any_token
from app.crud import user as user_crud
from app.crud.user import get_user_by_auth0_id, get_user_by_email, get_user_by_name
from app.models.user import User
from app.schemas.user import Auth0UserInfo, UserResponse, UserSummary
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.get("/auth0-info", response_model=Auth0UserInfo)
def get_auth0_user_info(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Get Auth0 user information directly from token without requiring database lookup.

    This endpoint is designed to help with debugging Auth0 integration and understanding
    what user information is available from Auth0 tokens. It returns:
    - All Auth0 user details from the token
    - Token metadata (audience, issuer, expiration)
    - Database lookup status and any matching user information

    This is useful for:
    - Understanding what Auth0 provides vs what's in the legacy database
    - Identifying data cleansing needs for Auth0 migration
    - Debugging authentication issues
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token and get payload
    token_payload = validate_any_token(credentials.credentials)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token information
    token_type = token_payload.get("token_type", "unknown")
    auth0_user_id = token_payload.get("auth0_user_id") or token_payload.get("sub", "")

    # Try to find user in database (but don't fail if not found)
    database_user_found = False
    database_user_id = None
    database_username = None
    database_email = None

    if token_type == "auth0" and auth0_user_id:  # nosec B105
        # Try direct Auth0 ID lookup
        user = get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
        if user:
            database_user_found = True
            database_user_id = int(user.id)
            database_username = str(user.name)
            database_email = str(user.email) if user.email else None
        else:
            # Try to find by email or username from Auth0 data
            email = token_payload.get("email")
            username = token_payload.get("username") or token_payload.get("nickname")

            if email:
                user = get_user_by_email(db, email)
                if user:
                    database_user_found = True
                    database_user_id = int(user.id)
                    database_username = str(user.name)
                    database_email = str(user.email) if user.email else None

            if not database_user_found and username:
                user = get_user_by_name(db, username)
                if user:
                    database_user_found = True
                    database_user_id = int(user.id)
                    database_username = str(user.name)
                    database_email = str(user.email) if user.email else None

    # Build response
    return Auth0UserInfo(
        # Auth0 user details
        auth0_user_id=auth0_user_id,
        email=token_payload.get("email"),
        username=token_payload.get("username"),
        nickname=token_payload.get("nickname"),
        name=token_payload.get("name"),
        given_name=token_payload.get("given_name"),
        family_name=token_payload.get("family_name"),
        email_verified=token_payload.get("email_verified"),
        # Token metadata
        token_type=token_type,
        audience=token_payload.get("aud"),
        issuer=token_payload.get("iss"),
        expires_at=token_payload.get("exp"),
        # Database lookup status
        database_user_found=database_user_found,
        database_user_id=database_user_id,
        database_username=database_username,
        database_email=database_email,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user's profile data.

    This endpoint provides a way to refresh user data or get complete profile
    information when the login response doesn't contain enough details.

    Returns:
        UserResponse: Complete user profile with all accessible fields
    """
    return filter_user_fields(current_user, current_user=current_user)


def filter_user_fields(user: User, current_user: Optional[User] = None) -> UserResponse:
    """
    Filter user fields based on permissions.

    Rules:
    - cryptpw: Never exposed
    - email: Only if public_ind='Y' OR current_user is admin OR current_user is the same user
    - email_valid, admin_ind, public_ind: Only if current_user is admin OR current_user is the same user
    """
    # Start with base fields (always visible)
    response = UserResponse(
        id=int(user.id),
        name=str(user.name),
        firstname=str(user.firstname),
        surname=str(user.surname),
        about=str(user.about),
    )

    # Determine if current user can see private fields
    is_same_user = current_user and current_user.id == user.id
    is_admin = current_user and user_crud.is_admin(current_user)
    can_see_private = is_same_user or is_admin

    # Email visibility rules
    if can_see_private or user_crud.is_public_profile(user):
        response.email = str(user.email)

    # Private flags - only for same user or admin
    if can_see_private:
        response.email_valid = str(user.email_valid)
        response.admin_ind = str(user.admin_ind)
        response.public_ind = str(user.public_ind)

    return response


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get a user by ID.

    Returns user data with field filtering based on permissions:
    - Public fields always visible
    - Email visible if profile is public OR user is authenticated as same user/admin
    - Private flags only visible to same user or admin
    """
    user = user_crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return filter_user_fields(user, current_user)


@router.get("/name/{username}", response_model=UserResponse)
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get a user by username.

    Returns user data with field filtering based on permissions.
    """
    user = user_crud.get_user_by_name(db, name=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return filter_user_fields(user, current_user)


@router.get("/search/name", response_model=List[UserSummary])
def search_users_by_name(
    q: str = Query(..., description="Search query for usernames"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    db: Session = Depends(get_db),
):
    """
    Search users by name pattern.

    Returns simplified user data (no sensitive fields).
    """
    users = user_crud.search_users_by_name(db, name_pattern=q, skip=skip, limit=limit)
    return users


@router.get("/stats/count")
def get_users_count(db: Session = Depends(get_db)):
    """
    Get total number of users in the database.

    Returns:
        JSON object with total count
    """
    count = user_crud.get_users_count(db)
    return {"total_users": count}
