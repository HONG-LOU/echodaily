from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnauthorizedError
from app.db.models import UserProfile
from app.db.session import get_db_session
from app.integrations.tencent_oral_evaluation_client import TencentOralEvaluationClient
from app.integrations.wechat_auth_client import WechatAuthClient
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository
from app.services.assessment_service import AssessmentService
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.profile_service import ProfileService

DbSession = Annotated[AsyncSession, Depends(get_db_session)]

assessment_repository = AssessmentRepository()
lesson_repository = LessonRepository()
user_repository = UserRepository()
user_session_repository = UserSessionRepository()
oral_evaluation_client = TencentOralEvaluationClient()
wechat_auth_client = WechatAuthClient()
bearer_scheme = HTTPBearer(auto_error=False)


def get_dashboard_service() -> DashboardService:
    return DashboardService(
        lesson_repository=lesson_repository,
        assessment_repository=assessment_repository,
    )


def get_assessment_service() -> AssessmentService:
    return AssessmentService(
        assessment_repository=assessment_repository,
        lesson_repository=lesson_repository,
        oral_evaluation_client=oral_evaluation_client,
    )


def get_profile_service() -> ProfileService:
    return ProfileService(
        assessment_repository=assessment_repository,
    )


def get_auth_service() -> AuthService:
    return AuthService(
        user_repository=user_repository,
        user_session_repository=user_session_repository,
        wechat_auth_client=wechat_auth_client,
    )


async def get_current_user(
    session: DbSession,
    service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserProfile:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("缺少登录凭证，请重新登录。", code="missing_access_token")

    return await service.authenticate_user(session, credentials.credentials)


CurrentUser = Annotated[UserProfile, Depends(get_current_user)]
