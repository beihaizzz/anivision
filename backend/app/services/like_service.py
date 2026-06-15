"""
Like Service

Business logic for toggling likes on posts and retrieving likers.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.schemas.post import UserBrief


async def toggle_like(
    db: AsyncSession,
    user_id: int,
    post_id: int,
) -> dict:
    """
    Toggle a like on a post.

    If the user has already liked the post, the like is removed (unlike).
    Otherwise, a new like is created.

    Args:
        db: Database session.
        user_id: ID of the user performing the action.
        post_id: ID of the post to like/unlike.

    Returns:
        dict with keys ``liked`` (bool) and ``like_count`` (int).

    Raises:
        HTTPException(404): If the post does not exist.
        HTTPException(400): If the user tries to like their own post.
    """
    # Check post exists
    post = (
        await db.execute(select(Post).where(Post.id == post_id))
    ).scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # Self-like guard
    if post.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot like your own post",
        )

    # Check for existing like
    existing = (
        await db.execute(
            select(Like).where(
                Like.user_id == user_id,
                Like.post_id == post_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        post.like_count = max(0, (post.like_count or 0) - 1)
        liked = False
    else:
        db.add(Like(user_id=user_id, post_id=post_id))
        post.like_count = (post.like_count or 0) + 1
        liked = True

    await db.flush()
    return {"liked": liked, "like_count": post.like_count}


async def get_post_likes(
    db: AsyncSession,
    post_id: int,
) -> list[UserBrief]:
    """
    Retrieve the list of users who liked a post.

    Args:
        db: Database session.
        post_id: ID of the post.

    Returns:
        A list of UserBrief objects representing users who liked the post.
    """
    result = await db.execute(
        select(User)
        .join(Like, Like.user_id == User.id)
        .where(Like.post_id == post_id)
    )
    users = result.scalars().all()
    return [
        UserBrief(
            id=u.id,
            username=u.username,
            avatar_url=u.avatar_url,
        )
        for u in users
    ]
