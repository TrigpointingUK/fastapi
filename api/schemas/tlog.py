"""
Pydantic schemas for TLog (logs) endpoints.
"""

from datetime import date, time
from typing import Optional

from pydantic import BaseModel, Field

from api.schemas.tphoto import TPhotoResponse


class TLogBase(BaseModel):
    id: int
    trig_id: int
    user_id: int
    date: date
    time: time
    osgb_eastings: int
    osgb_northings: int
    osgb_gridref: str = Field(..., max_length=14)
    fb_number: str = Field(..., max_length=10)
    condition: str = Field(..., min_length=1, max_length=1)
    comment: str
    score: int
    source: str = Field(..., min_length=1, max_length=1)

    class Config:
        from_attributes = True


class TLogResponse(TLogBase):
    pass


class TLogWithIncludes(TLogBase):
    # Optional includes for expanded responses
    photos: Optional[list[TPhotoResponse]] = None


class TLogCreate(BaseModel):
    # user_id is set from current user on POST endpoints
    date: date
    time: time
    osgb_eastings: int
    osgb_northings: int
    osgb_gridref: str = Field(..., max_length=14)
    fb_number: str = Field("", max_length=10)
    condition: str = Field(..., min_length=1, max_length=1)
    comment: str = ""
    score: int = 0
    source: str = Field("W", min_length=1, max_length=1)


class TLogUpdate(BaseModel):
    # Partial updates only
    date: Optional[date] = None
    time: Optional[time] = None
    osgb_eastings: Optional[int] = None
    osgb_northings: Optional[int] = None
    osgb_gridref: Optional[str] = Field(None, max_length=14)
    fb_number: Optional[str] = Field(None, max_length=10)
    condition: Optional[str] = Field(None, min_length=1, max_length=1)
    comment: Optional[str] = None
    score: Optional[int] = None
    source: Optional[str] = Field(None, min_length=1, max_length=1)
