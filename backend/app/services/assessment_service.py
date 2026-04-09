from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from difflib import SequenceMatcher
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models import Lesson, Submission
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.user_repository import UserRepository
from app.schemas.assessment import (
    AssessmentCreateSchema,
    AssessmentDetailSchema,
    AssessmentDimensionSchema,
    AssessmentHighlightSchema,
)

WORD_COACH_LIBRARY: dict[str, tuple[str, str, str]] = {
    "clear": ("/klɪr/", "元音拉得不够开。", "先把 /kl/ 贴紧，再把 /ɪr/ 拉圆一点。"),
    "concise": ("/kənˈsaɪs/", "重音没有落稳在第二拍。", "前轻后重，把 /saɪs/ 明确抬起来。"),
    "meeting": ("/ˈmiːtɪŋ/", "尾音 /ŋ/ 收得太急。", "结尾别咬成 /n/，让鼻音轻轻挂住。"),
    "kind": ("/kaɪnd/", "双元音过短，听感偏扁。", "把 /kaɪ/ 放慢半拍，再落到 /nd/。"),
    "softly": ("/ˈsɒftli/", "中间的 /f/ 摩擦感偏弱。", "上齿轻碰下唇，把气流送出来。"),
    "fear": ("/fɪr/", "元音偏平，少了张力。", "像轻轻叹气一样把 /ɪr/ 拉开。"),
    "courage": ("/ˈkʌrɪdʒ/", "结尾 /dʒ/ 不够干净。", "重音先给足，再把尾辅音收利落。"),
    "quiet": ("/ˈkwaɪət/", "双元音收得太快。", "先打开 /kwaɪ/，再轻轻落到 /ət/。"),
    "choices": ("/ˈtʃɔɪsɪz/", "尾音 /ɪz/ 略弱。", "最后一拍别吞掉，轻轻弹出来。"),
    "brave": ("/breɪv/", "元音延展度不够。", "把 /eɪ/ 再抬高一点，声音会更亮。"),
}


