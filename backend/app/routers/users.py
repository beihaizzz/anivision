"""
Users Router

Public user profile endpoints (no auth required):
- GET /api/users/{user_id}        — Get a user's public profile
- GET /api/users/{user_id}/posts  — Get a user's posts (paginated)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.post import PostListResponse
from app.schemas.user import UserProfileResponse
from app.services.user_service import get_user_posts, get_user_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Get user public profile",
)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """
    Retrieve a user's public profile.

    Returns profile fields plus aggregate counts
    (followers, following, posts).  Public endpoint.
    """
    return await get_user_profile(db, user_id)


@router.get(
    "/{user_id}/posts",
    response_model=PostListResponse,
    summary="Get user's posts (paginated)",
)
async def get_user_posts_endpoint(
    user_id: int,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> PostListResponse:
    """
    Retrieve paginated posts authored by a specific user.

    Results are ordered newest-first.
    """
    return await get_user_posts(db, user_id, page=page, size=size)
