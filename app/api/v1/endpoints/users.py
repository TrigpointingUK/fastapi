"""
User endpoints with permission-based field filtering.
"""

import io
import json
import os
from typing import Dict, Optional, Union

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
)
from app.api.lifecycle import openapi_lifecycle

# from app.core.security import auth0_validator
from app.core.tracing import trace_function
from app.crud import tlog as tlog_crud
from app.crud import tphoto as tphoto_crud
from app.crud import user as user_crud
from app.models.server import Server
from app.models.trig import Trig
from app.models.user import User
from app.schemas.tlog import TLogResponse
from app.schemas.tphoto import TPhotoResponse
from app.schemas.user import (
    UserBreakdown,
    UserPrefs,
    UserResponse,
    UserStats,
    UserUpdate,
    UserWithIncludes,
)
from app.services.badge_service import BadgeService
from app.utils.condition_mapping import get_condition_counts_by_description
from app.utils.geocalibrate import CalibrationResult
from app.utils.url import join_url
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.get(
    "/me",
    response_model=UserWithIncludes,
    openapi_extra=openapi_lifecycle(
        "beta",
        note="Returns the current authenticated user's profile. Supports include=stats,prefs.",
    ),
)
@trace_function("api.users.get_current_user_profile")
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
      - stats: adds basic log stats (totals only) for the user
      - breakdown: adds detailed breakdown statistics (requires stats)
      - prefs: adds the user's preferences (always allowed on /me)
    """

    # Create UserResponse with member_since field
    user_response = UserResponse.model_validate(current_user)
    user_response.member_since = current_user.crt_date  # type: ignore
    result = UserWithIncludes(**user_response.model_dump())

    if include:
        tokens = {t.strip() for t in include.split(",") if t.strip()}

        # Validate include tokens
        valid_includes = {"stats", "breakdown", "prefs"}
        invalid_tokens = tokens - valid_includes
        if invalid_tokens:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid include parameter(s): {', '.join(sorted(invalid_tokens))}. Valid options: {', '.join(sorted(valid_includes))}",
            )

        if "stats" in tokens:
            # Calculate basic stats
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
                total_logs=int(total_logs),
                total_trigs_logged=int(total_trigs),
            )

        if "breakdown" in tokens:
            # Calculate breakdowns by trig characteristics (distinct trigpoints only)
            by_current_use_raw = (
                db.query(
                    Trig.current_use, func.count(func.distinct(user_crud.TLog.trig_id))
                )
                .join(user_crud.TLog, user_crud.TLog.trig_id == Trig.id)
                .filter(user_crud.TLog.user_id == current_user.id)
                .group_by(Trig.current_use)
                .all()
            )
            by_current_use: Dict[str, int] = {
                str(use): int(count) for use, count in by_current_use_raw
            }

            by_historic_use_raw = (
                db.query(
                    Trig.historic_use, func.count(func.distinct(user_crud.TLog.trig_id))
                )
                .join(user_crud.TLog, user_crud.TLog.trig_id == Trig.id)
                .filter(user_crud.TLog.user_id == current_user.id)
                .group_by(Trig.historic_use)
                .all()
            )
            by_historic_use: Dict[str, int] = {
                str(use): int(count) for use, count in by_historic_use_raw
            }

            by_physical_type_raw = (
                db.query(
                    Trig.physical_type,
                    func.count(func.distinct(user_crud.TLog.trig_id)),
                )
                .join(user_crud.TLog, user_crud.TLog.trig_id == Trig.id)
                .filter(user_crud.TLog.user_id == current_user.id)
                .group_by(Trig.physical_type)
                .all()
            )
            by_physical_type: Dict[str, int] = {
                str(ptype): int(count) for ptype, count in by_physical_type_raw
            }

            # Calculate breakdown by log condition (all logs counted)
            condition_counts_raw = (
                db.query(user_crud.TLog.condition, func.count(user_crud.TLog.id))
                .filter(user_crud.TLog.user_id == current_user.id)
                .group_by(user_crud.TLog.condition)
                .all()
            )
            condition_counts: Dict[str, int] = {
                str(cond): int(count) for cond, count in condition_counts_raw
            }
            by_condition = get_condition_counts_by_description(condition_counts)

            result.breakdown = UserBreakdown(
                by_current_use=by_current_use,
                by_historic_use=by_historic_use,
                by_physical_type=by_physical_type,
                by_condition=by_condition,
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


@router.patch(
    "/me",
    response_model=UserWithIncludes,
    openapi_extra=openapi_lifecycle(
        "beta",
        note="Update the current authenticated user's profile and preferences",
    ),
)
@trace_function("api.users.update_current_user_profile")
def update_current_user_profile(
    user_updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserWithIncludes:
    """
    Update the current authenticated user's profile and preferences.

    All fields are optional - only provided fields will be updated.
    """
    # Update only the fields that were provided
    update_data = user_updates.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    # Update the timestamp
    from datetime import datetime

    current_user.upd_timestamp = datetime.now()  # type: ignore

    try:
        db.commit()
        db.refresh(current_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

    # Return updated user data with prefs
    user_response = UserResponse.model_validate(current_user)
    user_response.member_since = current_user.crt_date  # type: ignore
    result = UserWithIncludes(**user_response.model_dump())

    # Always include prefs in PATCH response since they might have been updated
    result.prefs = UserPrefs(
        status_max=int(current_user.status_max),
        distance_ind=str(current_user.distance_ind),
        public_ind=str(current_user.public_ind),
        online_map_type=str(current_user.online_map_type),
        online_map_type2=str(current_user.online_map_type2),
    )

    return result


@router.get(
    "/{user_id}/badge",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "User statistics badge as PNG image",
        }
    },
    openapi_extra=openapi_lifecycle(
        "beta",
        note="Generates a 200x50px PNG badge showing user statistics including nickname, trigpoints logged, and photos uploaded.",
    ),
)
@trace_function("api.users.get_user_badge")
def get_user_badge(
    user_id: int,
    scale: float = Query(
        1.0,
        ge=0.1,
        le=5.0,
        description="Scale factor for badge size (0.1-5.0, default: 1.0)",
    ),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Generate a PNG badge for a user showing their statistics.

    Returns a scalable PNG image (default 200x50px) with:
    - TrigpointingUK logo on the left (20%)
    - User's nickname on the first line (right 80%)
    - "logged: X / photos: Y" on the second line
    - "Trigpointing.UK" on the third line

    Scale parameter allows resizing from 0.1x to 5.0x (e.g., scale=2.0 returns 400x100px)
    """
    try:
        badge_service = BadgeService()
        badge_bytes = badge_service.generate_badge(db, user_id, scale=scale)

        return StreamingResponse(
            badge_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=user_{user_id}_badge.png",
                "Cache-Control": "public, max-age=300",  # Cache for 5 minutes
            },
        )
    except ValueError:
        # Normalise not-found message for consistency across tests
        raise HTTPException(status_code=404, detail="User not found")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Server configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating badge: {e}")


