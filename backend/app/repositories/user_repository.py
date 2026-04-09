from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProfile


class UserRepository:
    async def get_by_id(self, session: AsyncSession, user_id: str) -> UserProfile | None:
        statement = select(UserProfile).where(UserProfile.id == user_id)
        return await session.scalar(statement)
