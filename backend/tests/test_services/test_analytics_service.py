"""
Unit tests for analytics_service.py

Tests get_overview(), get_daily_stats(), and get_top_characters()
using mocked database sessions from conftest.py.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.character import Character
from app.schemas.analytics import AnalyticsOverview, DailyStats, TopCharacterItem
from app.services.analytics_service import get_daily_stats, get_overview, get_top_characters


def _make_scalar_result(value):
    """Create a mock execute result whose .scalar() returns value."""
    r = AsyncMock()
    r.scalar = MagicMock(return_value=value)
    return r


def _make_all_result(rows):
    """Create a mock execute result whose .all() returns rows."""
    r = AsyncMock()
    r.all = MagicMock(return_value=rows)
    return r


def _make_scalar_one_or_none_result(value):
    """Create a mock execute result whose .scalar_one_or_none() returns value."""
    r = AsyncMock()
    r.scalar_one_or_none = MagicMock(return_value=value)
    return r


class TestGetOverview:
    """Tests for get_overview()."""

    @pytest.mark.unit
    async def test_returns_analytics_overview_with_all_five_counters(self, mock_db):
        """get_overview returns AnalyticsOverview with all 5 counters."""
        mock_db.execute = AsyncMock(side_effect=[
            _make_scalar_result(100),   # total_users
            _make_scalar_result(200),   # total_posts
            _make_scalar_result(50),    # total_recognitions
            _make_scalar_result(300),   # total_likes
            _make_scalar_result(25),    # active_users_today
        ])

        result = await get_overview(mock_db)

        assert isinstance(result, AnalyticsOverview)
        assert result.total_users == 100
        assert result.total_posts == 200
        assert result.total_recognitions == 50
        assert result.total_likes == 300
        assert result.active_users_today == 25

    @pytest.mark.unit
    async def test_handles_empty_database(self, mock_db):
        """All counters are 0 when database has no data."""
        mock_db.execute = AsyncMock(side_effect=[
            _make_scalar_result(0),
            _make_scalar_result(0),
            _make_scalar_result(0),
            _make_scalar_result(0),
            _make_scalar_result(0),
        ])

        result = await get_overview(mock_db)

        assert result.total_users == 0
        assert result.total_posts == 0
        assert result.total_recognitions == 0
        assert result.total_likes == 0
        assert result.active_users_today == 0

    @pytest.mark.unit
    async def test_returns_zero_when_scalar_is_none(self, mock_db):
        """When scalar() returns None, counters default to 0."""
        mock_db.execute = AsyncMock(side_effect=[
            _make_scalar_result(None),
            _make_scalar_result(None),
            _make_scalar_result(None),
            _make_scalar_result(None),
            _make_scalar_result(None),
        ])

        result = await get_overview(mock_db)

        assert result.total_users == 0
        assert result.total_posts == 0


class TestGetDailyStats:
    """Tests for get_daily_stats()."""

    @pytest.mark.unit
    async def test_returns_list_of_daily_stats_for_past_n_days(self, mock_db):
        """get_daily_stats returns a list of DailyStats for past 3 days."""
        # 3 days * 3 queries per day = 9 execute calls
        results = []
        for i in range(3):  # day_offset 0, 1, 2
            results.append(_make_scalar_result(5 + i))   # new_users
            results.append(_make_scalar_result(10 + i))  # new_posts
            results.append(_make_scalar_result(3 + i))   # recognitions
        mock_db.execute = AsyncMock(side_effect=results)

        result = await get_daily_stats(mock_db, days=3)

        assert isinstance(result, list)
        assert len(result) == 3
        for item in result:
            assert isinstance(item, DailyStats)
            assert isinstance(item.date, datetime)
            assert isinstance(item.new_users, int)
            assert isinstance(item.new_posts, int)
            assert isinstance(item.recognitions, int)

    @pytest.mark.unit
    async def test_dates_are_descending_from_today(self, mock_db):
        """Returned dates are ordered from today backwards."""
        results = []
        for _ in range(2):  # 2 days * 3 queries
            results.append(_make_scalar_result(1))
            results.append(_make_scalar_result(1))
            results.append(_make_scalar_result(1))
        mock_db.execute = AsyncMock(side_effect=results)

        result = await get_daily_stats(mock_db, days=2)

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        assert result[0].date == today
        assert result[1].date == today - timedelta(days=1)

    @pytest.mark.unit
    async def test_defaults_to_7_days(self, mock_db):
        """Default days parameter is 7."""
        results = []
        for _ in range(7):  # 7 days * 3 queries
            results.append(_make_scalar_result(1))
            results.append(_make_scalar_result(1))
            results.append(_make_scalar_result(1))
        mock_db.execute = AsyncMock(side_effect=results)

        result = await get_daily_stats(mock_db)

        assert len(result) == 7


class TestGetTopCharacters:
    """Tests for get_top_characters()."""

    @pytest.mark.unit
    async def test_returns_top_character_items_sorted_by_count(self, mock_db):
        """get_top_characters returns list of TopCharacterItem sorted by recognition_count."""
        char1 = Character(id=1, name="Naruto")
        char2 = Character(id=2, name="Sasuke")

        mock_db.execute = AsyncMock(side_effect=[
            _make_all_result([(1, 15), (2, 8)]),               # grouped query
            _make_scalar_one_or_none_result(char1),             # Character #1
            _make_scalar_one_or_none_result(char2),             # Character #2
        ])

        result = await get_top_characters(mock_db, limit=10)

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], TopCharacterItem)
        assert result[0].character_id == 1
        assert result[0].character_name == "Naruto"
        assert result[0].recognition_count == 15
        assert result[1].character_id == 2
        assert result[1].character_name == "Sasuke"
        assert result[1].recognition_count == 8

    @pytest.mark.unit
    async def test_uses_fallback_name_for_missing_character(self, mock_db):
        """When character is not found, uses 'Character #id' as fallback name."""
        mock_db.execute = AsyncMock(side_effect=[
            _make_all_result([(99, 5)]),                       # grouped query
            _make_scalar_one_or_none_result(None),             # Character not found
        ])

        result = await get_top_characters(mock_db, limit=10)

        assert len(result) == 1
        assert result[0].character_id == 99
        assert result[0].character_name == "Character #99"
        assert result[0].recognition_count == 5

    @pytest.mark.unit
    async def test_returns_empty_list_when_no_data(self, mock_db):
        """Returns empty list when there are no recognition logs."""
        mock_db.execute = AsyncMock(side_effect=[
            _make_all_result([]),
        ])

        result = await get_top_characters(mock_db, limit=10)

        assert result == []
