"""
Recognition Router (Stub)

Image recognition API endpoints.
Will be fully implemented in Phase 2.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/recognition", tags=["Recognition"])


@router.post("/upload", summary="Upload image for recognition")
async def upload_image():
    """Upload an image and run character recognition (coming in Phase 2)."""
    return {"message": "Not implemented yet — Phase 2"}


@router.get("/{recognition_id}", summary="Get recognition result by ID")
async def get_recognition(recognition_id: int):
    """Retrieve a specific recognition result (coming in Phase 2)."""
    return {"message": "Not implemented yet — Phase 2", "id": recognition_id}


@router.get("/history", summary="Get user recognition history")
async def get_history():
    """Retrieve the authenticated user's recognition history (coming in Phase 2)."""
    return {"message": "Not implemented yet — Phase 2", "items": []}
