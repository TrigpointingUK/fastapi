"""
Pydantic schemas for trig endpoints.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TrigResponse(BaseModel):
    """Response model for trig data - includes all fields for now."""

    # Primary identifier
    id: int = Field(..., description="Trigpoint ID")
    waypoint: str = Field(..., description="Waypoint code (e.g., TP0001)")
    name: str = Field(..., description="Trigpoint name")

    # Classification
    status_id: int = Field(..., description="Status ID")
    user_added: int = Field(..., description="Whether user-added (0/1)")
    current_use: str = Field(..., description="Current use classification")
    historic_use: str = Field(..., description="Historic use classification")
    physical_type: str = Field(..., description="Physical type (e.g., Pillar)")
    condition: str = Field(..., description="Condition code")

    # Geographic coordinates
    wgs_lat: Decimal = Field(..., description="WGS84 latitude")
    wgs_long: Decimal = Field(..., description="WGS84 longitude")
    wgs_height: int = Field(..., description="WGS84 height (meters)")
    osgb_eastings: int = Field(..., description="OSGB eastings")
    osgb_northings: int = Field(..., description="OSGB northings")
    osgb_gridref: str = Field(..., description="OSGB grid reference")
    osgb_height: int = Field(..., description="OSGB height (meters)")

    # Location details
    postcode6: str = Field(..., description="Postcode area")
    county: str = Field(..., description="County")
    town: str = Field(..., description="Town/area")

    # Station identifiers
    fb_number: str = Field(..., description="Flush bracket number")
    stn_number: str = Field(..., description="Station number")
    stn_number_active: Optional[str] = Field(None, description="Active station number")
    stn_number_passive: Optional[str] = Field(
        None, description="Passive station number"
    )
    stn_number_osgb36: Optional[str] = Field(None, description="OSGB36 station number")

    # External systems
    os_net_web_id: Optional[int] = Field(None, description="OS Net Web ID")

    # Administrative
    permission_ind: str = Field(..., description="Permission indicator")
    needs_attention: int = Field(..., description="Needs attention flag (0/1)")
    attention_comment: str = Field(..., description="Attention comments")

    # Audit information
    crt_date: date = Field(..., description="Creation date")
    crt_time: time = Field(..., description="Creation time")
    crt_user_id: int = Field(..., description="Creating user ID")
    crt_ip_addr: str = Field(..., description="Creating IP address")
    admin_user_id: Optional[int] = Field(None, description="Admin user ID")
    admin_timestamp: Optional[datetime] = Field(
        None, description="Admin update timestamp"
    )
    admin_ip_addr: Optional[str] = Field(None, description="Admin IP address")
    upd_timestamp: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True  # Pydantic v2 syntax
        json_encoders = {
            Decimal: str,  # Convert Decimal to string for JSON serialization
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        }


class TrigSummary(BaseModel):
    """Simplified trig summary for list endpoints (future use)."""

    id: int
    waypoint: str
    name: str
    wgs_lat: Decimal
    wgs_long: Decimal
    county: str
    physical_type: str
    condition: str

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
        }


class TrigCountResponse(BaseModel):
    """Response model for trigpoint count queries."""

    trig_id: int
    count: int
