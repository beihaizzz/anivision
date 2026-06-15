"""
Tests for recognition router endpoints using FastAPI TestClient with mocked dependencies.

Tests cover all three recognition endpoints:
- POST /api/recognition/upload
- GET  /api/recognition/{id}
- GET  /api/recognition/history
"""

import io
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.recognition_log import RecognitionLog
from app.schemas.recognition import PredictionItem, RecognitionResultResponse


# ══════════════════════════════════════════════════════════════════════════
# Override Helpers
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _clear_overrides(app):
    """Ensure no dependency overrides leak between tests."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _override_db(app, mock_db):
    """Override get_db with the given mock session."""
    async def _gen():
        yield mock_db

    app.dependency_overrides[get_db] = _gen


def _override_current_user(app, user):
    """Override get_current_active_user to return the given user."""
    app.dependency_overrides[get_current_active_user] = lambda: user


# ══════════════════════════════════════════════════════════════════════════
# Shared Test Data
# ══════════════════════════════════════════════════════════════════════════

MOCK_PREDICTIONS = [
    {"rank": 1, "character_name": "蒙奇·D·路飞", "confidence": 0.65, "work_title": "One Piece"},
    {"rank": 2, "character_name": "妮可·罗宾", "confidence": 0.18, "work_title": "One Piece"},
    {"rank": 3, "character_name": "娜美", "confidence": 0.08, "work_title": "One Piece"},
    {"rank": 4, "character_name": "托尼托尼·乔巴", "confidence": 0.05, "work_title": "One Piece"},
    {"rank": 5, "character_name": "山治", "confidence": 0.04, "work_title": "One Piece"},
]


def make_recognition_log(**overrides) -> RecognitionLog:
    """Create a RecognitionLog ORM instance with defaults."""
    defaults = {
        "id": 42,
        "user_id": 1,
        "image_path": "images/2025/01/abc.jpg",
        "result": MOCK_PREDICTIONS,
        "confidence": 0.65,
        "is_mock": False,
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return RecognitionLog(**defaults)


# ══════════════════════════════════════════════════════════════════════════
# Upload Endpoint  POST /api/recognition/upload
# ══════════════════════════════════════════════════════════════════════════


class TestUploadEndpoint:
    """Tests for POST /api/recognition/upload."""

    @pytest.mark.unit
    def test_requires_auth(self, client):
        """401 when no Authorization header is provided."""
        response = client.post(
            "/api/recognition/upload",
            files={"file": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")},
        )

        assert response.status_code in (401, 403)

    @pytest.mark.unit
    def test_upload_image_success(self, client, app, test_user_orm):
        """200 with valid image; response has top-5 results with is_mock=False."""
        _override_current_user(app, test_user_orm)

        mock_log = MagicMock()
        mock_log.id = 42
        mock_log.confidence = 0.65
        mock_log.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        with (
            patch("app.routers.recognition.save_upload_file", AsyncMock(return_value="images/2025/01/abc.jpg")),
            patch("app.routers.recognition.real_recognize", AsyncMock(return_value=(MOCK_PREDICTIONS, 1))),
            patch("app.routers.recognition.save_recognition_log", AsyncMock(return_value=mock_log)),
        ):
            response = client.post(
                "/api/recognition/upload",
                files={"file": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 42
        assert body["image_url"] == "images/2025/01/abc.jpg"
        assert body["is_mock"] is False
        assert body["top_character"] == "蒙奇·D·路飞"
        assert body["confidence"] == 0.65
        assert "created_at" in body
        assert len(body["result"]) == 5
        assert body["result"][0]["rank"] == 1
        assert body["result"][0]["character_name"] == "蒙奇·D·路飞"

    @pytest.mark.unit
    def test_upload_non_image_file(self, client, app, test_user_orm):
        """400 when uploading a non-image file (.txt)."""
        _override_current_user(app, test_user_orm)

        # Don't mock save_upload_file / mock_recognize — let validate_image_file reject it
        response = client.post(
            "/api/recognition/upload",
            files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
        )

        assert response.status_code == 400
        assert "allowed" in response.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════
# Get Recognition Endpoint  GET /api/recognition/{id}
# ══════════════════════════════════════════════════════════════════════════


class TestGetRecognitionEndpoint:
    """Tests for GET /api/recognition/{recognition_id}."""

    @pytest.mark.unit
    def test_requires_auth(self, client):
        """401 when no Authorization header is provided."""
        response = client.get("/api/recognition/1")

        assert response.status_code in (401, 403)

    @pytest.mark.unit
    def test_get_result(self, client, app, mock_db, test_user_orm):
        """200 returns RecognitionResultResponse for existing log."""
        _override_current_user(app, test_user_orm)
        _override_db(app, mock_db)

        log = make_recognition_log(id=1)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=log)
        mock_db.execute.return_value = mock_result

        response = client.get("/api/recognition/1")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["image_url"] == "images/2025/01/abc.jpg"
        assert body["is_mock"] is False
        assert body["top_character"] == "蒙奇·D·路飞"
        assert len(body["result"]) == 5
        assert "confidence" in body
        assert "created_at" in body

    @pytest.mark.unit
    def test_get_result_not_found(self, client, app, mock_db, test_user_orm):
        """404 when recognition log does not exist."""
        _override_current_user(app, test_user_orm)
        _override_db(app, mock_db)

        # Default mock_db.scalar_one_or_none returns None → not found
        response = client.get("/api/recognition/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════
# History Endpoint  GET /api/recognition/history
# ══════════════════════════════════════════════════════════════════════════


class TestHistoryEndpoint:
    """Tests for GET /api/recognition/history."""

    @pytest.mark.unit
    def test_requires_auth(self, client):
        """401 when no Authorization header is provided."""
        response = client.get("/api/recognition/history")

        assert response.status_code in (401, 403)

    @pytest.mark.unit
    def test_get_history(self, client, app, mock_db, test_user_orm):
        """200 returns PaginatedResponse with recognition history."""
        _override_current_user(app, test_user_orm)
        _override_db(app, mock_db)

        log = make_recognition_log(id=1)

        # Mock the count query result
        count_mock = AsyncMock()
        count_mock.scalar = MagicMock(return_value=1)

        # Mock the data query result
        data_mock = AsyncMock()
        data_mock.scalars = MagicMock()
        data_mock.scalars().all = MagicMock(return_value=[log])

        # First execute → count query, second execute → data query
        mock_db.execute = AsyncMock(side_effect=[count_mock, data_mock])

        response = client.get("/api/recognition/history?page=1&size=10")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert body["size"] == 10
        assert len(body["items"]) == 1
        assert body["items"][0]["id"] == 1
        assert body["items"][0]["top_character"] == "蒙奇·D·路飞"

    @pytest.mark.unit
    def test_get_history_empty(self, client, app, mock_db, test_user_orm):
        """200 returns total=0, items=[] for user with no history."""
        _override_current_user(app, test_user_orm)
        _override_db(app, mock_db)

        # Mock the count query → 0
        count_mock = AsyncMock()
        count_mock.scalar = MagicMock(return_value=0)

        # Mock the data query → empty
        data_mock = AsyncMock()
        data_mock.scalars = MagicMock()
        data_mock.scalars().all = MagicMock(return_value=[])

        mock_db.execute = AsyncMock(side_effect=[count_mock, data_mock])

        response = client.get("/api/recognition/history")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert len(body["items"]) == 0
