"""
Follow Schemas

Request and response models for follow/unfollow operations.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.schemas.post import UserBrief


class FollowResponse(BaseModel):
    """Response model representing a single follow record."""

    id: int = Field(description="Follow record ID")
    follower_id: int = Field(description="ID of the user who followed")
    followed_id: int = Field(description="ID of the user being followed")
    created_at: datetime = Field(description="When the follow was created")

    model_config = {"from_attributes": True}


class FollowToggleResponse(BaseModel):
    """Response model after toggling a follow on a user."""

    following: bool = Field(description="Whether the user is now being followed")


class FollowerListResponse(BaseModel):
    """Paginated list of followers (users who follow the target)."""

    items: List[UserBrief] = Field(description="List of followers for the current page")
    total: int = Field(description="Total number of followers")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")


class FollowingListResponse(BaseModel):
    """Paginated list of users the target is following."""

    items: List[UserBrief] = Field(description="List of followed users for the current page")
    total: int = Field(description="Total number of followed users")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")
