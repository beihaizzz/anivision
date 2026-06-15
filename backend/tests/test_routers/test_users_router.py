"""
Tests for users router endpoints.

Tests for:
- GET /api/users/{user_id}       — Public profile retrieval
- GET /api/users/{user_id}/posts — Paginated user posts
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.database import get_db


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


# ══════════════════════════════════════════════════════════════════════════
# GET /api/users/{user_id}
# ══════════════════════════════════════════════════════════════════════════


class TestGetUserProfile:
    """Tests for GET /api/users/{user_id}."""

    @pytest.mark.unit
    def test_returns_profile(self, client, app, mock_db):
        """200 with UserProfileResponse for existing user."""
        _override_db(app, mock_db)

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.avatar_url = "https://example.com/avatar.png"
        mock_user.bio = "Test bio"
        mock_user.role = "user"
        mock_user.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_result.scalar = MagicMock(side_effect=[5, 3, 10])  # follower, following, post counts
        mock_db.execute.return_value = mock_result

        response = client.get("/api/users/1")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["avatar_url"] == "https://example.com/avatar.png"
        assert data["bio"] == "Test bio"
        assert data["role"] == "user"
        assert data["follower_count"] == 5
        assert data["following_count"] == 3
        assert data["post_count"] == 10
        assert "created_at" in data
        # must not expose sensitive fields
        assert "email" not in data
        assert "password_hash" not in data

    @pytest.mark.unit
    def test_404_for_nonexistent(self, client, app, mock_db):
        """404 when user does not exist."""
        _override_db(app, mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        response = client.get("/api/users/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ══════════════════════════════════════════════════════════════════════════
# GET /api/users/{user_id}/posts
# ══════════════════════════════════════════════════════════════════════════


class TestGetUserPosts:
    """Tests for GET /api/users/{user_id}/posts."""

    @pytest.mark.unit
    def test_returns_posts(self, client, app, mock_db):
        """200 with paginated posts for existing user."""
        _override_db(app, mock_db)

        mock_user = MagicMock()
        mock_user.id = 1

        mock_post = MagicMock()
        mock_post.id = 10
        mock_post.content = "First post"
        mock_post.image_urls = []
        mock_post.tags = ["tag1"]
        mock_post.like_count = 3
        mock_post.comment_count = 1
        # user relationship
        mock_post.user = MagicMock()
        mock_post.user.id = 1
        mock_post.user.username = "testuser"
        mock_post.user.avatar_url = None
        mock_post.created_at = datetime(2025, 6, 1, tzinfo=timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_result.scalar = MagicMock(return_value=2)
        mock_result.scalars = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(return_value=[mock_post])
        mock_db.execute.return_value = mock_result

        response = client.get("/api/users/1/posts?page=1&size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["total"] == 2
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == 10
        assert data["items"][0]["content"] == "First post"

    @pytest.mark.unit
    def test_404_for_nonexistent_user(self, client, app, mock_db):
        """404 when user does not exist."""
        _override_db(app, mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        response = client.get("/api/users/999/posts")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.unit
    def test_default_pagination(self, client, app, mock_db):
        """Uses default page=1, size=20 when not specified."""
        _override_db(app, mock_db)

        mock_user = MagicMock()
        mock_user.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_result.scalar = MagicMock(return_value=0)
        mock_result.scalars = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(return_value=[])
        mock_db.execute.return_value = mock_result

        response = client.get("/api/users/1/posts")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.unit
    def test_empty_posts_list(self, client, app, mock_db):
        """200 with empty items for user who has no posts."""
        _override_db(app, mock_db)

        mock_user = MagicMock()
        mock_user.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_result.scalar = MagicMock(return_value=0)
        mock_result.scalars = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(return_value=[])
        mock_db.execute.return_value = mock_result

        response = client.get("/api/users/1/posts?page=1&size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
