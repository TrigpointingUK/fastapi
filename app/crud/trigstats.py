"""
CRUD operations for trigstats table.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.tracing import trace_function
from app.models.trigstats import TrigStats


@trace_function("crud.trigstats.get_by_id")
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
