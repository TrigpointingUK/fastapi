"""
CRUD operations for tphoto table.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from api.models.tphoto import TPhoto
from api.models.user import TLog


def get_photo_by_id(db: Session, photo_id: int) -> Optional[TPhoto]:
    """Fetch a photo by primary key, excluding soft-deleted rows by default."""
    return (
        db.query(TPhoto)
        .filter(TPhoto.id == photo_id, TPhoto.deleted_ind != "Y")
        .first()
    )


def update_photo(db: Session, photo_id: int, updates: dict) -> Optional[TPhoto]:
    """Update mutable fields on a photo and return the updated row."""
    photo = db.query(TPhoto).filter(TPhoto.id == photo_id).first()
    if not photo:
        return None

    for key, value in updates.items():
        if hasattr(photo, key):
            setattr(photo, key, value)

    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def delete_photo(db: Session, photo_id: int, soft: bool = True) -> bool:
    """Delete a photo. Soft delete sets deleted_ind='Y' by default."""
    photo = db.query(TPhoto).filter(TPhoto.id == photo_id).first()
    if not photo:
        return False

    if soft:
        # Use setattr to avoid mypy Column type inference issues
        setattr(photo, "deleted_ind", "Y")
        db.add(photo)
    else:
        db.delete(photo)

    db.commit()
    return True


def list_photos_filtered(
    db: Session,
    *,
    trig_id: Optional[int] = None,
    log_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 10,
) -> List[TPhoto]:
    q = db.query(TPhoto).filter(TPhoto.deleted_ind != "Y")
    if log_id is not None:
        q = q.filter(TPhoto.tlog_id == log_id)
    if user_id is not None:
        q = q.join(TLog, TLog.id == TPhoto.tlog_id).filter(TLog.user_id == user_id)
    if trig_id is not None:
        q = q.join(TLog, TLog.id == TPhoto.tlog_id).filter(TLog.trig_id == trig_id)

    # Default newest first by id
    q = q.order_by(TPhoto.id.desc())
    return q.offset(skip).limit(limit).all()


def list_all_photos_for_log(db: Session, *, log_id: int) -> List[TPhoto]:
    """Return all non-deleted photos for a given tlog without pagination."""
    return (
        db.query(TPhoto)
        .filter(TPhoto.tlog_id == log_id, TPhoto.deleted_ind != "Y")
        .order_by(TPhoto.id.desc())
        .all()
    )


def create_photo(
    db: Session,
    *,
    log_id: int,
    values: dict,
) -> TPhoto:
    photo = TPhoto(tlog_id=log_id, **values)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo
