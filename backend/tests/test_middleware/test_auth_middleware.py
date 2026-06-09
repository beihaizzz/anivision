"""
Unit tests for app.middleware.auth_middleware.

Tests get_current_user() and get_current_active_user() with mocked
dependencies — no real database, no HTTP requests.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError

from app.config import settings
from app.middleware.auth_middleware import (
    get_current_active_user,
    get_current_user,
    oauth2_scheme,  # noqa: F401 — imported per test spec
)
from app.models.user import User


# ══════════════════════════════════════════════════════════════════════════
# get_current_user
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.unit
async def test_get_current_user_returns_user_when_token_valid(
    valid_token: str,
    mock_db_with_user: AsyncMock,
    test_user_orm: User,
):
    """Returns the User when the token is valid and user exists in DB."""
    user = await get_current_user(token=valid_token, db=mock_db_with_user)
    assert user == test_user_orm


@pytest.mark.unit
async def test_get_current_user_raises_401_when_token_invalid(
    mock_db_with_user: AsyncMock,
):
    """Raises 401 when the token string is garbage / corrupted."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="not.a.token", db=mock_db_with_user)
    assert exc_info.value.status_code == 401


@pytest.mark.unit
async def test_get_current_user_raises_401_when_sub_missing(
    valid_token: str,
    mock_db_with_user: AsyncMock,
):
    """Raises 401 when the token decodes but the 'sub' claim is absent."""
    with patch("app.middleware.auth_middleware.jwt.decode") as mock_decode:
        mock_decode.return_value = {}  # no "sub" key

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=valid_token, db=mock_db_with_user)

    assert exc_info.value.status_code == 401


@pytest.mark.unit
async def test_get_current_user_raises_401_when_user_not_found(
    valid_token: str,
    mock_db: AsyncMock,
):
    """Raises 401 when the token is valid but the user ID is not in DB."""
    # mock_db.scalar_one_or_none() returns None by default
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=valid_token, db=mock_db)
    assert exc_info.value.status_code == 401


@pytest.mark.unit
async def test_get_current_user_raises_401_when_token_expired(
    expired_token: str,
    mock_db_with_user: AsyncMock,
):
    """Raises 401 when the token has expired.

    Verifies the token is genuinely expired first by decoding with
    leeway=0, then confirms get_current_user rejects it.
    """
    from jose import jwt

    # Confirm the expired token (60 min past expiry) raises JWTError
    with pytest.raises(JWTError):
        jwt.decode(
            expired_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=expired_token, db=mock_db_with_user)
    assert exc_info.value.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# get_current_active_user
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.unit
async def test_get_current_active_user_returns_user_when_active(
    test_user_orm: User,
):
    """Returns the User when is_active is True."""
    user = await get_current_active_user(current_user=test_user_orm)
    assert user == test_user_orm


@pytest.mark.unit
async def test_get_current_active_user_raises_403_when_inactive(
    inactive_user_orm: User,
):
    """Raises 403 when the user's is_active flag is False."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=inactive_user_orm)
    assert exc_info.value.status_code == 403