@router.get("/{user_id}", response_model=UserWithIncludes)
@trace_function("api.users.get_user")
def get_user(
    user_id: int,
    include: Optional[str] = Query(
        None, description="Comma-separated includes: stats,breakdown"
    ),
    db: Session = Depends(get_db),
):
    """
    Get a user by ID - public data only.

    - Supports optional includes via the `include` query parameter:
      - stats: adds basic log stats (totals only) for the user
      - breakdown: adds detailed breakdown statistics

    For private data including preferences, use GET /users/me
    """
    user = user_crud.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build base response using Pydantic model validation with member_since field
    user_response = UserResponse.model_validate(user)
    user_response.member_since = user.crt_date  # type: ignore
    result = UserWithIncludes(**user_response.model_dump())

    # Handle includes...
    tokens = {t.strip() for t in include.split(",")} if include else set()

    # Validate include tokens
    valid_includes = {"stats", "breakdown"}
    invalid_tokens = tokens - valid_includes
    if invalid_tokens:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid include parameter(s): {', '.join(sorted(invalid_tokens))}. Valid options: {', '.join(sorted(valid_includes))}",
        )

    if "stats" in tokens:
        # Calculate basic stats
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
            total_logs=int(total_logs),
            total_trigs_logged=int(total_trigs),
        )

    if "breakdown" in tokens:
        # Calculate breakdowns by trig characteristics (distinct trigpoints only)
        by_current_use_raw = (
            db.query(
                Trig.current_use, func.count(func.distinct(user_crud.TLog.trig_id))
            )
            .join(user_crud.TLog, user_crud.TLog.trig_id == Trig.id)
            .filter(user_crud.TLog.user_id == user_id)
            .group_by(Trig.current_use)
            .all()
        )
        by_current_use: Dict[str, int] = {
            str(use): int(count) for use, count in by_current_use_raw
        }

        by_historic_use_raw = (
            db.query(
                Trig.historic_use, func.count(func.distinct(user_crud.TLog.trig_id))
            )
            .join(user_crud.TLog, user_crud.TLog.trig_id == Trig.id)
            .filter(user_crud.TLog.user_id == user_id)
            .group_by(Trig.historic_use)
            .all()
        )
        by_historic_use: Dict[str, int] = {
            str(use): int(count) for use, count in by_historic_use_raw
        }

        by_physical_type_raw = (
            db.query(
                Trig.physical_type, func.count(func.distinct(user_crud.TLog.trig_id))
            )
            .join(user_crud.TLog, user_crud.TLog.trig_id == Trig.id)
            .filter(user_crud.TLog.user_id == user_id)
            .group_by(Trig.physical_type)
            .all()
        )
        by_physical_type: Dict[str, int] = {
            str(ptype): int(count) for ptype, count in by_physical_type_raw
        }

        # Calculate breakdown by log condition (all logs counted)
        condition_counts_raw = (
            db.query(user_crud.TLog.condition, func.count(user_crud.TLog.id))
            .filter(user_crud.TLog.user_id == user_id)
            .group_by(user_crud.TLog.condition)
            .all()
        )
        condition_counts: Dict[str, int] = {
            str(cond): int(count) for cond, count in condition_counts_raw
        }
        by_condition = get_condition_counts_by_description(condition_counts)

        result.breakdown = UserBreakdown(
            by_current_use=by_current_use,
            by_historic_use=by_historic_use,
            by_physical_type=by_physical_type,
            by_condition=by_condition,
        )

    return result


