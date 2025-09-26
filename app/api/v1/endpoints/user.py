"""
User endpoints with permission-based field filtering.
"""

import io
import json
import os
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_db,
)
from app.api.lifecycle import openapi_lifecycle

# from app.core.security import auth0_validator
from app.crud import tlog as tlog_crud
from app.crud import tphoto as tphoto_crud
from app.crud import user as user_crud
from app.models.server import Server
from app.models.trig import Trig
from app.models.user import User
from app.schemas.tlog import TLogResponse
from app.schemas.tphoto import TPhotoResponse
from app.schemas.user import (
    UserPrefs,
    UserResponse,
    UserStats,
    UserWithIncludes,
)
from app.services.badge_service import BadgeService
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


@router.get("/{user_id}/logs", openapi_extra=openapi_lifecycle("beta"))
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
                tlog_id=int(p.tlog_id),
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
    found_colour: str = Query("#ff0000", description="Hex colour for found trigs"),
    notfound_colour: Optional[str] = Query(
        "#0000ff", description="Hex colour for not-found trigs"
    ),
    notlogged_colour: Optional[str] = Query(
        None, description="Hex colour for not-logged trigs (if provided)"
    ),
    db: Session = Depends(get_db),
):
    """
    Render a user map overlay using `res/ukmap.jpg` and `res/uk_map_calibration.json`.

    Expensive full-trig-table query is performed only when `notlogged_colour` is provided.
    """
    try:
        # Normalise empty strings to None
        notfound_hex = (notfound_colour or "").strip() or None
        notlogged_hex = (notlogged_colour or "").strip() or None
        found_hex = (found_colour or "#ff0000").strip() or "#ff0000"

        # Load base map image (fallback if missing)
        map_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "..",
            "res",
            "ukmap.jpg",
        )
        map_path = os.path.normpath(map_path)
        if os.path.isfile(map_path):
            base = Image.open(map_path).convert("RGB")
        else:
            # Fallback canvas (if resource missing)
            base = Image.new("RGB", (800, 900), color=(255, 255, 255))

        # Load calibration
        calib_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "..",
            "res",
            "uk_map_calibration.json",
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

        draw = ImageDraw.Draw(base)

        def draw_dot(px: float, py: float, hex_colour: str, r: int = 2) -> None:
            if not hex_colour:
                return
            x = int(round(px))
            y = int(round(py))
            if x < 0 or y < 0 or x >= base.size[0] or y >= base.size[1]:
                return
            bbox = [x - r, y - r, x + r, y + r]
            draw.ellipse(bbox, fill=hex_colour, outline=None)

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
        found_pts = []
        notfound_pts = []
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
                draw_dot(x, y, notlogged_hex)

        # Draw notfound beneath found
        if notfound_hex:
            for x, y in notfound_pts:
                draw_dot(x, y, notfound_hex)
        # Draw found on top
        for x, y in found_pts:
            draw_dot(x, y, found_hex)

        # Encode image
        buf = io.BytesIO()
        base.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Server configuration error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering user map: {e}")
