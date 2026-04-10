from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DailyHomepageMessage


class DailyMessageRepository:
    async def get_by_date(
        self,
        session: AsyncSession,
        *,
        message_date: date,
    ) -> DailyHomepageMessage | None:
        statement = select(DailyHomepageMessage).where(
            DailyHomepageMessage.message_date == message_date
        )
        return await session.scalar(statement)

    async def add(
        self,
        session: AsyncSession,
        message: DailyHomepageMessage,
    ) -> DailyHomepageMessage:
        session.add(message)
        await session.flush()
        return message
