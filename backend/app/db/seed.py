from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lesson

LESSON_SEEDS = [
    Lesson(
        id="lesson-bbc-morning",
        title="Morning Briefing",
        subtitle="晨读短句 · 练清晰发音",
        pack_name="晨间短句",
        english_text="Today is a quiet beginning, but brave choices still change everything.",
        translation="今天看似平静开场，但勇敢的选择依然会改变一切。",
        scenario="通勤路上的 30 秒晨读提醒",
        mode_hint="先把 but brave 连起来，尾音保持轻巧。",
        blind_box_prompt="你在鼓励一位准备面试的朋友：开局平静，也能走向转折。",
        tags=["晨读", "清晰度", "短句跟读"],
        difficulty="Beginner",
        estimated_seconds=18,
        poster_blurb="轻声一点，也可以很有力量。",
        theme_tone="cream-sky",
        published_on=date(2026, 4, 7),
    ),
    Lesson(
        id="lesson-movie-whisper",
        title="Cinema Whisper",
        subtitle="电影语感 · 练情绪和重音",
        pack_name="经典电影台词",
        english_text="Speak softly to your fear, and it will finally make room for your courage.",
        translation="温柔地对你的恐惧说话，它终会为你的勇气让路。",
        scenario="睡前 20 秒，练一条有画面感的告白句。",
        mode_hint="softly 和 finally 要拉开层次，fear 的 /f/ 清楚一点。",
        blind_box_prompt="你想表达：别跟恐惧硬碰硬，温柔也能赢。",
        tags=["电影台词", "重音", "语气"],
        difficulty="Intermediate",
        estimated_seconds=22,
        poster_blurb="今晚的回音，像一盏小夜灯。",
        theme_tone="peach-rose",
        published_on=date(2026, 4, 8),
    ),
    Lesson(
        id="lesson-office-kind",
        title="Clear Is Kind",
        subtitle="会议表达 · 练准确和节奏",
        pack_name="商务英语",
        english_text="Clear is kind, and concise words travel further in every meeting.",
        translation="表达清晰是一种善意，简洁的话语会在每场会议里传得更远。",
        scenario="会前热身，用一句高级商务英语打开状态。",
        mode_hint="concise 的重音落在第二拍，meeting 收尾别吞音。",
        blind_box_prompt="你在提醒团队：高效沟通不是冷淡，而是体贴。",
        tags=["商务英语", "会议表达", "发音节奏"],
        difficulty="Intermediate",
        estimated_seconds=20,
        poster_blurb="清晰，是今天最温柔的效率。",
        theme_tone="mint-latte",
        published_on=date(2026, 4, 9),
    ),
]


async def seed_database(session: AsyncSession) -> None:
    lesson_count = await session.scalar(select(func.count()).select_from(Lesson))
    if lesson_count:
        return

    session.add_all(LESSON_SEEDS)
    await session.commit()
