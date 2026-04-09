from pydantic import BaseModel, ConfigDict


class LessonResponseSchema(BaseModel):
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
