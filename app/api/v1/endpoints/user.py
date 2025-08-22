"""
User endpoints with permission-based field filtering.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import UserResponse, UserSummary
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter()


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
def get_user_by_name(
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
