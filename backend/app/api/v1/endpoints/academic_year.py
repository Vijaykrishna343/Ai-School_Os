"""
Academic Year Management Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting AcademicYear entities.
"""

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import (
    get_academic_year_service,
    get_db,
    get_progression_preview_service,
    get_student_promotion_service,
)
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.academic_year import (
    AcademicYearCreate,
    AcademicYearListResponse,
    AcademicYearResponse,
    AcademicYearUpdate,
)
from app.schemas.student.progression_preview_schema import (
    ProgressionPreviewRequest,
    ProgressionPreviewResponse,
)
from app.schemas.student.promotion_schema import (
    AcademicYearTransitionRequest,
    AcademicYearTransitionResponse,
)
from app.services.academic_year_service import AcademicYearService
from app.services.student.progression_preview_service import ProgressionPreviewService
from app.services.student.student_promotion_service import StudentPromotionService

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create Academic Year",
)
def create_academic_year(
    academic_year: AcademicYearCreate,
    current_user: IdentityUser = Depends(require_permission("academic_year.create")),
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Create a new academic year entity for the authenticated user's school.
    """
    created = service.create_academic_year(
        db,
        academic_year,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Academic year created successfully.",
        data=AcademicYearResponse.model_validate(
            created
        ).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All Academic Years",
)
def get_all_academic_years(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("academic_year.view")),
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Get paginated list of active academic years for the authenticated user's school.
    Uses database-level offset and limit.
    """
    items, total, total_pages = service.get_paginated_academic_years(
        db,
        school_id=current_user.school_id,
        page=page,
        page_size=page_size,
    )

    list_response = AcademicYearListResponse(
        items=[
            AcademicYearResponse.model_validate(ay)
            for ay in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return ApiResponse.success(
        message="Academic years fetched successfully.",
        data=list_response.model_dump(),
    )


@router.get(
    "/{academic_year_id}",
    response_model=dict,
    summary="Get Academic Year",
)
def get_academic_year(
    academic_year_id: UUID,
    current_user: IdentityUser = Depends(require_permission("academic_year.view")),
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Retrieve an academic year by ID for the authenticated user's school.
    """
    academic_year = service.get_academic_year(
        db,
        academic_year_id,
        school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Academic year fetched successfully.",
        data=AcademicYearResponse.model_validate(
            academic_year
        ).model_dump(),
    )


@router.put(
    "/{academic_year_id}",
    response_model=dict,
    summary="Update Academic Year",
)
def update_academic_year(
    academic_year_id: UUID,
    academic_year: AcademicYearUpdate,
    current_user: IdentityUser = Depends(require_permission("academic_year.update")),
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Update an existing academic year entity for the authenticated user's school.
    """
    updated = service.update_academic_year(
        db,
        academic_year_id,
        academic_year,
        school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Academic year updated successfully.",
        data=AcademicYearResponse.model_validate(
            updated
        ).model_dump(),
    )


@router.delete(
    "/{academic_year_id}",
    response_model=dict,
    summary="Delete Academic Year",
)
def delete_academic_year(
    academic_year_id: UUID,
    current_user: IdentityUser = Depends(require_permission("academic_year.delete")),
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Soft delete an academic year entity for the authenticated user's school.
    """
    service.delete_academic_year(
        db,
        academic_year_id,
        school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Academic year deleted successfully.",
    )


@router.post(
    "/{academic_year_id}/transition",
    response_model=dict,
    summary="Academic Year Transition",
)
def transition_academic_year(
    academic_year_id: UUID,
    request: AcademicYearTransitionRequest,
    current_user: IdentityUser = Depends(
        require_permission("student.transition")
    ),
    db: Session = Depends(get_db),
    service: StudentPromotionService = Depends(get_student_promotion_service),
) -> dict[str, object]:
    """
    Execute transition workflow from source academic year to target academic year.
    Preserves enrollment history of active students in source year and activates target academic year.
    """
    result = service.transition_academic_year(
        db=db,
        source_academic_year_id=academic_year_id,
        data=request,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message=result.message,
        data=result.model_dump(),
    )


@router.post(
    "/{academic_year_id}/progression-preview",
    response_model=dict,
    summary="Academic Year Progression Preview",
)
def generate_progression_preview(
    academic_year_id: UUID,
    request: ProgressionPreviewRequest,
    current_user: IdentityUser = Depends(
        require_permission("progression.preview")
    ),
    db: Session = Depends(get_db),
    service: ProgressionPreviewService = Depends(get_progression_preview_service),
) -> dict[str, object]:
    """
    READ-ONLY calculation of prospective student progression outcomes
    from source academic year to target academic year.
    """
    result = service.generate_preview(
        db=db,
        source_academic_year_id=academic_year_id,
        request=request,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Academic progression preview generated successfully.",
        data=result.model_dump(),
    )