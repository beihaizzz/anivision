"""
Unit tests for post_service.py

Tests Post CRUD operations using mocked database sessions from conftest.py.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdateRequest
from app.services.post_service import (
    create_post,
    delete_post,
    get_post,
    list_posts,
    update_post,
)


# ── Helpers ────────────────────────────────────────────────────────────

def _make_post(**overrides) -> Post:
    """Build a Post ORM instance with sensible defaults for testing."""
    defaults = dict(
        id=1,
        user_id=1,
        content="Hello AniVision!",
        image_urls=["https://img.example.com/1.png"],
        tags=["anime", "review"],
        like_count=0,
        comment_count=0,
        created_at=datetime(2025, 6, 1, 12, 0, 0),
    )
    defaults.update(overrides)
    post = Post(**defaults)
    # Attach user eagerly (mimics selectinload)
    if "user" not in overrides:
        post.user = User(
            id=defaults["user_id"],
            username="testuser",
            email="test@example.com",
            avatar_url="https://example.com/avatar.png",
        )
    return post


def _make_result(
    scalar_one_or_none=None,
    scalar_one=None,
    scalar=None,
    scalars_all=None,
):
    """Build a mock SQLAlchemy Result with configured return values."""
    result = AsyncMock()
    result.scalar_one_or_none = MagicMock(return_value=scalar_one_or_none)
    result.scalar_one = MagicMock(return_value=scalar_one)
    result.scalar = MagicMock(return_value=scalar)

    if scalars_all is not None:
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=scalars_all)
        result.scalars = MagicMock(return_value=mock_scalars)
    else:
        result.scalars = MagicMock()

    return result


def _configure_refresh(mock_db: AsyncMock) -> None:
    """Make mock_db.refresh set id/created_at on the passed object (like real DB)."""
    async def _refresh(obj):
        if not obj.id:
            obj.id = 1
        if not obj.created_at:
            obj.created_at = datetime(2025, 6, 1, 12, 0, 0)
    mock_db.refresh.side_effect = _refresh


# ── Tests ──────────────────────────────────────────────────────────────


class TestCreatePost:
    """Tests for create_post()."""

    @pytest.mark.unit
    async def test_create_post_returns_post_with_user_info(
        self, mock_db, test_user_orm
    ):
        """Creates a post, returns PostResponse with user info."""
        data = PostCreate(
            content="  Hello AniVision!  ",
            image_urls=["https://img.example.com/1.png"],
            tags=["anime"],
        )
        post = _make_post(content="Hello AniVision!", image_urls=["https://img.example.com/1.png"], tags=["anime"])
        post.user = test_user_orm

        _configure_refresh(mock_db)
        mock_db.execute.return_value = _make_result(scalar_one=post)

        result = await create_post(mock_db, user_id=1, data=data)

        assert isinstance(result, Post)
        assert result.content == "Hello AniVision!"
        assert result.image_urls == ["https://img.example.com/1.png"]
        assert result.tags == ["anime"]
        assert result.user_id == 1
        assert result.user is not None
        assert result.user.username == "testuser"

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()


class TestGetPost:
    """Tests for get_post()."""

    @pytest.mark.unit
    async def test_get_post_returns_post_with_correct_fields(
        self, mock_db, test_user_orm
    ):
        """Returns post with correct fields."""
        post = _make_post()
        post.user = test_user_orm

        mock_db.execute.return_value = _make_result(scalar_one_or_none=post)

        result = await get_post(mock_db, post_id=1)

        assert result.id == 1
        assert result.content == "Hello AniVision!"
        assert result.image_urls == ["https://img.example.com/1.png"]
        assert result.tags == ["anime", "review"]
        assert result.like_count == 0
        assert result.comment_count == 0
        assert result.user.username == "testuser"

    @pytest.mark.unit
    async def test_get_post_not_found_raises_404(self, mock_db):
        """Raises 404 when post does not exist."""
        mock_db.execute.return_value = _make_result(scalar_one_or_none=None)

        with pytest.raises(HTTPException) as exc:
            await get_post(mock_db, post_id=999)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Post not found" in exc.value.detail


class TestListPosts:
    """Tests for list_posts()."""

    @pytest.mark.unit
    async def test_list_posts_returns_paginated_results_newest_first(
        self, mock_db, test_user_orm
    ):
        """Returns paginated results, newest first."""
        post1 = _make_post(id=2, created_at=datetime(2025, 6, 2, 12, 0, 0))
        post1.user = test_user_orm
        post2 = _make_post(id=1, created_at=datetime(2025, 6, 1, 12, 0, 0))
        post2.user = test_user_orm

        # Two execute calls: count, then items. Use side_effect.
        count_result = _make_result(scalar=2)
        items_result = _make_result(scalars_all=[post1, post2])
        mock_db.execute.side_effect = [count_result, items_result]

        result = await list_posts(mock_db, page=1, size=20)

        assert result.total == 2
        assert result.page == 1
        assert result.size == 20
        assert len(result.items) == 2
        # Newest first
        assert result.items[0].id == 2
        assert result.items[1].id == 1

    @pytest.mark.unit
    async def test_list_posts_empty_returns_empty_items(self, mock_db):
        """Returns empty items when no posts exist."""
        count_result = _make_result(scalar=0)
        items_result = _make_result(scalars_all=[])
        mock_db.execute.side_effect = [count_result, items_result]

        result = await list_posts(mock_db, page=1, size=20)

        assert result.total == 0
        assert len(result.items) == 0


class TestUpdatePost:
    """Tests for update_post()."""

    @pytest.mark.unit
    async def test_update_post_owner_can_update(self, mock_db, test_user_orm):
        """Owner can update their own post."""
        post = _make_post()
        post.user = test_user_orm
        data = PostUpdateRequest(content="Updated content", tags=["updated"])

        # First execute: get_post (scalar_one_or_none), then implicit refresh via flush
        mock_db.execute.return_value = _make_result(scalar_one_or_none=post)
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await update_post(mock_db, post_id=1, user_id=1, data=data)

        assert result.content == "Updated content"
        assert result.tags == ["updated"]
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.unit
    async def test_update_post_not_owner_raises_403(self, mock_db, test_user_orm):
        """Non-owner raises 403 Forbidden."""
        post = _make_post(user_id=2)  # owned by user 2
        post.user = test_user_orm
        data = PostUpdateRequest(content="Hacked!")

        mock_db.execute.return_value = _make_result(scalar_one_or_none=post)

        with pytest.raises(HTTPException) as exc:
            await update_post(mock_db, post_id=1, user_id=1, data=data)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in exc.value.detail

    @pytest.mark.unit
    async def test_update_post_admin_can_update_any(self, mock_db, test_user_orm):
        """Admin can update any post."""
        post = _make_post(user_id=99)  # not admin's post
        post.user = test_user_orm
        data = PostUpdateRequest(content="Admin edit")

        mock_db.execute.return_value = _make_result(scalar_one_or_none=post)
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await update_post(
            mock_db, post_id=1, user_id=2, data=data, user_role="admin"
        )

        assert result.content == "Admin edit"


class TestDeletePost:
    """Tests for delete_post()."""

    @pytest.mark.unit
    async def test_delete_post_owner_can_delete(self, mock_db, test_user_orm):
        """Owner can delete their own post."""
        post = _make_post()
        post.user = test_user_orm

        mock_db.execute.return_value = _make_result(scalar_one_or_none=post)
        mock_db.flush = AsyncMock()
        mock_db.delete = MagicMock()

        await delete_post(mock_db, post_id=1, user_id=1)

        mock_db.delete.assert_called_once_with(post)
        mock_db.flush.assert_awaited_once()

    @pytest.mark.unit
    async def test_delete_post_admin_can_delete_anyones_post(
        self, mock_db, test_user_orm
    ):
        """Admin can delete anyone's post."""
        post = _make_post(user_id=99)
        post.user = test_user_orm

        mock_db.execute.return_value = _make_result(scalar_one_or_none=post)
        mock_db.flush = AsyncMock()
        mock_db.delete = MagicMock()

        await delete_post(mock_db, post_id=1, user_id=1, user_role="admin")

        mock_db.delete.assert_called_once_with(post)

    @pytest.mark.unit
    async def test_delete_post_not_owner_raises_403(self, mock_db, test_user_orm):
        """Non-owner non-admin raises 403 Forbidden."""
        post = _make_post(user_id=2)
        post.user = test_user_orm

        mock_db.execute.return_value = _make_result(scalar_one_or_none=post)

        with pytest.raises(HTTPException) as exc:
            await delete_post(mock_db, post_id=1, user_id=1)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in exc.value.detail
