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
        candidates = await daily_message_client.generate_lesson_candidates(
            current_day=current_day,
            seed_lesson=seed_lesson,
            count=len(missing_ids),
        )
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
    patterns = (
        ("说慢一点，意思会更清楚。", "Speak a little slower, and your meaning becomes clearer."),
        ("先把重音放对，再提语速。", "Place your stress first, then raise your speed."),
        ("一句读顺了，情绪就稳了。", "When one sentence flows, your mood settles."),
        ("温柔地说，也能很有力量。", "A gentle voice can still carry great strength."),
    )
    lessons: list[Lesson] = []
    for index, lesson_id in enumerate(generated_ids):
        zh, en = patterns[index % len(patterns)]
        lessons.append(
            Lesson(
                id=lesson_id,
                title=f"AI Daily Line {index + 1}",
                subtitle="AI 句库 · 当日生成",
                pack_name="AI 每日精选",
                english_text=en,
                translation=zh,
                scenario=seed_lesson.scenario,
                mode_hint=seed_lesson.mode_hint,
                blind_box_prompt=seed_lesson.blind_box_prompt,
                tags=["AI句库", "每日更新"],
                difficulty=seed_lesson.difficulty,
                estimated_seconds=seed_lesson.estimated_seconds,
                audio_url=None,
                poster_blurb=seed_lesson.poster_blurb,
                theme_tone=seed_lesson.theme_tone,
                published_on=current_day,
            )
        )
    return lessons
