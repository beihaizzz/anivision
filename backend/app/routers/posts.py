"""
Posts Router (Stub)

Community post API endpoints.
Will be fully implemented in Phase 3.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("", summary="List posts (paginated)")
async def list_posts():
    """Get a paginated list of community posts (coming in Phase 3)."""
    return {"message": "Not implemented yet — Phase 3", "items": []}


@router.post("", summary="Create a new post")
async def create_post():
    """Create a new community post (coming in Phase 3)."""
    return {"message": "Not implemented yet — Phase 3"}


@router.get("/{post_id}", summary="Get post by ID")
async def get_post(post_id: int):
    """Retrieve a single post with comments (coming in Phase 3)."""
    return {"message": "Not implemented yet — Phase 3", "id": post_id}


@router.delete("/{post_id}", summary="Delete a post")
async def delete_post(post_id: int):
    """Delete a post (own post or admin) (coming in Phase 3)."""
    return {"message": "Not implemented yet — Phase 3", "id": post_id}
