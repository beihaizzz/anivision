"""
Unit tests for auth_service.py

Tests register_user(), authenticate_user(), and create_user_token()
using mocked database sessions from conftest.py.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from jose import jwt

from app.config import settings
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.auth_service import (
    authenticate_user,
    create_user_token,
    register_user,
)


class TestRegisterUser:
    """Tests for register_user()."""

    @pytest.mark.unit
    async def test_successful_registration_creates_user_with_hashed_password(
        self, mock_db, test_user_data
    ):
        """Successful registration creates User with hashed password."""
        user_data = RegisterRequest(**test_user_data)

        result = await register_user(mock_db, user_data)

        assert isinstance(result, User)
        assert result.username == test_user_data["username"]
        assert result.email == test_user_data["email"]
        assert result.role == "user"
        # Password must be hashed, not stored as plaintext
        assert result.password_hash != test_user_data["password"]
        assert result.password_hash.startswith("$2b$")
        # Verify DB interactions occurred
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.unit
    async def test_returns_user_with_correct_fields(
        self, mock_db, test_user_data
    ):
        """Returns User with correct username, email, role='user'."""
        user_data = RegisterRequest(**test_user_data)

        result = await register_user(mock_db, user_data)

        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.role == "user"

    @pytest.mark.unit
    async def test_password_hash_is_hashed_not_plaintext(
        self, mock_db, test_user_data
    ):
        """verify password_hash is hashed, not plaintext."""
        user_data = RegisterRequest(**test_user_data)

        result = await register_user(mock_db, user_data)

        plain = test_user_data["password"]
        assert result.password_hash != plain
        assert result.password_hash.startswith("$2b$")
        # Verify it's a valid bcrypt hash (60 chars)
        assert len(result.password_hash) == 60

    @pytest.mark.unit
    async def test_raises_409_when_username_exists(
        self, mock_db, test_user_data
    ):
        """Raises HTTPException 409 when username already exists."""
        existing_user = User(
            username="testuser",
            email="different@example.com",
            password_hash="hashed",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        user_data = RegisterRequest(**test_user_data)

        with pytest.raises(HTTPException) as exc_info:
            await register_user(mock_db, user_data)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "Username already registered"

    @pytest.mark.unit
    async def test_raises_409_when_email_exists(
        self, mock_db, test_user_data
    ):
        """Raises HTTPException 409 when email already exists."""
        existing_user = User(
            username="different",
            email="test@example.com",
            password_hash="hashed",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        user_data = RegisterRequest(**test_user_data)

        with pytest.raises(HTTPException) as exc_info:
            await register_user(mock_db, user_data)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "Email already registered"


class TestAuthenticateUser:
    """Tests for authenticate_user()."""

    @pytest.mark.unit
    async def test_returns_user_when_credentials_valid_by_username(
        self, mock_db_with_user, test_user_orm
    ):
        """Returns User when credentials valid (login by username)."""
        with patch(
            "app.services.auth_service.verify_password", return_value=True
        ):
            result = await authenticate_user(
                mock_db_with_user, test_user_orm.username, "StrongP@ss1"
            )

        assert result is test_user_orm

    @pytest.mark.unit
    async def test_returns_user_when_credentials_valid_by_email(
        self, mock_db_with_user, test_user_orm
    ):
        """Returns User when credentials valid (login by email)."""
        with patch(
            "app.services.auth_service.verify_password", return_value=True
        ):
            result = await authenticate_user(
                mock_db_with_user, test_user_orm.email, "StrongP@ss1"
            )

        assert result is test_user_orm

    @pytest.mark.unit
    async def test_returns_none_when_user_not_found(self, mock_db):
        """Returns None when no user matches the credential."""
        result = await authenticate_user(
            mock_db, "nonexistent", "password"
        )

        assert result is None

    @pytest.mark.unit
    async def test_returns_none_when_password_wrong(
        self, mock_db_with_user, test_user_orm
    ):
        """Returns None when password does not match."""
        with patch(
            "app.services.auth_service.verify_password", return_value=False
        ):
            result = await authenticate_user(
                mock_db_with_user, test_user_orm.username, "WrongP@ss1"
            )

        assert result is None

    @pytest.mark.unit
    async def test_verify_password_is_called_correctly(
        self, mock_db_with_user, test_user_orm
    ):
        """verify_password is called with correct arguments."""
        with patch(
            "app.services.auth_service.verify_password"
        ) as mock_verify:
            mock_verify.return_value = True
            await authenticate_user(
                mock_db_with_user, test_user_orm.username, "StrongP@ss1"
            )

        mock_verify.assert_called_once_with(
            "StrongP@ss1", test_user_orm.password_hash
        )


class TestCreateUserToken:
    """Tests for create_user_token()."""

    @pytest.mark.unit
    async def test_returns_dict_with_all_expected_keys(self, test_user_orm):
        """Returns dict with access_token, token_type='bearer', expires_in, user dict."""
        result = await create_user_token(test_user_orm)

        assert isinstance(result, dict)
        assert "access_token" in result
        assert "token_type" in result
        assert "expires_in" in result
        assert "user" in result
        assert result["token_type"] == "bearer"
        assert isinstance(result["access_token"], str)
        assert len(result["access_token"]) > 0
        assert isinstance(result["expires_in"], int)
        assert result["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @pytest.mark.unit
    async def test_token_is_valid_jwt_that_can_be_decoded(self, test_user_orm):
        """Token is a valid JWT that can be decoded with the app's secret."""
        result = await create_user_token(test_user_orm)

        token = result["access_token"]
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        assert payload["sub"] == str(test_user_orm.id)
        assert "exp" in payload

    @pytest.mark.unit
    async def test_user_dict_contains_expected_fields(self, test_user_orm):
        """User dict contains id, username, email, role, etc."""
        result = await create_user_token(test_user_orm)

        user_dict = result["user"]
        assert user_dict["id"] == test_user_orm.id
        assert user_dict["username"] == test_user_orm.username
        assert user_dict["email"] == test_user_orm.email
        assert user_dict["role"] == test_user_orm.role
        assert user_dict["avatar_url"] == test_user_orm.avatar_url
        assert "bio" in user_dict
        assert "created_at" in user_dict
