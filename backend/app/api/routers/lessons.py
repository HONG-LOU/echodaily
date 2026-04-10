from datetime import date

from fastapi import APIRouter

from app.api.dependencies import DbSession, daily_message_client, lesson_repository
from app.core.errors import NotFoundError
from app.db.models import Lesson
from app.integrations.deepseek_daily_message_client import GeneratedLessonCandidate
from app.schemas.lesson import LessonResponseSchema

router = APIRouter(prefix="/lessons", tags=["lessons"])
MAX_RECENT_LESSONS = 50


@router.get("/today", response_model=LessonResponseSchema)
async def get_today_lesson(session: DbSession) -> LessonResponseSchema:
    lesson = await lesson_repository.get_today(session, current_day=date.today())
    if lesson is None:
        raise NotFoundError("No lesson available yet.", code="lesson_not_found")
    return LessonResponseSchema.model_validate(lesson)


@router.get("/recent", response_model=list[LessonResponseSchema])
async def get_recent_lessons(session: DbSession) -> list[LessonResponseSchema]:
    current_day = date.today()
    lessons = await lesson_repository.list_recent(
        session,
        current_day=current_day,
        limit=MAX_RECENT_LESSONS,
    )
    if len(lessons) < MAX_RECENT_LESSONS:
        generated_lessons = await _generate_and_store_lessons(
            session=session,
            current_day=current_day,
            existing_lessons=lessons,
            target_count=MAX_RECENT_LESSONS,
        )
        if generated_lessons:
            await lesson_repository.add_many(session, generated_lessons)
            await session.commit()
            lessons = await lesson_repository.list_recent(
                session,
                current_day=current_day,
                limit=MAX_RECENT_LESSONS,
            )
    return [LessonResponseSchema.model_validate(lesson) for lesson in lessons[:MAX_RECENT_LESSONS]]


@router.get("/{lesson_id}", response_model=LessonResponseSchema)
async def get_lesson(lesson_id: str, session: DbSession) -> LessonResponseSchema:
    lesson = await lesson_repository.get_by_id(session, lesson_id)
    if lesson is None:
        raise NotFoundError("Lesson not found.", code="lesson_not_found")
    return LessonResponseSchema.model_validate(lesson)


async def _generate_and_store_lessons(
    *,
    session: DbSession,
    current_day: date,
    existing_lessons: list[Lesson],
    target_count: int,
) -> list[Lesson]:
    missing_count = max(0, target_count - len(existing_lessons))
    if missing_count == 0:
        return []
    seed_lesson = await lesson_repository.get_today(session, current_day=current_day)
    if seed_lesson is None and existing_lessons:
        seed_lesson = existing_lessons[0]
    if seed_lesson is None:
        return []

    # Keep ids stable for a day and avoid duplicate inserts.
    generated_ids = [
        f"lesson-ai-{current_day.strftime('%Y%m%d')}-{idx:03d}"
        for idx in range(missing_count)
    ]
    existing_ids = {lesson.id for lesson in existing_lessons}
    missing_ids = [lesson_id for lesson_id in generated_ids if lesson_id not in existing_ids]
    if not missing_ids:
        return []

    try:
        candidates = []
        batch_size = 10
        for i in range(0, len(missing_ids), batch_size):
            batch_count = min(batch_size, len(missing_ids) - i)
            batch_candidates = await daily_message_client.generate_lesson_candidates(
                current_day=current_day,
                seed_lesson=seed_lesson,
                count=batch_count,
                offset=i,
            )
            candidates.extend(batch_candidates)
        
        return _build_generated_models(
            current_day=current_day,
            generated_ids=missing_ids,
            candidates=candidates,
        )
    except Exception:
        return _build_fallback_models(
            seed_lesson=seed_lesson,
            current_day=current_day,
            generated_ids=missing_ids,
        )


