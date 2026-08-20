from http import HTTPStatus
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException, NotFoundException
from app.common.responses import ApiResponse
from app.dependencies import get_db, get_school_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.school.school import (
    SchoolCreate,
    SchoolListResponse,
    SchoolResponse,
    SchoolStatusUpdate,
    SchoolSubscriptionUpdate,
    SchoolUpdate,
)
from app.services.school_service import SchoolService

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create School",
)
def create_school(
    school: SchoolCreate,
    current_user: IdentityUser = Depends(require_permission("school.create")),
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Create a new school entity (Super Admin platform action).
    """
    if not current_user.is_super_admin:
        raise ForbiddenException("School creation is restricted to Super Admin platform administrators.")

    created_school = service.create_school(db, school)

    return ApiResponse.success(
        message="School created successfully.",
        data=SchoolResponse.model_validate(created_school).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All Schools",
)
def get_all_schools(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("school.view")),
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Get paginated list of schools.
    Super Admin sees all platform schools. School users see only their own school.
    """
    if current_user.is_super_admin:
        schools = service.get_all_schools(db)
    else:
        schools = [service.get_school(db, current_user.school_id)] if current_user.school_id else []

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
)
def get_school(
    school_id: UUID,
    current_user: IdentityUser = Depends(require_permission("school.view")),
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Retrieve a school by ID with tenant verification.
    """
    if not current_user.is_super_admin and current_user.school_id != school_id:
        raise NotFoundException("School", str(school_id))

    school = service.get_school(db, school_id)

    return ApiResponse.success(
        message="School fetched successfully.",
        data=SchoolResponse.model_validate(school).model_dump(),
    )


@router.put(
    "/{school_id}",
    response_model=dict,
    summary="Update School",
)
def update_school(
    school_id: UUID,
    school: SchoolUpdate,
    current_user: IdentityUser = Depends(require_permission("school.update")),
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Update an existing school profile with tenant verification.
    """
    if not current_user.is_super_admin and current_user.school_id != school_id:
        raise NotFoundException("School", str(school_id))

    updated_school = service.update_school(
        db,
        school_id,
        school,
    )

    return ApiResponse.success(
        message="School updated successfully.",
        data=SchoolResponse.model_validate(updated_school).model_dump(),
    )


@router.put(
    "/{school_id}/status",
    response_model=dict,
    summary="Update School Status",
)
def update_school_status(
    school_id: UUID,
    status_data: SchoolStatusUpdate,
    current_user: IdentityUser = Depends(require_permission("school.update")),
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Update school status (Super Admin only: SUSPENDED, ACTIVE, BLOCKED, etc.).
    """
    if not current_user.is_super_admin:
        raise ForbiddenException("School status management is restricted strictly to Super Admin platform administrators.")

    updated_school = service.update_school_status(
        db,
        school_id,
        status_data,
    )

    return ApiResponse.success(
        message="School status updated successfully.",
        data=SchoolResponse.model_validate(updated_school).model_dump(),
    )


@router.put(
    "/{school_id}/subscription",
    response_model=dict,
    summary="Update School Subscription",
)
def update_school_subscription(
    school_id: UUID,
    subscription_data: SchoolSubscriptionUpdate,
    current_user: IdentityUser = Depends(require_permission("school.update")),
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Update school subscription tier and resource limits (Super Admin only).
    """
    if not current_user.is_super_admin:
        raise ForbiddenException("School subscription management is restricted strictly to Super Admin platform administrators.")

    updated_school = service.update_school_subscription(
        db,
        school_id,
        subscription_data,
    )

    return ApiResponse.success(
        message="School subscription updated successfully.",
        data=SchoolResponse.model_validate(updated_school).model_dump(),
    )


@router.delete(
    "/{school_id}",
    response_model=dict,
    summary="Delete School",
)
def delete_school(
    school_id: UUID,
    current_user: IdentityUser = Depends(require_permission("school.delete")),
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
) -> dict[str, object]:
    """
    Soft delete a school entity (Super Admin platform action).
    """
    if not current_user.is_super_admin:
        raise ForbiddenException("Deleting a school entity is restricted strictly to Super Admin platform administrators.")

    service.delete_school(
        db,
        school_id,
    )

    return ApiResponse.success(
        message="School deleted successfully.",
    )