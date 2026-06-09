"""
Characters Router (Stub)

Character database API endpoints.
Will be fully implemented in Phase 2.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/characters", tags=["Characters"])


@router.get("", summary="List characters (paginated)")
async def list_characters():
    """Get a paginated list of anime characters (coming in Phase 2)."""
    return {"message": "Not implemented yet — Phase 2", "items": []}


@router.get("/{character_id}", summary="Get character by ID")
async def get_character(character_id: int):
    """Retrieve a single character with work info (coming in Phase 2)."""
    return {"message": "Not implemented yet — Phase 2", "id": character_id}
