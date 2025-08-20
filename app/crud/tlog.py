"""
CRUD operations for tlog table.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import TLog


def get_trig_count(db: Session, trig_id: int) -> int:
    """Get count of rows matching trig_id in tlog table."""
    return db.query(func.count(TLog.id)).filter(TLog.trig_id == trig_id).scalar() or 0
