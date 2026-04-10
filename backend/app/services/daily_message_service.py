from __future__ import annotations

from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import IntegrationError
from app.db.models import DailyHomepageMessage, Lesson
from app.integrations.deepseek_daily_message_client import (
    DeepSeekDailyMessageClient,
    GeneratedDailyMessage,
)
from app.repositories.daily_message_repository import DailyMessageRepository


class DailyMessageService:
    def __init__(
        self,
        daily_message_repository: DailyMessageRepository,
        deepseek_client: DeepSeekDailyMessageClient,
    ) -> None:
        self.daily_message_repository = daily_message_repository
        self.deepseek_client = deepseek_client

    async def get_or_create_message(
        self,
        session: AsyncSession,
        *,
        current_day: date,
        lesson: Lesson,
    ) -> str:
        existing_message = await self.daily_message_repository.get_by_date(
            session,
            message_date=current_day,
        )
        if existing_message is not None:
            return existing_message.message_text

        generated_message = await self._generate_message(current_day=current_day, lesson=lesson)
        record = DailyHomepageMessage(
            message_date=current_day,
            message_text=generated_message.text,
            provider=generated_message.provider,
            model_name=generated_message.model,
        )
        await self.daily_message_repository.add(session, record)

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            existing_message = await self.daily_message_repository.get_by_date(
                session,
                message_date=current_day,
            )
            if existing_message is not None:
                return existing_message.message_text
            raise

        return record.message_text

    async def _generate_message(
        self,
        *,
        current_day: date,
        lesson: Lesson,
    ) -> GeneratedDailyMessage:
        try:
            return await self.deepseek_client.generate_message(
                current_day=current_day,
                lesson=lesson,
            )
        except IntegrationError:
            return GeneratedDailyMessage(
                text=self._build_fallback_message(current_day=current_day, lesson=lesson),
                provider="fallback",
                model="local-template",
            )

    def _build_fallback_message(self, *, current_day: date, lesson: Lesson) -> str:
        templates = (
            "今天先把这一句读顺，状态会慢慢安静下来。",
            "先把今天这句读稳，节奏感比着急更重要。",
            "从这一句开始热身，让嘴巴先进入状态。",
            "把今天这句练清楚，稳定感会一点点回来。",
            "今天先读好这一句，顺势把开口感觉找回来。",
        )
        lesson_offset = sum(ord(character) for character in lesson.id)
        template_index = (current_day.toordinal() + lesson_offset) % len(templates)
        return templates[template_index]
