"""
Auth Schemas

Pydantic models for authentication endpoints:
- User registration
- User login
- Token response
- User profile
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Request Models ────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username (3-50 chars, letters, digits, underscores)",
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 chars, must contain upper, lower, and digit)",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Ensure username only contains letters, digits, and underscores."""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username must only contain letters, digits, and underscores"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets complexity requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """Request body for user login."""

    username: str = Field(
        ...,
        description="Username or email address",
    )
    password: str = Field(
        ...,
        description="Account password",
    )


class UpdateProfileRequest(BaseModel):
    """Request body for updating user profile."""

    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar image URL")


# ── Response Models ───────────────────────────────────────────────────


class UserResponse(BaseModel):
    """Public user profile returned by the API."""

    id: int
    username: str
    email: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = ""
    role: str = "user"
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response after successful authentication."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(description="Token expiration time in seconds")
    user: UserResponse = Field(description="Authenticated user profile")
