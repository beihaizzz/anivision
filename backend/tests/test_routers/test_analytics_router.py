"""
Tests for analytics router endpoints using FastAPI TestClient with mocked dependencies.

Tests cover:
- GET /api/analytics/overview
- GET /api/analytics/daily
- GET /api/analytics/top-characters
- GET /api/analytics/recommendations
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.character import Character
from app.schemas.analytics import AnalyticsOverview, DailyStats, TopCharacterItem
from app.schemas.character import CharacterResponse


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
# GET /api/analytics/overview
# ══════════════════════════════════════════════════════════════════════════


class TestGetOverviewEndpoint:
    """Tests for GET /api/analytics/overview."""

    @pytest.mark.unit
    def test_get_overview_returns_200(self, client, app, mock_db, test_user_orm):
        """GET /api/analytics/overview returns 200 with analytics data."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        # Mock 5 execute calls for get_overview
        def _make_result(val):
            r = AsyncMock()
            r.scalar = MagicMock(return_value=val)
            return r

        mock_db.execute = AsyncMock(side_effect=[
            _make_result(42),   # total_users
            _make_result(15),   # total_posts
            _make_result(8),    # total_recognitions
            _make_result(100),  # total_likes
            _make_result(10),   # active_users_today
        ])

        response = client.get("/api/analytics/overview")

        assert response.status_code == 200
        body = response.json()
        assert body["total_users"] == 42
        assert body["total_posts"] == 15
        assert body["total_recognitions"] == 8
        assert body["total_likes"] == 100
        assert body["active_users_today"] == 10

    @pytest.mark.unit
    def test_get_overview_requires_auth(self, client, app, mock_db):
        """GET /api/analytics/overview without auth returns 401."""
        _override_db(app, mock_db)
        # NO current_user override

        response = client.get("/api/analytics/overview")

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# GET /api/analytics/daily
# ══════════════════════════════════════════════════════════════════════════


class TestGetDailyStatsEndpoint:
    """Tests for GET /api/analytics/daily."""

    @pytest.mark.unit
    def test_get_daily_stats_returns_200(self, client, app, mock_db, test_user_orm):
        """GET /api/analytics/daily?days=7 returns 200 with stats list."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        def _make_result(val):
            r = AsyncMock()
            r.scalar = MagicMock(return_value=val)
            return r

        # 7 days * 3 queries = 21 execute calls
        results = []
        for _ in range(7):
            results.append(_make_result(2))  # new_users
            results.append(_make_result(5))  # new_posts
            results.append(_make_result(3))  # recognitions
        mock_db.execute = AsyncMock(side_effect=results)

        response = client.get("/api/analytics/daily", params={"days": 7})

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 7
        for item in body:
            assert "date" in item
            assert "new_users" in item
            assert "new_posts" in item
            assert "recognitions" in item

    @pytest.mark.unit
    def test_get_daily_stats_requires_auth(self, client, app, mock_db):
        """GET /api/analytics/daily without auth returns 401."""
        _override_db(app, mock_db)

        response = client.get("/api/analytics/daily")

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# GET /api/analytics/top-characters
# ══════════════════════════════════════════════════════════════════════════


class TestGetTopCharactersEndpoint:
    """Tests for GET /api/analytics/top-characters."""

    @pytest.mark.unit
    def test_get_top_characters_returns_200(self, client, app, mock_db, test_user_orm):
        """GET /api/analytics/top-characters returns 200 with character list."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        char = Character(id=1, name="Goku")

        def _make_all(rows):
            r = AsyncMock()
            r.all = MagicMock(return_value=rows)
            return r

        def _make_one(val):
            r = AsyncMock()
            r.scalar_one_or_none = MagicMock(return_value=val)
            return r

        mock_db.execute = AsyncMock(side_effect=[
            _make_all([(1, 25)]),
            _make_one(char),
        ])

        response = client.get("/api/analytics/top-characters")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["character_id"] == 1
        assert body[0]["character_name"] == "Goku"
        assert body[0]["recognition_count"] == 25

    @pytest.mark.unit
    def test_get_top_characters_requires_auth(self, client, app, mock_db):
        """GET /api/analytics/top-characters without auth returns 401."""
        _override_db(app, mock_db)

        response = client.get("/api/analytics/top-characters")

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# GET /api/analytics/recommendations
# ══════════════════════════════════════════════════════════════════════════


class TestGetRecommendationsEndpoint:
    """Tests for GET /api/analytics/recommendations."""

    @pytest.mark.unit
    def test_get_recommendations_returns_200(self, client, app, mock_db, test_user_orm):
        """GET /api/analytics/recommendations returns 200 with character list."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        # Build mock characters with required attributes for CharacterResponse
        char = MagicMock(spec=Character)
        char.id = 10
        char.name = "Luffy"
        char.name_jp = "ルフィ"
        char.aliases = []
        char.description = "Pirate King"
        char.image_url = "http://example.com/luffy.png"
        char.work = None
        char.created_at = datetime.utcnow()

        # Mock the execute calls in recommendation_service.get_recommendations
        def _make_seen_result(rows):
            r = AsyncMock()
            r.all = MagicMock(return_value=rows)
            return r

        def _make_scalars(items):
            r = AsyncMock()
            r.scalars = MagicMock()
            r.scalars.return_value.all = MagicMock(return_value=items)
            return r

        # First call: seen_ids query returns empty (cold start)
        # Second call: popular characters query
        mock_db.execute = AsyncMock(side_effect=[
            _make_seen_result([]),      # seen character IDs (empty → cold start)
            _make_scalars([char]),      # popular characters
        ])

        response = client.get("/api/analytics/recommendations")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["id"] == 10
        assert body[0]["name"] == "Luffy"

    @pytest.mark.unit
    def test_get_recommendations_requires_auth(self, client, app, mock_db):
        """GET /api/analytics/recommendations without auth returns 401."""
        _override_db(app, mock_db)

        response = client.get("/api/analytics/recommendations")

        assert response.status_code == 401
