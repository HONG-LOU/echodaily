import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models import Base, Lesson
from app.db.seed import LESSON_SEEDS, seed_database
from app.db.session import _ensure_lessons_audio_url_column
from app.repositories.lesson_repository import LessonRepository


def build_lesson(*, lesson_id: str, published_on: date) -> Lesson:
    return Lesson(
        id=lesson_id,
        title=f"Title for {lesson_id}",
        subtitle="Subtitle",
        pack_name="Pack",
        english_text=f"Practice copy for {lesson_id}.",
        translation="Translation",
        scenario="Scenario",
        mode_hint="Hint",
        blind_box_prompt="Prompt",
        tags=["tag"],
        difficulty="Beginner",
        estimated_seconds=15,
        poster_blurb="Poster blurb",
        theme_tone="tone",
        published_on=published_on,
    )


@asynccontextmanager
async def create_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_get_today_rotates_after_last_scheduled_lesson() -> None:
    repository = LessonRepository()

    async with create_session() as session:
        await seed_database(session)

        first_rotation = await repository.get_today(
            session,
            current_day=date(2026, 4, 10),
        )
        second_rotation = await repository.get_today(
            session,
            current_day=date(2026, 4, 11),
        )

    assert first_rotation is not None
    assert first_rotation.id == "lesson-bbc-morning"
    assert second_rotation is not None
    assert second_rotation.id == "lesson-movie-whisper"


@pytest.mark.asyncio
async def test_get_today_prefers_exact_schedule_over_rotation() -> None:
    repository = LessonRepository()

    async with create_session() as session:
        session.add_all(
            [
                build_lesson(
                    lesson_id="lesson-alpha",
                    published_on=date(2026, 4, 1),
                ),
                build_lesson(
                    lesson_id="lesson-beta",
                    published_on=date(2026, 4, 3),
                ),
                build_lesson(
                    lesson_id="lesson-explicit",
                    published_on=date(2026, 4, 10),
                ),
            ]
        )
        await session.commit()

        lesson = await repository.get_today(
            session,
            current_day=date(2026, 4, 10),
        )

    assert lesson is not None
    assert lesson.id == "lesson-explicit"


@pytest.mark.asyncio
async def test_seed_database_backfills_missing_seed_lessons() -> None:
    async with create_session() as session:
        session.add(LESSON_SEEDS[0].to_model())
        await session.commit()

        await seed_database(session)
        lesson_count = await session.scalar(select(func.count()).select_from(Lesson))

    assert lesson_count == len(LESSON_SEEDS)


@pytest.mark.asyncio
async def test_schema_patch_adds_missing_lessons_audio_url_column() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    try:
        async with engine.begin() as connection:
            await connection.execute(text("CREATE TABLE lessons (id VARCHAR(64) PRIMARY KEY)"))
            await connection.run_sync(_ensure_lessons_audio_url_column)
            await connection.run_sync(_ensure_lessons_audio_url_column)
            column_names = await connection.run_sync(
                lambda sync_connection: {
                    column["name"]
                    for column in inspect(sync_connection).get_columns("lessons")
                }
            )
    finally:
        await engine.dispose()

    assert "audio_url" in column_names
