from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lesson


@dataclass(frozen=True, slots=True)
class LessonSeed:
    id: str
    title: str
    subtitle: str
    pack_name: str
    english_text: str
    translation: str
    scenario: str
    mode_hint: str
    blind_box_prompt: str
    tags: tuple[str, ...]
    difficulty: str
    estimated_seconds: int
    poster_blurb: str
    theme_tone: str
    published_on: date

    def to_model(self) -> Lesson:
        return Lesson(
            id=self.id,
            title=self.title,
            subtitle=self.subtitle,
            pack_name=self.pack_name,
            english_text=self.english_text,
            translation=self.translation,
            scenario=self.scenario,
            mode_hint=self.mode_hint,
            blind_box_prompt=self.blind_box_prompt,
            tags=list(self.tags),
            difficulty=self.difficulty,
            estimated_seconds=self.estimated_seconds,
            poster_blurb=self.poster_blurb,
            theme_tone=self.theme_tone,
            published_on=self.published_on,
        )


LESSON_SEEDS: tuple[LessonSeed, ...] = (
    LessonSeed(
        id="lesson-bbc-morning",
        title="Morning Briefing",
        subtitle="\u6668\u8bfb\u77ed\u53e5 \u00b7 \u7ec3\u6e05\u6670\u53d1\u97f3",
        pack_name="\u6668\u95f4\u77ed\u53e5",
        english_text="Today is a quiet beginning, but brave choices still change everything.",
        translation=(
            "\u4eca\u5929\u770b\u4f3c\u5e73\u9759\u5f00\u573a\uff0c"
            "\u4f46\u52c7\u6562\u7684\u9009\u62e9\u4f9d\u7136\u4f1a\u6539\u53d8\u4e00\u5207\u3002"
        ),
        scenario="\u901a\u52e4\u8def\u4e0a\u7684 30 \u79d2\u6668\u8bfb\u63d0\u9192",
        mode_hint=(
            "\u5148\u628a but brave \u8fde\u8d77\u6765\uff0c"
            "\u5c3e\u97f3\u4fdd\u6301\u8f7b\u5de7\u3002"
        ),
        blind_box_prompt=(
            "\u4f60\u5728\u9f13\u52b1\u4e00\u4f4d\u51c6\u5907\u9762\u8bd5\u7684\u670b\u53cb\uff1a"
            "\u5f00\u5c40\u5e73\u9759\uff0c\u4e5f\u80fd\u8d70\u5411\u8f6c\u6298\u3002"
        ),
        tags=(
            "\u6668\u8bfb",
            "\u6e05\u6670\u5ea6",
            "\u77ed\u53e5\u8ddf\u8bfb",
        ),
        difficulty="Beginner",
        estimated_seconds=18,
        poster_blurb="\u8f7b\u58f0\u4e00\u70b9\uff0c\u4e5f\u53ef\u4ee5\u5f88\u6709\u529b\u91cf\u3002",
        theme_tone="cream-sky",
        published_on=date(2026, 4, 7),
    ),
    LessonSeed(
        id="lesson-movie-whisper",
        title="Cinema Whisper",
        subtitle="\u7535\u5f71\u8bed\u611f \u00b7 \u7ec3\u60c5\u7eea\u548c\u91cd\u97f3",
        pack_name="\u7ecf\u5178\u7535\u5f71\u53f0\u8bcd",
        english_text="Speak softly to your fear, and it will finally make room for your courage.",
        translation=(
            "\u6e29\u67d4\u5730\u5bf9\u4f60\u7684\u6050\u60e7\u8bf4\u8bdd\uff0c"
            "\u5b83\u7ec8\u4f1a\u4e3a\u4f60\u7684\u52c7\u6c14\u8ba9\u8def\u3002"
        ),
        scenario=(
            "\u7761\u524d 20 \u79d2\uff0c"
            "\u7ec3\u4e00\u6761\u6709\u753b\u9762\u611f\u7684\u544a\u767d\u53e5\u3002"
        ),
        mode_hint=(
            "softly \u548c finally \u8981\u62c9\u5f00\u5c42\u6b21\uff0c"
            "fear \u7684 /f/ \u6e05\u695a\u4e00\u70b9\u3002"
        ),
        blind_box_prompt=(
            "\u4f60\u60f3\u8868\u8fbe\uff1a"
            "\u522b\u8ddf\u6050\u60e7\u786c\u78b0\u786c\uff0c\u6e29\u67d4\u4e5f\u80fd\u8d62\u3002"
        ),
        tags=(
            "\u7535\u5f71\u53f0\u8bcd",
            "\u91cd\u97f3",
            "\u8bed\u6c14",
        ),
        difficulty="Intermediate",
        estimated_seconds=22,
        poster_blurb="\u4eca\u591c\u7684\u56de\u97f3\uff0c\u50cf\u4e00\u76cf\u5c0f\u591c\u706f\u3002",
        theme_tone="peach-rose",
        published_on=date(2026, 4, 8),
    ),
    LessonSeed(
        id="lesson-office-kind",
        title="Clear Is Kind",
        subtitle="\u4f1a\u8bae\u8868\u8fbe \u00b7 \u7ec3\u51c6\u786e\u548c\u8282\u594f",
        pack_name="\u5546\u52a1\u82f1\u8bed",
        english_text="Clear is kind, and concise words travel further in every meeting.",
        translation=(
            "\u8868\u8fbe\u6e05\u6670\u662f\u4e00\u79cd\u5584\u610f\uff0c"
            "\u7b80\u6d01\u7684\u8bdd\u8bed\u4f1a\u5728\u6bcf\u573a\u4f1a\u8bae\u91cc\u4f20\u5f97\u66f4\u8fdc\u3002"
        ),
        scenario=(
            "\u4f1a\u524d\u70ed\u8eab\uff0c"
            "\u7528\u4e00\u53e5\u9ad8\u7ea7\u5546\u52a1\u82f1\u8bed\u6253\u5f00\u72b6\u6001\u3002"
        ),
        mode_hint=(
            "concise \u7684\u91cd\u97f3\u843d\u5728\u7b2c\u4e8c\u62cd\uff0c"
            "meeting \u6536\u5c3e\u522b\u541e\u97f3\u3002"
        ),
        blind_box_prompt=(
            "\u4f60\u5728\u63d0\u9192\u56e2\u961f\uff1a"
            "\u9ad8\u6548\u6c9f\u901a\u4e0d\u662f\u51b7\u6de1\uff0c\u800c\u662f\u4f53\u8d34\u3002"
        ),
        tags=(
            "\u5546\u52a1\u82f1\u8bed",
            "\u4f1a\u8bae\u8868\u8fbe",
            "\u53d1\u97f3\u8282\u594f",
        ),
        difficulty="Intermediate",
        estimated_seconds=20,
        poster_blurb="\u6e05\u6670\uff0c\u662f\u4eca\u5929\u6700\u6e29\u67d4\u7684\u6548\u7387\u3002",
        theme_tone="mint-latte",
        published_on=date(2026, 4, 9),
    ),
)


async def seed_database(session: AsyncSession) -> None:
    seed_ids = [seed.id for seed in LESSON_SEEDS]
    existing_ids = set(
        (await session.scalars(select(Lesson.id).where(Lesson.id.in_(seed_ids)))).all()
    )
    missing_lessons = [seed.to_model() for seed in LESSON_SEEDS if seed.id not in existing_ids]
    if not missing_lessons:
        return

    session.add_all(missing_lessons)
    await session.commit()
