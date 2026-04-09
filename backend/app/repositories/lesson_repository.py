from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lesson


class LessonRepository:
    async def get_today(self, session: AsyncSession, *, current_day: date) -> Lesson | None:
        statement = (
            select(Lesson)
            .where(Lesson.published_on <= current_day)
            .order_by(Lesson.published_on.desc())
            .limit(1)
        )
        return await session.scalar(statement)

    async def get_by_id(self, session: AsyncSession, lesson_id: str) -> Lesson | None:
        statement = select(Lesson).where(Lesson.id == lesson_id)
        return await session.scalar(statement)
