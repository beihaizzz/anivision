"""
Tests for follows router endpoints using FastAPI TestClient with mocked dependencies.

Tests cover:
- POST /api/users/{id}/follow        — Toggle follow (requires auth)
- GET  /api/users/{id}/followers     — Get followers (public)
- GET  /api/users/{id}/following     — Get following (public)
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
# Toggle Follow Endpoint  POST /api/users/{id}/follow
# ══════════════════════════════════════════════════════════════════════════


class TestToggleFollowEndpoint:
    """Tests for POST /api/users/{id}/follow."""

    @pytest.mark.unit
    def test_follow_user(self, client, app, mock_db, test_user_orm):
        """POST with auth returns 200 and {following: true}."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        # First execute: target user exists
        target_user = MagicMock()
        target_user.id = 2
        target_user.username = "targetuser"

        first_result = AsyncMock()
        first_result.scalar_one_or_none = MagicMock(return_value=target_user)

        # Second execute: no existing follow
        second_result = AsyncMock()
        second_result.scalar_one_or_none = MagicMock(return_value=None)

        mock_db.execute.side_effect = [first_result, second_result]
        mock_db.flush = AsyncMock()

        response = client.post("/api/users/2/follow")

        assert response.status_code == 200
        body = response.json()
        assert body["following"] is True

    @pytest.mark.unit
    def test_unfollow_user(self, client, app, mock_db, test_user_orm):
        """POST twice → second returns {following: false}."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        # First execute: target user exists
        target_user = MagicMock()
        target_user.id = 2

        first_result = AsyncMock()
        first_result.scalar_one_or_none = MagicMock(return_value=target_user)

        # Second execute: existing follow found
        existing_follow = MagicMock()
        existing_follow.id = 1
        existing_follow.follower_id = test_user_orm.id
        existing_follow.followed_id = 2

        second_result = AsyncMock()
        second_result.scalar_one_or_none = MagicMock(return_value=existing_follow)

        mock_db.execute.side_effect = [first_result, second_result]
        mock_db.flush = AsyncMock()
        mock_db.delete = AsyncMock()

        response = client.post("/api/users/2/follow")

        assert response.status_code == 200
        body = response.json()
        assert body["following"] is False

    @pytest.mark.unit
    def test_requires_auth(self, client):
        """POST without token returns 401."""
        response = client.post("/api/users/2/follow")
        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# Get Followers Endpoint  GET /api/users/{id}/followers
# ══════════════════════════════════════════════════════════════════════════


class TestGetFollowersEndpoint:
    """Tests for GET /api/users/{id}/followers (public)."""

    @pytest.mark.unit
    def test_get_followers(self, client, app, mock_db):
        """GET returns 200 with a paginated follower list."""
        _override_db(app, mock_db)

        # First execute: count query
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=5)
        count_result.scalar_one_or_none = MagicMock(return_value=None)

        # Second execute: data query
        data_result = AsyncMock()
        data_result.scalar = MagicMock(return_value=None)
        data_result.scalar_one_or_none = MagicMock(return_value=None)
        data_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )

        mock_db.execute.side_effect = [count_result, data_result]

        response = client.get("/api/users/1/followers")

        assert response.status_code == 200
        body = response.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "size" in body
        assert body["total"] == 5
        assert body["page"] == 1
        assert body["size"] == 20


# ══════════════════════════════════════════════════════════════════════════
# Get Following Endpoint  GET /api/users/{id}/following
# ══════════════════════════════════════════════════════════════════════════


class TestGetFollowingEndpoint:
    """Tests for GET /api/users/{id}/following (public)."""

    @pytest.mark.unit
    def test_get_following(self, client, app, mock_db):
        """GET returns 200 with a paginated following list."""
        _override_db(app, mock_db)

        # First execute: count query
        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=3)
        count_result.scalar_one_or_none = MagicMock(return_value=None)

        # Second execute: data query
        data_result = AsyncMock()
        data_result.scalar = MagicMock(return_value=None)
        data_result.scalar_one_or_none = MagicMock(return_value=None)
        data_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )

        mock_db.execute.side_effect = [count_result, data_result]

        response = client.get("/api/users/1/following")

        assert response.status_code == 200
        body = response.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "size" in body
        assert body["total"] == 3
        assert body["page"] == 1
        assert body["size"] == 20
