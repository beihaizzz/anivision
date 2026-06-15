"""
Recommendation Service

Simple character recommendation engine for course-project level.
Uses popularity-based recommendations excluding characters the user
has already interacted with. A production system would use full
collaborative filtering or content-based approaches.
"""

from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.recognition_log import RecognitionLog


async def get_recommendations(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> List[Character]:
    """Get character recommendations for a user.

    Strategy:
    1. Find characters the user has already recognized (to exclude).
    2. If cold start (no history), return most popular characters.
    3. Otherwise, return popular characters excluding already-seen ones.

    This is a simple course-project implementation. A real system would
    use collaborative filtering based on user similarity or content-based
    features from character attributes.

    Args:
        db: Database session.
        user_id: The user to generate recommendations for.
        limit: Maximum number of recommendations (default 10).

    Returns:
        List of Character ORM instances.
    """
    # Get characters the user has already interacted with
    seen_char_ids_q = (
        select(RecognitionLog.top_character_id)
        .where(RecognitionLog.user_id == user_id)
        .where(RecognitionLog.top_character_id != None)
    )
    seen_results = await db.execute(seen_char_ids_q)
    seen_ids = set(row[0] for row in seen_results.all())

    # Cold start: user has no history → return popular characters
    if not seen_ids:
        pop_query = select(Character).limit(limit)
        chars = (await db.execute(pop_query)).scalars().all()
        return list(chars)

    # Recommend characters the user hasn't interacted with,
    # ordered by global recognition popularity
    rec_query = (
        select(Character)
        .join(RecognitionLog, RecognitionLog.top_character_id == Character.id)
        .where(~Character.id.in_(seen_ids))
        .group_by(Character.id)
        .order_by(func.count(RecognitionLog.id).desc())
        .limit(limit)
    )
    results = (await db.execute(rec_query)).scalars().all()
    return list(results)
