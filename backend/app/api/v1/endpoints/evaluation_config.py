from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_evaluation_config_service
from app.identity.dependencies import require_permission
from app.identity.models import IdentityUser
from app.schemas.grading.evaluation_config import (
    EvaluationConfigCreate,
    EvaluationConfigListResponse,
    EvaluationConfigResponse,
)
from app.services.evaluation_config_service import EvaluationConfigService

router = APIRouter()


@router.post(
    "",
    response_model=EvaluationConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation_config(
    config_data: EvaluationConfigCreate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("evaluation_config.create")),
    service: EvaluationConfigService = Depends(get_evaluation_config_service),
) -> EvaluationConfigResponse:
    created = service.create_evaluation_config(
        db,
        config_data=config_data,
        current_school_id=current_user.school_id,
    )
    return EvaluationConfigResponse.model_validate(created)


@router.get(
    "",
    response_model=EvaluationConfigListResponse,
)
def list_evaluation_configs(
    academic_year_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("evaluation_config.view")),
    service: EvaluationConfigService = Depends(get_evaluation_config_service),
) -> EvaluationConfigListResponse:
    return service.list_evaluation_configs(
        db,
        school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{config_id}",
    response_model=EvaluationConfigResponse,
)
def get_evaluation_config(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("evaluation_config.view")),
    service: EvaluationConfigService = Depends(get_evaluation_config_service),
) -> EvaluationConfigResponse:
    config = service.get_evaluation_config(
        db,
        config_id=config_id,
        current_school_id=current_user.school_id,
    )
    return EvaluationConfigResponse.model_validate(config)
