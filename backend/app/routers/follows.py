"""
Follows Router

Endpoints:
- POST /users/{user_id}/follow    — Toggle follow on a user (requires auth)
- GET  /users/{user_id}/followers — Get followers of a user (public)
- GET  /users/{user_id}/following  — Get users that a user follows (public)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.user import User
from app.schemas.follow import (
    FollowToggleResponse,
    FollowerListResponse,
    FollowingListResponse,
)
from app.services.follow_service import (
    get_user_followers,
    get_user_following,
    toggle_follow,
)

router = APIRouter(tags=["Follows"])


@router.post(
    "/users/{user_id}/follow",
    response_model=FollowToggleResponse,
    summary="Toggle follow on a user",
)
async def follow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FollowToggleResponse:
    """Toggle follow on a user. If already following, unfollow; otherwise, follow."""
    result = await toggle_follow(db, current_user.id, user_id)
    return FollowToggleResponse(**result)


@router.get(
    "/users/{user_id}/followers",
    response_model=FollowerListResponse,
    summary="Get followers of a user",
)
async def get_followers(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> FollowerListResponse:
    """Get paginated list of followers for a user. Public endpoint."""
    return await get_user_followers(db, user_id, page=page, size=size)


@router.get(
    "/users/{user_id}/following",
    response_model=FollowingListResponse,
    summary="Get users that a user follows",
)
async def get_following(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> FollowingListResponse:
    """Get paginated list of users a user follows. Public endpoint."""
    return await get_user_following(db, user_id, page=page, size=size)
