"""
Characters & Works Router

Character and work query endpoints:
- GET /api/characters          — List characters (paginated, filterable)
- GET /api/characters/{id}     — Get character by ID with work info
- GET /api/characters/works    — List works (paginated)
- GET /api/characters/works/{id} — Get work by ID with character info
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.character import (
    CharacterListResponse,
    CharacterResponse,
    WorkListResponse,
    WorkResponse,
)
from app.services.character_service import (
    get_character,
    get_work,
    list_characters,
    list_works,
)

router = APIRouter(prefix="/characters", tags=["Characters"])


# ── Character Endpoints ──────────────────────────────────────────────


@router.get(
    "",
    response_model=CharacterListResponse,
    summary="List characters (paginated)",
)
async def get_characters(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: str = Query(None, description="Filter by character name (ILIKE)"),
    work_id: int = Query(None, ge=1, description="Filter by work ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get a paginated list of characters with optional name and work filters."""
    return await list_characters(db, page=page, size=size, name=name, work_id=work_id)


# ── Work Endpoints (must be before /{character_id} to avoid route collision) ──


@router.get(
    "/works",
    response_model=WorkListResponse,
    summary="List works (paginated)",
)
async def get_works(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Get a paginated list of anime/manga/game works."""
    return await list_works(db, page=page, size=size)


@router.get(
    "/works/{work_id}",
    response_model=WorkResponse,
    summary="Get work by ID",
)
async def get_work_by_id(
    work_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single work with associated character list."""
    work = await get_work(db, work_id)
    return WorkResponse.model_validate(work)


# ── Character Detail (must be last to avoid capturing /works) ────────


@router.get(
    "/{character_id}",
    response_model=CharacterResponse,
    summary="Get character by ID",
)
async def get_character_by_id(
    character_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single character with associated work information."""
    character = await get_character(db, character_id)
    return CharacterResponse.model_validate(character)
