"""
Trig endpoints for trigpoint data.
"""

from math import cos, radians, sqrt
from typing import Optional

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
from app.utils.url import join_url
from fastapi import APIRouter, Depends, HTTPException, Query

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
        unknown = tokens - {"details", "stats"}
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown include(s): {', '.join(sorted(unknown))}",
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
        unknown = tokens - {"photos"}
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown include(s): {', '.join(sorted(unknown))}",
            )
        if "photos" in tokens:
            for out, orig in zip(items_serialized, items):
                photos = tphoto_crud.list_all_photos_for_log(db, tlog_id=int(orig.id))
                out["photos"] = []
                for p in photos:
                    server: Server | None = (
                        db.query(Server).filter(Server.id == p.server_id).first()
                    )
                    base_url = str(server.url) if server and server.url else ""
                    out["photos"].append(
                        TPhotoResponse(
                            id=int(p.id),
                            tlog_id=int(p.tlog_id),
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
                tlog_id=int(p.tlog_id),
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
