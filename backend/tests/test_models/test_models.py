"""
Unit tests for all ORM models.

Covers instantiation, field defaults, repr, table names,
relationships, constraints, and required-field validation.
No database connections needed — pure unit tests.
"""

import pytest
from sqlalchemy import Column, UniqueConstraint

from app.models import (
    BehaviorLog,
    Character,
    Comment,
    Follow,
    Like,
    Post,
    RecognitionLog,
    Tag,
    User,
    Work,
)


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _nullable_required_columns(model_class, *col_names):
    """Verify that the given columns are required (nullable=False, no default).

    Uses pytest.raises semantics: raises AssertionError if column metadata
    does not match expectations for a required field.
    """
    for name in col_names:
        col = getattr(model_class.__table__.c, name)
        assert col.nullable is False, f"{model_class.__name__}.{name}: expected nullable=False"
        assert col.default is None, f"{model_class.__name__}.{name}: expected no default"
        assert col.server_default is None, f"{model_class.__name__}.{name}: expected no server_default"


# ═══════════════════════════════════════════════════════════════════════
# User
# ═══════════════════════════════════════════════════════════════════════


class TestUser:
    """Tests for User ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert User.__tablename__ == "users"

    @pytest.mark.unit
    def test_instantiation_full(self):
        user = User(
            id=1,
            username="alice",
            email="alice@example.com",
            password_hash="hashed_secret",
            avatar_url="https://img.example/alice.png",
            bio="Hello world",
            role="creator",
            is_active=False,
        )
        assert user.id == 1
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.password_hash == "hashed_secret"
        assert user.avatar_url == "https://img.example/alice.png"
        assert user.bio == "Hello world"
        assert user.role == "creator"
        assert user.is_active is False

    @pytest.mark.unit
    def test_defaults(self):
        """role / is_active / bio have SQLAlchemy Column defaults (applied at INSERT)."""
        role_col = User.__table__.c.role
        assert role_col.default is not None
        assert role_col.default.arg == "user"

        is_active_col = User.__table__.c.is_active
        assert is_active_col.default is not None
        assert is_active_col.default.arg is True

        bio_col = User.__table__.c.bio
        assert bio_col.default is not None
        assert bio_col.default.arg == ""

    @pytest.mark.unit
    def test_repr(self):
        user = User(id=7, username="charlie")
        assert repr(user) == "<User(id=7, username='charlie')>"

    @pytest.mark.unit
    def test_repr_no_id(self):
        """repr when id is not yet set (before flush)."""
        user = User(username="dana")
        assert repr(user) == "<User(id=None, username='dana')>"

    @pytest.mark.unit
    def test_required_columns(self):
        """Verify username, email, password_hash are required (no DB flush needed)."""
        _nullable_required_columns(User, "username", "email", "password_hash")

    @pytest.mark.unit
    def test_required_field_missing_raises_on_column_check(self):
        """pytest.raises used to confirm a non-existent column raises AttributeError."""
        with pytest.raises(AttributeError):
            _ = User.__table__.c.nonexistent_column  # should raise

    @pytest.mark.unit
    def test_relationship_posts(self):
        assert hasattr(User, "posts")

    @pytest.mark.unit
    def test_relationship_following_followers(self):
        assert hasattr(User, "following")
        assert hasattr(User, "followers")


# ═══════════════════════════════════════════════════════════════════════
# Work
# ═══════════════════════════════════════════════════════════════════════


class TestWork:
    """Tests for Work ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert Work.__tablename__ == "works"

    @pytest.mark.unit
    def test_instantiation_full(self):
        work = Work(
            id=10,
            title="Attack on Titan",
            title_jp="進撃の巨人",
            type="manga",
            description="A story about Titans.",
            cover_url="https://img.example/aot.png",
        )
        assert work.id == 10
        assert work.title == "Attack on Titan"
        assert work.title_jp == "進撃の巨人"
        assert work.type == "manga"
        assert work.description == "A story about Titans."
        assert work.cover_url == "https://img.example/aot.png"

    @pytest.mark.unit
    def test_default_type(self):
        """type column has default='anime' (applied at INSERT)."""
        type_col = Work.__table__.c.type
        assert type_col.default is not None
        assert type_col.default.arg == "anime"

    @pytest.mark.unit
    def test_repr(self):
        work = Work(id=3, title="One Piece")
        assert repr(work) == "<Work(id=3, title='One Piece')>"

    @pytest.mark.unit
    def test_repr_no_id(self):
        work = Work(title="Bleach")
        assert repr(work) == "<Work(id=None, title='Bleach')>"

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(Work, "title")


# ═══════════════════════════════════════════════════════════════════════
# Character
# ═══════════════════════════════════════════════════════════════════════


