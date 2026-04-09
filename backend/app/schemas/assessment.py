from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AssessmentCreateSchema(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=64)
    duration_seconds: int = Field(ge=1, le=300)
    audio_format: Literal["mp3", "wav", "pcm", "speex"] = "mp3"
    audio_base64: str = Field(min_length=1, max_length=8_000_000)

    model_config = ConfigDict(extra="forbid", strict=True)


class AssessmentDimensionSchema(BaseModel):
    key: str
    label: str
    score: int

    model_config = ConfigDict(from_attributes=True)


class AssessmentHighlightSchema(BaseModel):
    word: str
    expected_ipa: str
    observed_ipa: str
    accuracy_score: int
    observed_issue: str
    coach_tip: str
    severity: Literal["low", "medium", "high"]

    model_config = ConfigDict(from_attributes=True)


class AssessmentDetailSchema(BaseModel):
    id: str
    lesson_id: str
    lesson_title: str
    lesson_text: str
    translation: str
    duration_seconds: int
    recognized_text: str
    overall_score: int
    mistake_count: int
    headline: str
    encouragement: str
    created_at: datetime
    dimensions: list[AssessmentDimensionSchema]
    highlights: list[AssessmentHighlightSchema]

    model_config = ConfigDict(from_attributes=True)
