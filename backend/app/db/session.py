from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.models import Base


def _ensure_sqlite_directory() -> None:
    settings = get_settings()
    sqlite_prefix = "sqlite+aiosqlite:///"
    if not settings.database_url.startswith(sqlite_prefix):
        return

    raw_path = settings.database_url.removeprefix(sqlite_prefix)
    if raw_path.startswith("/"):
        database_path = Path(raw_path)
    else:
        database_path = Path.cwd() / raw_path
    database_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_engine() -> AsyncEngine:
    _ensure_sqlite_directory()
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def init_db() -> None:
    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(_ensure_lessons_audio_url_column)


def _ensure_lessons_audio_url_column(connection: Connection) -> None:
    inspector = inspect(connection)
    if "lessons" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("lessons")}
    if "audio_url" in column_names:
        return

    # Keep startup resilient when old databases miss newly added nullable columns.
    connection.execute(text("ALTER TABLE lessons ADD COLUMN audio_url VARCHAR(512)"))


async def close_db() -> None:
    await get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def reset_db_caches() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
