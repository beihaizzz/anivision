"""
Recognition Router

Image recognition API endpoints:
- POST /api/recognition/upload — Upload image and get mock recognition results
- GET  /api/recognition/history — Paginated recognition history for current user
- GET  /api/recognition/{id} — Retrieve a specific recognition result
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.recognition_log import RecognitionLog
from app.models.user import User
from app.schemas.recognition import (
    PredictionItem,
    RecognitionHistoryResponse,
    RecognitionResultResponse,
)
from app.services.recognition_service import (
    get_user_history,
    real_recognize,
    save_recognition_log,
)
from app.utils.file_upload import save_upload_file, validate_image_file

router = APIRouter(prefix="/recognition", tags=["Recognition"])


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_image(
    file: UploadFile = File(..., description="Image file to recognize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload an image and get character recognition results."""
    # Validate file type by reading content
    content = await file.read()
    file_size = len(content)

    # Reset file position for saving
    await file.seek(0)

    try:
        validate_image_file(file.filename or "image.png", file_size)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    # Save file (returns forward-slash path regardless of platform)
    image_path = await save_upload_file(file.file)

    # Run real recognition
    result, top_character_id = await real_recognize(db, image_path)

    # Determine top character (best match)
    top = result[0] if result else None
    top_character_name = top["character_name"] if top else None

    # Save log
    log = await save_recognition_log(
        db=db,
        user_id=current_user.id,
        image_path=image_path,
        result=result,
        top_character_id=top_character_id,
        is_mock=False,
    )

    return {
        "id": log.id,
        "image_url": image_path,
        "result": result,
        "confidence": log.confidence,
        "top_character": top_character_name,
        "is_mock": False,
        "created_at": log.created_at.isoformat(),
    }


# NOTE: /history MUST be registered before /{recognition_id}
# to prevent "history" from being captured as a path parameter.


@router.get("/history", response_model=RecognitionHistoryResponse)
async def get_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get paginated recognition history for the current user."""
    return await get_user_history(db, current_user.id, page=page, size=size)


@router.get("/{recognition_id}", response_model=RecognitionResultResponse)
async def get_recognition(
    recognition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific recognition result by ID."""
    result = await db.execute(
        select(RecognitionLog).where(RecognitionLog.id == recognition_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recognition result not found",
        )

    # Convert result dicts to PredictionItem instances
    predictions: list[PredictionItem] = []
    for pred_dict in log.result:
        if isinstance(pred_dict, dict):
            predictions.append(PredictionItem(**pred_dict))
        else:
            predictions.append(pred_dict)

    # Extract top character from first prediction
    top_character: Optional[str] = None
    if log.result and len(log.result) > 0:
        top_character = (
            log.result[0].get("character_name")
            if isinstance(log.result[0], dict)
            else None
        )

    return RecognitionResultResponse(
        id=log.id,
        image_url=log.image_path,
        result=predictions,
        confidence=log.confidence,
        top_character=top_character,
        is_mock=log.is_mock if log.is_mock is not None else True,
        created_at=log.created_at,
    )
