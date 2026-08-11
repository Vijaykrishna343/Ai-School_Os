from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_grade_scale_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.grading.grade_scale import GradeScale
from app.schemas.grading.grade_scale import (
    GradeMatchRequest,
    GradeMatchResponse,
    GradeScaleCreate,
    GradeScaleFilter,
    GradeScaleListResponse,
    GradeScaleResponse,
    GradeScaleUpdate,
)
from app.services.grading_scale_service import GradeScaleService

router = APIRouter()


@router.post(
    "",
    response_model=GradeScaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Grade Scale",
)
def create_grade_scale(
    scale_data: GradeScaleCreate,
    current_user: IdentityUser = Depends(require_permission("grading.manage")),
    db: Session = Depends(get_db),
    service: GradeScaleService = Depends(get_grade_scale_service),
) -> GradeScale:
    """
    Create a new grading scale for the tenant school.
    """
    return service.create_grade_scale(
        db=db,
        scale_data=scale_data,
        current_school_id=current_user.school_id,
    )


@router.get(
    "",
    response_model=GradeScaleListResponse,
    summary="Get Grade Scales",
)
def list_grade_scales(
    is_default: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("grading.view")),
    db: Session = Depends(get_db),
    service: GradeScaleService = Depends(get_grade_scale_service),
) -> GradeScaleListResponse:
    """
    Retrieve paginated grade scales for the tenant school.
    """
    filters = GradeScaleFilter(
        is_default=is_default,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.list_grade_scales(
        db=db,
        filters=filters,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/default",
    response_model=GradeScaleResponse,
    summary="Get Default Grade Scale",
)
def get_default_grade_scale(
    current_user: IdentityUser = Depends(require_permission("grading.view")),
    db: Session = Depends(get_db),
    service: GradeScaleService = Depends(get_grade_scale_service),
) -> GradeScale:
    """
    Retrieve the active default grade scale for the tenant school.
    """
    return service.get_default_grade_scale(
        db=db,
        current_school_id=current_user.school_id,
    )


@router.post(
    "/match-grade",
    response_model=GradeMatchResponse,
    summary="Match Percentage to Grade",
)
def match_grade(
    request: GradeMatchRequest,
    current_user: IdentityUser = Depends(require_permission("grading.view")),
    db: Session = Depends(get_db),
    service: GradeScaleService = Depends(get_grade_scale_service),
) -> GradeMatchResponse:
    """
    Match a percentage score to a grade band in a grade scale (or default scale if not specified).
    """
    return service.calculate_grade(
        db=db,
        percentage=request.percentage,
        scale_id=request.grade_scale_id,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/{scale_id}",
    response_model=GradeScaleResponse,
    summary="Get Grade Scale by ID",
)
def get_grade_scale(
    scale_id: UUID,
    current_user: IdentityUser = Depends(require_permission("grading.view")),
    db: Session = Depends(get_db),
    service: GradeScaleService = Depends(get_grade_scale_service),
) -> GradeScale:
    """
    Retrieve a grade scale by ID.
    """
    return service.get_grade_scale(
        db=db,
        scale_id=scale_id,
        current_school_id=current_user.school_id,
    )


@router.put(
    "/{scale_id}",
    response_model=GradeScaleResponse,
    summary="Update Grade Scale",
)
def update_grade_scale(
    scale_id: UUID,
    scale_data: GradeScaleUpdate,
    current_user: IdentityUser = Depends(require_permission("grading.manage")),
    db: Session = Depends(get_db),
    service: GradeScaleService = Depends(get_grade_scale_service),
) -> GradeScale:
    """
    Update an existing grade scale.
    """
    return service.update_grade_scale(
        db=db,
        scale_id=scale_id,
        scale_data=scale_data,
        current_school_id=current_user.school_id,
    )


@router.delete(
    "/{scale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Grade Scale",
)
def delete_grade_scale(
    scale_id: UUID,
    current_user: IdentityUser = Depends(require_permission("grading.manage")),
    db: Session = Depends(get_db),
    service: GradeScaleService = Depends(get_grade_scale_service),
) -> None:
    """
    Soft delete a grade scale.
    """
    service.delete_grade_scale(
        db=db,
        scale_id=scale_id,
        current_school_id=current_user.school_id,
        current_user_id=current_user.id,
    )
