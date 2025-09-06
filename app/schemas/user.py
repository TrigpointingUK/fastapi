"""
Pydantic schemas for user endpoints with permission-based field filtering.
"""

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user schema with always-public fields."""

    id: int = Field(..., description="User ID")
    name: str = Field(..., description="Username")
    firstname: str = Field(..., description="First name")
    surname: str = Field(..., description="Surname")
    about: str = Field(..., description="User bio/description")


class UserPublic(UserBase):
    """Public user schema - includes email only if user has public profile."""

    email: Optional[str] = Field(None, description="Email address (only if public)")
    homepage: Optional[str] = Field(None, description="User homepage URL")
    distance_ind: Optional[str] = Field(
        None, description="Distance unit preference (K/M)"
    )
    cacher_ind: Optional[str] = Field(None, description="Geocacher status (Y/N)")
    trigger_ind: Optional[str] = Field(None, description="Trigger status (Y/N)")

    class Config:
        from_attributes = True


class UserPrivate(UserBase):
    """Private user schema - includes all fields for authenticated users."""

    # Core identity
    cacher_id: int = Field(..., description="Cacher ID")
    email: str = Field(..., description="Email address")
    email_valid: str = Field(..., description="Email validation status (Y/N)")
    email_ind: str = Field(..., description="Email indicator (Y/N)")
    homepage: str = Field(..., description="User homepage URL")
    distance_ind: str = Field(..., description="Distance unit preference (K/M)")

    # Status and limits
    status_max: int = Field(..., description="Maximum status value")

    # Home locations
    home1_name: str = Field(..., description="Home 1 name")
    home1_eastings: int = Field(..., description="Home 1 eastings")
    home1_northings: int = Field(..., description="Home 1 northings")
    home1_gridref: str = Field(..., description="Home 1 grid reference")
    home2_name: str = Field(..., description="Home 2 name")
    home2_eastings: int = Field(..., description="Home 2 eastings")
    home2_northings: int = Field(..., description="Home 2 northings")
    home2_gridref: str = Field(..., description="Home 2 grid reference")
    home3_name: str = Field(..., description="Home 3 name")
    home3_eastings: int = Field(..., description="Home 3 eastings")
    home3_northings: int = Field(..., description="Home 3 northings")
    home3_gridref: str = Field(..., description="Home 3 grid reference")

    # Display preferences
    album_rows: int = Field(..., description="Album rows")
    album_cols: int = Field(..., description="Album columns")
    public_ind: str = Field(..., description="Public profile status (Y/N)")

    # SMS functionality
    sms_number: Optional[str] = Field(None, description="SMS number")
    sms_credit: int = Field(..., description="SMS credit")
    sms_grace: int = Field(..., description="SMS grace period")

    # User type indicators
    cacher_ind: str = Field(..., description="Geocacher status (Y/N)")
    trigger_ind: str = Field(..., description="Trigger status (Y/N)")
    admin_ind: str = Field(..., description="Admin status (Y/N)")

    # Timestamps
    crt_date: date = Field(..., description="Creation date")
    crt_time: time = Field(..., description="Creation time")
    upd_timestamp: datetime = Field(..., description="Last update timestamp")

    # Legal agreements
    disclaimer_ind: str = Field(..., description="Disclaimer accepted (Y/N)")
    disclaimer_timestamp: datetime = Field(..., description="Disclaimer timestamp")
    gc_licence_ind: str = Field(..., description="GC licence accepted (Y/N)")
    gc_licence_timestamp: datetime = Field(..., description="GC licence timestamp")

    # Geocaching.com integration
    gc_auth_ind: str = Field(..., description="GC auth status (Y/N)")
    gc_auth_challenge: str = Field(..., description="GC auth challenge")
    gc_auth_timestamp: datetime = Field(..., description="GC auth timestamp")
    gc_premium_ind: str = Field(..., description="GC premium status (Y/N)")
    gc_premium_timestamp: datetime = Field(..., description="GC premium timestamp")

    # Display and search preferences
    nearest_max_m: int = Field(
        ..., description="Maximum distance for nearest search (meters)"
    )
    online_map_type: str = Field(..., description="Online map type")
    online_map_type2: str = Field(..., description="Secondary online map type")
    trigmap_b: int = Field(..., description="Trigmaps B setting")
    trigmap_l: int = Field(..., description="Trigmaps L setting")
    trigmap_c: int = Field(..., description="Trigmaps C setting")
    showscores: str = Field(..., description="Show scores preference (Y/N)")
    showhandi: str = Field(..., description="Show handicap preference (Y/N)")

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Dynamic user response that adapts fields based on permissions."""

    # Always included
    id: int
    name: str
    firstname: str
    surname: str
    about: str

    # Conditionally included based on permissions
    email: Optional[str] = None
    email_valid: Optional[str] = None
    admin_ind: Optional[str] = None
    public_ind: Optional[str] = None
    homepage: Optional[str] = None
    distance_ind: Optional[str] = None
    cacher_ind: Optional[str] = None
    trigger_ind: Optional[str] = None

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """Simplified user summary for list endpoints."""

    id: int
    name: str
    firstname: str
    surname: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT Token response."""

    access_token: str
    token_type: str


class LoginResponse(BaseModel):
    """Enhanced login response with token and essential user data."""

    # JWT token for API authentication
    access_token: str
    token_type: str

    # Essential user data (reduces need for immediate /user/me call)
    user: UserResponse

    # Optional: token metadata
    expires_in: int  # seconds until token expires


class UserEmail(BaseModel):
    """User email response for JWT-protected endpoints."""

    user_id: int  # Keep as user_id for API compatibility
    email: str
