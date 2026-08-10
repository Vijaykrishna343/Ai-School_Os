from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_student_exam_result_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.exam.student_exam_result import StudentExamResult
from app.schemas.exam.student_exam_result import (
    StudentExamResultCreate,
    StudentExamResultFilter,
    StudentExamResultListResponse,
    StudentExamResultResponse,
    StudentExamResultUpdate,
)
from app.services.student_exam_result_service import StudentExamResultService

router = APIRouter()


@router.post(
    "",
    response_model=StudentExamResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Student Exam Result",
)
def create_student_exam_result(
    result: StudentExamResultCreate,
    current_user: IdentityUser = Depends(require_permission("exam.create")),
    db: Session = Depends(get_db),
    service: StudentExamResultService = Depends(
        get_student_exam_result_service
    ),
) -> StudentExamResult:
    """
    Create a new student exam result.
    """
    return service.create_student_exam_result(
        db=db,
        result_data=result,
        current_school_id=current_user.school_id,
    )


@router.get(
    "",
    response_model=StudentExamResultListResponse,
    summary="Get Student Exam Results",
)
def get_student_exam_results(
    exam_schedule_id: UUID | None = Query(default=None),
    student_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("exam.view")),
    db: Session = Depends(get_db),
    service: StudentExamResultService = Depends(
        get_student_exam_result_service
    ),
) -> StudentExamResultListResponse:
    """
    Retrieve paginated student exam results matching query parameters.
    """
    filters = StudentExamResultFilter(
        exam_schedule_id=exam_schedule_id,
        student_id=student_id,
        page=page,
        page_size=page_size,
    )
    return service.get_student_exam_results(
        db=db,
        filters=filters,
        school_id=current_user.school_id,
    )



@router.get(
    "/{result_id}",
    response_model=StudentExamResultResponse,
    summary="Get Student Exam Result by ID",
)
def get_student_exam_result(
    result_id: UUID,
    current_user: IdentityUser = Depends(require_permission("exam.view")),
    db: Session = Depends(get_db),
    service: StudentExamResultService = Depends(
        get_student_exam_result_service
    ),
) -> StudentExamResult:
    """
    Retrieve a student exam result by ID.
    """
    return service.get_student_exam_result(
        db=db,
        result_id=result_id,
        school_id=current_user.school_id,
    )


@router.put(
    "/{result_id}",
    response_model=StudentExamResultResponse,
    summary="Update Student Exam Result",
)
def update_student_exam_result(
    result_id: UUID,
    result: StudentExamResultUpdate,
    current_user: IdentityUser = Depends(require_permission("exam.update")),
    db: Session = Depends(get_db),
    service: StudentExamResultService = Depends(
        get_student_exam_result_service
    ),
) -> StudentExamResult:
    """
    Update an existing student exam result.
    """
    return service.update_student_exam_result(
        db=db,
        result_id=result_id,
        result_data=result,
        school_id=current_user.school_id,
    )


@router.delete(
    "/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Student Exam Result",
)
def delete_student_exam_result(
    result_id: UUID,
    current_user: IdentityUser = Depends(require_permission("exam.delete")),
    db: Session = Depends(get_db),
    service: StudentExamResultService = Depends(
        get_student_exam_result_service
    ),
) -> None:
    """
    Soft delete a student exam result.
    """
    service.delete_student_exam_result(
        db=db,
        result_id=result_id,
        school_id=current_user.school_id,
        current_user_id=current_user.id,
    )
