from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_teacher_substitution_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.schemas.timetable.teacher_substitution import (
    TeacherSubstitutionCreate,
    TeacherSubstitutionDetailResponse,
    TeacherSubstitutionFilter,
    TeacherSubstitutionListResponse,
    TeacherSubstitutionUpdate,
)
from app.services.teacher_substitution_service import TeacherSubstitutionService

router = APIRouter()


@router.post(
    "",
    response_model=TeacherSubstitutionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher_substitution(
    sub_data: TeacherSubstitutionCreate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("substitution.create")),
    service: TeacherSubstitutionService = Depends(get_teacher_substitution_service),
) -> TeacherSubstitutionDetailResponse:
    """
    Create a new TeacherSubstitution for a published timetable entry on a specific date.
    """
    return service.create_substitution(
        db,
        sub_data=sub_data,
        current_school_id=current_user.school_id,
    )


@router.get(
    "",
    response_model=TeacherSubstitutionListResponse,
)
def list_teacher_substitutions(
    timetable_entry_id: UUID | None = Query(default=None),
    original_teacher_id: UUID | None = Query(default=None),
    substitute_teacher_id: UUID | None = Query(default=None),
    substitution_date: date | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("substitution.view")),
    service: TeacherSubstitutionService = Depends(get_teacher_substitution_service),
) -> TeacherSubstitutionListResponse:
    """
    List paginated TeacherSubstitutions for the current school.
    """
    filters = TeacherSubstitutionFilter(
        school_id=current_user.school_id,
        timetable_entry_id=timetable_entry_id,
        original_teacher_id=original_teacher_id,
        substitute_teacher_id=substitute_teacher_id,
        substitution_date=substitution_date,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return service.list_substitutions(
        db,
        filters=filters,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/{substitution_id}",
    response_model=TeacherSubstitutionDetailResponse,
)
def get_teacher_substitution(
    substitution_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("substitution.view")),
    service: TeacherSubstitutionService = Depends(get_teacher_substitution_service),
) -> TeacherSubstitutionDetailResponse:
    """
    Get a specific TeacherSubstitution with full details.
    """
    return service.get_substitution(
        db,
        substitution_id=substitution_id,
        current_school_id=current_user.school_id,
    )


@router.put(
    "/{substitution_id}",
    response_model=TeacherSubstitutionDetailResponse,
)
def update_teacher_substitution(
    substitution_id: UUID,
    sub_data: TeacherSubstitutionUpdate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("substitution.update")),
    service: TeacherSubstitutionService = Depends(get_teacher_substitution_service),
) -> TeacherSubstitutionDetailResponse:
    """
    Update an existing TeacherSubstitution.
    """
    return service.update_substitution(
        db,
        substitution_id=substitution_id,
        sub_data=sub_data,
        current_school_id=current_user.school_id,
    )


@router.delete(
    "/{substitution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_teacher_substitution(
    substitution_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("substitution.delete")),
    service: TeacherSubstitutionService = Depends(get_teacher_substitution_service),
) -> None:
    """
    Soft delete a TeacherSubstitution.
    """
    service.delete_substitution(
        db,
        substitution_id=substitution_id,
        current_school_id=current_user.school_id,
    )
