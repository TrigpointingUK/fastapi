"""
Trig endpoints for trigpoint data.
"""

import io
import json
import os
from math import cos, radians, sqrt
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.lifecycle import lifecycle, openapi_lifecycle
from app.crud import status as status_crud
from app.crud import tlog as tlog_crud
from app.crud import tphoto as tphoto_crud
from app.crud import trig as trig_crud
from app.crud import trigstats as trigstats_crud
from app.models.server import Server
from app.schemas.tlog import TLogResponse
from app.schemas.tphoto import TPhotoResponse
from app.schemas.trig import (
    TrigDetails,
    TrigMinimal,
)
from app.schemas.trig import TrigStats as TrigStatsSchema
from app.schemas.trig import (
    TrigWithIncludes,
)
from app.utils.geocalibrate import CalibrationResult
from app.utils.url import join_url
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get(
    "/{trig_id}",
    response_model=TrigWithIncludes,
    openapi_extra=openapi_lifecycle(
        "beta", note="Shape may change; fieldset stabilising"
    ),
)
def get_trig(
    trig_id: int,
    include: Optional[str] = Query(
        None, description="Comma-separated list of includes: details,stats"
    ),
    _lc=lifecycle("beta", note="Shape may change"),
    db: Session = Depends(get_db),
):
    """
    Get a trigpoint by ID.

    Default: minimal fields. Supports include=details,stats.
    """
    trig = trig_crud.get_trig_by_id(db, trig_id=trig_id)
    if trig is None:
        raise HTTPException(status_code=404, detail="Trigpoint not found")

    # Build minimal response with status_name
    minimal_data = TrigMinimal.model_validate(trig).model_dump()
    status_name = status_crud.get_status_name_by_id(db, int(trig.status_id))
    minimal_data["status_name"] = status_name

    # Attach includes
    details_obj: Optional[TrigDetails] = None
    stats_obj: Optional[TrigStatsSchema] = None
    if include:
        tokens = {t.strip() for t in include.split(",") if t.strip()}

        # Validate include tokens
        valid_includes = {"details", "stats"}
        invalid_tokens = tokens - valid_includes
        if invalid_tokens:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid include parameter(s): {', '.join(sorted(invalid_tokens))}. Valid options: {', '.join(sorted(valid_includes))}",
            )
        if "details" in tokens:
            details_obj = TrigDetails.model_validate(trig)
        if "stats" in tokens:
            stats = trigstats_crud.get_trigstats_by_id(db, trig_id=trig_id)
            if stats:
                stats_obj = TrigStatsSchema.model_validate(stats)

    return TrigWithIncludes(**minimal_data, details=details_obj, stats=stats_obj)


@router.get(
    "/waypoint/{waypoint}",
    response_model=TrigWithIncludes,
    openapi_extra=openapi_lifecycle("beta", note="Returns minimal shape only"),
)
def get_trig_by_waypoint(
    waypoint: str, _lc=lifecycle("beta"), db: Session = Depends(get_db)
):
    """
    Get a trigpoint by waypoint code (e.g., "TP0001").

    Returns minimal data by waypoint.
    """
    trig = trig_crud.get_trig_by_waypoint(db, waypoint=waypoint)
    if trig is None:
        raise HTTPException(status_code=404, detail="Trigpoint not found")

    minimal_data = TrigMinimal.model_validate(trig).model_dump()
    status_name = status_crud.get_status_name_by_id(db, int(trig.status_id))
    minimal_data["status_name"] = status_name
    return TrigWithIncludes(**minimal_data)


# removed deprecated name search endpoint


