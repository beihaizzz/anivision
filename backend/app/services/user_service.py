"""
User Profile Service

Business logic for user profiles:
- Profile retrieval with aggregated stats (followers, following, posts)
- Paginated post listing for a user
- Profile updates (bio, avatar_url)
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.follow import Follow
from app.models.post import Post
from app.models.user import User
from app.schemas.auth import UpdateProfileRequest
from app.schemas.common import PaginatedResponse
from app.schemas.post import PostResponse
from app.schemas.user import UserProfileResponse


async def get_user_profile(
    db: AsyncSession,
    user_id: int,
) -> UserProfileResponse:
    """
    Retrieve a user's public profile with aggregated stats.

    Gathers follower count, following count, and post count from
    the database to populate the profile response.

    Args:
        db: Database session.
        user_id: ID of the user to look up.

    Returns:
        UserProfileResponse with profile fields + aggregate counts.

    Raises:
        HTTPException(404): If the user does not exist.
    """
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # ── Aggregate Counts ──────────────────────────────────────────────
    follower_count = (
        await db.execute(
            select(func.count()).select_from(Follow).where(Follow.followed_id == user_id)
        )
    ).scalar() or 0

    following_count = (
        await db.execute(
            select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
        )
    ).scalar() or 0

    post_count = (
        await db.execute(
            select(func.count()).select_from(Post).where(Post.user_id == user_id)
        )
    ).scalar() or 0

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url,
        bio=user.bio,
        role=user.role,
        created_at=user.created_at,
        follower_count=follower_count,
        following_count=following_count,
        post_count=post_count,
    )


async def get_user_posts(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[PostResponse]:
    """
    Retrieve paginated posts authored by a specific user.

    Verifies the user exists before querying posts.  Posts are
    ordered by creation date (newest first).

    Args:
        db: Database session.
        user_id: ID of the user whose posts to fetch.
        page: Page number (1-indexed).
        size: Number of posts per page.

    Returns:
        PaginatedResponse containing PostResponse items.

    Raises:
        HTTPException(404): If the user does not exist.
    """
    # Verify user exists
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Total post count
    total = (
        await db.execute(
            select(func.count()).select_from(Post).where(Post.user_id == user_id)
        )
    ).scalar() or 0

    # Fetch paginated posts with user relationship loaded
    query = (
        select(Post)
        .options(selectinload(Post.user))
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    posts = (await db.execute(query)).scalars().all()
    items = [PostResponse.model_validate(p) for p in posts]

    return PaginatedResponse[PostResponse](
        items=items,
        total=total,
        page=page,
        size=size,
    )


async def update_profile(
    db: AsyncSession,
    user_id: int,
    profile_data: UpdateProfileRequest,
) -> UserProfileResponse:
    """
    Update a user's profile fields (bio / avatar_url).

    Only non-None fields from ``profile_data`` are applied, allowing
    partial updates.  After saving, the full profile with aggregated
    counts is returned.

    Args:
        db: Database session.
        user_id: ID of the user to update.
        profile_data: Request body with optional bio / avatar_url.

    Returns:
        Updated UserProfileResponse with fresh aggregate counts.

    Raises:
        HTTPException(404): If the user does not exist.
    """
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Apply partial updates
    if profile_data.bio is not None:
        user.bio = profile_data.bio
    if profile_data.avatar_url is not None:
        user.avatar_url = profile_data.avatar_url

    await db.flush()
    await db.refresh(user)

    # ── Aggregate Counts ──────────────────────────────────────────────
    follower_count = (
        await db.execute(
            select(func.count()).select_from(Follow).where(Follow.followed_id == user_id)
        )
    ).scalar() or 0

    following_count = (
        await db.execute(
            select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
        )
    ).scalar() or 0

    post_count = (
        await db.execute(
            select(func.count()).select_from(Post).where(Post.user_id == user_id)
        )
    ).scalar() or 0

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url,
        bio=user.bio,
        role=user.role,
        created_at=user.created_at,
        follower_count=follower_count,
        following_count=following_count,
        post_count=post_count,
    )
