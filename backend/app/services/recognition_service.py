"""
Recognition Service

Business logic for anime character image recognition:
- Mock recognition with deterministic-ish Top-5 predictions
- Save recognition results to the database
- Retrieve paginated user recognition history
"""

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.character import Character
from app.models.recognition_log import RecognitionLog
from app.schemas.common import PaginatedResponse
from app.schemas.recognition import PredictionItem, RecognitionResultResponse

logger = logging.getLogger(__name__)

# Mock data: 7 One Piece characters with class_names.json data
CHARACTERS = [
    {"id": 0, "name": "蒙奇·D·路飞", "work": "One Piece"},
    {"id": 1, "name": "妮可·罗宾", "work": "One Piece"},
    {"id": 2, "name": "娜美", "work": "One Piece"},
    {"id": 3, "name": "托尼托尼·乔巴", "work": "One Piece"},
    {"id": 4, "name": "山治", "work": "One Piece"},
    {"id": 5, "name": "罗罗诺亚·索隆", "work": "One Piece"},
    {"id": 6, "name": "乌索普", "work": "One Piece"},
]

# Fixed confidence distribution for Top-5 predictions
CONFIDENCES = [0.65, 0.18, 0.08, 0.05, 0.04]


async def mock_recognize(image_path: str = "") -> List[Dict[str, Any]]:
    """Generate mock recognition results with Top-5 predictions.

    Selects a random "correct" character and 4 other distinct characters,
    all with decreasing confidence scores.

    Args:
        image_path: Optional image path (unused in mock mode).

    Returns:
        List of 5 prediction dicts with rank, character_name, confidence, work_title.
    """
    # Choose a random character as the "correct" answer
    correct = random.choice(CHARACTERS)

    # Build the top prediction
    results: List[Dict[str, Any]] = [
        {
            "rank": 1,
            "character_name": correct["name"],
            "confidence": CONFIDENCES[0],
            "work_title": correct["work"],
        }
    ]

    # Add 4 random other characters (shuffled to avoid bias)
    others = [c for c in CHARACTERS if c["id"] != correct["id"]]
    random.shuffle(others)

    for i in range(4):
        results.append(
            {
                "rank": i + 2,
                "character_name": others[i]["name"],
                "confidence": CONFIDENCES[i + 1],
                "work_title": others[i]["work"],
            }
        )

    # Sort by rank (already in order, but be explicit)
    results.sort(key=lambda x: x["rank"])
    return results


