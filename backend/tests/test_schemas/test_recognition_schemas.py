"""
Unit tests for Recognition Schemas

Tests validation, serialization, and edge cases for:
- PredictionItem
- RecognitionUploadResponse
- RecognitionResultResponse
- RecognitionHistoryResponse

NOTE: Tests are self-contained and do not depend on conftest.py fixtures,
because the root conftest triggers app.database module-level engine creation
which is incompatible with SQLite. Run with: pytest --noconftest -m unit
"""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.recognition import (
    PredictionItem,
    RecognitionHistoryResponse,
    RecognitionResultResponse,
    RecognitionUploadResponse,
)


def _make_utcnow() -> datetime:
    """Return current UTC datetime (avoiding deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Shared test data ───────────────────────────────────────────────────

VALID_PREDICTION = {
    "rank": 1,
    "character_name": "Hatake Kakashi",
    "confidence": 0.95,
    "work_title": "Naruto",
}

VALID_PREDICTIONS = [
    {"rank": 1, "character_name": "Hatake Kakashi", "confidence": 0.95, "work_title": "Naruto"},
    {"rank": 2, "character_name": "Uzumaki Naruto", "confidence": 0.72, "work_title": "Naruto"},
    {"rank": 3, "character_name": "Levi Ackerman", "confidence": 0.34, "work_title": "Attack on Titan"},
]

VALID_RESULT_DICT = {
    "id": 1,
    "image_url": "uploads/2025/kakashi.jpg",
    "result": VALID_PREDICTIONS,
    "confidence": 0.95,
    "top_character": "Hatake Kakashi",
    "is_mock": True,
    "created_at": _make_utcnow(),
}


# ══════════════════════════════════════════════════════════════════════════
# PredictionItem
# ══════════════════════════════════════════════════════════════════════════


class TestPredictionItem:
    """Tests for PredictionItem schema."""

    @pytest.mark.unit
    def test_valid_prediction_item(self):
        """Should accept valid prediction item data."""
        item = PredictionItem(**VALID_PREDICTION)
        assert item.rank == 1
        assert item.character_name == "Hatake Kakashi"
        assert item.confidence == 0.95
        assert item.work_title == "Naruto"

    @pytest.mark.unit
    def test_rank_min_ge_one(self):
        """Should reject rank=0 (less than ge=1)."""
        data = {**VALID_PREDICTION, "rank": 0}
        with pytest.raises(ValidationError) as exc:
            PredictionItem(**data)
        errors = exc.value.errors()
        assert any("rank" in str(e["loc"]) for e in errors)

    @pytest.mark.unit
    def test_rank_negative(self):
        """Should reject negative rank."""
        data = {**VALID_PREDICTION, "rank": -1}
        with pytest.raises(ValidationError) as exc:
            PredictionItem(**data)
        errors = exc.value.errors()
        assert any("rank" in str(e["loc"]) for e in errors)

    @pytest.mark.unit
    def test_confidence_zero(self):
        """Should accept confidence=0.0."""
        data = {**VALID_PREDICTION, "confidence": 0.0}
        item = PredictionItem(**data)
        assert item.confidence == 0.0

    @pytest.mark.unit
    def test_confidence_one(self):
        """Should accept confidence=1.0."""
        data = {**VALID_PREDICTION, "confidence": 1.0}
        item = PredictionItem(**data)
        assert item.confidence == 1.0

    @pytest.mark.unit
    def test_confidence_below_zero(self):
        """Should reject confidence < 0.0."""
        data = {**VALID_PREDICTION, "confidence": -0.01}
        with pytest.raises(ValidationError) as exc:
            PredictionItem(**data)
        errors = exc.value.errors()
        assert any("confidence" in str(e["loc"]) for e in errors)

    @pytest.mark.unit
    def test_confidence_above_one(self):
        """Should reject confidence > 1.0."""
        data = {**VALID_PREDICTION, "confidence": 1.1}
        with pytest.raises(ValidationError) as exc:
            PredictionItem(**data)
        errors = exc.value.errors()
        assert any("confidence" in str(e["loc"]) for e in errors)

    @pytest.mark.unit
    def test_serialize_to_dict(self):
        """Should serialize correctly to dict for JSONB storage."""
        item = PredictionItem(**VALID_PREDICTION)
        d = item.model_dump()
        assert d["rank"] == 1
        assert d["character_name"] == "Hatake Kakashi"
        assert d["confidence"] == 0.95
        assert d["work_title"] == "Naruto"

    @pytest.mark.unit
    def test_serialize_to_json(self):
        """Should serialize correctly to JSON for API responses."""
        item = PredictionItem(**VALID_PREDICTION)
        raw = item.model_dump_json()
        d = json.loads(raw)
        assert d["rank"] == 1
        assert d["character_name"] == "Hatake Kakashi"
        assert d["work_title"] == "Naruto"

    @pytest.mark.unit
    def test_numeric_confidence_serialization(self):
        """Confidence should serialize as a float, not a string."""
        item = PredictionItem(**VALID_PREDICTION)
        raw = item.model_dump_json()
        d = json.loads(raw)
        assert isinstance(d["confidence"], float)


# ══════════════════════════════════════════════════════════════════════════
# RecognitionUploadResponse
# ══════════════════════════════════════════════════════════════════════════


class TestRecognitionUploadResponse:
    """Tests for RecognitionUploadResponse schema."""

    @pytest.mark.unit
    def test_valid_response_with_id(self):
        """Should accept valid response with id."""
        resp = RecognitionUploadResponse(id=42)
        assert resp.id == 42
        assert resp.status == "processing"
        assert resp.message == "Image uploaded successfully"

    @pytest.mark.unit
    def test_default_status_and_message(self):
        """Should use default status and message values."""
        resp = RecognitionUploadResponse(id=1)
        assert resp.status == "processing"
        assert resp.message == "Image uploaded successfully"

    @pytest.mark.unit
    def test_custom_status(self):
        """Should accept custom status value."""
        resp = RecognitionUploadResponse(id=1, status="completed")
        assert resp.status == "completed"

    @pytest.mark.unit
    def test_custom_message(self):
        """Should accept custom message value."""
        resp = RecognitionUploadResponse(id=1, message="Custom message")
        assert resp.message == "Custom message"

    @pytest.mark.unit
    def test_serialize_to_json(self):
        """Should serialize correctly to JSON."""
        resp = RecognitionUploadResponse(id=5)
        raw = resp.model_dump_json()
        d = json.loads(raw)
        assert d["id"] == 5
        assert d["status"] == "processing"
        assert d["message"] == "Image uploaded successfully"


# ══════════════════════════════════════════════════════════════════════════
# RecognitionResultResponse
# ══════════════════════════════════════════════════════════════════════════


class TestRecognitionResultResponse:
    """Tests for RecognitionResultResponse schema."""

    @pytest.mark.unit
    def test_valid_full_result(self):
        """Should accept a complete recognition result."""
        resp = RecognitionResultResponse(**VALID_RESULT_DICT)
        assert resp.id == 1
        assert resp.image_url == "uploads/2025/kakashi.jpg"
        assert len(resp.result) == 3
        assert resp.confidence == 0.95
        assert resp.top_character == "Hatake Kakashi"
        assert resp.is_mock is True
        assert resp.created_at == VALID_RESULT_DICT["created_at"]

    @pytest.mark.unit
    def test_result_items_are_prediction_item_objects(self):
        """Result items should be parsed as PredictionItem objects."""
        resp = RecognitionResultResponse(**VALID_RESULT_DICT)
        for item in resp.result:
            assert isinstance(item, PredictionItem)
            assert isinstance(item.rank, int)
            assert isinstance(item.confidence, float)
            assert isinstance(item.character_name, str)
            assert isinstance(item.work_title, str)

    @pytest.mark.unit
    def test_is_mock_defaults_to_true(self):
        """is_mock should default to True when not provided."""
        data = {k: v for k, v in VALID_RESULT_DICT.items() if k != "is_mock"}
        resp = RecognitionResultResponse(**data)
        assert resp.is_mock is True

    @pytest.mark.unit
    def test_is_mock_explicit_false(self):
        """is_mock should accept explicit False."""
        data = {**VALID_RESULT_DICT, "is_mock": False}
        resp = RecognitionResultResponse(**data)
        assert resp.is_mock is False

    @pytest.mark.unit
    def test_image_url_nullable(self):
        """image_url should allow empty string for pending results."""
        data = {**VALID_RESULT_DICT, "image_url": ""}
        resp = RecognitionResultResponse(**data)
        assert resp.image_url == ""

    @pytest.mark.unit
    def test_nullable_confidence_and_top_character(self):
        """confidence and top_character should accept None."""
        data = {
            **VALID_RESULT_DICT,
            "confidence": None,
            "top_character": None,
        }
        resp = RecognitionResultResponse(**data)
        assert resp.confidence is None
        assert resp.top_character is None

    @pytest.mark.unit
    def test_from_attributes_compatible(self):
        """Should have from_attributes=True config for ORM compatibility."""
        assert RecognitionResultResponse.model_config.get("from_attributes") is True

    @pytest.mark.unit
    def test_serialize_to_json(self):
        """Should serialize correctly to JSON."""
        resp = RecognitionResultResponse(**VALID_RESULT_DICT)
        raw = resp.model_dump_json()
        d = json.loads(raw)
        assert d["id"] == 1
        assert d["image_url"] == "uploads/2025/kakashi.jpg"
        assert len(d["result"]) == 3
        assert d["confidence"] == 0.95
        assert d["top_character"] == "Hatake Kakashi"
        assert d["is_mock"] is True
        assert "created_at" in d


# ══════════════════════════════════════════════════════════════════════════
# RecognitionHistoryResponse
# ══════════════════════════════════════════════════════════════════════════


class TestRecognitionHistoryResponse:
    """Tests for RecognitionHistoryResponse schema."""

    @pytest.mark.unit
    def test_valid_history_response(self):
        """Should accept valid paginated history response."""
        item = RecognitionResultResponse(**VALID_RESULT_DICT)
        resp = RecognitionHistoryResponse(
            items=[item],
            total=1,
            page=1,
            size=20,
        )
        assert len(resp.items) == 1
        assert resp.total == 1
        assert resp.page == 1
        assert resp.size == 20
        assert resp.items[0].id == 1

    @pytest.mark.unit
    def test_pages_property(self):
        """Should calculate pages correctly from total and size."""
        items = [RecognitionResultResponse(**VALID_RESULT_DICT) for _ in range(3)]
        resp = RecognitionHistoryResponse(items=items, total=25, page=1, size=10)
        # 25 items / 10 per page = 3 pages (ceil)
        assert resp.pages == 3

    @pytest.mark.unit
    def test_pages_zero_size(self):
        """Should return 0 pages when size is 0."""
        resp = RecognitionHistoryResponse(items=[], total=0, page=1, size=0)
        assert resp.pages == 0

    @pytest.mark.unit
    def test_empty_items_list(self):
        """Should accept empty items list."""
        resp = RecognitionHistoryResponse(items=[], total=0, page=1, size=20)
        assert resp.items == []
        assert resp.total == 0

    @pytest.mark.unit
    def test_serialize_to_json(self):
        """Should serialize correctly to JSON."""
        item = RecognitionResultResponse(**VALID_RESULT_DICT)
        resp = RecognitionHistoryResponse(items=[item], total=1, page=1, size=20)
        raw = resp.model_dump_json()
        d = json.loads(raw)
        assert len(d["items"]) == 1
        assert d["total"] == 1
        assert d["page"] == 1
        assert d["size"] == 20
        assert d["items"][0]["id"] == 1