@router.get(
    "",
    openapi_extra=openapi_lifecycle("beta", note="Filtered collection listing"),
)
def list_trigs(
    name: Optional[str] = Query(None, description="Filter by trig name (contains)"),
    county: Optional[str] = Query(None, description="Filter by county (exact)"),
    lat: Optional[float] = Query(None, description="Centre latitude (WGS84)"),
    lon: Optional[float] = Query(None, description="Centre longitude (WGS84)"),
    max_km: Optional[float] = Query(
        None, ge=0, description="Max distance from centre (km)"
    ),
    order: Optional[str] = Query(None, description="id | name | distance"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    _lc=lifecycle("beta"),
    db: Session = Depends(get_db),
):
    """
    Filtered collection endpoint for trigs returning envelope with items, pagination, links.
    """
    items = trig_crud.list_trigs_filtered(
        db,
        name=name,
        county=county,
        skip=skip,
        limit=limit,
        center_lat=lat,
        center_lon=lon,
        max_km=max_km,
        order=order,
    )
    total = trig_crud.count_trigs_filtered(
        db,
        name=name,
        county=county,
        center_lat=lat,
        center_lon=lon,
        max_km=max_km,
    )

    # serialise
    items_serialized = [TrigMinimal.model_validate(i).model_dump() for i in items]

    # Compute distance_km for returned page only (cheap), matching SQL formula
    if lat is not None and lon is not None:
        deg_km = 111.32
        cos_lat = cos(radians(lat))
        for d in items_serialized:
            dlat_km = (float(d["wgs_lat"]) - lat) * deg_km
            dlon_km = (float(d["wgs_long"]) - lon) * deg_km * cos_lat
            d["distance_km"] = round(sqrt(dlat_km * dlat_km + dlon_km * dlon_km), 1)

    has_more = (skip + len(items)) < total
    base = "/v1/trigs"
    params = []
    if name:
        params.append(f"name={name}")
    if county:
        params.append(f"county={county}")
    if lat is not None:
        params.append(f"lat={lat}")
    if lon is not None:
        params.append(f"lon={lon}")
    if max_km is not None:
        params.append(f"max_km={max_km}")
    if order:
        params.append(f"order={order}")
    params.append(f"limit={limit}")
    # self link
    self_link = base + "?" + "&".join(params + [f"skip={skip}"])
    next_link = (
        base + "?" + "&".join(params + [f"skip={skip + limit}"]) if has_more else None
    )
    prev_offset = max(skip - limit, 0)
    prev_link = (
        base + "?" + "&".join(params + [f"skip={prev_offset}"]) if skip > 0 else None
    )

    # Serialize items minimally
    # items_serialized = [TrigMinimal.model_validate(i).model_dump() for i in items]
    # Attach status_name to each item
    for item, orig in zip(items_serialized, items):
        item["status_name"] = status_crud.get_status_name_by_id(db, int(orig.status_id))

    response = {
        "items": items_serialized,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": skip,
            "has_more": has_more,
        },
        "links": {"self": self_link, "next": next_link, "prev": prev_link},
    }
    if lat is not None and lon is not None:
        response["context"] = {
            "centre": {"lat": lat, "lon": lon, "srid": 4326},
            "max_km": max_km,
            "order": order or "distance",
        }
    else:
        response["context"] = {"order": order or "id"}
    return response


# -----------------------------------------------------------------------------
# Map for a single trig
# -----------------------------------------------------------------------------


