from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.errors import BadRequestError, IntegrationError, ServiceUnavailableError

WECHAT_CODE_TO_SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
INVALID_WECHAT_LOGIN_CODES = {40029, 40163}


@dataclass(slots=True)
class WechatSessionData:
    openid: str
    unionid: str | None


class WechatAuthClient:
    async def exchange_code(self, code: str) -> WechatSessionData:
        settings = get_settings()
        if settings.wechat_app_id is None or settings.wechat_app_secret is None:
            raise ServiceUnavailableError(
                "微信登录尚未配置，请先设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET。",
                code="wechat_login_not_configured",
            )

        params = {
            "appid": settings.wechat_app_id,
            "secret": settings.wechat_app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(WECHAT_CODE_TO_SESSION_URL, params=params)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise IntegrationError(
                "微信登录服务暂时不可用，请稍后再试。",
                code="wechat_login_unavailable",
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationError(
                "微信登录服务返回了无效响应。",
                code="wechat_login_invalid_response",
            ) from exc

        errcode = payload.get("errcode")
        if isinstance(errcode, int):
            if errcode in INVALID_WECHAT_LOGIN_CODES:
                raise BadRequestError(
                    "微信登录 code 无效或已过期，请重新进入小程序后再试一次。",
                    code="wechat_login_code_invalid",
                )
            raise IntegrationError(
                "微信登录失败，请稍后重试。",
                code="wechat_login_failed",
            )

        openid = payload.get("openid")
        if not isinstance(openid, str) or not openid.strip():
            raise IntegrationError(
                "微信登录响应缺少 openid。",
                code="wechat_login_invalid_response",
            )

        unionid = payload.get("unionid")
        normalized_unionid = (
            unionid.strip() if isinstance(unionid, str) and unionid.strip() else None
        )

        return WechatSessionData(openid=openid.strip(), unionid=normalized_unionid)
