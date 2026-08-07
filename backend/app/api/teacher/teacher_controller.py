from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Body,
)
from sqlalchemy.orm import Session

from app.common.responses.api_response import (
    ApiResponse,
)
from app.dependencies.database import (
    get_db,
)
from app.api.teacher.teacher_dependency import (
    get_teacher_service,
)
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
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
):
    """
    Create a new teacher.
    """

    created_teacher = service.create_teacher(
        db=db,
        teacher_data=teacher,
    )

    return ApiResponse.success(
        data=created_teacher.model_dump(mode="json"),
        message="Teacher created successfully.",
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
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
):
    """
    Retrieve a teacher by ID.
    """

    teacher = service.get_teacher(
        db=db,
        teacher_id=teacher_id,
    )

    return ApiResponse.success(
        data=teacher.model_dump(mode="json"),
        message="Teacher retrieved successfully.",
    )


@router.get(
    "",
    response_model=dict,
    summary="Get Teachers",
)
def get_teachers(
    filters: TeacherFilter = Depends(),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
):
    """
    Retrieve teachers with filtering and pagination.
    """

    result = service.get_teachers(
        db=db,
        filters=filters,
    )

    return ApiResponse.success(
        data=result.model_dump(mode="json"),
        message="Teachers retrieved successfully.",
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
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
):
    updated_teacher = service.update_teacher(
        db=db,
        teacher_id=teacher_id,
        teacher_data=teacher,
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
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
):
    """
    Soft delete a teacher.
    """

    service.delete_teacher(
        db=db,
        teacher_id=teacher_id,
    )

    return ApiResponse.success(
        message="Teacher deleted successfully.",
    )