@router.get(
    "/{trig_id}/map",
    responses={200: {"content": {"image/png": {}}, "description": "PNG map for trig"}},
    openapi_extra=openapi_lifecycle(
        "beta",
        note=(
            "Renders a transparent-background PNG with land fill and coastline stroke. "
            "Draws a single dot at the trig's WGS84 position."
        ),
    ),
)
def get_trig_map(
    trig_id: int,
    map_variant: Optional[str] = Query(
        "stretched53", description="Map variant: stretched53 (default) or wgs84"
    ),
    dot_colour: Optional[str] = Query(
        "#0000ff", description="Hex #RRGGBB for the trig dot"
    ),
    dot_diameter: int = Query(
        50, ge=1, le=100, description="Dot diameter in pixels (default 50)"
    ),
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
    # Fetch trig
    trig = trig_crud.get_trig_by_id(db, trig_id=trig_id)
    if trig is None:
        raise HTTPException(status_code=404, detail="Trigpoint not found")

    # Choose assets
    image_filename = (
        "ukmap_wgs84_stretched53.png"
        if (map_variant or "").lower() == "stretched53"
        else "ukmap_wgs84.png"
    )
    calib_filename = (
        "uk_map_calibration_wgs84_stretched53.json"
        if (map_variant or "").lower() == "stretched53"
        else "uk_map_calibration_wgs84.json"
    )
    res_dir = os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            "..",
            "res",
        )
    )
    map_path = os.path.join(res_dir, image_filename)
    calib_path = os.path.join(res_dir, calib_filename)

    # Load image (keep alpha) and calibration
    base = (
        Image.open(map_path).convert("RGBA")
        if os.path.isfile(map_path)
        else Image.new("RGBA", (800, 900), (0, 0, 0, 0))
    )
    with open(calib_path, "r") as f:
        d = json.load(f)
    calib = CalibrationResult(
        affine=np.array(d["affine"], dtype=float),
        inverse=np.array(d["inverse"], dtype=float),
        pixel_bbox=tuple(d.get("pixel_bbox", (0, 0, base.size[0], base.size[1]))),
        bounds_geo=tuple(d.get("bounds_geo", (-11.0, 49.0, 2.5, 61.5))),
    )

    # Optionally recolour land and reapply coastline stroke
    if land_colour and land_colour.strip().lower() != "none":
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
            # stroke
            edge_mask = alpha_ch.filter(ImageFilter.FIND_EDGES)
            try:
                edge_mask = edge_mask.filter(ImageFilter.MaxFilter(3))
            except Exception:
                edge_mask = edge_mask
            sc = (102, 102, 102, 255)
            if coastline_colour:
                s = coastline_colour.strip()
                if s.startswith("#"):
                    s = s[1:]
                if len(s) == 6:
                    sc = (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
            stroke_layer = Image.new("RGBA", base.size, sc)
            base.paste(stroke_layer, (0, 0), edge_mask)

    # Draw a single opaque dot at trig location
    x, y = calib.lonlat_to_xy(float(trig.wgs_long), float(trig.wgs_lat))
    draw = ImageDraw.Draw(base)
    r = max(1, int(round(dot_diameter / 2)))
    if dot_colour and dot_colour.strip().lower() != "none":
        s = dot_colour.strip()
        if s.startswith("#"):
            s = s[1:]
        if len(s) >= 6:
            rr = int(s[0:2], 16)
            gg = int(s[2:4], 16)
            bb = int(s[4:6], 16)
            fill = (rr, gg, bb, 255)  # hardcoded 100% alpha
        else:
            fill = (0, 0, 170, 255)
        bbox = [
            int(round(x - r)),
            int(round(y - r)),
            int(round(x + r)),
            int(round(y + r)),
        ]
        draw.ellipse(bbox, fill=fill, outline=None)

    # Optional final scaling
    if isinstance(height, int) and height > 0 and base.height != height:
        scale = float(height) / float(base.height)
        new_w = max(1, int(round(base.width * scale)))
        try:
            resample = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
        except Exception:
            try:
                resample = Image.Resampling.NEAREST  # type: ignore[attr-defined]
            except Exception:
                resample = 0  # type: ignore[assignment]
        base = base.resize((new_w, height), resample=resample)

    buf = io.BytesIO()
    base.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.get(
    "/{trig_id}/logs",
    openapi_extra=openapi_lifecycle("beta", note="List logs for a trig"),
)
def list_logs_for_trig(
    trig_id: int,
    include: Optional[str] = Query(
        None, description="Comma-separated list of includes: photos"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = tlog_crud.list_logs_filtered(db, trig_id=trig_id, skip=skip, limit=limit)
    total = tlog_crud.count_logs_filtered(db, trig_id=trig_id)
    items_serialized = [TLogResponse.model_validate(i).model_dump() for i in items]

    # Handle includes
    if include:
        tokens = {t.strip() for t in include.split(",") if t.strip()}

        # Validate include tokens
        valid_includes = {"photos"}
        invalid_tokens = tokens - valid_includes
        if invalid_tokens:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid include parameter(s): {', '.join(sorted(invalid_tokens))}. Valid options: {', '.join(sorted(valid_includes))}",
            )
        if "photos" in tokens:
            for out, orig in zip(items_serialized, items):
                photos = tphoto_crud.list_all_photos_for_log(db, log_id=int(orig.id))
                out["photos"] = []
                for p in photos:
                    server: Server | None = (
                        db.query(Server).filter(Server.id == p.server_id).first()
                    )
                    base_url = str(server.url) if server and server.url else ""
                    out["photos"].append(
                        TPhotoResponse(
                            id=int(p.id),
                            log_id=int(p.tlog_id),
                            user_id=int(orig.user_id),
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
    base = f"/v1/trigs/{trig_id}/logs"
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


# removed POST /{trig_id}/logs to keep mutations on their resource endpoints


@router.get(
    "/{trig_id}/photos",
    openapi_extra=openapi_lifecycle("beta", note="List photos for a trig"),
)
def list_photos_for_trig(
    trig_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = tphoto_crud.list_photos_filtered(
        db, trig_id=trig_id, skip=skip, limit=limit
    )
    total = (
        db.query(tphoto_crud.TPhoto)
        .join(tlog_crud.TLog, tlog_crud.TLog.id == tphoto_crud.TPhoto.tlog_id)
        .filter(
            tlog_crud.TLog.trig_id == trig_id, tphoto_crud.TPhoto.deleted_ind != "Y"
        )
        .count()
    )
    result_items = []
    for p in items:
        # Defer URLs; provide minimal fields consistent with collection shape
        # Resolve user via TLog join
        # Caution: join already filtered; just map
        server: Server | None = (
            db.query(Server).filter(Server.id == p.server_id).first()
        )
        base_url = str(server.url) if server and server.url else ""
        result_items.append(
            TPhotoResponse(
                id=int(p.id),
                log_id=int(p.tlog_id),
                user_id=0,  # omitted to avoid per-item query; can be enriched later
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
    base = f"/v1/trigs/{trig_id}/photos"
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
