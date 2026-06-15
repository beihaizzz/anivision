"""
Unit tests for Like and Follow Schemas

Tests validation, serialization, and edge cases for:
- LikeResponse, LikeToggleResponse
- FollowResponse, FollowToggleResponse, FollowerListResponse, FollowingListResponse

NOTE: Tests are self-contained and do not depend on conftest.py fixtures,
because the root conftest triggers app.database module-level engine creation
which is incompatible with SQLite. Run with: pytest --noconftest -m unit
"""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.like import LikeResponse, LikeToggleResponse
from app.schemas.follow import (
    FollowResponse,
    FollowToggleResponse,
    FollowerListResponse,
    FollowingListResponse,
)
from app.schemas.post import UserBrief


def _make_utcnow() -> datetime:
    """Return current UTC datetime (avoiding deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════
# LikeResponse
# ══════════════════════════════════════════════════════════════════════════


class TestLikeResponse:
    """Tests for LikeResponse schema."""

    @pytest.mark.unit
    def test_construct_with_all_fields(self):
        """Should construct with all fields."""
        now = _make_utcnow()
        like = LikeResponse(id=1, user_id=10, post_id=20, created_at=now)
        assert like.id == 1
        assert like.user_id == 10
        assert like.post_id == 20
        assert like.created_at == now

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        now = _make_utcnow()
        like = LikeResponse(id=1, user_id=10, post_id=20, created_at=now)
        d = like.model_dump()
        assert set(d.keys()) == {"id", "user_id", "post_id", "created_at"}

    @pytest.mark.unit
    def test_json_serialization(self):
        """Should produce valid JSON."""
        now = _make_utcnow()
        like = LikeResponse(id=2, user_id=11, post_id=22, created_at=now)
        json_str = like.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["id"] == 2
        assert parsed["user_id"] == 11
        assert parsed["post_id"] == 22

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required fields."""
        with pytest.raises(ValidationError):
            LikeResponse()


# ══════════════════════════════════════════════════════════════════════════
# LikeToggleResponse
# ══════════════════════════════════════════════════════════════════════════


class TestLikeToggleResponse:
    """Tests for LikeToggleResponse schema."""

    @pytest.mark.unit
    def test_construct_with_both_fields(self):
        """Should construct with liked and like_count."""
        toggle = LikeToggleResponse(liked=True, like_count=42)
        assert toggle.liked is True
        assert toggle.like_count == 42

    @pytest.mark.unit
    def test_liked_false(self):
        """Should accept liked=False."""
        toggle = LikeToggleResponse(liked=False, like_count=10)
        assert toggle.liked is False
        assert toggle.like_count == 10

    @pytest.mark.unit
    def test_zero_like_count(self):
        """Should accept like_count of 0."""
        toggle = LikeToggleResponse(liked=False, like_count=0)
        assert toggle.like_count == 0

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        toggle = LikeToggleResponse(liked=True, like_count=5)
        d = toggle.model_dump()
        assert set(d.keys()) == {"liked", "like_count"}

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required fields."""
        with pytest.raises(ValidationError):
            LikeToggleResponse()


# ══════════════════════════════════════════════════════════════════════════
# FollowResponse
# ══════════════════════════════════════════════════════════════════════════


class TestFollowResponse:
    """Tests for FollowResponse schema."""

    @pytest.mark.unit
    def test_construct_with_all_fields(self):
        """Should construct with all fields."""
        now = _make_utcnow()
        follow = FollowResponse(id=1, follower_id=10, followed_id=20, created_at=now)
        assert follow.id == 1
        assert follow.follower_id == 10
        assert follow.followed_id == 20
        assert follow.created_at == now

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        now = _make_utcnow()
        follow = FollowResponse(id=1, follower_id=10, followed_id=20, created_at=now)
        d = follow.model_dump()
        assert set(d.keys()) == {"id", "follower_id", "followed_id", "created_at"}

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required fields."""
        with pytest.raises(ValidationError):
            FollowResponse()


# ══════════════════════════════════════════════════════════════════════════
# FollowToggleResponse
# ══════════════════════════════════════════════════════════════════════════


class TestFollowToggleResponse:
    """Tests for FollowToggleResponse schema."""

    @pytest.mark.unit
    def test_construct_following_true(self):
        """Should construct with following=True."""
        toggle = FollowToggleResponse(following=True)
        assert toggle.following is True

    @pytest.mark.unit
    def test_construct_following_false(self):
        """Should construct with following=False."""
        toggle = FollowToggleResponse(following=False)
        assert toggle.following is False

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        toggle = FollowToggleResponse(following=True)
        d = toggle.model_dump()
        assert set(d.keys()) == {"following"}

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required field."""
        with pytest.raises(ValidationError):
            FollowToggleResponse()


# ══════════════════════════════════════════════════════════════════════════
# FollowerListResponse
# ══════════════════════════════════════════════════════════════════════════


class TestFollowerListResponse:
    """Tests for FollowerListResponse schema."""

    @pytest.mark.unit
    def test_construct_with_items(self):
        """Should construct with list of UserBrief items."""
        user1 = UserBrief(id=1, username="alice")
        user2 = UserBrief(id=2, username="bob")
        response = FollowerListResponse(
            items=[user1, user2],
            total=2,
            page=1,
            size=20,
        )
        assert len(response.items) == 2
        assert response.items[0].username == "alice"
        assert response.items[1].username == "bob"
        assert response.total == 2
        assert response.page == 1
        assert response.size == 20

    @pytest.mark.unit
    def test_empty_items(self):
        """Should accept empty items list."""
        response = FollowerListResponse(items=[], total=0, page=1, size=20)
        assert response.items == []
        assert response.total == 0

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        user = UserBrief(id=1, username="alice")
        response = FollowerListResponse(
            items=[user], total=1, page=1, size=10
        )
        d = response.model_dump()
        assert set(d.keys()) == {"items", "total", "page", "size"}
        assert len(d["items"]) == 1
        assert d["items"][0]["username"] == "alice"

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required fields."""
        with pytest.raises(ValidationError):
            FollowerListResponse()


# ══════════════════════════════════════════════════════════════════════════
# FollowingListResponse
# ══════════════════════════════════════════════════════════════════════════


class TestFollowingListResponse:
    """Tests for FollowingListResponse schema."""

    @pytest.mark.unit
    def test_construct_with_items(self):
        """Should construct with list of UserBrief items."""
        user1 = UserBrief(id=1, username="charlie")
        user2 = UserBrief(id=2, username="dave")
        response = FollowingListResponse(
            items=[user1, user2],
            total=2,
            page=1,
            size=20,
        )
        assert len(response.items) == 2
        assert response.items[0].username == "charlie"
        assert response.items[1].username == "dave"
        assert response.total == 2
        assert response.page == 1
        assert response.size == 20

    @pytest.mark.unit
    def test_empty_items(self):
        """Should accept empty items list."""
        response = FollowingListResponse(items=[], total=0, page=1, size=20)
        assert response.items == []
        assert response.total == 0

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict correctly."""
        user = UserBrief(id=1, username="charlie")
        response = FollowingListResponse(
            items=[user], total=1, page=1, size=15
        )
        d = response.model_dump()
        assert set(d.keys()) == {"items", "total", "page", "size"}
        assert d["items"][0]["username"] == "charlie"

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required fields."""
        with pytest.raises(ValidationError):
            FollowingListResponse()
