"""
Database models for the existing legacy database schema.
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.types import CHAR

from app.db.database import Base


class User(Base):
    """User model matching the existing legacy database schema."""

    __tablename__ = "user"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)  # MEDIUMINT in MySQL

    # Core identity fields
    name = Column(String(30), nullable=False, index=True)  # Username
    firstname = Column(String(30), nullable=False)
    surname = Column(String(30), nullable=False)
    email = Column(String(255), nullable=False, index=True)

    # Authentication - Unix crypt format password
    cryptpw = Column(String(34), nullable=False)  # Never expose in API

    # Profile information
    about = Column(Text, nullable=False)  # User bio/description

    # Permissions and visibility flags
    admin_ind = Column(CHAR(1), nullable=False, default="N")  # Y/N admin flag
    email_valid = Column(CHAR(1), nullable=False, default="N")  # Y/N email verified
    public_ind = Column(CHAR(1), nullable=False, default="Y")  # Y/N public profile


class TLog(Base):
    """TLog model for the tlog table."""

    __tablename__ = "tlog"

    id = Column(Integer, primary_key=True, index=True)
    trig_id = Column(Integer, index=True, nullable=False)
    # Add other fields as they exist in your legacy schema
    # log_data = Column(Text)
    # timestamp = Column(DateTime)
    # etc.