@router.get("")
@trace_function("api.users.list_users")
def list_users(
    name: Optional[str] = Query(None, description="Filter by username (contains)"),
    include: Optional[str] = Query(None, description="Comma-separated includes: stats"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    db: Session = Depends(get_db),
):
    """Filtered collection endpoint for users returning envelope with items and pagination.

    - Supports optional includes via the `include` query parameter:
      - stats: adds basic log stats (totals only) for each user
    """
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

    # Parse include tokens
    tokens = {t.strip() for t in include.split(",")} if include else set()

    # Validate include tokens (only 'stats' supported for list endpoint)
    valid_includes = {"stats"}
    invalid_tokens = tokens - valid_includes
    if invalid_tokens:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid include parameter(s): {', '.join(sorted(invalid_tokens))}. Valid options for user list: {', '.join(sorted(valid_includes))}",
        )

    # If stats are requested, get user IDs for bulk stats calculation
    user_stats: Dict[int, UserStats] = {}
    if "stats" in tokens:
        user_ids = [int(u.id) for u in items]
        if user_ids:
            # Calculate basic stats for all users at once
            total_logs_query = (
                db.query(user_crud.TLog.user_id, func.count(user_crud.TLog.id))
                .filter(user_crud.TLog.user_id.in_(user_ids))
                .group_by(user_crud.TLog.user_id)
                .all()
            )

            total_trigs_query = (
                db.query(
                    user_crud.TLog.user_id,
                    func.count(func.distinct(user_crud.TLog.trig_id)),
                )
                .filter(user_crud.TLog.user_id.in_(user_ids))
                .group_by(user_crud.TLog.user_id)
                .all()
            )

            # Convert to dictionaries for fast lookup
            logs_by_user: Dict[int, int] = {
                user_id: count for user_id, count in total_logs_query
            }
            trigs_by_user: Dict[int, int] = {
                user_id: count for user_id, count in total_trigs_query
            }

            for user_id in user_ids:
                user_stats[user_id] = UserStats(
                    total_logs=logs_by_user.get(user_id, 0),
                    total_trigs_logged=trigs_by_user.get(user_id, 0),
                )

    # Serialize users with optional stats
    items_serialized = []
    for u in items:
        user_response = UserResponse.model_validate(u)
        user_response.member_since = u.crt_date  # type: ignore

        # Create UserWithIncludes response
        result = UserWithIncludes(**user_response.model_dump())

        # Add stats if requested
        if "stats" in tokens and int(u.id) in user_stats:
            result.stats = user_stats[int(u.id)]

        items_serialized.append(result.model_dump())
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


