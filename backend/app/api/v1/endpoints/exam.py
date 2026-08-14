from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums.exam import AssessmentType, AttemptType, ExamStatus
from app.dependencies import get_db, get_exam_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.exam.exam import Exam
from app.schemas.exam.exam import (
    ExamCreate,
    ExamFilter,
    ExamListResponse,
    ExamResponse,
    ExamUpdate,
)
from app.services.exam_service import ExamService

router = APIRouter()


@router.post(
    "",
    response_model=ExamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam",
)
def create_exam(
    exam: ExamCreate,
    current_user: IdentityUser = Depends(require_permission("exam.create")),
    db: Session = Depends(get_db),
    service: ExamService = Depends(get_exam_service),
) -> Exam:
    """
    Create a new examination entity for the authenticated user's school.
    """
    return service.create_exam(
        db=db,
        exam_data=exam,
        current_school_id=current_user.school_id,
    )


@router.get(
    "",
    response_model=ExamListResponse,
    summary="Get Exams",
)
def get_exams(
    school_id: UUID | None = Query(default=None),
    academic_year_id: UUID | None = Query(default=None),
    assessment_type: AssessmentType | None = Query(default=None),
    attempt_type: AttemptType | None = Query(default=None),
    exam_type: str | None = Query(default=None, description="Deprecated legacy filter"),
    status: ExamStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("exam.view")),
    db: Session = Depends(get_db),
    service: ExamService = Depends(get_exam_service),
) -> ExamListResponse:
    """
    Retrieve paginated exams matching query parameters, scoped to user's school if applicable.
    """
    effective_school_id = current_user.school_id
    filters = ExamFilter(
        school_id=effective_school_id,
        academic_year_id=academic_year_id,
        assessment_type=assessment_type,
        attempt_type=attempt_type,
        exam_type=exam_type,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.get_exams(
        db=db,
        filters=filters,
    )


@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
    summary="Get Exam by ID",
)
def get_exam(
    exam_id: UUID,
    current_user: IdentityUser = Depends(require_permission("exam.view")),
    db: Session = Depends(get_db),
    service: ExamService = Depends(get_exam_service),
) -> Exam:
    """
    Retrieve an exam by ID.
    """
    return service.get_exam(
        db=db,
        exam_id=exam_id,
        school_id=current_user.school_id,
    )


@router.put(
    "/{exam_id}",
    response_model=ExamResponse,
    summary="Update Exam",
)
def update_exam(
    exam_id: UUID,
    exam: ExamUpdate,
    current_user: IdentityUser = Depends(require_permission("exam.update")),
    db: Session = Depends(get_db),
    service: ExamService = Depends(get_exam_service),
) -> Exam:
    """
    Update an existing exam.
    """
    return service.update_exam(
        db=db,
        exam_id=exam_id,
        exam_data=exam,
        school_id=current_user.school_id,
    )


@router.delete(
    "/{exam_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Exam",
)
def delete_exam(
    exam_id: UUID,
    current_user: IdentityUser = Depends(require_permission("exam.delete")),
    db: Session = Depends(get_db),
    service: ExamService = Depends(get_exam_service),
) -> None:
    """
    Soft delete an exam.
    """
    service.delete_exam(
        db=db,
        exam_id=exam_id,
        school_id=current_user.school_id,
    )
