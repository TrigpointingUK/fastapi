"""
Pydantic schemas for user endpoints with permission-based field filtering.
"""

import re
from datetime import date  # noqa: F401
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


class UserResponse(BaseModel):
    """Dynamic user response that adapts fields based on permissions."""

    # Always included
    id: int
    name: str
    firstname: str
    surname: str
    homepage: Optional[str] = Field(..., description="User homepage URL")
    about: str
    member_since: Optional[date] = Field(None, description="Date user joined")

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    total_logs: int
    total_trigs_logged: int


class UserBreakdown(BaseModel):
    # Breakdown by trig characteristics (distinct trigpoints only)
    by_current_use: Dict[str, int] = Field(
        {}, description="Trigpoints logged grouped by current use"
    )
    by_historic_use: Dict[str, int] = Field(
        {}, description="Trigpoints logged grouped by historic use"
    )
    by_physical_type: Dict[str, int] = Field(
        {}, description="Trigpoints logged grouped by physical type"
    )

    # Breakdown by log condition (all logs counted)
    by_condition: Dict[str, int] = Field(
        {}, description="All logs grouped by condition"
    )


class UserPrefs(BaseModel):
    status_max: int
    distance_ind: str
    public_ind: str
    online_map_type: str
    online_map_type2: str
    email: str
    email_valid: str = Field(
        ..., description="Email validation status (Y/N) - read-only"
    )


class UserUpdate(BaseModel):
    """Schema for updating user preferences and profile information."""

    # Profile fields that sync to Auth0
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=30,
        description="Username/nickname (syncs to Auth0)",
    )
    email: Optional[str] = Field(
        None, max_length=255, description="Email address (syncs to Auth0)"
    )

    # Profile fields (database only)
    firstname: Optional[str] = Field(
        None, max_length=30, description="First name (database only)"
    )
    surname: Optional[str] = Field(
        None, max_length=30, description="Surname (database only)"
    )
    homepage: Optional[str] = Field(
        None, max_length=255, description="User homepage URL"
    )
    about: Optional[str] = Field(None, description="About/description text")

    # Preference fields
    status_max: Optional[int] = Field(None, description="Status preference")
    distance_ind: Optional[str] = Field(
        None, pattern="^[KM]$", description="Distance units (K=km, M=miles)"
    )
    public_ind: Optional[str] = Field(
        None, pattern="^[YN]$", description="Public visibility (Y/N)"
    )
    online_map_type: Optional[str] = Field(
        None, max_length=10, description="Primary map type preference"
    )
    online_map_type2: Optional[str] = Field(
        None, max_length=10, description="Secondary map type preference"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        # Ban leading whitespace
        if v != v.lstrip():
            raise ValueError("Username cannot begin with whitespace")

        # Blacklist characters: @ and * (prevent SQL injection-like garbage)
        forbidden_chars = ["@", "*"]
        for char in forbidden_chars:
            if char in v:
                raise ValueError(f"Username cannot contain '{char}' character")

        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        # Basic email format validation
        # Pattern: local@domain with reasonable restrictions
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email address format")

        return v


class UserWithIncludes(UserResponse):
    stats: Optional[UserStats] = None
    breakdown: Optional[UserBreakdown] = None
    prefs: Optional[UserPrefs] = None


class Auth0UserInfo(BaseModel):
    """Auth0 user information from token without database lookup."""

    # Auth0 user details
    auth0_user_id: str = Field(..., description="Auth0 user ID")
    email: Optional[str] = Field(None, description="Email address from Auth0")
    nickname: Optional[str] = Field(None, description="Nickname from Auth0")
    name: Optional[str] = Field(None, description="Display name from Auth0")
    given_name: Optional[str] = Field(None, description="Given name from Auth0")
    family_name: Optional[str] = Field(None, description="Family name from Auth0")
    email_verified: Optional[bool] = Field(None, description="Email verified status")

    # Token metadata
    token_type: str = Field(..., description="Token type (auth0)")
    audience: Optional[list[str] | str] = Field(
        None, description="Token audience (string or list as provided in token)"
    )
    issuer: Optional[str] = Field(None, description="Token issuer")
    expires_at: Optional[int] = Field(None, description="Token expiration timestamp")
    scopes: Optional[list[str]] = Field(None, description="Scopes/permissions in token")

    # Database lookup status
    database_user_found: bool = Field(
        ..., description="Whether user was found in database"
    )
    database_user_id: Optional[int] = Field(
        None, description="Database user ID if found"
    )
    database_username: Optional[str] = Field(
        None, description="Database username if found"
    )
    database_email: Optional[str] = Field(None, description="Database email if found")


class UserCreate(BaseModel):
    """Schema for creating a new user from Auth0 webhook."""

    username: str = Field(
        ..., min_length=1, max_length=30, description="Username/nickname from Auth0"
    )
    email: str = Field(
        ..., min_length=1, max_length=255, description="Email address from Auth0"
    )
    auth0_user_id: str = Field(
        ..., min_length=1, max_length=50, description="Auth0 user ID"
    )


class UserCreateResponse(BaseModel):
    """Response schema for created user."""

    id: int = Field(..., description="Database user ID")
    name: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    auth0_user_id: str = Field(..., description="Auth0 user ID")

    class Config:
        from_attributes = True
