from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProfile
from app.repositories.assessment_repository import AssessmentRepository
from app.schemas.profile import (
    BadgeSchema,
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
        badges = [
            BadgeSchema(
                name="初试啼声",
                description="连续打卡 7 天解锁",
                unlocked=current_user.streak_days >= 7,
            ),
            BadgeSchema(
                name="音标终结者",
                description="累计纠错 100 词解锁",
                unlocked=current_user.total_practices >= 30,
            ),
            BadgeSchema(name="晨光俱乐部", description="加入一次 21 天挑战营", unlocked=True),
        ]

        notebook: list[MistakeNotebookEntrySchema] = []
        for submission in recent_submissions:
            for highlight in submission.highlight_words[:1]:
                notebook.append(
                    MistakeNotebookEntrySchema(
                        word=highlight["word"],
                        expected_ipa=highlight["expected_ipa"],
                        coach_tip=highlight["coach_tip"],
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
                poster_caption=submission.poster_caption,
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
            weekly_minutes=current_user.weekly_minutes,
            weak_sound=current_user.weak_sound,
            target_pack=current_user.target_pack,
            plan_name=current_user.plan_name,
            pro_active=current_user.pro_active,
            badges=badges,
            mistake_notebook=notebook[:4],
            recent_practices=recent_practices,
            coach_cta={
                "title": "添加真人纠音老师微信",
                "description": "把高活跃用户沉淀到私域，后续可承接 1 对 1 陪练和课程转化。",
                "wechat_hint": "EchoCoach_2026",
            },
            membership_hint={
                "title": "Pro 转化位",
                "description": "把“错了哪些词”和“高级海报模板”作为主要卡点。",
                "highlights": [
                    "首月 9.9 更适合冷启动测试",
                    "激励视频广告可作为免费解锁路径",
                    "历史题库和 PDF 导出适合包年卡",
                ],
            },
        )
