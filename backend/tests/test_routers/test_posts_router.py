"""
Tests for posts & comments router endpoints using FastAPI TestClient with mocked dependencies.

Tests cover all eight endpoints:
- GET    /api/posts                         — list posts (public)
- POST   /api/posts                         — create post (auth)
- GET    /api/posts/{post_id}               — get post (public)
- PUT    /api/posts/{post_id}               — update post (auth)
- DELETE /api/posts/{post_id}               — delete post (auth)
- GET    /api/posts/{post_id}/comments      — list comments (public)
- POST   /api/posts/{post_id}/comments      — create comment (auth)
- DELETE /api/posts/comments/{comment_id}   — delete comment (auth)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.post import (
    CommentListResponse,
    CommentResponse,
    PostListResponse,
    PostResponse,
    UserBrief,
)


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
# Mock Object Factories
# ══════════════════════════════════════════════════════════════════════════


def _mock_user_brief(user_id=1, username="testuser", avatar_url="https://example.com/avatar.png"):
    """Return a UserBrief dict ready for response validation."""
    return UserBrief(id=user_id, username=username, avatar_url=avatar_url)


def _mock_post_response(
    post_id=1,
    user_id=1,
    username="testuser",
    content="Test post content",
    image_urls=None,
    tags=None,
    like_count=0,
    comment_count=0,
    created_at=None,
):
    """Return a PostResponse for list/get responses."""
    if created_at is None:
        created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return PostResponse(
        id=post_id,
        content=content,
        image_urls=image_urls or [],
        tags=tags or [],
        like_count=like_count,
        comment_count=comment_count,
        user=UserBrief(id=user_id, username=username, avatar_url="https://example.com/avatar.png"),
        created_at=created_at,
    )


def _mock_comment_response(
    comment_id=1,
    user_id=1,
    username="testuser",
    content="Test comment",
    parent_id=None,
    replies=None,
    created_at=None,
):
    """Return a CommentResponse for list/create responses."""
    if created_at is None:
        created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return CommentResponse(
        id=comment_id,
        content=content,
        user=UserBrief(id=user_id, username=username, avatar_url="https://example.com/avatar.png"),
        parent_id=parent_id,
        replies=replies or [],
        created_at=created_at,
    )


def _mock_paginated_response(items, total=None, page=1, size=20):
    """Return a PaginatedResponse-like object."""
    return PaginatedResponse(
        items=items,
        total=total if total is not None else len(items),
        page=page,
        size=size,
    )


# ══════════════════════════════════════════════════════════════════════════
# 1. TestListPosts  GET /api/posts
# ══════════════════════════════════════════════════════════════════════════


class TestListPosts:
    """Tests for GET /api/posts (public, paginated)."""

    @pytest.mark.unit
    def test_returns_paginated_response(self, client, app, mock_db):
        """GET /api/posts returns 200 with items/total/page/size."""
        _override_db(app, mock_db)
        posts = [_mock_post_response(post_id=1), _mock_post_response(post_id=2)]
        paginated = _mock_paginated_response(posts, total=2, page=1, size=20)

        with patch("app.routers.posts.list_posts", new=AsyncMock(return_value=paginated)):
            response = client.get("/api/posts")

        assert response.status_code == 200
        body = response.json()
        assert body["items"] == [p.model_dump(mode="json") for p in posts]
        assert body["total"] == 2
        assert body["page"] == 1
        assert body["size"] == 20

    @pytest.mark.unit
    def test_public_no_auth_required(self, client, app, mock_db):
        """GET /api/posts without auth returns 200 (public endpoint)."""
        _override_db(app, mock_db)
        paginated = _mock_paginated_response([], total=0, page=1, size=20)

        with patch("app.routers.posts.list_posts", new=AsyncMock(return_value=paginated)):
            # No auth dependency override → no auth header
            response = client.get("/api/posts")

        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0

    @pytest.mark.unit
    def test_respects_pagination_params(self, client, app, mock_db):
        """GET /api/posts?page=2&size=5 passes params to service."""
        _override_db(app, mock_db)
        paginated = _mock_paginated_response([], total=0, page=2, size=5)
        mock_list = AsyncMock(return_value=paginated)

        with patch("app.routers.posts.list_posts", new=mock_list):
            response = client.get("/api/posts?page=2&size=5")

        assert response.status_code == 200
        mock_list.assert_called_once()
        # Check that page/size kwargs were passed
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs.get("page") == 2
        assert call_kwargs.get("size") == 5


# ══════════════════════════════════════════════════════════════════════════
# 2. TestCreatePost  POST /api/posts
# ══════════════════════════════════════════════════════════════════════════


class TestCreatePost:
    """Tests for POST /api/posts (auth required)."""

    @pytest.mark.unit
    def test_requires_auth(self, client, app, mock_db):
        """POST /api/posts without token returns 401."""
        _override_db(app, mock_db)
        # No auth override → FastAPI OAuth2PasswordBearer expects Bearer token
        response = client.post("/api/posts", json={"content": "Some content"})

        assert response.status_code == 401

    @pytest.mark.unit
    def test_creates_post(self, client, app, mock_db, test_user_orm):
        """POST /api/posts with valid data returns 201 + PostResponse."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        post_resp = _mock_post_response(
            post_id=42,
            user_id=test_user_orm.id,
            username=test_user_orm.username,
            content="My first post",
            tags=["anime", "review"],
        )

        with patch("app.routers.posts.create_post", new=AsyncMock(return_value=post_resp)):
            response = client.post(
                "/api/posts",
                json={"content": "My first post", "tags": ["anime", "review"]},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 42
        assert body["content"] == "My first post"
        assert body["tags"] == ["anime", "review"]
        assert body["user"]["id"] == test_user_orm.id
        assert body["user"]["username"] == test_user_orm.username
        assert "image_urls" in body
        assert "comment_count" in body
        assert "like_count" in body
        assert "created_at" in body
        assert "password_hash" not in body

    @pytest.mark.unit
    def test_empty_content_rejected(self, client, app, mock_db, test_user_orm):
        """POST /api/posts with empty content returns 422."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        # Pydantic validation happens before the router handler
        response = client.post("/api/posts", json={"content": ""})

        assert response.status_code == 422

    @pytest.mark.unit
    def test_non_authenticated_rejected(self, client, app, mock_db):
        """POST /api/posts without auth returns 401."""
        _override_db(app, mock_db)

        response = client.post("/api/posts", json={"content": "Some content"})

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# 3. TestGetPost  GET /api/posts/{post_id}
# ══════════════════════════════════════════════════════════════════════════


class TestGetPost:
    """Tests for GET /api/posts/{post_id} (public)."""

    @pytest.mark.unit
    def test_returns_post(self, client, app, mock_db):
        """GET /api/posts/{id} returns 200 + PostResponse."""
        _override_db(app, mock_db)

        post_resp = _mock_post_response(post_id=1, content="Single post")

        with patch("app.routers.posts.get_post", new=AsyncMock(return_value=post_resp)):
            response = client.get("/api/posts/1")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["content"] == "Single post"
        assert body["user"]["id"] == 1

    @pytest.mark.unit
    def test_404_for_nonexistent(self, client, app, mock_db):
        """GET /api/posts/999 returns 404 when post not found."""
        _override_db(app, mock_db)

        mock_get = AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        )

        with patch("app.routers.posts.get_post", new=mock_get):
            response = client.get("/api/posts/999")

        assert response.status_code == 404

    @pytest.mark.unit
    def test_public_no_auth_required(self, client, app, mock_db):
        """GET /api/posts/{id} without auth returns 200 (public endpoint)."""
        _override_db(app, mock_db)

        post_resp = _mock_post_response(post_id=1, content="Public post")

        with patch("app.routers.posts.get_post", new=AsyncMock(return_value=post_resp)):
            response = client.get("/api/posts/1")

        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# 4. TestUpdatePost  PUT /api/posts/{post_id}
# ══════════════════════════════════════════════════════════════════════════


class TestUpdatePost:
    """Tests for PUT /api/posts/{post_id} (auth required, owner/admin only)."""

    @pytest.mark.unit
    def test_owner_can_update(self, client, app, mock_db, test_user_orm):
        """PUT /api/posts/{id} as owner returns 200."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        updated = _mock_post_response(post_id=1, content="Updated content", tags=["updated"])

        with patch("app.routers.posts.update_post", new=AsyncMock(return_value=updated)):
            response = client.put(
                "/api/posts/1",
                json={"content": "Updated content", "tags": ["updated"]},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["content"] == "Updated content"
        assert body["tags"] == ["updated"]

    @pytest.mark.unit
    def test_non_owner_rejected(self, client, app, mock_db, test_user_orm):
        """PUT /api/posts/{id} as non-owner returns 403."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        mock_update = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to edit this post",
            )
        )

        with patch("app.routers.posts.update_post", new=mock_update):
            response = client.put(
                "/api/posts/1",
                json={"content": "Hacked content"},
            )

        assert response.status_code == 403

    @pytest.mark.unit
    def test_requires_auth(self, client, app, mock_db):
        """PUT /api/posts/{id} without token returns 401."""
        _override_db(app, mock_db)

        response = client.put("/api/posts/1", json={"content": "New content"})

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# 5. TestDeletePost  DELETE /api/posts/{post_id}
# ══════════════════════════════════════════════════════════════════════════


class TestDeletePost:
    """Tests for DELETE /api/posts/{post_id} (auth required, owner/admin only)."""

    @pytest.mark.unit
    def test_owner_can_delete(self, client, app, mock_db, test_user_orm):
        """DELETE /api/posts/{id} as owner returns 204."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        with patch("app.routers.posts.delete_post", new=AsyncMock(return_value=None)):
            response = client.delete("/api/posts/1")

        assert response.status_code == 204
        assert response.content == b""  # No Content

    @pytest.mark.unit
    def test_admin_can_delete(self, client, app, mock_db, admin_user_orm):
        """DELETE /api/posts/{id} as admin returns 204."""
        _override_db(app, mock_db)
        _override_current_user(app, admin_user_orm)

        with patch("app.routers.posts.delete_post", new=AsyncMock(return_value=None)):
            response = client.delete("/api/posts/1")

        assert response.status_code == 204

    @pytest.mark.unit
    def test_non_owner_rejected(self, client, app, mock_db, test_user_orm):
        """DELETE /api/posts/{id} as non-owner returns 403."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        mock_delete = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this post",
            )
        )

        with patch("app.routers.posts.delete_post", new=mock_delete):
            response = client.delete("/api/posts/1")

        assert response.status_code == 403

    @pytest.mark.unit
    def test_requires_auth(self, client, app, mock_db):
        """DELETE /api/posts/{id} without token returns 401."""
        _override_db(app, mock_db)

        response = client.delete("/api/posts/1")

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# 6. TestCreateComment  POST /api/posts/{post_id}/comments
# ══════════════════════════════════════════════════════════════════════════


class TestCreateComment:
    """Tests for POST /api/posts/{post_id}/comments (auth required)."""

    @pytest.mark.unit
    def test_requires_auth(self, client, app, mock_db):
        """POST /api/posts/{id}/comments without token returns 401."""
        _override_db(app, mock_db)

        response = client.post(
            "/api/posts/1/comments",
            json={"content": "Nice post!"},
        )

        assert response.status_code == 401

    @pytest.mark.unit
    def test_creates_comment(self, client, app, mock_db, test_user_orm):
        """POST /api/posts/{id}/comments with valid data returns 201."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        comment_resp = _mock_comment_response(
            comment_id=10,
            user_id=test_user_orm.id,
            username=test_user_orm.username,
            content="Nice post!",
        )

        with patch("app.routers.posts.create_comment", new=AsyncMock(return_value=comment_resp)):
            response = client.post(
                "/api/posts/1/comments",
                json={"content": "Nice post!"},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 10
        assert body["content"] == "Nice post!"
        assert body["user"]["id"] == test_user_orm.id
        assert body["user"]["username"] == test_user_orm.username
        assert body["parent_id"] is None
        assert body["replies"] == []
        assert "created_at" in body

    @pytest.mark.unit
    def test_creates_reply_comment(self, client, app, mock_db, test_user_orm):
        """POST /api/posts/{id}/comments with parent_id creates a reply."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        comment_resp = _mock_comment_response(
            comment_id=11,
            user_id=test_user_orm.id,
            username=test_user_orm.username,
            content="I agree!",
            parent_id=10,
        )

        with patch("app.routers.posts.create_comment", new=AsyncMock(return_value=comment_resp)):
            response = client.post(
                "/api/posts/1/comments",
                json={"content": "I agree!", "parent_id": 10},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["content"] == "I agree!"
        assert body["parent_id"] == 10


# ══════════════════════════════════════════════════════════════════════════
# 7. TestGetComments  GET /api/posts/{post_id}/comments
# ══════════════════════════════════════════════════════════════════════════


class TestGetComments:
    """Tests for GET /api/posts/{post_id}/comments (public)."""

    @pytest.mark.unit
    def test_returns_comments(self, client, app, mock_db):
        """GET /api/posts/{id}/comments returns 200 with paginated comments."""
        _override_db(app, mock_db)

        comments = [
            _mock_comment_response(comment_id=1, content="First!"),
            _mock_comment_response(comment_id=2, content="Second!"),
        ]
        paginated = _mock_paginated_response(comments, total=2, page=1, size=20)

        with patch("app.routers.posts.get_comments", new=AsyncMock(return_value=paginated)):
            response = client.get("/api/posts/1/comments")

        assert response.status_code == 200
        body = response.json()
        assert body["items"] == [c.model_dump(mode="json") for c in comments]
        assert body["total"] == 2
        assert body["page"] == 1
        assert body["size"] == 20

    @pytest.mark.unit
    def test_public_no_auth_required(self, client, app, mock_db):
        """GET /api/posts/{id}/comments without auth returns 200 (public)."""
        _override_db(app, mock_db)

        paginated = _mock_paginated_response([], total=0, page=1, size=20)

        with patch("app.routers.posts.get_comments", new=AsyncMock(return_value=paginated)):
            response = client.get("/api/posts/1/comments")

        assert response.status_code == 200

    @pytest.mark.unit
    def test_empty_comments_list(self, client, app, mock_db):
        """GET /api/posts/{id}/comments with no comments returns empty items."""
        _override_db(app, mock_db)

        paginated = _mock_paginated_response([], total=0, page=1, size=20)

        with patch("app.routers.posts.get_comments", new=AsyncMock(return_value=paginated)):
            response = client.get("/api/posts/1/comments")

        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["total"] == 0


# ══════════════════════════════════════════════════════════════════════════
# 8. TestDeleteComment  DELETE /api/posts/comments/{comment_id}
# ══════════════════════════════════════════════════════════════════════════


class TestDeleteComment:
    """Tests for DELETE /api/posts/comments/{comment_id} (auth required, owner/admin only)."""

    @pytest.mark.unit
    def test_owner_can_delete(self, client, app, mock_db, test_user_orm):
        """DELETE /api/posts/comments/{id} as owner returns 204."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        with patch("app.routers.posts.delete_comment", new=AsyncMock(return_value=None)):
            response = client.delete("/api/posts/comments/10")

        assert response.status_code == 204

    @pytest.mark.unit
    def test_non_owner_rejected(self, client, app, mock_db, test_user_orm):
        """DELETE /api/posts/comments/{id} as non-owner returns 403."""
        _override_db(app, mock_db)
        _override_current_user(app, test_user_orm)

        mock_delete = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment",
            )
        )

        with patch("app.routers.posts.delete_comment", new=mock_delete):
            response = client.delete("/api/posts/comments/10")

        assert response.status_code == 403

    @pytest.mark.unit
    def test_admin_can_delete(self, client, app, mock_db, admin_user_orm):
        """DELETE /api/posts/comments/{id} as admin returns 204."""
        _override_db(app, mock_db)
        _override_current_user(app, admin_user_orm)

        with patch("app.routers.posts.delete_comment", new=AsyncMock(return_value=None)):
            response = client.delete("/api/posts/comments/10")

        assert response.status_code == 204

    @pytest.mark.unit
    def test_requires_auth(self, client, app, mock_db):
        """DELETE /api/posts/comments/{id} without token returns 401."""
        _override_db(app, mock_db)

        response = client.delete("/api/posts/comments/10")

        assert response.status_code == 401
