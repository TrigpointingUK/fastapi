"""
CRUD operations for tphoto table.
"""

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tphoto import TPhoto
from app.models.user import TLog


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


def count_photos_by_user(db: Session, user_id: int) -> int:
    """Count photos uploaded by a user via join tphoto -> tlog -> user_id."""
    return (
        db.query(func.count(TPhoto.id))
        .join(TLog, TLog.id == TPhoto.tlog_id)
        .filter(TLog.user_id == user_id, TPhoto.deleted_ind != "Y")
        .scalar()
        or 0
    )
