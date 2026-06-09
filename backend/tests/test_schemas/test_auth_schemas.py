"""
Unit tests for Auth Schemas

Tests validation, serialization, and edge cases for:
- RegisterRequest
- LoginRequest
- UpdateProfileRequest
- UserResponse
- TokenResponse

NOTE: Tests are self-contained and do not depend on conftest.py fixtures,
because the root conftest triggers app.database module-level engine creation
which is incompatible with SQLite. Run with: pytest --noconftest -m unit
"""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)

# ── Shared test data ───────────────────────────────────────────────────

VALID_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "StrongP@ss1",
}


def _make_utcnow() -> datetime:
    """Return current UTC datetime (avoiding deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════
# RegisterRequest
# ══════════════════════════════════════════════════════════════════════════


class TestRegisterRequest:
    """Tests for RegisterRequest schema validation."""

    @pytest.mark.unit
    def test_valid_registration(self):
        """Should accept valid registration data."""
        req = RegisterRequest(**VALID_USER)
        assert req.username == VALID_USER["username"]
        assert req.email == VALID_USER["email"]
        assert req.password == VALID_USER["password"]

    @pytest.mark.unit
    def test_username_too_short(self):
        """Should reject username shorter than 3 characters."""
        data = {**VALID_USER, "username": "ab"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    @pytest.mark.unit
    def test_username_too_long(self):
        """Should reject username longer than 50 characters."""
        data = {**VALID_USER, "username": "a" * 51}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    @pytest.mark.unit
    def test_username_invalid_chars_spaces(self):
        """Should reject username containing spaces."""
        data = {**VALID_USER, "username": "test user"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    @pytest.mark.unit
    def test_username_invalid_chars_hyphens(self):
        """Should reject username containing hyphens."""
        data = {**VALID_USER, "username": "test-user"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    @pytest.mark.unit
    def test_username_invalid_chars_dots(self):
        """Should reject username containing dots."""
        data = {**VALID_USER, "username": "test.user"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    @pytest.mark.unit
    def test_username_valid_underscores(self):
        """Should accept username with underscores."""
        data = {**VALID_USER, "username": "test_user_123"}
        req = RegisterRequest(**data)
        assert req.username == "test_user_123"

    @pytest.mark.unit
    def test_username_valid_numbers(self):
        """Should accept username with digits."""
        data = {**VALID_USER, "username": "test123"}
        req = RegisterRequest(**data)
        assert req.username == "test123"

    @pytest.mark.unit
    def test_email_invalid_format(self):
        """Should reject invalid email address."""
        data = {**VALID_USER, "email": "not-an-email"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    @pytest.mark.unit
    def test_email_missing_domain(self):
        """Should reject email missing domain."""
        data = {**VALID_USER, "email": "user@"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    @pytest.mark.unit
    def test_password_too_short(self):
        """Should reject password shorter than 8 characters."""
        data = {**VALID_USER, "password": "Ab1"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    @pytest.mark.unit
    def test_password_missing_uppercase(self):
        """Should reject password without uppercase letter."""
        data = {**VALID_USER, "password": "alllowercase1"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any("uppercase" in str(e["msg"]).lower() for e in errors)

    @pytest.mark.unit
    def test_password_missing_lowercase(self):
        """Should reject password without lowercase letter."""
        data = {**VALID_USER, "password": "ALLUPPERCASE1"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any("lowercase" in str(e["msg"]).lower() for e in errors)

    @pytest.mark.unit
    def test_password_missing_digit(self):
        """Should reject password without a digit."""
        data = {**VALID_USER, "password": "NoDigitsHere"}
        with pytest.raises(ValidationError) as exc:
            RegisterRequest(**data)
        errors = exc.value.errors()
        assert any("digit" in str(e["msg"]).lower() for e in errors)

    @pytest.mark.unit
    def test_password_at_min_length(self):
        """Should accept password exactly 8 chars with all requirements."""
        data = {**VALID_USER, "password": "Str0ngP1"}
        req = RegisterRequest(**data)
        assert req.password == "Str0ngP1"

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict and JSON correctly."""
        req = RegisterRequest(**VALID_USER)
        d = req.model_dump()
        assert d == VALID_USER
        json_str = req.model_dump_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed == VALID_USER


# ══════════════════════════════════════════════════════════════════════════
# LoginRequest
# ══════════════════════════════════════════════════════════════════════════


