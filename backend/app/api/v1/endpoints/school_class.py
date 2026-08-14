"""
School Class Management Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting SchoolClass entities.
"""

from math import ceil
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import (
    get_db,
    get_school_class_service,
)
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.school_class import (

    SchoolClassCreate,
    SchoolClassListResponse,
    SchoolClassResponse,
    SchoolClassUpdate,
)
from app.services.school_class_service import (
    SchoolClassService,
)

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create School Class",
)
def create_school_class(
    school_class: SchoolClassCreate,
    current_user: IdentityUser = Depends(require_permission("class.create")),
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
) -> dict[str, object]:
    """
    Create a new school class entity.
    """
    # Enforce authoritative tenant boundary
    school_class.school_id = current_user.school_id

    created = service.create_school_class(
        db,
        school_class,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="School class created successfully.",
        data=SchoolClassResponse.model_validate(
            created
        ).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All School Classes",
)
def get_all_school_classes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("class.view")),
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
) -> dict[str, object]:
    """
    Get paginated list of active school classes for authenticated user's school.
    """
    classes = service.get_school_classes_by_school(
        db,
        school_id=current_user.school_id,
        current_school_id=current_user.school_id,
    )

    total = len(classes)

    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = classes[start:end]
    total_pages = ceil(total / page_size) if total > 0 else 0

    list_response = SchoolClassListResponse(
        items=[
            SchoolClassResponse.model_validate(cls)
            for cls in paginated_items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return ApiResponse.success(
        message="School classes fetched successfully.",
        data=list_response.model_dump(),
    )


@router.get(
    "/{school_class_id}",
    response_model=dict,
    summary="Get School Class",
)
def get_school_class(
    school_class_id: UUID,
    current_user: IdentityUser = Depends(require_permission("class.view")),
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
) -> dict[str, object]:
    """
    Retrieve a school class by ID.
    """
    school_class = service.get_school_class(
        db,
        school_class_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="School class fetched successfully.",
        data=SchoolClassResponse.model_validate(
            school_class
        ).model_dump(),
    )


@router.put(
    "/{school_class_id}",
    response_model=dict,
    summary="Update School Class",
)
def update_school_class(
    school_class_id: UUID,
    school_class: SchoolClassUpdate,
    current_user: IdentityUser = Depends(require_permission("class.update")),
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
) -> dict[str, object]:
    """
    Update an existing school class entity.
    """
    updated = service.update_school_class(
        db,
        school_class_id,
        school_class,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="School class updated successfully.",
        data=SchoolClassResponse.model_validate(
            updated
        ).model_dump(),
    )


@router.delete(
    "/{school_class_id}",
    response_model=dict,
    summary="Delete School Class",
)
def delete_school_class(
    school_class_id: UUID,
    current_user: IdentityUser = Depends(require_permission("class.delete")),
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
) -> dict[str, object]:
    """
    Soft delete a school class entity.
    """
    service.delete_school_class(
        db,
        school_class_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="School class deleted successfully.",
    )