"""
Search Router

Global search endpoint across characters, posts, and users.
Uses SQL ILIKE for simple pattern matching — no full-text search.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.character import Character
from app.models.post import Post
from app.models.user import User

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", summary="Global search")
async def search(
    q: str = Query(..., min_length=1, description="Search query (min 1 character)"),
    type: str = Query(
        "all",
        pattern="^(all|character|post|user)$",
        description="Filter by type: all, character, post, or user",
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Results per page (max 100)"),
    db: AsyncSession = Depends(get_db),
):
    """Search across characters (name), posts (content), and users (username).

    Returns paginated results from each category plus a combined total count.
    The endpoint is public — no authentication required.
    """
    query_lower = f"%{q}%"
    characters = []
    posts = []
    users = []
    total = 0

    # ── Search Characters (by name) ─────────────────────────────────
    if type in ("all", "character"):
        count_q = select(func.count()).select_from(Character).where(
            Character.name.ilike(query_lower)
        )
        char_total = (await db.execute(count_q)).scalar() or 0
        if char_total > 0:
            char_query = (
                select(Character)
                .where(Character.name.ilike(query_lower))
                .offset((page - 1) * size)
                .limit(size)
            )
            char_results = (await db.execute(char_query)).scalars().all()
            characters = [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "image_url": c.image_url,
                }
                for c in char_results
            ]
        total += char_total

    # ── Search Posts (by content) ───────────────────────────────────
    if type in ("all", "post"):
        count_q = select(func.count()).select_from(Post).where(
            Post.content.ilike(query_lower)
        )
        post_total = (await db.execute(count_q)).scalar() or 0
        if post_total > 0:
            post_query = (
                select(Post)
                .where(Post.content.ilike(query_lower))
                .offset((page - 1) * size)
                .limit(size)
            )
            post_results = (await db.execute(post_query)).scalars().all()
            posts = [
                {
                    "id": p.id,
                    "content": p.content[:200],
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in post_results
            ]
        total += post_total

    # ── Search Users (by username) ──────────────────────────────────
    if type in ("all", "user"):
        count_q = select(func.count()).select_from(User).where(
            User.username.ilike(query_lower)
        )
        user_total = (await db.execute(count_q)).scalar() or 0
        if user_total > 0:
            user_query = (
                select(User)
                .where(User.username.ilike(query_lower))
                .offset((page - 1) * size)
                .limit(size)
            )
            user_results = (await db.execute(user_query)).scalars().all()
            users = [
                {
                    "id": u.id,
                    "username": u.username,
                    "avatar_url": u.avatar_url,
                }
                for u in user_results
            ]
        total += user_total

    return {
        "characters": characters,
        "posts": posts,
        "users": users,
        "total": total,
    }
