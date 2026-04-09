from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import DbSession, get_assessment_service
from app.schemas.assessment import AssessmentCreateSchema, AssessmentDetailSchema
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreateSchema,
    session: DbSession,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentDetailSchema:
    return await service.create_assessment(session, payload)


@router.get("/{assessment_id}", response_model=AssessmentDetailSchema)
async def get_assessment(
    assessment_id: str,
    session: DbSession,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentDetailSchema:
    return await service.get_assessment(session, assessment_id)
