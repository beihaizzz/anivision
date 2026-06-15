"""
Alembic Environment Configuration

Async migration environment for AniVision.
Loads database URL from application config and uses asyncpg.
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add the backend directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.database import Base

# Import all models so Alembic can detect them for auto-generation
import app.models  # noqa: F401, E402

# ── Alembic Config ────────────────────────────────────────────────────
config = context.config

# Override the sqlalchemy.url from alembic.ini with our application settings
config.set_main_option("sqlalchemy.url", settings.ASYNC_DATABASE_URL)

# Set up Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Metadata ──────────────────────────────────────────────────────────
# Target metadata for 'autogenerate' support
target_metadata = Base.metadata

# Exclude Alembic's own version table from autogenerate detection
# (prevent circular dependency warnings)
def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and name == "alembic_version":
        return False
    return True


# ── Migration Runners ─────────────────────────────────────────────────


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.
    Calls to context.execute() emit SQL to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations synchronously from an async connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode using an async engine.

    Creates an async engine from the config and runs migrations
    within an async context manager, using run_sync to bridge
    async/sync worlds.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations — runs the async runner."""
    asyncio.run(run_async_migrations())


# ── Main ──────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
