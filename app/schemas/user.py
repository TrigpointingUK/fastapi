"""
Pydantic schemas for request/response models.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str


class UserInDB(UserBase):
    """Schema for user as stored in database."""
    user_id: int
    admin_ind: str
    password_hash: str

    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    """Schema for user in responses."""
    user_id: int
    admin_ind: str

    model_config = ConfigDict(from_attributes=True)


class UserEmail(BaseModel):
    """Schema for user email response."""
    user_id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TrigCountResponse(BaseModel):
    """Schema for trig count response."""
    trig_id: int
    count: int


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[int] = None
