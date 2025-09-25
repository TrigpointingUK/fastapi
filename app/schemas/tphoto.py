"""
Pydantic schemas for tphoto endpoints.
"""

# from datetime import datetime  # Not currently used
from typing import Optional

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


class TPhotoCreate(BaseModel):
    # Creation fields (server and filenames are required for now; upload is out of scope)
    server_id: int
    type: str = Field(..., min_length=1, max_length=1)
    filename: str
    filesize: int
    height: int
    width: int
    icon_filename: str
    icon_filesize: int
    icon_height: int
    icon_width: int
    name: str
    text_desc: str = ""
    public_ind: str = Field("Y", min_length=1, max_length=1)
