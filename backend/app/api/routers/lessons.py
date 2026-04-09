from datetime import date

from fastapi import APIRouter

from app.api.dependencies import DbSession, lesson_repository
from app.core.errors import NotFoundError
from app.schemas.lesson import LessonResponseSchema

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/today", response_model=LessonResponseSchema)
async def get_today_lesson(session: DbSession) -> LessonResponseSchema:
    lesson = await lesson_repository.get_today(session, current_day=date.today())
    if lesson is None:
        raise NotFoundError("No lesson available yet.", code="lesson_not_found")
    return LessonResponseSchema.model_validate(lesson)


@router.get("/{lesson_id}", response_model=LessonResponseSchema)
async def get_lesson(lesson_id: str, session: DbSession) -> LessonResponseSchema:
    lesson = await lesson_repository.get_by_id(session, lesson_id)
    if lesson is None:
        raise NotFoundError("Lesson not found.", code="lesson_not_found")
    return LessonResponseSchema.model_validate(lesson)
