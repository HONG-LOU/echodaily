from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Challenge


class ChallengeRepository:
    async def list_active(self, session: AsyncSession) -> list[Challenge]:
        statement = (
            select(Challenge)
            .where(Challenge.is_active.is_(True))
            .order_by(desc(Challenge.reward_pool), Challenge.days_left)
        )
        result = await session.scalars(statement)
        return list(result.all())
