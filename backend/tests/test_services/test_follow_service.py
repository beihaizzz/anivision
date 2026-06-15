"""
Unit tests for follow_service.py

Tests toggle_follow(), get_user_followers(), and get_user_following()
using mocked database sessions.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.follow import Follow
from app.models.user import User
from app.schemas.follow import FollowerListResponse, FollowingListResponse
from app.schemas.post import UserBrief
from app.services.follow_service import (
    get_user_followers,
    get_user_following,
    toggle_follow,
)


# ── Test Fixtures ──


@pytest.fixture
def other_user_orm() -> User:
    """Another user for follow tests (user_id=2)."""
    return User(
        id=2,
        username="otheruser",
        email="other@example.com",
        password_hash="does_not_matter",
        avatar_url="https://example.com/other.png",
        role="user",
    )


@pytest.fixture
def existing_follow_orm(test_user_orm, other_user_orm) -> Follow:
    """An existing Follow record (test_user follows other_user)."""
    return Follow(id=1, follower_id=test_user_orm.id, followed_id=other_user_orm.id)


# ── Mock Helpers ──


def _configure_execute_sequence(mock_db, scalar_one_or_none_values):
    """Configure mock_db.execute to return a sequence of scalar_one_or_none results."""
    results = []
    for val in scalar_one_or_none_values:
        r = AsyncMock()
        r.scalar_one_or_none = MagicMock(return_value=val)
        r.scalar = MagicMock(return_value=val)
        r.all = MagicMock(return_value=[val] if val is not None else [])
        results.append(r)
    mock_db.execute.side_effect = results


# ── toggle_follow Tests ──


class TestToggleFollow:
    """Tests for toggle_follow()."""

    @pytest.mark.unit
    async def test_toggle_follow_create(self, mock_db, other_user_orm):
        """First toggle follows a user → following=True."""
        _configure_execute_sequence(mock_db, [other_user_orm, None])

        result = await toggle_follow(mock_db, follower_id=1, followed_id=2)

        assert result["following"] is True
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    @pytest.mark.unit
    async def test_toggle_follow_delete(self, mock_db, other_user_orm, existing_follow_orm):
        """Second toggle unfollows → following=False."""
        # delete() must be async (conftest sets it as MagicMock)
        mock_db.delete = AsyncMock()
        _configure_execute_sequence(mock_db, [other_user_orm, existing_follow_orm])

        result = await toggle_follow(mock_db, follower_id=1, followed_id=2)

        assert result["following"] is False
        mock_db.delete.assert_called_once_with(existing_follow_orm)
        mock_db.flush.assert_awaited_once()
        mock_db.add.assert_not_called()

    @pytest.mark.unit
    async def test_toggle_follow_self(self, mock_db):
        """Self-follow raises HTTPException(400)."""
        with pytest.raises(HTTPException) as exc:
            await toggle_follow(mock_db, follower_id=1, followed_id=1)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        # No DB query should have been made
        mock_db.execute.assert_not_called()

    @pytest.mark.unit
    async def test_toggle_follow_nonexistent_user(self, mock_db):
        """Following a non-existent user raises HTTPException(404)."""
        _configure_execute_sequence(mock_db, [None])

        with pytest.raises(HTTPException) as exc:
            await toggle_follow(mock_db, follower_id=1, followed_id=999)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND


# ── get_user_followers Tests ──


class TestGetUserFollowers:
    """Tests for get_user_followers()."""

    @pytest.mark.unit
    async def test_get_user_followers_returns_followers(self, mock_db, test_user_orm):
        """Returns paginated list of followers for a user."""
        # First execute = count query, second execute = list query
        mock_count_result = AsyncMock()
        mock_count_result.scalar = MagicMock(return_value=1)
        mock_list_result = AsyncMock()
        mock_scalars_result = MagicMock()
        mock_scalars_result.all = MagicMock(return_value=[test_user_orm])
        mock_list_result.scalars = MagicMock(return_value=mock_scalars_result)
        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await get_user_followers(mock_db, user_id=2, page=1, size=20)

        assert isinstance(result, FollowerListResponse)
        assert result.total == 1
        assert result.page == 1
        assert result.size == 20
        assert len(result.items) == 1
        assert isinstance(result.items[0], UserBrief)
        assert result.items[0].id == test_user_orm.id
        assert result.items[0].username == test_user_orm.username

    @pytest.mark.unit
    async def test_get_user_followers_empty(self, mock_db):
        """Returns empty paginated result when user has no followers."""
        mock_count_result = AsyncMock()
        mock_count_result.scalar = MagicMock(return_value=0)
        mock_list_result = AsyncMock()
        mock_scalars_result = MagicMock()
        mock_scalars_result.all = MagicMock(return_value=[])
        mock_list_result.scalars = MagicMock(return_value=mock_scalars_result)
        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await get_user_followers(mock_db, user_id=999, page=1, size=20)

        assert result.total == 0
        assert result.items == []


# ── get_user_following Tests ──


class TestGetUserFollowing:
    """Tests for get_user_following()."""

    @pytest.mark.unit
    async def test_get_user_following_returns_followed(self, mock_db, test_user_orm):
        """Returns paginated list of users being followed."""
        mock_count_result = AsyncMock()
        mock_count_result.scalar = MagicMock(return_value=1)
        mock_list_result = AsyncMock()
        mock_scalars_result = MagicMock()
        mock_scalars_result.all = MagicMock(return_value=[test_user_orm])
        mock_list_result.scalars = MagicMock(return_value=mock_scalars_result)
        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await get_user_following(mock_db, user_id=1, page=1, size=20)

        assert isinstance(result, FollowingListResponse)
        assert result.total == 1
        assert result.page == 1
        assert result.size == 20
        assert len(result.items) == 1
        assert isinstance(result.items[0], UserBrief)
        assert result.items[0].id == test_user_orm.id
        assert result.items[0].username == test_user_orm.username

    @pytest.mark.unit
    async def test_get_user_following_empty(self, mock_db):
        """Returns empty paginated result when user follows nobody."""
        mock_count_result = AsyncMock()
        mock_count_result.scalar = MagicMock(return_value=0)
        mock_list_result = AsyncMock()
        mock_scalars_result = MagicMock()
        mock_scalars_result.all = MagicMock(return_value=[])
        mock_list_result.scalars = MagicMock(return_value=mock_scalars_result)
        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await get_user_following(mock_db, user_id=999, page=1, size=20)

        assert result.total == 0
        assert result.items == []
