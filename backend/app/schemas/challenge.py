from pydantic import BaseModel, ConfigDict


class ChallengeResponseSchema(BaseModel):
    id: str
    title: str
    description: str
    deposit_amount: int
    participants: int
    days_total: int
    days_left: int
    score_threshold: int
    reward_pool: int
    teaser: str

    model_config = ConfigDict(from_attributes=True)
