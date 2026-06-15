"""
Analytics Router

Usage analytics and statistics API endpoints.
All endpoints require authentication.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview, DailyStats, TopCharacterItem
from app.schemas.character import CharacterResponse
from app.services.analytics_service import get_daily_stats, get_overview, get_top_characters
from app.services.recommendation_service import get_recommendations

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get platform analytics overview with aggregate statistics."""
    return await get_overview(db)


@router.get("/daily")
async def daily_stats(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get daily statistics for the past N days (1-30, default 7)."""
    return await get_daily_stats(db, days=days)


@router.get("/top-characters")
async def top_characters(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the most frequently recognized characters."""
    return await get_top_characters(db, limit=limit)


@router.get("/recommendations")
async def recommendations(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get character recommendations based on user behavior."""
    chars = await get_recommendations(db, current_user.id, limit=limit)
    return [CharacterResponse.model_validate(c) for c in chars]
