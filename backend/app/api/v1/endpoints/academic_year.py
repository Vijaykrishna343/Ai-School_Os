"""
Academic Year Management Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting AcademicYear entities.
"""

from math import ceil
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_academic_year_service, get_db
from app.identity.dependencies.require_permission import require_permission
from app.schemas.academic_year import (
    AcademicYearCreate,
    AcademicYearListResponse,
    AcademicYearResponse,
    AcademicYearUpdate,
)
from app.services.academic_year_service import AcademicYearService

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create Academic Year",
    dependencies=[Depends(require_permission("academic_year.create"))],
)
def create_academic_year(
    academic_year: AcademicYearCreate,
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Create a new academic year entity.
    """
    created = service.create_academic_year(
        db,
        academic_year,
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
    dependencies=[Depends(require_permission("academic_year.view"))],
)
def get_all_academic_years(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Get paginated list of active academic years.
    """
    academic_years = service.get_all_academic_years(db)
    total = len(academic_years)

    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = academic_years[start:end]
    total_pages = ceil(total / page_size) if total > 0 else 0

    list_response = AcademicYearListResponse(
        items=[
            AcademicYearResponse.model_validate(ay)
            for ay in paginated_items
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
    dependencies=[Depends(require_permission("academic_year.view"))],
)
def get_academic_year(
    academic_year_id: UUID,
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Retrieve an academic year by ID.
    """
    academic_year = service.get_academic_year(
        db,
        academic_year_id,
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
    dependencies=[Depends(require_permission("academic_year.update"))],
)
def update_academic_year(
    academic_year_id: UUID,
    academic_year: AcademicYearUpdate,
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Update an existing academic year entity.
    """
    updated = service.update_academic_year(
        db,
        academic_year_id,
        academic_year,
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
    dependencies=[Depends(require_permission("academic_year.delete"))],
)
def delete_academic_year(
    academic_year_id: UUID,
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
) -> dict[str, object]:
    """
    Soft delete an academic year entity.
    """
    service.delete_academic_year(
        db,
        academic_year_id,
    )

    return ApiResponse.success(
        message="Academic year deleted successfully.",
    )