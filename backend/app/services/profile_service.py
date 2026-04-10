from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProfile
from app.repositories.assessment_repository import AssessmentRepository
from app.schemas.profile import (
    MistakeNotebookEntrySchema,
    ProfileResponseSchema,
    RecentPracticeSchema,
)


class ProfileService:
    def __init__(
        self,
        assessment_repository: AssessmentRepository,
    ) -> None:
        self.assessment_repository = assessment_repository

    async def get_profile(
        self,
        session: AsyncSession,
        *,
        current_user: UserProfile,
    ) -> ProfileResponseSchema:
        recent_submissions = await self.assessment_repository.list_recent_by_user(
            session,
            current_user.id,
            limit=6,
        )
        weekly_duration_seconds = await self.assessment_repository.get_total_duration_by_user_since(
            session,
            current_user.id,
            start_time=datetime.now(UTC) - timedelta(days=7),
        )
        weekly_minutes = (
            0 if weekly_duration_seconds == 0 else max(1, round(weekly_duration_seconds / 60))
        )

        check_in_dates = await self.assessment_repository.get_check_in_dates_by_user_since(
            session,
            current_user.id,
            start_time=datetime.now(UTC) - timedelta(days=60),
        )

        notebook: list[MistakeNotebookEntrySchema] = []
        for submission in recent_submissions:
            for highlight in (submission.highlight_words or [])[:2]:
                notebook.append(
                    MistakeNotebookEntrySchema(
                        word=str(highlight["word"]),
                        expected_ipa=str(highlight["expected_ipa"]),
                        coach_tip=str(highlight["coach_tip"]),
                        lesson_title=submission.lesson_id.replace("lesson-", "")
                        .replace("-", " ")
                        .title(),
                        score=submission.overall_score,
                    )
                )

        recent_practices = [
            RecentPracticeSchema(
                assessment_id=submission.id,
                lesson_title=submission.lesson_id.replace("lesson-", "").replace("-", " ").title(),
                score=submission.overall_score,
                practiced_at=submission.created_at.strftime("%m/%d %H:%M"),
            )
            for submission in recent_submissions
        ]

        return ProfileResponseSchema(
            id=current_user.id,
            nickname=current_user.nickname,
            avatar_symbol=current_user.avatar_symbol,
            avatar_url=current_user.avatar_url,
            city=current_user.city,
            bio=current_user.bio,
            streak_days=current_user.streak_days,
            total_practices=current_user.total_practices,
            weekly_minutes=weekly_minutes,
            weak_sound=current_user.weak_sound,
            mistake_notebook=notebook[:6],
            recent_practices=recent_practices,
            check_in_dates=check_in_dates,
        )
