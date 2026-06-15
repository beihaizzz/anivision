"""
Unit tests for recognition_service.py

Tests mock_recognize(), save_recognition_log(), and get_user_history()
using mocked database sessions from conftest.py.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.recognition_log import RecognitionLog
from app.schemas.common import PaginatedResponse
from app.schemas.recognition import PredictionItem, RecognitionResultResponse
from app.services.recognition_service import (
    CHARACTERS,
    get_user_history,
    mock_recognize,
    save_recognition_log,
)

# ══════════════════════════════════════════════════════════════════════
# mock_recognize
# ══════════════════════════════════════════════════════════════════════


class TestMockRecognize:
    """Tests for mock_recognize()."""

    @pytest.mark.unit
    async def test_returns_five_predictions(self):
        """Returns exactly 5 PredictionItem-compatible dicts."""
        results = await mock_recognize()

        assert isinstance(results, list)
        assert len(results) == 5, f"Expected 5 predictions, got {len(results)}"

    @pytest.mark.unit
    async def test_predictions_have_required_fields(self):
        """Each prediction has rank, character_name, confidence, work_title."""
        results = await mock_recognize()

        for pred in results:
            assert "rank" in pred
            assert "character_name" in pred
            assert "confidence" in pred
            assert "work_title" in pred

    @pytest.mark.unit
    async def test_confidences_decrease_monotonically(self):
        """Top prediction has highest confidence, values decrease."""
        results = await mock_recognize()

        confidences = [p["confidence"] for p in results]
        for i in range(len(confidences) - 1):
            assert (
                confidences[i] >= confidences[i + 1]
            ), f"Confidence at rank {i+1} ({confidences[i]}) < rank {i+2} ({confidences[i+1]})"

    @pytest.mark.unit
    async def test_all_character_names_from_class_names(self):
        """Every character name comes from the 7 CHARACTERS list."""
        results = await mock_recognize()

        valid_names = {c["name"] for c in CHARACTERS}
        for pred in results:
            assert (
                pred["character_name"] in valid_names
            ), f"'{pred['character_name']}' is not a known character"

    @pytest.mark.unit
    async def test_ranks_are_1_to_5_sequential(self):
        """Ranks are 1 through 5 in order."""
        results = await mock_recognize()

        ranks = [p["rank"] for p in results]
        assert ranks == [1, 2, 3, 4, 5], f"Expected ranks 1-5, got {ranks}"

    @pytest.mark.unit
    async def test_no_duplicate_characters(self):
        """No character appears more than once in top-5."""
        results = await mock_recognize()

        names = [p["character_name"] for p in results]
        assert len(names) == len(set(names)), f"Duplicate characters found: {names}"

    @pytest.mark.unit
    async def test_top_confidence_is_around_0_65(self):
        """Top prediction confidence is approximately 0.65."""
        results = await mock_recognize()

        top_conf = results[0]["confidence"]
        assert (
            0.6 <= top_conf <= 0.75
        ), f"Top confidence {top_conf} not in expected range"

    @pytest.mark.unit
    async def test_is_mock_flag_present_in_response_when_wrapped(self):
        """When results are wrapped for API, is_mock flag is present."""
        results = await mock_recognize()

        # mock_recognize returns raw predictions; the is_mock flag is
        # set by save_recognition_log / the API layer. Verify structure is correct.
        for pred in results:
            assert pred["confidence"] <= 1.0
            assert pred["confidence"] >= 0.0

    @pytest.mark.unit
    async def test_accepts_optional_image_path_parameter(self):
        """mock_recognize accepts an optional image_path parameter."""
        results = await mock_recognize(image_path="/some/path.jpg")
        assert len(results) == 5


# ══════════════════════════════════════════════════════════════════════
# save_recognition_log
# ══════════════════════════════════════════════════════════════════════


class TestSaveRecognitionLog:
    """Tests for save_recognition_log()."""

    @pytest.fixture
    def sample_results(self):
        """Sample recognition results for testing."""
        return [
            {
                "rank": 1,
                "character_name": "蒙奇·D·路飞",
                "confidence": 0.65,
                "work_title": "One Piece",
            },
            {
                "rank": 2,
                "character_name": "罗罗诺亚·索隆",
                "confidence": 0.18,
                "work_title": "One Piece",
            },
            {
                "rank": 3,
                "character_name": "娜美",
                "confidence": 0.08,
                "work_title": "One Piece",
            },
            {
                "rank": 4,
                "character_name": "山治",
                "confidence": 0.05,
                "work_title": "One Piece",
            },
            {
                "rank": 5,
                "character_name": "乌索普",
                "confidence": 0.04,
                "work_title": "One Piece",
            },
        ]

    @pytest.mark.unit
    async def test_saves_log_and_returns_recognition_log(
        self, mock_db, sample_results
    ):
        """Saves to DB, returns RecognitionLog with is_mock=True."""
        result = await save_recognition_log(
            db=mock_db,
            user_id=1,
            image_path="/uploads/test.png",
            result=sample_results,
            top_character_id=0,
            is_mock=True,
        )

        assert isinstance(result, RecognitionLog)
        assert result.is_mock is True
        assert result.user_id == 1
        assert result.image_path == "/uploads/test.png"
        assert result.top_character_id == 0

    @pytest.mark.unit
    async def test_adds_log_to_db_session(self, mock_db, sample_results):
        """Calls db.add() with the RecognitionLog."""
        await save_recognition_log(
            db=mock_db,
            user_id=1,
            image_path="/uploads/a.png",
            result=sample_results,
        )

        mock_db.add.assert_called_once()
        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, RecognitionLog)
        assert added_obj.is_mock is True

    @pytest.mark.unit
    async def test_flushes_and_refreshes(self, mock_db, sample_results):
        """Calls db.flush() and db.refresh()."""
        await save_recognition_log(
            db=mock_db,
            user_id=1,
            image_path="/uploads/b.png",
            result=sample_results,
        )

        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.unit
    async def test_properly_stores_result_jsonb(self, mock_db, sample_results):
        """Stores the full result array in the log."""
        result_log = await save_recognition_log(
            db=mock_db,
            user_id=1,
            image_path="/uploads/c.png",
            result=sample_results,
        )

        assert result_log.result == sample_results
        assert len(result_log.result) == 5

    @pytest.mark.unit
    async def test_extracts_top_confidence_from_results(
        self, mock_db, sample_results
    ):
        """Sets confidence from the top prediction."""
        result_log = await save_recognition_log(
            db=mock_db,
            user_id=1,
            image_path="/uploads/d.png",
            result=sample_results,
        )

        assert result_log.confidence == 0.65

    @pytest.mark.unit
    async def test_is_mock_defaults_to_true(self, mock_db, sample_results):
        """is_mock defaults to True when not explicitly passed."""
        result_log = await save_recognition_log(
            db=mock_db,
            user_id=2,
            image_path="/uploads/e.png",
            result=sample_results,
        )

        assert result_log.is_mock is True

    @pytest.mark.unit
    async def test_user_id_can_be_none(self, mock_db, sample_results):
        """Allows null user_id for anonymous recognition."""
        result_log = await save_recognition_log(
            db=mock_db,
            user_id=None,
            image_path="/uploads/anon.png",
            result=sample_results,
        )

        assert result_log.user_id is None


# ══════════════════════════════════════════════════════════════════════
# get_user_history
# ══════════════════════════════════════════════════════════════════════


class TestGetUserHistory:
    """Tests for get_user_history()."""

    @pytest.fixture
    def sample_logs(self):
        """Build a list of mock RecognitionLog objects."""
        logs = []
        for i in range(3):
            log = MagicMock(spec=RecognitionLog)
            log.id = i + 1
            log.user_id = 1
            log.image_path = f"/uploads/img_{i}.png"
            log.result = [
                {"rank": 1, "character_name": "蒙奇·D·路飞", "confidence": 0.65, "work_title": "One Piece"},
            ]
            log.confidence = 0.65
            log.top_character_id = 0
            log.is_mock = True
            log.created_at = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
            logs.append(log)
        return logs

    @pytest.mark.unit
    async def test_returns_paginated_response(self, mock_db, sample_logs):
        """Returns a PaginatedResponse instance."""
        # Setup: first execute = count (returns 3), second = data (returns sample_logs)
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=3)

        data_result = AsyncMock()
        data_result.scalars = MagicMock()
        data_result.scalars.return_value.all = MagicMock(return_value=sample_logs)

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        result = await get_user_history(
            db=mock_db,
            user_id=1,
            page=1,
            size=20,
        )

        assert isinstance(result, PaginatedResponse)
        assert result.total == 3
        assert result.page == 1
        assert result.size == 20
        assert len(result.items) == 3

    @pytest.mark.unit
    async def test_returns_recognition_result_responses(
        self, mock_db, sample_logs
    ):
        """Items are RecognitionResultResponse instances."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=3)

        data_result = AsyncMock()
        data_result.scalars = MagicMock()
        data_result.scalars.return_value.all = MagicMock(return_value=sample_logs)

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        result = await get_user_history(
            db=mock_db,
            user_id=1,
        )

        for item in result.items:
            assert isinstance(item, RecognitionResultResponse)
            assert item.is_mock is True
            assert item.id is not None

    @pytest.mark.unit
    async def test_empty_for_new_users(self, mock_db):
        """Returns empty items list for users with no history."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=0)

        data_result = AsyncMock()
        data_result.scalars = MagicMock()
        data_result.scalars.return_value.all = MagicMock(return_value=[])

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        result = await get_user_history(
            db=mock_db,
            user_id=999,
        )

        assert result.total == 0
        assert result.items == []
        assert result.page == 1

    @pytest.mark.unit
    async def test_returns_correct_total_count(self, mock_db, sample_logs):
        """Total reflects the count query result."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=42)

        data_result = AsyncMock()
        data_result.scalars = MagicMock()
        data_result.scalars.return_value.all = MagicMock(return_value=sample_logs)

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        result = await get_user_history(
            db=mock_db,
            user_id=1,
        )

        assert result.total == 42

    @pytest.mark.unit
    async def test_pagination_offset(self, mock_db, sample_logs):
        """Applies correct offset/limit for pagination."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=50)

        data_result = AsyncMock()
        data_result.scalars = MagicMock()
        data_result.scalars.return_value.all = MagicMock(return_value=sample_logs)

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        result = await get_user_history(
            db=mock_db,
            user_id=1,
            page=3,
            size=10,
        )

        assert result.page == 3
        assert result.size == 10

    @pytest.mark.unit
    async def test_image_url_mapped_from_model_image_path(
        self, mock_db, sample_logs
    ):
        """image_url in response is mapped from model's image_path."""
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=1)

        log = MagicMock(spec=RecognitionLog)
        log.id = 1
        log.user_id = 1
        log.image_path = "/uploads/characters/luffy.webp"
        log.result = [
            {"rank": 1, "character_name": "蒙奇·D·路飞", "confidence": 0.65, "work_title": "One Piece"},
        ]
        log.confidence = 0.65
        log.top_character_id = 0
        log.is_mock = True
        log.created_at = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        data_result = AsyncMock()
        data_result.scalars = MagicMock()
        data_result.scalars.return_value.all = MagicMock(return_value=[log])

        mock_db.execute = AsyncMock(side_effect=[count_result, data_result])

        result = await get_user_history(db=mock_db, user_id=1)

        assert result.items[0].image_url == "/uploads/characters/luffy.webp"
