from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DbSession, get_profile_service
from app.schemas.profile import ProfileResponseSchema
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponseSchema)
async def get_profile(
    session: DbSession,
    service: Annotated[ProfileService, Depends(get_profile_service)],
    user_id: str = Query(default="demo-user", min_length=1),
) -> ProfileResponseSchema:
    return await service.get_profile(session, user_id=user_id)
