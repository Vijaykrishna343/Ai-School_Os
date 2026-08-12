from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import (
    get_db,
    get_timetable_entry_service,
    get_timetable_service,
)
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.schemas.timetable.timetable import (
    TeacherScheduleEntryResponse,
    TimetableCreate,
    TimetableDetailResponse,
    TimetableFilter,
    TimetableListResponse,
    TimetableResponse,
)
from app.schemas.timetable.timetable_entry import (
    TimetableEntryCreate,
    TimetableEntryDetailResponse,
)
from app.common.enums.timetable import TimetableStatus
from app.services.timetable_entry_service import TimetableEntryService
from app.services.timetable_service import TimetableService

router = APIRouter()


@router.post(
    "",
    response_model=TimetableDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_timetable(
    timetable_data: TimetableCreate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.create")),
    service: TimetableService = Depends(get_timetable_service),
) -> TimetableDetailResponse:
    """
    Create a new Timetable container for a class section.
    """
    created = service.create_timetable(
        db,
        timetable_data=timetable_data,
        current_school_id=current_user.school_id,
    )
    return created


@router.get(
    "",
    response_model=TimetableListResponse,
)
def list_timetables(
    academic_year_id: UUID | None = Query(default=None),
    school_class_id: UUID | None = Query(default=None),
    section_id: UUID | None = Query(default=None),
    academic_term_id: UUID | None = Query(default=None),
    status_filter: TimetableStatus | None = Query(default=None, alias="status"),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: TimetableService = Depends(get_timetable_service),
) -> TimetableListResponse:
    """
    List paginated Timetables for the current school.
    """
    filters = TimetableFilter(
        school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        academic_term_id=academic_term_id,
        status=status_filter,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return service.list_timetables(
        db,
        filters=filters,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/section/{section_id}",
    response_model=TimetableDetailResponse,
)
def get_section_timetable(
    section_id: UUID,
    academic_year_id: UUID | None = Query(default=None),
    academic_term_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: TimetableService = Depends(get_timetable_service),
) -> TimetableDetailResponse:
    """
    Retrieve active timetable matrix for a section.
    """
    return service.get_section_timetable(
        db,
        section_id=section_id,
        current_school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        academic_term_id=academic_term_id,
    )


@router.get(
    "/teacher/{teacher_id}",
    response_model=list[TeacherScheduleEntryResponse],
)
def get_teacher_schedule(
    teacher_id: UUID,
    academic_year_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: TimetableService = Depends(get_timetable_service),
) -> list[TeacherScheduleEntryResponse]:
    """
    Retrieve scheduled entries for a teacher across all active timetables.
    """
    return service.get_teacher_schedule(
        db,
        teacher_id=teacher_id,
        current_school_id=current_user.school_id,
        academic_year_id=academic_year_id,
    )


@router.get(
    "/{timetable_id}",
    response_model=TimetableDetailResponse,
)
def get_timetable(
    timetable_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: TimetableService = Depends(get_timetable_service),
) -> TimetableDetailResponse:
    """
    Get a specific Timetable with full entry matrix.
    """
    return service.get_timetable(
        db,
        timetable_id=timetable_id,
        current_school_id=current_user.school_id,
    )


@router.post(
    "/{timetable_id}/publish",
    response_model=TimetableDetailResponse,
)
def publish_timetable(
    timetable_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.publish")),
    service: TimetableService = Depends(get_timetable_service),
) -> TimetableDetailResponse:
    """
    Publish a DRAFT timetable after validating entries and single active published constraint.
    """
    return service.publish_timetable(
        db,
        timetable_id=timetable_id,
        current_school_id=current_user.school_id,
    )


@router.post(
    "/{timetable_id}/archive",
    response_model=TimetableDetailResponse,
)
def archive_timetable(
    timetable_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.archive")),
    service: TimetableService = Depends(get_timetable_service),
) -> TimetableDetailResponse:
    """
    Archive a PUBLISHED timetable.
    """
    return service.archive_timetable(
        db,
        timetable_id=timetable_id,
        current_school_id=current_user.school_id,
    )


@router.post(
    "/{timetable_id}/entries",
    response_model=TimetableEntryDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_timetable_entry(
    timetable_id: UUID,
    entry_data: TimetableEntryCreate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.create")),
    service: TimetableEntryService = Depends(get_timetable_entry_service),
) -> TimetableEntryDetailResponse:
    """
    Add a new TimetableEntry to a timetable container.
    """
    created = service.create_entry(
        db,
        timetable_id=timetable_id,
        entry_data=entry_data,
        current_school_id=current_user.school_id,
    )
    return TimetableEntryDetailResponse.model_validate(created)


@router.get(
    "/{timetable_id}/entries",
    response_model=list[TimetableEntryDetailResponse],
)
def list_timetable_entries(
    timetable_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: TimetableEntryService = Depends(get_timetable_entry_service),
) -> list[TimetableEntryDetailResponse]:
    """
    List all entries for a specific timetable with full entity details.
    """
    entries = service.list_entries_by_timetable(
        db,
        timetable_id=timetable_id,
        current_school_id=current_user.school_id,
    )
    return [TimetableEntryDetailResponse.model_validate(e) for e in entries]
