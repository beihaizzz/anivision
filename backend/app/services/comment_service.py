"""
Comment Service

Business logic for threaded comment operations:
- Create top-level and nested reply comments
- List comments with their replies
- Delete comments with authorization checks
"""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import Comment
from app.models.post import Post
from app.schemas.common import PaginatedResponse
from app.schemas.post import CommentCreate, CommentResponse


async def create_comment(
    db: AsyncSession, post_id: int, user_id: int, data: CommentCreate
) -> Comment:
    """
    Create a comment (top-level or reply) on a post.

    Enforces a maximum nesting depth of 2: a reply is allowed, but
    replying to a reply (grandchild) is rejected.

    Args:
        db: Database session.
        post_id: Target post primary key.
        user_id: Comment author ID.
        data: Validated comment creation data.

    Returns:
        The newly created Comment instance.

    Raises:
        HTTPException(404): If post or parent comment not found.
        HTTPException(400): If nesting exceeds maximum depth of 2.
    """
    # Verify post exists
    post_query = select(Post).where(Post.id == post_id)
    post = (await db.execute(post_query)).scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # Check nesting depth if this is a reply
    if data.parent_id is not None:
        parent = await db.execute(
            select(Comment).where(Comment.id == data.parent_id)
        )
        parent_comment = parent.scalar_one_or_none()
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found",
            )
        if parent_comment.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment nesting exceeds maximum depth of 2",
            )

    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        content=data.content,
        parent_id=data.parent_id,
    )
    db.add(comment)

    # Increment post comment count
    post.comment_count = (post.comment_count or 0) + 1

    await db.flush()
    await db.refresh(comment)
    return comment


async def get_comments(
    db: AsyncSession,
    post_id: int,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[CommentResponse]:
    """
    Retrieve paginated top-level comments with their nested replies.

    Args:
        db: Database session.
        post_id: Target post primary key.
        page: Page number (1-indexed).
        size: Items per page.

    Returns:
        PaginatedResponse containing CommentResponse items with replies.
    """
    # Count top-level comments only
    total_q = (
        select(func.count())
        .select_from(Comment)
        .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
    )
    total = (await db.execute(total_q)).scalar() or 0

    # Fetch top-level comments for this page
    query = (
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    top_comments = (await db.execute(query)).scalars().all()

    # Load replies for each top-level comment
    items = []
    for c in top_comments:
        replies_q = (
            select(Comment)
            .options(selectinload(Comment.user))
            .where(Comment.parent_id == c.id)
            .order_by(Comment.created_at.asc())
        )
        replies = (await db.execute(replies_q)).scalars().all()

        cr = CommentResponse.model_validate(c)
        cr.replies = [CommentResponse.model_validate(r) for r in replies]
        items.append(cr)

    return PaginatedResponse[CommentResponse](
        items=items, total=total, page=page, size=size
    )


async def delete_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
    user_role: str = "user",
) -> None:
    """
    Delete a comment (owner or admin only).

    Updates the parent post's comment_count accordingly.

    Args:
        db: Database session.
        comment_id: Comment primary key.
        user_id: ID of the requesting user.
        user_role: Role of the requesting user (default "user").

    Raises:
        HTTPException(404): If comment does not exist.
        HTTPException(403): If user is not the owner and not an admin.
    """
    comment = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = comment.scalar_one_or_none()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if comment.user_id != user_id and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment",
        )

    # Decrement post comment count
    post = await db.execute(select(Post).where(Post.id == comment.post_id))
    post = post.scalar_one()
    post.comment_count = max(0, (post.comment_count or 0) - 1)

    db.delete(comment)
    await db.flush()
