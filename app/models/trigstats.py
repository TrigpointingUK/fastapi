"""
SQLAlchemy model for the trigstats table.
"""

from typing import Any

from sqlalchemy import DATE, DECIMAL, INTEGER, SMALLINT, TIMESTAMP, Column

from app.db.database import Base


class TrigStats(Base):
    """Statistics for a trigpoint, keyed by trig.id."""

    __tablename__ = "trigstats"

    # Primary key and FK to trig.id (not declared as FK due to legacy DB constraints)
    id = Column(INTEGER, primary_key=True, index=True)

    # Log related stats
    logged_first = Column(DATE, nullable=False)
    logged_last = Column(DATE, nullable=False)
    logged_count = Column(INTEGER, nullable=False)

    # Found related stats
    found_last = Column(DATE, nullable=False)
    found_count = Column(INTEGER, nullable=False)

    # Photos
    photo_count = Column(INTEGER, nullable=False)

    # Scores
    score_mean: Any = Column(DECIMAL(5, 2), nullable=False)
    score_baysian: Any = Column(DECIMAL(5, 2), nullable=False)

    # Area height
    area_osgb_height = Column(SMALLINT, nullable=False)

    # Audit
    upd_timestamp = Column(TIMESTAMP, nullable=True)

    def __repr__(self):
        return f"<TrigStats(id={self.id}, logged_count={self.logged_count}, photo_count={self.photo_count})>"
