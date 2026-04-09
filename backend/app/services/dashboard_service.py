from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.user_repository import UserRepository
from app.schemas.dashboard import (
    DashboardResponseSchema,
    DashboardUserSchema,
    LessonSpotlightSchema,
    MembershipOfferSchema,
    PartnerPitchSchema,
    RecentScoreSchema,
    StatCardSchema,
)


class DashboardService:
    def __init__(
        self,
        user_repository: UserRepository,
        lesson_repository: LessonRepository,
        challenge_repository: ChallengeRepository,
        assessment_repository: AssessmentRepository,
    ) -> None:
        self.user_repository = user_repository
        self.lesson_repository = lesson_repository
        self.challenge_repository = challenge_repository
        self.assessment_repository = assessment_repository

    async def get_dashboard(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        current_day: date,
    ) -> DashboardResponseSchema:
        user = await self.user_repository.get_by_id(session, user_id)
        if user is None:
            raise NotFoundError("User not found.", code="user_not_found")

        lesson = await self.lesson_repository.get_today(session, current_day=current_day)
        if lesson is None:
            raise NotFoundError("No lesson available yet.", code="lesson_not_found")

        challenges = await self.challenge_repository.list_active(session)
        challenge = challenges[0] if challenges else None
        recent_submissions = await self.assessment_repository.list_recent_by_user(
            session,
            user_id,
            limit=3,
        )

        quick_stats = [
            StatCardSchema(
                label="连续打卡",
                value=f"{user.streak_days} 天",
                caption="离“初试啼声”徽章还差 1 天",
            ),
            StatCardSchema(
                label="本周练习",
                value=f"{user.weekly_minutes} 分钟",
                caption="碎片化练习也能积累质感",
            ),
            StatCardSchema(
                label="弱项音标",
                value=user.weak_sound,
                caption="今天建议盯住这一个细节",
            ),
        ]
        membership_offer = MembershipOfferSchema(
            title="Pro 会员",
            monthly_price="¥15 / 月",
            yearly_price="¥98 / 年",
            highlights=[
                "解锁音素级纠错和错词详情",
                "高级海报模板去水印",
                "历史题库与长期错题本",
            ],
            call_to_action="先用 MVP 验证打卡和转化，再接正式支付。",
        )
        partner_pitch = PartnerPitchSchema(
            title="私域合作入口",
            summary="适合英语博主、雅思工作室和小班课老师作为官方作业打卡工具。",
            bullets=[
                "支持专属内容标签与班级圈原型",
                "天然适合返佣和私域转化",
                "后续可接企业微信沉淀高质量用户",
            ],
            call_to_action="在“我的”页预留老师微信/企微入口即可开启冷启动。",
        )
        recent_scores = [
            RecentScoreSchema(
                assessment_id=item.id,
                lesson_title=item.lesson_id.replace("lesson-", "").replace("-", " ").title(),
                overall_score=item.overall_score,
                practiced_at=item.created_at.strftime("%m/%d %H:%M"),
            )
            for item in recent_submissions
        ]

        challenge_spotlight = (
            {
                "title": challenge.title,
                "participants": challenge.participants,
                "days_left": challenge.days_left,
                "deposit_amount": challenge.deposit_amount,
                "reward_pool": challenge.reward_pool,
                "score_threshold": challenge.score_threshold,
                "teaser": challenge.teaser,
            }
            if challenge is not None
            else {
                "title": "共学挑战筹备中",
                "participants": 0,
                "days_left": 0,
                "deposit_amount": 0,
                "reward_pool": 0,
                "score_threshold": 80,
                "teaser": "下一批挑战营即将开放。",
            }
        )

        return DashboardResponseSchema(
            user=DashboardUserSchema.model_validate(user),
            today_lesson=LessonSpotlightSchema.model_validate(lesson),
            quick_stats=quick_stats,
            challenge_spotlight=challenge_spotlight,
            membership_offer=membership_offer,
            partner_pitch=partner_pitch,
            recent_scores=recent_scores,
        )
