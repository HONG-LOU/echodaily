from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import IntegrationError
from app.db.models import Lesson


@dataclass(frozen=True, slots=True)
class GeneratedDailyMessage:
    text: str
    provider: str
    model: str


class DeepSeekDailyMessageClient:
    async def generate_message(
        self,
        *,
        current_day: date,
        lesson: Lesson,
    ) -> GeneratedDailyMessage:
        settings = get_settings()
        if settings.deepseek_api_key is None:
            raise IntegrationError(
                "DeepSeek API key is not configured.",
                code="daily_message_provider_not_configured",
            )

        payload = await self._request_completion(current_day=current_day, lesson=lesson)
        text = self._extract_message_text(payload)
        normalized_text = self._normalize_message_text(text)
        return GeneratedDailyMessage(
            text=normalized_text,
            provider="deepseek",
            model=settings.deepseek_model,
        )

    async def _request_completion(
        self,
        *,
        current_day: date,
        lesson: Lesson,
    ) -> dict[str, Any]:
        settings = get_settings()
        request_payload = {
            "model": settings.deepseek_model,
            "temperature": 1.05,
            "max_tokens": 80,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是 EchoDaily 首页文案编辑。"
                        "请只输出 1 句中文短文案，不要解释，不要换行。"
                        "文案要温柔、具体、有陪伴感，避免鸡血口号。"
                        "不要出现 AI、模型、系统、打卡、坚持、英语、口语 这些词。"
                        "不要使用引号、书名号、emoji。"
                        "长度控制在 14 到 28 个汉字左右。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"创作日期种子：{current_day.isoformat()}，不要直接写出日期。\n"
                        f"今日练习标题：{lesson.title}\n"
                        f"今日练习副标题：{lesson.subtitle}\n"
                        f"英文原句：{lesson.english_text}\n"
                        f"中文释义：{lesson.translation}\n"
                        f"练习场景：{lesson.scenario}\n"
                        f"跟读提示：{lesson.mode_hint}\n"
                        f"标签：{', '.join(lesson.tags)}\n"
                        "请写一句适合首页顶部展示的中文文案，"
                        "和今天练习有轻微呼应，但不要直接复述原句。"
                    ),
                },
            ],
        }

        try:
            async with httpx.AsyncClient(
                timeout=settings.deepseek_request_timeout_seconds
            ) as client:
                response = await client.post(
                    f"{settings.deepseek_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.deepseek_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise IntegrationError(
                "DeepSeek request failed while generating the homepage message.",
                code="daily_message_generation_failed",
            ) from error
        except httpx.HTTPError as error:
            raise IntegrationError(
                "DeepSeek is unavailable while generating the homepage message.",
                code="daily_message_generation_failed",
            ) from error

        payload = response.json()
        if not isinstance(payload, dict):
            raise IntegrationError(
                "DeepSeek returned an invalid response payload.",
                code="daily_message_generation_failed",
            )
        return payload

    def _extract_message_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise IntegrationError(
                "DeepSeek returned no completion choices.",
                code="daily_message_generation_failed",
            )

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise IntegrationError(
                "DeepSeek returned an invalid completion choice.",
                code="daily_message_generation_failed",
            )

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise IntegrationError(
                "DeepSeek returned an invalid completion message.",
                code="daily_message_generation_failed",
            )

        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    part = item.get("text")
                    if isinstance(part, str) and part.strip():
                        text_parts.append(part.strip())
            if text_parts:
                return "".join(text_parts)

        raise IntegrationError(
            "DeepSeek returned an empty completion message.",
            code="daily_message_generation_failed",
        )

    def _normalize_message_text(self, text: str) -> str:
        normalized = " ".join(text.split()).strip().strip("\"'“”‘’")
        if not normalized:
            raise IntegrationError(
                "DeepSeek returned an empty homepage message.",
                code="daily_message_generation_failed",
            )
        if len(normalized) < 8 or len(normalized) > 40:
            raise IntegrationError(
                "DeepSeek returned a homepage message outside the expected length.",
                code="daily_message_generation_failed",
            )
        return normalized
