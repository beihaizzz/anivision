"""
Like Schemas

Request and response models for like/unlike operations.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class LikeResponse(BaseModel):
    """Response model representing a single like record."""

    id: int = Field(description="Like record ID")
    user_id: int = Field(description="ID of the user who liked")
    post_id: int = Field(description="ID of the liked post")
    created_at: datetime = Field(description="When the like was created")

    model_config = {"from_attributes": True}


class LikeToggleResponse(BaseModel):
    """Response model after toggling a like on a post."""

    liked: bool = Field(description="Whether the post is now liked")
    like_count: int = Field(description="Total like count for the post")
