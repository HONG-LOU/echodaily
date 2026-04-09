from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import DbSession, get_auth_service
from app.schemas.auth import WechatLoginRequestSchema, WechatLoginResponseSchema
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/wechat/login", response_model=WechatLoginResponseSchema)
async def login_with_wechat(
    payload: WechatLoginRequestSchema,
    session: DbSession,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> WechatLoginResponseSchema:
    return await service.login_with_wechat(session, payload)
