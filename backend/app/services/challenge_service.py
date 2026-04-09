from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.challenge_repository import ChallengeRepository
from app.schemas.challenge import ChallengeResponseSchema


class ChallengeService:
    def __init__(self, challenge_repository: ChallengeRepository) -> None:
        self.challenge_repository = challenge_repository

    async def list_challenges(self, session: AsyncSession) -> list[ChallengeResponseSchema]:
        challenges = await self.challenge_repository.list_active(session)
        return [ChallengeResponseSchema.model_validate(challenge) for challenge in challenges]