def _build_generated_models(
    *,
    current_day: date,
    generated_ids: list[str],
    candidates: list[GeneratedLessonCandidate],
) -> list[Lesson]:
    lessons: list[Lesson] = []
    for index, candidate in enumerate(candidates):
        if index >= len(generated_ids):
            break
        lessons.append(
            Lesson(
                id=generated_ids[index],
                title=candidate.title,
                subtitle=candidate.subtitle,
                pack_name=candidate.pack_name,
                english_text=candidate.english_text,
                translation=candidate.translation,
                scenario=candidate.scenario,
                mode_hint=candidate.mode_hint,
                blind_box_prompt=candidate.blind_box_prompt,
                tags=candidate.tags,
                difficulty=candidate.difficulty,
                estimated_seconds=candidate.estimated_seconds,
                audio_url=None,
                poster_blurb=candidate.poster_blurb,
                theme_tone=candidate.theme_tone,
                published_on=current_day,
            )
        )
    return lessons


def _build_fallback_models(
    *,
    seed_lesson: Lesson,
    current_day: date,
    generated_ids: list[str],
) -> list[Lesson]:
    patterns = [
        ("说慢一点，意思会更清楚。", "Speak a little slower, and your meaning becomes clearer.", "先放慢语速，确保每个词发音清晰。"),
        ("先把重音放对，再提语速。", "Place your stress first, then raise your speed.", "注意句子中的重音，不要急于求成。"),
        ("一句读顺了，情绪就稳了。", "When one sentence flows, your mood settles.", "保持平稳的情绪，流畅地读完这一句。"),
        ("温柔地说，也能很有力量。", "A gentle voice can still carry great strength.", "尝试用温柔但坚定的语气朗读。"),
        ("每天进步一点点。", "A little progress every day.", "每天坚持练习，积累下来就是巨大的进步。"),
        ("相信自己的声音。", "Believe in your own voice.", "自信地读出来，你的声音很有感染力。"),
        ("发音清晰是沟通的关键。", "Clear pronunciation is the key to communication.", "注意每个单词的发音，确保清晰可辨。"),
        ("多听多练，自然会好。", "Listen more, practice more, and it will naturally improve.", "多听原声，模仿其语调和节奏。"),
        ("不要害怕犯错。", "Do not be afraid of making mistakes.", "大胆开口，错误是学习过程中的一部分。"),
        ("语感是在练习中培养的。", "Language sense is cultivated through practice.", "多读多练，自然会形成良好的语感。"),
        ("坚持就是胜利。", "Persistence is victory.", "坚持每天练习，你一定会看到成效。"),
        ("把英语融入生活。", "Integrate English into your life.", "尝试在日常生活中多使用英语。"),
        ("享受学习的过程。", "Enjoy the learning process.", "把学习当作一种乐趣，而不是负担。"),
        ("每一次开口都是一次进步。", "Every time you speak is a step forward.", "珍惜每一次练习的机会，不断进步。"),
        ("用英语表达你的思想。", "Express your thoughts in English.", "尝试用英语思考和表达，提高表达能力。"),
        ("模仿是最好的老师。", "Imitation is the best teacher.", "多模仿原声，学习纯正的发音。"),
        ("保持好奇心，不断探索。", "Keep curious and keep exploring.", "对英语保持好奇心，不断学习新知识。"),
        ("自信地面对挑战。", "Face challenges with confidence.", "勇敢地面对学习中的困难，不要退缩。"),
        ("好的开始是成功的一半。", "A good beginning is half the battle.", "从现在开始，认真对待每一次练习。"),
        ("让英语成为你的朋友。", "Let English be your friend.", "把英语当作朋友，多和它交流。"),
        ("用心去感受语言的魅力。", "Feel the charm of language with your heart.", "用心体会英语的韵律和美感。"),
        ("每一次练习都是一种积累。", "Every practice is an accumulation.", "不断积累，你的英语水平会越来越高。"),
        ("不要轻易放弃。", "Do not give up easily.", "遇到困难时，坚持下去就是胜利。"),
        ("相信自己，你能行。", "Believe in yourself, you can do it.", "对自己充满信心，你一定能学好英语。"),
        ("学习语言需要耐心。", "Learning a language requires patience.", "保持耐心，一步一个脚印地学习。"),
        ("多与他人交流，提高口语。", "Communicate more with others to improve spoken English.", "多找机会用英语与他人交流。"),
        ("从错误中学习。", "Learn from mistakes.", "不要害怕犯错，从错误中吸取教训。"),
        ("保持积极的学习态度。", "Maintain a positive learning attitude.", "以积极的心态面对学习中的挑战。"),
        ("制定合理的学习计划。", "Make a reasonable learning plan.", "制定适合自己的学习计划，并坚持执行。"),
        ("多阅读英文原版书籍。", "Read more original English books.", "通过阅读提高词汇量和语感。"),
        ("看英文电影，学习地道表达。", "Watch English movies to learn authentic expressions.", "在娱乐中学习地道的英语表达。"),
        ("听英文歌曲，培养语感。", "Listen to English songs to cultivate language sense.", "通过听歌提高对英语语音的敏感度。"),
        ("记录学习心得，总结经验。", "Record learning experiences and summarize lessons.", "及时总结学习经验，不断改进学习方法。"),
        ("寻找志同道合的学习伙伴。", "Find like-minded learning partners.", "和伙伴一起学习，互相鼓励和支持。"),
        ("参加英语角，锻炼口语能力。", "Participate in English corners to exercise oral skills.", "在英语角中多开口，提高口语表达能力。"),
        ("利用碎片时间学习英语。", "Use fragmented time to learn English.", "充分利用零碎时间，提高学习效率。"),
        ("保持对英语的热爱。", "Keep your love for English.", "热爱是最好的老师，保持对英语的热情。"),
        ("不断挑战自己，突破极限。", "Constantly challenge yourself and break limits.", "勇于接受挑战，不断提高自己的英语水平。"),
        ("相信付出总会有回报。", "Believe that efforts will always pay off.", "只要付出努力，就一定会有收获。"),
        ("让英语为你打开新世界的大门。", "Let English open the door to a new world for you.", "掌握英语，探索更广阔的世界。"),
        ("学习英语是一场马拉松。", "Learning English is a marathon.", "保持持久的动力，坚持到底。"),
        ("不要和别人比较，只和自己比。", "Do not compare with others, only with yourself.", "关注自己的进步，不要盲目攀比。"),
        ("把英语当作一种工具，而不是目的。", "Treat English as a tool, not a goal.", "掌握英语，用它来实现你的目标。"),
        ("在实践中学习，在学习中实践。", "Learn in practice, practice in learning.", "将学到的知识应用到实际中去。"),
        ("保持谦虚的学习态度。", "Maintain a humble learning attitude.", "虚心向他人学习，不断丰富自己的知识。"),
        ("多关注英语国家的文化。", "Pay more attention to the culture of English-speaking countries.", "了解文化背景，更好地理解和使用英语。"),
        ("培养用英语思考的习惯。", "Cultivate the habit of thinking in English.", "尝试用英语进行思考，提高语言反应速度。"),
        ("不要让语法成为你开口的障碍。", "Do not let grammar become an obstacle to your speaking.", "大胆开口，不要过分纠结于语法错误。"),
        ("学习英语需要持之以恒。", "Learning English requires perseverance.", "坚持不懈，你一定能取得成功。"),
        ("让英语成为你生活的一部分。", "Let English become a part of your life.", "把英语融入日常生活的方方面面。")
    ]
    lessons: list[Lesson] = []
    for index, lesson_id in enumerate(generated_ids):
        zh, en, hint = patterns[index % len(patterns)]
        lessons.append(
            Lesson(
                id=lesson_id,
                title=f"Daily English {index + 1}",
                subtitle="每日精读 · 当日生成",
                pack_name="每日精选",
                english_text=en,
                translation=zh,
                scenario=seed_lesson.scenario,
                mode_hint=hint,
                blind_box_prompt=seed_lesson.blind_box_prompt,
                tags=["每日更新", "精选语料"],
                difficulty=seed_lesson.difficulty,
                estimated_seconds=seed_lesson.estimated_seconds,
                audio_url=None,
                poster_blurb=seed_lesson.poster_blurb,
                theme_tone=seed_lesson.theme_tone,
                published_on=current_day,
            )
        )
    return lessons