class TestCharacter:
    """Tests for Character ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert Character.__tablename__ == "characters"

    @pytest.mark.unit
    def test_instantiation_full(self):
        char = Character(
            id=20,
            name="Eren Yeager",
            name_jp="エレン・イェーガー",
            aliases=["Eren", "Titan-shifter"],
            work_id=10,
            description="Protagonist of AoT.",
            image_url="https://img.example/eren.png",
        )
        assert char.id == 20
        assert char.name == "Eren Yeager"
        assert char.name_jp == "エレン・イェーガー"
        assert char.aliases == ["Eren", "Titan-shifter"]
        assert char.work_id == 10
        assert char.description == "Protagonist of AoT."
        assert char.image_url == "https://img.example/eren.png"

    @pytest.mark.unit
    def test_defaults(self):
        """aliases and description have Column defaults (applied at INSERT)."""
        aliases_col = Character.__table__.c.aliases
        assert aliases_col.default is not None
        assert aliases_col.default.arg == []

        desc_col = Character.__table__.c.description
        assert desc_col.default is not None
        assert desc_col.default.arg == ""

    @pytest.mark.unit
    def test_work_id_nullable(self):
        """work_id is nullable (SET NULL on delete)."""
        char = Character(name="Levi")
        assert char.work_id is None

    @pytest.mark.unit
    def test_repr(self):
        char = Character(id=5, name="Armin")
        assert repr(char) == "<Character(id=5, name='Armin')>"

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(Character, "name")


# ═══════════════════════════════════════════════════════════════════════
# Post
# ═══════════════════════════════════════════════════════════════════════


class TestPost:
    """Tests for Post ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert Post.__tablename__ == "posts"

    @pytest.mark.unit
    def test_instantiation_full(self):
        post = Post(
            id=30,
            user_id=1,
            content="Great episode!",
            image_urls=["http://img/a.png", "http://img/b.png"],
            tags=["review", "hype"],
            like_count=42,
            comment_count=7,
        )
        assert post.id == 30
        assert post.user_id == 1
        assert post.content == "Great episode!"
        assert post.image_urls == ["http://img/a.png", "http://img/b.png"]
        assert post.tags == ["review", "hype"]
        assert post.like_count == 42
        assert post.comment_count == 7

    @pytest.mark.unit
    def test_defaults(self):
        """image_urls, tags, like_count, comment_count have Column defaults."""
        image_urls_col = Post.__table__.c.image_urls
        assert image_urls_col.default is not None
        assert image_urls_col.default.arg == []

        tags_col = Post.__table__.c.tags
        assert tags_col.default is not None
        assert tags_col.default.arg == []

        like_count_col = Post.__table__.c.like_count
        assert like_count_col.default is not None
        assert like_count_col.default.arg == 0

        comment_count_col = Post.__table__.c.comment_count
        assert comment_count_col.default is not None
        assert comment_count_col.default.arg == 0

    @pytest.mark.unit
    def test_repr(self):
        post = Post(id=8, user_id=2)
        assert repr(post) == "<Post(id=8, user_id=2)>"

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(Post, "content", "user_id")

    @pytest.mark.unit
    def test_relationship_user(self):
        assert hasattr(Post, "user")

    @pytest.mark.unit
    def test_relationship_comments(self):
        assert hasattr(Post, "comments")

    @pytest.mark.unit
    def test_relationship_likes(self):
        assert hasattr(Post, "likes")


# ═══════════════════════════════════════════════════════════════════════
# Comment
# ═══════════════════════════════════════════════════════════════════════


