"""
Post Service

Business logic for community post CRUD operations:
- Create, retrieve, list, update, and delete posts
- Authorization checks (owner vs admin)
"""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.post import Post
from app.schemas.common import PaginatedResponse
from app.schemas.post import PostCreate, PostResponse, PostUpdateRequest


async def create_post(db: AsyncSession, user_id: int, data: PostCreate) -> Post:
    """
    Create a new community post.

    Args:
        db: Database session.
        user_id: ID of the authenticated user creating the post.
        data: Validated post creation data.

    Returns:
        The newly created Post instance with user relationship loaded.
    """
    post = Post(
        user_id=user_id,
        content=data.content,
        image_urls=data.image_urls or [],
        tags=data.tags or [],
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)

    # Eager load user for response serialization
    result = await db.execute(
        select(Post).options(selectinload(Post.user)).where(Post.id == post.id)
    )
    return result.scalar_one()


async def get_post(db: AsyncSession, post_id: int) -> Post:
    """
    Retrieve a single post by ID with user relationship loaded.

    Args:
        db: Database session.
        post_id: Post primary key.

    Returns:
        The Post instance.

    Raises:
        HTTPException(404): If the post does not exist.
    """
    query = (
        select(Post)
        .options(selectinload(Post.user))
        .where(Post.id == post_id)
    )
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return post


async def list_posts(
    db: AsyncSession, page: int = 1, size: int = 20
) -> PaginatedResponse[PostResponse]:
    """
    List posts with pagination, newest first.

    Args:
        db: Database session.
        page: Page number (1-indexed).
        size: Items per page.

    Returns:
        PaginatedResponse containing PostResponse items.
    """
    # Count total posts
    count_q = select(func.count()).select_from(Post)
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch page with user relationship
    query = (
        select(Post)
        .options(selectinload(Post.user))
        .order_by(Post.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    posts = (await db.execute(query)).scalars().all()
    items = [PostResponse.model_validate(p) for p in posts]

    return PaginatedResponse[PostResponse](
        items=items, total=total, page=page, size=size
    )


async def update_post(
    db: AsyncSession,
    post_id: int,
    user_id: int,
    data: PostUpdateRequest,
    user_role: str = "user",
) -> Post:
    """
    Update a post (owner or admin only).

    Args:
        db: Database session.
        post_id: Post primary key.
        user_id: ID of the requesting user.
        data: Partial update data (all fields optional).
        user_role: Role of the requesting user (default "user").

    Returns:
        The updated Post instance.

    Raises:
        HTTPException(403): If the user is not the owner and not an admin.
    """
    post = await get_post(db, post_id)

    if post.user_id != user_id and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this post",
        )

    if data.content is not None:
        post.content = data.content
    if data.tags is not None:
        post.tags = data.tags

    await db.flush()
    await db.refresh(post)
    return post


async def delete_post(
    db: AsyncSession,
    post_id: int,
    user_id: int,
    user_role: str = "user",
) -> None:
    """
    Delete a post (owner or admin only).

    Args:
        db: Database session.
        post_id: Post primary key.
        user_id: ID of the requesting user.
        user_role: Role of the requesting user (default "user").

    Raises:
        HTTPException(403): If the user is not the owner and not an admin.
    """
    post = await get_post(db, post_id)

    if post.user_id != user_id and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post",
        )

    db.delete(post)
    await db.flush()
