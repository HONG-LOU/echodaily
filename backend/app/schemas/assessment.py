from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AssessmentCreateSchema(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=64)
    mode: Literal["follow", "blind_box"]
    duration_seconds: int = Field(ge=5, le=300)
    transcript: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid", strict=True)


class AssessmentDimensionSchema(BaseModel):
    key: str
    label: str
    score: int

    model_config = ConfigDict(from_attributes=True)


class AssessmentHighlightSchema(BaseModel):
    word: str
    expected_ipa: str
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
    mode: str
    duration_seconds: int
    transcript: str | None
    transcript_used: bool
    overall_score: int
    comparison_ratio: float
    mistake_count: int
    headline: str
    encouragement: str
    poster_caption: str
    poster_theme: str
    created_at: datetime
    dimensions: list[AssessmentDimensionSchema]
    highlights: list[AssessmentHighlightSchema]

    model_config = ConfigDict(from_attributes=True)
