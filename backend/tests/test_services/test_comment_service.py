"""
Unit tests for comment_service.py

Tests Comment CRUD operations using mocked database sessions from conftest.py.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.post import CommentCreate
from app.services.comment_service import (
    create_comment,
    delete_comment,
    get_comments,
)


# ── Helpers ────────────────────────────────────────────────────────────

def _make_user(**overrides) -> User:
    """Build a User ORM instance with sensible defaults."""
    defaults = dict(
        id=1,
        username="testuser",
        email="test@example.com",
        avatar_url="https://example.com/avatar.png",
    )
    defaults.update(overrides)
    return User(**defaults)


def _make_post(**overrides) -> Post:
    """Build a Post ORM instance for comment tests."""
    defaults = dict(
        id=1,
        user_id=1,
        content="Test post content",
        image_urls=[],
        tags=[],
        like_count=0,
        comment_count=0,
        created_at=datetime(2025, 6, 1, 12, 0, 0),
    )
    defaults.update(overrides)
    return Post(**defaults)


def _make_comment(**overrides) -> Comment:
    """Build a Comment ORM instance with sensible defaults."""
    defaults = dict(
        id=1,
        post_id=1,
        user_id=1,
        content="Great post!",
        parent_id=None,
        created_at=datetime(2025, 6, 2, 12, 0, 0),
    )
    defaults.update(overrides)
    comment = Comment(**defaults)
    if "user" not in overrides:
        comment.user = _make_user(id=defaults["user_id"])
    return comment


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
    """Make mock_db.refresh set id/created_at on the passed object."""
    async def _refresh(obj):
        if not obj.id:
            obj.id = 1
        if not obj.created_at:
            obj.created_at = datetime(2025, 6, 2, 12, 0, 0)
    mock_db.refresh.side_effect = _refresh


# ── Tests ──────────────────────────────────────────────────────────────


class TestCreateComment:
    """Tests for create_comment()."""

    @pytest.mark.unit
    async def test_create_comment_creates_top_level_comment_on_post(
        self, mock_db, test_user_orm
    ):
        """Creates a top-level comment on a post."""
        data = CommentCreate(content="  Nice post!  ")
        post = _make_post()
        comment = _make_comment(content="Nice post!")

        _configure_refresh(mock_db)

        # Three execute calls: verify post, check parent (none), then... 
        # Actually, the service will also do execute for parent check if parent_id is None, it shouldn't.
        # Let me trace through create_comment:
        # 1. select(Post).where(Post.id == post_id) → scalar_one_or_none=post
        # 2. if parent_id is not None: select(Comment) → skipped
        # That's just 1 execute call.
        mock_db.execute.return_value = _make_result(scalar_one_or_none=post)

        result = await create_comment(mock_db, post_id=1, user_id=1, data=data)

        assert isinstance(result, Comment)
        assert result.content == "Nice post!"
        assert result.post_id == 1
        assert result.user_id == 1
        assert result.parent_id is None

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.unit
    async def test_create_reply_creates_nested_reply_with_parent_id(
        self, mock_db, test_user_orm
    ):
        """Creates a nested reply with parent_id set."""
        data = CommentCreate(content="I agree!", parent_id=1)
        post = _make_post(comment_count=1)
        parent_comment = _make_comment(id=1, parent_id=None)  # top-level, valid parent

        _configure_refresh(mock_db)

        # Three execute calls:
        # 1. Verify post exists → post
        # 2. Verify parent comment exists and check nesting → parent_comment
        mock_db.execute.side_effect = [
            _make_result(scalar_one_or_none=post),
            _make_result(scalar_one_or_none=parent_comment),
        ]

        result = await create_comment(mock_db, post_id=1, user_id=1, data=data)

        assert result.parent_id == 1
        assert result.content == "I agree!"

    @pytest.mark.unit
    async def test_create_comment_post_not_found_raises_404(self, mock_db):
        """Raises 404 when post does not exist."""
        data = CommentCreate(content="Comment on nothing")

        mock_db.execute.return_value = _make_result(scalar_one_or_none=None)

        with pytest.raises(HTTPException) as exc:
            await create_comment(mock_db, post_id=999, user_id=1, data=data)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Post not found" in exc.value.detail

    @pytest.mark.unit
    async def test_create_comment_parent_not_found_raises_404(self, mock_db):
        """Raises 404 when parent comment does not exist."""
        data = CommentCreate(content="Reply to nothing", parent_id=999)
        post = _make_post()

        mock_db.execute.side_effect = [
            _make_result(scalar_one_or_none=post),
            _make_result(scalar_one_or_none=None),
        ]

        with pytest.raises(HTTPException) as exc:
            await create_comment(mock_db, post_id=1, user_id=1, data=data)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Parent comment not found" in exc.value.detail

    @pytest.mark.unit
    async def test_create_comment_nesting_too_deep_raises_400(self, mock_db):
        """Grandchild comment (parent has its own parent) raises 400."""
        data = CommentCreate(content="Too deep!", parent_id=2)
        post = _make_post()
        # parent_comment has parent_id=1 → it IS a reply, can't be replied to
        parent_comment = _make_comment(id=2, parent_id=1)

        mock_db.execute.side_effect = [
            _make_result(scalar_one_or_none=post),
            _make_result(scalar_one_or_none=parent_comment),
        ]

        with pytest.raises(HTTPException) as exc:
            await create_comment(mock_db, post_id=1, user_id=1, data=data)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "nesting" in exc.value.detail.lower()


class TestGetComments:
    """Tests for get_comments()."""

    @pytest.mark.unit
    async def test_get_comments_returns_paginated_comments_with_replies(
        self, mock_db, test_user_orm
    ):
        """Returns paginated comments with nested replies."""
        top = _make_comment(id=1, content="Top comment", parent_id=None)
        top.user = test_user_orm
        reply = _make_comment(id=2, content="Reply", parent_id=1, user_id=2)
        reply.user = _make_user(id=2, username="otheruser")

        _configure_refresh(mock_db)

        # Three execute calls:
        # 1. Count query → scalar=1
        # 2. Top-level comments → scalars_all=[top]
        # 3. Replies for top comment → scalars_all=[reply]
        mock_db.execute.side_effect = [
            _make_result(scalar=1),
            _make_result(scalars_all=[top]),
            _make_result(scalars_all=[reply]),
        ]

        result = await get_comments(mock_db, post_id=1, page=1, size=20)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == 1
        assert result.items[0].content == "Top comment"
        assert len(result.items[0].replies) == 1
        assert result.items[0].replies[0].id == 2
        assert result.items[0].replies[0].content == "Reply"

    @pytest.mark.unit
    async def test_get_comments_empty_returns_empty(self, mock_db):
        """Returns empty items when no comments exist."""
        mock_db.execute.side_effect = [
            _make_result(scalar=0),
            _make_result(scalars_all=[]),
        ]

        result = await get_comments(mock_db, post_id=1)

        assert result.total == 0
        assert len(result.items) == 0


class TestDeleteComment:
    """Tests for delete_comment()."""

    @pytest.mark.unit
    async def test_delete_comment_owner_can_delete(self, mock_db, test_user_orm):
        """Owner can delete their own comment."""
        comment = _make_comment()
        post = _make_post(comment_count=3)

        mock_db.execute.side_effect = [
            _make_result(scalar_one_or_none=comment),  # find comment
            _make_result(scalar_one=post),              # find post for count update
        ]
        mock_db.flush = AsyncMock()
        mock_db.delete = MagicMock()

        await delete_comment(mock_db, comment_id=1, user_id=1)

        mock_db.delete.assert_called_once_with(comment)
        mock_db.flush.assert_awaited_once()
        # comment count decremented
        assert post.comment_count == 2

    @pytest.mark.unit
    async def test_delete_comment_admin_can_delete_any(self, mock_db, test_user_orm):
        """Admin can delete anyone's comment."""
        comment = _make_comment(user_id=99)  # owned by someone else
        post = _make_post(comment_count=5)

        mock_db.execute.side_effect = [
            _make_result(scalar_one_or_none=comment),
            _make_result(scalar_one=post),
        ]
        mock_db.flush = AsyncMock()
        mock_db.delete = MagicMock()

        await delete_comment(mock_db, comment_id=1, user_id=1, user_role="admin")

        mock_db.delete.assert_called_once_with(comment)

    @pytest.mark.unit
    async def test_delete_comment_not_owner_raises_403(self, mock_db):
        """Non-owner non-admin raises 403."""
        comment = _make_comment(user_id=99)

        mock_db.execute.return_value = _make_result(scalar_one_or_none=comment)

        with pytest.raises(HTTPException) as exc:
            await delete_comment(mock_db, comment_id=1, user_id=1)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in exc.value.detail

    @pytest.mark.unit
    async def test_delete_comment_not_found_raises_404(self, mock_db):
        """Raises 404 when comment does not exist."""
        mock_db.execute.return_value = _make_result(scalar_one_or_none=None)

        with pytest.raises(HTTPException) as exc:
            await delete_comment(mock_db, comment_id=999, user_id=1)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Comment not found" in exc.value.detail
