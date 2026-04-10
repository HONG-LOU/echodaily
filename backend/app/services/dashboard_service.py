from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models import UserProfile
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.lesson_repository import LessonRepository
from app.schemas.dashboard import (
    DashboardResponseSchema,
    DashboardUserSchema,
    LessonSpotlightSchema,
    RecentScoreSchema,
    StatCardSchema,
)


class DashboardService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        assessment_repository: AssessmentRepository,
    ) -> None:
        self.lesson_repository = lesson_repository
        self.assessment_repository = assessment_repository

    async def get_dashboard(
        self,
        session: AsyncSession,
        *,
        current_user: UserProfile,
        current_day: date,
    ) -> DashboardResponseSchema:
        lesson = await self.lesson_repository.get_today(session, current_day=current_day)
        if lesson is None:
            raise NotFoundError("No lesson available yet.", code="lesson_not_found")

        recent_submissions = await self.assessment_repository.list_recent_by_user(
            session,
            current_user.id,
            limit=3,
        )
        weekly_duration_seconds = await self.assessment_repository.get_total_duration_by_user_since(
            session,
            current_user.id,
            start_time=datetime.now(UTC) - timedelta(days=7),
        )
        weekly_minutes = (
            0 if weekly_duration_seconds == 0 else max(1, round(weekly_duration_seconds / 60))
        )
        quick_stats = [
            StatCardSchema(
                label="连续练习",
                value=f"{current_user.streak_days} 天",
                caption="保持每天开口，稳定感会比突击更重要。",
            ),
            StatCardSchema(
                label="累计练习",
                value=f"{current_user.total_practices} 次",
                caption="每一次录音都会沉淀成你的发音样本。",
            ),
            StatCardSchema(
                label="重点音素",
                value=current_user.weak_sound,
                caption="下一次练习优先盯住这个发音细节。",
            ),
        ]
        recent_scores = [
            RecentScoreSchema(
                assessment_id=item.id,
                lesson_title=item.lesson_id.replace("lesson-", "").replace("-", " ").title(),
                overall_score=item.overall_score,
                practiced_at=item.created_at.strftime("%m/%d %H:%M"),
            )
            for item in recent_submissions
        ]

        return DashboardResponseSchema(
            user=DashboardUserSchema(
                id=current_user.id,
                nickname=current_user.nickname,
                avatar_symbol=current_user.avatar_symbol,
                avatar_url=current_user.avatar_url,
                streak_days=current_user.streak_days,
                total_practices=current_user.total_practices,
                weekly_minutes=weekly_minutes,
                weak_sound=current_user.weak_sound,
                city=current_user.city,
                bio=current_user.bio,
            ),
            today_lesson=LessonSpotlightSchema.model_validate(lesson),
            quick_stats=quick_stats,
            recent_scores=recent_scores,
        )
