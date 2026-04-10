from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models import Lesson, Submission, UserProfile
from app.integrations.tencent_oral_evaluation_client import (
    EvaluatedWord,
    OralEvaluationResult,
    TencentOralEvaluationClient,
)
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.lesson_repository import LessonRepository
from app.schemas.assessment import (
    AssessmentCreateSchema,
    AssessmentDetailSchema,
    AssessmentDimensionSchema,
    AssessmentHighlightSchema,
)

MATCH_TAG_MISSING = 2
MATCH_TAG_MISREAD = 3


class AssessmentService:
    def __init__(
        self,
        assessment_repository: AssessmentRepository,
        lesson_repository: LessonRepository,
        oral_evaluation_client: TencentOralEvaluationClient,
    ) -> None:
        self.assessment_repository = assessment_repository
        self.lesson_repository = lesson_repository
        self.oral_evaluation_client = oral_evaluation_client

    async def create_assessment(
        self,
        session: AsyncSession,
        current_user: UserProfile,
        payload: AssessmentCreateSchema,
    ) -> AssessmentDetailSchema:
        lesson = await self.lesson_repository.get_by_id(session, payload.lesson_id)
        if lesson is None:
            raise NotFoundError("Lesson not found.", code="lesson_not_found")

        latest_submission = await self.assessment_repository.get_latest_by_user(
            session,
            current_user.id,
        )
        evaluation = await self.oral_evaluation_client.evaluate_sentence(
            reference_text=lesson.english_text,
            audio_base64=payload.audio_base64,
            audio_format=payload.audio_format,
        )
        highlights = self._build_highlights(evaluation.words)
        rhythm_score = self._build_rhythm_score(evaluation=evaluation)
        headline, encouragement = self._build_copy(
            overall_score=evaluation.overall_score,
            highlights=highlights,
        )
        created_at = datetime.now(UTC)

        submission = Submission(
            id=f"assessment-{uuid4().hex[:16]}",
            user_id=current_user.id,
            lesson_id=lesson.id,
            mode="follow",
            duration_seconds=payload.duration_seconds,
            transcript=evaluation.recognized_text or None,
            transcript_used=bool(evaluation.recognized_text),
            comparison_ratio=round(evaluation.completeness_score / 100, 2),
            overall_score=evaluation.overall_score,
            pronunciation_score=evaluation.pronunciation_score,
            fluency_score=evaluation.fluency_score,
            intonation_score=rhythm_score,
            stress_score=evaluation.stress_score,
            completeness_score=evaluation.completeness_score,
            mistake_count=len(highlights),
            highlight_words=highlights,
            headline=headline,
            encouragement=encouragement,
            poster_caption=evaluation.request_id or "tencentcloud-soe",
            poster_theme=payload.audio_format,
            created_at=created_at,
        )
        await self.assessment_repository.add(session, submission)
        self._update_user_progress(
            current_user=current_user,
            latest_submission=latest_submission,
            created_at=created_at,
            duration_seconds=payload.duration_seconds,
            highlights=highlights,
        )
        await session.commit()
        return self._build_detail_schema(submission=submission, lesson=lesson)

    async def get_assessment(
        self,
        session: AsyncSession,
        current_user: UserProfile,
        assessment_id: str,
    ) -> AssessmentDetailSchema:
        submission = await self.assessment_repository.get_by_id(session, assessment_id)
        if submission is None or submission.user_id != current_user.id:
            raise NotFoundError("Assessment not found.", code="assessment_not_found")

        lesson = await self.lesson_repository.get_by_id(session, submission.lesson_id)
        if lesson is None:
            raise NotFoundError("Lesson not found.", code="lesson_not_found")

        return self._build_detail_schema(submission=submission, lesson=lesson)

    def _build_detail_schema(
        self,
        *,
        submission: Submission,
        lesson: Lesson,
    ) -> AssessmentDetailSchema:
        dimensions = [
            AssessmentDimensionSchema(
                key="pronunciation",
                label="发音",
                score=submission.pronunciation_score,
            ),
            AssessmentDimensionSchema(
                key="fluency",
                label="流利度",
                score=submission.fluency_score,
            ),
            AssessmentDimensionSchema(
                key="completeness",
                label="完整度",
                score=submission.completeness_score,
            ),
            AssessmentDimensionSchema(
                key="stress",
                label="重音",
                score=submission.stress_score,
            ),
            AssessmentDimensionSchema(
                key="rhythm",
                label="节奏",
                score=submission.intonation_score,
            ),
        ]
        highlights = [
            AssessmentHighlightSchema.model_validate(item)
            for item in (submission.highlight_words or [])
        ]
        return AssessmentDetailSchema(
            id=submission.id,
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            lesson_text=lesson.english_text,
            translation=lesson.translation,
            duration_seconds=submission.duration_seconds,
            recognized_text=submission.transcript or "",
            overall_score=submission.overall_score,
            mistake_count=submission.mistake_count,
            headline=submission.headline,
            encouragement=submission.encouragement,
            created_at=submission.created_at,
            dimensions=dimensions,
            highlights=highlights,
        )

    def _build_rhythm_score(self, *, evaluation: OralEvaluationResult) -> int:
        return round((evaluation.fluency_score * 0.6) + (evaluation.stress_score * 0.4))

    def _build_highlights(self, words: list[EvaluatedWord]) -> list[dict[str, str | int]]:
        focus_words = [word for word in words if self._needs_attention(word)]
        ranked_words = sorted(
            focus_words,
            key=lambda item: (
                self._severity_rank(item),
                item.pronunciation_score,
                item.fluency_score,
            ),
        )

        highlights: list[dict[str, str | int]] = []
        for word in ranked_words[:5]:
            severity = self._build_severity(word)
            highlights.append(
                {
                    "word": word.word or "未识别词",
                    "expected_ipa": word.expected_ipa or "待人工复核",
                    "observed_ipa": word.observed_ipa or "未形成有效发音",
                    "accuracy_score": word.pronunciation_score,
                    "observed_issue": self._build_issue(word),
                    "coach_tip": self._build_tip(word),
                    "severity": severity,
                }
            )
        return highlights

    def _needs_attention(self, word: EvaluatedWord) -> bool:
        if not word.word:
            return False
        return (
            word.match_tag in {MATCH_TAG_MISSING, MATCH_TAG_MISREAD}
            or word.pronunciation_score < 80
            or word.stress_mismatch_count > 0
        )

    def _severity_rank(self, word: EvaluatedWord) -> int:
        severity = self._build_severity(word)
        order = {"high": 0, "medium": 1, "low": 2}
        return order[severity]

    def _build_severity(self, word: EvaluatedWord) -> str:
        if (
            word.match_tag in {MATCH_TAG_MISSING, MATCH_TAG_MISREAD}
            or word.pronunciation_score < 60
        ):
            return "high"
        if word.pronunciation_score < 80 or word.stress_mismatch_count > 0:
            return "medium"
        return "low"

    def _build_issue(self, word: EvaluatedWord) -> str:
        if word.match_tag == MATCH_TAG_MISSING:
            return "这一词没有被完整识别出来，句子完整度被拉低了。"
        if word.match_tag == MATCH_TAG_MISREAD:
            if word.expected_ipa and word.observed_ipa and word.expected_ipa != word.observed_ipa:
                return f"检测到 {word.observed_ipa}，与标准 {word.expected_ipa} 有偏差。"
            return "这一词与标准读法的匹配度偏低。"
        if word.stress_mismatch_count > 0:
            return "重音位置不稳定，听感会偏平。"
        return "音素准确度偏低，需要拆词重练。"

    def _build_tip(self, word: EvaluatedWord) -> str:
        if word.match_tag == MATCH_TAG_MISSING:
            return "先单独补读这一词，再回到整句做一遍完整跟读。"
        if word.stress_mismatch_count > 0:
            return "先找主重音音节，重读拉开后再连回整句。"
        if word.expected_ipa:
            return f"对照标准音素 {word.expected_ipa}，拆成慢速两遍再恢复正常语速。"
        return "先放慢半拍，把词尾和主元音读清楚后再复练。"

    def _build_copy(
        self,
        *,
        overall_score: int,
        highlights: list[dict[str, str | int]],
    ) -> tuple[str, str]:
        if overall_score >= 90:
            headline = "这一遍已经很稳了"
        elif overall_score >= 80:
            headline = "整体发音已经接近标准"
        elif overall_score >= 70:
            headline = "主要问题已经收敛到少数几个词"
        else:
            headline = "先把清晰度稳住，再追求自然度"

        if not highlights:
            return headline, "继续保持当前节奏，再练一遍可以进一步拉高稳定性。"

        focus_word = str(highlights[0]["word"])
        return headline, f"下一步优先处理 {focus_word}，整句得分会提升得更明显。"

    def _update_user_progress(
        self,
        *,
        current_user: UserProfile,
        latest_submission: Submission | None,
        created_at: datetime,
        duration_seconds: int,
        highlights: list[dict[str, str | int]],
    ) -> None:
        current_user.total_practices += 1
        current_user.weekly_minutes += max(1, round(duration_seconds / 60))
        current_user.streak_days = self._next_streak_days(
            latest_submission=latest_submission,
            current_streak_days=current_user.streak_days,
            current_day=created_at.date(),
        )
        if highlights:
            current_user.weak_sound = str(highlights[0]["expected_ipa"])

    def _next_streak_days(
        self,
        *,
        latest_submission: Submission | None,
        current_streak_days: int,
        current_day: date,
    ) -> int:
        if latest_submission is None:
            return 1

        latest_day = self._to_utc_datetime(latest_submission.created_at).date()
        if latest_day == current_day:
            return max(current_streak_days, 1)
        if latest_day == current_day - timedelta(days=1):
            return max(current_streak_days, 0) + 1
        return 1

    def _to_utc_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
