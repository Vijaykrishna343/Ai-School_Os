"""
School Management Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting School entities.
"""

from math import ceil
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_db, get_school_service
from app.identity.dependencies.require_permission import require_permission
from app.schemas.school.school import (
    SchoolCreate,
    SchoolListResponse,
    SchoolResponse,
    SchoolUpdate,
)
from app.services.school_service import SchoolService

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create School",
    dependencies=[Depends(require_permission("school.create"))],
)
def create_school(
    school: SchoolCreate,
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Create a new school entity.
    """
    created_school = service.create_school(db, school)

    return ApiResponse.success(
        message="School created successfully.",
        data=SchoolResponse.model_validate(created_school).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All Schools",
    dependencies=[Depends(require_permission("school.view"))],
)
def get_all_schools(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Get paginated list of active school entities.
    """
    schools = service.get_all_schools(db)
    total = len(schools)

    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = schools[start:end]
    total_pages = ceil(total / page_size) if total > 0 else 0

    list_response = SchoolListResponse(
        items=[
            SchoolResponse.model_validate(school)
            for school in paginated_items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return ApiResponse.success(
        message="Schools fetched successfully.",
        data=list_response.model_dump(),
    )


@router.get(
    "/{school_id}",
    response_model=dict,
    summary="Get School",
    dependencies=[Depends(require_permission("school.view"))],
)
def get_school(
    school_id: UUID,
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Retrieve a school by ID.
    """
    school = service.get_school(db, school_id)

    return ApiResponse.success(
        message="School fetched successfully.",
        data=SchoolResponse.model_validate(school).model_dump(),
    )


@router.put(
    "/{school_id}",
    response_model=dict,
    summary="Update School",
    dependencies=[Depends(require_permission("school.update"))],
)
def update_school(
    school_id: UUID,
    school: SchoolUpdate,
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Update an existing school entity.
    """
    updated_school = service.update_school(
        db,
        school_id,
        school,
    )

    return ApiResponse.success(
        message="School updated successfully.",
        data=SchoolResponse.model_validate(updated_school).model_dump(),
    )


@router.delete(
    "/{school_id}",
    response_model=dict,
    summary="Delete School",
    dependencies=[Depends(require_permission("school.delete"))],
)
def delete_school(
    school_id: UUID,
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Soft delete a school entity.
    """
    service.delete_school(
        db,
        school_id,
    )

    return ApiResponse.success(
        message="School deleted successfully.",
    )