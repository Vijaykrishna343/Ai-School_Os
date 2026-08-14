from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_exam_schedule_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.exam.exam_schedule import ExamSchedule
from app.schemas.exam.exam_schedule import (
    ExamScheduleCreate,
    ExamScheduleFilter,
    ExamScheduleListResponse,
    ExamScheduleResponse,
    ExamScheduleUpdate,
)
from app.services.exam_schedule_service import ExamScheduleService

router = APIRouter()


@router.post(
    "",
    response_model=ExamScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam Schedule",
)
def create_exam_schedule(
    schedule: ExamScheduleCreate,
    current_user: IdentityUser = Depends(require_permission("exam.create")),
    db: Session = Depends(get_db),
    service: ExamScheduleService = Depends(get_exam_schedule_service),
) -> ExamSchedule:
    """
    Create a new examination schedule.
    """
    return service.create_exam_schedule(
        db=db,
        schedule_data=schedule,
        current_school_id=current_user.school_id,
    )


@router.get(
    "",
    response_model=ExamScheduleListResponse,
    summary="Get Exam Schedules",
)
def get_exam_schedules(
    exam_id: UUID | None = Query(default=None),
    school_id: UUID | None = Query(default=None),
    academic_year_id: UUID | None = Query(default=None),
    school_class_id: UUID | None = Query(default=None),
    section_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    exam_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("exam.view")),
    db: Session = Depends(get_db),
    service: ExamScheduleService = Depends(get_exam_schedule_service),
) -> ExamScheduleListResponse:
    """
    Retrieve paginated exam schedules matching query parameters.
    """
    effective_school_id = current_user.school_id
    filters = ExamScheduleFilter(
        exam_id=exam_id,
        school_id=effective_school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        subject_id=subject_id,
        exam_date=exam_date,
        page=page,
        page_size=page_size,
    )
    return service.get_exam_schedules(
        db=db,
        filters=filters,
    )


@router.get(
    "/{schedule_id}",
    response_model=ExamScheduleResponse,
    summary="Get Exam Schedule by ID",
)
def get_exam_schedule(
    schedule_id: UUID,
    current_user: IdentityUser = Depends(require_permission("exam.view")),
    db: Session = Depends(get_db),
    service: ExamScheduleService = Depends(get_exam_schedule_service),
) -> ExamSchedule:
    """
    Retrieve an exam schedule by ID.
    """
    return service.get_exam_schedule(
        db=db,
        schedule_id=schedule_id,
        school_id=current_user.school_id,
    )


@router.put(
    "/{schedule_id}",
    response_model=ExamScheduleResponse,
    summary="Update Exam Schedule",
)
def update_exam_schedule(
    schedule_id: UUID,
    schedule: ExamScheduleUpdate,
    current_user: IdentityUser = Depends(require_permission("exam.update")),
    db: Session = Depends(get_db),
    service: ExamScheduleService = Depends(get_exam_schedule_service),
) -> ExamSchedule:
    """
    Update an existing exam schedule.
    """
    return service.update_exam_schedule(
        db=db,
        schedule_id=schedule_id,
        schedule_data=schedule,
        school_id=current_user.school_id,
    )


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Exam Schedule",
)
def delete_exam_schedule(
    schedule_id: UUID,
    current_user: IdentityUser = Depends(require_permission("exam.delete")),
    db: Session = Depends(get_db),
    service: ExamScheduleService = Depends(get_exam_schedule_service),
) -> None:
    """
    Soft delete an exam schedule.
    """
    service.delete_exam_schedule(
        db=db,
        schedule_id=schedule_id,
        school_id=current_user.school_id,
    )
