"""
CRUD operations for tlog table.
"""

from typing import Iterable, List, Optional, Tuple

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from app.core.tracing import trace_function
from app.models.tphoto import TPhoto
from app.models.user import TLog


@trace_function("crud.tlog.get_by_id")
def get_log_by_id(db: Session, log_id: int) -> Optional[TLog]:
    return db.query(TLog).filter(TLog.id == log_id).first()


@trace_function("crud.tlog.list_filtered")
def list_logs_filtered(
    db: Session,
    *,
    trig_id: Optional[int] = None,
    user_id: Optional[int] = None,
    order: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> List[TLog]:
    q = db.query(TLog)
    if trig_id is not None:
        q = q.filter(TLog.trig_id == trig_id)
    if user_id is not None:
        q = q.filter(TLog.user_id == user_id)

    # Default ordering newest first by (date, time, id)
    if order:
        # support order fields with optional '-' prefix
        directives: List[Tuple[str, bool]] = []
        for token in order.split(","):
            token = token.strip()
            if not token:
                continue
            desc_ind = token.startswith("-")
            field = token[1:] if desc_ind else token
            directives.append((field, desc_ind))

        for field, is_desc in directives:
            col = getattr(TLog, field, None)
            if col is None:
                continue
            q = q.order_by(desc(col) if is_desc else asc(col))
    else:
        q = q.order_by(desc(TLog.date), desc(TLog.time), desc(TLog.id))

    return q.offset(skip).limit(limit).all()


@trace_function("crud.tlog.count_filtered")
def count_logs_filtered(
    db: Session, *, trig_id: Optional[int] = None, user_id: Optional[int] = None
) -> int:
    q = db.query(func.count(TLog.id))
    if trig_id is not None:
        q = q.filter(TLog.trig_id == trig_id)
    if user_id is not None:
        q = q.filter(TLog.user_id == user_id)
    return int(q.scalar() or 0)


@trace_function("crud.tlog.create")
def create_log(
    db: Session,
    *,
    trig_id: int,
    user_id: int,
    values: dict,
) -> TLog:
    log = TLog(trig_id=trig_id, user_id=user_id, **values)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@trace_function("crud.tlog.update")
def update_log(db: Session, *, log_id: int, updates: dict) -> Optional[TLog]:
    log = db.query(TLog).filter(TLog.id == log_id).first()
    if not log:
        return None
    for key, value in updates.items():
        if hasattr(log, key):
            setattr(log, key, value)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def delete_log_hard(db: Session, *, log_id: int) -> bool:
    log = db.query(TLog).filter(TLog.id == log_id).first()
    if not log:
        return False
    db.delete(log)
    db.commit()
    return True


def soft_delete_photos_for_log(db: Session, *, log_id: int) -> int:
    """Soft delete all photos for a given tlog by setting deleted_ind='Y'. Returns count."""
    photos: Iterable[TPhoto] = (
        db.query(TPhoto)
        .filter(TPhoto.tlog_id == log_id, TPhoto.deleted_ind != "Y")
        .all()
    )
    count = 0
    for p in photos:
        setattr(p, "deleted_ind", "Y")
        db.add(p)
        count += 1
    db.commit()
    return count


@trace_function("crud.tlog.get_trig_count")
def get_trig_count(db: Session, trig_id: int) -> int:
    """Get count of rows matching trig_id in tlog table."""
    return db.query(func.count(TLog.id)).filter(TLog.trig_id == trig_id).scalar() or 0
