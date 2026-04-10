from datetime import date

from fastapi import APIRouter

from app.api.dependencies import DbSession, daily_message_client, lesson_repository
from app.core.errors import NotFoundError
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
    if not lessons:
        return []
    if len(lessons) >= MAX_RECENT_LESSONS:
        return [LessonResponseSchema.model_validate(lesson) for lesson in lessons[:MAX_RECENT_LESSONS]]

    ai_seed = await _build_ai_seed_text(session=session, current_day=current_day)
    expanded: list[LessonResponseSchema] = []
    for index in range(MAX_RECENT_LESSONS):
        base_lesson = lessons[index % len(lessons)]
        expanded.append(
            LessonResponseSchema(
                id=base_lesson.id,
                title=base_lesson.title,
                subtitle=base_lesson.subtitle,
                pack_name=base_lesson.pack_name,
                english_text=base_lesson.english_text,
                translation=base_lesson.translation,
                scenario=base_lesson.scenario,
                mode_hint=_build_rotated_hint(
                    original_hint=base_lesson.mode_hint,
                    ai_seed=ai_seed,
                    index=index,
                ),
                tags=base_lesson.tags,
                difficulty=base_lesson.difficulty,
                estimated_seconds=base_lesson.estimated_seconds,
                audio_url=base_lesson.audio_url,
                theme_tone=base_lesson.theme_tone,
            )
        )
    return expanded


@router.get("/{lesson_id}", response_model=LessonResponseSchema)
async def get_lesson(lesson_id: str, session: DbSession) -> LessonResponseSchema:
    lesson = await lesson_repository.get_by_id(session, lesson_id)
    if lesson is None:
        raise NotFoundError("Lesson not found.", code="lesson_not_found")
    return LessonResponseSchema.model_validate(lesson)


async def _build_ai_seed_text(*, session: DbSession, current_day: date) -> str:
    lesson = await lesson_repository.get_today(
        session=session,
        current_day=current_day,
    )
    if lesson is None:
        return "今天先慢半拍，清晰比速度更重要。"
    try:
        generated = await daily_message_client.generate_message(
            current_day=current_day,
            lesson=lesson,
        )
        return generated.text
    except Exception:
        return "今天先慢半拍，清晰比速度更重要。"


def _build_rotated_hint(*, original_hint: str, ai_seed: str, index: int) -> str:
    stage = (index % 5) + 1
    suffixes = (
        "先拆开关键词再连读整句。",
        "重音先拉开，尾音要收稳。",
        "这遍重点放在停连和节奏。",
        "主元音拉满，辅音收干净。",
        "嘴型到位后再提一点语速。",
    )
    return f"{original_hint} 第{stage}轮：{suffixes[index % len(suffixes)]} {ai_seed}"
