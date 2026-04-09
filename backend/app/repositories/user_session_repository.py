from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserSession


class UserSessionRepository:
    async def add(self, session: AsyncSession, user_session: UserSession) -> UserSession:
        session.add(user_session)
        await session.flush()
        await session.refresh(user_session)
        return user_session

    async def get_by_token_hash(
        self,
        session: AsyncSession,
        token_hash: str,
    ) -> UserSession | None:
        statement = select(UserSession).where(UserSession.token_hash == token_hash)
        return await session.scalar(statement)