async def real_recognize(
    db: AsyncSession, image_path: str
) -> Tuple[List[Dict[str, Any]], Optional[int]]:
    """Run real anime character recognition using the trained model.

    Initializes the RecognitionPredictor singleton on first call (lazy load),
    then runs inference in a thread pool to avoid blocking the async event loop.

    Args:
        db: Database session (used to look up top_character_id by name).
        image_path: Path to the uploaded image file.

    Returns:
        Tuple of (predictions, top_character_id):
          - predictions: List of 5 dicts with rank, character_name, confidence, work_title.
          - top_character_id: FK to Character table (None if not found in DB).

    Raises:
        HTTPException(500): If the model fails to load or inference fails.
    """
    try:
        from ai_engine.recognition.predictor import RecognitionPredictor
    except ImportError as e:
        logger.error("Failed to import RecognitionPredictor: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI model module not available. Run `pip install -r requirements.txt` in ai_engine.",
        )

    # ── Lazy-load model singleton ───────────────────────────────────
    try:
        predictor = RecognitionPredictor.get_instance(
            settings.MODEL_PATH, settings.LABEL_MAP_PATH
        )
    except Exception as e:
        logger.error("Failed to load recognition model: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load recognition model: {e}",
        )

    # ── Run inference in thread pool (CPU/GPU-bound, non-blocking) ──
    loop = asyncio.get_event_loop()
    try:
        raw_result = await loop.run_in_executor(
            None, lambda: predictor.predict(image_path, top_k=5)
        )
    except Exception as e:
        logger.error("Recognition inference failed for %s: %s", image_path, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recognition inference failed: {e}",
        )

    raw_predictions: List[dict] = raw_result.get("predictions", [])

    # Handle model-not-loaded fallback
    if not raw_predictions:
        error_msg = raw_result.get("error", "No predictions returned")
        logger.warning("Recognition returned empty: %s", error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    # ── Map to service format ───────────────────────────────────────
    predictions: List[Dict[str, Any]] = []
    for p in raw_predictions:
        char_name = p.get("character_name", f"class_{p.get('character_id', '?')}")
        # Try to look up work_title from the database
        work_title = await _resolve_work_title(db, char_name)
        predictions.append(
            {
                "rank": p["rank"],
                "character_name": char_name,
                "confidence": p["confidence"],
                "work_title": work_title,
            }
        )

    # ── Look up top character in DB for FK ──────────────────────────
    top_name = predictions[0]["character_name"] if predictions else None
    top_character_id: Optional[int] = None
    if top_name:
        stmt = select(Character.id).where(Character.name == top_name)
        result = await db.execute(stmt)
        top_character_id = result.scalar()

    return predictions, top_character_id


async def _resolve_work_title(db: AsyncSession, character_name: str) -> str:
    """Resolve a character name to its work title via DB lookup.

    Falls back to the Work model join if the character exists.

    Args:
        db: Database session.
        character_name: Name of the character from model prediction.

    Returns:
        Work title string, or "Unknown" if not found.
    """
    from app.models.work import Work

    stmt = (
        select(Work.title)
        .join(Character, Character.work_id == Work.id)
        .where(Character.name == character_name)
        .limit(1)
    )
    result = await db.execute(stmt)
    work_title = result.scalar()
    return work_title or "Unknown"


async def save_recognition_log(
    db: AsyncSession,
    user_id: Optional[int],
    image_path: str,
    result: List[Dict[str, Any]],
    top_character_id: Optional[int] = None,
    is_mock: bool = True,
) -> RecognitionLog:
    """Save a recognition result to the database.

    Args:
        db: Database session.
        user_id: ID of the requesting user (None for anonymous).
        image_path: Path to the uploaded image file.
        result: List of Top-5 prediction dicts.
        top_character_id: FK to the top-matched character (None if unknown).
        is_mock: Whether this result came from the mock recognizer.

    Returns:
        The persisted RecognitionLog instance.

    Raises:
        HTTPException(500): If database operation fails.
    """
    top_confidence = result[0]["confidence"] if result else None

    log = RecognitionLog(
        user_id=user_id,
        image_path=image_path,
        result=result,
        confidence=top_confidence,
        top_character_id=top_character_id,
        is_mock=is_mock,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def get_user_history(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[RecognitionResultResponse]:
    """Get paginated recognition history for a user.

    Args:
        db: Database session.
        user_id: ID of the user whose history to fetch.
        page: 1-indexed page number.
        size: Number of items per page (max 100).

    Returns:
        PaginatedResponse containing RecognitionResultResponse items.

    Raises:
        HTTPException(404): If no results found for the user.
    """
    # Count total records for this user
    count_query = (
        select(func.count())
        .select_from(RecognitionLog)
        .where(RecognitionLog.user_id == user_id)
    )
    count_result = await db.execute(count_query)
    total: int = count_result.scalar() or 0

    # Fetch the current page ordered by newest first
    query = (
        select(RecognitionLog)
        .where(RecognitionLog.user_id == user_id)
        .order_by(RecognitionLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    data_result = await db.execute(query)
    logs: List[RecognitionLog] = list(data_result.scalars().all())

    # Build response items, mapping ORM fields to schema fields
    items: List[RecognitionResultResponse] = []
    for log in logs:
        # Extract top_character name from the first prediction if available
        top_character: Optional[str] = None
        if log.result and len(log.result) > 0:
            top_character = (
                log.result[0].get("character_name")
                if isinstance(log.result[0], dict)
                else None
            )

        # Convert raw result dicts to PredictionItem instances
        predictions: List[PredictionItem] = []
        for pred_dict in log.result:
            if isinstance(pred_dict, dict):
                predictions.append(PredictionItem(**pred_dict))
            else:
                predictions.append(pred_dict)

        items.append(
            RecognitionResultResponse(
                id=log.id,
                image_url=log.image_path,  # Model field image_path → schema field image_url
                result=predictions,
                confidence=log.confidence,
                top_character=top_character,
                is_mock=log.is_mock if log.is_mock is not None else True,
                created_at=log.created_at,
            )
        )

    return PaginatedResponse[RecognitionResultResponse](
        items=items,
        total=total,
        page=page,
        size=size,
    )
