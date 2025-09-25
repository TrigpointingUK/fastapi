"""
Pydantic schemas for tphoto endpoints.
"""

# from datetime import datetime  # Not currently used
from typing import List, Optional

from pydantic import BaseModel, Field


class TPhotoBase(BaseModel):
    id: int
    tlog_id: int
    user_id: int
    type: str = Field(..., min_length=1, max_length=1)
    filesize: int
    height: int
    width: int
    icon_filesize: int
    icon_height: int
    icon_width: int
    name: str
    text_desc: str
    public_ind: str = Field(..., min_length=1, max_length=1)
    # Derived fields
    photo_url: str
    icon_url: str

    class Config:
        from_attributes = True


class TPhotoResponse(TPhotoBase):
    pass


class TPhotoUpdate(BaseModel):
    # Allow updating metadata fields only (no IDs or sizes)
    name: Optional[str] = None
    text_desc: Optional[str] = None
    public_ind: Optional[str] = Field(None, min_length=1, max_length=1)


class TPhotoEvaluationResponse(BaseModel):
    photo_id: int
    photo_accessible: bool
    icon_accessible: bool
    photo_dimension_match: bool
    icon_dimension_match: bool
    photo_width_actual: Optional[int] = None
    photo_height_actual: Optional[int] = None
    icon_width_actual: Optional[int] = None
    icon_height_actual: Optional[int] = None
    orientation_analysis: Optional[dict] = None
    content_moderation: Optional[dict] = None
    errors: List[str] = []
