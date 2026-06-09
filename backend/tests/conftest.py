"""
AniVision Test Conftest

Shared pytest fixtures for all test modules.
Provides mocked database sessions, test client, and test user data.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock settings BEFORE importing any application code
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///")
os.environ.setdefault("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///")
os.environ.setdefault("CORS_ORIGINS", '["*"]')
os.environ.setdefault("UPLOAD_DIR", "./test_uploads")
os.environ.setdefault("GENERATED_DIR", "./test_generated")
os.environ.setdefault("MODEL_PATH", "./test_model.pth")
os.environ.setdefault("LABEL_MAP_PATH", "./test_label_map.json")

from app.config import settings
from app.models.user import User


# ══════════════════════════════════════════════════════════════════════
# Test Data Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def test_user_data() -> dict:
    """Valid user registration and login data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongP@ss1",
    }


@pytest.fixture
def weak_password_data() -> dict:
    """User data with a password that fails strength checks."""
    return {
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "short",
    }


@pytest.fixture
def test_user_orm() -> User:
    """A fully populated User ORM instance (not persisted)."""
    from app.utils.security import get_password_hash

    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("StrongP@ss1"),
        avatar_url="https://example.com/avatar.png",
        bio="Test user bio",
        role="user",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def admin_user_orm() -> User:
    """An admin User ORM instance."""
    from app.utils.security import get_password_hash

    return User(
        id=2,
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("AdminP@ss1"),
        role="admin",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def inactive_user_orm() -> User:
    """A deactivated User ORM instance."""
    from app.utils.security import get_password_hash

    return User(
        id=3,
        username="inactive",
        email="inactive@example.com",
        password_hash=get_password_hash("Inactive1"),
        role="user",
        is_active=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# ══════════════════════════════════════════════════════════════════════
# JWT Token Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def valid_token(test_user_orm: User) -> str:
    """A valid JWT access token for the test user."""
    from app.utils.security import create_access_token

    return create_access_token(data={"sub": str(test_user_orm.id)})


@pytest.fixture
def expired_token(test_user_orm: User) -> str:
    """An expired JWT access token."""
    from app.utils.security import create_access_token

    return create_access_token(
        data={"sub": str(test_user_orm.id)},
        expires_delta=timedelta(minutes=-60),
    )


@pytest.fixture
def admin_token(admin_user_orm: User) -> str:
    """Valid JWT token for admin user."""
    from app.utils.security import create_access_token

    return create_access_token(data={"sub": str(admin_user_orm.id)})


# ══════════════════════════════════════════════════════════════════════
# Mocked DB Session
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mocked AsyncSession for unit testing DB-dependent code.

    Provides:
    - mock_db.execute() → returns a mock with .scalar_one_or_none() / .scalar()
    - mock_db.add()
    - mock_db.flush()
    - mock_db.refresh()
    - mock_db.commit()
    - mock_db.rollback()
    """
    session = AsyncMock(spec=AsyncSession)

    # Default execute result
    # NOTE: scalar_one_or_none / scalar / all are *sync* methods on
    # SQLAlchemy's Result; use MagicMock so they return values directly
    # instead of coroutines.
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_result.scalar = MagicMock(return_value=None)
    mock_result.all = MagicMock(return_value=[])
    session.execute.return_value = mock_result
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()

    return session


@pytest.fixture
def mock_db_with_user(mock_db: AsyncMock, test_user_orm: User) -> AsyncMock:
    """Mocked AsyncSession that returns the test user on execute."""
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=test_user_orm)
    mock_result.scalar = MagicMock(return_value=test_user_orm)
    mock_db.execute.return_value = mock_result
    return mock_db


# ══════════════════════════════════════════════════════════════════════
# FastAPI Test Client
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def app() -> FastAPI:
    """FastAPI application instance for testing."""
    # We must import main AFTER environment is set
    from app.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Synchronous TestClient for simple endpoint tests."""
    return TestClient(app)


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing async endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ══════════════════════════════════════════════════════════════════════
# Dependency Override Helpers
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def override_get_db(app: FastAPI, mock_db: AsyncMock):
    """Override the get_db dependency with a mock session."""
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield mock_db

    app.dependency_overrides["get_db"] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_get_current_user(app: FastAPI, test_user_orm: User):
    """Override get_current_active_user with a test user."""
    async def _override_get_current_user() -> User:
        return test_user_orm

    # We need to find the dependency key. FastAPI uses function references.
    # Instead, patch the middleware's get_current_active_user
    from app.middleware import auth_middleware

    original = auth_middleware.get_current_active_user
    auth_middleware.get_current_active_user = lambda: _override_get_current_user
    yield
    auth_middleware.get_current_active_user = original


# ══════════════════════════════════════════════════════════════════════
# Cleanup
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _clean_settings():
    """Reset settings to defaults after each test."""
    from app.config import settings as s

    original_secret = s.SECRET_KEY
    original_algorithm = s.ALGORITHM
    original_expire = s.ACCESS_TOKEN_EXPIRE_MINUTES

    yield

    s.SECRET_KEY = original_secret
    s.ALGORITHM = original_algorithm
    s.ACCESS_TOKEN_EXPIRE_MINUTES = original_expire