class AssessmentService:
    def __init__(
        self,
        assessment_repository: AssessmentRepository,
        lesson_repository: LessonRepository,
        user_repository: UserRepository,
    ) -> None:
        self.assessment_repository = assessment_repository
        self.lesson_repository = lesson_repository
        self.user_repository = user_repository

    async def create_assessment(
        self,
        session: AsyncSession,
        payload: AssessmentCreateSchema,
    ) -> AssessmentDetailSchema:
        lesson = await self.lesson_repository.get_by_id(session, payload.lesson_id)
        if lesson is None:
            raise NotFoundError("Lesson not found.", code="lesson_not_found")

        user = await self.user_repository.get_by_id(session, payload.user_id)
        if user is None:
            raise NotFoundError("User not found.", code="user_not_found")

        result = self._evaluate_lesson(lesson=lesson, payload=payload)
        submission = Submission(
            id=f"assessment-{uuid4().hex[:16]}",
            user_id=payload.user_id,
            lesson_id=lesson.id,
            mode=payload.mode,
            duration_seconds=payload.duration_seconds,
            transcript=payload.transcript,
            transcript_used=result["transcript_used"],
            comparison_ratio=result["comparison_ratio"],
            overall_score=result["overall_score"],
            pronunciation_score=result["pronunciation"],
            fluency_score=result["fluency"],
            intonation_score=result["intonation"],
            stress_score=result["stress"],
            completeness_score=result["completeness"],
            mistake_count=len(result["highlights"]),
            highlight_words=result["highlights"],
            headline=result["headline"],
            encouragement=result["encouragement"],
            poster_caption=result["poster_caption"],
            poster_theme=result["poster_theme"],
            created_at=datetime.now(UTC),
        )
        await self.assessment_repository.add(session, submission)
        user.total_practices += 1
        user.weekly_minutes += max(1, round(payload.duration_seconds / 60))
        await session.commit()
        return self._build_detail_schema(submission=submission, lesson=lesson)

    async def get_assessment(
        self,
        session: AsyncSession,
        assessment_id: str,
    ) -> AssessmentDetailSchema:
        submission = await self.assessment_repository.get_by_id(session, assessment_id)
        if submission is None:
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
                key="intonation",
                label="语调",
                score=submission.intonation_score,
            ),
            AssessmentDimensionSchema(
                key="stress",
                label="重音",
                score=submission.stress_score,
            ),
            AssessmentDimensionSchema(
                key="completeness",
                label="完整度",
                score=submission.completeness_score,
            ),
        ]
        highlights = [
            AssessmentHighlightSchema.model_validate(item) for item in submission.highlight_words
        ]
        return AssessmentDetailSchema(
            id=submission.id,
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            lesson_text=lesson.english_text,
            translation=lesson.translation,
            mode=submission.mode,
            duration_seconds=submission.duration_seconds,
            transcript=submission.transcript,
            transcript_used=submission.transcript_used,
            overall_score=submission.overall_score,
            comparison_ratio=submission.comparison_ratio,
            mistake_count=submission.mistake_count,
            headline=submission.headline,
            encouragement=submission.encouragement,
            poster_caption=submission.poster_caption,
            poster_theme=submission.poster_theme,
            created_at=submission.created_at,
            dimensions=dimensions,
            highlights=highlights,
        )

    def _evaluate_lesson(
        self,
        *,
        lesson: Lesson,
        payload: AssessmentCreateSchema,
    ) -> dict[str, object]:
        target_words = self._tokenize(lesson.english_text)
        transcript_words = self._tokenize(payload.transcript or "")
        transcript_used = bool(transcript_words)

        if transcript_used:
            comparison_ratio = SequenceMatcher(
                None,
                " ".join(target_words),
                " ".join(transcript_words),
            ).ratio()
            completeness_ratio = min(len(transcript_words) / max(len(target_words), 1), 1.0)
            missing_words = self._missing_words(
                target_words=target_words,
                transcript_words=transcript_words,
            )
        else:
            duration_ratio = payload.duration_seconds / max(lesson.estimated_seconds, 1)
            seeded_lift = self._stable_float(
                f"{lesson.id}:{payload.duration_seconds}:{payload.mode}"
            )
            comparison_ratio = self._clamp(
                0.66 + min(duration_ratio, 1.15) * 0.18 + seeded_lift * 0.08,
                0.6,
                0.92,
            )
            completeness_ratio = self._clamp(
                0.7 + min(duration_ratio, 1.1) * 0.18 + seeded_lift * 0.06,
                0.62,
                0.96,
            )
            missing_words = self._pick_focus_words(
                target_words,
                count=max(2, round((1 - comparison_ratio) * 6)),
            )

        pace_gap = abs(payload.duration_seconds - lesson.estimated_seconds) / max(
            lesson.estimated_seconds,
            1,
        )
        pronunciation = round(
            self._clamp(56 + comparison_ratio * 38 - len(missing_words) * 2, 55, 97)
        )
        fluency = round(
            self._clamp(62 + (1 - min(pace_gap, 1)) * 22 + comparison_ratio * 8, 58, 96)
        )
        intonation = round(
            self._clamp(
                60 + comparison_ratio * 25 + self._stable_delta(f"{lesson.id}:intonation", 0, 6),
                58,
                95,
            )
        )
        stress = round(
            self._clamp(
                59 + comparison_ratio * 24 + self._stable_delta(f"{payload.mode}:stress", 0, 5),
                57,
                94,
            )
        )
        completeness = round(self._clamp(54 + completeness_ratio * 42, 55, 97))
        overall_score = round(
            pronunciation * 0.28
            + fluency * 0.2
            + intonation * 0.18
            + stress * 0.14
            + completeness * 0.2
        )

        highlights = self._build_highlights(missing_words)
        headline, encouragement = self._build_copy(overall_score=overall_score, lesson=lesson)
        poster_caption = self._build_poster_caption(overall_score=overall_score, lesson=lesson)

        return {
            "transcript_used": transcript_used,
            "comparison_ratio": round(comparison_ratio, 2),
            "overall_score": overall_score,
            "pronunciation": pronunciation,
            "fluency": fluency,
            "intonation": intonation,
            "stress": stress,
            "completeness": completeness,
            "highlights": highlights,
            "headline": headline,
            "encouragement": encouragement,
            "poster_caption": poster_caption,
            "poster_theme": lesson.theme_tone,
        }

    def _missing_words(self, *, target_words: list[str], transcript_words: list[str]) -> list[str]:
        transcript_lookup = set(transcript_words)
        missing_words: list[str] = []
        for word in target_words:
            if word not in transcript_lookup and word not in missing_words:
                missing_words.append(word)
        if missing_words:
            return missing_words[:3]
        return self._pick_focus_words(target_words, count=2)

    def _pick_focus_words(self, target_words: list[str], *, count: int) -> list[str]:
        candidates = sorted(
            {word for word in target_words if len(word) >= 5},
            key=lambda word: (-len(word), word),
        )
        if not candidates:
            return target_words[:count]
        return candidates[:count]

    def _build_highlights(self, words: list[str]) -> list[dict[str, str]]:
        highlights: list[dict[str, str]] = []
        severities = ["medium", "high", "low"]
        for index, word in enumerate(words[:3]):
            expected_ipa, observed_issue, coach_tip = WORD_COACH_LIBRARY.get(
                word,
                (
                    "/custom/",
                    "这一拍的口型和尾音还不够稳定。",
                    "先放慢半拍，再把重音和尾辅音收干净。",
                ),
            )
            highlights.append(
                {
                    "word": word,
                    "expected_ipa": expected_ipa,
                    "observed_issue": observed_issue,
                    "coach_tip": coach_tip,
                    "severity": severities[index % len(severities)],
                }
            )
        return highlights

    def _build_copy(self, *, overall_score: int, lesson: Lesson) -> tuple[str, str]:
        if overall_score >= 90:
            return (
                "这地道的节奏感，已经有点主播腔了。",
                f"你这次的气口和层次都很稳，下一次把 {lesson.title} 再读得更松弛一点，会更高级。",
            )
        if overall_score >= 80:
            return (
                "今天的状态很在线，温柔里有力量。",
                "整体已经顺了，挑 1 到 2 个标红词单独复练，会明显更像母语者的呼吸感。",
            )
        return (
            "你的发音已经很有个人风格了，我们再把细节磨亮一点。",
            "这次先别追求满分，先把标红词慢读 3 遍，再回到整句，你会发现连读自然很多。",
        )

    def _build_poster_caption(self, *, overall_score: int, lesson: Lesson) -> str:
        if overall_score >= 88:
            return f"{lesson.poster_blurb} 今天的回音，像奶油色的晨光。"
        if overall_score >= 75:
            return f"{lesson.poster_blurb} 再练一遍，就很适合拿去发朋友圈。"
        return f"{lesson.poster_blurb} 先把勇气说出来，分数会慢慢跟上。"

    def _tokenize(self, raw_text: str) -> list[str]:
        return re.findall(r"[a-zA-Z']+", raw_text.lower())

    def _stable_float(self, seed: str) -> float:
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return int(digest[:8], 16) / 0xFFFFFFFF

    def _stable_delta(self, seed: str, minimum: int, maximum: int) -> int:
        span = maximum - minimum + 1
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return minimum + (int(digest[8:12], 16) % span)

    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))
