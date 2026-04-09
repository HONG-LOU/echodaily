from pydantic import BaseModel, ConfigDict


class DashboardUserSchema(BaseModel):
    id: str
    nickname: str
    avatar_symbol: str
    avatar_url: str | None
    streak_days: int
    total_practices: int
    weekly_minutes: int
    weak_sound: str
    city: str
    bio: str

    model_config = ConfigDict(from_attributes=True)


class StatCardSchema(BaseModel):
    label: str
    value: str
    caption: str


class LessonSpotlightSchema(BaseModel):
    id: str
    title: str
    subtitle: str
    pack_name: str
    english_text: str
    translation: str
    scenario: str
    mode_hint: str
    tags: list[str]
    difficulty: str
    estimated_seconds: int
    theme_tone: str

    model_config = ConfigDict(from_attributes=True)


class RecentScoreSchema(BaseModel):
    assessment_id: str
    lesson_title: str
    overall_score: int
    practiced_at: str


class DashboardResponseSchema(BaseModel):
    user: DashboardUserSchema
    today_lesson: LessonSpotlightSchema
    quick_stats: list[StatCardSchema]
    recent_scores: list[RecentScoreSchema]
