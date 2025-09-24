"""
Pydantic schemas for trig endpoints.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TrigMinimal(BaseModel):
    """Minimal trig response for /trig/{id}."""

    id: int = Field(..., description="Trigpoint ID")
    waypoint: str = Field(..., description="Waypoint code (e.g., TP0001)")
    name: str = Field(..., description="Trigpoint name")

    # Public basic classification/identity
    status_name: Optional[str] = Field(
        None, description="Human-readable status derived from status_id"
    )
    physical_type: str = Field(..., description="Physical type (e.g., Pillar)")
    condition: str = Field(..., description="Condition code")

    # Coordinates and grid ref
    wgs_lat: Decimal = Field(..., description="WGS84 latitude")
    wgs_long: Decimal = Field(..., description="WGS84 longitude")
    osgb_gridref: str = Field(..., description="OSGB grid reference")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
        }


class TrigDetails(BaseModel):
    """Details sub-object for /trig/{id}/details or include=details."""

    current_use: str
    historic_use: str
    wgs_height: int
    postcode: str = Field(..., validation_alias="postcode6")
    county: str
    town: str
    fb_number: str
    stn_number: str
    stn_number_active: Optional[str] = None
    stn_number_passive: Optional[str] = None
    stn_number_osgb36: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
        }


# class TrigSummary(BaseModel):
#     """Simplified trig summary for list endpoints (future use)."""

#     id: int
#     waypoint: str
#     name: str
#     wgs_lat: Decimal
#     wgs_long: Decimal
#     county: str
#     physical_type: str
#     condition: str

#     class Config:
#         from_attributes = True
#         json_encoders = {
#             Decimal: str,
#         }


class TrigStats(BaseModel):
    """Statistics for a trigpoint."""

    logged_first: date
    logged_last: date
    logged_count: int
    found_last: date
    found_count: int
    photo_count: int
    score_mean: Decimal
    score_baysian: Decimal

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat() if v else None,
        }


class TrigWithIncludes(TrigMinimal):
    """Envelope for minimal trig with optional includes."""

    details: Optional[TrigDetails] = None
    stats: Optional[TrigStats] = None


class TrigCountResponse(BaseModel):
    """Response model for trigpoint count queries."""

    trig_id: int
    count: int
