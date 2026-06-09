"""
Users Router (Stub)

User profile API endpoints.
Will be fully implemented in Phase 3.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", summary="Get user profile by ID")
async def get_user(user_id: int):
    """Retrieve a user's public profile (coming in Phase 3)."""
    return {"message": "Not implemented yet — Phase 3", "id": user_id}


@router.get("/{user_id}/posts", summary="Get user's posts")
async def get_user_posts(user_id: int):
    """Retrieve posts by a specific user (coming in Phase 3)."""
    return {"message": "Not implemented yet — Phase 3", "id": user_id, "items": []}
