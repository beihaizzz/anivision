"""
Tests for auth router endpoints using FastAPI TestClient with mocked dependencies.

Tests cover all four auth endpoints:
- POST /api/auth/register
- POST /api/auth/login
- GET  /api/auth/me
- PUT  /api/auth/me
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.user import User


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
# Register Endpoint  POST /api/auth/register
# ══════════════════════════════════════════════════════════════════════════


class TestRegisterEndpoint:
    """Tests for POST /api/auth/register."""

    @pytest.mark.unit
    def test_register_success(
        self, client, app, mock_db, test_user_orm, test_user_data
    ):
        """201 with valid data; response has UserResponse fields."""
        _override_db(app, mock_db)

        # Simulate DB: no duplicate, refresh populates id + timestamps
        async def _refresh(obj):
            obj.id = 42
            obj.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        mock_db.refresh = AsyncMock(side_effect=_refresh)
        # execute already returns scalar_one_or_none=None by default → no duplicate

        response = client.post("/api/auth/register", json=test_user_data)

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 42
        assert body["username"] == test_user_data["username"]
        assert body["email"] == test_user_data["email"]
        assert body["role"] == "user"
        assert "created_at" in body
        # password_hash must never leak
        assert "password_hash" not in body

    @pytest.mark.unit
    def test_register_duplicate_username(
        self, client, app, mock_db, test_user_data, test_user_orm
    ):
        """409 when username already exists."""
        _override_db(app, mock_db)

        # execute returns existing user with same username
        existing = User(
            id=1,
            username=test_user_data["username"],
            email="other@example.com",
            password_hash="...",
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing)
        mock_db.execute.return_value = mock_result

        response = client.post("/api/auth/register", json=test_user_data)

        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.unit
    def test_register_duplicate_email(
        self, client, app, mock_db, test_user_data
    ):
        """409 when email already exists (different username)."""
        _override_db(app, mock_db)

        # Different username, same email
        existing = User(
            id=2,
            username="different_user",
            email=test_user_data["email"],
            password_hash="...",
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing)
        mock_db.execute.return_value = mock_result

        response = client.post("/api/auth/register", json=test_user_data)

        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    @pytest.mark.unit
    def test_register_username_too_short(self, client, app, mock_db):
        """422 when username is too short (min 3)."""
        _override_db(app, mock_db)

        response = client.post(
            "/api/auth/register",
            json={"username": "ab", "email": "ok@test.com", "password": "Str0ngP@ss"},
        )

        assert response.status_code == 422

    @pytest.mark.unit
    def test_register_password_weak_no_uppercase(self, client, app, mock_db):
        """422 when password has no uppercase letter."""
        _override_db(app, mock_db)

        response = client.post(
            "/api/auth/register",
            json={
                "username": "validuser",
                "email": "valid@test.com",
                "password": "alllowercase1",  # no uppercase
            },
        )

        assert response.status_code == 422

    @pytest.mark.unit
    def test_register_invalid_email(self, client, app, mock_db):
        """422 when email format is invalid."""
        _override_db(app, mock_db)

        response = client.post(
            "/api/auth/register",
            json={
                "username": "validuser",
                "email": "not-an-email",
                "password": "Str0ngP@ss",
            },
        )

        assert response.status_code == 422


# ══════════════════════════════════════════════════════════════════════════
# Login Endpoint  POST /api/auth/login
# ══════════════════════════════════════════════════════════════════════════


class TestLoginEndpoint:
    """Tests for POST /api/auth/login."""

    @pytest.fixture(autouse=True)
    def _patch_services(self):
        """Patch auth service functions so login tests don't hit real crypto/DB."""
        with (
            patch("app.routers.auth.authenticate_user") as mock_auth,
            patch("app.routers.auth.create_user_token") as mock_token,
        ):
            self.mock_authenticate = mock_auth
            self.mock_create_token = mock_token
            yield

    @pytest.mark.unit
    def test_login_success(self, client, app, mock_db, test_user_orm):
        """200 with valid credentials; response has TokenResponse fields."""
        _override_db(app, mock_db)
        self.mock_authenticate.return_value = test_user_orm
        self.mock_create_token.return_value = {
            "access_token": "fake-jwt-token",
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": test_user_orm.id,
                "username": test_user_orm.username,
                "email": test_user_orm.email,
                "avatar_url": test_user_orm.avatar_url,
                "bio": test_user_orm.bio or "",
                "role": test_user_orm.role,
                "created_at": test_user_orm.created_at.isoformat(),
            },
        }

        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "StrongP@ss1"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] == "fake-jwt-token"
        assert body["token_type"] == "bearer"
        assert body["expires_in"] == 86400
        assert body["user"]["username"] == "testuser"
        assert body["user"]["email"] == "test@example.com"

    @pytest.mark.unit
    def test_login_wrong_password(self, client, app, mock_db):
        """401 when password is incorrect."""
        _override_db(app, mock_db)
        self.mock_authenticate.return_value = None  # auth fails

        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "WrongP@ss1"},
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.unit
    def test_login_user_not_found(self, client, app, mock_db):
        """401 when user does not exist."""
        _override_db(app, mock_db)
        self.mock_authenticate.return_value = None

        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "SomeP@ss1"},
        )

        assert response.status_code == 401

    @pytest.mark.unit
    def test_login_account_deactivated(
        self, client, app, mock_db, inactive_user_orm
    ):
        """403 when account is deactivated."""
        _override_db(app, mock_db)
        self.mock_authenticate.return_value = inactive_user_orm

        response = client.post(
            "/api/auth/login",
            json={"username": "inactive", "password": "Inactive1"},
        )

        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()

    @pytest.mark.unit
    def test_login_with_email(self, client, app, mock_db, test_user_orm):
        """200 when logging in with email instead of username."""
        _override_db(app, mock_db)
        self.mock_authenticate.return_value = test_user_orm
        self.mock_create_token.return_value = {
            "access_token": "fake-jwt-token",
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": test_user_orm.id,
                "username": test_user_orm.username,
                "email": test_user_orm.email,
                "avatar_url": test_user_orm.avatar_url,
                "bio": test_user_orm.bio or "",
                "role": test_user_orm.role,
                "created_at": test_user_orm.created_at.isoformat(),
            },
        }

        response = client.post(
            "/api/auth/login",
            json={"username": "test@example.com", "password": "StrongP@ss1"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["user"]["email"] == "test@example.com"


# ══════════════════════════════════════════════════════════════════════════
# Me Endpoint  GET /api/auth/me
# ══════════════════════════════════════════════════════════════════════════


class TestMeEndpoint:
    """Tests for GET /api/auth/me."""

    @pytest.mark.unit
    def test_get_me_success(self, client, app, test_user_orm):
        """200 returns current user profile."""
        _override_current_user(app, test_user_orm)

        response = client.get("/api/auth/me")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == test_user_orm.id
        assert body["username"] == test_user_orm.username
        assert body["email"] == test_user_orm.email
        assert body["avatar_url"] == test_user_orm.avatar_url
        assert body["bio"] == test_user_orm.bio
        assert body["role"] == test_user_orm.role
        # password_hash must never leak
        assert "password_hash" not in body

    @pytest.mark.unit
    def test_get_me_no_auth_header(self, client):
        """401 when no Authorization header is provided."""
        # No dependency overrides → real middleware rejects missing token
        response = client.get("/api/auth/me")

        assert response.status_code in (401, 403)

    @pytest.mark.unit
    def test_get_me_invalid_token(self, client):
        """401 with an invalid / malformed token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# Update Me Endpoint  PUT /api/auth/me
# ══════════════════════════════════════════════════════════════════════════


class TestUpdateMeEndpoint:
    """Tests for PUT /api/auth/me."""

    @pytest.mark.unit
    def test_update_me_bio(self, client, app, mock_db, test_user_orm):
        """200 updates bio."""
        _override_current_user(app, test_user_orm)
        _override_db(app, mock_db)

        response = client.put(
            "/api/auth/me",
            json={"bio": "New bio text"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["bio"] == "New bio text"
        # avatar_url unchanged
        assert body["avatar_url"] == test_user_orm.avatar_url

    @pytest.mark.unit
    def test_update_me_avatar_url(self, client, app, mock_db, test_user_orm):
        """200 updates avatar_url."""
        _override_current_user(app, test_user_orm)
        _override_db(app, mock_db)

        response = client.put(
            "/api/auth/me",
            json={"avatar_url": "https://new-avatar.com/pic.png"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["avatar_url"] == "https://new-avatar.com/pic.png"
        # bio unchanged
        assert body["bio"] == test_user_orm.bio

    @pytest.mark.unit
    def test_update_me_partial(self, client, app, mock_db, test_user_orm):
        """200 partial update — only bio changes, avatar stays."""
        original_avatar = test_user_orm.avatar_url
        _override_current_user(app, test_user_orm)
        _override_db(app, mock_db)

        response = client.put(
            "/api/auth/me",
            json={"bio": "Partial update bio"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["bio"] == "Partial update bio"
        assert body["avatar_url"] == original_avatar

    @pytest.mark.unit
    def test_update_me_unauthenticated(self, client):
        """401 when no auth header is provided."""
        response = client.put(
            "/api/auth/me",
            json={"bio": "Should not work"},
        )

        assert response.status_code in (401, 403)