class TestLoginRequest:
    """Tests for LoginRequest schema validation."""

    @pytest.mark.unit
    def test_valid_login(self):
        """Should accept valid login credentials."""
        req = LoginRequest(username="testuser", password="StrongP@ss1")
        assert req.username == "testuser"
        assert req.password == "StrongP@ss1"

    @pytest.mark.unit
    def test_missing_username(self):
        """Should reject missing username field."""
        with pytest.raises(ValidationError) as exc:
            LoginRequest(password="SomePass1")
        errors = exc.value.errors()
        assert any(e["loc"] == ("username",) for e in errors)

    @pytest.mark.unit
    def test_missing_password(self):
        """Should reject missing password field."""
        with pytest.raises(ValidationError) as exc:
            LoginRequest(username="testuser")
        errors = exc.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    @pytest.mark.unit
    def test_accepts_empty_username(self):
        """LoginRequest has no min_length; empty username is accepted by Pydantic."""
        req = LoginRequest(username="", password="SomePass1")
        assert req.username == ""

    @pytest.mark.unit
    def test_accepts_empty_password(self):
        """LoginRequest has no min_length; empty password is accepted by Pydantic."""
        req = LoginRequest(username="testuser", password="")
        assert req.password == ""

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict and JSON correctly."""
        req = LoginRequest(username="testuser", password="StrongP@ss1")
        d = req.model_dump()
        assert d["username"] == "testuser"
        assert d["password"] == "StrongP@ss1"
        json_str = req.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["username"] == "testuser"


# ══════════════════════════════════════════════════════════════════════════
# UpdateProfileRequest
# ══════════════════════════════════════════════════════════════════════════


class TestUpdateProfileRequest:
    """Tests for UpdateProfileRequest schema validation."""

    @pytest.mark.unit
    def test_valid_bio_and_avatar(self):
        """Should accept valid bio and avatar_url."""
        req = UpdateProfileRequest(
            bio="This is my bio",
            avatar_url="https://example.com/avatar.png",
        )
        assert req.bio == "This is my bio"
        assert req.avatar_url == "https://example.com/avatar.png"

    @pytest.mark.unit
    def test_none_values_default(self):
        """Should default to None when fields not provided."""
        req = UpdateProfileRequest()
        assert req.bio is None
        assert req.avatar_url is None

    @pytest.mark.unit
    def test_explicit_none_values(self):
        """Should accept explicit None for optional fields."""
        req = UpdateProfileRequest(bio=None, avatar_url=None)
        assert req.bio is None
        assert req.avatar_url is None

    @pytest.mark.unit
    def test_bio_too_long(self):
        """Should reject bio longer than 500 characters."""
        with pytest.raises(ValidationError) as exc:
            UpdateProfileRequest(bio="a" * 501)
        errors = exc.value.errors()
        assert any(e["loc"] == ("bio",) for e in errors)

    @pytest.mark.unit
    def test_bio_at_max_length(self):
        """Should accept bio exactly 500 characters."""
        bio = "a" * 500
        req = UpdateProfileRequest(bio=bio)
        assert len(req.bio) == 500

    @pytest.mark.unit
    def test_avatar_url_too_long(self):
        """Should reject avatar_url longer than 500 characters."""
        with pytest.raises(ValidationError) as exc:
            UpdateProfileRequest(avatar_url="a" * 501)
        errors = exc.value.errors()
        assert any(e["loc"] == ("avatar_url",) for e in errors)

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict and JSON correctly."""
        req = UpdateProfileRequest(bio="My bio", avatar_url="https://img.com/pic.png")
        d = req.model_dump()
        assert d["bio"] == "My bio"
        assert d["avatar_url"] == "https://img.com/pic.png"
        json_str = req.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["bio"] == "My bio"


# ══════════════════════════════════════════════════════════════════════════
# UserResponse
# ══════════════════════════════════════════════════════════════════════════


