"""
Trig endpoints for trigpoint data.
"""

from typing import List

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud import trig as trig_crud
from app.schemas.trig import TrigResponse, TrigSummary
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter()


@router.get("/{trig_id}", response_model=TrigResponse)
def get_trig(trig_id: int, db: Session = Depends(get_db)):
    """
    Get a trigpoint by ID.

    Returns all trigpoint data including coordinates, classification,
    and audit information.
    """
    trig = trig_crud.get_trig_by_id(db, trig_id=trig_id)
    if trig is None:
        raise HTTPException(status_code=404, detail="Trigpoint not found")
    return trig


@router.get("/waypoint/{waypoint}", response_model=TrigResponse)
def get_trig_by_waypoint(waypoint: str, db: Session = Depends(get_db)):
    """
    Get a trigpoint by waypoint code (e.g., "TP0001").

    Returns all trigpoint data including coordinates, classification,
    and audit information.
    """
    trig = trig_crud.get_trig_by_waypoint(db, waypoint=waypoint)
    if trig is None:
        raise HTTPException(status_code=404, detail="Trigpoint not found")
    return trig


@router.get("/search/name", response_model=List[TrigSummary])
def search_trigs_by_name(
    q: str = Query(..., description="Search query for trigpoint names"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    db: Session = Depends(get_db),
):
    """
    Search trigpoints by name.

    Returns a list of trigpoints matching the search query.
    Limited to essential fields for performance.
    """
    trigs = trig_crud.search_trigs_by_name(db, name_pattern=q, skip=skip, limit=limit)
    return trigs


@router.get("/county/{county}", response_model=List[TrigSummary])
def get_trigs_by_county(
    county: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    db: Session = Depends(get_db),
):
    """
    Get trigpoints in a specific county.

    Returns a list of trigpoints in the specified county.
    Limited to essential fields for performance.
    """
    trigs = trig_crud.get_trigs_by_county(db, county=county, skip=skip, limit=limit)
    return trigs


@router.get("/stats/count")
def get_trig_count(db: Session = Depends(get_db)):
    """
    Get total number of trigpoints in the database.

    Returns:
        JSON object with total count
    """
    count = trig_crud.get_trigs_count(db)
    return {"total_trigpoints": count}
