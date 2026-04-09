from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.user_repository import UserRepository
from app.services.assessment_service import AssessmentService
from app.services.challenge_service import ChallengeService
from app.services.dashboard_service import DashboardService
from app.services.profile_service import ProfileService

DbSession = Annotated[AsyncSession, Depends(get_db_session)]

assessment_repository = AssessmentRepository()
challenge_repository = ChallengeRepository()
lesson_repository = LessonRepository()
user_repository = UserRepository()


def get_dashboard_service() -> DashboardService:
    return DashboardService(
        user_repository=user_repository,
        lesson_repository=lesson_repository,
        challenge_repository=challenge_repository,
        assessment_repository=assessment_repository,
    )


def get_assessment_service() -> AssessmentService:
    return AssessmentService(
        assessment_repository=assessment_repository,
        lesson_repository=lesson_repository,
        user_repository=user_repository,
    )


def get_profile_service() -> ProfileService:
    return ProfileService(
        user_repository=user_repository,
        assessment_repository=assessment_repository,
    )


def get_challenge_service() -> ChallengeService:
    return ChallengeService(challenge_repository=challenge_repository)
