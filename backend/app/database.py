"""
Database Configuration

Async SQLAlchemy 2.0 setup with asyncpg driver for PostgreSQL.
Provides session dependency and database initialization utilities.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

# ── Async Engine ──────────────────────────────────────────────────────
# Uses asyncpg for non-blocking database operations
_is_sqlite = "sqlite" in settings.ASYNC_DATABASE_URL.lower()
_engine_kwargs = {
    "echo": False,  # Set to True for SQL debugging
    "pool_pre_ping": True,  # Verify connections before use
}
if not _is_sqlite:
    _engine_kwargs.update({"pool_size": 10, "max_overflow": 20})
engine = create_async_engine(settings.ASYNC_DATABASE_URL, **_engine_kwargs)

# ── Session Factory ───────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
)

# ── Declarative Base ──────────────────────────────────────────────────
# All ORM models inherit from this base class
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    Ensures the session is properly closed after the request,
    even if an exception occurs.

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Create all database tables from ORM metadata.

    Intended for development and testing only.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
