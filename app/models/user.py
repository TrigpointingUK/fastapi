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
    cacher_id = Column(Integer, nullable=False, default=0)

    # Core identity fields
    name = Column(String(30), nullable=False, index=True, unique=True)  # Username
    firstname = Column(String(30), nullable=False, default="")
    surname = Column(String(30), nullable=False, default="")
    email = Column(String(255), nullable=False, default="", index=True)
    email_challenge = Column(String(34), nullable=False, default="")
    email_valid = Column(CHAR(1), nullable=False, default="N")
    email_ind = Column(CHAR(1), nullable=False, default="N")
    homepage = Column(String(255), nullable=False, default="")
    distance_ind = Column(CHAR(1), nullable=False, default="K")
    about = Column(Text, nullable=False, default="")

    # Status and limits
    status_max = Column(Integer, nullable=False, default=0)

    # Home locations (3 different home/work locations)
    home1_name = Column(String(20), nullable=False, default="home")
    home1_eastings = Column(Integer, nullable=False, default=0)
    home1_northings = Column(Integer, nullable=False, default=0)
    home1_gridref = Column(String(14), nullable=False, default="")
    home2_name = Column(String(20), nullable=False, default="work")
    home2_eastings = Column(Integer, nullable=False, default=0)
    home2_northings = Column(Integer, nullable=False, default=0)
    home2_gridref = Column(String(14), nullable=False, default="")
    home3_name = Column(String(20), nullable=False, default="")
    home3_eastings = Column(Integer, nullable=False, default=0)
    home3_northings = Column(Integer, nullable=False, default=0)
    home3_gridref = Column(String(14), nullable=False, default="")

    # Display preferences
    album_rows = Column(SmallInteger, nullable=False, default=2)
    album_cols = Column(SmallInteger, nullable=False, default=4)
    public_ind = Column(CHAR(1), nullable=False, default="N")

    # SMS functionality
    sms_number = Column(String(12), nullable=True)
    sms_credit = Column(Integer, nullable=False, default=0)
    sms_grace = Column(SmallInteger, nullable=False, default=5)

    # Authentication - Unix crypt format password
    cryptpw = Column(String(34), nullable=False, default="")

    # Auth0 integration
    auth0_user_id = Column(CHAR(24), nullable=True, index=True)

    # User type indicators
    cacher_ind = Column(CHAR(1), nullable=False, default="N")
    trigger_ind = Column(CHAR(1), nullable=False, default="N")
    admin_ind = Column(CHAR(1), nullable=False, default="N")

    # Timestamps
    crt_date = Column(Date, nullable=False, default=date(1900, 1, 1))
    crt_time = Column(Time, nullable=False, default=time(0, 0, 0))
    upd_timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # Legal agreements
    disclaimer_ind = Column(CHAR(1), nullable=False, default="N")
    disclaimer_timestamp = Column(
        DateTime, nullable=False, default=datetime(1900, 1, 1, 0, 0, 0)
    )
    gc_licence_ind = Column(CHAR(1), nullable=False, default="N")
    gc_licence_timestamp = Column(
        DateTime, nullable=False, default=datetime(1900, 1, 1, 0, 0, 0)
    )

    # Geocaching.com integration
    gc_auth_ind = Column(CHAR(1), nullable=False, default="Y")
    gc_auth_challenge = Column(String(34), nullable=False, default="")
    gc_auth_timestamp = Column(
        DateTime, nullable=False, default=datetime(1900, 1, 1, 0, 0, 0)
    )
    gc_premium_ind = Column(CHAR(1), nullable=False, default="N")
    gc_premium_timestamp = Column(
        DateTime, nullable=False, default=datetime(1900, 1, 1, 0, 0, 0)
    )

    # Display and search preferences
    nearest_max_m = Column(Integer, nullable=False, default=50000)
    online_map_type = Column(String(10), nullable=False, default="")
    online_map_type2 = Column(String(10), nullable=False, default="lla")
    trigmap_b = Column(SmallInteger, nullable=False, default=2)
    trigmap_l = Column(SmallInteger, nullable=False, default=0)
    trigmap_c = Column(SmallInteger, nullable=False, default=0)
    showscores = Column(CHAR(1), nullable=False, default="Y")
    showhandi = Column(CHAR(1), nullable=False, default="Y")


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
