from __future__ import annotations

from sqlalchemy import desc, select
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
