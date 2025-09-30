"""
Database models for the existing legacy database schema.
"""

from datetime import date, datetime, time

from sqlalchemy import Column, Date, DateTime, Integer, SmallInteger, String, Text, Time
from sqlalchemy.types import CHAR

from app.db.database import Base


class User(Base):
    """User model matching the existing legacy database schema."""

    __tablename__ = "user"

    # Primary identifier
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Core identity fields
    name = Column(String(30), nullable=False, index=True, unique=True)  # Username
    firstname = Column(String(30), nullable=False, default="")
    surname = Column(String(30), nullable=False, default="")
    email = Column(String(255), nullable=False, default="", index=True)
    email_valid = Column(CHAR(1), nullable=False, default="N")
    email_ind = Column(CHAR(1), nullable=False, default="N")
    homepage = Column(String(255), nullable=False, default="")
    distance_ind = Column(CHAR(1), nullable=False, default="K")
    about = Column(Text, nullable=False, default="")
    status_max = Column(Integer, nullable=False, default=0)

    # License preferences
    public_ind = Column(CHAR(1), nullable=False, default="N")

    # Legacy authentication
    cryptpw = Column(String(34), nullable=False, default="")

    # Auth0 integration
    auth0_user_id = Column(String(50), nullable=True, index=True)

    # Timestamps
    crt_date = Column(Date, nullable=False, default=date(1900, 1, 1))
    crt_time = Column(Time, nullable=False, default=time(0, 0, 0))
    upd_timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # Display and search preferences
    online_map_type = Column(String(10), nullable=False, default="")
    online_map_type2 = Column(String(10), nullable=False, default="lla")


class TLog(Base):
    """TLog model for the tlog table."""

    __tablename__ = "tlog"

    id = Column(Integer, primary_key=True, index=True)
    trig_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    osgb_eastings = Column(Integer, nullable=False)
    osgb_northings = Column(Integer, nullable=False)
    osgb_gridref = Column(String(14), nullable=False)
    fb_number = Column(String(10), nullable=False)
    condition = Column(CHAR(1), nullable=False)
    comment = Column(Text, nullable=False)
    score = Column(SmallInteger, nullable=False)
    ip_addr = Column(String(15), nullable=False)
    source = Column(CHAR(1), nullable=False)
    upd_timestamp = Column(DateTime, nullable=True)
