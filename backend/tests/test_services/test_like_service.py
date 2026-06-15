"""
Unit tests for like_service.py

Tests toggle_like() and get_post_likes() using mocked database sessions.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.like import Like
from app.models.post import Post
from app.schemas.post import UserBrief
from app.services.like_service import get_post_likes, toggle_like


# ── Test Fixtures ──


@pytest.fixture
def other_user_post_orm() -> Post:
    """A Post owned by another user (user_id=2)."""
    return Post(
        id=1,
        user_id=2,
        content="Post from another user",
        like_count=0,
        image_urls=[],
        tags=[],
    )


@pytest.fixture
def self_post_orm() -> Post:
    """A Post owned by the current test user (user_id=1)."""
    return Post(
        id=2,
        user_id=1,
        content="My own post",
        like_count=0,
        image_urls=[],
        tags=[],
    )


@pytest.fixture
def existing_like_orm(test_user_orm, other_user_post_orm) -> Like:
    """An existing Like record for test_user on other_user's post."""
    return Like(id=1, user_id=test_user_orm.id, post_id=other_user_post_orm.id)


# ── Mock Helpers ──


def _configure_execute_sequence(mock_db, scalar_one_or_none_values):
    """Configure mock_db.execute to return a sequence of scalar_one_or_none results.

    Each entry in scalar_one_or_none_values corresponds to one call to
    mock_db.execute().
    """
    results = []
    for val in scalar_one_or_none_values:
        r = AsyncMock()
        r.scalar_one_or_none = MagicMock(return_value=val)
        r.scalar = MagicMock(return_value=val)
        r.all = MagicMock(return_value=[val] if val is not None else [])
        results.append(r)
    mock_db.execute.side_effect = results


# ── toggle_like Tests ──


class TestToggleLike:
    """Tests for toggle_like()."""

    @pytest.mark.unit
    async def test_toggle_like_create(self, mock_db, other_user_post_orm):
        """First toggle on a post creates a like → liked=True, like_count=1."""
        _configure_execute_sequence(mock_db, [other_user_post_orm, None])

        result = await toggle_like(mock_db, user_id=1, post_id=1)

        assert result["liked"] is True
        assert result["like_count"] == 1
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    @pytest.mark.unit
    async def test_toggle_like_delete(self, mock_db, other_user_post_orm, existing_like_orm):
        """Second toggle on the same post removes the like → liked=False, like_count=0."""
        other_user_post_orm.like_count = 1  # simulate one existing like
        # delete() must be async (conftest sets it as MagicMock)
        mock_db.delete = AsyncMock()
        _configure_execute_sequence(mock_db, [other_user_post_orm, existing_like_orm])

        result = await toggle_like(mock_db, user_id=1, post_id=1)

        assert result["liked"] is False
        assert result["like_count"] == 0
        mock_db.delete.assert_called_once_with(existing_like_orm)
        mock_db.flush.assert_awaited_once()
        # Verify no new like was added
        mock_db.add.assert_not_called()

    @pytest.mark.unit
    async def test_toggle_like_self(self, mock_db, self_post_orm):
        """Liking own post raises HTTPException(400)."""
        _configure_execute_sequence(mock_db, [self_post_orm])

        with pytest.raises(HTTPException) as exc:
            await toggle_like(mock_db, user_id=1, post_id=2)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.unit
    async def test_toggle_like_nonexistent_post(self, mock_db):
        """Liking a non-existent post raises HTTPException(404)."""
        _configure_execute_sequence(mock_db, [None])

        with pytest.raises(HTTPException) as exc:
            await toggle_like(mock_db, user_id=1, post_id=999)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND


# ── get_post_likes Tests ──


class TestGetPostLikes:
    """Tests for get_post_likes()."""

    @pytest.mark.unit
    async def test_get_post_likes_returns_users(self, mock_db, test_user_orm):
        """Returns a list of UserBrief objects for users who liked a post."""
        mock_exec_result = AsyncMock()
        mock_scalars_result = MagicMock()
        mock_scalars_result.all = MagicMock(return_value=[test_user_orm])
        mock_exec_result.scalars = MagicMock(return_value=mock_scalars_result)
        mock_db.execute.return_value = mock_exec_result

        result = await get_post_likes(mock_db, post_id=1)

        assert len(result) == 1
        assert isinstance(result[0], UserBrief)
        assert result[0].id == test_user_orm.id
        assert result[0].username == test_user_orm.username

    @pytest.mark.unit
    async def test_get_post_likes_empty(self, mock_db):
        """Returns an empty list when no likes exist for a post."""
        mock_exec_result = AsyncMock()
        mock_scalars_result = MagicMock()
        mock_scalars_result.all = MagicMock(return_value=[])
        mock_exec_result.scalars = MagicMock(return_value=mock_scalars_result)
        mock_db.execute.return_value = mock_exec_result

        result = await get_post_likes(mock_db, post_id=999)

        assert result == []
