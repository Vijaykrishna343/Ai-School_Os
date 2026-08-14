"""
Teacher Management Controller Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting Teacher entities.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
)
from sqlalchemy.orm import Session

from app.api.teacher.teacher_dependency import (
    get_teacher_service,
)
from app.common.responses.api_response import (
    ApiResponse,
)
from app.dependencies.database import (
    get_db,
)
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.schemas.teacher import (
    TeacherCreate,
    TeacherFilter,
    TeacherUpdate,
)
from app.services.teacher.teacher_service import (
    TeacherService,
)

router = APIRouter()


@router.post(
    "",
    response_model=dict,
    summary="Create Teacher",
)
def create_teacher(
    teacher: TeacherCreate,
    current_user: IdentityUser = Depends(require_permission("teacher.create")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Create a new teacher.
    """
    # Enforce authoritative tenant boundary
    teacher.school_id = current_user.school_id

    created_teacher = service.create_teacher(
        db=db,
        teacher_data=teacher,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=created_teacher.model_dump(mode="json"),
        message="Teacher created successfully.",
    )


@router.get(
    "",
    response_model=dict,
    summary="Get Teachers",
)
def get_teachers(
    filters: TeacherFilter = Depends(),
    current_user: IdentityUser = Depends(require_permission("teacher.view")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Retrieve teachers with filtering and pagination.
    """
    # Enforce authoritative tenant boundary
    filters.school_id = current_user.school_id

    result = service.get_teachers(
        db=db,
        filters=filters,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=result.model_dump(mode="json"),
        message="Teachers retrieved successfully.",
    )


@router.get(
    "/{teacher_id}",
    response_model=dict,
    summary="Get Teacher by ID",
)
def get_teacher(
    teacher_id: UUID = Path(
        ...,
        description="Teacher ID",
    ),
    current_user: IdentityUser = Depends(require_permission("teacher.view")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Retrieve a teacher by ID.
    """
    teacher = service.get_teacher(
        db=db,
        teacher_id=teacher_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=teacher.model_dump(mode="json"),
        message="Teacher retrieved successfully.",
    )


@router.put(
    "/{teacher_id}",
    response_model=dict,
    summary="Update Teacher",
)
def update_teacher(
    teacher: TeacherUpdate = Body(...),
    teacher_id: UUID = Path(
        ...,
        description="Teacher ID",
    ),
    current_user: IdentityUser = Depends(require_permission("teacher.update")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Update an existing teacher.
    """
    updated_teacher = service.update_teacher(
        db=db,
        teacher_id=teacher_id,
        teacher_data=teacher,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=updated_teacher.model_dump(mode="json"),
        message="Teacher updated successfully.",
    )


@router.delete(
    "/{teacher_id}",
    response_model=dict,
    summary="Delete Teacher",
)
def delete_teacher(
    teacher_id: UUID = Path(
        ...,
        description="Teacher ID",
    ),
    current_user: IdentityUser = Depends(require_permission("teacher.delete")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Soft delete a teacher.
    """
    service.delete_teacher(
        db=db,
        teacher_id=teacher_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Teacher deleted successfully.",
    )