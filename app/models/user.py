"""
Database models for the existing legacy database schema.
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.types import CHAR

from app.db.database import Base


class User(Base):
    """User model matching the existing legacy database schema."""
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    admin_ind = Column(CHAR(1), default='N', nullable=False)
    # Add other fields as they exist in your legacy schema
    # first_name = Column(String(100))
    # last_name = Column(String(100))
    # created_at = Column(DateTime)
    # etc.


class TLog(Base):
    """TLog model for the tlog table."""
    __tablename__ = "tlog"

    id = Column(Integer, primary_key=True, index=True)
    trig_id = Column(Integer, index=True, nullable=False)
    # Add other fields as they exist in your legacy schema
    # log_data = Column(Text)
    # timestamp = Column(DateTime)
    # etc.
