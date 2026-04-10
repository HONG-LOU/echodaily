from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lesson


class LessonRepository:
    async def get_today(self, session: AsyncSession, *, current_day: date) -> Lesson | None:
        exact_lesson = await self._get_exact_published_lesson(
            session,
            current_day=current_day,
        )
        if exact_lesson is not None:
            return exact_lesson

        rotation_candidates = await self._list_rotation_candidates(
            session,
            current_day=current_day,
        )
        if not rotation_candidates:
            return None

        rotation_start_day = rotation_candidates[0].published_on
        rotation_index = (current_day - rotation_start_day).days % len(rotation_candidates)
        return rotation_candidates[rotation_index]

    async def _get_exact_published_lesson(
        self,
        session: AsyncSession,
        *,
        current_day: date,
    ) -> Lesson | None:
        statement = (
            select(Lesson)
            .where(Lesson.published_on == current_day)
            .order_by(Lesson.id.asc())
            .limit(1)
        )
        return await session.scalar(statement)

    async def _list_rotation_candidates(
        self,
        session: AsyncSession,
        *,
        current_day: date,
    ) -> list[Lesson]:
        statement = (
            select(Lesson)
            .where(Lesson.published_on < current_day)
            .order_by(Lesson.published_on.asc(), Lesson.id.asc())
        )
        return list((await session.scalars(statement)).all())

    async def get_by_id(self, session: AsyncSession, lesson_id: str) -> Lesson | None:
        statement = select(Lesson).where(Lesson.id == lesson_id)
        return await session.scalar(statement)

    async def list_recent(self, session: AsyncSession, *, current_day: date, limit: int = 7) -> list[Lesson]:
        statement = (
            select(Lesson)
            .where(Lesson.published_on <= current_day)
            .order_by(Lesson.published_on.desc(), Lesson.id.desc())
            .limit(limit)
        )
        return list((await session.scalars(statement)).all())
