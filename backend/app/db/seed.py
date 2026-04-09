from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Challenge, Lesson, Submission, UserProfile

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


USER_SEEDS = [
    UserProfile(
        id="demo-user",
        nickname="Mia",
        avatar_symbol="M",
        streak_days=6,
        total_practices=18,
        weekly_minutes=46,
        pro_active=False,
        plan_name="Free Starter",
        weak_sound="/θ/",
        target_pack="经典电影台词",
        focus_tag="暖调跟读",
        city="Shanghai",
        bio="每天 30 秒，把英语练得更柔和一点。",
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


SUBMISSION_SEEDS = [
    Submission(
        id="seed-submission-1",
        user_id="demo-user",
        lesson_id="lesson-bbc-morning",
        mode="follow",
        duration_seconds=19,
        transcript="Today is a quiet beginning, but brave choices still change everything.",
        transcript_used=True,
        comparison_ratio=0.94,
        overall_score=88,
        pronunciation_score=86,
        fluency_score=90,
        intonation_score=87,
        stress_score=84,
        completeness_score=92,
        mistake_count=2,
        highlight_words=[
            {
                "word": "quiet",
                "expected_ipa": "/ˈkwaɪət/",
                "observed_issue": "中间的双元音收得太快。",
                "coach_tip": "把 /kwaɪ/ 拉开，再轻轻落到 /ət/。",
                "severity": "medium",
            },
            {
                "word": "choices",
                "expected_ipa": "/ˈtʃɔɪsɪz/",
                "observed_issue": "尾音 /ɪz/ 略弱。",
                "coach_tip": "结尾再带一点气流，别直接收死。",
                "severity": "low",
            },
        ],
        headline="今天的节奏很稳，已经有晨间播报感了。",
        encouragement="你的跟读很顺，下一次把 quiet 的开口再放松一点，会更自然。",
        poster_caption="今天也把英语说得很温柔。",
        poster_theme="cream-sky",
        created_at=datetime(2026, 4, 6, 8, 10, 0),
    ),
    Submission(
        id="seed-submission-2",
        user_id="demo-user",
        lesson_id="lesson-movie-whisper",
        mode="blind_box",
        duration_seconds=23,
        transcript=None,
        transcript_used=False,
        comparison_ratio=0.79,
        overall_score=81,
        pronunciation_score=80,
        fluency_score=83,
        intonation_score=82,
        stress_score=78,
        completeness_score=80,
        mistake_count=1,
        highlight_words=[
            {
                "word": "softly",
                "expected_ipa": "/ˈsɒftli/",
                "observed_issue": "soft 的 /f/ 不够清晰。",
                "coach_tip": "上齿轻碰下唇，把气流送出去。",
                "severity": "medium",
            },
        ],
        headline="这句已经很有电影感了，情绪铺得很好。",
        encouragement="盲盒模式下还能稳住语调很不错，下一次把 courage 的重音再抬高一点。",
        poster_caption="温柔不是退让，是更高级的勇气。",
        poster_theme="peach-rose",
        created_at=datetime(2026, 4, 8, 22, 0, 0),
    ),
]


async def seed_database(session: AsyncSession) -> None:
    lesson_count = await session.scalar(select(func.count()).select_from(Lesson))
    if lesson_count:
        return

    session.add_all(LESSON_SEEDS)
    session.add_all(USER_SEEDS)
    session.add_all(CHALLENGE_SEEDS)
    session.add_all(SUBMISSION_SEEDS)
    await session.commit()
