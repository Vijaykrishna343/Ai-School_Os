"""
Student Management Controller Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting Student entities.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Path,
)
from sqlalchemy.orm import Session

from app.api.student.student_dependency import (
    get_student_service,
)
from app.common.responses.api_response import (
    ApiResponse,
)
from app.dependencies.database import (
    get_db,
)
from app.identity.dependencies.require_permission import require_permission
from app.schemas.student.student_schema import (
    StudentCreate,
    StudentFilter,
    StudentResponse,
    StudentUpdate,
)
from app.services.student.student_service import (
    StudentService,
)

router = APIRouter()


@router.post(
    "",
    response_model=dict,
    summary="Create Student",
    dependencies=[Depends(require_permission("student.create"))],
)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    service: StudentService = Depends(get_student_service),
) -> dict[str, object]:
    """
    Create a new student.
    """
    created_student = service.create_student(
        db=db,
        student_data=student,
    )

    return ApiResponse.success(
        data=StudentResponse.model_validate(
            created_student
        ).model_dump(
            mode="json"
        ),
        message="Student created successfully.",
    )


@router.get(
    "",
    response_model=dict,
    summary="Get Students",
    dependencies=[Depends(require_permission("student.view"))],
)
def get_students(
    filters: StudentFilter = Depends(),
    db: Session = Depends(get_db),
    service: StudentService = Depends(get_student_service),
) -> dict[str, object]:
    """
    Retrieve students with filtering and pagination.
    """
    result = service.get_students(
        db=db,
        filters=filters,
    )

    return ApiResponse.success(
        data=result,
        message="Students retrieved successfully.",
    )


@router.get(
    "/{student_id}",
    response_model=dict,
    summary="Get Student by ID",
    dependencies=[Depends(require_permission("student.view"))],
)
def get_student(
    student_id: UUID = Path(
        ...,
        description="Student ID",
    ),
    db: Session = Depends(get_db),
    service: StudentService = Depends(get_student_service),
) -> dict[str, object]:
    """
    Retrieve a student by ID.
    """
    student = service.get_student(
        db=db,
        student_id=student_id,
    )

    return ApiResponse.success(
        data=StudentResponse.model_validate(
            student
        ).model_dump(
            mode="json"
        ),
        message="Student retrieved successfully.",
    )


@router.put(
    "/{student_id}",
    response_model=dict,
    summary="Update Student",
    dependencies=[Depends(require_permission("student.update"))],
)
def update_student(
    student_id: UUID = Path(
        ...,
        description="Student ID",
    ),
    student: StudentUpdate = ...,
    db: Session = Depends(get_db),
    service: StudentService = Depends(get_student_service),
) -> dict[str, object]:
    """
    Update an existing student.
    """
    updated_student = service.update_student(
        db=db,
        student_id=student_id,
        student_data=student,
    )

    return ApiResponse.success(
        data=StudentResponse.model_validate(
            updated_student
        ).model_dump(
            mode="json"
        ),
        message="Student updated successfully.",
    )


@router.delete(
    "/{student_id}",
    response_model=dict,
    summary="Delete Student",
    dependencies=[Depends(require_permission("student.delete"))],
)
def delete_student(
    student_id: UUID = Path(
        ...,
        description="Student ID",
    ),
    db: Session = Depends(get_db),
    service: StudentService = Depends(get_student_service),
) -> dict[str, object]:
    """
    Soft delete a student.
    """
    service.delete_student(
        db=db,
        student_id=student_id,
    )

    return ApiResponse.success(
        message="Student deleted successfully.",
    )