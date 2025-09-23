"""
Pydantic schemas for user endpoints with permission-based field filtering.
"""

from datetime import date  # noqa: F401
from typing import Optional

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """Dynamic user response that adapts fields based on permissions."""

    # Always included
    id: int
    name: str
    firstname: str
    surname: str
    homepage: Optional[str] = Field(..., description="User homepage URL")
    about: str
    # Conditionally included private/public fields
    email: Optional[str] = None
    email_valid: Optional[str] = None
    admin_ind: Optional[str] = None
    public_ind: Optional[str] = None

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    total_logs: int
    total_trigs_logged: int


class UserPrefs(BaseModel):
    status_max: int
    distance_ind: str
    public_ind: str
    online_map_type: str
    online_map_type2: str


class UserWithIncludes(UserResponse):
    stats: Optional[UserStats] = None
    prefs: Optional[UserPrefs] = None


# Removed UserSummary; lists now use UserResponse


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


class Auth0UserInfo(BaseModel):
    """Auth0 user information from token without database lookup."""

    # Auth0 user details
    auth0_user_id: str = Field(..., description="Auth0 user ID")
    email: Optional[str] = Field(None, description="Email address from Auth0")
    username: Optional[str] = Field(None, description="Username from Auth0")
    nickname: Optional[str] = Field(None, description="Nickname from Auth0")
    name: Optional[str] = Field(None, description="Display name from Auth0")
    given_name: Optional[str] = Field(None, description="Given name from Auth0")
    family_name: Optional[str] = Field(None, description="Family name from Auth0")
    email_verified: Optional[bool] = Field(None, description="Email verified status")

    # Token metadata
    token_type: str = Field(..., description="Token type (auth0 or legacy)")
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
