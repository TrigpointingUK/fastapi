"""
CRUD helpers for status lookup.
"""

from typing import Optional

from sqlalchemy.orm import Session

from api.models.status import Status


def get_status_name_by_id(db: Session, status_id: int) -> Optional[str]:
    # Return a plain string using scalar() to avoid ORM attribute types in typing
    return db.query(Status.name).filter(Status.id == status_id).scalar()
