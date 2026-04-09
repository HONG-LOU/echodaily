from pydantic import BaseModel, ConfigDict


class BadgeSchema(BaseModel):
    name: str
    description: str
    unlocked: bool

    model_config = ConfigDict(from_attributes=True)


class MistakeNotebookEntrySchema(BaseModel):
    word: str
    expected_ipa: str
    coach_tip: str
    lesson_title: str
    score: int

    model_config = ConfigDict(from_attributes=True)


class RecentPracticeSchema(BaseModel):
    assessment_id: str
    lesson_title: str
    score: int
    poster_caption: str
    practiced_at: str

    model_config = ConfigDict(from_attributes=True)


class ProfileResponseSchema(BaseModel):
    id: str
    nickname: str
    avatar_symbol: str
    avatar_url: str | None
    city: str
    bio: str
    streak_days: int
    total_practices: int
    weekly_minutes: int
    weak_sound: str
    target_pack: str
    plan_name: str
    pro_active: bool
    badges: list[BadgeSchema]
    mistake_notebook: list[MistakeNotebookEntrySchema]
    recent_practices: list[RecentPracticeSchema]
    coach_cta: dict[str, str]
    membership_hint: dict[str, str | list[str]]

    model_config = ConfigDict(from_attributes=True)
