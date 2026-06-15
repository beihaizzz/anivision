"""
Follow Service

Business logic for toggling follow relationships and retrieving
follower/following lists.
"""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import Follow
from app.models.user import User
from app.schemas.follow import FollowerListResponse, FollowingListResponse
from app.schemas.post import UserBrief


async def toggle_follow(
    db: AsyncSession,
    follower_id: int,
    followed_id: int,
) -> dict:
    """
    Toggle a follow relationship between two users.

    If the follower already follows the target user, the follow is removed
    (unfollow). Otherwise, a new follow relationship is created.

    Args:
        db: Database session.
        follower_id: ID of the user who is following.
        followed_id: ID of the user to be followed.

    Returns:
        dict with key ``following`` (bool).

    Raises:
        HTTPException(400): If a user tries to follow themselves.
        HTTPException(404): If the target user does not exist.
    """
    # Self-follow guard
    if follower_id == followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself",
        )

    # Check target user exists
    followed_user = (
        await db.execute(select(User).where(User.id == followed_id))
    ).scalar_one_or_none()
    if not followed_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check for existing follow relationship
    existing = (
        await db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.followed_id == followed_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        following = False
    else:
        db.add(Follow(follower_id=follower_id, followed_id=followed_id))
        following = True

    await db.flush()
    return {"following": following}


async def get_user_followers(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    size: int = 20,
) -> FollowerListResponse:
    """
    Get a paginated list of followers for a user.

    Args:
        db: Database session.
        user_id: ID of the user whose followers to retrieve.
        page: Page number (1-indexed, default 1).
        size: Number of items per page (default 20).

    Returns:
        A FollowerListResponse containing the paginated follower list.
    """
    # Total count
    total = (
        await db.execute(
            select(func.count()).select_from(Follow).where(
                Follow.followed_id == user_id
            )
        )
    ).scalar() or 0

    # Paginated list
    result = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.followed_id == user_id)
        .offset((page - 1) * size)
        .limit(size)
    )
    users = result.scalars().all()

    return FollowerListResponse(
        items=[
            UserBrief(id=u.id, username=u.username, avatar_url=u.avatar_url)
            for u in users
        ],
        total=total,
        page=page,
        size=size,
    )


async def get_user_following(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    size: int = 20,
) -> FollowingListResponse:
    """
    Get a paginated list of users that the given user is following.

    Args:
        db: Database session.
        user_id: ID of the user whose following list to retrieve.
        page: Page number (1-indexed, default 1).
        size: Number of items per page (default 20).

    Returns:
        A FollowingListResponse containing the paginated following list.
    """
    # Total count
    total = (
        await db.execute(
            select(func.count()).select_from(Follow).where(
                Follow.follower_id == user_id
            )
        )
    ).scalar() or 0

    # Paginated list
    result = await db.execute(
        select(User)
        .join(Follow, Follow.followed_id == User.id)
        .where(Follow.follower_id == user_id)
        .offset((page - 1) * size)
        .limit(size)
    )
    users = result.scalars().all()

    return FollowingListResponse(
        items=[
            UserBrief(id=u.id, username=u.username, avatar_url=u.avatar_url)
            for u in users
        ],
        total=total,
        page=page,
        size=size,
    )
