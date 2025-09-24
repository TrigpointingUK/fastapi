"""
User endpoints with permission-based field filtering.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_db,
)
from app.api.lifecycle import openapi_lifecycle

# from app.core.security import auth0_validator
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import (
    UserPrefs,
    UserResponse,
    UserStats,
    UserWithIncludes,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.get(
    "/me",
    response_model=UserWithIncludes,
    openapi_extra=openapi_lifecycle(
        "ga",
        note="Returns the current authenticated user's profile. Supports include=stats,prefs.",
    ),
)
def get_current_user_profile(
    include: Optional[str] = Query(
        None, description="Comma-separated includes: stats,prefs"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserWithIncludes:
    """
    Get the current authenticated user's profile.

    - Supports optional includes via the `include` query parameter:
      - stats: adds aggregate log stats for the user
      - prefs: adds the user's preferences (always allowed on /me)
    """

    result = UserWithIncludes(**UserResponse.model_validate(current_user).model_dump())

    if include:
        tokens = {t.strip() for t in include.split(",") if t.strip()}

        if "stats" in tokens:
            total_logs = (
                db.query(user_crud.TLog)
                .filter(user_crud.TLog.user_id == current_user.id)
                .count()
            )
            total_trigs = (
                db.query(user_crud.TLog.trig_id)
                .filter(user_crud.TLog.user_id == current_user.id)
                .distinct()
                .count()
            )
            result.stats = UserStats(
                total_logs=int(total_logs), total_trigs_logged=int(total_trigs)
            )

        if "prefs" in tokens:
            # Always allowed on /me
            result.prefs = UserPrefs(
                status_max=int(current_user.status_max),
                distance_ind=str(current_user.distance_ind),
                public_ind=str(current_user.public_ind),
                online_map_type=str(current_user.online_map_type),
                online_map_type2=str(current_user.online_map_type2),
            )

    return result


@router.get("/{user_id}", response_model=UserWithIncludes)
def get_user(
    user_id: int,
    include: Optional[str] = Query(
        None, description="Comma-separated includes: stats,prefs"
    ),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    credentials=Depends(security),
):
    """
    Get a user by ID.
    """
    user = user_crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build base response using Pydantic model validation
    result = UserWithIncludes(**UserResponse.model_validate(user).model_dump())

    # Handle includes...
    tokens = {t.strip() for t in include.split(",")} if include else set()

    if "stats" in tokens:
        total_logs = (
            db.query(user_crud.TLog).filter(user_crud.TLog.user_id == user_id).count()
        )
        total_trigs = (
            db.query(user_crud.TLog.trig_id)
            .filter(user_crud.TLog.user_id == user_id)
            .distinct()
            .count()
        )
        result.stats = UserStats(
            total_logs=int(total_logs), total_trigs_logged=int(total_trigs)
        )

    if "prefs" in tokens:
        allowed = False
        if current_user and current_user.id == user.id:
            allowed = True
        else:
            try:
                from app.core.security import auth0_validator, extract_scopes

                if credentials is not None:
                    payload = auth0_validator.validate_auth0_token(
                        credentials.credentials
                    )
                    scopes = extract_scopes(payload or {}) if payload else set()
                    if "user:admin" in scopes:
                        allowed = True
            except Exception:
                allowed = False
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden")

        result.prefs = UserPrefs(
            status_max=int(user.status_max),
            distance_ind=str(user.distance_ind),
            public_ind=str(user.public_ind),
            online_map_type=str(user.online_map_type),
            online_map_type2=str(user.online_map_type2),
        )

    return result


@router.get("")
def list_users(
    name: Optional[str] = Query(None, description="Filter by username (contains)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    db: Session = Depends(get_db),
):
    """Filtered collection endpoint for users returning envelope with items and pagination."""
    # Explicit empty string should mean: return all users (no name filter)
    if name is not None and name.strip() == "":
        query = db.query(user_crud.User)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
    elif name:
        items = user_crud.search_users_by_name(
            db, name_pattern=name, skip=skip, limit=limit
        )
        # Estimate total via a count query matching the filter
        total = (
            db.query(user_crud.User)
            .filter(user_crud.User.name.ilike(f"%{name}%"))
            .count()
            if hasattr(user_crud, "User")
            else len(items)
        )
    else:
        # No name filter provided -> return all users with pagination
        if hasattr(user_crud, "User"):
            total = db.query(user_crud.User).count()
            items = db.query(user_crud.User).offset(skip).limit(limit).all()
        else:
            items = []
            total = 0

    has_more = (skip + len(items)) < total
    base = "/v1/users"
    params = [f"limit={limit}"]
    if name:
        params.insert(0, f"name={name}")
    self_link = base + "?" + "&".join(params + [f"skip={skip}"])
    next_link = (
        base + "?" + "&".join(params + [f"skip={skip + limit}"]) if has_more else None
    )
    prev_offset = max(skip - limit, 0)
    prev_link = (
        base + "?" + "&".join(params + [f"skip={prev_offset}"]) if skip > 0 else None
    )

    items_serialized = [UserResponse.model_validate(u).model_dump() for u in items]
    return {
        "items": items_serialized,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": skip,
            "has_more": has_more,
        },
        "links": {"self": self_link, "next": next_link, "prev": prev_link},
    }
