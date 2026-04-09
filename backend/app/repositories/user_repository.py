from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProfile


class UserRepository:
    async def add(self, session: AsyncSession, user: UserProfile) -> UserProfile:
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def get_by_id(self, session: AsyncSession, user_id: str) -> UserProfile | None:
        statement = select(UserProfile).where(UserProfile.id == user_id)
        return await session.scalar(statement)

    async def get_by_wechat_openid(
        self,
        session: AsyncSession,
        wechat_openid: str,
    ) -> UserProfile | None:
        statement = select(UserProfile).where(UserProfile.wechat_openid == wechat_openid)
        return await session.scalar(statement)
