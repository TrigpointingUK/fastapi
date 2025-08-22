"""
CRUD operations for trig table.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.trig import Trig


def get_trig_by_id(db: Session, trig_id: int) -> Optional[Trig]:
    """
    Get a trigpoint by ID.

    Args:
        db: Database session
        trig_id: Trigpoint ID

    Returns:
        Trig object or None if not found
    """
    return db.query(Trig).filter(Trig.id == trig_id).first()


def get_trig_by_waypoint(db: Session, waypoint: str) -> Optional[Trig]:
    """
    Get a trigpoint by waypoint code.

    Args:
        db: Database session
        waypoint: Waypoint code (e.g., "TP0001")

    Returns:
        Trig object or None if not found
    """
    return db.query(Trig).filter(Trig.waypoint == waypoint).first()


def get_trigs_by_county(
    db: Session, county: str, skip: int = 0, limit: int = 100
) -> list[Trig]:
    """
    Get trigpoints by county.

    Args:
        db: Database session
        county: County name
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Trig objects
    """
    return db.query(Trig).filter(Trig.county == county).offset(skip).limit(limit).all()


def search_trigs_by_name(
    db: Session, name_pattern: str, skip: int = 0, limit: int = 100
) -> list[Trig]:
    """
    Search trigpoints by name pattern.

    Args:
        db: Database session
        name_pattern: Name pattern to search for (case-insensitive)
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Trig objects
    """
    return (
        db.query(Trig)
        .filter(Trig.name.ilike(f"%{name_pattern}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_trigs_count(db: Session) -> int:
    """
    Get total number of trigpoints.

    Args:
        db: Database session

    Returns:
        Total count of trigpoints
    """
    return db.query(Trig).count()
