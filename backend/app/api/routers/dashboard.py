from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DbSession, get_dashboard_service
from app.schemas.dashboard import DashboardResponseSchema
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponseSchema)
async def get_dashboard(
    session: DbSession,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    user_id: str = Query(default="demo-user", min_length=1),
) -> DashboardResponseSchema:
    return await service.get_dashboard(session, user_id=user_id, current_day=date.today())
