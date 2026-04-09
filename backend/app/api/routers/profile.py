from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, DbSession, get_profile_service
from app.schemas.profile import ProfileResponseSchema
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponseSchema)
async def get_profile(
    session: DbSession,
    current_user: CurrentUser,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponseSchema:
    return await service.get_profile(session, current_user=current_user)
