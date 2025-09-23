"""
Trig endpoints for trigpoint data.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.lifecycle import lifecycle, openapi_lifecycle
from app.crud import status as status_crud
from app.crud import trig as trig_crud
from app.crud import trigstats as trigstats_crud
from app.schemas.trig import (
    TrigDetails,
    TrigMinimal,
)
from app.schemas.trig import TrigStats as TrigStatsSchema
from app.schemas.trig import (
    TrigSummary,
    TrigWithIncludes,
)
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
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    _lc=lifecycle("beta"),
    db: Session = Depends(get_db),
):
    """
    Filtered collection endpoint for trigs returning envelope with items, pagination, links.
    """
    items = trig_crud.list_trigs_filtered(
        db, name=name, county=county, skip=skip, limit=limit
    )
    total = trig_crud.count_trigs_filtered(db, name=name, county=county)

    has_more = (skip + len(items)) < total
    base = "/v1/trigs"
    params = []
    if name:
        params.append(f"name={name}")
    if county:
        params.append(f"county={county}")
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

    # Serialize items using TrigSummary
    items_serialized = [TrigSummary.model_validate(i).model_dump() for i in items]
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


# removed stats count endpoint


# removed separate details endpoint (use include=details)


# removed separate stats endpoint (use include=stats)
