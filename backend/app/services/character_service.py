"""
Character & Work Service

Business logic for character and work queries:
- Single entity retrieval with eager-loaded relationships
- Paginated listing with optional filters
- ILIKE search for case-insensitive name matching
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.character import Character
from app.models.work import Work
from app.schemas.character import CharacterResponse, WorkResponse
from app.schemas.common import PaginatedResponse


async def get_character(db: AsyncSession, character_id: int) -> Character:
    """
    Get a single character by ID with work info eagerly loaded.

    Args:
        db: Database session.
        character_id: Character primary key.

    Returns:
        The Character ORM instance with work relationship populated.

    Raises:
        HTTPException(404): If no character with the given ID exists.
    """
    query = (
        select(Character)
        .options(selectinload(Character.work))
        .where(Character.id == character_id)
    )
    result = await db.execute(query)
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )
    return character


async def list_characters(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    name: Optional[str] = None,
    work_id: Optional[int] = None,
) -> PaginatedResponse[CharacterResponse]:
    """
    List characters with optional filters and pagination.

    Supports ILIKE name search for case-insensitive partial matching.

    Args:
        db: Database session.
        page: Page number (1-indexed).
        size: Items per page.
        name: Optional name filter (ILIKE, partial match).
        work_id: Optional work ID filter.

    Returns:
        PaginatedResponse containing CharacterResponse items.
    """
    query = select(Character).options(selectinload(Character.work))
    count_query = select(func.count()).select_from(Character)

    if name:
        filter_cond = Character.name.ilike(f"%{name}%")
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)
    if work_id is not None:
        filter_cond = Character.work_id == work_id
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Character.id).offset((page - 1) * size).limit(size)
    characters = (await db.execute(query)).scalars().all()
    items = [CharacterResponse.model_validate(c) for c in characters]
    return PaginatedResponse[CharacterResponse](
        items=items, total=total, page=page, size=size
    )


async def get_work(db: AsyncSession, work_id: int) -> Work:
    """
    Get a single work by ID with characters eagerly loaded.

    Args:
        db: Database session.
        work_id: Work primary key.

    Returns:
        The Work ORM instance with characters relationship populated.

    Raises:
        HTTPException(404): If no work with the given ID exists.
    """
    query = (
        select(Work)
        .options(selectinload(Work.characters))
        .where(Work.id == work_id)
    )
    result = await db.execute(query)
    work = result.scalar_one_or_none()
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    return work


async def list_works(
    db: AsyncSession, page: int = 1, size: int = 20
) -> PaginatedResponse[WorkResponse]:
    """
    List all works with pagination.

    Args:
        db: Database session.
        page: Page number (1-indexed).
        size: Items per page.

    Returns:
        PaginatedResponse containing WorkResponse items.
    """
    total = (await db.execute(select(func.count()).select_from(Work))).scalar() or 0
    query = select(Work).order_by(Work.id).offset((page - 1) * size).limit(size)
    works = (await db.execute(query)).scalars().all()
    items = [WorkResponse.model_validate(w) for w in works]
    return PaginatedResponse[WorkResponse](
        items=items, total=total, page=page, size=size
    )
