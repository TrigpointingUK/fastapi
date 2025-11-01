"""
CRUD operations for trigstats table.
"""

from typing import Optional

from sqlalchemy.orm import Session

from api.models.trigstats import TrigStats


def get_trigstats_by_id(db: Session, trig_id: int) -> Optional[TrigStats]:
    """
    Get trigstats by trig ID.

    Args:
        db: Database session
        trig_id: Trigpoint ID (primary key in trigstats)

    Returns:
        TrigStats object or None if not found
    """
    return db.query(TrigStats).filter(TrigStats.id == trig_id).first()
