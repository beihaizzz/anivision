"""
Analytics Service

Business logic for platform analytics:
- get_overview: Aggregate platform statistics
- get_daily_stats: Per-day trend data for charts
- get_top_characters: Most frequently recognized characters
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior_log import BehaviorLog
from app.models.character import Character
from app.models.like import Like
from app.models.post import Post
from app.models.recognition_log import RecognitionLog
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview, DailyStats, TopCharacterItem


async def get_overview(db: AsyncSession) -> AnalyticsOverview:
    """Get platform analytics overview with aggregate counts.

    Returns five key metrics: total users, posts, recognitions,
    likes, and unique active users today.
    """
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    total_posts = (await db.execute(select(func.count()).select_from(Post))).scalar() or 0
    total_recognitions = (await db.execute(select(func.count()).select_from(RecognitionLog))).scalar() or 0
    total_likes = (await db.execute(select(func.count()).select_from(Like))).scalar() or 0

    # Active users today: users with behavior_logs from today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    active_users_today = (await db.execute(
        select(func.count(func.distinct(BehaviorLog.user_id)))
        .where(BehaviorLog.created_at >= today_start)
        .where(BehaviorLog.user_id != None)
    )).scalar() or 0

    return AnalyticsOverview(
        total_users=total_users,
        total_posts=total_posts,
        total_recognitions=total_recognitions,
        total_likes=total_likes,
        active_users_today=active_users_today,
    )


async def get_daily_stats(db: AsyncSession, days: int = 7) -> List[DailyStats]:
    """Get daily statistics for the past N days.

    Returns per-day new user, new post, and recognition counts
    for charting trends over time.

    Args:
        db: Database session.
        days: Number of past days to include (default 7).

    Returns:
        List of DailyStats, ordered from today backwards.
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    stats = []

    for day_offset in range(days):
        day_start = today - timedelta(days=day_offset)
        day_end = day_start + timedelta(days=1)

        new_users = (await db.execute(
            select(func.count()).select_from(User)
            .where(User.created_at >= day_start)
            .where(User.created_at < day_end)
        )).scalar() or 0

        new_posts = (await db.execute(
            select(func.count()).select_from(Post)
            .where(Post.created_at >= day_start)
            .where(Post.created_at < day_end)
        )).scalar() or 0

        recognitions = (await db.execute(
            select(func.count()).select_from(RecognitionLog)
            .where(RecognitionLog.created_at >= day_start)
            .where(RecognitionLog.created_at < day_end)
        )).scalar() or 0

        stats.append(DailyStats(
            date=day_start,
            new_users=new_users,
            new_posts=new_posts,
            recognitions=recognitions,
        ))

    return stats


async def get_top_characters(db: AsyncSession, limit: int = 10) -> List[TopCharacterItem]:
    """Get the most frequently recognized characters.

    Groups recognition logs by the top-matched character and ranks
    by recognition count.

    Args:
        db: Database session.
        limit: Maximum number of characters to return (default 10).

    Returns:
        List of TopCharacterItem sorted descending by recognition_count.
    """
    # Group recognition_logs by top_character_id and count
    query = (
        select(
            RecognitionLog.top_character_id,
            func.count(RecognitionLog.id).label("recognition_count"),
        )
        .where(RecognitionLog.top_character_id != None)
        .group_by(RecognitionLog.top_character_id)
        .order_by(func.count(RecognitionLog.id).desc())
        .limit(limit)
    )
    results = (await db.execute(query)).all()

    items = []
    for row in results:
        character_id, count = row
        # Get character name
        char = (await db.execute(
            select(Character).where(Character.id == character_id)
        )).scalar_one_or_none()
        character_name = char.name if char else f"Character #{character_id}"
        items.append(TopCharacterItem(
            character_id=character_id,
            character_name=character_name,
            recognition_count=count,
        ))

    return items
