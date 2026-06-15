"""
Unit tests for user_service.py

Tests get_user_profile(), get_user_posts(), and update_profile()
using mocked database sessions from conftest.py.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.post import Post
from app.models.user import User
from app.schemas.auth import UpdateProfileRequest
from app.schemas.common import PaginatedResponse
from app.schemas.post import PostResponse
from app.schemas.user import UserProfileResponse
from app.services.user_service import (
    get_user_posts,
    get_user_profile,
    update_profile,
)


class TestGetUserProfile:
    """Tests for get_user_profile()."""

    @pytest.mark.unit
    async def test_get_user_profile(
        self, mock_db: AsyncMock, test_user_orm: User
    ):
        """Returns UserProfileResponse with follower_count, following_count, post_count."""
        # ── Arrange ──────────────────────────────────────────────────────
        user_result = AsyncMock()
        user_result.scalar_one_or_none = MagicMock(return_value=test_user_orm)

        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=5)

        mock_db.execute.side_effect = [
            user_result,      # user lookup
            count_result,     # follower count
            count_result,     # following count
            count_result,     # post count
        ]

        # ── Act ──────────────────────────────────────────────────────────
        result = await get_user_profile(mock_db, user_id=1)

        # ── Assert ───────────────────────────────────────────────────────
        assert isinstance(result, UserProfileResponse)
        assert result.id == 1
        assert result.username == "testuser"
        assert result.avatar_url == "https://example.com/avatar.png"
        assert result.bio == "Test user bio"
        assert result.role == "user"
        assert result.follower_count == 5
        assert result.following_count == 5
        assert result.post_count == 5

    @pytest.mark.unit
    async def test_get_user_profile_not_found(self, mock_db: AsyncMock):
        """Invalid user_id raises HTTPException 404."""
        # ── Arrange ──────────────────────────────────────────────────────
        # Default mock_result already returns None for scalar_one_or_none
        result = mock_db.execute.return_value
        result.scalar_one_or_none = MagicMock(return_value=None)

        # ── Act / Assert ─────────────────────────────────────────────────
        with pytest.raises(HTTPException) as exc:
            await get_user_profile(mock_db, user_id=999)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc.value.detail == "User not found"

    @pytest.mark.unit
    async def test_get_user_profile_counts_default_to_zero(
        self, mock_db: AsyncMock, test_user_orm: User
    ):
        """When no followers/following/posts exist, counts default to 0."""
        # ── Arrange ──────────────────────────────────────────────────────
        user_result = AsyncMock()
        user_result.scalar_one_or_none = MagicMock(return_value=test_user_orm)

        zero_result = AsyncMock()
        zero_result.scalar = MagicMock(return_value=None)  # simulate None → 0

        mock_db.execute.side_effect = [
            user_result,    # user lookup
            zero_result,    # follower count → None
            zero_result,    # following count → None
            zero_result,    # post count → None
        ]

        # ── Act ──────────────────────────────────────────────────────────
        result = await get_user_profile(mock_db, user_id=1)

        # ── Assert ───────────────────────────────────────────────────────
        assert result.follower_count == 0
        assert result.following_count == 0
        assert result.post_count == 0


class TestGetUserPosts:
    """Tests for get_user_posts()."""

    @pytest.mark.unit
    async def test_get_user_posts(
        self, mock_db: AsyncMock, test_user_orm: User
    ):
        """Returns paginated PostResponse list for a user."""
        # ── Arrange ──────────────────────────────────────────────────────
        now = datetime.utcnow()

        post1 = Post(
            id=1,
            user_id=test_user_orm.id,
            content="My first post",
            image_urls=["https://example.com/img1.png"],
            tags=["anime"],
            like_count=3,
            comment_count=1,
            user=test_user_orm,
            created_at=now,
        )
        post2 = Post(
            id=2,
            user_id=test_user_orm.id,
            content="My second post",
            image_urls=[],
            tags=[],
            like_count=0,
            comment_count=0,
            user=test_user_orm,
            created_at=now,
        )

        user_result = AsyncMock()
        user_result.scalar_one_or_none = MagicMock(return_value=test_user_orm)

        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=2)

        posts_result = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[post1, post2])
        posts_result.scalars = MagicMock(return_value=mock_scalars)

        mock_db.execute.side_effect = [
            user_result,    # user lookup
            count_result,   # total post count
            posts_result,   # paginated posts
        ]

        # ── Act ──────────────────────────────────────────────────────────
        result = await get_user_posts(mock_db, user_id=1, page=1, size=20)

        # ── Assert ───────────────────────────────────────────────────────
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 2
        assert result.total == 2
        assert result.page == 1
        assert result.size == 20

        assert isinstance(result.items[0], PostResponse)
        assert result.items[0].content == "My first post"
        assert result.items[0].like_count == 3
        assert result.items[0].user.id == test_user_orm.id
        assert result.items[0].user.username == "testuser"

        assert result.items[1].content == "My second post"

    @pytest.mark.unit
    async def test_get_user_posts_empty(
        self, mock_db: AsyncMock, test_user_orm: User
    ):
        """User with no posts returns empty items, total=0."""
        # ── Arrange ──────────────────────────────────────────────────────
        user_result = AsyncMock()
        user_result.scalar_one_or_none = MagicMock(return_value=test_user_orm)

        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=0)

        posts_result = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        posts_result.scalars = MagicMock(return_value=mock_scalars)

        mock_db.execute.side_effect = [
            user_result,    # user lookup
            count_result,   # total post count
            posts_result,   # paginated posts
        ]

        # ── Act ──────────────────────────────────────────────────────────
        result = await get_user_posts(mock_db, user_id=1, page=1, size=20)

        # ── Assert ───────────────────────────────────────────────────────
        assert len(result.items) == 0
        assert result.total == 0
        assert result.page == 1
        assert result.size == 20

    @pytest.mark.unit
    async def test_get_user_posts_user_not_found(self, mock_db: AsyncMock):
        """Non-existent user_id raises 404."""
        # ── Arrange ──────────────────────────────────────────────────────
        result = mock_db.execute.return_value
        result.scalar_one_or_none = MagicMock(return_value=None)

        # ── Act / Assert ─────────────────────────────────────────────────
        with pytest.raises(HTTPException) as exc:
            await get_user_posts(mock_db, user_id=999)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateProfile:
    """Tests for update_profile()."""

    @pytest.mark.unit
    async def test_update_profile(
        self, mock_db: AsyncMock, test_user_orm: User
    ):
        """Updates bio and avatar_url, returns updated profile with counts."""
        # ── Arrange ──────────────────────────────────────────────────────
        user_result = AsyncMock()
        user_result.scalar_one_or_none = MagicMock(return_value=test_user_orm)

        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=3)

        mock_db.execute.side_effect = [
            user_result,    # user lookup
            count_result,   # follower count
            count_result,   # following count
            count_result,   # post count
        ]

        profile_data = UpdateProfileRequest(
            bio="Updated biography",
            avatar_url="https://example.com/new-avatar.png",
        )

        # ── Act ──────────────────────────────────────────────────────────
        result = await update_profile(mock_db, user_id=1, profile_data=profile_data)

        # ── Assert ───────────────────────────────────────────────────────
        # Verify ORM object was mutated
        assert test_user_orm.bio == "Updated biography"
        assert test_user_orm.avatar_url == "https://example.com/new-avatar.png"

        # Verify DB flush/refresh called
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(test_user_orm)

        # Verify response shape
        assert isinstance(result, UserProfileResponse)
        assert result.bio == "Updated biography"
        assert result.avatar_url == "https://example.com/new-avatar.png"
        assert result.follower_count == 3
        assert result.following_count == 3
        assert result.post_count == 3

    @pytest.mark.unit
    async def test_update_profile_partial(
        self, mock_db: AsyncMock, test_user_orm: User
    ):
        """Updating only one field leaves the other unchanged."""
        # ── Arrange ──────────────────────────────────────────────────────
        original_avatar = test_user_orm.avatar_url
        original_bio = test_user_orm.bio

        user_result = AsyncMock()
        user_result.scalar_one_or_none = MagicMock(return_value=test_user_orm)

        count_result = AsyncMock()
        count_result.scalar = MagicMock(return_value=0)

        mock_db.execute.side_effect = [
            user_result,    # user lookup
            count_result,   # follower count
            count_result,   # following count
            count_result,   # post count
        ]

        # Only update bio, leave avatar_url as None (not provided)
        profile_data = UpdateProfileRequest(bio="Only bio changed", avatar_url=None)

        # ── Act ──────────────────────────────────────────────────────────
        result = await update_profile(mock_db, user_id=1, profile_data=profile_data)

        # ── Assert ───────────────────────────────────────────────────────
        assert result.bio == "Only bio changed"
        # avatar_url should still have the original value (not overwritten by None)
        assert result.avatar_url == original_avatar

    @pytest.mark.unit
    async def test_update_profile_user_not_found(self, mock_db: AsyncMock):
        """Non-existent user_id raises 404."""
        # ── Arrange ──────────────────────────────────────────────────────
        result = mock_db.execute.return_value
        result.scalar_one_or_none = MagicMock(return_value=None)

        profile_data = UpdateProfileRequest(bio="New bio")

        # ── Act / Assert ─────────────────────────────────────────────────
        with pytest.raises(HTTPException) as exc:
            await update_profile(mock_db, user_id=999, profile_data=profile_data)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
