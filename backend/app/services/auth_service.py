from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.db.models import UserProfile, UserSession
from app.integrations.wechat_auth_client import WechatAuthClient
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository
from app.schemas.auth import (
    AuthenticatedUserSchema,
    WechatLoginRequestSchema,
    WechatLoginResponseSchema,
)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_session_repository: UserSessionRepository,
        wechat_auth_client: WechatAuthClient,
    ) -> None:
        self.user_repository = user_repository
        self.user_session_repository = user_session_repository
        self.wechat_auth_client = wechat_auth_client

    async def login_with_wechat(
        self,
        session: AsyncSession,
        payload: WechatLoginRequestSchema,
    ) -> WechatLoginResponseSchema:
        wechat_session = await self.wechat_auth_client.exchange_code(payload.code)
        user = await self.user_repository.get_by_wechat_openid(session, wechat_session.openid)
        is_new_user = user is None
        if user is None:
            user = UserProfile(
                id=f"user-{uuid4().hex[:16]}",
                wechat_openid=wechat_session.openid,
                wechat_unionid=wechat_session.unionid,
                nickname=self._resolve_nickname(payload.nickname, wechat_session.openid),
                avatar_symbol=self._build_avatar_symbol(payload.nickname, wechat_session.openid),
                avatar_url=self._normalize_optional_string(payload.avatar_url),
                streak_days=0,
                total_practices=0,
                weekly_minutes=0,
                pro_active=False,
                plan_name="Free Starter",
                weak_sound="/θ/",
                target_pack="每日回音精选",
                focus_tag="每日一练",
                city=self._normalize_optional_string(payload.city) or "未设置",
                bio=self._normalize_optional_string(payload.bio) or "开始你的每日回音打卡。",
                last_login_at=datetime.now(UTC),
            )
            await self.user_repository.add(session, user)
        else:
            user.wechat_unionid = wechat_session.unionid or user.wechat_unionid
            user.nickname = self._resolve_nickname(payload.nickname, wechat_session.openid, user)
            user.avatar_symbol = self._build_avatar_symbol(user.nickname, wechat_session.openid)
            user.avatar_url = self._normalize_optional_string(payload.avatar_url) or user.avatar_url
            user.city = self._normalize_optional_string(payload.city) or user.city
            user.bio = self._normalize_optional_string(payload.bio) or user.bio
            user.last_login_at = datetime.now(UTC)

        raw_access_token = token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=get_settings().auth_session_days)
        user_session = UserSession(
            id=f"session-{uuid4().hex[:16]}",
            user_id=user.id,
            token_hash=self._hash_token(raw_access_token),
            expires_at=expires_at,
        )
        await self.user_session_repository.add(session, user_session)
        await session.commit()
        await session.refresh(user)

        return WechatLoginResponseSchema(
            access_token=raw_access_token,
            expires_at=expires_at,
            is_new_user=is_new_user,
            user=AuthenticatedUserSchema.model_validate(user),
        )

    async def authenticate_user(
        self,
        session: AsyncSession,
        access_token: str,
    ) -> UserProfile:
        user_session = await self.user_session_repository.get_by_token_hash(
            session,
            self._hash_token(access_token),
        )
        if user_session is None:
            raise UnauthorizedError("登录态无效，请重新登录。", code="invalid_access_token")

        if self._ensure_utc_datetime(user_session.expires_at) <= datetime.now(UTC):
            raise UnauthorizedError("登录态已过期，请重新登录。", code="expired_access_token")

        user = await self.user_repository.get_by_id(session, user_session.user_id)
        if user is None:
            raise UnauthorizedError("当前登录用户不存在。", code="user_not_found")
        return user

    def _hash_token(self, raw_access_token: str) -> str:
        return hashlib.sha256(raw_access_token.encode("utf-8")).hexdigest()

    def _normalize_optional_string(self, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _resolve_nickname(
        self,
        preferred_nickname: str | None,
        openid: str,
        user: UserProfile | None = None,
    ) -> str:
        normalized_nickname = self._normalize_optional_string(preferred_nickname)
        if normalized_nickname is not None:
            return normalized_nickname
        if user is not None and user.nickname.strip():
            return user.nickname
        return f"微信用户{openid[-4:]}"

    def _build_avatar_symbol(self, preferred_nickname: str | None, openid: str) -> str:
        nickname = self._resolve_nickname(preferred_nickname, openid)
        first_character = nickname.strip()[0]
        return first_character.upper()

    def _ensure_utc_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value.astimezone(UTC)
        return value.replace(tzinfo=UTC)
