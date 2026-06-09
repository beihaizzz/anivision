"""
Search Router (Stub)

Global search API endpoint.
Will be fully implemented in Phase 3.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", summary="Global search")
async def search():
    """Search across characters, posts, and users (coming in Phase 3)."""
    return {"message": "Not implemented yet — Phase 3", "results": []}
