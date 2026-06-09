"""
Analytics Router (Stub)

Usage analytics and statistics API endpoints.
Will be fully implemented in Phase 4.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", summary="Get analytics overview")
async def get_overview():
    """Get platform analytics overview (coming in Phase 4)."""
    return {"message": "Not implemented yet — Phase 4"}