@router.get("/{user_id}/logs", openapi_extra=openapi_lifecycle("beta"))
@trace_function("api.users.list_logs_for_user")
def list_logs_for_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = tlog_crud.list_logs_filtered(db, user_id=user_id, skip=skip, limit=limit)
    total = tlog_crud.count_logs_filtered(db, user_id=user_id)
    items_serialized = [TLogResponse.model_validate(i).model_dump() for i in items]
    has_more = (skip + len(items)) < total
    base = f"/v1/users/{user_id}/logs"
    self_link = base + f"?limit={limit}&skip={skip}"
    next_link = base + f"?limit={limit}&skip={skip + limit}" if has_more else None
    prev_offset = max(skip - limit, 0)
    prev_link = base + f"?limit={limit}&skip={prev_offset}" if skip > 0 else None
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


@router.get("/{user_id}/photos", openapi_extra=openapi_lifecycle("beta"))
def list_photos_for_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = tphoto_crud.list_photos_filtered(
        db, user_id=user_id, skip=skip, limit=limit
    )
    total = (
        db.query(tphoto_crud.TPhoto)
        .join(user_crud.TLog, user_crud.TLog.id == tphoto_crud.TPhoto.tlog_id)
        .filter(
            user_crud.TLog.user_id == user_id, tphoto_crud.TPhoto.deleted_ind != "Y"
        )
        .count()
    )
    result_items = []
    for p in items:
        server: Server | None = (
            db.query(Server).filter(Server.id == p.server_id).first()
        )
        base_url = str(server.url) if server and server.url else ""
        result_items.append(
            TPhotoResponse(
                id=int(p.id),
                log_id=int(p.tlog_id),
                user_id=user_id,
                type=str(p.type),
                filesize=int(p.filesize),
                height=int(p.height),
                width=int(p.width),
                icon_filesize=int(p.icon_filesize),
                icon_height=int(p.icon_height),
                icon_width=int(p.icon_width),
                name=str(p.name),
                text_desc=str(p.text_desc),
                public_ind=str(p.public_ind),
                photo_url=join_url(base_url, str(p.filename)),
                icon_url=join_url(base_url, str(p.icon_filename)),
            ).model_dump()
        )
    has_more = (skip + len(items)) < total
    base = f"/v1/users/{user_id}/photos"
    self_link = base + f"?limit={limit}&skip={skip}"
    next_link = base + f"?limit={limit}&skip={skip + limit}" if has_more else None
    prev_offset = max(skip - limit, 0)
    prev_link = base + f"?limit={limit}&skip={prev_offset}" if skip > 0 else None
    return {
        "items": result_items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": skip,
            "has_more": has_more,
        },
        "links": {"self": self_link, "next": next_link, "prev": prev_link},
    }


