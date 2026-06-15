"""
Tests for likes router endpoints using FastAPI TestClient with mocked dependencies.

Tests cover:
- POST /api/posts/{id}/like — Toggle like (requires auth)
- GET  /api/posts/{id}/likes — Get likers (public)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user


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
# Toggle Like Endpoint  POST /api/posts/{id}/like
# ══════════════════════════════════════════════════════════════════════════


class TestToggleLikeEndpoint:
    """Tests for POST /api/posts/{id}/like."""

    @pytest.mark.unit
    def test_like_post(self, client, app, mock_db, test_user_orm):
        """POST with auth returns 200 and {liked, like_count}."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        # First execute: post existence check
        post_mock = MagicMock()
        post_mock.id = 1
        post_mock.user_id = 99  # different from current user (id=1)
        post_mock.like_count = 5

        first_result = AsyncMock()
        first_result.scalar_one_or_none = MagicMock(return_value=post_mock)

        # Second execute: existing like check → None (no existing like)
        second_result = AsyncMock()
        second_result.scalar_one_or_none = MagicMock(return_value=None)

        mock_db.execute.side_effect = [first_result, second_result]
        mock_db.flush = AsyncMock()

        response = client.post("/api/posts/1/like")

        assert response.status_code == 200
        body = response.json()
        assert body["liked"] is True
        assert body["like_count"] == 6  # incremented from 5

    @pytest.mark.unit
    def test_unlike_post(self, client, app, mock_db, test_user_orm):
        """POST twice → second returns liked=false."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        # First execute: post existence check
        post_mock = MagicMock()
        post_mock.id = 1
        post_mock.user_id = 99
        post_mock.like_count = 5

        first_result = AsyncMock()
        first_result.scalar_one_or_none = MagicMock(return_value=post_mock)

        # Second execute: existing like found
        existing_like = MagicMock()
        existing_like.id = 1
        existing_like.user_id = test_user_orm.id
        existing_like.post_id = 1

        second_result = AsyncMock()
        second_result.scalar_one_or_none = MagicMock(return_value=existing_like)

        mock_db.execute.side_effect = [first_result, second_result]
        mock_db.flush = AsyncMock()
        mock_db.delete = AsyncMock()

        response = client.post("/api/posts/1/like")

        assert response.status_code == 200
        body = response.json()
        assert body["liked"] is False
        assert body["like_count"] == 4  # decremented from 5

    @pytest.mark.unit
    def test_requires_auth(self, client):
        """POST without token returns 401."""
        response = client.post("/api/posts/1/like")
        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# Get Likes Endpoint  GET /api/posts/{id}/likes
# ══════════════════════════════════════════════════════════════════════════


class TestGetLikesEndpoint:
    """Tests for GET /api/posts/{id}/likes (public)."""

    @pytest.mark.unit
    def test_get_likes(self, client, app, mock_db):
        """GET returns 200 with a list of likers."""
        _override_db(app, mock_db)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_result.scalar = MagicMock(return_value=None)
        mock_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )
        mock_db.execute.return_value = mock_result

        response = client.get("/api/posts/1/likes")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
