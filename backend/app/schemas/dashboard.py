from pydantic import BaseModel, ConfigDict


class DashboardUserSchema(BaseModel):
    id: str
    nickname: str
    avatar_symbol: str
    streak_days: int
    total_practices: int
    weekly_minutes: int
    plan_name: str
    weak_sound: str
    target_pack: str
    focus_tag: str
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
    blind_box_prompt: str
    tags: list[str]
    difficulty: str
    estimated_seconds: int
    poster_blurb: str
    theme_tone: str

    model_config = ConfigDict(from_attributes=True)


class RecentScoreSchema(BaseModel):
    assessment_id: str
    lesson_title: str
    overall_score: int
    practiced_at: str


class MembershipOfferSchema(BaseModel):
    title: str
    monthly_price: str
    yearly_price: str
    highlights: list[str]
    call_to_action: str


class PartnerPitchSchema(BaseModel):
    title: str
    summary: str
    bullets: list[str]
    call_to_action: str


class DashboardResponseSchema(BaseModel):
    user: DashboardUserSchema
    today_lesson: LessonSpotlightSchema
    quick_stats: list[StatCardSchema]
    challenge_spotlight: dict[str, str | int]
    membership_offer: MembershipOfferSchema
    partner_pitch: PartnerPitchSchema
    recent_scores: list[RecentScoreSchema]