class TestUserResponse:
    """Tests for UserResponse schema."""

    @pytest.mark.unit
    def test_construct_from_dict(self):
        """Should construct from a dictionary with all fields."""
        now = _make_utcnow()
        data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "avatar_url": "https://example.com/avatar.png",
            "bio": "Test bio",
            "role": "user",
            "created_at": now,
        }
        user = UserResponse(**data)
        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.avatar_url == "https://example.com/avatar.png"
        assert user.bio == "Test bio"
        assert user.role == "user"
        assert user.created_at == now

    @pytest.mark.unit
    def test_default_role(self):
        """Should default role to 'user' when not provided."""
        now = _make_utcnow()
        user = UserResponse(
            id=1, username="testuser", email="test@example.com", created_at=now,
        )
        assert user.role == "user"

    @pytest.mark.unit
    def test_default_avatar_bio(self):
        """Should default avatar_url to None and bio to ''."""
        now = _make_utcnow()
        user = UserResponse(
            id=1, username="testuser", email="test@example.com", created_at=now,
        )
        assert user.avatar_url is None
        assert user.bio == ""

    @pytest.mark.unit
    def test_model_validate_from_dict(self):
        """Should validate from a plain dict."""
        now = _make_utcnow()
        data = {
            "id": 42,
            "username": "dictuser",
            "email": "dict@example.com",
            "created_at": now,
        }
        user = UserResponse.model_validate(data)
        assert user.id == 42
        assert user.username == "dictuser"

    @pytest.mark.unit
    def test_model_validate_from_mock_orm(self):
        """Should populate from an object with ORM-like attributes (from_attributes)."""
        now = _make_utcnow()

        class MockUser:
            id = 7
            username = "ormuser"
            email = "orm@example.com"
            avatar_url = "https://img.com/orm.png"
            bio = "ORM bio"
            role = "admin"
            created_at = now

        user = UserResponse.model_validate(MockUser())
        assert user.id == 7
        assert user.username == "ormuser"
        assert user.email == "orm@example.com"
        assert user.avatar_url == "https://img.com/orm.png"
        assert user.bio == "ORM bio"
        assert user.role == "admin"
        assert isinstance(user.created_at, datetime)

    @pytest.mark.unit
    def test_serialization_excludes_extra(self):
        """Serialized output should not include fields not in schema."""
        now = _make_utcnow()
        user = UserResponse(
            id=1, username="testuser", email="test@example.com",
            created_at=now, avatar_url=None, bio="", role="user",
        )
        d = user.model_dump()
        assert "password_hash" not in d
        assert "is_active" not in d
        assert set(d.keys()) == {
            "id", "username", "email", "avatar_url", "bio", "role", "created_at",
        }

    @pytest.mark.unit
    def test_json_serialization(self):
        """Should produce valid JSON output with created_at as ISO string."""
        now = _make_utcnow()
        user = UserResponse(
            id=1, username="testuser", email="test@example.com",
            created_at=now, role="user",
        )
        json_str = user.model_dump_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["id"] == 1
        assert parsed["username"] == "testuser"
        assert "created_at" in parsed


# ══════════════════════════════════════════════════════════════════════════
# TokenResponse
# ══════════════════════════════════════════════════════════════════════════


class TestTokenResponse:
    """Tests for TokenResponse schema."""

    @pytest.mark.unit
    def test_construct_with_all_fields(self):
        """Should construct with access_token, token_type, expires_in, and user."""
        now = _make_utcnow()
        user = UserResponse(
            id=1, username="testuser", email="test@example.com",
            role="user", created_at=now,
        )
        token = TokenResponse(
            access_token="jwt.token.here",
            token_type="bearer",
            expires_in=3600,
            user=user,
        )
        assert token.access_token == "jwt.token.here"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600
        assert token.user.id == 1
        assert token.user.username == "testuser"

    @pytest.mark.unit
    def test_default_token_type(self):
        """Should default token_type to 'bearer'."""
        now = _make_utcnow()
        user = UserResponse(
            id=1, username="testuser", email="test@example.com",
            role="user", created_at=now,
        )
        token = TokenResponse(
            access_token="token123",
            expires_in=1800,
            user=user,
        )
        assert token.token_type == "bearer"

    @pytest.mark.unit
    def test_serialization(self):
        """Should serialize to dict and JSON."""
        now = _make_utcnow()
        user = UserResponse(
            id=1, username="testuser", email="test@example.com",
            role="user", created_at=now,
        )
        token = TokenResponse(
            access_token="abc.def.ghi",
            token_type="bearer",
            expires_in=3600,
            user=user,
        )
        d = token.model_dump()
        assert d["access_token"] == "abc.def.ghi"
        assert d["token_type"] == "bearer"
        assert d["expires_in"] == 3600
        assert d["user"]["id"] == 1
        json_str = token.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["access_token"] == "abc.def.ghi"
        assert parsed["user"]["username"] == "testuser"

    @pytest.mark.unit
    def test_requires_user(self):
        """Should require the user field."""
        with pytest.raises(ValidationError):
            TokenResponse(access_token="token", expires_in=3600)
