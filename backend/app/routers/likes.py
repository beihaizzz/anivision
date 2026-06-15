"""
Likes Router

Endpoints:
- POST /posts/{post_id}/like  — Toggle like on a post (requires auth)
- GET  /posts/{post_id}/likes — Get users who liked a post (public)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.user import User
from app.schemas.like import LikeToggleResponse
from app.services.like_service import get_post_likes, toggle_like

router = APIRouter(tags=["Likes"])


@router.post(
    "/posts/{post_id}/like",
    response_model=LikeToggleResponse,
    summary="Toggle like on a post",
)
async def like_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> LikeToggleResponse:
    """Toggle like on a post. If already liked, unlike; otherwise, like."""
    result = await toggle_like(db, current_user.id, post_id)
    return LikeToggleResponse(**result)


@router.get(
    "/posts/{post_id}/likes",
    summary="Get users who liked a post",
)
async def get_post_likes_endpoint(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get list of users who liked a post. Public endpoint (no auth required)."""
    return await get_post_likes(db, post_id)
