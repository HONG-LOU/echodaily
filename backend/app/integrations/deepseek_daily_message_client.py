from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
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


@dataclass(frozen=True, slots=True)
class GeneratedLessonCandidate:
    title: str
    subtitle: str
    pack_name: str
    english_text: str
    translation: str
    scenario: str
    mode_hint: str
    blind_box_prompt: str
    tags: list[str]
    difficulty: str
    estimated_seconds: int
    poster_blurb: str
    theme_tone: str


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

    async def generate_lesson_candidates(
        self,
        *,
        current_day: date,
        seed_lesson: Lesson,
        count: int,
        offset: int = 0,
    ) -> list[GeneratedLessonCandidate]:
        settings = get_settings()
        if settings.deepseek_api_key is None:
            raise IntegrationError(
                "DeepSeek API key is not configured.",
                code="lesson_generation_provider_not_configured",
            )
        if count <= 0:
            return []

        prompt = (
            "你是英语跟读课程编辑。请基于给定种子课程，生成新的练习卡片 JSON 数组。\n"
            f"目标数量：{count}\n"
            "返回格式要求：\n"
            "1) 只返回 JSON 数组，不要 markdown，不要解释。\n"
            "2) 每个元素字段必须完整："
            "title, subtitle, pack_name, english_text, translation, scenario, mode_hint, "
            "blind_box_prompt, tags, difficulty, estimated_seconds, poster_blurb, theme_tone。\n"
            "3) english_text 必须是自然、真实、可朗读的一句英文；translation 为自然中文。每一张卡片的 english_text 和 translation 必须完全不同。\n"
            "4) mode_hint 必须针对当前的 english_text 提供具体的发音或连读提示，每一张卡片的 mode_hint 必须完全不同，不要照抄参考提示。\n"
            "5) tags 为 2~3 个简短中文标签；estimated_seconds 在 14~30 之间。\n"
            f"6) title 可以按顺序编号，例如 'Daily English {offset + 1}', 'Daily English {offset + 2}' 等。\n"
            "7) 避免重复内容，不要生成占位符。"
        )
        payload = {
            "model": settings.deepseek_model,
            "temperature": 1.15,
            "max_tokens": min(8192, 320 * count),
            "messages": [
                {"role": "system", "content": "你是严格输出 JSON 的课程内容生成器。"},
                {"role": "user", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"日期种子：{current_day.isoformat()}\n"
                        f"批次偏移量：{offset}（请生成完全不同于之前批次的内容）\n"
                        f"参考标题：{seed_lesson.title}\n"
                        f"参考副标题：{seed_lesson.subtitle}\n"
                        f"参考句子：{seed_lesson.english_text}\n"
                        f"参考释义：{seed_lesson.translation}\n"
                        f"参考场景：{seed_lesson.scenario}\n"
                        f"参考提示：{seed_lesson.mode_hint}\n"
                        f"参考标签：{', '.join(seed_lesson.tags)}\n"
                    ),
                },
            ],
        }
        raw = await self._request_chat_completion(payload)
        content = self._extract_message_text(raw)
        items = self._parse_lesson_candidates(content)
        if not items:
            raise IntegrationError(
                "DeepSeek returned empty lesson candidates.",
                code="lesson_generation_failed",
            )
        return items[:count]

    async def _request_chat_completion(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
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
                "DeepSeek request failed while generating lessons.",
                code="lesson_generation_failed",
            ) from error
        except httpx.HTTPError as error:
            raise IntegrationError(
                "DeepSeek is unavailable while generating lessons.",
                code="lesson_generation_failed",
            ) from error

        payload = response.json()
        if not isinstance(payload, dict):
            raise IntegrationError(
                "DeepSeek returned an invalid response payload.",
                code="lesson_generation_failed",
            )
        return payload

    def _parse_lesson_candidates(self, content: str) -> list[GeneratedLessonCandidate]:
        text = content.strip()
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end >= start:
            text = text[start : end + 1]
        data = json.loads(text)
        if not isinstance(data, list):
            raise IntegrationError(
                "DeepSeek lesson payload is not a JSON array.",
                code="lesson_generation_failed",
            )

        candidates: list[GeneratedLessonCandidate] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            tags = item.get("tags")
            normalized_tags = (
                [str(tag).strip() for tag in tags if str(tag).strip()]
                if isinstance(tags, list)
                else []
            )
            english_text = str(item.get("english_text", "")).strip()
            translation = str(item.get("translation", "")).strip()
            title = str(item.get("title", "")).strip()
            if not title or not english_text or not translation:
                continue
            estimated_seconds = int(item.get("estimated_seconds", 20))
            candidates.append(
                GeneratedLessonCandidate(
                    title=title,
                    subtitle=str(item.get("subtitle", "每日精读 · 今日推荐")).strip()
                    or "每日精读 · 今日推荐",
                    pack_name=str(item.get("pack_name", "每日精选")).strip() or "每日精选",
                    english_text=english_text,
                    translation=translation,
                    scenario=str(item.get("scenario", "日常跟读训练")).strip() or "日常跟读训练",
                    mode_hint=str(item.get("mode_hint", "先慢读一遍，再按正常语速连读。")).strip()
                    or "先慢读一遍，再按正常语速连读。",
                    blind_box_prompt=str(
                        item.get("blind_box_prompt", "把这句读给未来的你，声音会更坚定。")
                    ).strip()
                    or "把这句读给未来的你，声音会更坚定。",
                    tags=normalized_tags[:3] or ["每日更新", "真实语料"],
                    difficulty=str(item.get("difficulty", "Intermediate")).strip() or "Intermediate",
                    estimated_seconds=max(14, min(30, estimated_seconds)),
                    poster_blurb=str(
                        item.get("poster_blurb", "你读出的每一句，都会变成更清晰的自己。")
                    ).strip()
                    or "你读出的每一句，都会变成更清晰的自己。",
                    theme_tone=str(item.get("theme_tone", "mint-latte")).strip() or "mint-latte",
                )
            )
        return candidates
