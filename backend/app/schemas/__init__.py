"""
Pydantic Schemas Package

Request and response validation models for the API.
"""

from app.schemas.analytics import AnalyticsOverview, DailyStats, TopCharacterItem
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.schemas.common import PaginationParams, PaginatedResponse
from app.schemas.follow import (
    FollowerListResponse,
    FollowingListResponse,
    FollowResponse,
    FollowToggleResponse,
)
from app.schemas.like import LikeResponse, LikeToggleResponse
from app.schemas.post import UserBrief
from app.schemas.user import UserProfileResponse

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "UserProfileResponse",
    "UserBrief",
    "PaginationParams",
    "PaginatedResponse",
    "LikeResponse",
    "LikeToggleResponse",
    "FollowResponse",
    "FollowToggleResponse",
    "FollowerListResponse",
    "FollowingListResponse",
    "AnalyticsOverview",
    "DailyStats",
    "TopCharacterItem",
]
