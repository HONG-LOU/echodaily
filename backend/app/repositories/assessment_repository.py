from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Submission


class AssessmentRepository:
    async def add(self, session: AsyncSession, submission: Submission) -> Submission:
        session.add(submission)
        await session.flush()
        await session.refresh(submission)
        return submission

    async def get_by_id(self, session: AsyncSession, assessment_id: str) -> Submission | None:
        statement = select(Submission).where(Submission.id == assessment_id)
        return await session.scalar(statement)

    async def list_recent_by_user(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        limit: int = 3,
    ) -> list[Submission]:
        statement = (
            select(Submission)
            .where(Submission.user_id == user_id)
            .order_by(desc(Submission.created_at))
            .limit(limit)
        )
        result = await session.scalars(statement)
        return list(result.all())

    async def get_latest_by_user(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> Submission | None:
        statement = (
            select(Submission)
            .where(Submission.user_id == user_id)
            .order_by(desc(Submission.created_at))
            .limit(1)
        )
        return await session.scalar(statement)

    async def get_total_duration_by_user_since(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        start_time: datetime,
    ) -> int:
        statement = (
            select(func.coalesce(func.sum(Submission.duration_seconds), 0))
            .where(Submission.user_id == user_id)
            .where(Submission.created_at >= start_time)
        )
        value = await session.scalar(statement)
        return int(value or 0)

    async def get_check_in_dates_by_user_since(
        self,
        session: AsyncSession,
        user_id: str,
        *,
        start_time: datetime,
    ) -> list[str]:
        statement = (
            select(func.distinct(func.date(Submission.created_at)))
            .where(Submission.user_id == user_id)
            .where(Submission.created_at >= start_time)
            .order_by(func.date(Submission.created_at).desc())
        )
        result = await session.scalars(statement)
        # Convert date objects to YYYY-MM-DD string format
        return [str(d) for d in result.all() if d]