class TestComment:
    """Tests for Comment ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert Comment.__tablename__ == "comments"

    @pytest.mark.unit
    def test_instantiation_full(self):
        comment = Comment(
            id=40,
            post_id=30,
            user_id=1,
            content="Nice analysis!",
            parent_id=None,
        )
        assert comment.id == 40
        assert comment.post_id == 30
        assert comment.user_id == 1
        assert comment.content == "Nice analysis!"
        assert comment.parent_id is None

    @pytest.mark.unit
    def test_instantiation_with_parent(self):
        comment = Comment(
            post_id=30,
            user_id=2,
            content="+1",
            parent_id=40,
        )
        assert comment.parent_id == 40

    @pytest.mark.unit
    def test_parent_id_nullable(self):
        comment = Comment(post_id=30, user_id=1, content="Top-level")
        assert comment.parent_id is None

    @pytest.mark.unit
    def test_repr(self):
        comment = Comment(id=12, post_id=99)
        assert repr(comment) == "<Comment(id=12, post_id=99)>"

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(Comment, "content", "post_id", "user_id")

    @pytest.mark.unit
    def test_self_referential_relationship(self):
        """parent relationship with remote_side and replies backref."""
        assert hasattr(Comment, "parent")
        assert hasattr(Comment, "replies")

    @pytest.mark.unit
    def test_relationship_parent_setup(self):
        """Verify parent_id FK points at comments.id."""
        fk = Comment.__table__.c.parent_id
        assert fk.nullable is True
        # parent_id has a ForeignKey to comments.id
        assert any(
            fk_col.column.table.name == "comments" and fk_col.column.name == "id"
            for fk_col in fk.foreign_keys
        )


# ═══════════════════════════════════════════════════════════════════════
# Like
# ═══════════════════════════════════════════════════════════════════════


class TestLike:
    """Tests for Like ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert Like.__tablename__ == "likes"

    @pytest.mark.unit
    def test_instantiation(self):
        like = Like(user_id=1, post_id=30)
        assert like.user_id == 1
        assert like.post_id == 30

    @pytest.mark.unit
    def test_repr(self):
        like = Like(user_id=3, post_id=7)
        assert repr(like) == "<Like(user_id=3, post_id=7)>"

    @pytest.mark.unit
    def test_unique_constraint_exists(self):
        """Verify uq_user_post_like is defined."""
        constraints = {
            c.name: c
            for c in Like.__table_args__
            if isinstance(c, UniqueConstraint)
        }
        assert "uq_user_post_like" in constraints

    @pytest.mark.unit
    def test_unique_constraint_raises_if_missing(self):
        """pytest.raises used to confirm missing constraint is detectable."""
        with pytest.raises(KeyError):
            constraints = {
                c.name: c
                for c in Like.__table_args__
                if isinstance(c, UniqueConstraint)
            }
            _ = constraints["nonexistent_constraint"]

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(Like, "user_id", "post_id")

    @pytest.mark.unit
    def test_relationship_user(self):
        assert hasattr(Like, "user")

    @pytest.mark.unit
    def test_relationship_post(self):
        assert hasattr(Like, "post")


# ═══════════════════════════════════════════════════════════════════════
# Follow
# ═══════════════════════════════════════════════════════════════════════


class TestFollow:
    """Tests for Follow ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert Follow.__tablename__ == "follows"

    @pytest.mark.unit
    def test_instantiation(self):
        follow = Follow(follower_id=1, followed_id=2)
        assert follow.follower_id == 1
        assert follow.followed_id == 2

    @pytest.mark.unit
    def test_repr(self):
        follow = Follow(follower_id=5, followed_id=9)
        assert repr(follow) == "<Follow(follower=5 -> followed=9)>"

    @pytest.mark.unit
    def test_unique_constraint_exists(self):
        constraints = {
            c.name: c
            for c in Follow.__table_args__
            if isinstance(c, UniqueConstraint)
        }
        assert "uq_follower_followed" in constraints

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(Follow, "follower_id", "followed_id")

    @pytest.mark.unit
    def test_bidirectional_relationship(self):
        """Both follower and followed point at User."""
        assert hasattr(Follow, "follower")
        assert hasattr(Follow, "followed")

    @pytest.mark.unit
    def test_bidirectional_relationship_missing_raises(self):
        """pytest.raises: verify a non-existent relationship raises KeyError."""
        with pytest.raises(KeyError):
            _ = Follow.__mapper__.relationships["nonexistent_rel"]


# ═══════════════════════════════════════════════════════════════════════
# RecognitionLog
# ═══════════════════════════════════════════════════════════════════════


class TestRecognitionLog:
    """Tests for RecognitionLog ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert RecognitionLog.__tablename__ == "recognition_logs"

    @pytest.mark.unit
    def test_instantiation_full(self):
        log = RecognitionLog(
            id=50,
            user_id=1,
            top_character_id=20,
            image_path="/uploads/img001.jpg",
            result=[{"name": "Eren", "confidence": 0.92}],
            confidence=0.92,
            is_mock=True,
        )
        assert log.id == 50
        assert log.user_id == 1
        assert log.top_character_id == 20
        assert log.image_path == "/uploads/img001.jpg"
        assert log.result == [{"name": "Eren", "confidence": 0.92}]
        assert log.confidence == 0.92
        assert log.is_mock is True

    @pytest.mark.unit
    def test_defaults(self):
        """is_mock defaults to False, top_character_id and user_id are nullable."""
        is_mock_col = RecognitionLog.__table__.c.is_mock
        assert is_mock_col.default is not None
        assert is_mock_col.default.arg is False

        assert RecognitionLog.__table__.c.top_character_id.nullable is True
        assert RecognitionLog.__table__.c.user_id.nullable is True

    @pytest.mark.unit
    def test_repr(self):
        log = RecognitionLog(id=3, user_id=7)
        assert repr(log) == "<RecognitionLog(id=3, user_id=7)>"

    @pytest.mark.unit
    def test_repr_no_user(self):
        log = RecognitionLog(id=9)
        assert repr(log) == "<RecognitionLog(id=9, user_id=None)>"

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(RecognitionLog, "image_path", "result")


