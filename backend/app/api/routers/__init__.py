from fastapi import APIRouter

from app.api.routers.assessments import router as assessments_router
from app.api.routers.auth import router as auth_router
from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.health import router as health_router
from app.api.routers.lessons import router as lessons_router
from app.api.routers.profile import router as profile_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(lessons_router)
api_router.include_router(assessments_router)
api_router.include_router(profile_router)
