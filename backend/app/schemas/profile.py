from pydantic import BaseModel, ConfigDict


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
    mistake_notebook: list[MistakeNotebookEntrySchema]
    recent_practices: list[RecentPracticeSchema]

    model_config = ConfigDict(from_attributes=True)
