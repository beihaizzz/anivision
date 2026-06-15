"""
Posts & Comments Router

Community API endpoints:
- GET    /api/posts                         — list posts (public)
- POST   /api/posts                         — create post (auth)
- GET    /api/posts/{post_id}               — get post (public)
- PUT    /api/posts/{post_id}               — update post (owner/admin)
- DELETE /api/posts/{post_id}               — delete post (owner/admin)
- GET    /api/posts/{post_id}/comments      — list comments (public)
- POST   /api/posts/{post_id}/comments      — create comment (auth)
- DELETE /api/posts/comments/{comment_id}   — delete comment (owner/admin)
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.user import User
from app.schemas.post import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    PostCreate,
    PostListResponse,
    PostResponse,
    PostUpdateRequest,
)
from app.services.comment_service import create_comment, delete_comment, get_comments
from app.services.post_service import create_post, delete_post, get_post, list_posts, update_post

router = APIRouter(prefix="/posts", tags=["Posts"])


# ══════════════════════════════════════════════════════════════════════════
# Post Endpoints
# ══════════════════════════════════════════════════════════════════════════


@router.get("", response_model=PostListResponse)
async def get_posts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List posts with pagination, newest first (public, no auth)."""
    return await list_posts(db, page=page, size=size)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post_endpoint(
    data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new community post (auth required)."""
    post = await create_post(db, current_user.id, data)
    return PostResponse.model_validate(post)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post_by_id(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single post by ID (public, no auth)."""
    post = await get_post(db, post_id)
    return PostResponse.model_validate(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post_endpoint(
    post_id: int,
    data: PostUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a post (owner or admin only)."""
    post = await update_post(db, post_id, current_user.id, data, current_user.role)
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_endpoint(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a post (owner or admin only)."""
    await delete_post(db, post_id, current_user.id, current_user.role)


# ══════════════════════════════════════════════════════════════════════════
# Comment Endpoints
# ══════════════════════════════════════════════════════════════════════════


@router.get("/{post_id}/comments", response_model=CommentListResponse)
async def get_comments_by_post(
    post_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List paginated comments for a post (public, no auth)."""
    return await get_comments(db, post_id, page=page, size=size)


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment_endpoint(
    post_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a comment (top-level or reply) on a post (auth required)."""
    comment = await create_comment(db, post_id, current_user.id, data)
    return CommentResponse.model_validate(comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_endpoint(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a comment (owner or admin only)."""
    await delete_comment(db, comment_id, current_user.id, current_user.role)
