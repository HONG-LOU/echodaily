from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import DbSession, get_challenge_service
from app.schemas.challenge import ChallengeResponseSchema
from app.services.challenge_service import ChallengeService

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("", response_model=list[ChallengeResponseSchema])
async def list_challenges(
    session: DbSession,
    service: Annotated[ChallengeService, Depends(get_challenge_service)],
) -> list[ChallengeResponseSchema]:
    return await service.list_challenges(session)
