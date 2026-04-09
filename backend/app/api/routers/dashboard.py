from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, DbSession, get_dashboard_service
from app.schemas.dashboard import DashboardResponseSchema
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponseSchema)
async def get_dashboard(
    session: DbSession,
    current_user: CurrentUser,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> DashboardResponseSchema:
    return await service.get_dashboard(
        session,
        current_user=current_user,
        current_day=date.today(),
    )
