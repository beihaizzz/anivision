"""
Analytics Schemas (Stub)

Will be fully implemented in Phase 4 (analytics features).
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class AnalyticsOverview(BaseModel):
    """High-level platform statistics for the dashboard."""

    total_users: int = Field(description="Total registered users")
    total_posts: int = Field(description="Total posts created")
    total_recognitions: int = Field(description="Total character recognitions performed")
    total_likes: int = Field(description="Total likes across all posts")
    active_users_today: int = Field(description="Unique active users in the last 24 hours")


class DailyStats(BaseModel):
    """Per-day statistics for trend charts."""

    date: datetime = Field(description="Date of the statistics")
    new_users: int = Field(default=0, description="New users registered on this date")
    new_posts: int = Field(default=0, description="New posts created on this date")
    recognitions: int = Field(default=0, description="Recognitions performed on this date")


class TopCharacterItem(BaseModel):
    """A single entry in the top-recognised characters list."""

    character_id: int = Field(description="Character ID")
    character_name: str = Field(description="Character display name")
    recognition_count: int = Field(description="Total recognition count")
