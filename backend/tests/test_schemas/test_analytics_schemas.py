"""
Unit tests for Analytics Schemas

Tests validation, serialization, and edge cases for:
- AnalyticsOverview, DailyStats, TopCharacterItem

NOTE: Tests are self-contained and do not depend on conftest.py fixtures,
because the root conftest triggers app.database module-level engine creation
which is incompatible with SQLite. Run with: pytest --noconftest -m unit
"""

import json
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.analytics import AnalyticsOverview, DailyStats, TopCharacterItem


def _make_utcnow() -> datetime:
    """Return current UTC datetime (avoiding deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════
# AnalyticsOverview
# ══════════════════════════════════════════════════════════════════════════


class TestAnalyticsOverview:
    """Tests for AnalyticsOverview schema."""

    @pytest.mark.unit
    def test_construct_with_all_fields(self):
        """Should construct with all fields."""
        overview = AnalyticsOverview(
            total_users=1000,
            total_posts=500,
            total_recognitions=2500,
            total_likes=3500,
            active_users_today=120,
        )
        assert overview.total_users == 1000
        assert overview.total_posts == 500
        assert overview.total_recognitions == 2500
        assert overview.total_likes == 3500
        assert overview.active_users_today == 120

    @pytest.mark.unit
    def test_zero_values(self):
        """Should accept zero for all counts."""
        overview = AnalyticsOverview(
            total_users=0,
            total_posts=0,
            total_recognitions=0,
            total_likes=0,
            active_users_today=0,
        )
        assert overview.total_users == 0

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        overview = AnalyticsOverview(
            total_users=100,
            total_posts=50,
            total_recognitions=200,
            total_likes=300,
            active_users_today=15,
        )
        d = overview.model_dump()
        assert set(d.keys()) == {
            "total_users", "total_posts", "total_recognitions",
            "total_likes", "active_users_today",
        }

    @pytest.mark.unit
    def test_json_serialization(self):
        """Should produce valid JSON."""
        overview = AnalyticsOverview(
            total_users=10,
            total_posts=5,
            total_recognitions=20,
            total_likes=30,
            active_users_today=3,
        )
        json_str = overview.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["total_users"] == 10
        assert parsed["total_posts"] == 5

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required fields."""
        with pytest.raises(ValidationError):
            AnalyticsOverview()

    @pytest.mark.unit
    def test_not_from_attributes(self):
        """AnalyticsOverview should be a plain data model, not ORM-bound."""
        assert AnalyticsOverview.model_config.get("from_attributes") is not True


# ══════════════════════════════════════════════════════════════════════════
# DailyStats
# ══════════════════════════════════════════════════════════════════════════


class TestDailyStats:
    """Tests for DailyStats schema."""

    @pytest.mark.unit
    def test_construct_with_all_fields(self):
        """Should construct with all fields."""
        today = _make_utcnow()
        stats = DailyStats(
            date=today,
            new_users=10,
            new_posts=5,
            recognitions=20,
        )
        assert stats.date == today
        assert stats.new_users == 10
        assert stats.new_posts == 5
        assert stats.recognitions == 20

    @pytest.mark.unit
    def test_default_zero_values(self):
        """Count fields should default to 0."""
        today = _make_utcnow()
        stats = DailyStats(date=today)
        assert stats.new_users == 0
        assert stats.new_posts == 0
        assert stats.recognitions == 0

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        today = _make_utcnow()
        stats = DailyStats(date=today, new_users=5, new_posts=2, recognitions=7)
        d = stats.model_dump()
        assert set(d.keys()) == {"date", "new_users", "new_posts", "recognitions"}

    @pytest.mark.unit
    def test_json_serialization(self):
        """Should produce valid JSON with date as string."""
        today = _make_utcnow()
        stats = DailyStats(date=today, new_users=1, new_posts=0, recognitions=3)
        json_str = stats.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["new_users"] == 1
        assert parsed["new_posts"] == 0
        assert parsed["recognitions"] == 3
        assert "date" in parsed

    @pytest.mark.unit
    def test_accepts_date_obj(self):
        """Should accept a date object (not just datetime) for date field."""
        today = date.today()
        stats = DailyStats(date=today, new_users=1, new_posts=2, recognitions=3)
        # Pydantic v2 coerces date to datetime by default
        assert stats.date is not None
        assert isinstance(stats.date, datetime)

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required field."""
        with pytest.raises(ValidationError):
            DailyStats()


# ══════════════════════════════════════════════════════════════════════════
# TopCharacterItem
# ══════════════════════════════════════════════════════════════════════════


class TestTopCharacterItem:
    """Tests for TopCharacterItem schema."""

    @pytest.mark.unit
    def test_construct_with_all_fields(self):
        """Should construct with all fields."""
        item = TopCharacterItem(
            character_id=101,
            character_name="Goku",
            recognition_count=42,
        )
        assert item.character_id == 101
        assert item.character_name == "Goku"
        assert item.recognition_count == 42

    @pytest.mark.unit
    def test_zero_recognitions(self):
        """Should accept recognition_count of 0."""
        item = TopCharacterItem(
            character_id=102,
            character_name="Naruto",
            recognition_count=0,
        )
        assert item.recognition_count == 0

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        item = TopCharacterItem(
            character_id=201,
            character_name="Luffy",
            recognition_count=99,
        )
        d = item.model_dump()
        assert set(d.keys()) == {
            "character_id", "character_name", "recognition_count",
        }

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required fields."""
        with pytest.raises(ValidationError):
            TopCharacterItem()
