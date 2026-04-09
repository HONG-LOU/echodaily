from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Challenge, Lesson

LESSON_SEEDS = [
    Lesson(
        id="lesson-bbc-morning",
        title="Morning Briefing",
        subtitle="BBC 风短句 · 轻柔开口",
        pack_name="晨间短句",
        english_text="Today is a quiet beginning, but brave choices still change everything.",
        translation="今天看似安静开场，但勇敢的选择依然会改变一切。",
        scenario="通勤路上的 30 秒晨读提醒",
        mode_hint="先把 but brave 连起来，尾音保持轻巧。",
        blind_box_prompt="你在鼓励一位准备面试的朋友：开局平静，也能走向转折。",
        tags=["BBC 短句", "晨间打卡", "治愈感"],
        difficulty="Beginner",
        estimated_seconds=18,
        poster_blurb="轻声一点，也可以很有力量。",
        theme_tone="cream-sky",
        published_on=date(2026, 4, 7),
    ),
    Lesson(
        id="lesson-movie-whisper",
        title="Cinema Whisper",
        subtitle="电影台词 · 温柔但坚定",
        pack_name="经典电影台词",
        english_text="Speak softly to your fear, and it will finally make room for your courage.",
        translation="温柔地对你的恐惧说话，它终会为你的勇气让路。",
        scenario="睡前 20 秒，练一条有画面感的告白句。",
        mode_hint="softly 和 finally 要拉开层次，fear 的 /f/ 清楚一点。",
        blind_box_prompt="你想表达：别跟恐惧硬碰硬，温柔也能赢。",
        tags=["电影台词", "情绪价值", "暖暖的"],
        difficulty="Intermediate",
        estimated_seconds=22,
        poster_blurb="今晚的回音，像一盏小夜灯。",
        theme_tone="peach-rose",
        published_on=date(2026, 4, 8),
    ),
    Lesson(
        id="lesson-office-kind",
        title="Clear Is Kind",
        subtitle="外企沟通 · 高级又简洁",
        pack_name="外企黑话",
        english_text="Clear is kind, and concise words travel further in every meeting.",
        translation="表达清晰是一种善意，简洁的话语会在每场会议里传得更远。",
        scenario="会前热身，用一句高级商务英语打开状态。",
        mode_hint="concise 的重音落在第二拍，meeting 收尾别吞音。",
        blind_box_prompt="你在提醒团队：高效沟通不是冷淡，而是体贴。",
        tags=["外企表达", "Apple 感", "短句高频"],
        difficulty="Intermediate",
        estimated_seconds=20,
        poster_blurb="清晰，是今天最温柔的效率。",
        theme_tone="mint-latte",
        published_on=date(2026, 4, 9),
    ),
]


CHALLENGE_SEEDS = [
    Challenge(
        id="challenge-21-sunrise",
        title="21 天晨读现金池",
        description="每天 1 条短句，分数达到 80 即记为打卡成功。",
        deposit_amount=21,
        participants=132,
        days_total=21,
        days_left=14,
        score_threshold=80,
        reward_pool=2310,
        teaser="坚持到最后的人，拿回本金再平分失约者的奖励池。",
        is_active=True,
    ),
    Challenge(
        id="challenge-classroom-circle",
        title="班级共学圈 MVP",
        description="给英语博主和工作室的私域班级打卡工具原型。",
        deposit_amount=0,
        participants=48,
        days_total=7,
        days_left=3,
        score_threshold=75,
        reward_pool=0,
        teaser="适合对接 B2B2C 老师渠道，支持专属标签和返佣入口。",
        is_active=True,
    ),
]


async def seed_database(session: AsyncSession) -> None:
    lesson_count = await session.scalar(select(func.count()).select_from(Lesson))
    if lesson_count:
        return

    session.add_all(LESSON_SEEDS)
    session.add_all(CHALLENGE_SEEDS)
    await session.commit()
