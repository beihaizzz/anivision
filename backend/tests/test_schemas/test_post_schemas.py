"""
Unit tests for Post & Comment Schemas

Tests validation, serialization, and edge cases for:
- UserBrief
- PostCreate
- PostResponse
- PostUpdateRequest
- CommentCreate
- CommentResponse
- PostListResponse
- CommentListResponse

NOTE: Tests are self-contained and do not depend on conftest.py fixtures,
because the root conftest triggers app.database module-level engine creation
which is incompatible with SQLite. Run with: pytest --noconftest -m unit
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.post import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    PostCreate,
    PostListResponse,
    PostResponse,
    PostUpdateRequest,
    UserBrief,
)


def _make_utcnow() -> datetime:
    """Return current UTC datetime (avoiding deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════
# UserBrief
# ══════════════════════════════════════════════════════════════════════════


class TestUserBrief:
    """Tests for UserBrief schema."""

    @pytest.mark.unit
    def test_valid_user_brief(self):
        """Should accept all required fields."""
        user = UserBrief(id=1, username="alice", avatar_url="https://example.com/av.jpg")
        assert user.id == 1
        assert user.username == "alice"
        assert user.avatar_url == "https://example.com/av.jpg"

    @pytest.mark.unit
    def test_avatar_url_optional(self):
        """Should accept None avatar_url."""
        user = UserBrief(id=2, username="bob", avatar_url=None)
        assert user.avatar_url is None

    @pytest.mark.unit
    def test_avatar_url_default(self):
        """Should default avatar_url to None."""
        user = UserBrief(id=3, username="carol")
        assert user.avatar_url is None

    @pytest.mark.unit
    def test_username_required(self):
        """Should reject missing username."""
        with pytest.raises(ValidationError) as exc:
            UserBrief(id=1)  # type: ignore[call-arg]
        errors = exc.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    @pytest.mark.unit
    def test_id_required(self):
        """Should reject missing id."""
        with pytest.raises(ValidationError) as exc:
            UserBrief(username="test")  # type: ignore[call-arg]
        errors = exc.value.errors()
        assert any(e["loc"] == ("id",) for e in errors)

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to JSON correctly."""
        user = UserBrief(id=1, username="alice", avatar_url="https://example.com/av.jpg")
        data = user.model_dump()
        assert data == {
            "id": 1,
            "username": "alice",
            "avatar_url": "https://example.com/av.jpg",
        }


# ══════════════════════════════════════════════════════════════════════════
# PostCreate
# ══════════════════════════════════════════════════════════════════════════


class TestPostCreate:
    """Tests for PostCreate schema."""

    @pytest.mark.unit
    def test_valid_post_create(self):
        """Should accept valid creation data."""
        post = PostCreate(content="Hello world!")
        assert post.content == "Hello world!"
        assert post.image_urls == []
        assert post.tags == []

    @pytest.mark.unit
    def test_content_required(self):
        """Should reject missing content."""
        with pytest.raises(ValidationError) as exc:
            PostCreate()  # type: ignore[call-arg]
        errors = exc.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    @pytest.mark.unit
    def test_content_empty_string(self):
        """Should reject empty content string."""
        with pytest.raises(ValidationError) as exc:
            PostCreate(content="")
        errors = exc.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    @pytest.mark.unit
    def test_content_whitespace_only(self):
        """Should reject whitespace-only content."""
        with pytest.raises(ValidationError) as exc:
            PostCreate(content="   ")
        errors = exc.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    @pytest.mark.unit
    def test_image_urls_default(self):
        """Should default image_urls to empty list."""
        post = PostCreate(content="Test")
        assert post.image_urls == []

    @pytest.mark.unit
    def test_tags_default(self):
        """Should default tags to empty list."""
        post = PostCreate(content="Test")
        assert post.tags == []

    @pytest.mark.unit
    def test_image_urls_custom(self):
        """Should accept custom image_urls."""
        urls = ["https://example.com/1.jpg", "https://example.com/2.jpg"]
        post = PostCreate(content="Test", image_urls=urls)
        assert post.image_urls == urls

    @pytest.mark.unit
    def test_tags_custom(self):
        """Should accept custom tags."""
        tags = ["anime", "review"]
        post = PostCreate(content="Test", tags=tags)
        assert post.tags == tags

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to JSON (excluding unset defaults)."""
        post = PostCreate(content="Hello", tags=["anime"])
        data = post.model_dump()
        assert data["content"] == "Hello"
        assert data["tags"] == ["anime"]
        # image_urls uses default_factory, so it should be present
        assert data["image_urls"] == []


# ══════════════════════════════════════════════════════════════════════════
# PostResponse
# ══════════════════════════════════════════════════════════════════════════


class TestPostResponse:
    """Tests for PostResponse schema."""

    @pytest.mark.unit
    def test_valid_post_response(self):
        """Should accept valid response data."""
        created_at = _make_utcnow()
        post = PostResponse(
            id=1,
            content="Test post",
            image_urls=[],
            tags=["anime"],
            like_count=5,
            comment_count=2,
            user=UserBrief(id=1, username="alice", avatar_url=None),
            created_at=created_at,
        )
        assert post.id == 1
        assert post.content == "Test post"
        assert post.like_count == 5
        assert post.comment_count == 2
        assert post.user.username == "alice"
        assert post.created_at == created_at

    @pytest.mark.unit
    def test_default_counters(self):
        """Should default like_count and comment_count to 0."""
        created_at = _make_utcnow()
        post = PostResponse(
            id=1,
            content="Test",
            image_urls=[],
            tags=[],
            user=UserBrief(id=1, username="alice"),
            created_at=created_at,
        )
        assert post.like_count == 0
        assert post.comment_count == 0

    @pytest.mark.unit
    def test_user_is_userbrief(self):
        """Should enforce user field is UserBrief type."""
        created_at = _make_utcnow()
        post = PostResponse(
            id=1,
            content="Test",
            image_urls=[],
            tags=[],
            user=UserBrief(id=1, username="alice"),
            created_at=created_at,
        )
        assert isinstance(post.user, UserBrief)

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to JSON correctly."""
        created_at = _make_utcnow()
        post = PostResponse(
            id=1,
            content="Post",
            image_urls=["https://example.com/img.jpg"],
            tags=["anime"],
            like_count=3,
            comment_count=1,
            user=UserBrief(id=1, username="alice", avatar_url="https://example.com/av.jpg"),
            created_at=created_at,
        )
        data = post.model_dump()
        assert data["id"] == 1
        assert data["content"] == "Post"
        assert data["user"] == {
            "id": 1,
            "username": "alice",
            "avatar_url": "https://example.com/av.jpg",
        }

    @pytest.mark.unit
    def test_from_attributes(self):
        """Should support from_attributes mode for ORM compatibility."""
        created_at = _make_utcnow()
        post = PostResponse.model_validate({
            "id": 1,
            "content": "ORM post",
            "image_urls": ["https://example.com/img.jpg"],
            "tags": ["a", "b"],
            "like_count": 10,
            "comment_count": 3,
            "user": {"id": 2, "username": "bob", "avatar_url": None},
            "created_at": created_at,
        })
        assert post.id == 1
        assert post.content == "ORM post"
        assert post.user.username == "bob"


# ══════════════════════════════════════════════════════════════════════════
# PostUpdateRequest
# ══════════════════════════════════════════════════════════════════════════


class TestPostUpdateRequest:
    """Tests for PostUpdateRequest schema."""

    @pytest.mark.unit
    def test_empty_update(self):
        """Should allow empty update (no fields provided)."""
        req = PostUpdateRequest()
        assert req.content is None
        assert req.tags is None

    @pytest.mark.unit
    def test_content_only(self):
        """Should accept content-only update."""
        req = PostUpdateRequest(content="Updated content")
        assert req.content == "Updated content"
        assert req.tags is None

    @pytest.mark.unit
    def test_tags_only(self):
        """Should accept tags-only update."""
        req = PostUpdateRequest(tags=["new", "tags"])
        assert req.content is None
        assert req.tags == ["new", "tags"]

    @pytest.mark.unit
    def test_both_fields(self):
        """Should accept update with both fields."""
        req = PostUpdateRequest(content="Updated", tags=["a", "b"])
        assert req.content == "Updated"
        assert req.tags == ["a", "b"]


# ══════════════════════════════════════════════════════════════════════════
# CommentCreate
# ══════════════════════════════════════════════════════════════════════════


class TestCommentCreate:
    """Tests for CommentCreate schema."""

    @pytest.mark.unit
    def test_valid_comment_create(self):
        """Should accept valid comment data."""
        comment = CommentCreate(content="Great post!")
        assert comment.content == "Great post!"
        assert comment.parent_id is None

    @pytest.mark.unit
    def test_content_required(self):
        """Should reject missing content."""
        with pytest.raises(ValidationError) as exc:
            CommentCreate()  # type: ignore[call-arg]
        errors = exc.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    @pytest.mark.unit
    def test_content_empty_string(self):
        """Should reject empty content string."""
        with pytest.raises(ValidationError) as exc:
            CommentCreate(content="")
        errors = exc.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    @pytest.mark.unit
    def test_content_whitespace_only(self):
        """Should reject whitespace-only content."""
        with pytest.raises(ValidationError) as exc:
            CommentCreate(content="   ")
        errors = exc.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    @pytest.mark.unit
    def test_with_parent_id(self):
        """Should accept comment with parent_id for replies."""
        comment = CommentCreate(content="Reply!", parent_id=1)
        assert comment.content == "Reply!"
        assert comment.parent_id == 1

    @pytest.mark.unit
    def test_parent_id_none(self):
        """Should accept None parent_id (top-level comment)."""
        comment = CommentCreate(content="Top level", parent_id=None)
        assert comment.parent_id is None

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize correctly."""
        comment = CommentCreate(content="Hello", parent_id=5)
        data = comment.model_dump()
        assert data == {"content": "Hello", "parent_id": 5}


# ══════════════════════════════════════════════════════════════════════════
# CommentResponse
# ══════════════════════════════════════════════════════════════════════════


class TestCommentResponse:
    """Tests for CommentResponse schema."""

    @pytest.mark.unit
    def test_valid_comment_response(self):
        """Should accept valid response data without replies."""
        created_at = _make_utcnow()
        comment = CommentResponse(
            id=1,
            content="Nice post!",
            user=UserBrief(id=1, username="alice"),
            parent_id=None,
            created_at=created_at,
        )
        assert comment.id == 1
        assert comment.content == "Nice post!"
        assert comment.parent_id is None
        assert comment.replies == []
        assert comment.created_at == created_at

    @pytest.mark.unit
    def test_with_nested_replies(self):
        """Should accept comment with nested replies."""
        created_at = _make_utcnow()
        reply = CommentResponse(
            id=2,
            content="Thanks!",
            user=UserBrief(id=2, username="bob"),
            parent_id=1,
            created_at=created_at,
        )
        comment = CommentResponse(
            id=1,
            content="Great post!",
            user=UserBrief(id=1, username="alice"),
            parent_id=None,
            replies=[reply],
            created_at=created_at,
        )
        assert len(comment.replies) == 1
        assert comment.replies[0].id == 2
        assert comment.replies[0].parent_id == 1
        assert comment.replies[0].content == "Thanks!"

    @pytest.mark.unit
    def test_replies_default_empty_list(self):
        """Should default replies to empty list (no mutable default)."""
        created_at = _make_utcnow()
        c1 = CommentResponse(
            id=1, content="A", user=UserBrief(id=1, username="a"),
            parent_id=None, created_at=created_at,
        )
        c2 = CommentResponse(
            id=2, content="B", user=UserBrief(id=1, username="a"),
            parent_id=None, created_at=created_at,
        )
        # Both should have independent empty lists
        assert c1.replies == []
        assert c2.replies == []
        c1.replies.append(
            CommentResponse(
                id=3, content="R", user=UserBrief(id=2, username="b"),
                parent_id=1, created_at=created_at,
            )
        )
        # c2 should NOT be affected
        assert len(c2.replies) == 0

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to JSON correctly."""
        created_at = _make_utcnow()
        comment = CommentResponse(
            id=1,
            content="Post!",
            user=UserBrief(id=1, username="alice", avatar_url="https://example.com/av.jpg"),
            parent_id=None,
            created_at=created_at,
        )
        data = comment.model_dump()
        assert data["id"] == 1
        assert data["content"] == "Post!"
        assert data["parent_id"] is None
        assert data["replies"] == []

    @pytest.mark.unit
    def test_from_attributes(self):
        """Should support from_attributes mode for ORM compatibility."""
        created_at = _make_utcnow()
        comment = CommentResponse.model_validate({
            "id": 10,
            "content": "ORM comment",
            "user": {"id": 3, "username": "charlie", "avatar_url": None},
            "parent_id": None,
            "replies": [],
            "created_at": created_at,
        })
        assert comment.id == 10
        assert comment.content == "ORM comment"
        assert comment.user.username == "charlie"


# ══════════════════════════════════════════════════════════════════════════
# PostListResponse
# ══════════════════════════════════════════════════════════════════════════


class TestPostListResponse:
    """Tests for PostListResponse schema."""

    @pytest.mark.unit
    def test_valid_list_response(self):
        """Should accept valid paginated post list."""
        created_at = _make_utcnow()
        posts = [
            PostResponse(
                id=1, content="Post 1", image_urls=[], tags=[],
                user=UserBrief(id=1, username="alice"),
                created_at=created_at,
            ),
        ]
        response = PostListResponse(items=posts, total=1, page=1, size=20)
        assert len(response.items) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.size == 20

    @pytest.mark.unit
    def test_empty_list(self):
        """Should accept empty items list."""
        response = PostListResponse(items=[], total=0, page=1, size=20)
        assert response.items == []
        assert response.total == 0


# ══════════════════════════════════════════════════════════════════════════
# CommentListResponse
# ══════════════════════════════════════════════════════════════════════════


class TestCommentListResponse:
    """Tests for CommentListResponse schema."""

    @pytest.mark.unit
    def test_valid_list_response(self):
        """Should accept valid paginated comment list."""
        created_at = _make_utcnow()
        comments = [
            CommentResponse(
                id=1, content="Comment 1",
                user=UserBrief(id=1, username="alice"),
                parent_id=None, created_at=created_at,
            ),
        ]
        response = CommentListResponse(items=comments, total=1, page=1, size=20)
        assert len(response.items) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.size == 20

    @pytest.mark.unit
    def test_empty_list(self):
        """Should accept empty items list."""
        response = CommentListResponse(items=[], total=0, page=1, size=20)
        assert response.items == []
        assert response.total == 0


# ══════════════════════════════════════════════════════════════════════════
# Integration: Cross-schema nesting
# ══════════════════════════════════════════════════════════════════════════


class TestNestedSchemas:
    """Tests for cross-schema nesting scenarios."""

    @pytest.mark.unit
    def test_post_with_user(self):
        """Should create PostResponse with nested UserBrief."""
        created_at = _make_utcnow()
        post = PostResponse(
            id=42,
            content="Deep test",
            image_urls=["https://example.com/img.jpg"],
            tags=["deep"],
            like_count=7,
            comment_count=0,
            user=UserBrief(id=99, username="deepuser", avatar_url="https://example.com/av.jpg"),
            created_at=created_at,
        )
        assert post.user.id == 99
        assert post.user.username == "deepuser"

    @pytest.mark.unit
    def test_comment_with_replies_tree(self):
        """Should build a 3-level comment tree."""
        created_at = _make_utcnow()
        deep_reply = CommentResponse(
            id=3,
            content="Deep",
            user=UserBrief(id=3, username="charlie"),
            parent_id=2,
            created_at=created_at,
        )
        reply = CommentResponse(
            id=2,
            content="Reply",
            user=UserBrief(id=2, username="bob"),
            parent_id=1,
            replies=[deep_reply],
            created_at=created_at,
        )
        top = CommentResponse(
            id=1,
            content="Top",
            user=UserBrief(id=1, username="alice"),
            parent_id=None,
            replies=[reply],
            created_at=created_at,
        )
        assert top.replies[0].replies[0].content == "Deep"
        assert top.replies[0].replies[0].parent_id == 2
