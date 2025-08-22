"""
Pydantic schemas for user endpoints with permission-based field filtering.
"""
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

    class Config:
        from_attributes = True


class UserPrivate(UserBase):
    """Private user schema - includes all fields for authenticated users."""

    email: str = Field(..., description="Email address")
    email_valid: str = Field(..., description="Email validation status (Y/N)")
    admin_ind: str = Field(..., description="Admin status (Y/N)")
    public_ind: str = Field(..., description="Public profile status (Y/N)")

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


class UserEmail(BaseModel):
    """User email response for JWT-protected endpoints."""

    user_id: int  # Keep as user_id for API compatibility
    email: str
