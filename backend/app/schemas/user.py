"""
User Schemas

Public profile models exposed by the API.  These intentionally omit
sensitive fields such as email and password_hash.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    """Detailed public user profile returned by profile / user endpoints."""

    id: int = Field(description="User ID")
    username: str = Field(description="Unique username")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, description="Short biography")
    role: str = Field(default="user", description="User role (user / creator / admin)")
    created_at: datetime = Field(description="Account creation timestamp")
    follower_count: int = Field(default=0, description="Number of followers")
    following_count: int = Field(default=0, description="Number of users followed")
    post_count: int = Field(default=0, description="Number of posts created")

    model_config = {"from_attributes": True}