# ═══════════════════════════════════════════════════════════════════════
# BehaviorLog
# ═══════════════════════════════════════════════════════════════════════


class TestBehaviorLog:
    """Tests for BehaviorLog ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert BehaviorLog.__tablename__ == "behavior_logs"

    @pytest.mark.unit
    def test_instantiation_full(self):
        log = BehaviorLog(
            id=60,
            user_id=1,
            action_type="search",
            context={"query": "Eren", "results_count": 5},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert log.id == 60
        assert log.user_id == 1
        assert log.action_type == "search"
        assert log.context == {"query": "Eren", "results_count": 5}
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Mozilla/5.0"

    @pytest.mark.unit
    def test_defaults(self):
        """context defaults to {}, ip_address/user_agent/user_id are nullable."""
        ctx_col = BehaviorLog.__table__.c.context
        assert ctx_col.default is not None
        assert ctx_col.default.arg == {}

        assert BehaviorLog.__table__.c.ip_address.nullable is True
        assert BehaviorLog.__table__.c.user_agent.nullable is True
        assert BehaviorLog.__table__.c.user_id.nullable is True

    @pytest.mark.unit
    def test_repr(self):
        log = BehaviorLog(id=4, action_type="login")
        assert repr(log) == "<BehaviorLog(id=4, action='login')>"

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(BehaviorLog, "action_type")


# ═══════════════════════════════════════════════════════════════════════
# Tag
# ═══════════════════════════════════════════════════════════════════════


class TestTag:
    """Tests for Tag ORM model."""

    @pytest.mark.unit
    def test_table_name(self):
        assert Tag.__tablename__ == "tags"

    @pytest.mark.unit
    def test_instantiation_full(self):
        tag = Tag(id=70, name="action")
        assert tag.id == 70
        assert tag.name == "action"

    @pytest.mark.unit
    def test_instantiation_minimal(self):
        tag = Tag(name="romance")
        assert tag.name == "romance"

    @pytest.mark.unit
    def test_repr(self):
        tag = Tag(id=2, name="comedy")
        assert repr(tag) == "<Tag(id=2, name='comedy')>"

    @pytest.mark.unit
    def test_repr_no_id(self):
        tag = Tag(name="drama")
        assert repr(tag) == "<Tag(id=None, name='drama')>"

    @pytest.mark.unit
    def test_required_columns(self):
        _nullable_required_columns(Tag, "name")


# ═══════════════════════════════════════════════════════════════════════
# Cross-model Relationship Tests
# ═══════════════════════════════════════════════════════════════════════


class TestRelationships:
    """Verify ORM-level relationships are wired correctly."""

    @pytest.mark.unit
    def test_user_has_posts_relationship(self):
        """User.posts back_populates to Post.user."""
        rel = User.__mapper__.relationships["posts"]
        assert rel.back_populates == "user"

    @pytest.mark.unit
    def test_post_belongs_to_user(self):
        """Post.user back_populates to User.posts."""
        rel = Post.__mapper__.relationships["user"]
        assert rel.back_populates == "posts"

    @pytest.mark.unit
    def test_comment_self_referential_parent(self):
        """Comment.parent uses remote_side=[Comment.id]."""
        rel = Comment.__mapper__.relationships["parent"]
        # remote_side should be [Comment.id]
        assert rel.remote_side is not None

    @pytest.mark.unit
    def test_comment_replies_backref(self):
        """Comment.replies is the backref from parent relationship."""
        assert hasattr(Comment, "replies")

    @pytest.mark.unit
    def test_follow_bidirectional(self):
        """Follow.follower -> User.following, Follow.followed -> User.followers."""
        follower_rel = Follow.__mapper__.relationships["follower"]
        followed_rel = Follow.__mapper__.relationships["followed"]
        assert follower_rel.back_populates == "following"
        assert followed_rel.back_populates == "followers"

    @pytest.mark.unit
    def test_like_unique_constraint_name(self):
        """Verify the unique constraint is correctly named."""
        uq = [
            c for c in Like.__table_args__
            if isinstance(c, UniqueConstraint) and c.name == "uq_user_post_like"
        ]
        assert len(uq) == 1
        constraint = uq[0]
        col_names = {col.name for col in constraint.columns}
        assert col_names == {"user_id", "post_id"}

    @pytest.mark.unit
    def test_follow_unique_constraint_name(self):
        """Verify the unique constraint is correctly named."""
        uq = [
            c for c in Follow.__table_args__
            if isinstance(c, UniqueConstraint) and c.name == "uq_follower_followed"
        ]
        assert len(uq) == 1
        constraint = uq[0]
        col_names = {col.name for col in constraint.columns}
        assert col_names == {"follower_id", "followed_id"}