@router.get(
    "/{user_id}/map",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Rendered user trigpoint map overlay as PNG",
        }
    },
    openapi_extra=openapi_lifecycle(
        "beta",
        note=(
            "Generates a PNG map with dots for found/notfound/notlogged trigpoints. "
            "Colours may be provided as hex strings. Rendering order: notlogged (bottom), notfound (middle), found (top)."
        ),
    ),
)
def get_user_map(
    user_id: int,
    found_colour: Optional[str] = Query(
        None,
        description="Hex #RRGGBB or 'none' for found trigs (blank → default)",
    ),
    notfound_colour: Optional[str] = Query(
        None,
        description="Hex #RRGGBB or 'none' for not-found trigs (blank → default)",
    ),
    notlogged_colour: Optional[str] = Query(
        None,
        description="Hex #RRGGBB or 'none' for not-logged trigs (blank → default)",
    ),
    map_variant: Optional[str] = Query(
        "stretched53",
        description="Map variant: stretched53 (default) or wgs84",
    ),
    # Re-add configurable dot size (diameter, default 10px)
    dot_diameter: int = Query(
        50, ge=1, le=100, description="Diameter of plotted dots in pixels (default 50)"
    ),
    # Optional alpha for dots to allow visual stacking
    dot_alpha: Optional[int] = Query(
        40, ge=1, le=255, description="Per-dot alpha increment (default 40)"
    ),
    # Optional land recolour; sea remains transparent
    land_colour: Optional[str] = Query(
        "#dddddd", description="Hex fill for land; 'none' to keep original"
    ),
    coastline_colour: Optional[str] = Query(
        "#666666", description="Stroke colour for coastline edges"
    ),
    height: int = Query(
        110, ge=10, le=4000, description="Output image height in pixels (default 110)"
    ),
    db: Session = Depends(get_db),
):
    """
    Render a user map overlay using `res/ukmap.jpg` and `res/uk_map_calibration.json`.

    Expensive full-trig-table query is performed only when `notlogged_colour` is provided.
    """
    try:
        # Resolve colours: blank → default; 'none' → disable
        def _norm(cval: Optional[str], default_hex: Optional[str]) -> Optional[str]:
            s = (cval or "").strip()
            if not s:
                return default_hex
            if s.lower() == "none":
                return None
            return s

        found_hex = _norm(found_colour, "#ff0000")
        notfound_hex = _norm(notfound_colour, "#0000ff")
        notlogged_hex = _norm(notlogged_colour, None)

        # Load base map image (fallback if missing)
        image_filename = (
            "ukmap_wgs84_stretched53.png"
            if map_variant == "stretched53"
            else "ukmap_wgs84.png"
        )
        calib_filename = (
            "uk_map_calibration_wgs84_stretched53.json"
            if map_variant == "stretched53"
            else "uk_map_calibration_wgs84.json"
        )
        map_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "..",
            "res",
            image_filename,
        )
        map_path = os.path.normpath(map_path)
        if os.path.isfile(map_path):
            # Preserve alpha from the asset (transparent sea)
            base = Image.open(map_path).convert("RGBA")
        else:
            # Fallback transparent canvas
            base = Image.new("RGBA", (800, 900), color=(0, 0, 0, 0))

        # Load calibration
        calib_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "..",
            "res",
            calib_filename,
        )
        calib_path = os.path.normpath(calib_path)
        with open(calib_path, "r") as f:
            d = json.load(f)
        calib = CalibrationResult(
            affine=np.array(d["affine"], dtype=float),
            inverse=np.array(d["inverse"], dtype=float),
            pixel_bbox=tuple(d.get("pixel_bbox", (0, 0, base.size[0], base.size[1]))),
            bounds_geo=tuple(d.get("bounds_geo", (-11.0, 49.0, 2.5, 61.5))),
        )

        # If a land colour is provided, recolour the land using the alpha mask,
        # then re-apply a coastline stroke extracted from the alpha edges.
        if land_colour and land_colour.strip():
            hc = land_colour.strip()
            if hc.startswith("#"):
                hc = hc[1:]
            if len(hc) == 6:
                r = int(hc[0:2], 16)
                g = int(hc[2:4], 16)
                b = int(hc[4:6], 16)
                alpha_ch = base.getchannel("A")
                recol = Image.new("RGBA", base.size, (r, g, b, 255))
                recol.putalpha(alpha_ch)
                base = recol

                # Coastline stroke from alpha edge
                edge_mask = alpha_ch.filter(ImageFilter.FIND_EDGES)
                # Thicken slightly for visibility
                try:
                    edge_mask = edge_mask.filter(ImageFilter.MaxFilter(3))
                except Exception:
                    # If MaxFilter is unavailable in this Pillow build, continue with the thin edge
                    edge_mask = edge_mask
                sc = (40, 40, 40, 255)
                if coastline_colour:
                    s = coastline_colour.strip()
                    if s.startswith("#"):
                        s = s[1:]
                    if len(s) == 6:
                        sc = (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
                stroke_layer = Image.new("RGBA", base.size, sc)
                base.paste(stroke_layer, (0, 0), edge_mask)

        draw = ImageDraw.Draw(base)

        def draw_dot(px: float, py: float, hex_colour: str) -> None:
            if not hex_colour:
                return
            r = max(1, int(round(dot_diameter / 2)))
            x = int(round(px))
            y = int(round(py))
            if x < 0 or y < 0 or x >= base.size[0] or y >= base.size[1]:
                return
            bbox = [x - r, y - r, x + r, y + r]
            # Support optional alpha override for stacking
            fill: Union[str, tuple[int, int, int, int]] = hex_colour
            if dot_alpha is not None:
                s = hex_colour.strip()
                if s.startswith("#"):
                    s = s[1:]
                if len(s) == 6:
                    rr = int(s[0:2], 16)
                    gg = int(s[2:4], 16)
                    bb = int(s[4:6], 16)
                    fill = (rr, gg, bb, int(dot_alpha))
            draw.ellipse(bbox, fill=fill, outline=None)

        def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
            s = hex_str.strip()
            if s.startswith("#"):
                s = s[1:]
            if len(s) >= 6:
                return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
            return (255, 0, 0)

        def accumulate_and_paste(
            points: list[tuple[float, float]], colour_hex: str
        ) -> None:
            if not points:
                return
            r = max(1, int(round(dot_diameter / 2)))
            inc = int(dot_alpha) if dot_alpha is not None else 64
            w, h = base.size
            accum = Image.new("L", (w, h), 0)
            for px, py in points:
                x = int(round(px))
                y = int(round(py))
                if x < 0 or y < 0 or x >= w or y >= h:
                    continue
                left = max(0, x - r)
                right = min(w, x + r)
                top = max(0, y - r)
                bottom = min(h, y + r)
                if right <= left or bottom <= top:
                    continue
                dot_w = right - left
                dot_h = bottom - top
                dot = Image.new("L", (dot_w, dot_h), 0)
                ddraw = ImageDraw.Draw(dot)
                ddraw.ellipse([0, 0, dot_w - 1, dot_h - 1], fill=inc)
                region = accum.crop((left, top, right, bottom))
                added = ImageChops.add(region, dot)
                accum.paste(added, (left, top))

            rgb = _hex_to_rgb(colour_hex)
            overlay = Image.new("RGBA", (w, h), (rgb[0], rgb[1], rgb[2], 255))
            base.paste(overlay, (0, 0), accum)

        GOOD = {"G", "S", "D", "T"}

        # Query user's tlogs with trig coords
        tlog_rows = (
            db.query(
                user_crud.TLog.trig_id,
                user_crud.TLog.condition,
                Trig.wgs_lat,
                Trig.wgs_long,
            )
            .join(Trig, Trig.id == user_crud.TLog.trig_id)
            .filter(user_crud.TLog.user_id == user_id)
            .all()
        )

        # Prepare sets and lists
        logged_ids = set()
        found_pts: list[tuple[float, float]] = []
        notfound_pts: list[tuple[float, float]] = []
        notlogged_pts: list[tuple[float, float]] = []
        for trig_id, condition, lat, lon in tlog_rows:
            logged_ids.add(int(trig_id))
            lat_f = float(lat)
            lon_f = float(lon)
            x, y = calib.lonlat_to_xy(lon_f, lat_f)
            if str(condition) in GOOD:
                found_pts.append((x, y))
            else:
                notfound_pts.append((x, y))

        # Only if notlogged requested, query all trigpoints
        if notlogged_hex:
            all_trigs = db.query(Trig.id, Trig.wgs_lat, Trig.wgs_long).all()
            for tid, lat, lon in all_trigs:
                if int(tid) in logged_ids:
                    continue
                x, y = calib.lonlat_to_xy(float(lon), float(lat))
                notlogged_pts.append((x, y))

        # Draw notfound beneath found
        if notlogged_hex:
            accumulate_and_paste(notlogged_pts, notlogged_hex)
        if notfound_hex:
            accumulate_and_paste(notfound_pts, notfound_hex)
        if found_hex:
            accumulate_and_paste(found_pts, found_hex)

        # Optional final scaling to requested height (preserve aspect, anti-aliased)
        if isinstance(height, int) and height > 0 and base.height != height:
            scale = float(height) / float(base.height)
            new_w = max(1, int(round(base.width * scale)))
            # Pillow>=10 recommends Image.Resampling.LANCZOS; keep compatibility
            try:
                resample = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
            except Exception:
                try:
                    resample = Image.Resampling.NEAREST  # type: ignore[attr-defined]
                except Exception:
                    resample = 0  # type: ignore[assignment]
            base = base.resize((new_w, height), resample=resample)

        # Encode image (preserve alpha)
        buf = io.BytesIO()
        base.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Server configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering user map: {e}")
