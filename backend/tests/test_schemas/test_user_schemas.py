"""
Unit tests for User Schemas

Tests validation, serialization, and edge cases for:
- UserProfileResponse

NOTE: Tests are self-contained and do not depend on conftest.py fixtures,
because the root conftest triggers app.database module-level engine creation
which is incompatible with SQLite. Run with: pytest --noconftest -m unit
"""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.user import UserProfileResponse


def _make_utcnow() -> datetime:
    """Return current UTC datetime (avoiding deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════
# UserProfileResponse
# ══════════════════════════════════════════════════════════════════════════


class TestUserProfileResponse:
    """Tests for UserProfileResponse schema."""

    @pytest.mark.unit
    def test_construct_with_all_fields(self):
        """Should construct with all fields provided."""
        now = _make_utcnow()
        profile = UserProfileResponse(
            id=1,
            username="animefan",
            avatar_url="https://example.com/avatar.png",
            bio="I love anime!",
            role="creator",
            created_at=now,
            follower_count=42,
            following_count=10,
            post_count=7,
        )
        assert profile.id == 1
        assert profile.username == "animefan"
        assert profile.avatar_url == "https://example.com/avatar.png"
        assert profile.bio == "I love anime!"
        assert profile.role == "creator"
        assert profile.created_at == now
        assert profile.follower_count == 42
        assert profile.following_count == 10
        assert profile.post_count == 7

    @pytest.mark.unit
    def test_defaults_for_count_fields(self):
        """Count fields should default to 0."""
        now = _make_utcnow()
        profile = UserProfileResponse(
            id=2,
            username="newuser",
            created_at=now,
        )
        assert profile.follower_count == 0
        assert profile.following_count == 0
        assert profile.post_count == 0

    @pytest.mark.unit
    def test_optional_fields_none(self):
        """avatar_url and bio should accept None."""
        now = _make_utcnow()
        profile = UserProfileResponse(
            id=3,
            username="noner",
            created_at=now,
            avatar_url=None,
            bio=None,
        )
        assert profile.avatar_url is None
        assert profile.bio is None

    @pytest.mark.unit
    def test_default_role_is_user(self):
        """role should default to 'user'."""
        now = _make_utcnow()
        profile = UserProfileResponse(
            id=4,
            username="defaultrole",
            created_at=now,
        )
        assert profile.role == "user"

    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Should reject construction without required fields."""
        with pytest.raises(ValidationError):
            UserProfileResponse()

    @pytest.mark.unit
    def test_serialization_excludes_email_and_password(self):
        """Serialized output should not include email or password_hash."""
        now = _make_utcnow()
        profile = UserProfileResponse(
            id=1,
            username="animefan",
            created_at=now,
        )
        d = profile.model_dump()
        assert "email" not in d
        assert "password_hash" not in d

    @pytest.mark.unit
    def test_serialization_includes_all_fields(self):
        """Should include all expected fields in serialized output."""
        now = _make_utcnow()
        profile = UserProfileResponse(
            id=1,
            username="animefan",
            avatar_url="https://example.com/avatar.png",
            bio="Bio text",
            role="creator",
            created_at=now,
            follower_count=5,
            following_count=3,
            post_count=2,
        )
        d = profile.model_dump()
        assert set(d.keys()) == {
            "id", "username", "avatar_url", "bio", "role",
            "created_at", "follower_count", "following_count", "post_count",
        }

    @pytest.mark.unit
    def test_json_serialization(self):
        """Should produce valid JSON output with created_at as ISO string."""
        now = _make_utcnow()
        profile = UserProfileResponse(
            id=10,
            username="jsonfan",
            created_at=now,
        )
        json_str = profile.model_dump_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["id"] == 10
        assert parsed["username"] == "jsonfan"
        assert "created_at" in parsed

    @pytest.mark.unit
    def test_from_attributes_config(self):
        """Should confirm from_attributes is enabled."""
        assert UserProfileResponse.model_config.get("from_attributes") is True
